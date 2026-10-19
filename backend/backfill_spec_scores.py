"""Backfill spec-compliant score, confidence, gap kind/status. Idempotent."""
from datetime import datetime, timezone
from app.database import SessionLocal
from app import models
from app.scoring.configs import (
    load_active_weight_config, load_active_confidence_config,
    seed_defaults_if_empty,
)
from app.scoring.scoring_agent import compute_score, compute_confidence, factor_recency


def main():
    seed_defaults_if_empty()
    weights = load_active_weight_config()
    conf_cfg = load_active_confidence_config()

    db = SessionLocal()
    try:
        opps = db.query(models.Opportunity).all()
        all_evidence = {}
        for ev in db.query(models.OpportunityEvidence).all():
            all_evidence.setdefault(ev.opportunity_id, []).append(ev)

        now = datetime.now(timezone.utc)
        opp_updated = 0
        for opp in opps:
            s_problem = float(opp.demand_score or 0.0) * 100
            s_tech = float(opp.technology_suitability_score or 0.0) * 100
            s_gap = float(opp.research_gap_score or 0.0) * 100
            s_trend = float(opp.trend_score or 0.0) * 100
            s_evidence = float(opp.evidence_strength_score or 0.0) * 100
            s_feasibility = float(opp.feasibility_score or 0.0) * 100

            evidences = all_evidence.get(opp.id, [])
            if evidences:
                ages = []
                for ev in evidences:
                    ts = ev.created_at
                    if ts is None:
                        continue
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=timezone.utc)
                    ages.append(max(0, int((now - ts).total_seconds() // 86400)))
                mean_age = (sum(ages) / len(ages)) if ages else 30.0
            elif opp.created_at is not None:
                ts = opp.created_at
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                mean_age = max(0.0, (now - ts).total_seconds() / 86400.0)
            else:
                mean_age = 30.0

            s_recency = factor_recency(mean_age)

            try:
                score = compute_score(
                    s_problem, s_tech, s_gap, s_trend, s_evidence,
                    s_feasibility, s_recency, weights,
                )
            except ValueError:
                score = 0

            opp.opportunity_score_spec = float(score)
            opp.weights_version = weights.version
            opp.trend_window = 90

            ev_items = []
            for ev in evidences:
                ev_items.append({
                    "polarity": getattr(ev, "polarity", "SUPPORTS") or "SUPPORTS",
                    "source_type": ev.source or "unknown",
                    "credibility_weight": float(ev.relevance_score or 0.5),
                    "doc_id": str(ev.id),
                })
            confidence = compute_confidence(ev_items, 0.0, conf_cfg)
            opp.confidence_spec = int(confidence)
            opp.confidence_version = conf_cfg.version
            opp_updated += 1

        gaps = db.query(models.ResearchGap).all()
        gap_updated = 0
        for gap in gaps:
            ev = gap.evidence or {}
            semantic = float(ev.get("semantic_coverage") or 0.0)
            coverage = float(ev.get("coverage") or 0.0)
            if semantic < 0.3:
                gap.kind = "COVERAGE"
            else:
                gap.kind = "CAPABILITY"
            gap.gap_status = "PROPOSED"
            gap.gap_confidence = int(round(max(0.0, min(1.0, 1.0 - coverage)) * 100))
            snippets = ev.get("future_work_snippets") or []
            gap.supporting_limitations = snippets if isinstance(snippets, list) else []
            gap_updated += 1

        db.commit()
        print("[backfill] opportunities updated: " + str(opp_updated))
        print("[backfill] research_gaps updated: " + str(gap_updated))
    except Exception as e:
        db.rollback()
        print("[backfill] FAILED: " + str(e))
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
