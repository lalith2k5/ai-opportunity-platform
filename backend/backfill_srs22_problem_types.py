"""SRS 22 -- backfill problem_type on existing opportunities.

Walks every opportunity, finds the best-matching profile by cluster keyword
overlap, copies profile.problem_type onto the opportunity. Zero LLM.

Idempotent.

Usage (from backend/, venv active):
    python3 backfill_srs22_problem_types.py
"""
from app.database import SessionLocal
from app import models


def best_profile_for_cluster(cluster, all_profiles):
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


def main():
    db = SessionLocal()
    try:
        profiles = db.query(models.ProblemProfile).all()
        clusters = {c.id: c for c in db.query(models.ProblemCluster).all()}
        opps = db.query(models.Opportunity).all()
        print(f"[srs22] {len(opps)} opps, {len(profiles)} profiles")

        updated = 0
        for opp in opps:
            cluster = clusters.get(opp.problem_cluster_id)
            profile = best_profile_for_cluster(cluster, profiles)
            if profile and profile.problem_type and opp.problem_type != profile.problem_type:
                opp.problem_type = profile.problem_type
                updated += 1

        db.commit()
        print(f"[srs22] updated {updated}")
        print("[srs22] DONE")
    finally:
        db.close()


if __name__ == "__main__":
    main()
