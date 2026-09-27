"""Regenerate all opportunity + gap titles using current logic."""
from app.database import SessionLocal
from app import models
from app.agents.opportunity_intelligence import OpportunityIntelligenceAgent
from app.agents.research_gap import ResearchGapAgent
import re


def main():
    opp_agent = OpportunityIntelligenceAgent()
    gap_agent = ResearchGapAgent()
    db = SessionLocal()
    try:
        # Opportunities
        opps = db.query(models.Opportunity).all()
        for opp in opps:
            cluster = None
            if opp.problem_cluster_id:
                cluster = db.query(models.ProblemCluster).filter(
                    models.ProblemCluster.id == opp.problem_cluster_id
                ).first()
            if not cluster:
                continue
            gap = None
            if opp.research_gap_id:
                gap = db.query(models.ResearchGap).filter(
                    models.ResearchGap.id == opp.research_gap_id
                ).first()

            cluster_dict = {
                "title": cluster.title,
                "description": cluster.description,
                "keywords": cluster.keywords or [],
                "demand_score": cluster.demand_score,
            }
            gap_dict = {"gap_score": gap.gap_score} if gap else None

            opp.title = opp_agent._generate_title(cluster_dict, gap_dict)
            new_desc = opp_agent._generate_description(cluster_dict, gap_dict)
            if cluster.title:
                from app.agents.opportunity_intelligence import _is_latin_only
                if _is_latin_only(cluster.title):
                    new_desc += f" Source cluster: {cluster.title[:120]}"
            opp.description = new_desc

        # Research gaps
        gaps = db.query(models.ResearchGap).all()
        for gap in gaps:
            cluster = None
            if gap.problem_cluster_id:
                cluster = db.query(models.ProblemCluster).filter(
                    models.ProblemCluster.id == gap.problem_cluster_id
                ).first()
            if not cluster:
                continue
            raw_title = cluster.title or "Unknown"
            clean = raw_title.replace("Problem Cluster:", "").strip()
            clean = re.sub(r"[^\x00-\x7F]+", "", clean).strip()
            if not clean:
                clean = "Unknown Domain"
            gap.title = f"Research Gap: {clean}"

        db.commit()
        print(f"Regenerated {len(opps)} opportunities, {len(gaps)} gaps")
    finally:
        db.close()


if __name__ == "__main__":
    main()
