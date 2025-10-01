"""
RSS feed scraper that fetches article metadata from news sources.
Stores: title, url, author, published_at, source_id
"""

import feedparser
from sqlmodel import Session, select
from app.models import Source, Article, ProcessingStatus
from app.database import engine
from datetime import datetime
from typing import List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def scrape_source(source: Source, session: Session) -> List[Article]:
    """
    Scrape a single source's RSS feed and create article records.

    Args:
        source: Source model instance with RSS feed URL
        session: Database session

    Returns:
        List of newly created Article instances
    """
    new_articles = []

    try:
        logger.info(f"Scraping {source.name} from {source.rss_feed_url}")

        # Parse RSS feed
        feed = feedparser.parse(source.rss_feed_url)

        if feed.bozo:  # feedparser sets this flag if there was an error
            logger.warning(f"Error parsing feed for {source.name}: {feed.bozo_exception}")
            return new_articles

        if not feed.entries:
            logger.warning(f"No entries found in feed for {source.name}")
            return new_articles

        logger.info(f"Found {len(feed.entries)} entries in {source.name}")

        # Process each entry
        for entry in feed.entries:
            # Extract URL (required)
            url = entry.get('link') or entry.get('id')
            if not url:
                logger.warning(f"Skipping entry without URL in {source.name}")
                continue

            # Check if article already exists
            existing = session.exec(
                select(Article).where(Article.url == url)
            ).first()

            if existing:
                logger.debug(f"Article already exists: {url}")
                continue

            # Extract title (required)
            title = entry.get('title', 'No title')

            # Extract author (optional)
            author = None
            if hasattr(entry, 'author'):
                author = entry.author
            elif hasattr(entry, 'authors') and entry.authors:
                author = entry.authors[0].get('name')

            # Extract published date
            published_at = datetime.utcnow()  # Default to now
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                try:
                    published_at = datetime(*entry.published_parsed[:6])
                except Exception as e:
                    logger.warning(f"Error parsing date for {url}: {e}")

            # Create article record
            article = Article(
                source_id=source.id,
                title=title[:500],  # Truncate to max length
                url=url[:1000],  # Truncate to max length
                author=author[:200] if author else None,
                published_at=published_at,
                scraped_at=datetime.utcnow(),
                processing_status=ProcessingStatus.PENDING,
                topic_category=None,  # Will be inferred later
            )

            session.add(article)
            new_articles.append(article)
            logger.info(f"Added new article: {title[:50]}...")

        # Commit all new articles for this source
        if new_articles:
            session.commit()
            logger.info(f"Successfully scraped {len(new_articles)} new articles from {source.name}")
        else:
            logger.info(f"No new articles found for {source.name}")

    except Exception as e:
        logger.error(f"Error scraping {source.name}: {e}")
        session.rollback()

    return new_articles


def scrape_all_active_sources() -> int:
    """
    Scrape all active sources and return the total count of new articles.

    Returns:
        Total number of new articles scraped
    """
    total_count = 0

    with Session(engine) as session:
        # Get all active sources
        active_sources = session.exec(
            select(Source).where(Source.is_active == True)
        ).all()

        logger.info(f"Starting scrape of {len(active_sources)} active sources")

        for source in active_sources:
            new_articles = scrape_source(source, session)
            total_count += len(new_articles)

        logger.info(f"Scraping complete. Total new articles: {total_count}")

    return total_count


if __name__ == "__main__":
    # Test the scraper
    count = scrape_all_active_sources()
    print(f"Scraped {count} new articles")
