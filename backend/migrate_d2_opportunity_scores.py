"""Phase 10.3 migration -- 3 new SRS 21 scoring-factor columns on opportunities.

Idempotent. Safe to run repeatedly.
"""
from sqlalchemy import text
from app.database import engine


def main():
    print("[migrate_d2] adding scoring factor columns")
    with engine.begin() as conn:
        for col, typ in [
            ("technology_suitability_score", "DOUBLE PRECISION DEFAULT 0.0"),
            ("evidence_strength_score",      "DOUBLE PRECISION DEFAULT 0.0"),
            ("recency_score",                "DOUBLE PRECISION DEFAULT 0.0"),
        ]:
            conn.execute(text(
                f"ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS {col} {typ}"
            ))
            print(f"  + opportunities.{col}")
    print("[migrate_d2] done")


if __name__ == "__main__":
    main()
