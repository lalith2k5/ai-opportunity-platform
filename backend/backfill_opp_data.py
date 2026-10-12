
"""Recompute data-derived enrichment fields for every opportunity.

ZERO LLM calls. Uses the same logic as OrchestratorAgent._enrich_opportunities
but bypasses the LLM direction generation step entirely.

Populates:
  domain, industry, problem_type, related_technologies, existing_research,
  existing_approaches, known_limitations, emerging_trend, evidence_sources,
  technology_suitability_score, evidence_strength_score, recency_score

Runs in batches. Idempotent. Safe to re-run.
"""
from app.database import SessionLocal
from app import models
from app.agents.orchestrator import OrchestratorAgent


BATCH_SIZE = 25


def main():
    db = SessionLocal()
    try:
        all_ids = [r[0] for r in db.query(models.Opportunity.id).order_by(
            models.Opportunity.id).all()]
    finally:
        db.close()

    print(f"[opp-data] {len(all_ids)} opportunities")

    orch = OrchestratorAgent()
    total_updated = 0
    for i in range(0, len(all_ids), BATCH_SIZE):
        chunk = all_ids[i:i+BATCH_SIZE]
        try:
            stats = orch._enrich_opportunities(opp_ids=chunk, skip_llm=True)
            total_updated += stats.get("updated", 0)
            print(f"  batch {i//BATCH_SIZE + 1}: {stats}")
        except Exception as e:
            print(f"  batch {i//BATCH_SIZE + 1} FAILED: {e}")
    print(f"[opp-data] total updated={total_updated}")
    print("[opp-data] DONE")


if __name__ == "__main__":
    main()
