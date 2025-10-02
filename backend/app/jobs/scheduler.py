"""
APScheduler configuration and job scheduling.
Sets up 8 separate background jobs with different schedules.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from app.jobs.tasks import (
    scrape_job,
    extract_job,
    analyze_job,
    framework_job,
    newsletter_job,
    statistics_verification_job,
    article_clustering_job,
    context_generation_job
)
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Create scheduler instance
scheduler = BackgroundScheduler()


def start_scheduler():
    """
    Initialize and start the background job scheduler.
    This should be called once when the application starts.
    """
    if scheduler.running:
        logger.warning("Scheduler is already running")
        return

    logger.info("Initializing APScheduler with 8 jobs...")

    # Job 1: Scrape RSS feeds every 3 hours
    scheduler.add_job(
        func=scrape_job,
        trigger=IntervalTrigger(hours=settings.scrape_interval_hours),
        id='scrape_rss',
        name='Scrape RSS Feeds',
        replace_existing=True,
        max_instances=1,  # Only one instance at a time
    )
    logger.info(f"✓ Scheduled: RSS scraping every {settings.scrape_interval_hours} hours")

    # Job 2: Extract article content every 4 hours
    scheduler.add_job(
        func=extract_job,
        trigger=IntervalTrigger(hours=settings.process_interval_hours),
        id='extract_articles',
        name='Extract Article Content',
        replace_existing=True,
        max_instances=1,  # Prevent overlapping runs
    )
    logger.info(f"✓ Scheduled: Article extraction every {settings.process_interval_hours} hours")

    # Job 3: AI analysis every 6 hours (after extraction has run)
    scheduler.add_job(
        func=analyze_job,
        trigger=IntervalTrigger(hours=6),
        id='analyze_articles',
        name='AI Article Analysis',
        replace_existing=True,
        max_instances=1,
    )
    logger.info("✓ Scheduled: AI analysis every 6 hours")

    # Job 4: Update frameworks daily at 2am
    scheduler.add_job(
        func=framework_job,
        trigger=CronTrigger(hour=2, minute=0),
        id='update_frameworks',
        name='Update Frameworks',
        replace_existing=True,
    )
    logger.info("✓ Scheduled: Framework updates daily at 2:00 AM")

    # Job 5: Send newsletters daily at 10:20 AM PST
    scheduler.add_job(
        func=newsletter_job,
        trigger=CronTrigger(hour=10, minute=20, timezone='America/Los_Angeles'),
        id='send_newsletters',
        name='Send Newsletters',
        replace_existing=True,
    )
    logger.info("✓ Scheduled: Newsletter sending daily at 10:20 AM PST")

    # Job 6: Statistics verification every 6 hours
    scheduler.add_job(
        func=statistics_verification_job,
        trigger=IntervalTrigger(hours=6),
        id='verify_statistics',
        name='Verify Statistics',
        replace_existing=True,
        max_instances=1,
    )
    logger.info("✓ Scheduled: Statistics verification every 6 hours")

    # Job 7: Article clustering every 4 hours
    scheduler.add_job(
        func=article_clustering_job,
        trigger=IntervalTrigger(hours=4),
        id='cluster_articles',
        name='Cluster Articles',
        replace_existing=True,
        max_instances=1,
    )
    logger.info("✓ Scheduled: Article clustering every 4 hours")

    # Job 8: Context generation every 8 hours
    scheduler.add_job(
        func=context_generation_job,
        trigger=IntervalTrigger(hours=8),
        id='generate_context',
        name='Generate Context',
        replace_existing=True,
        max_instances=1,
    )
    logger.info("✓ Scheduled: Context generation every 8 hours")

    # Start the scheduler
    scheduler.start()
    logger.info("🚀 APScheduler started successfully!")

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
