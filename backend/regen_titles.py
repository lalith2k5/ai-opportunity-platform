"""Regenerate titles for existing opportunities using current logic."""
from app.database import SessionLocal
from app import models
from app.agents.opportunity_intelligence import OpportunityIntelligenceAgent


def main():
    agent = OpportunityIntelligenceAgent()
    db = SessionLocal()
    try:
        opps = db.query(models.Opportunity).all()
        updated = 0
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

            opp.title = agent._generate_title(cluster_dict, gap_dict)
            new_desc = agent._generate_description(cluster_dict, gap_dict)
            if cluster.title:
                new_desc += f" Source cluster: {cluster.title[:120]}"
            opp.description = new_desc
            updated += 1

        db.commit()
        print(f"Regenerated {updated} opportunities")
    finally:
        db.close()


if __name__ == "__main__":
    main()
