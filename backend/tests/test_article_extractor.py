"""
Tests for the article content extraction service.
Tests web scraping, content extraction, and fallback methods.
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from sqlmodel import Session, select
from ..services.article_extractor import (
    extract_article_content,
    process_pending_articles
)
from ..models import Article, Source, ProcessingStatus, PoliticalLean
from datetime import datetime
import requests


@pytest.fixture
def sample_source(session: Session):
    """Create a test source"""
    source = Source(
        name="Test News",
        url="https://testnews.com",
        rss_feed_url="https://testnews.com/rss",
        political_lean=PoliticalLean.CENTER,
        is_active=True
    )
    session.add(source)
    session.commit()
    session.refresh(source)
    return source


@pytest.fixture
def pending_article(session: Session, sample_source: Source):
    """Create a pending article ready for extraction"""
    article = Article(
        source_id=sample_source.id,
        title="Test Article",
        url="https://testnews.com/article",
        published_at=datetime.utcnow(),
        scraped_at=datetime.utcnow(),
        processing_status=ProcessingStatus.PENDING
    )
    session.add(article)
    session.commit()
    session.refresh(article)
    return article


@pytest.fixture
def sample_html():
    """Sample HTML content for testing"""
    return """
    <html>
    <head><title>Test Article</title></head>
    <body>
        <article>
            <h1>Breaking News: AI Breakthrough</h1>
            <p>Researchers announced a major breakthrough in artificial intelligence today.</p>
            <p>The new model shows unprecedented capabilities in natural language understanding.</p>
            <p>This development could revolutionize how we interact with computers.</p>
            <p>Industry experts are calling it a watershed moment for the field.</p>
        </article>
    </body>
    </html>
    """


@pytest.fixture
def sample_html_with_ads():
    """Sample HTML with ads and navigation (needs cleaning)"""
    return """
    <html>
    <head><title>Article</title></head>
    <body>
        <nav>Home | About | Contact</nav>
        <aside class="ad">Buy this product!</aside>
        <article>
            <h1>Main Article Content</h1>
            <p>This is the actual article content that should be extracted.</p>
            <p>It contains multiple paragraphs of valuable information.</p>
        </article>
        <aside class="ad">Another advertisement</aside>
        <footer>Copyright 2025</footer>
    </body>
    </html>
    """


class TestExtractArticleContent:
    """Test the article content extraction function"""

    @patch('app.services.article_extractor.requests.get')
    @patch('app.services.article_extractor.trafilatura.extract')
    def test_successful_extraction_trafilatura(self, mock_trafilatura, mock_get, sample_html):
        """Test successful extraction using trafilatura (primary method)"""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.text = sample_html
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Mock trafilatura extraction
        extracted_text = "Breaking News: AI Breakthrough. Researchers announced a major breakthrough in artificial intelligence today. The new model shows unprecedented capabilities in natural language understanding. This development could revolutionize how we interact with computers. Industry experts are calling it a watershed moment for the field."
        mock_trafilatura.return_value = extracted_text

        result = extract_article_content("https://testnews.com/article")

        assert result['success'] is True
        assert result['method'] == 'trafilatura'
        assert result['content'] == extracted_text
        assert result['word_count'] > 0
        mock_get.assert_called_once()

    @patch('bs4.BeautifulSoup')
    @patch('app.services.article_extractor.Document')
    @patch('app.services.article_extractor.requests.get')
    @patch('app.services.article_extractor.trafilatura.extract')
    def test_fallback_to_readability(self, mock_trafilatura, mock_get, mock_document, mock_bs, sample_html):
        """Test fallback to readability-lxml when trafilatura fails"""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.text = sample_html
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Trafilatura returns short content (< 200 chars)
        mock_trafilatura.return_value = "Too short"

        # Mock readability Document and BeautifulSoup
        # Need >200 chars after BeautifulSoup extracts text
        long_text = "This is a longer article content that should be extracted successfully from the HTML using readability library as a fallback method when trafilatura fails to extract sufficient content. Adding more text here to ensure we exceed the 200 character minimum requirement for successful extraction."
        mock_doc = Mock()
        mock_doc.summary.return_value = f"<p>{long_text}</p>"
        mock_document.return_value = mock_doc

        # Mock BeautifulSoup to extract text from HTML
        mock_soup = Mock()
        mock_soup.get_text.return_value = long_text
        mock_bs.return_value = mock_soup

        result = extract_article_content("https://testnews.com/article")

        assert result['success'] is True
        assert result['method'] == 'readability'
        assert len(result['content']) > 200

    @patch('app.services.article_extractor.requests.get')
    def test_request_timeout(self, mock_get):
        """Test handling of request timeout"""
        mock_get.side_effect = requests.Timeout("Connection timeout")

        result = extract_article_content("https://testnews.com/article", timeout=5)

        assert result['success'] is False
        assert result['content'] is None
        assert result['method'] is None

    @patch('app.services.article_extractor.requests.get')
    def test_request_error(self, mock_get):
        """Test handling of request errors (404, 500, etc.)"""
        mock_get.side_effect = requests.RequestException("404 Not Found")

        result = extract_article_content("https://testnews.com/article")

        assert result['success'] is False
        assert result['content'] is None

    @patch('app.services.article_extractor.Document')
    @patch('app.services.article_extractor.requests.get')
    @patch('app.services.article_extractor.trafilatura.extract')
    def test_extraction_too_short(self, mock_trafilatura, mock_get, mock_document, sample_html):
        """Test that very short extractions are rejected"""
        mock_response = Mock()
        mock_response.text = sample_html
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Both methods return content < 200 chars
        mock_trafilatura.return_value = "Short"

        # Mock readability also returning short content
        mock_doc = Mock()
        mock_doc.summary.return_value = "<p>Short</p>"
        mock_document.return_value = mock_doc

        result = extract_article_content("https://testnews.com/article")

        assert result['success'] is False

    @patch('app.services.article_extractor.requests.get')
    @patch('app.services.article_extractor.trafilatura.extract')
    def test_extraction_with_custom_timeout(self, mock_trafilatura, mock_get):
        """Test that custom timeout is respected"""
        mock_response = Mock()
        mock_response.text = "<html><body>Content</body></html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        mock_trafilatura.return_value = "x" * 300

        extract_article_content("https://testnews.com/article", timeout=20)

        # Verify timeout was passed to requests
        call_kwargs = mock_get.call_args[1]
        assert call_kwargs['timeout'] == 20

    @patch('app.services.article_extractor.requests.get')
    @patch('app.services.article_extractor.trafilatura.extract')
    def test_user_agent_header(self, mock_trafilatura, mock_get):
        """Test that User-Agent header is set (prevents blocking)"""
        mock_response = Mock()
        mock_response.text = "<html><body>Content</body></html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        mock_trafilatura.return_value = "x" * 300

        extract_article_content("https://testnews.com/article")

        # Verify User-Agent was sent
        call_kwargs = mock_get.call_args[1]
        assert 'headers' in call_kwargs
        assert 'User-Agent' in call_kwargs['headers']
        assert 'Mozilla' in call_kwargs['headers']['User-Agent']

    @patch('app.services.article_extractor.requests.get')
    @patch('app.services.article_extractor.trafilatura.extract')
    def test_word_count_calculation(self, mock_trafilatura, mock_get):
        """Test accurate word count calculation"""
        mock_response = Mock()
        mock_response.text = "<html><body>Content</body></html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Create content with known word count
        content_words = ["word"] * 500
        mock_trafilatura.return_value = " ".join(content_words)

        result = extract_article_content("https://testnews.com/article")

        assert result['word_count'] == 500


class TestProcessPendingArticles:
    """Test the batch article processing function"""

    @patch('app.services.article_extractor.extract_article_content')
    def test_process_single_article(self, mock_extract, session: Session, pending_article: Article):
        """Test processing a single pending article"""
        # Mock successful extraction
        mock_extract.return_value = {
            'success': True,
            'content': "Extracted article content with sufficient length for testing purposes.",
            'method': 'trafilatura',
            'word_count': 250
        }

        count = process_pending_articles(session, batch_size=10, delay=0)

        assert count == 1

        # Verify article was updated - need to refresh from DB
        session.expire(pending_article)
        updated_article = session.get(Article, pending_article.id)
        assert updated_article.processing_status == ProcessingStatus.COMPLETED
        assert updated_article.content_text is not None
        assert updated_article.word_count == 250
        assert updated_article.extraction_method == 'trafilatura'

    @patch('app.services.article_extractor.extract_article_content')
    def test_process_failed_extraction(self, mock_extract, session: Session, pending_article: Article):
        """Test handling of failed extraction"""
        # Mock failed extraction
        mock_extract.return_value = {
            'success': False,
            'content': None,
            'method': None,
            'word_count': 0
        }

        count = process_pending_articles(session, batch_size=10, delay=0)

        assert count == 0

        # Verify article was marked as failed
        session.expire(pending_article)
        updated_article = session.get(Article, pending_article.id)
        assert updated_article.processing_status == ProcessingStatus.FAILED
        assert updated_article.extraction_method == 'failed'

    @patch('app.services.article_extractor.extract_article_content')
    @patch('app.services.article_extractor.time.sleep')
    def test_rate_limiting(self, mock_sleep, mock_extract, session: Session, sample_source: Source):
        """Test that rate limiting delay is applied between requests"""
        # Create multiple pending articles
        for i in range(3):
            article = Article(
                source_id=sample_source.id,
                title=f"Article {i}",
                url=f"https://testnews.com/article{i}",
                published_at=datetime.utcnow(),
                scraped_at=datetime.utcnow(),
                processing_status=ProcessingStatus.PENDING
            )
            session.add(article)
        session.commit()

        mock_extract.return_value = {
            'success': True,
            'content': "x" * 250,
            'method': 'trafilatura',
            'word_count': 250
        }

        process_pending_articles(session, batch_size=10, delay=0.5)

        # Should sleep 2 times (between 3 articles)
        assert mock_sleep.call_count == 2
        mock_sleep.assert_called_with(0.5)

    @patch('app.services.article_extractor.extract_article_content')
    def test_batch_size_limit(self, mock_extract, session: Session, sample_source: Source):
        """Test that batch size limit is respected"""
        # Create 10 pending articles
        for i in range(10):
            article = Article(
                source_id=sample_source.id,
                title=f"Article {i}",
                url=f"https://testnews.com/article{i}",
                published_at=datetime.utcnow(),
                scraped_at=datetime.utcnow(),
                processing_status=ProcessingStatus.PENDING
            )
            session.add(article)
        session.commit()

        mock_extract.return_value = {
            'success': True,
            'content': "x" * 250,
            'method': 'trafilatura',
            'word_count': 250
        }

        # Process with batch_size=5
        count = process_pending_articles(session, batch_size=5, delay=0)

        # Should only process 5 articles
        assert count == 5
        assert mock_extract.call_count == 5

    @patch('app.services.article_extractor.extract_article_content')
    def test_no_pending_articles(self, mock_extract, session: Session):
        """Test handling when no pending articles exist"""
        count = process_pending_articles(session, batch_size=10, delay=0)

        assert count == 0
        mock_extract.assert_not_called()

    @patch('app.services.article_extractor.extract_article_content')
    def test_skip_non_pending_articles(self, mock_extract, session: Session, sample_source: Source):
        """Test that only PENDING articles are processed"""
        # Create articles with different statuses
        article_pending = Article(
            source_id=sample_source.id,
            title="Pending Article",
            url="https://testnews.com/pending",
            processing_status=ProcessingStatus.PENDING,
            published_at=datetime.utcnow(),
            scraped_at=datetime.utcnow()
        )
        article_completed = Article(
            source_id=sample_source.id,
            title="Completed Article",
            url="https://testnews.com/completed",
            processing_status=ProcessingStatus.COMPLETED,
            published_at=datetime.utcnow(),
            scraped_at=datetime.utcnow()
        )
        article_failed = Article(
            source_id=sample_source.id,
            title="Failed Article",
            url="https://testnews.com/failed",
            processing_status=ProcessingStatus.FAILED,
            published_at=datetime.utcnow(),
            scraped_at=datetime.utcnow()
        )
        session.add_all([article_pending, article_completed, article_failed])
        session.commit()

        mock_extract.return_value = {
            'success': True,
            'content': "x" * 250,
            'method': 'trafilatura',
            'word_count': 250
        }

        count = process_pending_articles(session, batch_size=10, delay=0)

        # Should only process 1 pending article
        assert count == 1
        assert mock_extract.call_count == 1
