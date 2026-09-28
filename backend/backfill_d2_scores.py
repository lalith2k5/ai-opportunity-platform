"""Backfill Phase 10.3 (SRS 21) scoring factors on all opportunities.

Recomputes technology_suitability_score, evidence_strength_score, and
recency_score for every opportunity. ZERO LLM calls -- pure local math.

Also recomputes opportunity_score with the new weights so the ranking
reflects the 3 new factors.

Idempotent. Fast (< 5 seconds for 300 opportunities).

Usage (from backend/, venv active):
    python3 backfill_d2_scores.py
"""
from app.database import SessionLocal
from app import models
from app.agents.opportunity_intelligence import OpportunityIntelligenceAgent


def main():
    agent = OpportunityIntelligenceAgent()
    db = SessionLocal()
    try:
        opps = db.query(models.Opportunity).all()
        print(f"[d2] {len(opps)} opportunities to rescore")

        # Preload tables
        all_techs = db.query(models.ProblemTechnology).all()
        all_profiles = db.query(models.ProblemProfile).all()
        all_evidence = db.query(models.OpportunityEvidence).all()
        clusters_by_id = {c.id: c for c in db.query(models.ProblemCluster).all()}

        techs_by_profile = {}
        for t in all_techs:
            techs_by_profile.setdefault(t.problem_profile_id, []).append(t)

        evidence_by_opp = {}
        for e in all_evidence:
            evidence_by_opp.setdefault(e.opportunity_id, []).append(e)

        def best_profile_for_cluster(cluster):
            if not cluster or not cluster.keywords:
                return None
            ck = {str(k).lower() for k in cluster.keywords[:10] if k}
            if not ck:
                return None
            best, best_n = None, 0
            for p in all_profiles:
                pk = {str(k).lower() for k in (p.keywords or [])[:10] if k}
                n = len(ck & pk)
                if n > best_n:
                    best, best_n = p, n
            return best

        updated = 0
        for opp in opps:
            cluster = clusters_by_id.get(opp.problem_cluster_id)
            profile = best_profile_for_cluster(cluster)
            techs = techs_by_profile.get(profile.id, []) if profile else []
            evs = evidence_by_opp.get(opp.id, [])

            _profile_techs = [
                {"name": t.technology_name, "stage": t.stage, "confidence": t.confidence}
                for t in techs
            ]
            ts = agent._derive_technology_suitability_score(_profile_techs, [])
            es = agent._derive_evidence_strength_score(len(evs))
            rc = agent._derive_recency_score(opp.created_at)

            opp.technology_suitability_score = ts
            opp.evidence_strength_score = es
            opp.recency_score = rc

            # Recompute composite with new weights
            w = agent.WEIGHTS
            new_score = (
                w["demand"]              * (opp.demand_score or 0.0)
                + w["research_gap"]      * (opp.research_gap_score or 0.0)
                + w["trend"]             * (opp.trend_score or 0.0)
                + w["innovation"]        * (opp.innovation_score or 0.0)
                + w["competition"]       * (1 - (opp.competition_score or 0.0))
                + w["feasibility"]       * (opp.feasibility_score or 0.0)
                + w["market_readiness"]  * (opp.market_readiness_score or 0.0)
                + w["confidence"]        * (opp.confidence_score or 0.0)
                + w["technology_suitability"] * ts
                + w["evidence_strength"]      * es
                + w["recency"]                * rc
            )
            opp.opportunity_score = round(new_score, 3)
            updated += 1

        db.commit()
        print(f"[d2] rescored {updated} opportunities")
        print("[d2] DONE")
    finally:
        db.close()


if __name__ == "__main__":
    main()
