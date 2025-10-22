#!/usr/bin/env python3
"""
Source Diversity Backfill Script

This script helps balance article distribution across sources by fetching
additional articles from underrepresented sources. It's designed to be run
both in development and production environments.

Usage:
    python scripts/backfill_sources.py [--source SOURCE_NAME] [--count NUM] [--dry-run]

Examples:
    # Backfill all sources (except BBC) to 200 articles each
    python scripts/backfill_sources.py

    # Backfill specific source
    python scripts/backfill_sources.py --source "NPR" --count 200

    # Dry run to see what would be fetched
    python scripts/backfill_sources.py --dry-run
"""

import argparse
import asyncio
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path to import from backend
sys.path.append(str(Path(__file__).parent.parent))

from backend.app.database import get_session, engine
from backend.app.models import Source, Article
from backend.app.services.rss_scraper import scrape_source_articles
from sqlmodel import Session, select, func

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_source_statistics(session: Session) -> dict:
    """Get current article count per source."""
    stats = session.exec(
        select(Source.name, func.count(Article.id).label('article_count'))
        .join(Article, Source.id == Article.source_id, isouter=True)
        .group_by(Source.name)
        .order_by(func.count(Article.id).desc())
    ).all()

    return {name: count for name, count in stats}

def get_underrepresented_sources(session: Session, target_count: int = 200, exclude_sources: list = None) -> list:
    """Get sources that need more articles."""
    if exclude_sources is None:
        exclude_sources = ['BBC News', 'www.bbc.com']  # Exclude BBC variants

    stats = get_source_statistics(session)
    underrepresented = []

    for source_name, current_count in stats.items():
        if source_name not in exclude_sources and current_count < target_count:
            needed = target_count - current_count
            underrepresented.append({
                'name': source_name,
                'current_count': current_count,
                'needed': needed
            })

    return sorted(underrepresented, key=lambda x: x['needed'], reverse=True)

def backfill_source_articles(session: Session, source_name: str, target_count: int, dry_run: bool = False) -> dict:
    """Backfill articles for a specific source."""
    logger.info(f"{'[DRY RUN] ' if dry_run else ''}Processing source: {source_name}")

    # Get source
    source = session.exec(select(Source).where(Source.name == source_name)).first()
    if not source:
        logger.error(f"Source not found: {source_name}")
        return {'success': False, 'error': f'Source not found: {source_name}'}

    # Count current articles
    current_count = len(session.exec(select(Article).where(Article.source_id == source.id)).all())
    needed = max(0, target_count - current_count)

    if needed == 0:
        logger.info(f"Source {source_name} already has {current_count} articles (target: {target_count})")
        return {'success': True, 'current_count': current_count, 'added': 0}

    logger.info(f"Source {source_name} has {current_count} articles, needs {needed} more (target: {target_count})")

    if dry_run:
        logger.info(f"[DRY RUN] Would fetch {needed} articles from {source_name}")
        return {'success': True, 'current_count': current_count, 'would_add': needed}

    try:
        # Scrape articles from this source
        logger.info(f"Fetching articles from {source.rss_feed_url}")
        added_count = 0

        # Scrape in batches to avoid overwhelming the source
        batch_size = 50
        remaining = needed

        while remaining > 0:
            batch_needed = min(batch_size, remaining)
            logger.info(f"Fetching batch of {batch_needed} articles from {source_name}")

            # This would need to be adapted based on your RSS scraper implementation
            # For now, using a placeholder approach
            articles = scrape_source_articles(source, session, limit=batch_needed)

            if articles:
                added_count += len(articles)
                remaining -= len(articles)
                logger.info(f"Added {len(articles)} articles to {source_name} (total: {added_count})")
            else:
                logger.warning(f"No more articles found for {source_name}")
                break

        final_count = current_count + added_count
        logger.info(f"Completed backfill for {source_name}: {current_count} -> {final_count} articles (+{added_count})")

        return {
            'success': True,
            'current_count': current_count,
            'added': added_count,
            'final_count': final_count
        }

    except Exception as e:
        logger.error(f"Error backfilling {source_name}: {e}")
        return {'success': False, 'error': str(e), 'current_count': current_count}

async def main():
    parser = argparse.ArgumentParser(description='Backfill articles for source diversity')
    parser.add_argument('--source', help='Specific source to backfill')
    parser.add_argument('--count', type=int, default=200, help='Target article count per source')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without executing')
    parser.add_argument('--exclude', nargs='+', default=['BBC News', 'www.bbc.com'],
                       help='Sources to exclude from backfill')

    args = parser.parse_args()

    logger.info("Starting source diversity backfill")
    logger.info(f"Target count: {args.count} articles per source")
    logger.info(f"Excluding sources: {args.exclude}")
    if args.dry_run:
        logger.info("DRY RUN MODE - No changes will be made")

    # Get database session
    with Session(engine) as session:
        if args.source:
            # Backfill specific source
            logger.info(f"Backfilling specific source: {args.source}")
            result = backfill_source_articles(session, args.source, args.count, args.dry_run)
            logger.info(f"Result: {result}")

        else:
            # Backfill all underrepresented sources
            underrepresented = get_underrepresented_sources(session, args.count, args.exclude)

            if not underrepresented:
                logger.info("All sources meet target count!")
                return

            logger.info(f"Found {len(underrepresented)} sources needing backfill:")
            for source_info in underrepresented:
                logger.info(f"  - {source_info['name']}: {source_info['current_count']} -> {args.count} (need {source_info['needed']})")

            # Process each source
            total_added = 0
            successful_sources = 0

            for source_info in underrepresented:
                source_name = source_info['name']
                logger.info(f"\n{'='*60}")
                logger.info(f"Processing: {source_name}")
                logger.info(f"{'='*60}")

                result = backfill_source_articles(session, source_name, args.count, args.dry_run)

                if result['success']:
                    successful_sources += 1
                    if not args.dry_run:
                        total_added += result.get('added', 0)
                        session.commit()  # Commit changes for this source
                else:
                    logger.error(f"Failed to backfill {source_name}: {result.get('error')}")

            # Summary
            logger.info(f"\n{'='*60}")
            logger.info("BACKFILL SUMMARY")
            logger.info(f"{'='*60}")
            logger.info(f"Sources processed: {len(underrepresented)}")
            logger.info(f"Successful sources: {successful_sources}")

            if args.dry_run:
                total_would_add = sum(s['needed'] for s in underrepresented)
                logger.info(f"Would add approximately {total_would_add} articles total")
            else:
                logger.info(f"Total articles added: {total_added}")

                # Show updated statistics
                updated_stats = get_source_statistics(session)
                logger.info("\nUpdated source distribution:")
                for source_name, count in sorted(updated_stats.items(), key=lambda x: x[1], reverse=True):
                    status = "✓" if count >= args.count else "✗" if source_name not in args.exclude else "−"
                    logger.info(f"  {status} {source_name}: {count} articles")

if __name__ == "__main__":
    asyncio.run(main())