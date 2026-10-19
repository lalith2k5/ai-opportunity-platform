"""Conflict detection + resolution (spec 28.3, rules CR-1..CR-6)."""
from datetime import datetime, timezone
from app.database import SessionLocal
from app import models
from app.logger import logger


DEFAULT_SOURCE_CREDIBILITY = {
    "arxiv": 0.90,
    "patents": 0.85,
    "challenge_portal": 0.80,
    "rd_cells": 0.75,
    "news": 0.65,
    "github": 0.60,
    "github_issues": 0.60,
    "reddit": 0.40,
}


def source_credibility(source_name):
    return DEFAULT_SOURCE_CREDIBILITY.get((source_name or "").lower(), 0.50)


def _severity(sup_n, con_n):
    if con_n >= sup_n:
        return "MAJOR"
    return "MINOR"


def detect_conflicts_for_opportunity(opp_id, db=None):
    close_here = db is None
    if close_here:
        db = SessionLocal()
    try:
        evs = db.query(models.OpportunityEvidence).filter(
            models.OpportunityEvidence.opportunity_id == opp_id
        ).all()
        if not evs:
            return []
        supports = [e for e in evs if (e.polarity or "SUPPORTS") == "SUPPORTS"]
        contradicts = [e for e in evs if (e.polarity or "SUPPORTS") == "CONTRADICTS"]
        if not contradicts:
            return []

        existing = db.query(models.ConflictFlag).filter(
            models.ConflictFlag.target_type == "OPPORTUNITY",
            models.ConflictFlag.target_id == str(opp_id),
            models.ConflictFlag.resolved_at.is_(None),
        ).first()
        if existing:
            return [existing.id]

        severity = _severity(len(supports), len(contradicts))
        sup_cred = sum(source_credibility(e.source) for e in supports) / max(len(supports), 1)
        con_cred = sum(source_credibility(e.source) for e in contradicts) / max(len(contradicts), 1)
        rule = "CR-2" if abs(sup_cred - con_cred) >= 0.10 else "CR-4"

        flag = models.ConflictFlag(
            target_type="OPPORTUNITY",
            target_id=str(opp_id),
            severity=severity,
            rule_applied=rule,
            evidence_ids=[e.id for e in evs[:20]],
            raised_at=datetime.now(timezone.utc),
        )
        db.add(flag)
        db.commit()
        logger.info("[ConflictDetector] opp=" + str(opp_id) + " severity=" + severity + " rule=" + rule)
        return [flag.id]
    except Exception as e:
        if db:
            db.rollback()
        logger.warning("[ConflictDetector] failed opp=" + str(opp_id) + ": " + str(e))
        return []
    finally:
        if close_here and db:
            db.close()


def sweep_all_opportunities(limit=500):
    db = SessionLocal()
    try:
        opps = db.query(models.Opportunity.id).limit(limit).all()
        raised = 0
        for (oid,) in opps:
            ids = detect_conflicts_for_opportunity(oid, db)
            raised += len(ids)
        return {"scanned": len(opps), "raised": raised}
    finally:
        db.close()
