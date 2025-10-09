"""
Tests for the AI analyzer service.
Tests article analysis, batch processing, and OpenAI integration.
"""

import pytest
from unittest.mock import MagicMock, patch
from sqlmodel import Session, select
from app.services.ai_analyzer import (
    analyze_articles_batch,
    get_article_analysis,
    get_unanalyzed_article_count
)
from app.models import (
    Article, ArticleAnalysis, Source, ProcessingStatus, PoliticalLean
)
from datetime import datetime


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
def sample_article(session: Session, sample_source: Source):
    """Create a test article ready for analysis"""
    article = Article(
        source_id=sample_source.id,
        title="Test Article on Climate Policy",
        url="https://testnews.com/article1",
        content_text="This is a detailed article about climate change policy and its implications for the economy.",
        published_at=datetime.utcnow(),
        scraped_at=datetime.utcnow(),
        processing_status=ProcessingStatus.COMPLETED
    )
    session.add(article)
    session.commit()
    session.refresh(article)
    return article


@pytest.fixture
def analyzed_article(session: Session, sample_article: Article):
    """Create an article that already has analysis"""
    analysis = ArticleAnalysis(
        article_id=sample_article.id,
        summary="Test summary of the article",
        sentiment_score=5,
        political_lean=PoliticalLean.CENTER,
        bias_indicators="neutral",
        key_stats='["50% increase", "2030 target"]',
        processing_cost=0.002,
        processed_at=datetime.utcnow()
    )
    session.add(analysis)
    session.commit()
    session.refresh(analysis)
    return sample_article


class TestAnalyzeArticlesBatch:
    """Test the batch article analysis function"""

    @patch('app.services.ai_analyzer.openai_client')
    def test_analyze_articles_success(self, mock_client, session: Session, sample_article: Article):
        """Test successful batch analysis of articles"""
        # Mock OpenAI client
        mock_client.is_available.return_value = True
        mock_client.analyze_articles_batch.return_value = [
            {
                "summary": "Climate policy article summary",
                "sentiment_score": 3,
                "political_lean": "CENTER",
                "bias_indicators": "neutral",
                "key_stats": ["50% reduction", "2030 deadline"]
            }
        ]

        # Run analysis
        count = analyze_articles_batch(session, batch_size=5)

        # Verify results
        assert count == 1
        mock_client.analyze_articles_batch.assert_called_once()

        # Check database
        analysis = session.exec(
            select(ArticleAnalysis).where(ArticleAnalysis.article_id == sample_article.id)
        ).first()

        assert analysis is not None
        assert analysis.summary == "Climate policy article summary"
        assert analysis.sentiment_score == 3
        assert analysis.political_lean == PoliticalLean.CENTER
        assert analysis.bias_indicators == "neutral"

    @patch('app.services.ai_analyzer.openai_client')
    def test_analyze_no_api_key(self, mock_client, session: Session, sample_article: Article):
        """Test that analysis fails gracefully without API key"""
        mock_client.is_available.return_value = False

        count = analyze_articles_batch(session, batch_size=5)

        assert count == 0
        mock_client.analyze_articles_batch.assert_not_called()

    @patch('app.services.ai_analyzer.openai_client')
    def test_analyze_no_articles(self, mock_client, session: Session):
        """Test analysis when no articles are ready"""
        mock_client.is_available.return_value = True

        count = analyze_articles_batch(session, batch_size=5)

        assert count == 0
        mock_client.analyze_articles_batch.assert_not_called()

    @patch('app.services.ai_analyzer.openai_client')
    def test_analyze_skip_already_analyzed(self, mock_client, session: Session, analyzed_article: Article):
        """Test that already analyzed articles are skipped"""
        mock_client.is_available.return_value = True

        count = analyze_articles_batch(session, batch_size=5)

        assert count == 0
        mock_client.analyze_articles_batch.assert_not_called()

    @patch('app.services.ai_analyzer.openai_client')
    def test_analyze_invalid_political_lean(self, mock_client, session: Session, sample_article: Article):
        """Test handling of invalid political lean values"""
        mock_client.is_available.return_value = True
        mock_client.analyze_articles_batch.return_value = [
            {
                "summary": "Test summary",
                "sentiment_score": 0,
                "political_lean": "INVALID_VALUE",  # Invalid
                "bias_indicators": "neutral",
                "key_stats": []
            }
        ]

        count = analyze_articles_batch(session, batch_size=5)

        assert count == 1

        # Should default to CENTER
        analysis = session.exec(
            select(ArticleAnalysis).where(ArticleAnalysis.article_id == sample_article.id)
        ).first()
        assert analysis.political_lean == PoliticalLean.CENTER

    @patch('app.services.ai_analyzer.openai_client')
    def test_analyze_api_error(self, mock_client, session: Session, sample_article: Article):
        """Test handling of API errors"""
        mock_client.is_available.return_value = True
        mock_client.analyze_articles_batch.return_value = None  # API error

        count = analyze_articles_batch(session, batch_size=5)

        assert count == 0

        # No analysis should be created
        analysis = session.exec(
            select(ArticleAnalysis).where(ArticleAnalysis.article_id == sample_article.id)
        ).first()
        assert analysis is None

    @patch('app.services.ai_analyzer.openai_client')
    def test_analyze_batch_size_limit(self, mock_client, session: Session, sample_source: Source):
        """Test that batch size is respected"""
        # Create 10 articles
        for i in range(10):
            article = Article(
                source_id=sample_source.id,
                title=f"Article {i}",
                url=f"https://testnews.com/article{i}",
                content_text=f"Content {i}",
                published_at=datetime.utcnow(),
                scraped_at=datetime.utcnow(),
                processing_status=ProcessingStatus.COMPLETED
            )
            session.add(article)
        session.commit()

        mock_client.is_available.return_value = True
        mock_client.analyze_articles_batch.return_value = [
            {
                "summary": f"Summary {i}",
                "sentiment_score": 0,
                "political_lean": "CENTER",
                "bias_indicators": "neutral",
                "key_stats": []
            }
            for i in range(3)  # Only 3 will be analyzed
        ]

        count = analyze_articles_batch(session, batch_size=3)

        assert count == 3
        # Should only send 3 articles
        call_args = mock_client.analyze_articles_batch.call_args
        assert len(call_args[0][0]) == 3

    @patch('app.services.ai_analyzer.openai_client')
    def test_analyze_summary_truncation(self, mock_client, session: Session, sample_article: Article):
        """Test that summaries longer than 1000 chars are truncated"""
        long_summary = "x" * 2000  # 2000 char summary

        mock_client.is_available.return_value = True
        mock_client.analyze_articles_batch.return_value = [
            {
                "summary": long_summary,
                "sentiment_score": 0,
                "political_lean": "CENTER",
                "bias_indicators": "neutral",
                "key_stats": []
            }
        ]

        count = analyze_articles_batch(session, batch_size=5)

        assert count == 1

        analysis = session.exec(
            select(ArticleAnalysis).where(ArticleAnalysis.article_id == sample_article.id)
        ).first()
        assert len(analysis.summary) <= 1000


class TestGetArticleAnalysis:
    """Test retrieving article analysis"""

    def test_get_existing_analysis(self, session: Session, analyzed_article: Article):
        """Test retrieving an existing analysis"""
        analysis = get_article_analysis(analyzed_article.id, session)

        assert analysis is not None
        assert analysis.article_id == analyzed_article.id
        assert analysis.summary == "Test summary of the article"

    def test_get_nonexistent_analysis(self, session: Session, sample_article: Article):
        """Test retrieving analysis for article without one"""
        analysis = get_article_analysis(sample_article.id, session)

        assert analysis is None


class TestGetUnanalyzedArticleCount:
    """Test counting unanalyzed articles"""

    def test_count_with_no_articles(self, session: Session):
        """Test count when no articles exist"""
        count = get_unanalyzed_article_count(session)
        assert count == 0

    def test_count_with_unanalyzed_articles(self, session: Session, sample_article: Article):
        """Test count with unanalyzed articles"""
        count = get_unanalyzed_article_count(session)
        assert count == 1

    def test_count_excludes_analyzed_articles(self, session: Session, analyzed_article: Article):
        """Test that analyzed articles are not counted"""
        count = get_unanalyzed_article_count(session)
        assert count == 0

    def test_count_excludes_pending_articles(self, session: Session, sample_source: Source):
        """Test that pending articles are not counted"""
        article = Article(
            source_id=sample_source.id,
            title="Pending Article",
            url="https://testnews.com/pending",
            content_text="Content",
            published_at=datetime.utcnow(),
            scraped_at=datetime.utcnow(),
            processing_status=ProcessingStatus.PENDING  # Not COMPLETED
        )
        session.add(article)
        session.commit()

        count = get_unanalyzed_article_count(session)
        assert count == 0
