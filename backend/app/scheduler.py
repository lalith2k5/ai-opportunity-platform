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
    outcome = {"status": "error", "topic": None, "message": None}
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
        outcome = {"status": "success", "topic": topic,
                   "message": f"{len(result['opportunities'])} opps"}

        # Log to agent_logs
        db.add(models.AgentLog(
            agent_name="Scheduler",
            action="scheduled_pipeline",
            status="success",
            details={"topic": topic, "opportunities": len(result["opportunities"])},
        ))
        db.commit()
    except Exception as e:
        msg = str(e)
        is_busy = "already running" in msg.lower()
        if is_busy:
            logger.info(f"[Scheduler] Pipeline busy, skipping this tick: {msg}")
            status = "skipped"
            outcome = {"status": "busy", "topic": None, "message": msg}
        else:
            logger.error(f"[Scheduler] Pipeline error: {msg}")
            status = "error"
            outcome = {"status": "error", "topic": None, "message": msg}
        try:
            db.add(models.AgentLog(
                agent_name="Scheduler",
                action="scheduled_pipeline",
                status=status,
                details={"error": msg, "busy": is_busy},
            ))
            db.commit()
        except Exception:
            pass
    finally:
        db.close()

    return outcome


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

        # Recommendations — 180 days (D7: prevents unbounded growth)
        cutoff = now - timedelta(days=180)
        n = db.query(models.Recommendation).filter(models.Recommendation.created_at < cutoff).delete(synchronize_session=False)
        result["recommendations"] = n

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


def _sync_spec_hooks():
    """Periodic spec hooks: conflict sweep (28.3) + score-delta ChangeEvents (35.2)."""
    try:
        from app.services.conflict_detector import sweep_all_opportunities
        stats = sweep_all_opportunities(limit=200)
        logger.info(f"[SyncHooks] Conflict sweep: {stats}")
    except Exception as e:
        logger.warning(f"[SyncHooks] Conflict sweep failed: {e}")

    from app.database import SessionLocal as _SL
    from app import models as _M
    db = _SL()
    try:
        opps = db.query(_M.Opportunity.id).limit(200).all()
        new_events = 0
        for (oid,) in opps:
            snaps = (
                db.query(_M.OpportunityScoreHistory)
                .filter(_M.OpportunityScoreHistory.opportunity_id == oid)
                .order_by(_M.OpportunityScoreHistory.recorded_at.desc())
                .limit(2)
                .all()
            )
            if len(snaps) < 2:
                continue
            delta = abs((snaps[0].opportunity_score or 0.0) - (snaps[1].opportunity_score or 0.0))
            if delta < 5.0:
                continue
            existing = (
                db.query(_M.ChangeEvent)
                .filter(_M.ChangeEvent.entity_type == "OPPORTUNITY")
                .filter(_M.ChangeEvent.entity_id == str(oid))
                .filter(_M.ChangeEvent.change_type == "score_changed")
                .filter(_M.ChangeEvent.detected_at >= snaps[0].recorded_at)
                .first()
            )
            if existing:
                continue
            db.add(_M.ChangeEvent(
                entity_type="OPPORTUNITY",
                entity_id=str(oid),
                change_type="score_changed",
                significance="MAJOR",
            ))
            new_events += 1
        db.commit()
        if new_events:
            logger.info(f"[SyncHooks] Emitted {new_events} score_changed ChangeEvent(s)")
    except Exception as e:
        db.rollback()
        logger.warning(f"[SyncHooks] ChangeEvent scan failed: {e}")
    finally:
        db.close()


def _deliver_notifications():
    """Spec 35.4 / FR-24: turn undelivered MAJOR ChangeEvents into user
    notifications. Dedup via AgentLog marker so re-runs never double-send."""
    from app.database import SessionLocal as _SL
    from app import models as _M

    db = _SL()
    try:
        recent_events = (
            db.query(_M.ChangeEvent)
            .filter(_M.ChangeEvent.significance == "MAJOR")
            .order_by(_M.ChangeEvent.id.desc())
            .limit(200)
            .all()
        )
        if not recent_events:
            return {"delivered": 0, "reason": "no_events"}

        delivered = 0
        for ev in recent_events:
            marker = f"delivered:ChangeEvent:{ev.id}"
            already = (
                db.query(_M.AgentLog)
                .filter(_M.AgentLog.action == marker)
                .first()
            )
            if already:
                continue

            title = ""
            link = "/dashboard"
            if ev.entity_type == "OPPORTUNITY":
                opp = db.query(_M.Opportunity).filter(_M.Opportunity.id == int(ev.entity_id)).first()
                if opp:
                    if ev.change_type == "score_changed":
                        title = f"Score changed: {opp.title[:80]}"
                    else:
                        title = f"{ev.change_type.replace('_', ' ').title()}: {opp.title[:80]}"
                    link = f"/opportunities/{opp.id}"
                else:
                    title = f"{ev.entity_type} {ev.entity_id}: {ev.change_type}"
            elif ev.entity_type == "GAP":
                title = f"Research gap status changed (id={ev.entity_id})"
                link = "/review"
            else:
                title = f"{ev.entity_type} {ev.entity_id}: {ev.change_type}"

            n = _M.Notification(
                type="change_alert",
                title=title[:200],
                message=f"Auto-generated from {ev.change_type} event #{ev.id}",
                link=link,
                severity="info",
                read=False,
            )
            db.add(n)
            db.add(_M.AgentLog(
                agent_name="Notifier",
                action=marker,
                status="success",
                details={"change_event_id": ev.id, "notification_title": title[:120]},
            ))
            delivered += 1

        db.commit()
        if delivered:
            logger.info(f"[Notifier] Delivered {delivered} notification(s)")
        return {"delivered": delivered}
    except Exception as e:
        db.rollback()
        logger.warning(f"[Notifier] delivery failed: {e}")
        return {"delivered": 0, "error": str(e)}
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
        _sync_spec_hooks,
        trigger=IntervalTrigger(minutes=15),
        id="spec_sync_hooks",
        name="Spec hooks: conflict sweep + ChangeEvent scan",
        replace_existing=True,
        next_run_time=datetime.now() + timedelta(minutes=2),
    )

    _scheduler.add_job(
        _deliver_notifications,
        trigger=IntervalTrigger(minutes=30),
        id="notification_delivery",
        name="Deliver MAJOR ChangeEvents as notifications",
        replace_existing=True,
        next_run_time=datetime.now() + timedelta(minutes=3),
    )

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
