"""One-shot migration: create opportunity_score_history table.

Idempotent — safe to run multiple times.
"""
from sqlalchemy import text
from app.database import engine


def main():
    print("[migrate] create opportunity_score_history")
    with engine.begin() as conn:
        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS opportunity_score_history ("
            "  id SERIAL PRIMARY KEY,"
            "  opportunity_id INTEGER NOT NULL "
            "    REFERENCES opportunities(id) ON DELETE CASCADE,"
            "  opportunity_score DOUBLE PRECISION DEFAULT 0.0,"
            "  rank INTEGER,"
            "  recorded_at TIMESTAMPTZ DEFAULT NOW()"
            ")"
        ))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_opp_score_hist_opp "
            "ON opportunity_score_history (opportunity_id)"
        ))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_opp_score_hist_time "
            "ON opportunity_score_history (recorded_at)"
        ))
    print("[migrate] done")


if __name__ == "__main__":
    main()
