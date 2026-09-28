"""Researcher + R&D workflow flow endpoints (SRS §25, §26).

Kept in a separate router file so routes.py stays focused on the core
opportunity/pipeline surface. All endpoints are read-only aggregations
over the Phase 1-6 tables.
"""
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app import models
from app.auth.dependencies import get_current_user


router = APIRouter(tags=["workflows"])


@router.get("/researcher/flow")
def researcher_flow(
    topic: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """Researcher workflow (SRS §25).

    topic -> related problem clusters -> best-matching profile ->
    technologies + papers + limitations + gaps + trend + opportunities.
    Returns one chain per cluster so the UI can render the full narrative.
    """
    q = db.query(models.ProblemCluster)
    if topic:
        pat = f"%{topic.lower()}%"
        q = q.filter(or_(
            models.ProblemCluster.title.ilike(pat),
            models.ProblemCluster.description.ilike(pat),
        ))
    clusters = q.order_by(models.ProblemCluster.demand_score.desc()).limit(limit).all()
    if not clusters:
        return {"topic": topic, "chains": []}

    all_profiles = db.query(models.ProblemProfile).all()
    all_techs = db.query(models.ProblemTechnology).all()
    all_papers = db.query(models.ProblemPaper).all()
    all_gaps = db.query(models.ResearchGap).all()
    all_trends = db.query(models.Trend).all()
    all_opps = db.query(models.Opportunity).all()

    techs_by_profile, papers_by_profile = {}, {}
    for t in all_techs:
        techs_by_profile.setdefault(t.problem_profile_id, []).append(t)
    for p in all_papers:
        papers_by_profile.setdefault(p.problem_profile_id, []).append(p)
    gaps_by_cluster = {}
    for g in all_gaps:
        if g.problem_cluster_id:
            gaps_by_cluster.setdefault(g.problem_cluster_id, []).append(g)
    opps_by_cluster = {}
    for o in all_opps:
        if o.problem_cluster_id:
            opps_by_cluster.setdefault(o.problem_cluster_id, []).append(o)

    def best_profile_for_cluster(cluster):
        if not cluster or not cluster.keywords:
            return None
        ck = {str(k).lower() for k in cluster.keywords[:10] if k}
        if not ck:
            return None
        best, best_n = None, 0
        for p in all_profiles:
            pk = {str(k).lower() for k in (p.keywords or [])[:10] if k}
            n = len(ck & pk)
            if n > best_n:
                best, best_n = p, n
        return best

    chains = []
    for c in clusters:
        profile = best_profile_for_cluster(c)
        techs = techs_by_profile.get(profile.id, []) if profile else []
        papers = papers_by_profile.get(profile.id, []) if profile else []
        lims = []
        for p in papers:
            for L in (p.limitations or []):
                s = str(L).strip()
                if s and s not in lims:
                    lims.append(s)

        tnames = [t.technology_name.lower() for t in techs]
        best_trend = None
        for tr in all_trends:
            trn = (tr.name or "").lower()
            if trn and any(trn in t or t in trn for t in tnames):
                if best_trend is None or (tr.trend_score or 0) > (best_trend.trend_score or 0):
                    best_trend = tr

        chains.append({
            "cluster": {
                "id": c.id,
                "title": c.title,
                "description": c.description,
                "keywords": c.keywords or [],
                "demand_score": c.demand_score,
                "source_count": c.source_count,
            },
            "profile": ({
                "id": profile.id,
                "problem_title": profile.problem_title,
                "industry_domain": profile.industry_domain,
                "organization": profile.organization,
            } if profile else None),
            "technologies": [
                {"name": t.technology_name, "stage": t.stage, "confidence": t.confidence}
                for t in techs[:10]
            ],
            "papers": [
                {"title": p.title, "url": p.url, "arxiv_id": p.arxiv_id,
                 "relevance_score": p.relevance_score, "authors": p.authors or []}
                for p in sorted(papers, key=lambda x: -(x.relevance_score or 0))[:10]
            ],
            "limitations": lims[:12],
            "gaps": [
                {"id": g.id, "title": g.title, "description": g.description,
                 "gap_score": g.gap_score}
                for g in sorted(gaps_by_cluster.get(c.id, []),
                                key=lambda x: -(x.gap_score or 0))[:5]
            ],
            "emerging_trend": ({
                "name": best_trend.name, "score": best_trend.trend_score,
            } if best_trend else None),
            "opportunities": [
                {"id": o.id, "title": o.title, "opportunity_score": o.opportunity_score,
                 "feasibility_score": o.feasibility_score,
                 "research_gap_score": o.research_gap_score}
                for o in sorted(opps_by_cluster.get(c.id, []),
                                key=lambda x: -(x.opportunity_score or 0))[:5]
            ],
        })

    return {"topic": topic, "chains": chains}


@router.get("/rd/flow")
def rd_flow(
    industry_problem: Optional[str] = None,
    industry: Optional[str] = None,
    limit: int = 15,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """R&D workflow (SRS §26).

    industry problem -> technology landscape + research landscape +
    emerging trends + innovation opportunities.
    """
    q = db.query(models.ProblemProfile)
    if industry_problem:
        pat = f"%{industry_problem.lower()}%"
        q = q.filter(or_(
            models.ProblemProfile.problem_title.ilike(pat),
            models.ProblemProfile.problem_description.ilike(pat),
        ))
    if industry:
        q = q.filter(models.ProblemProfile.industry_domain == industry)

    profiles = q.order_by(models.ProblemProfile.id.desc()).limit(limit).all()
    if not profiles:
        return {"industry_problem": industry_problem, "industry": industry,
                "profile_count": 0, "technologies": [], "research": [],
                "trends": [], "opportunities": []}

    profile_ids = [p.id for p in profiles]

    tech_rows = (db.query(models.ProblemTechnology)
                 .filter(models.ProblemTechnology.problem_profile_id.in_(profile_ids))
                 .all())
    tech_map = {}
    for t in tech_rows:
        key = t.technology_name
        if key not in tech_map:
            tech_map[key] = {"name": key, "stages": [], "avg_confidence": 0.0,
                             "_n": 0, "_sum": 0.0}
        if t.stage and t.stage not in tech_map[key]["stages"]:
            tech_map[key]["stages"].append(t.stage)
        tech_map[key]["_sum"] += (t.confidence or 0.0)
        tech_map[key]["_n"] += 1
    for v in tech_map.values():
        v["avg_confidence"] = round(v["_sum"] / max(v["_n"], 1), 3)
        del v["_sum"], v["_n"]
    technologies = sorted(tech_map.values(), key=lambda x: -x["avg_confidence"])[:20]

    paper_rows = (db.query(models.ProblemPaper)
                  .filter(models.ProblemPaper.problem_profile_id.in_(profile_ids))
                  .all())
    paper_map = {}
    for p in paper_rows:
        if p.arxiv_id and p.arxiv_id not in paper_map:
            paper_map[p.arxiv_id] = {
                "title": p.title, "url": p.url, "arxiv_id": p.arxiv_id,
                "relevance_score": p.relevance_score,
                "limitations_count": len(p.limitations or []),
            }
    research = sorted(paper_map.values(), key=lambda x: -(x["relevance_score"] or 0))[:20]

    tech_names = {t["name"].lower() for t in technologies}
    all_trends = db.query(models.Trend).all()
    matched_trends = []
    for tr in all_trends:
        trn = (tr.name or "").lower()
        if trn and any(trn in tn or tn in trn for tn in tech_names):
            matched_trends.append({
                "name": tr.name, "category": tr.category,
                "trend_score": tr.trend_score,
            })
    matched_trends.sort(key=lambda x: -(x["trend_score"] or 0))
    matched_trends = matched_trends[:15]

    clusters = db.query(models.ProblemCluster).all()
    cluster_ids_from_profiles = set()
    for p in profiles:
        pk = {str(k).lower() for k in (p.keywords or [])[:10] if k}
        if not pk:
            continue
        for c in clusters:
            ck = {str(k).lower() for k in (c.keywords or [])[:10] if k}
            if len(pk & ck) >= 1:
                cluster_ids_from_profiles.add(c.id)
    opps = (db.query(models.Opportunity)
            .filter(models.Opportunity.problem_cluster_id.in_(list(cluster_ids_from_profiles)))
            .order_by(models.Opportunity.opportunity_score.desc())
            .limit(20).all()) if cluster_ids_from_profiles else []
    opportunities = [
        {"id": o.id, "title": o.title, "opportunity_score": o.opportunity_score,
         "feasibility_score": o.feasibility_score,
         "market_readiness_score": o.market_readiness_score}
        for o in opps
    ]

    return {
        "industry_problem": industry_problem,
        "industry": industry,
        "profile_count": len(profiles),
        "technologies": technologies,
        "research": research,
        "trends": matched_trends,
        "opportunities": opportunities,
    }
