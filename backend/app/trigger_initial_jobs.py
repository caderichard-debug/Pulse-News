"""
Trigger all background jobs immediately after initial deployment.

This script runs once after the first deployment to populate the database
with articles, analysis, and other data. It checks if this is the first run
by looking for existing articles.
"""

import logging
import time
import sys
from sqlalchemy import text
from .database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def should_trigger_jobs() -> bool:
    """Check if we should trigger initial jobs (only if database is empty)."""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM articles"))
        count = result.scalar()
        return count == 0


def trigger_all_jobs():
    """Trigger all background jobs to populate the database."""
    import requests
    import os

    # Get the base URL (use localhost in docker, or the service URL)
    base_url = os.getenv("BASE_URL", "http://localhost:8000")

    logger.info("=== Triggering Initial Background Jobs ===")

    jobs = [
        ("Scrape RSS Feeds", f"{base_url}/admin/jobs/scrape"),
        ("Extract Article Content", f"{base_url}/admin/jobs/extract"),
        ("AI Analysis", f"{base_url}/admin/jobs/analyze"),
        ("Verify Statistics", f"{base_url}/admin/jobs/verify-statistics"),
        ("Cluster Articles", f"{base_url}/admin/jobs/cluster"),
        ("Generate Context", f"{base_url}/admin/jobs/generate-context"),
        ("Update Frameworks", f"{base_url}/admin/jobs/update-frameworks"),
    ]

    for job_name, url in jobs:
        try:
            logger.info(f"Triggering: {job_name}...")
            response = requests.post(url, timeout=30)

            if response.status_code == 200:
                logger.info(f"✓ {job_name} triggered successfully")
            else:
                logger.warning(f"⚠️  {job_name} returned status {response.status_code}")

            # Wait between jobs to avoid overwhelming the system
            time.sleep(2)

        except requests.exceptions.RequestException as e:
            logger.error(f"✗ Failed to trigger {job_name}: {e}")

    logger.info("=== Initial job triggers complete ===\n")
    logger.info("Jobs will run in the background. Check logs for progress.")


if __name__ == "__main__":
    try:
        if should_trigger_jobs():
            logger.info("Empty database detected - triggering initial jobs")
            # Wait for the server to be fully ready
            logger.info("Waiting 10 seconds for server to be fully ready...")
            time.sleep(10)
            trigger_all_jobs()
        else:
            logger.info("Articles already exist - skipping initial job triggers")
    except Exception as e:
        logger.error(f"Failed to trigger initial jobs: {e}", exc_info=True)
        sys.exit(1)
