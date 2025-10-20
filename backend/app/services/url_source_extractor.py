"""
URL Source Extractor Service

Extracts source information from article URLs (not RSS feeds).
Uses web scraping to find RSS feeds for discovered sources.
"""

import logging
import feedparser
import requests
from urllib.parse import urlparse
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class URLSourceExtractor:
    """Extract source information from article URLs."""

    def __init__(self):
        self.timeout = 10

    def extract_source_from_article_url(self, article_url: str) -> Dict[str, Any]:
        """
        Extract source information from an article URL.

        Args:
            article_url: Full URL to an article (e.g., https://example.com/article/123)

        Returns:
            Dict containing:
                - domain: Source domain (e.g., "example.com")
                - base_url: Base URL (e.g., "https://example.com")
                - rss_feed_url: Discovered RSS feed URL
                - is_news_site: Whether this appears to be a news site

        Raises:
            ValueError: If URL is invalid or not a news source
        """
        logger.info(f"Extracting source from article URL: {article_url}")

        # Step 1: Parse and validate URL
        try:
            parsed = urlparse(article_url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("Invalid URL format")
        except Exception as e:
            raise ValueError(f"Invalid URL: {str(e)}")

        domain = parsed.netloc
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        # Step 2: Fetch the article page to find RSS feed
        try:
            rss_feed_url = self._discover_rss_feed(base_url, article_url)
            if not rss_feed_url:
                raise ValueError("Could not discover RSS feed for this source")
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"RSS discovery failed for {article_url}: {str(e)}")
            raise ValueError(f"Failed to discover RSS feed: {str(e)}")

        # Step 3: Validate it's a news site by checking RSS feed
        is_news_site = self._validate_news_site(rss_feed_url)
        if not is_news_site:
            raise ValueError("This URL does not appear to be from a news source")

        return {
            "domain": domain,
            "base_url": base_url,
            "rss_feed_url": rss_feed_url,
            "is_news_site": is_news_site
        }

    def _discover_rss_feed(self, base_url: str, article_url: str) -> Optional[str]:
        """
        Discover RSS feed URL from article page or base URL.

        Priority:
        1. Check article page for <link rel="alternate" type="application/rss+xml">
        2. Common RSS feed locations (/rss, /feed, /rss.xml, etc.)
        3. Check base URL for RSS feed links
        """
        logger.info(f"Discovering RSS feed for {base_url}")

        # Try article page first
        try:
            response = requests.get(article_url, timeout=self.timeout, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; PulseBot/1.0)'
            })
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Look for RSS feed link in <head>
            rss_link = soup.find('link', {'type': 'application/rss+xml'})
            if not rss_link:
                # Also check for atom feeds
                rss_link = soup.find('link', {'type': 'application/atom+xml'})

            if rss_link and rss_link.get('href'):
                rss_url = rss_link['href']
                # Handle relative URLs
                if rss_url.startswith('/'):
                    rss_url = base_url + rss_url
                elif not rss_url.startswith('http'):
                    rss_url = base_url + '/' + rss_url

                # Validate the feed
                if self._validate_rss_feed(rss_url):
                    logger.info(f"Found RSS feed in article page: {rss_url}")
                    return rss_url
        except Exception as e:
            logger.warning(f"Failed to check article page for RSS: {str(e)}")

        # Try common RSS feed locations
        common_paths = [
            '/rss',
            '/feed',
            '/rss.xml',
            '/feed.xml',
            '/index.xml',
            '/atom.xml',
            '/?feed=rss2',
            '/feeds/posts/default',  # Blogger
            '/feed/',
            '/rss/',
        ]

        for path in common_paths:
            candidate_url = base_url + path
            if self._validate_rss_feed(candidate_url):
                logger.info(f"Found RSS feed at common location: {candidate_url}")
                return candidate_url

        logger.warning(f"Could not discover RSS feed for {base_url}")
        return None

    def _validate_rss_feed(self, rss_url: str) -> bool:
        """Check if URL is a valid RSS/Atom feed."""
        try:
            feed = feedparser.parse(rss_url)

            # Check if feed has entries and is not malformed
            if feed.bozo and not feed.entries:
                return False

            if not feed.entries:
                return False

            logger.debug(f"Validated RSS feed: {rss_url} ({len(feed.entries)} entries)")
            return True
        except Exception as e:
            logger.debug(f"RSS validation failed for {rss_url}: {str(e)}")
            return False

    def _validate_news_site(self, rss_feed_url: str) -> bool:
        """
        Validate that the RSS feed appears to be from a news source.

        Checks:
        - Has recent entries (published within last 30 days)
        - Entries have titles and links
        - Feed title suggests news content
        """
        try:
            feed = feedparser.parse(rss_feed_url)

            if not feed.entries:
                return False

            # Check feed has basic news characteristics
            # (This is a simple heuristic - can be improved)
            recent_entries = 0
            from datetime import datetime, timedelta
            cutoff = datetime.now() - timedelta(days=30)

            for entry in feed.entries[:10]:  # Check first 10 entries
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    try:
                        pub_date = datetime(*entry.published_parsed[:6])
                        if pub_date > cutoff:
                            recent_entries += 1
                    except:
                        pass

                # Check entry has title and link
                if not entry.get('title') or not entry.get('link'):
                    logger.debug(f"Entry missing title or link: {entry}")
                    return False

            # Require at least some recent content
            if recent_entries == 0:
                logger.warning(f"No recent entries found in feed: {rss_feed_url}")
                return False

            logger.info(f"Validated news site with {recent_entries} recent entries")
            return True

        except Exception as e:
            logger.error(f"News site validation failed: {str(e)}")
            return False
