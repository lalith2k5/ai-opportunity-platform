
"""Technology endpoints (Screen 3 -- "Choose the Technology").

Read-only aggregations across problem_technologies, problem_profiles,
problem_papers, research_gaps, opportunities, trends, and raw_documents.

Design notes:
  - No new tables, no migrations. Pure SELECTs plus in-Python joins.
  - List endpoint preloads every table once -- no N+1 queries.
  - Detail endpoint matches raw_documents by case-insensitive substring,
    min length 3 to avoid noise like "AI", capped 5 per source.
"""
from typing import Optional
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.database import get_db
from app import models
from app.auth.dependencies import get_current_user


router = APIRouter(prefix="/technologies", tags=["technologies"])

MIN_NAME_LEN = 3
MAX_PER_SOURCE = 5


def _avg(values):
    clean = [v for v in values if v is not None]
    if not clean:
        return 0.0
    return round(sum(clean) / len(clean), 3)


def _majority(values):
    counts = {}
    for v in values:
        if v is None:
            continue
        counts[v] = counts.get(v, 0) + 1
    if not counts:
        return None
    return max(counts, key=counts.get)


def _trend_for_tech(db, tech_name):
    tl = tech_name.lower()
    best = None
    best_score = -1.0
    for tr in db.query(models.Trend).all():
        trn = (tr.name or "").lower()
        if not trn:
            continue
        if tl == trn or tl in trn or trn in tl:
            s = tr.trend_score or 0.0
            if s > best_score:
                best = tr
                best_score = s
    return best


def _trend_label(db, trend_name):
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    two_weeks_ago = now - timedelta(days=14)

    recent = db.query(func.avg(models.TrendSnapshot.mention_count)).filter(
        models.TrendSnapshot.trend_name == trend_name,
        models.TrendSnapshot.snapshot_at >= week_ago,
    ).scalar()
    prior = db.query(func.avg(models.TrendSnapshot.mention_count)).filter(
        models.TrendSnapshot.trend_name == trend_name,
        models.TrendSnapshot.snapshot_at >= two_weeks_ago,
        models.TrendSnapshot.snapshot_at < week_ago,
    ).scalar()

    recent = float(recent or 0)
    prior = float(prior or 0)

    if prior == 0 and recent == 0:
        growth, label = 0.0, "no_data"
    elif prior == 0:
        growth = 1.0
        label = "emerging" if recent >= 3 else "new"
    else:
        growth = (recent - prior) / prior
        if growth > 0.5:
            label = "emerging"
        elif growth > 0.2:
            label = "growing"
        elif growth < -0.2:
            label = "declining"
        else:
            label = "stable"

    return {
        "growth_rate": round(growth, 3),
        "recent_avg": round(recent, 2),
        "prior_avg": round(prior, 2),
        "label": label,
    }


@router.get("")
def list_technologies(
    domain: Optional[str] = None,
    stage: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    tech_rows = db.query(models.ProblemTechnology).all()
    if not tech_rows:
        return []

    profiles_by_id = {p.id: p for p in db.query(models.ProblemProfile).all()}

    papers_by_profile = {}
    for pp in db.query(models.ProblemPaper).all():
        papers_by_profile.setdefault(pp.problem_profile_id, []).append(pp)

    buckets = {}
    for t in tech_rows:
        key = (t.technology_name or "").strip()
        if not key:
            continue
        k_low = key.lower()
        b = buckets.setdefault(k_low, {
            "name": key,
            "confidences": [],
            "stages": [],
            "profile_ids": set(),
            "domains": [],
        })
        if t.confidence is not None:
            b["confidences"].append(t.confidence)
        if t.stage:
            b["stages"].append(t.stage)
        b["profile_ids"].add(t.problem_profile_id)
        parent = profiles_by_id.get(t.problem_profile_id)
        if parent and parent.industry_domain:
            b["domains"].append(parent.industry_domain)

    results = []
    for k_low, b in buckets.items():
        if q and q.lower() not in k_low:
            continue
        dom = _majority(b["domains"])
        stg = _majority(b["stages"])
        if domain and dom != domain:
            continue
        if stage and stg != stage:
            continue

        profiles_for_tech = [
            profiles_by_id[pid] for pid in b["profile_ids"] if pid in profiles_by_id
        ]
        paper_count = sum(len(papers_by_profile.get(pid, [])) for pid in b["profile_ids"])

        recent = None
        for p in profiles_for_tech:
            if p.created_at and (recent is None or p.created_at > recent):
                recent = p.created_at

        trend = _trend_for_tech(db, b["name"])
        conf = _avg(b["confidences"])
        source_count = len(b["profile_ids"]) + paper_count
        trend_score = (trend.trend_score if trend else 0.0) or 0.0
        norm_src = min(1.0, source_count / 20.0)
        composite = round(0.35 * conf + 0.35 * norm_src + 0.30 * trend_score, 3)

        desc_bits = []
        if stg:
            desc_bits.append(f"Stage: {stg}")
        if dom:
            desc_bits.append(f"Domain: {dom}")
        if source_count:
            desc_bits.append(f"{source_count} linked signals")

        results.append({
            "name": b["name"],
            "domain": dom,
            "stage": stg,
            "confidence": conf,
            "source_count": source_count,
            "related_problem_count": len(b["profile_ids"]),
            "related_paper_count": paper_count,
            "trend_score": round(trend_score, 3),
            "trend_label": (trend.name if trend else None),
            "recent_activity": recent.isoformat() if recent else None,
            "description": " · ".join(desc_bits),
            "composite_score": composite,
        })

    results.sort(key=lambda x: -x["composite_score"])
    return results[:limit]


@router.get("/{name}")
def technology_detail(
    name: str,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    key = (name or "").strip()
    if not key:
        raise HTTPException(400, "Technology name required")
    k_low = key.lower()

    tech_rows = db.query(models.ProblemTechnology).filter(
        func.lower(models.ProblemTechnology.technology_name) == k_low
    ).all()
    if not tech_rows:
        raise HTTPException(404, f"Technology '{key}' not found")

    profile_ids = list({t.problem_profile_id for t in tech_rows})
    profiles = db.query(models.ProblemProfile).filter(
        models.ProblemProfile.id.in_(profile_ids)
    ).all()

    papers = db.query(models.ProblemPaper).filter(
        models.ProblemPaper.problem_profile_id.in_(profile_ids)
    ).order_by(models.ProblemPaper.relevance_score.desc()).all()

    conf = _avg([t.confidence for t in tech_rows])
    stg = _majority([t.stage for t in tech_rows])
    dom = _majority([p.industry_domain for p in profiles if p.industry_domain])
    all_domains = sorted({p.industry_domain for p in profiles if p.industry_domain})

    profile_kw = set()
    for p in profiles:
        for k in (p.keywords or []):
            if k:
                profile_kw.add(str(k).lower())

    gaps = []
    if profile_kw:
        for g in db.query(models.ResearchGap).all():
            gk = set()
            for k in ((g.evidence or {}).get("keywords") or []):
                if k:
                    gk.add(str(k).lower())
            if len(gk & profile_kw) >= 1:
                gaps.append(g)
    gaps.sort(key=lambda g: -(g.gap_score or 0))
    gaps = gaps[:10]

    cluster_ids = set()
    if profile_kw:
        for c in db.query(models.ProblemCluster).all():
            ck = {str(k).lower() for k in (c.keywords or []) if k}
            if len(ck & profile_kw) >= 2:
                cluster_ids.add(c.id)

    opps = []
    if cluster_ids:
        opps = db.query(models.Opportunity).filter(
            models.Opportunity.problem_cluster_id.in_(list(cluster_ids))
        ).order_by(models.Opportunity.opportunity_score.desc()).limit(15).all()

    raw_matches = {"github": [], "news": [], "reddit": [], "arxiv": [], "patents": [], "rd_cells": []}
    if len(k_low) >= MIN_NAME_LEN:
        pattern = f"%{k_low}%"
        for src in raw_matches.keys():
            rows = db.query(models.RawDocument).filter(
                models.RawDocument.source == src,
                or_(
                    func.lower(models.RawDocument.title).like(pattern),
                    func.lower(models.RawDocument.content).like(pattern),
                ),
            ).order_by(models.RawDocument.collected_at.desc()).limit(MAX_PER_SOURCE).all()
            raw_matches[src] = [
                {
                    "id": r.id,
                    "title": r.title,
                    "url": r.url,
                    "source": r.source,
                    "collected_at": r.collected_at.isoformat() if r.collected_at else None,
                }
                for r in rows
            ]

    trend = _trend_for_tech(db, key)
    trend_block = None
    if trend:
        trend_block = {
            "name": trend.name,
            "trend_score": trend.trend_score,
            "category": trend.category,
            "detected_at": trend.detected_at.isoformat() if trend.detected_at else None,
            **_trend_label(db, trend.name),
        }

    sorted_profiles = sorted(
        profiles,
        key=lambda x: -(x.created_at.timestamp() if x.created_at else 0.0),
    )

    return {
        "technology": {
            "name": key,
            "stage": stg,
            "confidence": conf,
            "domain": dom,
            "domains": all_domains,
            "source_count": len(profile_ids) + len(papers),
            "related_problem_count": len(profile_ids),
            "related_paper_count": len(papers),
            "description": (
                f"{key} appears across {len(profile_ids)} problem profiles "
                f"and {len(papers)} linked research papers."
            ),
        },
        "related_problems": [
            {
                "id": p.id,
                "problem_title": p.problem_title,
                "problem_description": (p.problem_description or "")[:400],
                "industry_domain": p.industry_domain,
                "problem_type": p.problem_type,
                "organization": p.organization,
                "source": p.source,
                "source_url": p.source_url,
                "stage": p.technology_stage,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in sorted_profiles[:20]
        ],
        "related_papers": [
            {
                "id": pp.id,
                "title": pp.title,
                "arxiv_id": pp.arxiv_id,
                "url": pp.url,
                "relevance_score": pp.relevance_score,
                "authors": pp.authors or [],
                "abstract": (pp.abstract or "")[:800],
                "research_methods": pp.research_methods or [],
                "results_summary": pp.results_summary,
                "limitations": pp.limitations or [],
                "research_areas": pp.research_areas or [],
            }
            for pp in papers[:20]
        ],
        "github_repositories": raw_matches["github"],
        "news_articles": raw_matches["news"],
        "reddit_discussions": raw_matches["reddit"],
        "trend": trend_block,
        "potential_gaps": [
            {
                "id": g.id,
                "title": g.title,
                "description": g.description,
                "gap_score": g.gap_score,
            }
            for g in gaps
        ],
        "opportunities": [
            {
                "id": o.id,
                "title": o.title,
                "opportunity_score": o.opportunity_score,
                "feasibility_score": o.feasibility_score,
                "research_gap_score": o.research_gap_score,
                "domain": o.domain,
                "industry": o.industry,
            }
            for o in opps
        ],
        "sources": [
            {"source": m["source"], "title": m["title"], "url": m["url"]}
            for src_list in raw_matches.values()
            for m in src_list
            if m.get("url")
        ][:20],
    }
