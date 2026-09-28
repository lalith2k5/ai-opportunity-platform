"""One-shot migration: add ProblemProfile.canonical_hash + backfill.

Idempotent — safe to run multiple times. Uses ADD COLUMN IF NOT EXISTS
(PostgreSQL) then backfills hashes for existing rows.

Run with:
    cd ~/ai-opportunity-platform/backend
    source venv/bin/activate
    python3 migrate_problem_profiles_canonical_hash.py
"""
from sqlalchemy import text

from app.database import engine, SessionLocal
from app import models
from app.agents.problem_agent import ProblemAgent


def main():
    print("[migrate] step 1: ensure column exists")
    with engine.begin() as conn:
        conn.execute(text(
            "ALTER TABLE problem_profiles "
            "ADD COLUMN IF NOT EXISTS canonical_hash VARCHAR(16)"
        ))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_problem_profiles_canonical_hash "
            "ON problem_profiles (canonical_hash)"
        ))
    print("[migrate] step 1: OK")

    print("[migrate] step 2: backfill hashes for existing rows")
    db = SessionLocal()
    try:
        agent = ProblemAgent()
        rows = db.query(models.ProblemProfile).all()
        updated = 0
        for r in rows:
            h = agent.compute_hash(r.problem_title or "")
            if h and r.canonical_hash != h:
                r.canonical_hash = h
                updated += 1
        db.commit()
        print(f"[migrate] step 2: backfilled {updated} of {len(rows)} rows")

        # Report any dup collisions the backfill revealed
        from sqlalchemy import func
        dups = (
            db.query(models.ProblemProfile.canonical_hash, func.count(models.ProblemProfile.id))
            .filter(models.ProblemProfile.canonical_hash.isnot(None))
            .group_by(models.ProblemProfile.canonical_hash)
            .having(func.count(models.ProblemProfile.id) > 1)
            .all()
        )
        if dups:
            print(f"[migrate] NOTE: {len(dups)} canonical_hash collision(s) found in existing rows.")
            print("[migrate]       These pre-date Phase 1.2 and are left in place.")
            print("[migrate]       Future saves will dedup against them automatically.")
    finally:
        db.close()
    print("[migrate] done")


if __name__ == "__main__":
    main()
