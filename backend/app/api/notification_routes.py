from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.auth.dependencies import get_current_user

router = APIRouter(tags=["notifications"])


@router.get("/notifications")
def list_notifications(
    limit: int = 50,
    unread_only: bool = False,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    q = db.query(models.Notification)
    if unread_only:
        q = q.filter(models.Notification.read == False)
    rows = q.order_by(models.Notification.created_at.desc()).limit(limit).all()
    return [
        {
            "id": n.id,
            "type": n.type,
            "title": n.title,
            "message": n.message,
            "link": n.link,
            "severity": n.severity,
            "read": n.read,
            "created_at": n.created_at,
        }
        for n in rows
    ]


@router.get("/notifications/unread-count")
def unread_count(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    return {"count": db.query(models.Notification).filter(models.Notification.read == False).count()}


@router.post("/notifications/{nid}/read")
def mark_read(
    nid: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    n = db.query(models.Notification).filter(models.Notification.id == nid).first()
    if n:
        n.read = True
        db.commit()
    return {"id": nid, "read": True}


@router.post("/notifications/read-all")
def mark_all_read(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    db.query(models.Notification).filter(models.Notification.read == False).update({"read": True})
    db.commit()
    return {"message": "All marked read"}


@router.delete("/notifications/{nid}")
def delete_notification(
    nid: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    db.query(models.Notification).filter(models.Notification.id == nid).delete()
    db.commit()
    return {"deleted": nid}
