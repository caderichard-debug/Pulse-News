"""
Background job task definitions.
These are the actual functions that get executed by the scheduler.
"""

from app.services.rss_scraper import scrape_all_active_sources
from app.services.article_extractor import process_pending_articles
import logging

logger = logging.getLogger(__name__)


def scrape_job():
    """
    Job 1: Scrape RSS feeds from all active sources.
    Scheduled to run every 3 hours.
    """
    try:
        logger.info("=" * 60)
        logger.info("Starting scheduled RSS scrape job")
        logger.info("=" * 60)

        count = scrape_all_active_sources()

        logger.info("=" * 60)
        logger.info(f"RSS scrape job completed: {count} new articles")
        logger.info("=" * 60)

        return {"success": True, "articles_scraped": count}
    except Exception as e:
        logger.error(f"RSS scrape job failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


def extract_job():
    """
    Job 2: Extract full article content from pending articles.
    Scheduled to run every 4 hours.
    """
    try:
        logger.info("=" * 60)
        logger.info("Starting scheduled article extraction job")
        logger.info("=" * 60)

        # Process up to 50 articles per run (adjust based on performance)
        count = process_pending_articles(batch_size=50, delay=1.0)

        logger.info("=" * 60)
        logger.info(f"Article extraction job completed: {count} articles processed")
        logger.info("=" * 60)

        return {"success": True, "articles_processed": count}
    except Exception as e:
        logger.error(f"Article extraction job failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


def analyze_job():
    """
    Job 3: Analyze articles with AI (sentiment, bias, frameworks).
    Scheduled to run every 6 hours.
    """
    try:
        logger.info("=" * 60)
        logger.info("Starting scheduled AI analysis job")
        logger.info("=" * 60)

        from app.services.ai_analyzer import analyze_articles_batch

        # Process up to 10 articles (2 batches of 5)
        total_analyzed = 0
        for i in range(2):
            count = analyze_articles_batch(batch_size=5)
            total_analyzed += count
            if count == 0:
                break  # No more articles to process

        logger.info("=" * 60)
        logger.info(f"AI analysis job completed: {total_analyzed} articles analyzed")
        logger.info("=" * 60)

        return {"success": True, "articles_analyzed": total_analyzed}
    except Exception as e:
        logger.error(f"AI analysis job failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


def framework_job():
    """
    Job 4: Update frameworks and map articles to ethical debates.
    Scheduled to run daily at 2am.

    This is the "competitive edge" - mapping articles to underlying ethical debates.
    """
    try:
        logger.info("=" * 60)
        logger.info("Starting scheduled framework update job")
        logger.info("=" * 60)

        from app.services.framework_generator import (
            map_articles_to_frameworks,
            discover_new_frameworks
        )

        # Step 1: Map recent analyzed articles to existing frameworks
        logger.info("Step 1: Mapping articles to existing frameworks...")
        mappings_created = map_articles_to_frameworks(limit=20)
        logger.info(f"Created {mappings_created} framework mappings")

        # Step 2: Discover new frameworks (only on Sundays to avoid noise)
        from datetime import datetime
        if datetime.utcnow().weekday() == 6:  # Sunday
            logger.info("Step 2: Discovering new frameworks (weekly task)...")
            new_frameworks = discover_new_frameworks(min_articles=50)
            logger.info(f"Discovered {new_frameworks} new frameworks")
        else:
            logger.info("Step 2: Skipping framework discovery (only runs on Sundays)")
            new_frameworks = 0

        logger.info("=" * 60)
        logger.info(f"Framework update job completed: {mappings_created} mappings, {new_frameworks} new frameworks")
        logger.info("=" * 60)

        return {
            "success": True,
            "mappings_created": mappings_created,
            "frameworks_discovered": new_frameworks
        }
    except Exception as e:
        logger.error(f"Framework update job failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


def newsletter_job():
    """
    Job 5: Send daily newsletters to users.
    Scheduled to run daily at 7am.
    """
    try:
        logger.info("=" * 60)
        logger.info("Starting scheduled newsletter job")
        logger.info("=" * 60)

        from app.services.newsletter_service import generate_and_send_newsletters

        # Generate and send newsletters
        stats = generate_and_send_newsletters()

        logger.info("=" * 60)
        logger.info(
            f"Newsletter job completed: {stats['generated']} generated, "
            f"{stats['sent']} sent, {stats['failed']} failed"
        )
        logger.info("=" * 60)

        return {
            "success": True,
            "newsletters_generated": stats["generated"],
            "newsletters_sent": stats["sent"],
            "newsletters_failed": stats["failed"]
        }
    except Exception as e:
        logger.error(f"Newsletter job failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}
