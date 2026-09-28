"""EvidenceAgent — aggregate supporting evidence per opportunity.

For each Opportunity, looks at its linked ProblemCluster keywords and
retrieves top matching RawDocument rows from each source category.
Produces transparent "Opportunity —SUPPORTED_BY→ Evidence" records
(SRS Module 11 / §18).

Design notes:
  - CPU-only: keyword matching against the raw_documents table. No LLM
    calls, no external APIs — safe to run on every pipeline, zero quota.
  - SQL-level filtering via ILIKE keeps memory bounded even with tens of
    thousands of raw docs.
  - Caps: MAX_PER_SOURCE items per source, MAX_TOTAL per opportunity, so
    a single noisy source cannot flood the UI.
  - KG edges (Opportunity -SUPPORTED_BY-> Evidence per SRS §31) are
    deferred to Phase 5 (KG schema alignment).
"""
from sqlalchemy import or_, inspect as _sa_inspect

from app.database import SessionLocal
from app import models
from app.logger import logger


class EvidenceAgent:
    # Source categories queried in order. Include every pipeline source
    # we currently collect from, so any evidence row is attributable.
    SOURCES = [
        "github",
        "github_issues",
        "arxiv",
        "news",
        "rd_cells",
        "patents",
        "challenge_portal",
    ]
    MAX_PER_SOURCE = 3
    MAX_TOTAL = 12
    MIN_KEYWORD_LEN = 2

    @staticmethod
    def _row_id(obj):
        """Return PK of a possibly-detached ORM instance without refresh."""
        ident = _sa_inspect(obj).identity
        if ident:
            return ident[0]
        return obj.__dict__.get("id")

    def _keywords_for(self, cluster) -> list:
        if not cluster or not cluster.keywords:
            return []
        out = []
        for k in cluster.keywords[:8]:
            s = str(k or "").strip().lower()
            if len(s) >= self.MIN_KEYWORD_LEN:
                out.append(s)
        return out

    def _aggregate_one(self, opp_row, db) -> list:
        """Return list of evidence dicts for one opportunity."""
        cluster_id = opp_row.problem_cluster_id
        if not cluster_id:
            return []
        cluster = db.query(models.ProblemCluster).filter(
            models.ProblemCluster.id == cluster_id
        ).first()
        keywords = self._keywords_for(cluster)
        if not keywords:
            return []

        # SQL clause: any keyword matches title OR content
        clauses = []
        for kw in keywords:
            pat = "%" + kw + "%"
            clauses.append(models.RawDocument.title.ilike(pat))
            clauses.append(models.RawDocument.content.ilike(pat))
        clause = or_(*clauses)

        out = []
        for src in self.SOURCES:
            if len(out) >= self.MAX_TOTAL:
                break
            try:
                rows = (
                    db.query(models.RawDocument)
                    .filter(models.RawDocument.source == src)
                    .filter(clause)
                    .filter(models.RawDocument.url.isnot(None))
                    .order_by(models.RawDocument.collected_at.desc())
                    .limit(self.MAX_PER_SOURCE * 3)
                    .all()
                )
            except Exception as e:
                logger.warning(f"[Evidence] query failed for source={src}: {e}")
                continue

            # Rank by keyword hit count within the fetched window
            scored = []
            for d in rows:
                hay = ((d.title or "") + " " + (d.content or "")).lower()
                hits = sum(1 for kw in keywords if kw in hay)
                if hits > 0:
                    scored.append((hits, d))
            scored.sort(key=lambda x: -x[0])

            for hits, d in scored[: self.MAX_PER_SOURCE]:
                rel = round(min(1.0, hits / max(len(keywords), 1)), 3)
                out.append({
                    "source": src,
                    "title": (d.title or "")[:300],
                    "url": (d.url or "")[:500],
                    "relevance_score": rel,
                    "snippet": (d.content or "")[:500],
                })
        return out

    def aggregate_batch(self, opportunities: list) -> list:
        """Return [(opportunity_row, [evidence_dict, ...]), ...] for opps
        that had at least one matching document."""
        if not opportunities:
            return []
        results = []
        db = SessionLocal()
        try:
            for opp in opportunities:
                try:
                    ev = self._aggregate_one(opp, db)
                except Exception as e:
                    logger.warning(f"[Evidence] aggregate failed: {e}")
                    ev = []
                if ev:
                    results.append((opp, ev))
        finally:
            db.close()
        total_rows = sum(len(ev) for _o, ev in results)
        logger.info(
            f"[Evidence] Aggregated {total_rows} evidence rows "
            f"across {len(results)}/{len(opportunities)} opportunities"
        )
        return results
