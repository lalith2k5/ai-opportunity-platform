from app.database import SessionLocal
from app import models
from app.logger import logger


def create_notification(
    type_: str,
    title: str,
    message: str = "",
    link: str = "",
    severity: str = "info",
    user_id: int = None,
):
    """Create a single notification."""
    db = SessionLocal()
    try:
        n = models.Notification(
            user_id=user_id,
            type=type_,
            title=title[:200],
            message=message[:1000],
            link=link,
            severity=severity,
        )
        db.add(n)
        db.commit()
        return n.id
    except Exception as e:
        db.rollback()
        logger.error(f"Notification error: {e}")
        return None
    finally:
        db.close()


def generate_pipeline_notifications(opportunities, gaps, trends, query: str):
    """Generate all 5 SRS-mandated notification types after a pipeline run."""
    created = 0

    # 1. New Research Opportunity
    if opportunities:
        top = max(opportunities, key=lambda o: o.get("opportunity_score", 0))
        create_notification(
            "research_opportunity",
            f"New research opportunity: {top.get('title', '')[:80]}",
            f"Score {top.get('opportunity_score', 0):.2f} from '{query}' pipeline",
            link=f"/opportunities",
            severity="success",
        )
        created += 1

    # 2. Emerging Technology
    if trends:
        top_trend = trends[0]
        create_notification(
            "emerging_tech",
            f"Emerging technology: {top_trend.get('name', '')}",
            f"Trend score {top_trend.get('trend_score', 0):.2f}",
            link="/reports",
            severity="info",
        )
        created += 1

    # 3. New Startup Opportunity
    if opportunities:
        top = max(opportunities, key=lambda o: o.get("feasibility_score", 0))
        create_notification(
            "startup_opportunity",
            f"Startup idea: {top.get('title', '')[:80]}",
            f"Feasibility {top.get('feasibility_score', 0):.2f}",
            link="/opportunities",
            severity="success",
        )
        created += 1

    # 4. Innovation Alert
    create_notification(
        "innovation_alert",
        f"Pipeline completed for '{query}'",
        f"{len(opportunities)} opportunities · {len(trends)} trends detected",
        link="/",
        severity="info",
    )
    created += 1

    # 5. Research Gap Alert
    if gaps:
        high_gaps = [g for g in gaps if g.get("gap_score", 0) > 0.5]
        if high_gaps:
            create_notification(
                "research_gap_alert",
                f"{len(high_gaps)} high-priority research gaps detected",
                f"Coverage gaps in '{query}' domain",
                link="/reports",
                severity="warning",
            )
            created += 1

    logger.info(f"Generated {created} notifications")
    return created
