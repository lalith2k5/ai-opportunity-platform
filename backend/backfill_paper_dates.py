
"""Backfill ProblemPaper.published from arxiv_id prefix.

ZERO API calls, ZERO LLM. Derives the year from the arxiv_id (YYMM.NNNNN).
Skips papers that already have a published value.
"""
from app.database import SessionLocal
from app import models
from app.agents.research_gap import ResearchGapAgent  # noqa: F401  (ensures imports load)


def year_from_arxiv_id(aid):
    if not aid:
        return None
    s = aid.strip()
    for prefix in ("http://arxiv.org/abs/", "https://arxiv.org/abs/"):
        if s.startswith(prefix):
            s = s[len(prefix):]
            break
    s = s.lstrip("/")
    if len(s) < 4 or "." not in s:
        return None
    yymm = s[:4]
    if not yymm.isdigit():
        return None
    yy = int(yymm[:2])
    full = 1900 + yy if yy >= 91 else 2000 + yy
    return full


def main():
    db = SessionLocal()
    try:
        rows = db.query(models.ProblemPaper).all()
        touched = 0
        skipped = 0
        no_id = 0
        print(f"[dates] {len(rows)} papers total")
        for p in rows:
            if p.published:
                skipped += 1
                continue
            y = year_from_arxiv_id(p.arxiv_id)
            if y is None:
                no_id += 1
                continue
            p.published = f"{y}-01-01"
            touched += 1
        db.commit()
        print(f"[dates] updated={touched} skipped={skipped} no_id={no_id}")
        print("[dates] DONE")
    finally:
        db.close()


if __name__ == "__main__":
    main()
