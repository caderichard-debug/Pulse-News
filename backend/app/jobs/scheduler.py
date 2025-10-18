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
    process_articles_job
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

    SIMPLIFIED WORKFLOW (chained jobs):
    - Scrape job runs every 3 hours
      → Auto-chains to extraction job
        → Auto-chains to monolithic processing job (runs 5 tasks concurrently)
    - Newsletter job runs daily at 10:20 AM PST
    """
    if scheduler.running:
        logger.warning("Scheduler is already running")
        return

    logger.info("Initializing APScheduler with simplified chained workflow...")

    # Job 1: Scrape RSS feeds every 3 hours (chains to extraction → processing)
    scheduler.add_job(
        func=scrape_job,
        trigger=IntervalTrigger(hours=settings.scrape_interval_hours),
        id='scrape_rss',
        name='Scrape RSS Feeds (chains to extraction → processing)',
        replace_existing=True,
        max_instances=1,  # Only one instance at a time
    )
    logger.info(f"✓ Scheduled: RSS scraping every {settings.scrape_interval_hours} hours")
    logger.info("  └─> Auto-chains: extraction → processing (5 tasks concurrently)")

    # Job 2: Send newsletters daily at 10:20 AM PST
    scheduler.add_job(
        func=newsletter_job,
        trigger=CronTrigger(hour=10, minute=20, timezone='America/Los_Angeles'),
        id='send_newsletters',
        name='Send Newsletters',
        replace_existing=True,
    )
    logger.info("✓ Scheduled: Newsletter sending daily at 10:20 AM PST")

    # Start the scheduler
    scheduler.start()
    logger.info("🚀 APScheduler started successfully!")
    logger.info("📋 Note: Individual jobs (analyze, frameworks, etc.) can still be triggered manually via /admin/jobs/* endpoints")

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
