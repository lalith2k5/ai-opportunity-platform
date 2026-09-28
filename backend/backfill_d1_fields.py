"""Backfill D1 fields (SRS §11 + §13) on existing rows.

  ProblemProfile: affected_stakeholders, evidence, confidence
  ProblemPaper:   research_methods, results_summary, research_areas

Runs focused LLM calls per row using the row's own fields. Resumable
(skips rows already populated). Circuit-breaker aware.

Usage (from backend/, venv active):
    python3 backfill_d1_fields.py            # both
    python3 backfill_d1_fields.py profiles   # profiles only
    python3 backfill_d1_fields.py papers     # papers only
"""
import json
import re
import sys
import time

from app.database import SessionLocal
from app import models
from app.logger import logger
from app.services.llm_service import LLMService


MAX_CONSECUTIVE_FAILURES = 3
THROTTLE_SECONDS = 1


def _extract_json(text):
    if not text:
        return None
    text = re.sub(r"^```(?:json)?\s*", "", text.strip())
    text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(text[start:end+1])
    except Exception:
        return None


# ---------------- profiles ----------------
PROFILE_PROMPT = """You are extracting structured metadata from a problem profile.

Return ONLY valid JSON, no markdown, no preamble:
{
  "affected_stakeholders": ["up to 6 roles/orgs/user-types impacted"],
  "evidence": ["up to 6 direct facts or claims from the description below"],
  "confidence": 0.0
}

RULES:
- Only include stakeholders and evidence that are supported by the text below.
- Do NOT invent.
- confidence is a float 0.0 to 1.0 reflecting how complete and specific the description is.

PROBLEM:
Title: {title}
Description: {description}
Industry: {domain}
Keywords: {keywords}
"""


def _profile_needs(pr):
    return (not pr.affected_stakeholders) or (not pr.evidence)


def _do_profiles(llm, db):
    rows = db.query(models.ProblemProfile).all()
    pending = [r for r in rows if _profile_needs(r)]
    print(f"[d1] {len(pending)}/{len(rows)} profiles need backfill", flush=True)
    done = 0
    consecutive = 0
    for r in pending:
        prompt = (PROFILE_PROMPT
                  .replace("{title}", (r.problem_title or "")[:300])
                  .replace("{description}", (r.problem_description or "")[:2000])
                  .replace("{domain}", r.industry_domain or "Other")
                  .replace("{keywords}", ", ".join((r.keywords or [])[:10])))
        try:
            resp = llm.generate(prompt)
        except Exception as e:
            print(f"[d1] profile #{r.id} LLM error: {e}", flush=True)
            consecutive += 1
            if consecutive >= MAX_CONSECUTIVE_FAILURES:
                print("[d1] circuit breaker (profiles)", flush=True)
                break
            continue
        if not resp or resp.startswith("All LLM providers failed") or resp.startswith("AI service not configured"):
            consecutive += 1
            if consecutive >= MAX_CONSECUTIVE_FAILURES:
                print("[d1] circuit breaker (profiles)", flush=True)
                break
            continue
        data = _extract_json(resp)
        if not data:
            consecutive += 1
            continue
        consecutive = 0
        st = data.get("affected_stakeholders") or []
        if not isinstance(st, list): st = [str(st)]
        st = [str(x).strip()[:120] for x in st if x and str(x).strip()][:10]
        ev = data.get("evidence") or []
        if not isinstance(ev, list): ev = [str(ev)]
        ev = [str(x).strip()[:400] for x in ev if x and str(x).strip()][:10]
        try: conf = float(data.get("confidence", 0.5))
        except Exception: conf = 0.5
        conf = max(0.0, min(1.0, conf))
        if st: r.affected_stakeholders = st
        if ev: r.evidence = ev
        r.confidence = round(conf, 3)
        db.add(r)
        done += 1
        if done % 5 == 0:
            db.commit()
            print(f"[d1] profiles committed: {done}", flush=True)
        time.sleep(THROTTLE_SECONDS)
    db.commit()
    print(f"[d1] profiles done: {done}", flush=True)


# ---------------- papers ----------------
PAPER_PROMPT = """You are extracting metadata from a research paper relative to a problem.

Return ONLY valid JSON, no markdown, no preamble:
{
  "research_methods": ["up to 4 short methodology names"],
  "results_summary": "one short sentence (<=200 chars) or empty string",
  "research_areas": ["up to 3 broad topic labels"]
}

RULES:
- Only from the abstract below. Do NOT invent.
- Empty arrays/string if the abstract does not state them.

PROBLEM: {problem_title}

PAPER TITLE: {paper_title}
ABSTRACT: {abstract}
"""


def _paper_needs(pp):
    return (not pp.research_methods) or (not pp.results_summary) or (not pp.research_areas)


def _do_papers(llm, db):
    profiles = {p.id: p for p in db.query(models.ProblemProfile).all()}
    rows = db.query(models.ProblemPaper).all()
    pending = [r for r in rows if _paper_needs(r)]
    print(f"[d1] {len(pending)}/{len(rows)} papers need backfill", flush=True)
    done = 0
    consecutive = 0
    for r in pending:
        parent = profiles.get(r.problem_profile_id)
        prompt = (PAPER_PROMPT
                  .replace("{problem_title}", (parent.problem_title if parent else "")[:300])
                  .replace("{paper_title}", (r.title or "")[:300])
                  .replace("{abstract}", (r.abstract or "")[:1500]))
        try:
            resp = llm.generate(prompt)
        except Exception as e:
            print(f"[d1] paper #{r.id} LLM error: {e}", flush=True)
            consecutive += 1
            if consecutive >= MAX_CONSECUTIVE_FAILURES:
                print("[d1] circuit breaker (papers)", flush=True)
                break
            continue
        if not resp or resp.startswith("All LLM providers failed") or resp.startswith("AI service not configured"):
            consecutive += 1
            if consecutive >= MAX_CONSECUTIVE_FAILURES:
                print("[d1] circuit breaker (papers)", flush=True)
                break
            continue
        data = _extract_json(resp)
        if not data:
            consecutive += 1
            continue
        consecutive = 0
        rm = data.get("research_methods") or []
        if not isinstance(rm, list): rm = [str(rm)]
        rm = [str(x).strip()[:120] for x in rm if x and str(x).strip()][:4]
        rs = str(data.get("results_summary") or "").strip()[:400]
        ra = data.get("research_areas") or []
        if not isinstance(ra, list): ra = [str(ra)]
        ra = [str(x).strip()[:60] for x in ra if x and str(x).strip()][:3]
        if rm: r.research_methods = rm
        if rs: r.results_summary = rs
        if ra: r.research_areas = ra
        db.add(r)
        done += 1
        if done % 5 == 0:
            db.commit()
            print(f"[d1] papers committed: {done}", flush=True)
        time.sleep(THROTTLE_SECONDS)
    db.commit()
    print(f"[d1] papers done: {done}", flush=True)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "both"
    llm = LLMService()
    db = SessionLocal()
    try:
        if mode in ("profiles", "both"):
            _do_profiles(llm, db)
        if mode in ("papers", "both"):
            _do_papers(llm, db)
    finally:
        db.close()
    print("[d1] ALL DONE", flush=True)


if __name__ == "__main__":
    main()
