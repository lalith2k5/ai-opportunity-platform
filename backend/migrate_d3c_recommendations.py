"""Phase 10.10 -- create recommendations table (SRS 30).

Idempotent.
"""
from sqlalchemy import text
from app.database import engine


def main():
    print("[migrate_d3c] recommendations table")
    with engine.begin() as conn:
        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS recommendations ("
            "  id SERIAL PRIMARY KEY,"
            "  opportunity_id INTEGER NOT NULL "
            "    REFERENCES opportunities(id) ON DELETE CASCADE,"
            "  user_id INTEGER REFERENCES users(id),"
            "  suggested_research_direction TEXT,"
            "  suggested_project_direction TEXT,"
            "  rationale TEXT,"
            "  score_at_time DOUBLE PRECISION,"
            "  rank_at_time INTEGER,"
            "  created_at TIMESTAMPTZ DEFAULT NOW()"
            ")"
        ))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_recommendations_opp "
            "ON recommendations (opportunity_id)"
        ))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_recommendations_created "
            "ON recommendations (created_at)"
        ))
    print("[migrate_d3c] done")


if __name__ == "__main__":
    main()
