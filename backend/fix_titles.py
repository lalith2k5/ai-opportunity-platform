"""Clean garbage titles in problem_clusters, research_gaps, opportunities.

Rows whose keyword list yields < 2 meaningful keywords after cleaning are
deleted along with their dependent rows (opportunities reference them by FK).
"""
from app.database import SessionLocal
from app import models
from app.agents.problem_discovery import _EXTRA_NOISE  # applies NOISE_WORDS mutation
from app.agents.opportunity_intelligence import (
    _clean_keywords, _title_case, _is_latin_only, OpportunityIntelligenceAgent,
)

MIN_KEEP = 2


def _clean_flat(raw):
    cleaned = _clean_keywords(raw or [])
    return cleaned["phrases"] + cleaned["singles"]


def _label(kws):
    return ", ".join(_title_case(k) for k in kws[:3])


def main():
    db = SessionLocal()
    try:
        # ---------- 1. Classify clusters ----------
        all_clusters = db.query(models.ProblemCluster).all()
        keep, drop = [], []
        for c in all_clusters:
            clean = _clean_flat(c.keywords or [])
            if len(clean) >= MIN_KEEP:
                keep.append((c, clean))
            else:
                drop.append(c)

        drop_ids = [c.id for c in drop]
        print(f"Clusters: {len(keep)} kept, {len(drop)} will be deleted")

        # ---------- 2. Delete noise clusters + dependents ----------
        if drop_ids:
            opp_to_drop = db.query(models.Opportunity).filter(
                models.Opportunity.problem_cluster_id.in_(drop_ids)
            ).all()
            opp_drop_ids = [o.id for o in opp_to_drop]
            db.query(models.Opportunity).filter(
                models.Opportunity.problem_cluster_id.in_(drop_ids)
            ).delete(synchronize_session=False)
            db.query(models.ResearchGap).filter(
                models.ResearchGap.problem_cluster_id.in_(drop_ids)
            ).delete(synchronize_session=False)
            db.query(models.ProblemCluster).filter(
                models.ProblemCluster.id.in_(drop_ids)
            ).delete(synchronize_session=False)
            db.flush()
            print(f"  -> deleted {len(drop_ids)} clusters, {len(opp_drop_ids)} linked opportunities, "
                  f"and their linked gaps")

        # ---------- 3. Rewrite surviving cluster titles ----------
        c_updated = 0
        for c, clean in keep:
            new_title = f"Problem Cluster: {_label(clean)}"
            new_desc = f"Recurring issues related to: {', '.join(clean[:8])}"
            if c.title != new_title or c.keywords != clean:
                c.title = new_title
                c.keywords = clean
                c.description = new_desc
                c_updated += 1
        db.flush()

        # ---------- 4. Rewrite gap titles ----------
        cluster_by_id = {c.id: c for c in db.query(models.ProblemCluster).all()}
        g_updated = g_dropped = 0
        for g in db.query(models.ResearchGap).all():
            c = cluster_by_id.get(g.problem_cluster_id)
            if not c:
                db.delete(g)
                g_dropped += 1
                continue
            kws = _clean_flat(c.keywords or [])
            if len(kws) < MIN_KEEP:
                db.delete(g)
                g_dropped += 1
                continue
            new_title = f"Research Gap: {_label(kws)}"
            if g.title != new_title:
                g.title = new_title
                g_updated += 1
        db.flush()

        # ---------- 5. Rewrite opportunity titles ----------
        agent = OpportunityIntelligenceAgent()
        cluster_by_id = {c.id: c for c in db.query(models.ProblemCluster).all()}
        gap_by_id = {g.id: g for g in db.query(models.ResearchGap).all()}
        o_updated = 0
        for opp in db.query(models.Opportunity).all():
            c = cluster_by_id.get(opp.problem_cluster_id)
            if not c:
                continue
            gap = gap_by_id.get(opp.research_gap_id)
            cluster_dict = {
                "title": c.title, "description": c.description,
                "keywords": c.keywords or [], "demand_score": c.demand_score,
            }
            gap_dict = {"gap_score": gap.gap_score} if gap else None
            new_title = agent._generate_title(cluster_dict, gap_dict)
            new_desc = agent._generate_description(cluster_dict, gap_dict)
            if c.title and _is_latin_only(c.title):
                new_desc += f" Source cluster: {c.title[:120]}"
            if opp.title != new_title:
                opp.title = new_title
                o_updated += 1
            opp.description = new_desc

        db.commit()
        print("=" * 60)
        print(f"Clusters kept:     {len(keep)} (updated titles: {c_updated})")
        print(f"Clusters deleted:  {len(drop)}")
        print(f"Gaps updated:      {g_updated}")
        print(f"Gaps deleted:      {g_dropped}")
        print(f"Opportunities upd: {o_updated}")
        print("=" * 60)
    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
