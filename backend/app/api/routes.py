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
        return orchestrator.run_full_pipeline(query.query, user_id=user.id if user else None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/opportunities")
def get_opportunities(db: Session = Depends(get_db)):
    return db.query(models.Opportunity).order_by(models.Opportunity.opportunity_score.desc()).limit(50).all()

@router.get("/problems")
def get_problems(db: Session = Depends(get_db)):
    return db.query(models.ProblemCluster).order_by(models.ProblemCluster.demand_score.desc()).limit(50).all()

@router.get("/research-gaps")
def get_research_gaps(db: Session = Depends(get_db)):
    return db.query(models.ResearchGap).order_by(models.ResearchGap.gap_score.desc()).limit(50).all()

@router.get("/trends")
def get_trends(db: Session = Depends(get_db)):
    return db.query(models.Trend).order_by(models.Trend.trend_score.desc()).limit(50).all()

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

    buf = pdf_service.generate_report(
        opportunities, problems, gaps, trends,
        username=user.name if user else "Guest",
    )
    filename = f"opportunity_report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/scheduler/status")
def scheduler_status():
    return get_scheduler_status()


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
            "explanation": opp.explanation,
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
    }


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
