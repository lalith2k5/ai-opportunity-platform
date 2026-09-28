"""One-shot backfill: enrich opportunities missing Phase-6 fields.

Sized for reliability on the Gemini free tier:
  - small batches (5) so commits happen fast and failures cost little
  - per-batch SIGALRM timeout (150s) so a stalled API call cannot hang
  - circuit-breaker aware -- stops cleanly when the LLM provider is down
  - fully resumable: filters on suggested_research_direction IS NULL

Usage (from backend/, venv active):
    python3 backfill_enrichment.py           # enrich everything
    python3 backfill_enrichment.py 50        # cap at 50
"""
import signal
import sys
import time

from app.database import SessionLocal
from app import models
from app.logger import logger


BATCH_SIZE = 5
BATCH_TIMEOUT_SECONDS = 150
THROTTLE_SECONDS = 2


class _BatchTimeout(Exception):
    pass


def _alarm_handler(signum, frame):
    raise _BatchTimeout("batch exceeded timeout")


def unenriched_ids(db, limit):
    rows = (
        db.query(models.Opportunity.id)
        .filter(models.Opportunity.suggested_research_direction.is_(None))
        .order_by(models.Opportunity.id)
        .limit(limit)
        .all()
    )
    return [r[0] for r in rows]


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10000

    db = SessionLocal()
    try:
        pending = unenriched_ids(db, limit)
    finally:
        db.close()

    total_pending = len(pending)
    print(f"[backfill] {total_pending} opportunities need enrichment (cap={limit})", flush=True)
    if total_pending == 0:
        print("[backfill] nothing to do.", flush=True)
        return

    from app.agents.orchestrator import OrchestratorAgent
    orch = OrchestratorAgent()

    signal.signal(signal.SIGALRM, _alarm_handler)

    processed = 0
    batches = 0
    consecutive_empty_batches = 0
    for i in range(0, total_pending, BATCH_SIZE):
        batch_ids = pending[i:i+BATCH_SIZE]
        batches += 1
        print(f"[backfill] batch {batches} ({len(batch_ids)} opps): ids {batch_ids[0]}..{batch_ids[-1]}", flush=True)

        timed_out = False
        try:
            signal.alarm(BATCH_TIMEOUT_SECONDS)
            stats = orch._enrich_opportunities(opp_ids=batch_ids)
        except _BatchTimeout:
            timed_out = True
            print(f"[backfill]   batch {batches} TIMED OUT after {BATCH_TIMEOUT_SECONDS}s -- skipping", flush=True)
            stats = {"updated": 0, "llm_directions": 0}
        except Exception as e:
            print(f"[backfill]   batch {batches} FAILED: {e}", flush=True)
            logger.exception("[backfill] batch failed")
            stats = {"updated": 0, "llm_directions": 0}
        finally:
            signal.alarm(0)

        updated = stats.get("updated", 0)
        llm = stats.get("llm_directions", 0)
        print(f"[backfill]   -> updated={updated} llm_directions={llm}", flush=True)

        if updated > 0:
            processed += updated
            consecutive_empty_batches = 0
        else:
            consecutive_empty_batches += 1
            if consecutive_empty_batches >= 4 and not timed_out:
                print(f"[backfill] 4 consecutive empty batches -- LLM provider likely exhausted. Stopping.", flush=True)
                print(f"[backfill] Re-run later; it will resume from where it stopped.", flush=True)
                break

        if i + BATCH_SIZE < total_pending:
            time.sleep(THROTTLE_SECONDS)

    print(f"[backfill] done. processed {processed}/{total_pending} across {batches} batches.", flush=True)


if __name__ == "__main__":
    main()
