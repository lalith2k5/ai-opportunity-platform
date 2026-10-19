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


# ============================================================
# Spec 38.5 / FR-32: reproducibility manifest
# ============================================================
import json as _json
from datetime import datetime as _datetime
import hashlib as _hashlib
import subprocess as _subprocess


@router.get("/reproducibility-manifest")
def reproducibility_manifest(
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "reviewer")),
):
    """Return a full configuration fingerprint. Any two manifests with the
    same sha256 hash describe the same computation environment."""
    weights = db.query(models.WeightConfig).order_by(models.WeightConfig.id).all()
    confs = db.query(models.ConfidenceConfig).order_by(models.ConfidenceConfig.id).all()
    trends = db.query(models.TrendConfig).order_by(models.TrendConfig.id).all()

    def _wf(w):
        return {
            "version": w.version,
            "w_problem": w.w_problem, "w_tech": w.w_tech, "w_gap": w.w_gap,
            "w_trend": w.w_trend, "w_evidence": w.w_evidence,
            "w_feasibility": w.w_feasibility, "w_recency": w.w_recency,
            "is_active": bool(w.is_active),
            "published_at": w.published_at.isoformat() if w.published_at else None,
        }

    def _cf(c):
        return {
            "version": c.version,
            "beta1": c.beta1, "beta2": c.beta2, "beta3": c.beta3, "beta4": c.beta4,
            "n_max": c.n_max, "d_max": c.d_max,
            "conflict_penalty": c.conflict_penalty,
            "is_active": bool(c.is_active),
            "published_at": c.published_at.isoformat() if c.published_at else None,
        }

    def _tf(t):
        return {
            "version": t.version,
            "window_short": t.window_short, "window_mid": t.window_mid,
            "window_long": t.window_long,
            "emerging_threshold": t.emerging_threshold,
            "growing_threshold": t.growing_threshold,
            "declining_threshold": t.declining_threshold,
            "default_window": t.default_window,
            "is_active": bool(t.is_active),
            "published_at": t.published_at.isoformat() if t.published_at else None,
        }

    weight_payload = [_wf(w) for w in weights]
    conf_payload = [_cf(c) for c in confs]
    trend_payload = [_tf(t) for t in trends]

    try:
        from app.config import settings as _s
        models_payload = {
            "gemini": _s.GEMINI_MODEL,
            "openrouter": _s.OPENROUTER_MODEL,
            "openai": _s.OPENAI_MODEL,
            "anthropic": _s.ANTHROPIC_MODEL,
            "embedding": _s.EMBEDDING_MODEL,
            "llm_primary": _s.LLM_PRIMARY_PROVIDER,
            "license_gate_enforce": bool(getattr(_s, "LICENSE_GATE_ENFORCE", False)),
        }
    except Exception:
        models_payload = {}

    try:
        git_sha = _subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=".", stderr=_subprocess.DEVNULL, timeout=5,
        ).decode("utf-8", "replace").strip()
    except Exception:
        git_sha = None

    fingerprint_payload = {
        "weight_configs": weight_payload,
        "confidence_configs": conf_payload,
        "trend_configs": trend_payload,
        "models": models_payload,
    }
    canonical = _json.dumps(fingerprint_payload, sort_keys=True, default=str).encode("utf-8")
    sha = _hashlib.sha256(canonical).hexdigest()

    return {
        "manifest_version": "1.0",
        "git_sha": git_sha,
        "computed_at": _datetime.utcnow().isoformat() + "Z",
        "weight_configs": weight_payload,
        "confidence_configs": conf_payload,
        "trend_configs": trend_payload,
        "models": models_payload,
        "fingerprint_sha256": sha,
    }
