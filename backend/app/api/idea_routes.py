
"""Idea (problem cluster) endpoints for Screen 2 -- "Find the Real-Time Ideas".

A "real-time idea" here is a ProblemCluster discovered by the pipeline,
enriched with cross-source evidence, trends, and opportunities.

Read-only, no migrations. Payload shaped to the 9 SRS sections so the
frontend does not need to join anything client-side.
"""
from typing import Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.database import get_db
from app import models
from app.auth.dependencies import get_current_user

try:
    from app.api.research_routes import _normalize_arxiv_id
except Exception:
    def _normalize_arxiv_id(x):
        return x


router = APIRouter(prefix="/ideas", tags=["ideas"])

MIN_KEYWORD_LEN = 3
MAX_PER_SOURCE = 6


def _days_since(ts):
    if ts is None:
        return 999.0
    now = datetime.now(timezone.utc)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return max(0.0, (now - ts).total_seconds() / 86400.0)


def _recency_score(ts):
    d = _days_since(ts)
    if d <= 1:
        return 1.0
    if d <= 7:
        return 0.9
    if d <= 30:
        return 0.6
    if d <= 90:
        return 0.3
    return 0.1


def _keywords_for_cluster(cluster):
    out = []
    for k in (cluster.keywords or []):
        s = str(k or "").strip().lower()
        if len(s) >= MIN_KEYWORD_LEN:
            out.append(s)
    return out[:8]


def _best_trend_for_keywords(db, keywords):
    if not keywords:
        return None
    best = None
    best_score = -1.0
    all_trends = db.query(models.Trend).all()
    for tr in all_trends:
        trn = (tr.name or "").lower()
        if not trn:
            continue
        for kw in keywords:
            if kw == trn or kw in trn or trn in kw:
                s = tr.trend_score or 0.0
                if s > best_score:
                    best = tr
                    best_score = s
                break
    return best


def _best_profile_for_keywords(all_profiles, keywords):
    if not keywords:
        return None
    kset = set(keywords)
    best = None
    best_overlap = 0
    for p in all_profiles:
        pk = {str(k).lower() for k in (p.keywords or [])[:10] if k}
        overlap = len(kset & pk)
        if overlap > best_overlap:
            best = p
            best_overlap = overlap
    return best


def _matched_docs(db, keywords, source, limit=MAX_PER_SOURCE):
    if not keywords:
        return []
    clauses = []
    for kw in keywords:
        pat = f"%{kw}%"
        clauses.append(func.lower(models.RawDocument.title).like(pat))
        clauses.append(func.lower(models.RawDocument.content).like(pat))
    clause = or_(*clauses)
    return db.query(models.RawDocument).filter(
        models.RawDocument.source == source,
    ).filter(clause).order_by(
        models.RawDocument.collected_at.desc()
    ).limit(limit).all()


@router.get("")
def list_ideas(
    domain: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = Query(60, ge=1, le=200),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    clusters = db.query(models.ProblemCluster).all()
    if not clusters:
        return []

    all_opps = db.query(models.Opportunity).all()
    opps_by_cluster = {}
    for o in all_opps:
        if o.problem_cluster_id:
            opps_by_cluster.setdefault(o.problem_cluster_id, []).append(o)

    all_profiles = db.query(models.ProblemProfile).all()

    results = []
    for c in clusters:
        keywords = _keywords_for_cluster(c)
        if q:
            needle = q.lower()
            hay = ((c.title or "") + " " + (c.description or "")).lower()
            if needle not in hay:
                continue

        profile = _best_profile_for_keywords(all_profiles, keywords)
        domain_val = profile.industry_domain if profile else None
        if domain and domain_val != domain:
            continue

        trend = _best_trend_for_keywords(db, keywords)
        trend_score = (trend.trend_score if trend else 0.0) or 0.0

        opps = opps_by_cluster.get(c.id, [])
        top_opp_score = max((o.opportunity_score or 0.0) for o in opps) if opps else 0.0

        recency = _recency_score(c.created_at)
        demand = c.demand_score or 0.0
        src_norm = min(1.0, (c.source_count or 0) / 10.0)

        composite = (
            0.40 * demand
            + 0.20 * trend_score
            + 0.20 * src_norm
            + 0.10 * top_opp_score
            + 0.10 * recency
        )

        results.append({
            "id": c.id,
            "title": c.title,
            "description": c.description,
            "keywords": keywords,
            "domain": domain_val,
            "source_count": c.source_count or 0,
            "demand_score": round(demand, 3),
            "trend_score": round(trend_score, 3),
            "trend_name": trend.name if trend else None,
            "opportunity_count": len(opps),
            "top_opportunity_score": round(top_opp_score, 3),
            "recent_activity": c.created_at.isoformat() if c.created_at else None,
            "composite_score": round(composite, 3),
        })

    results.sort(key=lambda x: -x["composite_score"])
    return results[:limit]


@router.get("/{cluster_id}")
def idea_detail(
    cluster_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    cluster = db.query(models.ProblemCluster).filter(
        models.ProblemCluster.id == cluster_id
    ).first()
    if not cluster:
        raise HTTPException(404, f"Idea {cluster_id} not found")

    keywords = _keywords_for_cluster(cluster)
    all_profiles = db.query(models.ProblemProfile).all()
    profile = _best_profile_for_keywords(all_profiles, keywords)

    techs = []
    if profile:
        rows = db.query(models.ProblemTechnology).filter(
            models.ProblemTechnology.problem_profile_id == profile.id
        ).all()
        techs = [
            {"name": t.technology_name, "stage": t.stage, "confidence": t.confidence}
            for t in rows
        ]

    news_rows = _matched_docs(db, keywords, "news")
    reddit_rows = _matched_docs(db, keywords, "reddit")
    github_rows = _matched_docs(db, keywords, "github") + _matched_docs(db, keywords, "github_issues")
    arxiv_rows = _matched_docs(db, keywords, "arxiv")

    papers = []
    if profile:
        paper_rows = db.query(models.ProblemPaper).filter(
            models.ProblemPaper.problem_profile_id == profile.id
        ).order_by(models.ProblemPaper.relevance_score.desc()).limit(10).all()
        papers = [
            {
                "id": p.id,
                "title": p.title,
                "arxiv_id": _normalize_arxiv_id(p.arxiv_id) if p.arxiv_id else None,
                "url": p.url,
                "relevance_score": p.relevance_score,
                "authors": p.authors or [],
                "results_summary": p.results_summary,
                "limitations": p.limitations or [],
                "research_methods": p.research_methods or [],
            }
            for p in paper_rows
        ]

    gaps = []
    if keywords:
        kset = set(keywords)
        for g in db.query(models.ResearchGap).all():
            gk = set()
            for k in ((g.evidence or {}).get("keywords") or []):
                if k and len(str(k)) >= MIN_KEYWORD_LEN:
                    gk.add(str(k).lower())
            if len(gk & kset) >= 1:
                gaps.append(g)
    gaps.sort(key=lambda g: -(g.gap_score or 0))
    gaps = gaps[:8]

    opps = db.query(models.Opportunity).filter(
        models.Opportunity.problem_cluster_id == cluster_id
    ).order_by(models.Opportunity.opportunity_score.desc()).limit(10).all()

    evidence = []
    if opps:
        ev_rows = db.query(models.OpportunityEvidence).filter(
            models.OpportunityEvidence.opportunity_id == opps[0].id
        ).limit(15).all()
        evidence = [
            {
                "source": e.source,
                "title": e.title,
                "url": e.url,
                "relevance_score": e.relevance_score,
            }
            for e in ev_rows
        ]

    top_opp = opps[0] if opps else None
    suggested = []
    if top_opp:
        if top_opp.suggested_research_direction:
            suggested.append({"kind": "research", "text": top_opp.suggested_research_direction})
        if top_opp.suggested_project_direction:
            suggested.append({"kind": "project", "text": top_opp.suggested_project_direction})
    if not suggested:
        suggested.append({
            "kind": "research",
            "text": "Run a fresh pipeline to generate suggested directions for this cluster.",
        })

    return {
        "idea": {
            "id": cluster.id,
            "title": cluster.title,
            "description": cluster.description,
            "keywords": keywords,
            "source_count": cluster.source_count or 0,
            "demand_score": cluster.demand_score or 0.0,
            "created_at": cluster.created_at.isoformat() if cluster.created_at else None,
            "domain": profile.industry_domain if profile else None,
            "problem_type": profile.problem_type if profile else None,
        },
        "related_technologies": techs[:15],
        "related_news": [
            {
                "id": r.id,
                "title": r.title,
                "url": r.url,
                "collected_at": r.collected_at.isoformat() if r.collected_at else None,
            }
            for r in news_rows
        ],
        "reddit_discussions": [
            {"id": r.id, "title": r.title, "url": r.url} for r in reddit_rows
        ],
        "github_repositories": [
            {"id": r.id, "title": r.title, "url": r.url, "source": r.source}
            for r in github_rows
        ],
        "research_papers": papers if papers else [
            {"id": r.id, "title": r.title, "url": r.url, "source": "arxiv"}
            for r in arxiv_rows
        ],
        "evidence": evidence,
        "potential_gaps": [
            {"id": g.id, "title": g.title, "description": g.description, "gap_score": g.gap_score}
            for g in gaps
        ],
        "opportunities": [
            {
                "id": o.id,
                "title": o.title,
                "opportunity_score": o.opportunity_score,
                "feasibility_score": o.feasibility_score,
            }
            for o in opps
        ],
        "suggested_directions": suggested,
    }
