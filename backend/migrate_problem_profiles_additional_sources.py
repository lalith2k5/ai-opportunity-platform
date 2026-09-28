"""One-shot migration: add ProblemProfile.additional_sources JSONB column.

Idempotent — safe to run multiple times.

Run with:
    cd ~/ai-opportunity-platform/backend
    source venv/bin/activate
    python3 migrate_problem_profiles_additional_sources.py
"""
from sqlalchemy import text
from app.database import engine


def main():
    print("[migrate] ensure additional_sources column exists")
    with engine.begin() as conn:
        conn.execute(text(
            "ALTER TABLE problem_profiles "
            "ADD COLUMN IF NOT EXISTS additional_sources JSONB DEFAULT '[]'::jsonb"
        ))
        conn.execute(text(
            "UPDATE problem_profiles SET additional_sources = '[]'::jsonb "
            "WHERE additional_sources IS NULL"
        ))
    print("[migrate] done")


if __name__ == "__main__":
    main()
