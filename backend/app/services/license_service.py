"""License gate service -- spec 6.7, FR-27, Module 1."""
from functools import wraps
from datetime import datetime, timezone

from app.config import settings
from app.database import SessionLocal
from app import models
from app.logger import logger


def list_licenses():
    db = SessionLocal()
    try:
        rows = db.query(models.LicenseRecord).order_by(models.LicenseRecord.source_name).all()
        return [
            {
                "source_name": r.source_name,
                "status": r.status,
                "terms_url": r.terms_url,
                "robots_policy": r.robots_policy,
                "redistribution": r.redistribution,
                "pii_rules": r.pii_rules,
                "retention_days": r.retention_days,
                "legal_basis": r.legal_basis,
                "next_review_at": r.next_review_at.isoformat() if r.next_review_at else None,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]
    finally:
        db.close()


def get_blocked_source_names():
    db = SessionLocal()
    try:
        rows = db.query(models.LicenseRecord).all()
        if not rows:
            return set()
        now = datetime.now(timezone.utc)
        blocked = set()
        for r in rows:
            status = (r.status or "").upper()
            if status != "APPROVED":
                blocked.add(r.source_name)
                continue
            if r.next_review_at is not None:
                ts = r.next_review_at
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if ts < now:
                    blocked.add(r.source_name)
        return blocked
    finally:
        db.close()


def enforce_license_gate(fn):
    @wraps(fn)
    def wrapper(self, *args, **kwargs):
        if getattr(settings, "LICENSE_GATE_ENFORCE", False):
            blocked = get_blocked_source_names()
            if blocked:
                msg = (
                    "License gate blocked collection. Sources not APPROVED or "
                    "expired: " + ", ".join(sorted(blocked)) +
                    ". Approve them at PATCH /api/admin/license/{source_name} "
                    "or unset LICENSE_GATE_ENFORCE."
                )
                logger.error(f"[LicenseGate] {msg}")
                raise RuntimeError(msg)
        return fn(self, *args, **kwargs)
    return wrapper


def set_license_status(source_name, status, next_review_at=None, legal_basis=None):
    status = (status or "").upper()
    if status not in ("APPROVED", "PENDING", "REJECTED"):
        raise ValueError("status must be APPROVED / PENDING / REJECTED")
    db = SessionLocal()
    try:
        row = db.query(models.LicenseRecord).filter(
            models.LicenseRecord.source_name == source_name
        ).first()
        if not row:
            row = models.LicenseRecord(source_name=source_name)
            db.add(row)
        row.status = status
        if next_review_at:
            try:
                ts = datetime.fromisoformat(next_review_at.replace("Z", "+00:00"))
                row.next_review_at = ts
            except Exception:
                pass
        if legal_basis:
            row.legal_basis = legal_basis[:200]
        db.commit()
        return {"source_name": source_name, "status": status}
    finally:
        db.close()
