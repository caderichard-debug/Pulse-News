"""
Article content extraction service.
Uses trafilatura as primary method, readability-lxml as fallback.
"""

import trafilatura
from readability import Document
from bs4 import BeautifulSoup
import requests
from sqlmodel import Session, select
from ..models import Article, ProcessingStatus
from ..database import engine
from typing import Optional, Dict
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_article_content(url: str, timeout: int = 10) -> Dict[str, any]:
    """
    Extract full article text from URL using cascade of methods.

    Args:
        url: Article URL to extract
        timeout: Request timeout in seconds

    Returns:
        Dict with keys: content (str), method (str), word_count (int), success (bool)
    """
    result = {
        'content': None,
        'title': None,
        'author': None,
        'published_date': None,
        'method': None,
        'word_count': 0,
        'success': False
    }

    try:
        # Fetch the page
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, timeout=timeout, headers=headers)
        response.raise_for_status()
        html = response.text

        # Method 1: trafilatura (best for news articles)
        content = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=False,
            output_format='txt'
        )

        # Extract metadata using trafilatura
        metadata = trafilatura.extract_metadata(html)

        if content and len(content) > 200:  # Minimum reasonable article length
            result['content'] = content
            result['method'] = 'trafilatura'
            result['word_count'] = len(content.split())
            result['success'] = True

            # Add metadata if available
            if metadata:
                result['title'] = metadata.title
                result['author'] = metadata.author
                result['published_date'] = metadata.date

            # Fallback to BeautifulSoup for title if trafilatura didn't get it
            if not result['title']:
                soup = BeautifulSoup(html, 'html.parser')
                title_tag = soup.find('title')
                if title_tag:
                    result['title'] = title_tag.get_text().strip()
                # Try og:title meta tag
                if not result['title']:
                    og_title = soup.find('meta', property='og:title')
                    if og_title and og_title.get('content'):
                        result['title'] = og_title.get('content').strip()

            logger.debug(f"Extracted {result['word_count']} words using trafilatura (title: {result['title']})")
            return result

        # Method 2: readability-lxml (fallback)
        logger.debug("Trafilatura failed, trying readability-lxml")
        doc = Document(html)
        content_html = doc.summary()
        text = BeautifulSoup(content_html, 'html.parser').get_text()

        if text and len(text) > 200:
            result['content'] = text
            result['method'] = 'readability'
            result['word_count'] = len(text.split())
            result['success'] = True

            # Extract title using readability
            result['title'] = doc.title()

            # Fallback to BeautifulSoup for title if readability didn't get it
            if not result['title']:
                soup = BeautifulSoup(html, 'html.parser')
                title_tag = soup.find('title')
                if title_tag:
                    result['title'] = title_tag.get_text().strip()
                # Try og:title meta tag
                if not result['title']:
                    og_title = soup.find('meta', property='og:title')
                    if og_title and og_title.get('content'):
                        result['title'] = og_title.get('content').strip()

            logger.debug(f"Extracted {result['word_count']} words using readability (title: {result['title']})")
            return result

        logger.warning(f"Both extraction methods failed for {url}")

    except requests.Timeout:
        logger.error(f"Timeout fetching {url}")
    except requests.RequestException as e:
        logger.error(f"Request error for {url}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error extracting {url}: {e}")

    return result


def process_pending_articles(session: Session, batch_size: int = 20, delay: float = 1.0) -> int:
    """
    Process articles with status=PENDING, extracting their full content.

    Args:
        session: Database session (injected for testing)
        batch_size: Maximum number of articles to process
        delay: Delay between requests in seconds (rate limiting)

    Returns:
        Number of articles successfully processed
    """
    processed_count = 0

    # Get pending articles
    pending_articles = session.exec(
        select(Article)
        .where(Article.processing_status == ProcessingStatus.PENDING)
        .limit(batch_size)
    ).all()

    if not pending_articles:
        logger.info("No pending articles to process")
        return 0

    logger.info(f"Processing {len(pending_articles)} pending articles")

    for i, article in enumerate(pending_articles, 1):
        logger.info(f"[{i}/{len(pending_articles)}] Extracting: {article.title[:50]}...")

        # Extract content
        extraction_result = extract_article_content(article.url)

        if extraction_result['success']:
            # Update article with extracted content
            article.content_text = extraction_result['content']
            article.word_count = extraction_result['word_count']
            article.extraction_method = extraction_result['method']
            article.processing_status = ProcessingStatus.COMPLETED

            session.add(article)
            processed_count += 1
            logger.info(f"  ✓ Extracted {extraction_result['word_count']} words via {extraction_result['method']}")
        else:
            # Mark as failed
            article.processing_status = ProcessingStatus.FAILED
            article.extraction_method = 'failed'
            session.add(article)
            logger.warning(f"  ✗ Extraction failed")

        # Commit after each article to avoid losing progress
        session.commit()

        # Rate limiting
        if i < len(pending_articles):
            time.sleep(delay)

    logger.info(f"Processing complete. Successfully extracted: {processed_count}/{len(pending_articles)}")

    return processed_count


if __name__ == "__main__":
    # Test the extractor
    with Session(engine) as session:
        count = process_pending_articles(session, batch_size=10, delay=1.0)
        print(f"Processed {count} articles")
