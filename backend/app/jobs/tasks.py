"""
Background job task definitions.
These are the actual functions that get executed by the scheduler.
"""

from sqlmodel import Session
from app.database import engine
from app.services.rss_scraper import scrape_all_active_sources
from app.services.article_extractor import process_pending_articles
import logging

logger = logging.getLogger(__name__)


def scrape_job(session: Session = None):
    """
    Job 1: Scrape RSS feeds from all active sources.
    Scheduled to run every 3 hours.

    Args:
        session: Optional session (for testing). If None, creates new session.
    """
    try:
        logger.info("=" * 60)
        logger.info("Starting scheduled RSS scrape job")
        logger.info("=" * 60)

        if session is None:
            with Session(engine) as session:
                count = scrape_all_active_sources(session)
        else:
            count = scrape_all_active_sources(session)

        logger.info("=" * 60)
        logger.info(f"RSS scrape job completed: {count} new articles")
        logger.info("=" * 60)

        return {"success": True, "articles_scraped": count}
    except Exception as e:
        logger.error(f"RSS scrape job failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


def extract_job(session: Session = None):
    """
    Job 2: Extract full article content from pending articles.
    Scheduled to run every 4 hours.

    Args:
        session: Optional session (for testing). If None, creates new session.
    """
    try:
        logger.info("=" * 60)
        logger.info("Starting scheduled article extraction job")
        logger.info("=" * 60)

        # Process up to 50 articles per run (adjust based on performance)
        if session is None:
            with Session(engine) as session:
                count = process_pending_articles(session, batch_size=50, delay=1.0)
        else:
            count = process_pending_articles(session, batch_size=50, delay=1.0)

        logger.info("=" * 60)
        logger.info(f"Article extraction job completed: {count} articles processed")
        logger.info("=" * 60)

        return {"success": True, "articles_processed": count}
    except Exception as e:
        logger.error(f"Article extraction job failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


def analyze_job(session: Session = None):
    """
    Job 3: Analyze articles with AI (sentiment, bias, frameworks).
    Scheduled to run every 6 hours.

    Args:
        session: Optional session (for testing). If None, creates new session.
    """
    try:
        logger.info("=" * 60)
        logger.info("Starting scheduled AI analysis job")
        logger.info("=" * 60)

        from app.services.ai_analyzer import analyze_articles_batch

        # Process up to 10 articles (2 batches of 5)
        total_analyzed = 0

        if session is None:
            with Session(engine) as session:
                for i in range(2):
                    count = analyze_articles_batch(session, batch_size=5)
                    total_analyzed += count
                    if count == 0:
                        break  # No more articles to process
        else:
            for i in range(2):
                count = analyze_articles_batch(session, batch_size=5)
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


def framework_job(session: Session = None):
    """
    Job 4: Update frameworks and map articles to ethical debates.
    Scheduled to run daily at 2am.

    This is the "competitive edge" - mapping articles to underlying ethical debates.

    Args:
        session: Optional session (for testing). If None, creates new session.
    """
    try:
        logger.info("=" * 60)
        logger.info("Starting scheduled framework update job")
        logger.info("=" * 60)

        from app.services.framework_generator import (
            map_articles_to_frameworks,
            discover_new_frameworks
        )
        from datetime import datetime

        if session is None:
            with Session(engine) as session:
                # Step 1: Map recent analyzed articles to existing frameworks
                logger.info("Step 1: Mapping articles to existing frameworks...")
                mappings_created = map_articles_to_frameworks(session, limit=20)
                logger.info(f"Created {mappings_created} framework mappings")

                # Step 2: Discover new frameworks (only on Sundays to avoid noise)
                if datetime.utcnow().weekday() == 6:  # Sunday
                    logger.info("Step 2: Discovering new frameworks (weekly task)...")
                    new_frameworks = discover_new_frameworks(session, min_articles=50)
                    logger.info(f"Discovered {new_frameworks} new frameworks")
                else:
                    logger.info("Step 2: Skipping framework discovery (only runs on Sundays)")
                    new_frameworks = 0
        else:
            # Step 1: Map recent analyzed articles to existing frameworks
            logger.info("Step 1: Mapping articles to existing frameworks...")
            mappings_created = map_articles_to_frameworks(session, limit=20)
            logger.info(f"Created {mappings_created} framework mappings")

            # Step 2: Discover new frameworks (only on Sundays to avoid noise)
            if datetime.utcnow().weekday() == 6:  # Sunday
                logger.info("Step 2: Discovering new frameworks (weekly task)...")
                new_frameworks = discover_new_frameworks(session, min_articles=50)
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


def statistics_verification_job(session: Session = None):
    """
    Job 6: Extract and verify statistics from articles.
    Scheduled to run every 6 hours.

    Args:
        session: Optional session (for testing). If None, creates new session.
    """
    try:
        logger.info("=" * 60)
        logger.info("Starting scheduled statistics verification job")
        logger.info("=" * 60)

        from app.services.statistics_verifier import process_pending_verifications

        if session is None:
            with Session(engine) as session:
                # Process up to 10 articles per run
                stats = process_pending_verifications(session, limit=10)
        else:
            stats = process_pending_verifications(session, limit=10)

        logger.info("=" * 60)
        logger.info(
            f"Statistics verification job completed: "
            f"{stats['articles_processed']} articles, "
            f"{stats['statistics_extracted']} statistics, "
            f"{stats['statistics_verified']} verified"
        )
        logger.info("=" * 60)

        return {
            "success": True,
            "articles_processed": stats["articles_processed"],
            "statistics_extracted": stats["statistics_extracted"],
            "statistics_verified": stats["statistics_verified"]
        }
    except Exception as e:
        logger.error(f"Statistics verification job failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


def article_clustering_job(session: Session = None):
    """
    Job 7: Cluster similar articles for cross-source comparison.
    Scheduled to run every 4 hours.

    Args:
        session: Optional session (for testing). If None, creates new session.
    """
    try:
        logger.info("=" * 60)
        logger.info("Starting scheduled article clustering job")
        logger.info("=" * 60)

        from app.services.article_clusterer import process_pending_clustering

        if session is None:
            with Session(engine) as session:
                # Process up to 20 articles per run
                stats = process_pending_clustering(session, limit=20)
        else:
            stats = process_pending_clustering(session, limit=20)

        logger.info("=" * 60)
        logger.info(
            f"Article clustering job completed: "
            f"{stats['articles_processed']} articles, "
            f"{stats['clusters_created']} new clusters, "
            f"{stats['articles_clustered']} articles clustered"
        )
        logger.info("=" * 60)

        return {
            "success": True,
            "articles_processed": stats["articles_processed"],
            "clusters_created": stats["clusters_created"],
            "articles_clustered": stats["articles_clustered"]
        }
    except Exception as e:
        logger.error(f"Article clustering job failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


def context_generation_job(session: Session = None):
    """
    Job 8: Generate background context for articles.
    Scheduled to run every 8 hours.

    Args:
        session: Optional session (for testing). If None, creates new session.
    """
    try:
        logger.info("=" * 60)
        logger.info("Starting scheduled context generation job")
        logger.info("=" * 60)

        from app.services.context_generator import process_article_contexts

        if session is None:
            with Session(engine) as session:
                # Process up to 5 articles per run (context generation is expensive)
                stats = process_article_contexts(session, limit=5)
        else:
            stats = process_article_contexts(session, limit=5)

        logger.info("=" * 60)
        logger.info(
            f"Context generation job completed: "
            f"{stats['articles_processed']} articles, "
            f"{stats['contexts_generated']} contexts, "
            f"{stats['total_tokens']} tokens used"
        )
        logger.info("=" * 60)

        return {
            "success": True,
            "articles_processed": stats["articles_processed"],
            "contexts_generated": stats["contexts_generated"],
            "tokens_used": stats["total_tokens"]
        }
    except Exception as e:
        logger.error(f"Context generation job failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}
