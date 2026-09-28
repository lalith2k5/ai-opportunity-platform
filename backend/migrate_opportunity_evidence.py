"""One-shot migration: create opportunity_evidence table.

Idempotent — safe to run multiple times.

Run with:
    cd ~/ai-opportunity-platform/backend
    source venv/bin/activate
    python3 migrate_opportunity_evidence.py
"""
from sqlalchemy import text
from app.database import engine


def main():
    print("[migrate] create opportunity_evidence table if missing")
    with engine.begin() as conn:
        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS opportunity_evidence ("
            "  id SERIAL PRIMARY KEY,"
            "  opportunity_id INTEGER NOT NULL "
            "    REFERENCES opportunities(id) ON DELETE CASCADE,"
            "  source VARCHAR(64) NOT NULL,"
            "  title VARCHAR(500),"
            "  url VARCHAR(500),"
            "  relevance_score DOUBLE PRECISION DEFAULT 0.0,"
            "  snippet TEXT,"
            "  created_at TIMESTAMPTZ DEFAULT NOW()"
            ")"
        ))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_opportunity_evidence_opp "
            "ON opportunity_evidence (opportunity_id)"
        ))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_opportunity_evidence_source "
            "ON opportunity_evidence (source)"
        ))
        conn.execute(text(
            "CREATE UNIQUE INDEX IF NOT EXISTS ux_opportunity_evidence_opp_url "
            "ON opportunity_evidence (opportunity_id, url)"
        ))
    print("[migrate] done")


if __name__ == "__main__":
    main()
