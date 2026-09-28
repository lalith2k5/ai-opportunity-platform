"""One-shot migration: add enrichment columns to opportunities.

Idempotent — safe to run multiple times.

Run with:
    cd ~/ai-opportunity-platform/backend
    source venv/bin/activate
    python3 migrate_opportunity_enrichment.py
"""
from sqlalchemy import text
from app.database import engine


COLS = [
    ("domain",                    "VARCHAR(120)"),
    ("industry",                  "VARCHAR(120)"),
    ("related_technologies",      "JSONB DEFAULT '[]'::jsonb"),
    ("existing_research",         "JSONB DEFAULT '[]'::jsonb"),
    ("existing_approaches",       "TEXT"),
    ("known_limitations",         "TEXT"),
    ("suggested_research_direction", "TEXT"),
    ("suggested_project_direction",  "TEXT"),
    ("emerging_trend",            "VARCHAR(200)"),
    ("evidence_sources",          "JSONB DEFAULT '[]'::jsonb"),
]


def main():
    print("[migrate] adding enrichment columns to opportunities")
    with engine.begin() as conn:
        for name, typ in COLS:
            conn.execute(text(
                f"ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS {name} {typ}"
            ))
            print(f"  + {name:<32} {typ}")
    print("[migrate] done")


if __name__ == "__main__":
    main()
