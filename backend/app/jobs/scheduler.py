"""
APScheduler configuration and job scheduling.
Sets up 4 separate background jobs with different schedules.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from app.jobs.tasks import scrape_job, extract_job, analyze_job, framework_job, newsletter_job
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

    logger.info("Initializing APScheduler with 5 jobs...")

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

    # Job 5: Send newsletters daily at 7am
    scheduler.add_job(
        func=newsletter_job,
        trigger=CronTrigger(hour=settings.newsletter_send_hour, minute=0),
        id='send_newsletters',
        name='Send Newsletters',
        replace_existing=True,
    )
    logger.info(f"✓ Scheduled: Newsletter sending daily at {settings.newsletter_send_hour}:00 AM")

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
