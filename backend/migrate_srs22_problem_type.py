"""SRS 22 -- add problem_type to opportunities.

Idempotent.
"""
from sqlalchemy import text
from app.database import engine


def main():
    print("[migrate_srs22] problem_type on opportunities")
    with engine.begin() as conn:
        conn.execute(text(
            "ALTER TABLE opportunities "
            "ADD COLUMN IF NOT EXISTS problem_type VARCHAR(80)"
        ))
    print("[migrate_srs22] done")


if __name__ == "__main__":
    main()
