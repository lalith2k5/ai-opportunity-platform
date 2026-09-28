"""One-shot migration -- Phase 10.2 (SRS §11, §13 completion).

Adds 6 columns:
  ProblemProfile: affected_stakeholders (jsonb), evidence (jsonb), confidence (float)
  ProblemPaper:   research_methods (jsonb), results_summary (text), research_areas (jsonb)

Idempotent. Safe to run repeatedly.
"""
from sqlalchemy import text
from app.database import engine


def main():
    print("[migrate_d1] adding columns")
    with engine.begin() as conn:
        for table, col, typ in [
            ("problem_profiles", "affected_stakeholders", "JSONB DEFAULT '[]'::jsonb"),
            ("problem_profiles", "evidence",               "JSONB DEFAULT '[]'::jsonb"),
            ("problem_profiles", "confidence",             "DOUBLE PRECISION DEFAULT 0.5"),
            ("problem_papers",   "research_methods",       "JSONB DEFAULT '[]'::jsonb"),
            ("problem_papers",   "results_summary",        "TEXT"),
            ("problem_papers",   "research_areas",         "JSONB DEFAULT '[]'::jsonb"),
        ]:
            conn.execute(text(
                f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {typ}"
            ))
            print(f"  + {table}.{col}")
    print("[migrate_d1] done")


if __name__ == "__main__":
    main()
