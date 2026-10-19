"""Evaluation metrics endpoint (spec 38, FR-30). Read-only."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app import models
from app.auth.dependencies import require_role


router = APIRouter(prefix="/admin/evaluation", tags=["admin-evaluation"])


def _percentiles(values):
    if not values:
        return {"min": 0, "max": 0, "mean": 0, "p50": 0, "p90": 0}
    vs = sorted(values)
    n = len(vs)
    return {
        "min": round(vs[0], 2),
        "max": round(vs[-1], 2),
        "mean": round(sum(vs) / n, 2),
        "p50": round(vs[n // 2], 2),
        "p90": round(vs[min(n - 1, int(n * 0.9))], 2),
    }


@router.get("/metrics")
def evaluation_metrics(
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "reviewer")),
):
    opp_total = db.query(models.Opportunity).count()
    scores = [o.opportunity_score_spec for o in db.query(models.Opportunity).all() if o.opportunity_score_spec is not None]
    confs = [o.confidence_spec for o in db.query(models.Opportunity).all() if o.confidence_spec is not None]

    gap_total = db.query(models.ResearchGap).count()
    gap_status_counts = dict(
        db.query(models.ResearchGap.gap_status, func.count(models.ResearchGap.id))
        .group_by(models.ResearchGap.gap_status).all()
    )
    gap_kind_counts = dict(
        db.query(models.ResearchGap.kind, func.count(models.ResearchGap.id))
        .group_by(models.ResearchGap.kind).all()
    )

    ev_total = db.query(models.OpportunityEvidence).count()
    ev_with_source = db.query(models.OpportunityEvidence).filter(
        models.OpportunityEvidence.source.isnot(None)
    ).count()

    fb_count = db.query(models.Feedback).count()
    cf_open = db.query(models.ConflictFlag).filter(models.ConflictFlag.resolved_at.is_(None)).count()
    cf_total = db.query(models.ConflictFlag).count()
    ce_count = db.query(models.ChangeEvent).count()

    return {
        "opportunities": {
            "total": opp_total,
            "score_spec": _percentiles(scores),
            "confidence_spec": _percentiles(confs),
        },
        "research_gaps": {
            "total": gap_total,
            "by_status": {str(k or "PROPOSED"): v for k, v in gap_status_counts.items()},
            "by_kind": {str(k or "COVERAGE"): v for k, v in gap_kind_counts.items()},
        },
        "provenance": {
            "evidence_total": ev_total,
            "evidence_with_source": ev_with_source,
            "completeness_pct": round(100.0 * ev_with_source / ev_total, 2) if ev_total else 100.0,
        },
        "validation": {
            "feedback_total": fb_count,
            "gaps_validated": gap_status_counts.get("VALIDATED", 0),
            "gaps_under_review": gap_status_counts.get("UNDER_REVIEW", 0),
        },
        "conflicts": {
            "open": cf_open,
            "total_raised": cf_total,
        },
        "change_events_total": ce_count,
        "reproducibility": {
            "weight_config_versions": [r.version for r in db.query(models.WeightConfig).all()],
            "confidence_config_versions": [r.version for r in db.query(models.ConfidenceConfig).all()],
            "trend_config_versions": [r.version for r in db.query(models.TrendConfig).all()],
        },
    }


@router.post("/conflict-sweep")
def conflict_sweep(
    _=Depends(require_role("admin")),
):
    from app.services.conflict_detector import sweep_all_opportunities
    return sweep_all_opportunities(limit=500)
