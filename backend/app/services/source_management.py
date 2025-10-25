"""
Source management utilities for RSS feed discovery and deduplication.
Handles automatic RSS URL discovery, source consolidation, and validation.
"""

import requests
import feedparser
from urllib.parse import urlparse, urljoin
from sqlmodel import Session, select
from ..models import Source, Article
from ..database import engine
from typing import Optional, List, Tuple, Dict
import logging
import re
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class RSSDiscoveryService:
    """Service for discovering RSS feeds and managing source deduplication."""

    def __init__(self):
        self.common_rss_paths = [
            '/rss',
            '/feed',
            '/rss.xml',
            '/feed.xml',
            '/rss/feed',
            '/feeds/rss',
            '/feeds/news',
            '/news/rss',
            '/rss/news',
            '/feed/rss',
            '/feeds',
            '/atom.xml',
            '/rss2.xml',
            '/index.rdf',
            '/rss/latest',
            '/rss/topstories'
        ]

        self.news_source_patterns = {
            # Major news domains and their likely RSS patterns
            'bbc.com': ['http://feeds.bbci.co.uk/news/rss.xml'],
            'cnn.com': ['http://rss.cnn.com/rss/edition.rss', 'http://rss.cnn.com/rss/cnn_topstories.rss'],
            'foxnews.com': ['https://www.foxnews.com/rss', 'https://www.foxnews.com/about/rss/feeds.xml'],
            'reuters.com': ['https://www.reuters.com/rssFeed/worldNews', 'https://www.reuters.com/rssFeed/topNews'],
            'nytimes.com': ['https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml'],
            'washingtonpost.com': ['http://feeds.washingtonpost.com/rss/world'],
            'theguardian.com': ['https://www.theguardian.com/rss', 'https://www.theguardian.com/world/rss'],
            'npr.org': ['https://feeds.npr.org/1001/rss.xml', 'https://feeds.npr.org/1002/rss.xml'],
            'wsj.com': ['https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml'],
            'apnews.com': ['https://news.google.com/rss/search?q=Associated+Press&hl=en-US&gl=US&ceid=US:en'],
            'politico.com': ['https://news.google.com/rss/search?q=Politico&hl=en-US&gl=US&ceid=US:en'],
            'arstechnica.com': ['http://feeds.arstechnica.com/arstechnica/index'],
            'theatlantic.com': ['https://www.theatlantic.com/feed/all/'],
        }

    def normalize_domain(self, url: str) -> str:
        """Extract and normalize domain from URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www. prefix for comparison
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except Exception:
            return ""

    def find_duplicate_sources(self, session: Session) -> List[Tuple[List[Source], str]]:
        """Find potential duplicate sources based on domain similarity."""
        sources = session.exec(select(Source)).all()

        # Group sources by normalized domain
        domain_groups: Dict[str, List[Source]] = {}
        for source in sources:
            domain = self.normalize_domain(source.url)
            if domain:
                if domain not in domain_groups:
                    domain_groups[domain] = []
                domain_groups[domain].append(source)

        # Find groups with duplicates
        duplicates = []
        for domain, source_list in domain_groups.items():
            if len(source_list) > 1:
                duplicates.append((source_list, domain))

        return duplicates

    def similarity_score(self, str1: str, str2: str) -> float:
        """Calculate similarity score between two strings."""
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

    def consolidate_duplicate_sources(self, session: Session, source_group: List[Source], domain: str) -> Source:
        """Consolidate duplicate sources into a single source."""
        if len(source_group) == 1:
            return source_group[0]

        # Choose the best source based on criteria
        best_source = None
        best_score = 0

        for source in source_group:
            score = 0

            # Prefer sources with working RSS feeds
            if source.rss_feed_url:
                try:
                    response = requests.head(source.rss_feed_url, timeout=5)
                    if response.status_code == 200:
                        score += 10
                except:
                    pass

            # Prefer shorter, cleaner names
            if len(source.name) < 20:
                score += 5

            # Prefer official-looking names
            if any(keyword in source.name.lower() for keyword in ['official', 'news', 'latest']):
                score += 3

            # Prefer main domain over subdomains
            if 'www.' in source.url or not any(sub in source.url for sub in ['.', 'news', 'www']):
                score += 2

            if score > best_score:
                best_score = score
                best_source = source

        # If no clear winner, choose the first one
        if not best_source:
            best_source = source_group[0]

        logger.info(f"Selected {best_source.name} as primary source for domain {domain}")

        # Migrate articles from other sources to the best one
        for source in source_group:
            if source.id != best_source.id:
                # Update articles to point to the best source
                from sqlmodel import text
                session.exec(
                    text(f"UPDATE articles SET source_id = {best_source.id} WHERE source_id = {source.id}")
                )
                logger.info(f"Migrated articles from {source.name} to {best_source.name}")

                # Delete the duplicate source
                session.delete(source)
                logger.info(f"Deleted duplicate source: {source.name}")

        return best_source

    def discover_rss_feeds(self, url: str) -> List[str]:
        """Discover RSS feeds for a given website URL."""
        feeds = []

        try:
            # First try common RSS paths
            parsed_url = urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

            # Check known patterns for this domain
            domain = self.normalize_domain(url)
            if domain in self.news_source_patterns:
                feeds.extend(self.news_source_patterns[domain])

            # Try common RSS paths
            for path in self.common_rss_paths:
                rss_url = urljoin(base_url, path)
                if self.validate_rss_feed(rss_url):
                    feeds.append(rss_url)

            # Try to find RSS links in the HTML
            try:
                response = requests.get(url, timeout=10, headers={
                    'User-Agent': 'Mozilla/5.0 (compatible; RSS-Detector/1.0)'
                })

                if response.status_code == 200:
                    # Look for RSS/Atom links in HTML
                    rss_patterns = [
                        r'<link[^>]+type=["\']application/rss\+xml["\'][^>]+href=["\']([^"\']+)["\']',
                        r'<link[^>]+type=["\']application/atom\+xml["\'][^>]+href=["\']([^"\']+)["\']',
                        r'<a[^>]+href=["\']([^"\']*\.xml)["\'][^>]*rss',
                        r'<a[^>]+href=["\']([^"\']*\.xml)["\'][^>]*feed'
                    ]

                    for pattern in rss_patterns:
                        matches = re.findall(pattern, response.text, re.IGNORECASE)
                        for match in matches:
                            rss_url = urljoin(base_url, match)
                            if self.validate_rss_feed(rss_url) and rss_url not in feeds:
                                feeds.append(rss_url)

            except Exception as e:
                logger.warning(f"Failed to parse HTML for {url}: {e}")

            # Fallback to Google News RSS if no feeds found
            if not feeds:
                # Extract site name from URL for Google News search
                site_name = self.extract_site_name(url)
                if site_name:
                    google_news_url = f"https://news.google.com/rss/search?q={site_name}+news&hl=en-US&gl=US&ceid=US:en"
                    if self.validate_rss_feed(google_news_url):
                        feeds.append(google_news_url)

        except Exception as e:
            logger.error(f"Error discovering RSS feeds for {url}: {e}")

        return feeds

    def validate_rss_feed(self, url: str) -> bool:
        """Validate if a URL is a working RSS feed."""
        try:
            response = requests.head(url, timeout=5, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; RSS-Detector/1.0)'
            })

            if response.status_code != 200:
                return False

            content_type = response.headers.get('content-type', '').lower()
            if not any(ct in content_type for ct in ['xml', 'rss', 'atom']):
                # Try to parse anyway, some feeds don't set proper content type
                pass

            # Try to parse the feed
            feed = feedparser.parse(url)
            return not feed.bozo or bool(feed.entries)

        except Exception:
            return False

    def extract_site_name(self, url: str) -> str:
        """Extract site name from URL for Google News search."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Remove www. and common suffixes
            if domain.startswith('www.'):
                domain = domain[4:]

            # Remove TLD
            parts = domain.split('.')
            if len(parts) >= 2:
                return parts[0]

            return domain
        except Exception:
            return ""

    def create_source_with_auto_rss(self, session: Session, name: str, url: str, **kwargs) -> Tuple[Optional[Source], List[str]]:
        """Create a new source with automatic RSS discovery and deduplication."""
        errors = []

        try:
            # Check for duplicates first
            domain = self.normalize_domain(url)
            existing_sources = session.exec(select(Source)).all()

            for existing in existing_sources:
                if self.normalize_domain(existing.url) == domain:
                    errors.append(f"Source with domain {domain} already exists: {existing.name}")
                    return existing, errors

            # Discover RSS feeds
            rss_feeds = self.discover_rss_feeds(url)

            if not rss_feeds:
                errors.append("No RSS feeds found for this URL")
                return None, errors

            # Use the first valid RSS feed
            rss_url = rss_feeds[0]

            # Create the source
            source = Source(
                name=name,
                url=url,
                rss_feed_url=rss_url,
                **kwargs
            )

            session.add(source)
            session.commit()
            session.refresh(source)

            logger.info(f"Created new source: {name} with RSS feed: {rss_url}")
            return source, errors

        except Exception as e:
            errors.append(f"Error creating source: {str(e)}")
            session.rollback()
            return None, errors

    def update_source_rss_if_broken(self, session: Session, source: Source) -> bool:
        """Update RSS URL for a source if the current one is broken."""
        if not source.rss_feed_url:
            return False

        try:
            # Test current RSS feed
            response = requests.head(source.rss_feed_url, timeout=5)
            if response.status_code == 200:
                return True  # Current feed is working

            logger.warning(f"RSS feed for {source.name} is broken: {source.rss_feed_url}")

            # Try to find a new RSS feed
            new_feeds = self.discover_rss_feeds(source.url)

            if new_feeds:
                new_rss_url = new_feeds[0]
                source.rss_feed_url = new_rss_url
                session.commit()
                logger.info(f"Updated RSS feed for {source.name}: {new_rss_url}")
                return True
            else:
                logger.error(f"No working RSS feeds found for {source.name}")
                return False

        except Exception as e:
            logger.error(f"Error updating RSS feed for {source.name}: {e}")
            return False


def consolidate_all_sources(session: Session) -> Dict[str, int]:
    """Consolidate all duplicate sources in the database."""
    discovery_service = RSSDiscoveryService()
    duplicates = discovery_service.find_duplicate_sources(session)

    results = {
        'duplicates_found': len(duplicates),
        'sources_consolidated': 0,
        'sources_deleted': 0
    }

    for source_group, domain in duplicates:
        original_count = len(source_group)
        discovery_service.consolidate_duplicate_sources(session, source_group, domain)

        results['sources_consolidated'] += 1
        results['sources_deleted'] += (original_count - 1)

    session.commit()
    return results


def validate_and_fix_all_sources(session: Session) -> Dict[str, int]:
    """Validate and fix RSS feeds for all sources."""
    discovery_service = RSSDiscoveryService()
    sources = session.exec(select(Source)).all()

    results = {
        'total_sources': len(sources),
        'working_feeds': 0,
        'fixed_feeds': 0,
        'broken_feeds': 0
    }

    for source in sources:
        if discovery_service.update_source_rss_if_broken(session, source):
            results['working_feeds'] += 1
        else:
            results['broken_feeds'] += 1

    session.commit()
    return results