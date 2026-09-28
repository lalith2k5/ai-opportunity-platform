"""One-shot migration: uppercase existing kg_edges relations.

Uses the LEGACY_RELATION_MAP from app.kg_schema. Idempotent.

Run with:
    cd ~/ai-opportunity-platform/backend
    source venv/bin/activate
    python3 migrate_kg_relations_uppercase.py
"""
from sqlalchemy import text
from app.database import engine
from app.kg_schema import LEGACY_RELATION_MAP


def main():
    print("[migrate] uppercase kg_edges.relation values")
    total = 0
    with engine.begin() as conn:
        for old, new in LEGACY_RELATION_MAP.items():
            if old == new:
                continue
            n = conn.execute(text(
                "UPDATE kg_edges SET relation = :new WHERE relation = :old"
            ), {"new": new, "old": old}).rowcount
            if n:
                print(f"  {old:>22} -> {new:<22} : {n} rows")
                total += n
    print(f"[migrate] done ({total} rows updated)")


if __name__ == "__main__":
    main()
