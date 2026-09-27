"""Dedup opportunities/clusters/gaps/trends by title/name, re-pointing FK refs first."""
from app.database import SessionLocal
from app import models


def find_keep_map(rows, key_field, score_field):
    """Return (keep_map, delete_ids). keep_map: dup_id -> keep_id"""
    seen = {}          # key -> best row (keep candidate)
    keep_map = {}      # every_id -> its keep_id (identity for kept rows)
    delete_ids = []

    for r in rows:
        key = getattr(r, key_field)
        if not key:
            keep_map[r.id] = r.id
            continue
        if key not in seen:
            seen[key] = r
            keep_map[r.id] = r.id
            continue
        keep = seen[key]
        keep_score = getattr(keep, score_field) or 0
        dup_score = getattr(r, score_field) or 0
        if dup_score > keep_score:
            # duplicate is better → it becomes the keeper, old keeper gets deleted
            keep_map[keep.id] = r.id
            delete_ids.append(keep.id)
            keep_map[r.id] = r.id
            seen[key] = r
        else:
            keep_map[r.id] = keep.id
            delete_ids.append(r.id)
    return keep_map, delete_ids


def remap_fk(db, table_model, fk_column_name, keep_map, delete_ids):
    """Update fk_column to point to kept row before deleting duplicates."""
    if not delete_ids:
        return
    for dup_id in delete_ids:
        keep_id = keep_map[dup_id]
        db.query(table_model).filter(
            getattr(table_model, fk_column_name) == dup_id
        ).update({fk_column_name: keep_id})
    db.flush()


def delete_ids(db, Model, ids):
    if not ids:
        return
    db.query(Model).filter(Model.id.in_(ids)).delete(synchronize_session=False)
    db.flush()


def main():
    db = SessionLocal()
    try:
        # --- Opportunities (no incoming FKs) ---
        opps = db.query(models.Opportunity).order_by(models.Opportunity.id).all()
        _, opp_del = find_keep_map(opps, "title", "opportunity_score")
        n_opps = len(opp_del)
        delete_ids(db, models.Opportunity, opp_del)

        # --- Research gaps (referenced by opportunities.research_gap_id) ---
        gaps = db.query(models.ResearchGap).order_by(models.ResearchGap.id).all()
        gap_keep, gap_del = find_keep_map(gaps, "title", "gap_score")
        remap_fk(db, models.Opportunity, "research_gap_id", gap_keep, gap_del)
        n_gaps = len(gap_del)
        delete_ids(db, models.ResearchGap, gap_del)

        # --- Problem clusters (referenced by gaps + opportunities) ---
        clusters = db.query(models.ProblemCluster).order_by(models.ProblemCluster.id).all()
        cluster_keep, cluster_del = find_keep_map(clusters, "title", "demand_score")
        remap_fk(db, models.ResearchGap, "problem_cluster_id", cluster_keep, cluster_del)
        remap_fk(db, models.Opportunity, "problem_cluster_id", cluster_keep, cluster_del)
        n_clusters = len(cluster_del)
        delete_ids(db, models.ProblemCluster, cluster_del)

        # --- Trends (no incoming FKs) ---
        trends = db.query(models.Trend).order_by(models.Trend.id).all()
        _, trend_del = find_keep_map(trends, "name", "trend_score")
        n_trends = len(trend_del)
        delete_ids(db, models.Trend, trend_del)

        db.commit()

        print(f"Deleted: {n_opps} opps, {n_clusters} clusters, {n_gaps} gaps, {n_trends} trends")
        print(f"Opportunities: {db.query(models.Opportunity).count()}")
        print(f"Clusters:      {db.query(models.ProblemCluster).count()}")
        print(f"Gaps:          {db.query(models.ResearchGap).count()}")
        print(f"Trends:        {db.query(models.Trend).count()}")
    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
