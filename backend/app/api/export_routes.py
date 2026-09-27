import json
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.auth.dependencies import get_current_user, require_role

router = APIRouter(prefix="/export", tags=["export"])


def _serialize_opportunity(o):
    return {
        "id": o.id,
        "title": o.title,
        "description": o.description,
        "opportunity_score": o.opportunity_score,
        "confidence_score": o.confidence_score,
        "demand_score": o.demand_score,
        "research_gap_score": o.research_gap_score,
        "trend_score": o.trend_score,
        "competition_score": o.competition_score,
        "feasibility_score": o.feasibility_score,
        "market_readiness_score": o.market_readiness_score,
        "explanation": o.explanation,
        "problem_cluster_id": o.problem_cluster_id,
        "research_gap_id": o.research_gap_id,
        "created_at": o.created_at.isoformat() if o.created_at else None,
    }


def _serialize_cluster(c):
    return {
        "id": c.id,
        "title": c.title,
        "description": c.description,
        "keywords": c.keywords or [],
        "source_count": c.source_count,
        "demand_score": c.demand_score,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


def _serialize_gap(g):
    return {
        "id": g.id,
        "title": g.title,
        "description": g.description,
        "gap_score": g.gap_score,
        "evidence": g.evidence or {},
        "problem_cluster_id": g.problem_cluster_id,
        "created_at": g.created_at.isoformat() if g.created_at else None,
    }


def _serialize_trend(t):
    return {
        "id": t.id,
        "name": t.name,
        "category": t.category,
        "trend_score": t.trend_score,
        "source_data": t.source_data or {},
        "detected_at": t.detected_at.isoformat() if t.detected_at else None,
    }


def _json_response(payload, filename: str) -> Response:
    body = json.dumps(payload, indent=2, default=str)
    return Response(
        content=body,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/opportunities.json")
def export_opportunities(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    rows = db.query(models.Opportunity).order_by(models.Opportunity.opportunity_score.desc()).all()
    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "count": len(rows),
        "opportunities": [_serialize_opportunity(r) for r in rows],
    }
    return _json_response(payload, f"opportunities_{datetime.now().strftime('%Y%m%d_%H%M')}.json")


@router.get("/research-gaps.json")
def export_gaps(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    rows = db.query(models.ResearchGap).order_by(models.ResearchGap.gap_score.desc()).all()
    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "count": len(rows),
        "research_gaps": [_serialize_gap(r) for r in rows],
    }
    return _json_response(payload, f"research_gaps_{datetime.now().strftime('%Y%m%d_%H%M')}.json")


@router.get("/full.json")
def export_full(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    opportunities = db.query(models.Opportunity).order_by(models.Opportunity.opportunity_score.desc()).all()
    clusters = db.query(models.ProblemCluster).order_by(models.ProblemCluster.demand_score.desc()).all()
    gaps = db.query(models.ResearchGap).order_by(models.ResearchGap.gap_score.desc()).all()
    trends = db.query(models.Trend).order_by(models.Trend.trend_score.desc()).all()
    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "summary": {
            "opportunities": len(opportunities),
            "problem_clusters": len(clusters),
            "research_gaps": len(gaps),
            "trends": len(trends),
        },
        "opportunities": [_serialize_opportunity(r) for r in opportunities],
        "problem_clusters": [_serialize_cluster(r) for r in clusters],
        "research_gaps": [_serialize_gap(r) for r in gaps],
        "trends": [_serialize_trend(r) for r in trends],
    }
    return _json_response(payload, f"full_export_{datetime.now().strftime('%Y%m%d_%H%M')}.json")


@router.get("/opportunities.jsonl")
def export_opportunities_jsonl(
    db: Session = Depends(get_db),
    _=Depends(require_role("admin")),
):
    """Newline-delimited JSON — streamable format for data pipelines."""
    rows = db.query(models.Opportunity).order_by(models.Opportunity.opportunity_score.desc()).all()
    lines = [json.dumps(_serialize_opportunity(r), default=str) for r in rows]
    body = "\n".join(lines)
    return Response(
        content=body,
        media_type="application/x-ndjson",
        headers={"Content-Disposition": f'attachment; filename="opportunities_{datetime.now().strftime("%Y%m%d_%H%M")}.jsonl"'},
    )
