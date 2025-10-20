"""
Background job task definitions.
These are the actual functions that get executed by the scheduler.

All jobs are wrapped with execution tracking that creates JobExecutionHistory records.
"""

from sqlmodel import Session
from ..database import engine
from ..services.rss_scraper import scrape_all_active_sources
from ..services.article_extractor import process_pending_articles
from ..models import JobExecutionHistory
from datetime import datetime
import logging
from functools import wraps
from typing import Callable, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

logger = logging.getLogger(__name__)


def track_job_execution(job_id: str, job_name: str):
    """
    Decorator to track job execution in JobExecutionHistory table.

    Creates a history record before execution, updates it on completion.
    Captures success/failure status, duration, and result metrics.

    Also implements job locking to prevent concurrent executions of the same job.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(session: Session = None, *args, **kwargs) -> Dict[str, Any]:
            # Use PostgreSQL advisory lock to prevent concurrent executions
            # Convert job_id string to integer hash for advisory lock
            lock_id = hash(job_id) % (2**31)  # Keep within PostgreSQL bigint range

            with Session(engine) as lock_session:
                from sqlmodel import select, text

                # Try to acquire advisory lock (non-blocking)
                result = lock_session.exec(text(f"SELECT pg_try_advisory_lock({lock_id})")).first()
                lock_acquired = result[0] if result else False

                if not lock_acquired:
                    logger.warning(f"Job {job_id} is already running (could not acquire lock). Skipping this execution.")
                    return {
                        "success": False,
                        "error": "Job already running (lock not acquired)",
                        "skipped": True
                    }

                try:
                    # Double-check database for safety
                    running_job = lock_session.exec(
                        select(JobExecutionHistory)
                        .where(JobExecutionHistory.job_id == job_id)
                        .where(JobExecutionHistory.status == "running")
                    ).first()

                    if running_job:
                        logger.warning(f"Job {job_id} is already running (started at {running_job.started_at}). Skipping this execution.")
                        lock_session.exec(text(f"SELECT pg_advisory_unlock({lock_id})"))
                        return {
                            "success": False,
                            "error": f"Job already running (started at {running_job.started_at})",
                            "skipped": True
                        }

                    # Create execution history record
                    history = JobExecutionHistory(
                        job_id=job_id,
                        job_name=job_name,
                        started_at=datetime.utcnow(),
                        status="running",
                        triggered_by="scheduler"
                    )
                    lock_session.add(history)
                    lock_session.commit()
                    lock_session.refresh(history)
                    history_id = history.id
                finally:
                    # Release the advisory lock after creating the record
                    lock_session.exec(text(f"SELECT pg_advisory_unlock({lock_id})"))
                    lock_session.commit()

            # Execute the job
            try:
                result = func(session=session, *args, **kwargs)

                # Update history with success
                with Session(engine) as history_session:
                    history = history_session.get(JobExecutionHistory, history_id)
                    history.status = "success" if result.get("success", True) else "failed"
                    history.completed_at = datetime.utcnow()
                    history.duration_seconds = (
                        history.completed_at - history.started_at
                    ).total_seconds()
                    history.result_data = str(result)

                    # Extract metrics from result
                    if isinstance(result, dict):
                        history.items_processed = (
                            result.get("articles_scraped") or
                            result.get("articles_processed") or
                            result.get("articles_analyzed") or
                            result.get("mappings_created") or
                            result.get("stats_extracted") or
                            result.get("articles_clustered") or
                            result.get("contexts_generated")
                        )
                        history.tokens_used = result.get("tokens_used") or result.get("total_tokens")

                    history_session.add(history)
                    history_session.commit()

                return result

            except Exception as e:
                # Update history with failure
                with Session(engine) as history_session:
                    history = history_session.get(JobExecutionHistory, history_id)
                    history.status = "failed"
                    history.completed_at = datetime.utcnow()
                    history.duration_seconds = (
                        history.completed_at - history.started_at
                    ).total_seconds()
                    history.error_message = str(e)
                    history_session.add(history)
                    history_session.commit()

                # Re-raise the exception
                raise

        return wrapper
    return decorator


@track_job_execution(job_id="scrape_rss", job_name="Scrape RSS Feeds")
def scrape_job(session: Session = None, chain_extraction: bool = True):
    """
    Job 1: Scrape RSS feeds from all active sources.
    Scheduled to run every 3 hours.

    Args:
        session: Optional session (for testing). If None, creates new session.
        chain_extraction: If True, automatically triggers extraction job after completion.
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

        # Chain extraction job if new articles were found
        if chain_extraction and count > 0:
            logger.info("Chaining extraction job...")
            try:
                extract_job(session=None, chain_analysis=True)
            except Exception as e:
                logger.error(f"Chained extraction job failed: {e}", exc_info=True)
                # Don't fail the scrape job if chained job fails

        return {"success": True, "articles_scraped": count}
    except Exception as e:
        logger.error(f"RSS scrape job failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


@track_job_execution(job_id="extract_articles", job_name="Extract Article Content")
def extract_job(session: Session = None, chain_analysis: bool = False):
    """
    Job 2: Extract full article content from pending articles.

    Args:
        session: Optional session (for testing). If None, creates new session.
        chain_analysis: If True, automatically triggers analysis job after completion.
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

        # Chain analysis job if articles were extracted
        if chain_analysis and count > 0:
            logger.info("Chaining analysis job...")
            try:
                analyze_job(session=None, chain_processing=True)
            except Exception as e:
                logger.error(f"Chained analysis job failed: {e}", exc_info=True)
                # Don't fail the extraction job if chained job fails

        return {"success": True, "articles_processed": count}
    except Exception as e:
        logger.error(f"Article extraction job failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


@track_job_execution(job_id="analyze_articles", job_name="AI Article Analysis")
def analyze_job(session: Session = None, chain_processing: bool = False):
    """
    Job 3: Analyze articles with AI (sentiment, bias, summary).

    This job processes ALL unanalyzed articles in the database by running
    batches until no more articles remain. This prevents backlogs of
    "analysis pending" articles.

    Args:
        session: Optional session (for testing). If None, creates new session.
        chain_processing: If True, automatically triggers processing job after completion.
    """
    try:
        logger.info("=" * 60)
        logger.info("Starting scheduled AI analysis job")
        logger.info("=" * 60)

        from ..services.ai_analyzer import analyze_articles_batch, get_unanalyzed_article_count

        total_analyzed = 0
        batch_num = 0

        # Get initial count of unanalyzed articles
        if session is None:
            with Session(engine) as temp_session:
                initial_count = get_unanalyzed_article_count(temp_session)
        else:
            initial_count = get_unanalyzed_article_count(session)

        logger.info(f"Found {initial_count} unanalyzed articles in database")

        # Process batches until no more articles remain
        if session is None:
            with Session(engine) as session:
                while True:
                    batch_num += 1
                    logger.info(f"Processing batch {batch_num}...")
                    count = analyze_articles_batch(session, batch_size=5)
                    total_analyzed += count

                    if count == 0:
                        logger.info("No more articles to analyze")
                        break  # No more articles to process

                    # Add a small delay between batches to avoid rate limiting
                    if count > 0:
                        time.sleep(1)
        else:
            while True:
                batch_num += 1
                logger.info(f"Processing batch {batch_num}...")
                count = analyze_articles_batch(session, batch_size=5)
                total_analyzed += count

                if count == 0:
                    logger.info("No more articles to analyze")
                    break  # No more articles to process

                # Add a small delay between batches to avoid rate limiting
                if count > 0:
                    time.sleep(1)

        logger.info("=" * 60)
        logger.info(f"AI analysis job completed: {total_analyzed}/{initial_count} articles analyzed in {batch_num} batches")
        logger.info("=" * 60)

        # Chain processing job if articles were analyzed
        if chain_processing and total_analyzed > 0:
            logger.info("Chaining processing job...")
            try:
                process_articles_job(session=None)
            except Exception as e:
                logger.error(f"Chained processing job failed: {e}", exc_info=True)
                # Don't fail the analysis job if chained job fails

        return {"success": True, "articles_analyzed": total_analyzed}
    except Exception as e:
        logger.error(f"AI analysis job failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


@track_job_execution(job_id="framework_mapping", job_name="Framework Mapping & Discovery")
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

        from ..services.framework_generator import (
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


@track_job_execution(job_id="send_newsletters", job_name="Send Daily Newsletters")
def newsletter_job(session: Session = None):
    """
    Job 5: Send daily newsletters to users.
    Scheduled to run daily at 7am.
    """
    try:
        logger.info("=" * 60)
        logger.info("Starting scheduled newsletter job")
        logger.info("=" * 60)

        from ..services.newsletter_service import generate_and_send_newsletters

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


@track_job_execution(job_id="verify_statistics", job_name="Statistics Verification")
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

        from ..services.statistics_verifier import process_pending_verifications

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
            f"{stats['stats_extracted']} statistics, "
            f"{stats['stats_verified']} verified"
        )
        logger.info("=" * 60)

        return {
            "success": True,
            "articles_processed": stats["articles_processed"],
            "statistics_extracted": stats["stats_extracted"],
            "statistics_verified": stats["stats_verified"]
        }
    except Exception as e:
        logger.error(f"Statistics verification job failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


@track_job_execution(job_id="cluster_articles", job_name="Article Clustering")
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

        from ..services.article_clusterer import process_article_clustering

        if session is None:
            with Session(engine) as session:
                # Process up to 20 articles per run
                stats = process_article_clustering(session, limit=20)
        else:
            stats = process_article_clustering(session, limit=20)

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


@track_job_execution(job_id="generate_context", job_name="Context Generation")
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

        from ..services.context_generator import process_article_contexts

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


@track_job_execution(job_id="process_articles", job_name="Process Articles (Post-Analysis)")
def process_articles_job(session: Session = None):
    """
    Job 4: Article processing job that runs post-analysis tasks concurrently.

    This job combines (requires ArticleAnalysis to exist):
    - Framework mapping
    - Statistics verification
    - Article clustering
    - Context generation

    All tasks are run in parallel using ThreadPoolExecutor for maximum efficiency.

    Args:
        session: Optional session (for testing). If None, creates new session.
    """
    try:
        logger.info("=" * 60)
        logger.info("Starting article processing job (post-analysis)")
        logger.info("=" * 60)

        def run_frameworks():
            """Map articles to ethical frameworks"""
            try:
                from ..services.framework_generator import map_articles_to_frameworks, discover_new_frameworks
                from sqlmodel import select
                from ..models import Article, ArticleAnalysis, ArticleFrameworkLink

                with Session(engine) as task_session:
                    # Count unmapped articles
                    unmapped_articles = task_session.exec(
                        select(Article)
                        .join(ArticleAnalysis)
                        .where(~Article.id.in_(
                            select(ArticleFrameworkLink.article_id)
                        ))
                    ).all()
                    initial_count = len(unmapped_articles)
                    logger.info(f"[Frameworks] Found {initial_count} unmapped articles")

                    # Process all unmapped articles in batches
                    total_mappings = 0
                    batch_num = 0
                    while True:
                        batch_num += 1
                        logger.info(f"[Frameworks] Processing batch {batch_num}...")
                        count = map_articles_to_frameworks(task_session, limit=20)
                        total_mappings += count
                        if count == 0:
                            break
                        time.sleep(0.5)  # Brief delay between batches

                    # Discover new frameworks on Sundays
                    new_frameworks = 0
                    if datetime.utcnow().weekday() == 6:
                        logger.info("[Frameworks] Sunday - discovering new frameworks...")
                        new_frameworks = discover_new_frameworks(task_session, min_articles=50)

                    logger.info(f"[Frameworks] Completed: {total_mappings} mappings, {new_frameworks} new frameworks")
                    return {
                        "task": "frameworks",
                        "mappings_created": total_mappings,
                        "frameworks_discovered": new_frameworks
                    }
            except Exception as e:
                logger.error(f"[Frameworks] Failed: {e}", exc_info=True)
                return {"task": "frameworks", "error": str(e)}

        def run_statistics():
            """Verify statistics in articles"""
            try:
                from ..services.statistics_verifier import process_pending_verifications
                from sqlmodel import select
                from ..models import Article, ArticleAnalysis

                with Session(engine) as task_session:
                    # Count articles without statistics verification
                    pending_articles = task_session.exec(
                        select(Article)
                        .join(ArticleAnalysis)
                        .where(ArticleAnalysis.stats_verification_date.is_(None))
                    ).all()
                    initial_count = len(pending_articles)
                    logger.info(f"[Statistics] Found {initial_count} articles pending verification")

                    # Process all pending articles in batches
                    total_stats = {
                        "articles_processed": 0,
                        "stats_extracted": 0,
                        "stats_verified": 0
                    }
                    batch_num = 0
                    while True:
                        batch_num += 1
                        logger.info(f"[Statistics] Processing batch {batch_num}...")
                        stats = process_pending_verifications(task_session, limit=10)

                        total_stats["articles_processed"] += stats["articles_processed"]
                        total_stats["stats_extracted"] += stats["stats_extracted"]
                        total_stats["stats_verified"] += stats["stats_verified"]

                        if stats["articles_processed"] == 0:
                            break
                        time.sleep(1)  # Rate limiting for API calls

                    logger.info(
                        f"[Statistics] Completed: {total_stats['articles_processed']} articles, "
                        f"{total_stats['stats_extracted']} extracted, {total_stats['stats_verified']} verified"
                    )
                    return {
                        "task": "statistics",
                        "articles_processed": total_stats["articles_processed"],
                        "stats_extracted": total_stats["stats_extracted"],
                        "stats_verified": total_stats["stats_verified"]
                    }
            except Exception as e:
                logger.error(f"[Statistics] Failed: {e}", exc_info=True)
                return {"task": "statistics", "error": str(e)}

        def run_clustering():
            """Cluster similar articles"""
            try:
                from ..services.article_clusterer import process_article_clustering
                from sqlmodel import select
                from ..models import Article, ArticleAnalysis, ArticleClusterMember

                with Session(engine) as task_session:
                    # Count unclustered articles
                    unclustered_articles = task_session.exec(
                        select(Article)
                        .join(ArticleAnalysis)
                        .where(~Article.id.in_(
                            select(ArticleClusterMember.article_id)
                        ))
                    ).all()
                    initial_count = len(unclustered_articles)
                    logger.info(f"[Clustering] Found {initial_count} unclustered articles")

                    # Process all unclustered articles in batches
                    total_stats = {
                        "articles_processed": 0,
                        "clusters_created": 0,
                        "articles_clustered": 0
                    }
                    batch_num = 0
                    while True:
                        batch_num += 1
                        logger.info(f"[Clustering] Processing batch {batch_num}...")
                        stats = process_article_clustering(task_session, limit=20)

                        total_stats["articles_processed"] += stats["articles_processed"]
                        total_stats["clusters_created"] += stats["clusters_created"]
                        total_stats["articles_clustered"] += stats["articles_clustered"]

                        if stats["articles_processed"] == 0:
                            break
                        time.sleep(0.5)  # Brief delay between batches

                    logger.info(
                        f"[Clustering] Completed: {total_stats['articles_processed']} articles, "
                        f"{total_stats['clusters_created']} clusters, {total_stats['articles_clustered']} clustered"
                    )
                    return {
                        "task": "clustering",
                        "articles_processed": total_stats["articles_processed"],
                        "clusters_created": total_stats["clusters_created"],
                        "articles_clustered": total_stats["articles_clustered"]
                    }
            except Exception as e:
                logger.error(f"[Clustering] Failed: {e}", exc_info=True)
                return {"task": "clustering", "error": str(e)}

        def run_context():
            """Generate article contexts"""
            try:
                from ..services.context_generator import process_article_contexts
                from sqlmodel import select
                from ..models import ArticleAnalysis

                with Session(engine) as task_session:
                    # Count articles without context
                    no_context_articles = task_session.exec(
                        select(ArticleAnalysis)
                        .where(ArticleAnalysis.has_context == False)
                    ).all()
                    initial_count = len(no_context_articles)
                    logger.info(f"[Context] Found {initial_count} articles without context")

                    # Process all articles without context in batches
                    total_stats = {
                        "articles_processed": 0,
                        "contexts_generated": 0,
                        "total_tokens": 0
                    }
                    batch_num = 0
                    while True:
                        batch_num += 1
                        logger.info(f"[Context] Processing batch {batch_num}...")
                        stats = process_article_contexts(task_session, limit=5)

                        total_stats["articles_processed"] += stats["articles_processed"]
                        total_stats["contexts_generated"] += stats["contexts_generated"]
                        total_stats["total_tokens"] += stats["total_tokens"]

                        if stats["articles_processed"] == 0:
                            break
                        time.sleep(1)  # Rate limiting for API calls

                    logger.info(
                        f"[Context] Completed: {total_stats['articles_processed']} articles, "
                        f"{total_stats['contexts_generated']} contexts, {total_stats['total_tokens']} tokens"
                    )
                    return {
                        "task": "context",
                        "articles_processed": total_stats["articles_processed"],
                        "contexts_generated": total_stats["contexts_generated"],
                        "tokens_used": total_stats["total_tokens"]
                    }
            except Exception as e:
                logger.error(f"[Context] Failed: {e}", exc_info=True)
                return {"task": "context", "error": str(e)}

        # Execute all tasks concurrently (4 post-analysis tasks)
        tasks = [run_frameworks, run_statistics, run_clustering, run_context]
        results = []

        logger.info(f"Executing {len(tasks)} post-analysis tasks concurrently...")

        with ThreadPoolExecutor(max_workers=4) as executor:
            # Submit all tasks
            futures = {executor.submit(task): task.__name__ for task in tasks}

            # Collect results as they complete
            for future in as_completed(futures):
                task_name = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    logger.info(f"✓ Task completed: {task_name}")
                except Exception as e:
                    logger.error(f"✗ Task failed: {task_name} - {e}")
                    results.append({"task": task_name, "error": str(e)})

        logger.info("=" * 60)
        logger.info("Article processing job completed")
        logger.info(f"Results: {len([r for r in results if 'error' not in r])}/{len(tasks)} tasks succeeded")
        logger.info("=" * 60)

        return {
            "success": True,
            "tasks_completed": len([r for r in results if "error" not in r]),
            "tasks_failed": len([r for r in results if "error" in r]),
            "results": results
        }
    except Exception as e:
        logger.error(f"Article processing job failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


@track_job_execution(job_id="process_unprocessed", job_name="Process Unprocessed Articles")
def process_unprocessed_articles_job(session: Session = None):
    """
    Job 5: Search for and process any articles that missed the main pipeline.

    This backup job runs every 10 hours to catch articles that may have been:
    - Extracted but not analyzed
    - Analyzed but not processed (frameworks/stats/clustering/context)

    It ensures no articles get stuck in partial processing states.

    Args:
        session: Optional session (for testing). If None, creates new session.
    """
    try:
        logger.info("=" * 60)
        logger.info("Starting unprocessed articles scan job")
        logger.info("=" * 60)

        from ..services.ai_analyzer import get_unanalyzed_article_count
        from sqlmodel import select
        from ..models import Article, ArticleAnalysis, ArticleFrameworkLink

        stats = {
            "unanalyzed_found": 0,
            "analyzed_unprocessed_found": 0,
            "actions_taken": []
        }

        with Session(engine) as job_session:
            # Step 1: Find extracted but unanalyzed articles
            unanalyzed_count = get_unanalyzed_article_count(job_session)
            stats["unanalyzed_found"] = unanalyzed_count

            if unanalyzed_count > 0:
                logger.info(f"Found {unanalyzed_count} extracted but unanalyzed articles")
                logger.info("Triggering analysis job...")
                stats["actions_taken"].append(f"analyze_{unanalyzed_count}_articles")
                # Run analysis with chaining to process
                try:
                    analyze_job(session=None, chain_processing=True)
                except Exception as e:
                    logger.error(f"Triggered analysis job failed: {e}", exc_info=True)
                    # Don't fail the unprocessed scan if triggered job fails
            else:
                logger.info("All extracted articles have been analyzed ✓")

                # Step 2: Find analyzed but unprocessed articles (missing frameworks)
                analyzed_unprocessed = job_session.exec(
                    select(Article)
                    .join(ArticleAnalysis)
                    .where(~Article.id.in_(
                        select(ArticleFrameworkLink.article_id)
                    ))
                ).all()

                stats["analyzed_unprocessed_found"] = len(analyzed_unprocessed)

                if analyzed_unprocessed:
                    logger.info(f"Found {len(analyzed_unprocessed)} analyzed but unprocessed articles")
                    logger.info("Triggering processing job...")
                    stats["actions_taken"].append(f"process_{len(analyzed_unprocessed)}_articles")
                    try:
                        process_articles_job(session=None)
                    except Exception as e:
                        logger.error(f"Triggered processing job failed: {e}", exc_info=True)
                        # Don't fail the unprocessed scan if triggered job fails
                else:
                    logger.info("All analyzed articles have been processed ✓")

        logger.info("=" * 60)
        logger.info(f"Unprocessed articles scan completed")
        logger.info(f"Actions taken: {', '.join(stats['actions_taken']) if stats['actions_taken'] else 'None - all caught up!'}")
        logger.info("=" * 60)

        return {
            "success": True,
            "unanalyzed_found": stats["unanalyzed_found"],
            "analyzed_unprocessed_found": stats["analyzed_unprocessed_found"],
            "actions_taken": stats["actions_taken"]
        }
    except Exception as e:
        logger.error(f"Unprocessed articles scan job failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


@track_job_execution(job_id="regenerate_viewpoints", job_name="Regenerate Opposing Viewpoints")
def regenerate_viewpoints_job(session: Session = None):
    """
    Job 9: Batch regenerate opposing viewpoints for articles.
    Scheduled to run daily to refresh viewpoint relationships.

    This job:
    - Finds articles with expired or missing viewpoint relationships
    - Regenerates framework oppositions using the ViewpointAnalyzer
    - Updates cached relationships with fresh AI analysis
    - Manages API costs by processing in batches with delays

    Args:
        session: Optional session (for testing). If None, creates new session.
    """
    try:
        logger.info("=" * 60)
        logger.info("Starting opposing viewpoints regeneration job")
        logger.info("=" * 60)

        from ..services.viewpoint_analyzer import ViewpointAnalyzer
        from sqlmodel import select
        from ..models import Article, ArticleAnalysis, ViewpointRelationship

        stats = {
            "articles_processed": 0,
            "relationships_created": 0,
            "relationships_updated": 0,
            "errors": 0,
            "processing_time_ms": 0
        }

        if session is None:
            with Session(engine) as job_session:
                start_time = datetime.utcnow()

                # Find articles that need viewpoint regeneration
                articles_to_process = job_session.exec(
                    select(Article)
                    .join(ArticleAnalysis)
                    .where(
                        or_(
                            # Articles with no viewpoint relationships
                            ~Article.id.in_(
                                select(ViewpointRelationship.primary_article_id)
                                .where(ViewpointRelationship.is_active == True)
                            ),
                            # Articles with expired relationships
                            Article.id.in_(
                                select(ViewpointRelationship.primary_article_id)
                                .where(ViewpointRelationship.expires_at < datetime.utcnow())
                                .where(ViewpointRelationship.is_active == True)
                            )
                        )
                    )
                    .order_by(func.random())  # Random order for variety
                    .limit(100)  # Process up to 100 articles per day
                ).all()

                stats["total_articles_found"] = len(articles_to_process)
                logger.info(f"Found {len(articles_to_process)} articles needing viewpoint regeneration")

                for article in articles_to_process:
                    try:
                        article_start = datetime.utcnow()

                        # Regenerate viewpoints for this article
                        viewpoints = ViewpointAnalyzer.find_opposing_viewpoints(
                            article_id=article.id,
                            session=job_session,
                            max_results=5,
                            relationship_types=["framework_opposition"]
                        )

                        article_time = (datetime.utcnow() - article_start).total_seconds() * 1000
                        stats["processing_time_ms"] += article_time

                        if viewpoints:
                            stats["relationships_created"] += len(viewpoints)
                            logger.debug(f"Generated {len(viewpoints)} viewpoints for article {article.id}")
                        else:
                            logger.debug(f"No viewpoints found for article {article.id}")

                        stats["articles_processed"] += 1

                        # Rate limiting: brief delay between articles to manage API costs
                        time.sleep(0.5)

                    except Exception as e:
                        logger.error(f"Error processing article {article.id}: {e}")
                        stats["errors"] += 1
                        continue

                total_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                stats["total_processing_time_ms"] = total_time

        else:
            # For testing with provided session
            start_time = datetime.utcnow()

            articles_to_process = session.exec(
                select(Article)
                .join(ArticleAnalysis)
                .where(
                    or_(
                        ~Article.id.in_(
                            select(ViewpointRelationship.primary_article_id)
                            .where(ViewpointRelationship.is_active == True)
                        ),
                        Article.id.in_(
                            select(ViewpointRelationship.primary_article_id)
                            .where(ViewpointRelationship.expires_at < datetime.utcnow())
                            .where(ViewpointRelationship.is_active == True)
                        )
                    )
                )
                .limit(10)  # Smaller limit for testing
            ).all()

            for article in articles_to_process:
                try:
                    viewpoints = ViewpointAnalyzer.find_opposing_viewpoints(
                        article_id=article.id,
                        session=session,
                        max_results=5,
                        relationship_types=["framework_opposition"]
                    )

                    if viewpoints:
                        stats["relationships_created"] += len(viewpoints)

                    stats["articles_processed"] += 1
                    time.sleep(0.5)  # Rate limiting

                except Exception as e:
                    logger.error(f"Error processing article {article.id}: {e}")
                    stats["errors"] += 1
                    continue

            total_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            stats["total_processing_time_ms"] = total_time

        logger.info("=" * 60)
        logger.info(
            f"Viewpoint regeneration job completed: "
            f"{stats['articles_processed']} articles processed, "
            f"{stats['relationships_created']} relationships created, "
            f"{stats['errors']} errors"
        )
        logger.info(
            f"Processing time: {stats.get('total_processing_time_ms', 0):.0f}ms total, "
            f"{stats.get('processing_time_ms', 0) / max(stats['articles_processed'], 1):.0f}ms avg per article"
        )
        logger.info("=" * 60)

        return {
            "success": True,
            "articles_processed": stats["articles_processed"],
            "relationships_created": stats["relationships_created"],
            "errors": stats["errors"],
            "processing_time_ms": stats.get("total_processing_time_ms", 0)
        }

    except Exception as e:
        logger.error(f"Viewpoint regeneration job failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}
