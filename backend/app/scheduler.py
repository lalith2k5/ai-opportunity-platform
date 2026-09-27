from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
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
        # Pick the topic that was run least recently (round-robin)
        from sqlalchemy import func
        used_topics = {
            row[0]: row[1]
            for row in db.query(
                models.SearchHistory.query,
                func.max(models.SearchHistory.created_at),
            ).group_by(models.SearchHistory.query).all()
        } if False else {}

        # Simple approach: pick the least-used topic from the list
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
    """Placeholder for periodic cleanup tasks."""
    logger.info("[Scheduler] Running cleanup job (noop for now)")


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
        next_run_time=datetime.now(),  # run once at startup
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
