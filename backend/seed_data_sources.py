"""Seed the data_sources table with the 7 known pipeline sources (FR-01).

Idempotent -- uses name as the natural key.
"""
from app.database import SessionLocal
from app import models


SEEDS = [
    ("github",           "repo + issues"),
    ("arxiv",            "research papers"),
    ("news",             "RSS news feeds"),
    ("rd_cells",         "R&D lab feeds"),
    ("challenge_portal", "gov challenges"),
    ("patents",          "PatentsView"),
    ("reddit",           "community posts"),
]


def main():
    db = SessionLocal()
    try:
        existing = {r.name for r in db.query(models.DataSource).all()}
        created = 0
        for name, source_type in SEEDS:
            if name in existing:
                continue
            db.add(models.DataSource(
                name=name,
                source_type=source_type,
                is_active=True,
            ))
            created += 1
        db.commit()
        total = db.query(models.DataSource).count()
        print(f"[seed] created={created} total={total}")
        print("[seed] DONE")
    finally:
        db.close()


if __name__ == "__main__":
    main()
