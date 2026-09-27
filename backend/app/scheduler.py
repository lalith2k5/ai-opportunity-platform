from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
from app.logger import logger
from app.database import SessionLocal
from app import models

# Global scheduler instance
_scheduler = None

# Topics that get auto-monitored
MONITORED_TOPICS = [
    "artificial intelligence",
    "machine learning",
    "cybersecurity",
    "healthcare technology",
    "climate technology",
    "quantum computing",
    "robotics",
    "blockchain",
]


def _run_monitored_pipeline():
    """Runs the pipeline for each monitored topic, cycling through them."""
    from app.agents.orchestrator import OrchestratorAgent

    logger.info("[Scheduler] Starting scheduled monitoring run")
    db = SessionLocal()
    try:
        # Pick the least-used topic from the list
        counts = {}
        for topic in MONITORED_TOPICS:
            count = db.query(models.SearchHistory).filter(
                models.SearchHistory.query == topic
            ).count()
            counts[topic] = count

        topic = min(counts, key=counts.get)
        logger.info(f"[Scheduler] Next topic: '{topic}' (run count: {counts[topic]})")

        orchestrator = OrchestratorAgent()
        result = orchestrator.run_full_pipeline(topic, user_id=None)
        logger.info(f"[Scheduler] Pipeline complete for '{topic}': "
                    f"{result['documents_count']} docs, "
                    f"{len(result['opportunities'])} opportunities")

        # Log to agent_logs
        db.add(models.AgentLog(
            agent_name="Scheduler",
            action="scheduled_pipeline",
            status="success",
            details={"topic": topic, "opportunities": len(result["opportunities"])},
        ))
        db.commit()
    except Exception as e:
        logger.error(f"[Scheduler] Pipeline error: {e}")
        try:
            db.add(models.AgentLog(
                agent_name="Scheduler",
                action="scheduled_pipeline",
                status="error",
                details={"error": str(e)},
            ))
            db.commit()
        except Exception:
            pass
    finally:
        db.close()


def _cleanup_old_logs():
    """Purge old data based on retention policy. Runs daily at 3 AM."""
    from datetime import datetime, timedelta, timezone

    db = SessionLocal()
    result = {}
    now = datetime.now(timezone.utc)

    try:
        # Agent logs — 30 days
        cutoff = now - timedelta(days=30)
        n = db.query(models.AgentLog).filter(models.AgentLog.created_at < cutoff).delete(synchronize_session=False)
        result["agent_logs"] = n

        # Trend snapshots — 90 days
        cutoff = now - timedelta(days=90)
        n = db.query(models.TrendSnapshot).filter(models.TrendSnapshot.snapshot_at < cutoff).delete(synchronize_session=False)
        result["trend_snapshots"] = n

        # Password reset tokens — expired OR used, older than 7 days
        cutoff = now - timedelta(days=7)
        n = db.query(models.PasswordResetToken).filter(
            models.PasswordResetToken.created_at < cutoff,
            (models.PasswordResetToken.used == True) |
            (models.PasswordResetToken.expires_at < now),
        ).delete(synchronize_session=False)
        result["password_reset_tokens"] = n

        # Refresh tokens — revoked or expired, older than 7 days
        cutoff = now - timedelta(days=7)
        n = db.query(models.RefreshToken).filter(
            models.RefreshToken.created_at < cutoff,
            (models.RefreshToken.revoked == True) |
            (models.RefreshToken.expires_at < now),
        ).delete(synchronize_session=False)
        result["refresh_tokens"] = n

        # Search history — 180 days
        cutoff = now - timedelta(days=180)
        n = db.query(models.SearchHistory).filter(models.SearchHistory.created_at < cutoff).delete(synchronize_session=False)
        result["search_history"] = n

        db.commit()
        total = sum(result.values())
        logger.info(f"[Scheduler] Cleanup done — {total} rows purged: {result}")

        # Log to agent_logs (fresh table after purge)
        try:
            db.add(models.AgentLog(
                agent_name="Scheduler",
                action="cleanup_old_logs",
                status="success",
                details={"deleted": result, "total": total},
            ))
            db.commit()
        except Exception:
            pass

        return result
    except Exception as e:
        db.rollback()
        logger.error(f"[Scheduler] Cleanup error: {e}")
        return {}
    finally:
        db.close()


def start_scheduler():
    """Start the background scheduler if not already running."""
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        logger.info("[Scheduler] Already running")
        return _scheduler

    _scheduler = BackgroundScheduler()

    # Continuous monitoring: run every 6 hours
    _scheduler.add_job(
        _run_monitored_pipeline,
        trigger=IntervalTrigger(hours=6),
        id="monitored_pipeline",
        name="Continuous monitoring pipeline",
        replace_existing=True,
        next_run_time=datetime.now() + timedelta(seconds=60),  # first run 60s after startup (avoids race with --reload)
    )

    # Daily cleanup at 3 AM
    _scheduler.add_job(
        _cleanup_old_logs,
        trigger=CronTrigger(hour=3, minute=0),
        id="daily_cleanup",
        name="Daily cleanup",
        replace_existing=True,
    )

    _scheduler.start()
    logger.info("[Scheduler] Started — monitored pipeline every 6h, cleanup daily at 3 AM")
    return _scheduler


def stop_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("[Scheduler] Stopped")
    _scheduler = None


def get_scheduler_status():
    global _scheduler
    if not _scheduler or not _scheduler.running:
        return {"running": False, "jobs": []}
    jobs = []
    for job in _scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": str(job.next_run_time) if job.next_run_time else None,
        })
    return {"running": True, "jobs": jobs}
