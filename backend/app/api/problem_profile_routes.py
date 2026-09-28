"""Endpoints for the structured Problem Profile feature.

Problem profiles are extracted by ProblemExtractorAgent from challenge
portals (SBIR, challenge.gov) and represent industry/gov problem statements.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app import models
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/problem-profiles", tags=["problem-profiles"])


@router.get("")
def list_profiles(
    domain: Optional[str] = None,
    problem_type: Optional[str] = None,
    student_suitability: Optional[str] = None,
    source: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """List structured problem profiles with optional filters."""
    q = db.query(models.ProblemProfile)
    if domain:
        q = q.filter(models.ProblemProfile.industry_domain == domain)
    if problem_type:
        q = q.filter(models.ProblemProfile.problem_type == problem_type)
    if student_suitability:
        q = q.filter(models.ProblemProfile.student_suitability == student_suitability)
    if source:
        q = q.filter(models.ProblemProfile.source == source)
    if search:
        like = f"%{search}%"
        q = q.filter(
            models.ProblemProfile.problem_title.ilike(like)
            | models.ProblemProfile.problem_description.ilike(like)
            | models.ProblemProfile.organization.ilike(like)
        )

    total = q.count()
    rows = q.order_by(models.ProblemProfile.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "items": [
            {
                "id": r.id,
                "organization": r.organization,
                "problem_title": r.problem_title,
                "problem_description": r.problem_description,
                "industry_domain": r.industry_domain,
                "problem_type": r.problem_type,
                "technology_stage": r.technology_stage,
                "required_technology": r.required_technology or [],
                "current_approach": r.current_approach,
                "known_limitations": r.known_limitations,
                "expected_outcome": r.expected_outcome,
                "source": r.source,
                "source_url": r.source_url,
                "keywords": r.keywords or [],
                "problem_status": r.problem_status,
                "student_suitability": r.student_suitability,
                "extracted_by": r.extracted_by,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
    }


@router.get("/stats")
def profile_stats(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """Counts by domain, suitability, source — for the frontend header."""
    by_domain = dict(
        db.query(models.ProblemProfile.industry_domain, func.count(models.ProblemProfile.id))
        .group_by(models.ProblemProfile.industry_domain).all()
    )
    by_suitability = dict(
        db.query(models.ProblemProfile.student_suitability, func.count(models.ProblemProfile.id))
        .group_by(models.ProblemProfile.student_suitability).all()
    )
    by_source = dict(
        db.query(models.ProblemProfile.source, func.count(models.ProblemProfile.id))
        .group_by(models.ProblemProfile.source).all()
    )
    total = db.query(models.ProblemProfile).count()
    return {
        "total": total,
        "by_domain": by_domain,
        "by_suitability": by_suitability,
        "by_source": by_source,
    }


@router.get("/{profile_id}")
def get_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    r = db.query(models.ProblemProfile).filter(models.ProblemProfile.id == profile_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Problem profile not found")
    return {
        "id": r.id,
        "organization": r.organization,
        "problem_title": r.problem_title,
        "problem_description": r.problem_description,
        "industry_domain": r.industry_domain,
        "problem_type": r.problem_type,
        "technology_stage": r.technology_stage,
        "required_technology": r.required_technology or [],
        "current_approach": r.current_approach,
        "known_limitations": r.known_limitations,
        "expected_outcome": r.expected_outcome,
        "source": r.source,
        "source_url": r.source_url,
        "keywords": r.keywords or [],
        "problem_status": r.problem_status,
        "student_suitability": r.student_suitability,
        "extracted_by": r.extracted_by,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }
