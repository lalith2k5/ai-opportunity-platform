"""Unified connector runner: fetch from any source, dedupe, insert to raw_documents."""
from datetime import datetime, timezone
from sqlalchemy import and_
from app.database import SessionLocal
from app import models
from app.logger import logger


REQUIRED_FIELDS = ["source", "external_id", "title", "url", "content",
                   "author", "metadata_json", "collected_at", "processed"]


class ConnectorRunner:
    def __init__(self, dedupe=True):
        self.dedupe = dedupe
        self.stats = {"fetched": 0, "inserted": 0, "skipped_dup": 0,
                      "skipped_invalid": 0, "errors": 0}

    def _validate(self, doc):
        missing = [k for k in REQUIRED_FIELDS if k not in doc]
        if missing:
            logger.warning(f"[Runner] missing fields: {missing}")
            return False
        if not doc.get("url") or not doc.get("external_id"):
            return False
        return True

    def _exists(self, db, source, external_id):
        return db.query(models.RawDocument).filter(
            and_(
                models.RawDocument.source == source,
                models.RawDocument.external_id == external_id,
            )
        ).first() is not None

    def ingest(self, docs, commit=True, verbose=False):
        db = SessionLocal()
        try:
            for d in docs:
                self.stats["fetched"] += 1
                if not self._validate(d):
                    self.stats["skipped_invalid"] += 1
                    continue
                if self.dedupe and self._exists(db, d["source"], d["external_id"]):
                    self.stats["skipped_dup"] += 1
                    if verbose:
                        logger.info(f"[Runner] dup skipped: {d['source']}:{d['external_id']}")
                    continue
                try:
                    row = models.RawDocument(
                        source=d["source"],
                        external_id=str(d["external_id"])[:500],
                        title=(d.get("title") or "")[:500],
                        content=(d.get("content") or "")[:8000],
                        url=(d.get("url") or "")[:500],
                        author=(d.get("author") or "")[:200],
                        metadata_json=d.get("metadata_json") or {},
                        collected_at=d.get("collected_at") or datetime.now(timezone.utc),
                        processed=False,
                    )
                    db.add(row)
                    db.flush()
                    self.stats["inserted"] += 1
                    if verbose:
                        logger.info(f"[Runner] inserted: {row.source}:{row.external_id} -> id={row.id}")
                except Exception as e:
                    self.stats["errors"] += 1
                    logger.warning(f"[Runner] insert error: {e}")
            if commit:
                db.commit()
            else:
                db.rollback()
        finally:
            db.close()
        return self.stats

    def run_source(self, service, method, *args, commit=True, verbose=False, **kwargs):
        """Fetch via any service.method(...) then ingest."""
        try:
            fn = getattr(service, method, None)
            if not callable(fn):
                logger.error(f"[Runner] {type(service).__name__}.{method} not callable")
                return self.stats
            docs = fn(*args, **kwargs) or []
            return self.ingest(docs, commit=commit, verbose=verbose)
        except Exception as e:
            logger.error(f"[Runner] source run failed: {e}")
            self.stats["errors"] += 1
            return self.stats


def register_data_sources():
    """Idempotent -- ensure the 4 new connectors are in data_sources."""
    NEW = [
        {"name": "hackernews", "type": "community"},
        {"name": "openalex", "type": "research papers"},
        {"name": "crossref", "type": "research papers"},
        {"name": "gdelt", "type": "news feeds"},
    ]
    db = SessionLocal()
    try:
        added = []
        for src in NEW:
            exists = db.query(models.DataSource).filter(
                models.DataSource.name == src["name"]
            ).first()
            if not exists:
                row = models.DataSource(name=src["name"], type=src["type"])
                db.add(row)
                added.append(src["name"])
        db.commit()
        return added
    finally:
        db.close()
