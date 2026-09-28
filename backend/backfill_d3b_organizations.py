"""Backfill organizations from existing problem_profiles.

Walks every ProblemProfile, groups by canonical_name (lowercase, whitespace
and punctuation normalised), creates Organization rows, and links
problem_profiles.organization_id.

Idempotent. No LLM.
"""
import re

from app.database import SessionLocal
from app import models


_CLEAN = re.compile(r"[^a-z0-9]+")


def canonical(name: str) -> str:
    if not name:
        return ""
    return _CLEAN.sub(" ", name.lower()).strip()


def main():
    db = SessionLocal()
    try:
        profiles = db.query(models.ProblemProfile).all()
        print(f"[d3b] {len(profiles)} profiles to process")

        # Existing organizations by canonical_name
        existing = {
            o.canonical_name: o
            for o in db.query(models.Organization).all()
        }
        print(f"[d3b] {len(existing)} organizations already exist")

        created = 0
        linked = 0
        skipped = 0

        for p in profiles:
            raw = (p.organization or "").strip()
            if not raw or raw.lower() == "unknown":
                skipped += 1
                continue
            cn = canonical(raw)
            if not cn:
                skipped += 1
                continue

            org = existing.get(cn)
            if not org:
                org = models.Organization(
                    name=raw[:300],
                    canonical_name=cn[:200],
                    industry_domain=(p.industry_domain or "")[:120] or None,
                    source=(p.source or "")[:64] or None,
                )
                db.add(org)
                db.flush()
                existing[cn] = org
                created += 1

            if p.organization_id != org.id:
                p.organization_id = org.id
                linked += 1

        db.commit()
        print(f"[d3b] created={created} linked={linked} skipped={skipped}")
        total = db.query(models.Organization).count()
        print(f"[d3b] total organizations now: {total}")
        print("[d3b] DONE")
    finally:
        db.close()


if __name__ == "__main__":
    main()
