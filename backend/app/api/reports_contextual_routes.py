
"""Contextual PDF report endpoint.

    GET /api/reports/pdf/{kind}/{id}

kind is one of: opportunity | idea | technology | research | rd
id is:
    opportunity -> integer
    idea        -> integer (problem_cluster.id)
    technology  -> URL-encoded technology name
    research    -> URL-encoded arxiv_id (bare or full URL)
    rd          -> integer (problem_profile.id)

Reuses PDFReportService with a new sectioned-report renderer.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.auth.dependencies import get_current_user
from app.services.pdf_service import PDFReportService


router = APIRouter(prefix="/reports", tags=["reports"])


MAX_SECTION_ITEMS = 15
MAX_ITEM_LEN = 800


def _clip(items, n=MAX_SECTION_ITEMS):
    out = []
    for it in (items or [])[:n]:
        s = str(it).strip()
        if not s:
            continue
        if len(s) > MAX_ITEM_LEN:
            s = s[:MAX_ITEM_LEN].rstrip() + "..."
        out.append(s)
    return out


def _safe_num(v, default=0.0):
    try:
        return float(v)
    except Exception:
        return default


def _profile_for_keywords(db, keywords):
    if not keywords:
        return None
    kset = set(str(k).lower() for k in keywords[:10] if k)
    if not kset:
        return None
    best, best_n = None, 0
    for p in db.query(models.ProblemProfile).all():
        pk = set(str(k).lower() for k in (p.keywords or [])[:10] if k)
        n = len(kset & pk)
        if n > best_n:
            best, best_n = p, n
    return best


def _build_opportunity(db, id_str):
    try:
        oid = int(id_str)
    except Exception:
        raise HTTPException(400, "opportunity id must be an integer")
    opp = db.query(models.Opportunity).filter(models.Opportunity.id == oid).first()
    if not opp:
        raise HTTPException(404, "Opportunity not found")

    title = opp.title or "Opportunity"
    subtitle = (
        f"Opportunity #{opp.id} | Score {_safe_num(opp.opportunity_score):.2f} | "
        f"Confidence {_safe_num(opp.confidence_score):.2f}"
    )
    sections = []
    sections.append(("Overview", _clip([opp.description or "No description provided."], 1)))
    sections.append(("Scoring breakdown", [
        f"Demand: {_safe_num(opp.demand_score):.2f}",
        f"Research gap: {_safe_num(opp.research_gap_score):.2f}",
        f"Trend: {_safe_num(opp.trend_score):.2f}",
        f"Feasibility: {_safe_num(opp.feasibility_score):.2f}",
        f"Market readiness: {_safe_num(opp.market_readiness_score):.2f}",
        f"Technology suitability: {_safe_num(opp.technology_suitability_score):.2f}",
        f"Evidence strength: {_safe_num(opp.evidence_strength_score):.2f}",
        f"Recency: {_safe_num(opp.recency_score):.2f}",
    ]))
    if opp.explanation:
        sections.append(("AI explanation", _clip([opp.explanation], 1)))
    if opp.related_technologies:
        sections.append(("Related technologies", _clip(opp.related_technologies, 15)))
    if opp.existing_research:
        sections.append(("Existing research", _clip(opp.existing_research, 12)))
    if opp.existing_approaches:
        sections.append(("Existing approaches", _clip([opp.existing_approaches], 1)))
    if opp.known_limitations:
        lims = [x.strip() for x in str(opp.known_limitations).split(" | ") if x.strip()]
        if lims:
            sections.append(("Known limitations", _clip(lims, 10)))
    if opp.suggested_research_direction:
        sections.append(("Suggested research direction", _clip([opp.suggested_research_direction], 1)))
    if opp.suggested_project_direction:
        sections.append(("Suggested project direction", _clip([opp.suggested_project_direction], 1)))
    if opp.evidence_sources:
        items = []
        for e in list(opp.evidence_sources)[:12]:
            src = (e or {}).get("source", "?")
            ttl = ((e or {}).get("title") or "")[:120]
            url = (e or {}).get("url") or ""
            items.append(f"[{src}] {ttl} -- {url}")
        sections.append(("Evidence sources", _clip(items, 12)))
    return title, subtitle, sections


def _build_idea(db, id_str):
    try:
        iid = int(id_str)
    except Exception:
        raise HTTPException(400, "idea id must be an integer")
    c = db.query(models.ProblemCluster).filter(models.ProblemCluster.id == iid).first()
    if not c:
        raise HTTPException(404, "Idea not found")

    keywords = [str(k).strip().lower() for k in (c.keywords or []) if k and len(str(k)) >= 3][:10]
    profile = _profile_for_keywords(db, keywords)
    description = c.description or ""
    if profile and profile.problem_description and len(profile.problem_description) > len(description):
        description = profile.problem_description

    title = c.title or "Idea"
    subtitle = (
        f"Idea #{c.id} | Demand {_safe_num(c.demand_score):.2f} | "
        f"{int(c.source_count or 0)} sources"
    )
    sections = []
    sections.append(("Problem statement", _clip([description], 1)))
    if keywords:
        sections.append(("Keywords", _clip(keywords, 10)))

    if profile:
        techs = db.query(models.ProblemTechnology).filter(
            models.ProblemTechnology.problem_profile_id == profile.id
        ).all()
        if techs:
            items = [f"{t.technology_name} ({t.stage or 'potential'})" for t in techs[:15]]
            sections.append(("Related technologies", _clip(items, 15)))
        papers = db.query(models.ProblemPaper).filter(
            models.ProblemPaper.problem_profile_id == profile.id
        ).order_by(models.ProblemPaper.relevance_score.desc()).limit(10).all()
        if papers:
            items = [f"{p.title} (rel {_safe_num(p.relevance_score):.2f})" for p in papers]
            sections.append(("Research papers", _clip(items, 10)))

    opps = db.query(models.Opportunity).filter(
        models.Opportunity.problem_cluster_id == c.id
    ).order_by(models.Opportunity.opportunity_score.desc()).limit(10).all()
    if opps:
        items = [f"{o.title} (score {_safe_num(o.opportunity_score):.2f})" for o in opps]
        sections.append(("Related opportunities", _clip(items, 10)))

    if keywords:
        clauses = []
        for kw in keywords:
            pat = f"%{kw}%"
            clauses.append(models.RawDocument.title.ilike(pat))
            clauses.append(models.RawDocument.content.ilike(pat))
        from sqlalchemy import or_
        clause = or_(*clauses)
        for src in ("github", "news", "arxiv"):
            rows = db.query(models.RawDocument).filter(
                models.RawDocument.source == src,
            ).filter(clause).order_by(
                models.RawDocument.collected_at.desc()
            ).limit(6).all()
            if rows:
                items = [f"{r.title} -- {r.url}" for r in rows]
                sections.append((f"Recent {src} signals", _clip(items, 6)))
    return title, subtitle, sections


def _build_technology(db, name):
    key = (name or "").strip()
    if not key:
        raise HTTPException(400, "technology name required")
    k_low = key.lower()
    tech_rows = db.query(models.ProblemTechnology).filter(
        models.ProblemTechnology.technology_name.ilike(k_low)
    ).all()
    if not tech_rows:
        raise HTTPException(404, "Technology not found")

    profile_ids = list({t.problem_profile_id for t in tech_rows})
    profiles = db.query(models.ProblemProfile).filter(
        models.ProblemProfile.id.in_(profile_ids)
    ).all()
    papers = db.query(models.ProblemPaper).filter(
        models.ProblemPaper.problem_profile_id.in_(profile_ids)
    ).order_by(models.ProblemPaper.relevance_score.desc()).limit(15).all()

    title = key
    subtitle = (
        f"Technology | {len(profile_ids)} linked problems | "
        f"{len(papers)} linked papers"
    )
    sections = []
    desc = f"{key} appears in {len(profile_ids)} problem profiles and {len(papers)} research papers."
    sections.append(("Overview", [desc]))
    if profiles:
        items = [f"{p.problem_title} ({p.industry_domain or 'Other'})" for p in profiles[:12]]
        sections.append(("Related problems", _clip(items, 12)))
    if papers:
        items = [f"{pp.title} (rel {_safe_num(pp.relevance_score):.2f})" for pp in papers]
        sections.append(("Related papers", _clip(items, 12)))
    if tech_rows:
        stages = {}
        for t in tech_rows:
            stages.setdefault(t.stage or "potential", 0)
            stages[t.stage or "potential"] += 1
        items = [f"{k}: {v}" for k, v in stages.items()]
        sections.append(("Stage distribution", _clip(items, 6)))
    return title, subtitle, sections


def _normalize_arxiv(raw):
    s = (raw or "").strip()
    for pre in ("http://arxiv.org/abs/", "https://arxiv.org/abs/"):
        if s.startswith(pre):
            s = s[len(pre):]
            break
    import re
    s = re.sub(r"v\d+$", "", s)
    return s.strip("/")


def _build_research(db, aid):
    key = _normalize_arxiv(aid)
    rows = []
    for candidate in {key, aid, "http://arxiv.org/abs/" + key, "https://arxiv.org/abs/" + key}:
        rows = db.query(models.ProblemPaper).filter(
            models.ProblemPaper.arxiv_id == candidate
        ).all()
        if rows:
            break
    if not rows:
        raise HTTPException(404, "Paper not found")

    p = rows[0]
    title = p.title or "Research paper"
    subtitle = f"arXiv:{key} | Relevance {_safe_num(p.relevance_score):.2f}"
    sections = []
    if p.authors:
        sections.append(("Authors", _clip(p.authors, 20)))
    if p.abstract:
        sections.append(("Abstract", _clip([p.abstract], 1)))
    if p.research_methods:
        sections.append(("Methodology", _clip(p.research_methods, 10)))
    if p.results_summary:
        sections.append(("Key findings", _clip([p.results_summary], 1)))
    if p.limitations:
        sections.append(("Limitations", _clip(p.limitations, 10)))
    if p.research_areas:
        sections.append(("Research areas", _clip(p.research_areas, 10)))
    if p.url:
        sections.append(("Original source", [p.url]))
    return title, subtitle, sections


def _build_rd(db, id_str):
    try:
        pid = int(id_str)
    except Exception:
        raise HTTPException(400, "profile id must be an integer")
    profile = db.query(models.ProblemProfile).filter(
        models.ProblemProfile.id == pid
    ).first()
    if not profile:
        raise HTTPException(404, "Problem profile not found")

    title = profile.problem_title or "Industry problem"
    subtitle = (
        f"R&D problem #{profile.id} | {profile.industry_domain or 'Other'} | "
        f"Source: {profile.source or 'unknown'}"
    )
    sections = []
    sections.append(("Problem statement", _clip([profile.problem_description or "No description."], 1)))
    if profile.current_approach:
        sections.append(("Current approach", _clip([profile.current_approach], 1)))
    if profile.known_limitations:
        sections.append(("Known limitations", _clip([profile.known_limitations], 1)))
    if profile.expected_outcome:
        sections.append(("Expected outcome", _clip([profile.expected_outcome], 1)))
    if profile.required_technology:
        sections.append(("Required technologies", _clip(profile.required_technology, 10)))
    if profile.affected_stakeholders:
        sections.append(("Affected stakeholders", _clip(profile.affected_stakeholders, 10)))
    if profile.evidence:
        sections.append(("Source evidence", _clip(profile.evidence, 10)))
    if profile.source_url:
        sections.append(("Original source URL", [profile.source_url]))

    techs = db.query(models.ProblemTechnology).filter(
        models.ProblemTechnology.problem_profile_id == pid
    ).all()
    if techs:
        items = [f"{t.technology_name} ({t.stage or 'potential'})" for t in techs]
        sections.append(("Technology landscape", _clip(items, 12)))

    papers = db.query(models.ProblemPaper).filter(
        models.ProblemPaper.problem_profile_id == pid
    ).order_by(models.ProblemPaper.relevance_score.desc()).limit(10).all()
    if papers:
        items = [f"{p.title} (rel {_safe_num(p.relevance_score):.2f})" for p in papers]
        sections.append(("Research landscape", _clip(items, 10)))

    return title, subtitle, sections


BUILDERS = {
    "opportunity": _build_opportunity,
    "idea":        _build_idea,
    "technology":  _build_technology,
    "research":    _build_research,
    "rd":          _build_rd,
}


@router.get("/pdf/{kind}/{id}")
def contextual_pdf(
    kind: str,
    id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    builder = BUILDERS.get(kind)
    if not builder:
        raise HTTPException(400, f"Unknown kind '{kind}'. Use one of: {list(BUILDERS.keys())}")

    title, subtitle, sections = builder(db, id)

    svc = PDFReportService()
    buf = svc.generate_sectioned_report(
        title=title,
        subtitle=subtitle,
        sections=sections,
        username=user.name if user else "User",
    )

    safe_title = "".join(c if c.isalnum() or c in "-_" else "_" for c in title[:60])
    filename = f"{kind}_{safe_title}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"

    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
