"""
Tests for the RSS scraper service.
Tests feed parsing, article extraction, and duplicate handling.
"""

import pytest
from unittest.mock import MagicMock, patch
from sqlmodel import Session, select
from app.services.rss_scraper import scrape_source, scrape_all_active_sources
from app.models import Source, Article, ProcessingStatus, PoliticalLean
from datetime import datetime
import time


@pytest.fixture
def active_source(session: Session):
    """Create an active news source"""
    source = Source(
        name="Tech News",
        url="https://technews.com",
        rss_feed_url="https://technews.com/feed",
        political_lean=PoliticalLean.CENTER,
        is_active=True
    )
    session.add(source)
    session.commit()
    session.refresh(source)
    return source


@pytest.fixture
def inactive_source(session: Session):
    """Create an inactive news source"""
    source = Source(
        name="Inactive News",
        url="https://inactive.com",
        rss_feed_url="https://inactive.com/feed",
        political_lean=PoliticalLean.CENTER,
        is_active=False
    )
    session.add(source)
    session.commit()
    session.refresh(source)
    return source


@pytest.fixture
def existing_article(session: Session, active_source: Source):
    """Create an existing article in the database"""
    article = Article(
        source_id=active_source.id,
        title="Existing Article",
        url="https://technews.com/existing",
        author="Test Author",
        published_at=datetime.utcnow(),
        scraped_at=datetime.utcnow(),
        processing_status=ProcessingStatus.PENDING
    )
    session.add(article)
    session.commit()
    session.refresh(article)
    return article


@pytest.fixture
def mock_rss_feed():
    """Create a mock RSS feed response"""
    mock_feed = MagicMock()
    mock_feed.bozo = False  # No parsing errors
    mock_feed.entries = [
        {
            'link': 'https://technews.com/article1',
            'title': 'AI Breakthrough in 2025',
            'author': 'John Doe',
            'published_parsed': time.struct_time((2025, 1, 15, 12, 0, 0, 0, 0, 0))
        },
        {
            'link': 'https://technews.com/article2',
            'title': 'New Programming Language Released',
            'author': 'Jane Smith',
            'published_parsed': time.struct_time((2025, 1, 14, 10, 0, 0, 0, 0, 0))
        }
    ]
    return mock_feed


@pytest.fixture
def mock_empty_feed():
    """Create a mock empty RSS feed"""
    mock_feed = MagicMock()
    mock_feed.bozo = False
    mock_feed.entries = []
    return mock_feed


@pytest.fixture
def mock_invalid_feed():
    """Create a mock invalid RSS feed"""
    mock_feed = MagicMock()
    mock_feed.bozo = True
    mock_feed.bozo_exception = Exception("Invalid XML")
    mock_feed.entries = []
    return mock_feed


class TestScrapeSource:
    """Test scraping a single RSS source"""

    @patch('app.services.rss_scraper.feedparser.parse')
    def test_successful_scrape(self, mock_parse, session: Session, active_source: Source, mock_rss_feed):
        """Test successful scraping of new articles"""
        mock_parse.return_value = mock_rss_feed

        articles = scrape_source(active_source, session)

        assert len(articles) == 2
        assert articles[0].title == "AI Breakthrough in 2025"
        assert articles[0].url == "https://technews.com/article1"
        assert articles[0].author == "John Doe"
        assert articles[0].source_id == active_source.id
        assert articles[0].processing_status == ProcessingStatus.PENDING

        # Verify articles were saved to database
        saved_articles = session.exec(
            select(Article).where(Article.source_id == active_source.id)
        ).all()
        assert len(saved_articles) == 2

    @patch('app.services.rss_scraper.feedparser.parse')
    def test_skip_duplicate_articles(
        self, mock_parse, session: Session,
        active_source: Source, existing_article: Article, mock_rss_feed
    ):
        """Test that duplicate articles are skipped"""
        # Modify mock to include existing article URL
        mock_rss_feed.entries[0]['link'] = existing_article.url
        mock_parse.return_value = mock_rss_feed

        articles = scrape_source(active_source, session)

        # Only 1 new article should be created (the second one)
        assert len(articles) == 1
        assert articles[0].url == "https://technews.com/article2"

    @patch('app.services.rss_scraper.feedparser.parse')
    def test_empty_feed(self, mock_parse, session: Session, active_source: Source, mock_empty_feed):
        """Test scraping an empty feed"""
        mock_parse.return_value = mock_empty_feed

        articles = scrape_source(active_source, session)

        assert len(articles) == 0

    @patch('app.services.rss_scraper.feedparser.parse')
    def test_invalid_feed(self, mock_parse, session: Session, active_source: Source, mock_invalid_feed):
        """Test handling of invalid RSS feed"""
        mock_parse.return_value = mock_invalid_feed

        articles = scrape_source(active_source, session)

        assert len(articles) == 0

    @patch('app.services.rss_scraper.feedparser.parse')
    def test_entry_without_url(self, mock_parse, session: Session, active_source: Source):
        """Test handling of entries without URL"""
        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.entries = [
            {
                'title': 'Article Without URL',
                # No 'link' or 'id' field
            }
        ]
        mock_parse.return_value = mock_feed

        articles = scrape_source(active_source, session)

        assert len(articles) == 0

    @patch('app.services.rss_scraper.feedparser.parse')
    def test_entry_with_id_instead_of_link(self, mock_parse, session: Session, active_source: Source):
        """Test using 'id' field when 'link' is not available"""
        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.entries = [
            {
                'id': 'https://technews.com/article-id',
                'title': 'Article with ID',
            }
        ]
        mock_parse.return_value = mock_feed

        articles = scrape_source(active_source, session)

        assert len(articles) == 1
        assert articles[0].url == "https://technews.com/article-id"

    @patch('app.services.rss_scraper.feedparser.parse')
    def test_entry_without_title(self, mock_parse, session: Session, active_source: Source):
        """Test handling of entries without title (should use default)"""
        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.entries = [
            {
                'link': 'https://technews.com/notitle',
                # No 'title' field
            }
        ]
        mock_parse.return_value = mock_feed

        articles = scrape_source(active_source, session)

        assert len(articles) == 1
        assert articles[0].title == "No title"

    @patch('app.services.rss_scraper.feedparser.parse')
    def test_author_extraction_from_author_field(self, mock_parse, session: Session, active_source: Source):
        """Test author extraction from 'author' field"""
        mock_feed = MagicMock()
        mock_feed.bozo = False
        entry = MagicMock()
        entry.get = lambda key, default=None: {
            'link': 'https://technews.com/test',
            'title': 'Test Article'
        }.get(key, default)
        entry.author = "Test Author"
        mock_feed.entries = [entry]
        mock_parse.return_value = mock_feed

        articles = scrape_source(active_source, session)

        assert len(articles) == 1
        assert articles[0].author == "Test Author"

    @patch('app.services.rss_scraper.feedparser.parse')
    def test_author_extraction_from_authors_list(self, mock_parse, session: Session, active_source: Source):
        """Test author extraction from 'authors' array"""
        mock_feed = MagicMock()
        mock_feed.bozo = False
        entry = MagicMock()
        entry.get = lambda key, default=None: {
            'link': 'https://technews.com/test',
            'title': 'Test Article'
        }.get(key, default)
        entry.authors = [{'name': 'First Author'}, {'name': 'Second Author'}]
        delattr(entry, 'author')  # Remove author attribute
        mock_feed.entries = [entry]
        mock_parse.return_value = mock_feed

        articles = scrape_source(active_source, session)

        assert len(articles) == 1
        assert articles[0].author == "First Author"

    @patch('app.services.rss_scraper.feedparser.parse')
    def test_published_date_parsing(self, mock_parse, session: Session, active_source: Source):
        """Test correct parsing of published date"""
        mock_feed = MagicMock()
        mock_feed.bozo = False
        entry = MagicMock()
        entry.get = lambda key, default=None: {
            'link': 'https://technews.com/test',
            'title': 'Test Article'
        }.get(key, default)
        entry.published_parsed = time.struct_time((2025, 10, 1, 14, 30, 0, 0, 0, 0))
        mock_feed.entries = [entry]
        mock_parse.return_value = mock_feed

        articles = scrape_source(active_source, session)

        assert len(articles) == 1
        assert articles[0].published_at.year == 2025
        assert articles[0].published_at.month == 10
        assert articles[0].published_at.day == 1
        assert articles[0].published_at.hour == 14
        assert articles[0].published_at.minute == 30

    @patch('app.services.rss_scraper.feedparser.parse')
    def test_invalid_date_fallback(self, mock_parse, session: Session, active_source: Source):
        """Test fallback to current time for invalid dates"""
        mock_feed = MagicMock()
        mock_feed.bozo = False
        entry = MagicMock()
        entry.get = lambda key, default=None: {
            'link': 'https://technews.com/test',
            'title': 'Test Article'
        }.get(key, default)
        entry.published_parsed = "invalid date"  # Invalid format
        mock_feed.entries = [entry]
        mock_parse.return_value = mock_feed

        before = datetime.utcnow()
        articles = scrape_source(active_source, session)
        after = datetime.utcnow()

        assert len(articles) == 1
        assert before <= articles[0].published_at <= after

    @patch('app.services.rss_scraper.feedparser.parse')
    def test_title_truncation(self, mock_parse, session: Session, active_source: Source):
        """Test that long titles are truncated to 500 chars"""
        long_title = "x" * 1000
        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.entries = [
            {
                'link': 'https://technews.com/long',
                'title': long_title
            }
        ]
        mock_parse.return_value = mock_feed

        articles = scrape_source(active_source, session)

        assert len(articles) == 1
        assert len(articles[0].title) == 500

    @patch('app.services.rss_scraper.feedparser.parse')
    def test_url_truncation(self, mock_parse, session: Session, active_source: Source):
        """Test that long URLs are truncated to 1000 chars"""
        long_url = "https://technews.com/" + "x" * 2000
        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.entries = [
            {
                'link': long_url,
                'title': 'Test'
            }
        ]
        mock_parse.return_value = mock_feed

        articles = scrape_source(active_source, session)

        assert len(articles) == 1
        assert len(articles[0].url) == 1000

    @patch('app.services.rss_scraper.feedparser.parse')
    def test_author_truncation(self, mock_parse, session: Session, active_source: Source):
        """Test that long author names are truncated to 200 chars"""
        long_author = "x" * 500
        mock_feed = MagicMock()
        mock_feed.bozo = False
        entry = MagicMock()
        entry.get = lambda key, default=None: {
            'link': 'https://technews.com/test',
            'title': 'Test'
        }.get(key, default)
        entry.author = long_author
        mock_feed.entries = [entry]
        mock_parse.return_value = mock_feed

        articles = scrape_source(active_source, session)

        assert len(articles) == 1
        assert len(articles[0].author) == 200

    @patch('app.services.rss_scraper.feedparser.parse')
    def test_exception_handling(self, mock_parse, session: Session, active_source: Source):
        """Test that exceptions during scraping are handled gracefully"""
        mock_parse.side_effect = Exception("Network error")

        articles = scrape_source(active_source, session)

        assert len(articles) == 0
        # Database should not have any new articles
        saved_articles = session.exec(
            select(Article).where(Article.source_id == active_source.id)
        ).all()
        assert len(saved_articles) == 0


class TestScrapeAllActiveSources:
    """Test scraping all active sources"""

    @patch('app.services.rss_scraper.feedparser.parse')
    def test_scrape_multiple_sources(
        self, mock_parse, session: Session,
        active_source: Source, mock_rss_feed
    ):
        """Test scraping multiple active sources"""
        # Create second active source
        source2 = Source(
            name="Business News",
            url="https://biznews.com",
            rss_feed_url="https://biznews.com/feed",
            political_lean=PoliticalLean.RIGHT,
            is_active=True
        )
        session.add(source2)
        session.commit()

        mock_parse.return_value = mock_rss_feed

        total_count = scrape_all_active_sources()

        # Should scrape both sources: 2 articles × 2 sources = 4 articles
        assert total_count == 4

        # Verify articles from both sources
        source1_articles = session.exec(
            select(Article).where(Article.source_id == active_source.id)
        ).all()
        source2_articles = session.exec(
            select(Article).where(Article.source_id == source2.id)
        ).all()

        assert len(source1_articles) == 2
        assert len(source2_articles) == 2

    @patch('app.services.rss_scraper.feedparser.parse')
    def test_skip_inactive_sources(
        self, mock_parse, session: Session,
        active_source: Source, inactive_source: Source, mock_rss_feed
    ):
        """Test that inactive sources are skipped"""
        mock_parse.return_value = mock_rss_feed

        total_count = scrape_all_active_sources()

        # Only active source should be scraped
        assert total_count == 2

        # Verify no articles from inactive source
        inactive_articles = session.exec(
            select(Article).where(Article.source_id == inactive_source.id)
        ).all()
        assert len(inactive_articles) == 0

    @patch('app.services.rss_scraper.feedparser.parse')
    def test_no_active_sources(self, mock_parse, session: Session, inactive_source: Source):
        """Test scraping when no active sources exist"""
        total_count = scrape_all_active_sources()

        assert total_count == 0
        mock_parse.assert_not_called()

    @patch('app.services.rss_scraper.feedparser.parse')
    def test_partial_failure(self, mock_parse, session: Session, active_source: Source):
        """Test that failure on one source doesn't stop others"""
        # Create second source
        source2 = Source(
            name="News 2",
            url="https://news2.com",
            rss_feed_url="https://news2.com/feed",
            political_lean=PoliticalLean.CENTER,
            is_active=True
        )
        session.add(source2)
        session.commit()

        # First call fails, second succeeds
        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.entries = [{'link': 'https://news2.com/article', 'title': 'Article'}]

        mock_parse.side_effect = [
            Exception("Error on first source"),
            mock_feed
        ]

        total_count = scrape_all_active_sources()

        # Second source should still be scraped
        assert total_count == 1

        # Verify article from second source exists
        articles = session.exec(
            select(Article).where(Article.source_id == source2.id)
        ).all()
        assert len(articles) == 1
