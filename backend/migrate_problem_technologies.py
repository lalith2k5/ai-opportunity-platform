"""One-shot migration: create problem_technologies table.

Idempotent — safe to run multiple times.

Run with:
    cd ~/ai-opportunity-platform/backend
    source venv/bin/activate
    python3 migrate_problem_technologies.py
"""
from sqlalchemy import text
from app.database import engine


def main():
    print("[migrate] create problem_technologies table if missing")
    with engine.begin() as conn:
        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS problem_technologies ("
            "  id SERIAL PRIMARY KEY,"
            "  problem_profile_id INTEGER NOT NULL REFERENCES problem_profiles(id) ON DELETE CASCADE,"
            "  technology_name VARCHAR(200) NOT NULL,"
            "  stage VARCHAR(32) NOT NULL DEFAULT 'potentially_applicable',"
            "  confidence DOUBLE PRECISION DEFAULT 0.5,"
            "  evidence TEXT,"
            "  created_at TIMESTAMPTZ DEFAULT NOW()"
            ")"
        ))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_problem_technologies_profile "
            "ON problem_technologies (problem_profile_id)"
        ))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_problem_technologies_name "
            "ON problem_technologies (technology_name)"
        ))
        # Prevent exact dup rows for the same profile + tech name (case-insensitive)
        conn.execute(text(
            "CREATE UNIQUE INDEX IF NOT EXISTS ux_problem_technologies_profile_name "
            "ON problem_technologies (problem_profile_id, LOWER(technology_name))"
        ))
    print("[migrate] done")


if __name__ == "__main__":
    main()
