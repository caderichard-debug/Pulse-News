#!/usr/bin/env python3
"""
Backfill script to re-analyze existing articles and populate topic classifications.

This script deletes existing ArticleAnalysis records in batches and triggers
re-analysis to populate both Article.topic_category and ArticleTopicLink.

Usage:
    python backend/scripts/backfill_article_topics.py [--batch-size 50] [--max-articles 0] [--dry-run]

Options:
    --batch-size: Number of articles to analyze per batch (default: 50)
    --max-articles: Maximum total articles to process (0 = all, default: 0)
    --dry-run: Show what would be done without making changes
"""

import sys
import os
import time
import argparse
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.database import get_session
from app.models import Article, ArticleAnalysis
from app.services.ai_analyzer import analyze_articles_batch
from sqlmodel import select, func
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def backfill_topics(batch_size: int = 50, max_articles: int = 0, dry_run: bool = False):
    """
    Backfill topic classifications for existing analyzed articles.

    Args:
        batch_size: Number of articles to process in each batch
        max_articles: Maximum articles to process (0 = all)
        dry_run: If True, show what would be done without making changes
    """
    logger.info("=" * 80)
    logger.info("ARTICLE TOPIC BACKFILL SCRIPT")
    logger.info("=" * 80)

    if dry_run:
        logger.warning("DRY RUN MODE - No changes will be made")

    with next(get_session()) as session:
        # Count articles that need backfilling (analyzed but no topic)
        articles_without_topics = session.exec(
            select(func.count(Article.id))
            .join(ArticleAnalysis)
            .where(Article.topic_category.is_(None))
        ).one()

        logger.info(f"Found {articles_without_topics} articles without topics")

        if articles_without_topics == 0:
            logger.info("✓ All articles already have topics assigned!")
            return 0

        # Calculate batches
        total_to_process = articles_without_topics if max_articles == 0 else min(max_articles, articles_without_topics)
        num_batches = (total_to_process + batch_size - 1) // batch_size

        logger.info(f"Will process {total_to_process} articles in {num_batches} batches")
        logger.info(f"Batch size: {batch_size}")

        if dry_run:
            logger.info("Dry run complete - no changes made")
            return 0

        input(f"\nPress ENTER to continue or Ctrl+C to cancel...")

        total_processed = 0
        total_analyzed = 0

        for batch_num in range(num_batches):
            logger.info("")
            logger.info("=" * 80)
            logger.info(f"BATCH {batch_num + 1}/{num_batches}")
            logger.info("=" * 80)

            # Get articles in this batch that need topics
            articles_to_reanalyze = session.exec(
                select(Article, ArticleAnalysis)
                .join(ArticleAnalysis)
                .where(Article.topic_category.is_(None))
                .limit(batch_size)
            ).all()

            if not articles_to_reanalyze:
                logger.info("No more articles to process")
                break

            logger.info(f"Found {len(articles_to_reanalyze)} articles to re-analyze")

            # Delete their analyses to trigger re-analysis
            for article, analysis in articles_to_reanalyze:
                logger.debug(f"Deleting analysis for article {article.id}: {article.title[:60]}")
                session.delete(analysis)

            session.commit()
            logger.info(f"Deleted {len(articles_to_reanalyze)} analyses")

            # Re-analyze in smaller sub-batches (OpenAI API optimal batch size is 5)
            articles_in_batch = len(articles_to_reanalyze)
            sub_batch_size = 5
            analyzed_in_batch = 0

            for sub_batch_start in range(0, articles_in_batch, sub_batch_size):
                logger.info(f"  Sub-batch {sub_batch_start // sub_batch_size + 1}...")

                # Create new session for each analysis to avoid stale data
                with next(get_session()) as analysis_session:
                    count = analyze_articles_batch(analysis_session, batch_size=sub_batch_size)
                    analyzed_in_batch += count

                # Small delay between API calls to avoid rate limits
                if sub_batch_start + sub_batch_size < articles_in_batch:
                    time.sleep(1)

            total_processed += articles_in_batch
            total_analyzed += analyzed_in_batch

            logger.info(f"Batch {batch_num + 1} complete: {analyzed_in_batch}/{articles_in_batch} articles analyzed")
            logger.info(f"Progress: {total_processed}/{total_to_process} ({100*total_processed//total_to_process}%)")

            # Delay between batches
            if batch_num < num_batches - 1:
                logger.info("Pausing 2 seconds before next batch...")
                time.sleep(2)

            # Check if we've hit max_articles
            if max_articles > 0 and total_processed >= max_articles:
                logger.info(f"Reached max_articles limit ({max_articles})")
                break

    logger.info("")
    logger.info("=" * 80)
    logger.info("BACKFILL COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Total articles processed: {total_processed}")
    logger.info(f"Successfully analyzed: {total_analyzed}")
    logger.info(f"Failed: {total_processed - total_analyzed}")

    return total_analyzed


def main():
    parser = argparse.ArgumentParser(
        description="Backfill topic classifications for existing articles"
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=50,
        help='Number of articles to process per batch (default: 50)'
    )
    parser.add_argument(
        '--max-articles',
        type=int,
        default=0,
        help='Maximum total articles to process (0 = all, default: 0)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )

    args = parser.parse_args()

    try:
        result = backfill_topics(
            batch_size=args.batch_size,
            max_articles=args.max_articles,
            dry_run=args.dry_run
        )
        sys.exit(0 if result >= 0 else 1)
    except KeyboardInterrupt:
        logger.warning("\n\nBackfill cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during backfill: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
