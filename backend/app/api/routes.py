from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.database import get_db
from app import models, schemas
from app.agents.orchestrator import OrchestratorAgent
from app.agents.ai_chat import AIChatAgent
from app.services.embedding_service import EmbeddingService
from app.auth.dependencies import get_current_user, optional_user
from app.scheduler import get_scheduler_status
from app.services.pdf_service import PDFReportService
from fastapi.responses import StreamingResponse

router = APIRouter()
orchestrator = OrchestratorAgent()
chat_agent = AIChatAgent()
embedding_service = EmbeddingService()

@router.get("/health")
def health():
    return {"status": "healthy", "vectors_stored": embedding_service.count()}

@router.post("/pipeline/run")
def run_pipeline(
    query: schemas.SearchQuery,
    db: Session = Depends(get_db),
    user: Optional[models.User] = Depends(optional_user),
):
    try:
        return orchestrator.run_full_pipeline(
            query.query,
            user_id=user.id if user else None,
            mode=(query.mode or "quick"),
        )
    except RuntimeError as e:
        # Concurrent pipeline rejection — return 409, not 500
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/opportunities")
def get_opportunities(db: Session = Depends(get_db), _=Depends(get_current_user)):
    from sqlalchemy import func
    # Show only the highest-scoring row per unique title
    subq = (
        db.query(
            models.Opportunity.title,
            func.max(models.Opportunity.opportunity_score).label("max_score"),
        )
        .group_by(models.Opportunity.title)
        .subquery()
    )
    return (
        db.query(models.Opportunity)
        .join(
            subq,
            (models.Opportunity.title == subq.c.title)
            & (models.Opportunity.opportunity_score == subq.c.max_score),
        )
        .order_by(models.Opportunity.opportunity_score.desc())
        .limit(50)
        .all()
    )

@router.get("/problems")
def get_problems(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(models.ProblemCluster).order_by(models.ProblemCluster.demand_score.desc()).limit(50).all()

@router.get("/research-gaps")
def get_research_gaps(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(models.ResearchGap).order_by(models.ResearchGap.gap_score.desc()).limit(50).all()

def _compute_growth(db, trend_name: str) -> dict:
    """7-day avg vs prior-7-day avg of the mention_count. Returns growth metrics."""
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import func

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
        growth = 0.0
        label = "no_data"
    elif prior == 0:
        growth = 1.0
        label = "new"
    else:
        growth = (recent - prior) / prior
        if growth > 0.2:
            label = "rising"
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


@router.get("/trends")
def get_trends(db: Session = Depends(get_db), _=Depends(get_current_user)):
    rows = db.query(models.Trend).order_by(models.Trend.trend_score.desc()).limit(50).all()
    out = []
    seen = set()
    for t in rows:
        if t.name in seen:
            continue
        seen.add(t.name)
        growth = _compute_growth(db, t.name)
        out.append({
            "id": t.id,
            "name": t.name,
            "category": t.category,
            "trend_score": t.trend_score,
            "source_data": t.source_data,
            "detected_at": t.detected_at.isoformat() if t.detected_at else None,
            **growth,
        })
    return out


@router.get("/trends/{trend_name}/history")
def get_trend_history(
    trend_name: str,
    days: int = 30,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """Return daily mention-count history for a trend."""
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import func

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    rows = (
        db.query(
            func.date(models.TrendSnapshot.snapshot_at).label("day"),
            func.avg(models.TrendSnapshot.mention_count).label("avg_mentions"),
            func.count(models.TrendSnapshot.id).label("runs"),
        )
        .filter(
            models.TrendSnapshot.trend_name == trend_name,
            models.TrendSnapshot.snapshot_at >= cutoff,
        )
        .group_by(func.date(models.TrendSnapshot.snapshot_at))
        .order_by(func.date(models.TrendSnapshot.snapshot_at))
        .all()
    )
    return {
        "trend_name": trend_name,
        "days": days,
        "history": [
            {
                "day": str(r.day),
                "avg_mentions": round(float(r.avg_mentions or 0), 2),
                "runs": r.runs,
            }
            for r in rows
        ],
        "growth": _compute_growth(db, trend_name),
    }

@router.get("/search-history")
def get_search_history(
    db: Session = Depends(get_db),
    user: Optional[models.User] = Depends(optional_user),
):
    if not user:
        return []
    return (
        db.query(models.SearchHistory)
        .filter(models.SearchHistory.user_id == user.id)
        .order_by(models.SearchHistory.created_at.desc())
        .limit(20)
        .all()
    )

@router.post("/chat")
def chat(
    query: schemas.ChatQuery,
    db: Session = Depends(get_db),
    user: Optional[models.User] = Depends(optional_user),
):
    result = chat_agent.answer(query.question)

    # Persist chat session + messages
    try:
        session_id = query.session_id
        if not session_id:
            session = models.ChatSession(
                user_id=user.id if user else None,
                title=query.question[:60],
            )
            db.add(session)
            db.flush()
            session_id = session.id

        db.add(models.ChatMessage(session_id=session_id, role="user", content=query.question))
        db.add(models.ChatMessage(
            session_id=session_id,
            role="assistant",
            content=result.get("response", ""),
            sources=result.get("sources", []),
        ))
        db.commit()
        result["session_id"] = session_id
    except Exception as e:
        db.rollback()
        print(f"Chat persistence error: {e}")

    return result

@router.get("/chat-history")
def chat_history(
    db: Session = Depends(get_db),
    user: Optional[models.User] = Depends(optional_user),
):
    if not user:
        return []
    sessions = (
        db.query(models.ChatSession)
        .filter(models.ChatSession.user_id == user.id)
        .order_by(models.ChatSession.created_at.desc())
        .limit(20)
        .all()
    )
    return [
        {
            "id": s.id,
            "title": s.title,
            "created_at": s.created_at,
            "messages": [
                {"role": m.role, "content": m.content, "sources": m.sources}
                for m in db.query(models.ChatMessage).filter(models.ChatMessage.session_id == s.id).order_by(models.ChatMessage.id).all()
            ],
        }
        for s in sessions
    ]

@router.post("/search")
def semantic_search(query: schemas.SearchQuery):
    return embedding_service.search(query.query, n_results=10)


pdf_service = PDFReportService()

@router.get("/reports/pdf")
def generate_pdf(
    db: Session = Depends(get_db),
    user: Optional[models.User] = Depends(optional_user),
):
    opportunities = db.query(models.Opportunity).order_by(models.Opportunity.opportunity_score.desc()).limit(20).all()
    problems = db.query(models.ProblemCluster).order_by(models.ProblemCluster.demand_score.desc()).limit(20).all()
    gaps = db.query(models.ResearchGap).order_by(models.ResearchGap.gap_score.desc()).limit(20).all()
    trends = db.query(models.Trend).order_by(models.Trend.trend_score.desc()).limit(20).all()

    # AI executive summary (graceful fallback inside generate_narrative)
    from app.services.llm_service import LLMService
    narrative = LLMService().generate_narrative(opportunities, gaps, trends)

    buf = pdf_service.generate_report(
        opportunities, problems, gaps, trends,
        username=user.name if user else "Guest",
        narrative=narrative,
    )
    filename = f"opportunity_report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/reports/narrative")
def generate_narrative_endpoint(
    query: str = "",
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """Return an AI-written executive summary based on current DB state."""
    from app.services.llm_service import LLMService
    opps = db.query(models.Opportunity).order_by(models.Opportunity.opportunity_score.desc()).limit(20).all()
    gaps = db.query(models.ResearchGap).order_by(models.ResearchGap.gap_score.desc()).limit(10).all()
    trends = db.query(models.Trend).order_by(models.Trend.trend_score.desc()).limit(10).all()
    svc = LLMService()
    narrative = svc.generate_narrative(opps, gaps, trends, query=query)
    return {
        "narrative": narrative,
        "counts": {
            "opportunities": len(opps),
            "gaps": len(gaps),
            "trends": len(trends),
        },
    }


@router.get("/scheduler/status")
def scheduler_status():
    return get_scheduler_status()


@router.get("/opportunities/{opp_id}/history")
def get_opportunity_history(
    opp_id: int,
    days: int = 30,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """Time-series of opportunity_score + rank (Phase 8.2)."""
    from datetime import datetime, timedelta, timezone
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    rows = (
        db.query(models.OpportunityScoreHistory)
        .filter(models.OpportunityScoreHistory.opportunity_id == opp_id)
        .filter(models.OpportunityScoreHistory.recorded_at >= cutoff)
        .order_by(models.OpportunityScoreHistory.recorded_at.asc())
        .all()
    )
    return {
        "opportunity_id": opp_id,
        "days": days,
        "history": [
            {
                "score": r.opportunity_score,
                "rank": r.rank,
                "recorded_at": r.recorded_at.isoformat() if r.recorded_at else None,
            }
            for r in rows
        ],
    }


@router.get("/opportunities/{opp_id}")
def get_opportunity(opp_id: int, db: Session = Depends(get_db)):
    opp = db.query(models.Opportunity).filter(models.Opportunity.id == opp_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    cluster = None
    if opp.problem_cluster_id:
        cluster = db.query(models.ProblemCluster).filter(models.ProblemCluster.id == opp.problem_cluster_id).first()

    gap = None
    if opp.research_gap_id:
        gap = db.query(models.ResearchGap).filter(models.ResearchGap.id == opp.research_gap_id).first()

    # Find raw source documents whose content matches the cluster's keywords
    related_sources = []
    if cluster and cluster.keywords:
        keywords = [str(k).lower() for k in (cluster.keywords or [])[:8] if k]
        if keywords:
            candidates = (
                db.query(models.RawDocument)
                .order_by(models.RawDocument.collected_at.desc())
                .limit(1000)
                .all()
            )
            scored = []
            for doc in candidates:
                if not doc.url:
                    continue
                haystack = ((doc.title or "") + " " + (doc.content or "")).lower()
                hits = sum(1 for kw in keywords if kw in haystack)
                if hits > 0:
                    scored.append((hits, doc))
            scored.sort(key=lambda x: -x[0])
            related_sources = [
                {
                    "id": d.id,
                    "title": (d.title or "")[:200],
                    "url": d.url,
                    "source": d.source or "unknown",
                    "matched_keywords": h,
                }
                for h, d in scored[:12]
            ]

    return {
        "opportunity": {
            "id": opp.id,
            "title": opp.title,
            "description": opp.description,
            "opportunity_score": opp.opportunity_score,
            "confidence_score": opp.confidence_score,
            "demand_score": opp.demand_score,
            "research_gap_score": opp.research_gap_score,
            "trend_score": opp.trend_score,
            "competition_score": opp.competition_score,
            "feasibility_score": opp.feasibility_score,
            "market_readiness_score": opp.market_readiness_score,
            # ---- Phase 10.3: SRS §21 new scoring factors ----
            "technology_suitability_score": opp.technology_suitability_score or 0.0,
            "evidence_strength_score": opp.evidence_strength_score or 0.0,
            "recency_score": opp.recency_score or 0.0,
            "explanation": opp.explanation,
            # ---- Phase 6.1 enrichment (SRS §34) ----
            "domain": opp.domain,
            "industry": opp.industry,
            "related_technologies": opp.related_technologies or [],
            "existing_research": opp.existing_research or [],
            "existing_approaches": opp.existing_approaches,
            "known_limitations": opp.known_limitations,
            "suggested_research_direction": opp.suggested_research_direction,
            "suggested_project_direction": opp.suggested_project_direction,
            "emerging_trend": opp.emerging_trend,
            "evidence_sources": opp.evidence_sources or [],
            "created_at": opp.created_at,
        },
        "problem_cluster": {
            "id": cluster.id,
            "title": cluster.title,
            "description": cluster.description,
            "keywords": cluster.keywords,
            "source_count": cluster.source_count,
        } if cluster else None,
        "research_gap": {
            "id": gap.id,
            "title": gap.title,
            "description": gap.description,
            "gap_score": gap.gap_score,
            "evidence": gap.evidence,
        } if gap else None,
        "sources": related_sources,
    }


@router.get("/processed-documents")
def list_processed_documents(
    source: Optional[str] = None,
    keyword: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """List processed documents with optional filters."""
    q = db.query(models.ProcessedDocument).order_by(
        models.ProcessedDocument.processed_at.desc()
    )
    if source or keyword:
        q = q.join(
            models.RawDocument,
            models.ProcessedDocument.raw_document_id == models.RawDocument.id,
        )
        if source:
            q = q.filter(models.RawDocument.source == source)
        if keyword:
            q = q.filter(models.RawDocument.title.ilike(f"%{keyword}%"))

    rows = q.limit(limit).all()

    raw_ids = [r.raw_document_id for r in rows]
    raw_map = {}
    if raw_ids:
        for rd in db.query(models.RawDocument).filter(models.RawDocument.id.in_(raw_ids)).all():
            raw_map[rd.id] = rd

    out = []
    for r in rows:
        rd = raw_map.get(r.raw_document_id)
        out.append({
            "id": r.id,
            "raw_document_id": r.raw_document_id,
            "source": (rd.source if rd else None),
            "title": (rd.title if rd else None),
            "url": (rd.url if rd else None),
            "keywords": r.keywords or [],
            "entities": r.entities or [],
            "topics": r.topics or [],
            "sentiment_score": r.sentiment_score,
            "processed_at": r.processed_at.isoformat() if r.processed_at else None,
        })
    return {"count": len(out), "documents": out}


@router.get("/chat-sessions/{session_id}")
def get_chat_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(models.ChatSession).filter(models.ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    messages = (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.session_id == session_id)
        .order_by(models.ChatMessage.id)
        .all()
    )
    return {
        "id": session.id,
        "title": session.title,
        "created_at": session.created_at,
        "messages": [
            {"role": m.role, "content": m.content, "sources": m.sources}
            for m in messages
        ],
    }
