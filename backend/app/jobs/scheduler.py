"""
APScheduler configuration and job scheduling.
Sets up 8 separate background jobs with different schedules.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from ..jobs.tasks import (
    scrape_job,
    extract_job,
    analyze_job,
    framework_job,
    newsletter_job,
    statistics_verification_job,
    article_clustering_job,
    context_generation_job,
    process_articles_job,
    process_unprocessed_articles_job,
    regenerate_viewpoints_job
)
from ..config import settings
import logging

logger = logging.getLogger(__name__)

# Create scheduler instance
scheduler = BackgroundScheduler()


def start_scheduler():
    """
    Initialize and start the background job scheduler.
    This should be called once when the application starts.

    PIPELINE WORKFLOW:
    - Main pipeline (every 6 hours): scrape → extract → analyze → process
      - Scrape: Fetch articles from RSS feeds
      - Extract: Get full article content
      - Analyze: AI analysis (sentiment, bias, summary)
      - Process: 4 concurrent tasks (frameworks, stats, clustering, context)

    - Backup job (every 10 hours): Check for any missed/unprocessed articles

    - Newsletter job (daily at 10:20 AM PST): Send daily newsletters
    """
    if scheduler.running:
        logger.warning("Scheduler is already running")
        return

    logger.info("Initializing APScheduler with 3 scheduled jobs...")

    # Job 1: Main article pipeline - runs every 6 hours
    scheduler.add_job(
        func=scrape_job,
        trigger=IntervalTrigger(hours=6),
        id='scrape_rss',
        name='Article Pipeline (scrape → extract → analyze → process)',
        replace_existing=True,
        max_instances=1,  # Only one instance at a time
    )
    logger.info("✓ Scheduled: Article pipeline every 6 hours")
    logger.info("  └─> Chains: scrape → extract → analyze → process (4 concurrent tasks)")

    # Job 2: Backup cleanup job - runs every 10 hours
    scheduler.add_job(
        func=process_unprocessed_articles_job,
        trigger=IntervalTrigger(hours=10),
        id='process_unprocessed',
        name='Process Unprocessed Articles',
        replace_existing=True,
        max_instances=1,
    )
    logger.info("✓ Scheduled: Unprocessed articles check every 10 hours")
    logger.info("  └─> Catches articles that missed main pipeline")

    # Job 3: Send newsletters daily at 10:20 AM PST
    scheduler.add_job(
        func=newsletter_job,
        trigger=CronTrigger(hour=10, minute=20, timezone='America/Los_Angeles'),
        id='send_newsletters',
        name='Send Newsletters',
        replace_existing=True,
    )
    logger.info("✓ Scheduled: Newsletter sending daily at 10:20 AM PST")

    # Job 4: Regenerate opposing viewpoints daily at 3:00 AM PST
    scheduler.add_job(
        func=regenerate_viewpoints_job,
        trigger=CronTrigger(hour=3, minute=0, timezone='America/Los_Angeles'),
        id='regenerate_viewpoints',
        name='Regenerate Opposing Viewpoints',
        replace_existing=True,
        max_instances=1,
    )
    logger.info("✓ Scheduled: Viewpoint regeneration daily at 3:00 AM PST")
    logger.info("  └─> Refreshes cached viewpoint relationships with fresh AI analysis")

    # Start the scheduler
    scheduler.start()
    logger.info("🚀 APScheduler started successfully!")
    logger.info("📋 Note: Individual jobs can still be triggered manually via /admin/jobs/* endpoints")

    # Log next run times
    for job in scheduler.get_jobs():
        logger.info(f"   {job.name}: Next run at {job.next_run_time}")


def stop_scheduler():
    """Stop the scheduler gracefully"""
    if scheduler.running:
        scheduler.shutdown(wait=True)
        logger.info("Scheduler stopped")


def get_job_status():
    """Get status of all scheduled jobs"""
    if not scheduler.running:
        return {"status": "stopped", "jobs": []}

    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": str(job.next_run_time),
            "trigger": str(job.trigger),
        })

    return {
        "status": "running",
        "jobs": jobs
    }
