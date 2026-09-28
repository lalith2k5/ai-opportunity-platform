"""One-shot migration: create problem_papers table.

Idempotent — safe to run multiple times.

Run with:
    cd ~/ai-opportunity-platform/backend
    source venv/bin/activate
    python3 migrate_problem_papers.py
"""
from sqlalchemy import text
from app.database import engine


def main():
    print("[migrate] create problem_papers table if missing")
    with engine.begin() as conn:
        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS problem_papers ("
            "  id SERIAL PRIMARY KEY,"
            "  problem_profile_id INTEGER NOT NULL "
            "    REFERENCES problem_profiles(id) ON DELETE CASCADE,"
            "  arxiv_id VARCHAR(200),"
            "  title VARCHAR(500),"
            "  authors JSONB DEFAULT '[]'::jsonb,"
            "  abstract TEXT,"
            "  url VARCHAR(500),"
            "  relevance_score DOUBLE PRECISION DEFAULT 0.5,"
            "  limitations JSONB DEFAULT '[]'::jsonb,"
            "  published VARCHAR(100),"
            "  created_at TIMESTAMPTZ DEFAULT NOW()"
            ")"
        ))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_problem_papers_profile "
            "ON problem_papers (problem_profile_id)"
        ))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_problem_papers_arxiv "
            "ON problem_papers (arxiv_id)"
        ))
        conn.execute(text(
            "CREATE UNIQUE INDEX IF NOT EXISTS ux_problem_papers_profile_arxiv "
            "ON problem_papers (problem_profile_id, arxiv_id)"
        ))
    print("[migrate] done")


if __name__ == "__main__":
    main()
