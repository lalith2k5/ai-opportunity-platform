
"""Research paper + R&D problem endpoints.

Covers Screen 4 (Research Analysis) and Screen 5 (R&D) detail views.

Read-only. No new tables. Preloads each table once per request to avoid
N+1 queries. Year parsing falls back to the arxiv_id prefix (YYMM.NNNNN).
"""
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.database import get_db
from app import models
from app.auth.dependencies import get_current_user


router = APIRouter(tags=["research"])

MIN_KEYWORD_LEN = 3
MAX_EVIDENCE_PER_SOURCE = 5


ARXIV_ID_RE = re.compile(r"(\d{2})(\d{2})\.\d+")
ARXIV_URL_RE = re.compile(r"https?://arxiv\.org/abs/", re.IGNORECASE)
ARXIV_VERSION_RE = re.compile(r"v\d+$")


def _normalize_arxiv_id(raw: str) -> str:
    if not raw:
        return ""
    s = str(raw).strip()
    s = ARXIV_URL_RE.sub("", s)
    s = ARXIV_VERSION_RE.sub("", s)
    return s.strip("/")


def _arxiv_id_variants(bare_id: str) -> list:
    if not bare_id:
        return []
    b = bare_id.strip()
    variants = {b}
    for scheme in ("http", "https"):
        variants.add(f"{scheme}://arxiv.org/abs/{b}")
        for v in range(1, 10):
            variants.add(f"{scheme}://arxiv.org/abs/{b}v{v}")
    return list(variants)


def _year_from_arxiv(arxiv_id: str) -> Optional[int]:
    if not arxiv_id:
        return None
    m = ARXIV_ID_RE.match(arxiv_id.strip())
    if not m:
        return None
    yy = int(m.group(1))
    full = 1900 + yy if yy >= 91 else 2000 + yy
    return full


def _year_from_published(published: str) -> Optional[int]:
    if not published:
        return None
    m = re.search(r"(\d{4})", published)
    return int(m.group(1)) if m else None


def _paper_year(paper) -> Optional[int]:
    y = _year_from_published(getattr(paper, "published", "") or "")
    if y:
        return y
    raw = getattr(paper, "arxiv_id", "") or ""
    return _year_from_arxiv(_normalize_arxiv_id(raw))


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


def _keyword_set(paper):
    kws = set()
    for k in (paper.research_areas or []):
        if k:
            kws.add(str(k).lower())
    for k in (paper.research_methods or []):
        if k:
            kws.add(str(k).lower())
    return kws


@router.get("/research-papers")
def list_research_papers(
    year: Optional[int] = None,
    domain: Optional[str] = None,
    q: Optional[str] = None,
    min_relevance: float = Query(0.0, ge=0.0, le=1.0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    rows = db.query(models.ProblemPaper).all()
    if not rows:
        return []

    profiles_by_id = {p.id: p for p in db.query(models.ProblemProfile).all()}

    grouped = {}
    for pp in rows:
        key = (pp.arxiv_id or "").strip() or f"paper:{pp.id}"
        g = grouped.setdefault(key, {
            "arxiv_id": pp.arxiv_id,
            "title": pp.title,
            "authors": pp.authors or [],
            "abstract": pp.abstract or "",
            "url": pp.url,
            "published": pp.published,
            "year": _paper_year(pp),
            "relevance_scores": [],
            "limitations": [],
            "methods": [],
            "areas": [],
            "domains": [],
        })
        if pp.relevance_score is not None:
            g["relevance_scores"].append(pp.relevance_score)
        for L in (pp.limitations or []):
            if L and L not in g["limitations"]:
                g["limitations"].append(L)
        for m in (pp.research_methods or []):
            if m and m not in g["methods"]:
                g["methods"].append(m)
        for a in (pp.research_areas or []):
            if a and a not in g["areas"]:
                g["areas"].append(a)
        parent = profiles_by_id.get(pp.problem_profile_id)
        if parent and parent.industry_domain:
            g["domains"].append(parent.industry_domain)

    results = []
    for key, g in grouped.items():
        rel = _avg(g["relevance_scores"]) or 0.0
        if rel < min_relevance:
            continue
        if year and g["year"] != year:
            continue
        dom = _majority(g["domains"])
        if domain and dom != domain:
            continue
        if q:
            needle = q.lower()
            hay = ((g["title"] or "") + " " + (g["abstract"] or "")).lower()
            if needle not in hay:
                continue
        results.append({
            "arxiv_id": _normalize_arxiv_id(g["arxiv_id"]),
            "arxiv_id_raw": g["arxiv_id"],
            "title": g["title"],
            "authors": g["authors"][:8],
            "year": g["year"],
            "published": g["published"],
            "domain": dom,
            "keywords": (g["areas"] or [])[:8],
            "abstract_snippet": (g["abstract"] or "")[:400],
            "relevance_score": rel,
            "url": g["url"],
            "limitations_count": len(g["limitations"]),
            "methods": g["methods"][:5],
        })

    results.sort(key=lambda r: (-r["relevance_score"], -(r["year"] or 0)))
    return results[:limit]


@router.get("/research-papers/{arxiv_id}")
def research_paper_detail(
    arxiv_id: str,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    raw = (arxiv_id or "").strip()
    if not raw:
        raise HTTPException(400, "arxiv_id required")

    bare = _normalize_arxiv_id(raw)
    variants = _arxiv_id_variants(bare)

    rows = db.query(models.ProblemPaper).filter(
        models.ProblemPaper.arxiv_id.in_(variants)
    ).all() if variants else []
    if not rows:
        raise HTTPException(404, f"Paper '{bare or raw}' not found")

    key = bare or raw

    primary = rows[0]
    profile_ids = list({pp.problem_profile_id for pp in rows})

    profiles = db.query(models.ProblemProfile).filter(
        models.ProblemProfile.id.in_(profile_ids)
    ).all()

    all_techs = db.query(models.ProblemTechnology).filter(
        models.ProblemTechnology.problem_profile_id.in_(profile_ids)
    ).all()

    tech_names = sorted({t.technology_name for t in all_techs if t.technology_name})

    this_kw = set()
    for a in (primary.research_areas or []):
        if a and len(str(a)) >= MIN_KEYWORD_LEN:
            this_kw.add(str(a).lower())
    for m in (primary.research_methods or []):
        if m and len(str(m)) >= MIN_KEYWORD_LEN:
            this_kw.add(str(m).lower())

    related_papers = []
    if this_kw:
        for pp in db.query(models.ProblemPaper).filter(
            models.ProblemPaper.arxiv_id != key
        ).all():
            other_kw = _keyword_set(pp)
            if len(other_kw & this_kw) >= 1:
                related_papers.append((len(other_kw & this_kw), pp))
    related_papers.sort(key=lambda x: -x[0])
    related_papers = [pp for _score, pp in related_papers[:10]]

    potential_gaps = []
    if this_kw:
        for g in db.query(models.ResearchGap).all():
            gk = set()
            for k in ((g.evidence or {}).get("keywords") or []):
                if k and len(str(k)) >= MIN_KEYWORD_LEN:
                    gk.add(str(k).lower())
            if len(gk & this_kw) >= 1:
                potential_gaps.append(g)
    potential_gaps.sort(key=lambda g: -(g.gap_score or 0))
    potential_gaps = potential_gaps[:8]

    domain = _majority([p.industry_domain for p in profiles if p.industry_domain])

    return {
        "paper": {
            "arxiv_id": _normalize_arxiv_id(primary.arxiv_id),
            "arxiv_id_raw": primary.arxiv_id,
            "title": primary.title,
            "authors": primary.authors or [],
            "published": primary.published,
            "year": _paper_year(primary),
            "url": primary.url,
            "abstract": primary.abstract or "",
            "relevance_score": _avg([pp.relevance_score for pp in rows]),
            "domain": domain,
        },
        "research_objective": (primary.abstract or "")[:600],
        "methodology": primary.research_methods or [],
        "key_findings": primary.results_summary or "",
        "limitations": primary.limitations or [],
        "related_papers": [
            {
                "arxiv_id": _normalize_arxiv_id(pp.arxiv_id),
                "title": pp.title,
                "year": _paper_year(pp),
                "relevance_score": pp.relevance_score,
                "url": pp.url,
            }
            for pp in related_papers
        ],
        "related_technologies": tech_names[:20],
        "potential_gaps": [
            {
                "id": g.id,
                "title": g.title,
                "description": g.description,
                "gap_score": g.gap_score,
            }
            for g in potential_gaps
        ],
        "source": {
            "url": primary.url,
            "arxiv_id": _normalize_arxiv_id(primary.arxiv_id),
        },
    }


@router.get("/rd/problems/{profile_id}")
def rd_problem_detail(
    profile_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    profile = db.query(models.ProblemProfile).filter(
        models.ProblemProfile.id == profile_id
    ).first()
    if not profile:
        raise HTTPException(404, f"Problem profile {profile_id} not found")

    organization = None
    if profile.organization_id:
        org = db.query(models.Organization).filter(
            models.Organization.id == profile.organization_id
        ).first()
        if org:
            organization = {
                "id": org.id,
                "name": org.name,
                "industry_domain": org.industry_domain,
                "source": org.source,
            }
    if organization is None and profile.organization:
        organization = {
            "id": None,
            "name": profile.organization,
            "industry_domain": profile.industry_domain,
            "source": profile.source,
        }

    techs = db.query(models.ProblemTechnology).filter(
        models.ProblemTechnology.problem_profile_id == profile_id
    ).all()

    papers = db.query(models.ProblemPaper).filter(
        models.ProblemPaper.problem_profile_id == profile_id
    ).order_by(models.ProblemPaper.relevance_score.desc()).all()

    all_keywords = set()
    for k in (profile.keywords or []):
        if k and len(str(k)) >= MIN_KEYWORD_LEN:
            all_keywords.add(str(k).lower())
    for t in techs:
        if t.technology_name and len(t.technology_name) >= MIN_KEYWORD_LEN:
            all_keywords.add(t.technology_name.lower())

    trends = []
    if all_keywords:
        for tr in db.query(models.Trend).all():
            tn = (tr.name or "").lower()
            if not tn:
                continue
            if any(kw == tn or kw in tn or tn in kw for kw in all_keywords):
                trends.append(tr)
    trends.sort(key=lambda t: -(t.trend_score or 0))
    trends = trends[:10]

    evidence = {"github": [], "github_issues": [], "arxiv": [],
                "news": [], "reddit": [], "patents": [], "rd_cells": [],
                "challenge_portal": []}

    if all_keywords:
        kw_list = list(all_keywords)[:8]
        clauses = []
        for kw in kw_list:
            pat = f"%{kw}%"
            clauses.append(func.lower(models.RawDocument.title).like(pat))
            clauses.append(func.lower(models.RawDocument.content).like(pat))
        clause = or_(*clauses)
        for src in evidence.keys():
            rows = db.query(models.RawDocument).filter(
                models.RawDocument.source == src,
            ).filter(clause).order_by(
                models.RawDocument.collected_at.desc()
            ).limit(MAX_EVIDENCE_PER_SOURCE).all()
            evidence[src] = [
                {
                    "id": r.id,
                    "title": r.title,
                    "url": r.url,
                    "source": r.source,
                    "collected_at": r.collected_at.isoformat() if r.collected_at else None,
                }
                for r in rows
            ]

    kg_node = profile.problem_title or ""
    kg_edges = []
    kg_nodes = []
    if kg_node:
        outgoing = db.query(models.KnowledgeGraphEdge).filter(
            models.KnowledgeGraphEdge.source == kg_node
        ).limit(30).all()
        incoming = db.query(models.KnowledgeGraphEdge).filter(
            models.KnowledgeGraphEdge.target == kg_node
        ).limit(30).all()
        seen_nodes = {kg_node}
        for e in outgoing:
            kg_edges.append({"source": e.source, "target": e.target, "relation": e.relation})
            seen_nodes.add(e.target)
        for e in incoming:
            kg_edges.append({"source": e.source, "target": e.target, "relation": e.relation})
            seen_nodes.add(e.source)
        if seen_nodes:
            node_rows = db.query(models.KnowledgeGraphNode).filter(
                models.KnowledgeGraphNode.name.in_(list(seen_nodes))
            ).all()
            kg_nodes = [
                {"name": n.name, "type": n.entity_type, "metadata": n.metadata_json}
                for n in node_rows
            ]

    gaps = []
    if all_keywords:
        for g in db.query(models.ResearchGap).all():
            gk = set()
            for k in ((g.evidence or {}).get("keywords") or []):
                if k and len(str(k)) >= MIN_KEYWORD_LEN:
                    gk.add(str(k).lower())
            if len(gk & all_keywords) >= 1:
                gaps.append(g)
    gaps.sort(key=lambda g: -(g.gap_score or 0))
    gaps = gaps[:10]

    clusters = db.query(models.ProblemCluster).all()
    best_cluster = None
    best_overlap = 0
    for c in clusters:
        ck = {str(k).lower() for k in (c.keywords or []) if k}
        overlap = len(ck & all_keywords)
        if overlap > best_overlap:
            best_overlap = overlap
            best_cluster = c

    opps = []
    if best_cluster:
        opps = db.query(models.Opportunity).filter(
            models.Opportunity.problem_cluster_id == best_cluster.id
        ).order_by(models.Opportunity.opportunity_score.desc()).limit(10).all()

    top_opp = opps[0] if opps else None
    scoring_breakdown = None
    if top_opp:
        scoring_breakdown = {
            "opportunity_id": top_opp.id,
            "title": top_opp.title,
            "opportunity_score": top_opp.opportunity_score,
            "demand": top_opp.demand_score,
            "research_gap": top_opp.research_gap_score,
            "trend": top_opp.trend_score,
            "feasibility": top_opp.feasibility_score,
            "market_readiness": top_opp.market_readiness_score,
            "technology_suitability": top_opp.technology_suitability_score,
            "evidence_strength": top_opp.evidence_strength_score,
            "recency": top_opp.recency_score,
            "confidence": top_opp.confidence_score,
            "explanation": top_opp.explanation,
        }

    next_steps = []
    if top_opp:
        if top_opp.suggested_research_direction:
            next_steps.append({"kind": "research", "text": top_opp.suggested_research_direction})
        if top_opp.suggested_project_direction:
            next_steps.append({"kind": "project", "text": top_opp.suggested_project_direction})
    if not next_steps and papers:
        next_steps.append({
            "kind": "research",
            "text": f"Review the top {min(3, len(papers))} linked papers for current approaches and stated limitations.",
        })
    if not next_steps:
        next_steps.append({
            "kind": "research",
            "text": "Run a fresh pipeline on this problem to populate suggested research and project directions.",
        })

    evidence_flat = [
        {"source": src, "title": m["title"], "url": m["url"]}
        for src, items in evidence.items()
        for m in items
        if m.get("url")
    ]

    return {
        "problem": {
            "id": profile.id,
            "problem_title": profile.problem_title,
            "problem_description": profile.problem_description,
            "industry_domain": profile.industry_domain,
            "problem_type": profile.problem_type,
            "technology_stage": profile.technology_stage,
            "source": profile.source,
            "source_url": profile.source_url,
            "keywords": profile.keywords or [],
            "problem_status": profile.problem_status,
            "student_suitability": profile.student_suitability,
            "affected_stakeholders": profile.affected_stakeholders or [],
            "evidence": profile.evidence or [],
            "confidence": profile.confidence,
            "created_at": profile.created_at.isoformat() if profile.created_at else None,
        },
        "organization": organization,
        "related_technologies": [
            {"name": t.technology_name, "stage": t.stage, "confidence": t.confidence}
            for t in techs
        ],
        "technology_landscape": {
            "count": len(techs),
            "stages": list({t.stage for t in techs if t.stage}),
            "average_confidence": _avg([t.confidence for t in techs]),
        },
        "research_landscape": [
            {
                "id": pp.id,
                "arxiv_id": pp.arxiv_id,
                "title": pp.title,
                "year": _paper_year(pp),
                "relevance_score": pp.relevance_score,
                "url": pp.url,
                "research_methods": pp.research_methods or [],
                "results_summary": pp.results_summary,
            }
            for pp in papers[:15]
        ],
        "emerging_trends": [
            {
                "name": t.name,
                "trend_score": t.trend_score,
                "category": t.category,
                "detected_at": t.detected_at.isoformat() if t.detected_at else None,
            }
            for t in trends
        ],
        "evidence_aggregation": evidence,
        "evidence_sources": evidence_flat[:20],
        "knowledge_graph": {
            "node": kg_node,
            "nodes": kg_nodes,
            "edges": kg_edges,
        },
        "potential_gaps": [
            {
                "id": g.id,
                "title": g.title,
                "description": g.description,
                "gap_score": g.gap_score,
            }
            for g in gaps
        ],
        "innovation_opportunities": [
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
        "opportunity_scoring": scoring_breakdown,
        "recommended_next_steps": next_steps,
    }
