from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.auth.dependencies import require_role
from app.scheduler import get_scheduler_status, _run_monitored_pipeline
from datetime import datetime, timezone

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats")
def admin_stats(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("admin")),
):
    """System-wide stats."""
    return {
        "users": db.query(models.User).count(),
        "raw_documents": db.query(models.RawDocument).count(),
        "problem_clusters": db.query(models.ProblemCluster).count(),
        "research_gaps": db.query(models.ResearchGap).count(),
        "trends": db.query(models.Trend).count(),
        "opportunities": db.query(models.Opportunity).count(),
        "search_history": db.query(models.SearchHistory).count(),
        "chat_sessions": db.query(models.ChatSession).count(),
        "notifications_unread": db.query(models.Notification).filter(models.Notification.read == False).count(),
        "kg_nodes": db.query(models.KnowledgeGraphNode).count(),
        "kg_edges": db.query(models.KnowledgeGraphEdge).count(),
    }


@router.get("/users")
def list_users(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("admin")),
):
    users = db.query(models.User).order_by(models.User.id).all()
    return [
        {"id": u.id, "name": u.name, "email": u.email, "role": u.role, "created_at": u.created_at}
        for u in users
    ]


@router.patch("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    role: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("admin")),
):
    allowed = {"student", "researcher", "entrepreneur", "investor", "admin"}
    if role not in allowed:
        raise HTTPException(400, f"Role must be one of {allowed}")
    target = db.query(models.User).filter(models.User.id == user_id).first()
    if not target:
        raise HTTPException(404, "User not found")
    target.role = role
    db.commit()
    return {"id": target.id, "role": target.role}


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("admin")),
):
    if user.id == user_id:
        raise HTTPException(400, "Cannot delete yourself")
    target = db.query(models.User).filter(models.User.id == user_id).first()
    if not target:
        raise HTTPException(404, "User not found")

    try:
        # Cascade manually — the FK constraints don't have ON DELETE CASCADE.
        # ChatMessage rows reference chat_sessions, so delete those first.
        session_ids = [
            row[0] for row in db.query(models.ChatSession.id)
            .filter(models.ChatSession.user_id == user_id).all()
        ]
        if session_ids:
            db.query(models.ChatMessage).filter(
                models.ChatMessage.session_id.in_(session_ids)
            ).delete(synchronize_session=False)

        db.query(models.ChatSession).filter(
            models.ChatSession.user_id == user_id
        ).delete(synchronize_session=False)

        db.query(models.SearchHistory).filter(
            models.SearchHistory.user_id == user_id
        ).delete(synchronize_session=False)

        db.query(models.RefreshToken).filter(
            models.RefreshToken.user_id == user_id
        ).delete(synchronize_session=False)

        db.query(models.PasswordResetToken).filter(
            models.PasswordResetToken.user_id == user_id
        ).delete(synchronize_session=False)

        db.query(models.Notification).filter(
            models.Notification.user_id == user_id
        ).delete(synchronize_session=False)

        db.query(models.Report).filter(
            models.Report.user_id == user_id
        ).delete(synchronize_session=False)

        db.query(models.Recommendation).filter(
            models.Recommendation.user_id == user_id
        ).delete(synchronize_session=False)

        db.delete(target)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Failed to delete user: {e}")

    return {"deleted": user_id}


@router.get("/agent-logs")
def agent_logs(
    limit: int = 50,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("admin")),
):
    logs = db.query(models.AgentLog).order_by(models.AgentLog.created_at.desc()).limit(limit).all()
    return [
        {"id": l.id, "agent_name": l.agent_name, "action": l.action, "status": l.status,
         "details": l.details, "created_at": l.created_at}
        for l in logs
    ]


@router.get("/scheduler")
def scheduler_status_admin(
    user: models.User = Depends(require_role("admin")),
):
    return get_scheduler_status()


@router.post("/scheduler/trigger")
def trigger_scheduler(
    user: models.User = Depends(require_role("admin")),
):
    _run_monitored_pipeline()
    return {"triggered": True, "at": datetime.now(timezone.utc).isoformat()}


@router.post("/pipeline/run")
def admin_run_pipeline(
    query: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("admin")),
):
    from app.agents.orchestrator import OrchestratorAgent
    orch = OrchestratorAgent()
    result = orch.run_full_pipeline(query, user_id=user.id)
    return {"query": query, "documents_count": result["documents_count"],
            "opportunities": len(result["opportunities"])}
