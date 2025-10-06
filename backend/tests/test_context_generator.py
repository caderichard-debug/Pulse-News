"""
Tests for Context Generation Service
"""
import pytest
from unittest.mock import Mock, patch
from sqlmodel import Session, select
from .models import (
    Article, Source, ArticleAnalysis, ArticleContext,
    ProcessingStatus, PoliticalLean
)
from .services.context_generator import (
    generate_article_context,
    get_article_context,
    format_context_for_newsletter,
    process_article_contexts
)
from datetime import datetime
import json


class TestContextGeneration:
    """Test context generation"""

    @patch('app.services.context_generator.openai_api.chat.completions.create')
    def test_generate_context_success(self, mock_openai, session: Session):
        """Test successful context generation"""
        source = Source(
            name="News Source",
            url="https://news.com",
            rss_feed_url="https://news.com/feed"
        )
        session.add(source)
        session.commit()

        article = Article(
            source_id=source.id,
            title="Student Loan Forgiveness Announced",
            url="https://news.com/article",
            published_at=datetime.utcnow()
        )
        session.add(article)
        session.commit()

        analysis = ArticleAnalysis(
            article_id=article.id,
            summary="Biden announces relief for student borrowers",
            sentiment_score=5,
            political_lean=PoliticalLean.LEFT,
            has_context=False
        )
        session.add(analysis)
        session.commit()

        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content=json.dumps({
            "background": "Student loan debt has exceeded $1.7 trillion, affecting 43 million borrowers.",
            "key_players": ["President Biden", "Education Secretary", "Supreme Court"],
            "timeline": [
                {"date": "2020-11", "event": "Biden campaigns on debt relief"},
                {"date": "2022-08", "event": "First plan announced"},
                {"date": "2023-06", "event": "Supreme Court blocks plan"}
            ],
            "significance": "This affects millions of borrowers and has major economic implications.",
            "next_developments": "Further legal challenges expected in Q4.",
            "quality_score": 0.85
        })))]
        mock_response.usage = Mock(total_tokens=850)
        mock_openai.return_value = mock_response

        # Generate context
        context = generate_article_context(article, analysis, session)

        assert context is not None
        assert context.article_id == article.id
        assert "student loan debt" in context.background.lower()
        assert context.key_players is not None
        assert context.timeline is not None
        assert context.significance is not None
        assert context.next_developments is not None
        assert context.context_quality_score == 0.85
        assert context.tokens_used == 850

        # Check that analysis was updated
        session.refresh(analysis)
        assert analysis.has_context is True

    @patch('app.services.context_generator.openai_api.chat.completions.create')
    def test_skip_existing_context(self, mock_openai, session: Session):
        """Test skipping articles that already have context"""
        source = Source(
            name="News",
            url="https://news.com",
            rss_feed_url="https://news.com/feed"
        )
        session.add(source)
        session.commit()

        article = Article(
            source_id=source.id,
            title="Article",
            url="https://news.com/article",
            published_at=datetime.utcnow()
        )
        session.add(article)
        session.commit()

        analysis = ArticleAnalysis(
            article_id=article.id,
            summary="Summary",
            sentiment_score=0,
            political_lean=PoliticalLean.CENTER,
            has_context=True
        )
        session.add(analysis)
        session.commit()

        # Create existing context
        existing_context = ArticleContext(
            article_id=article.id,
            background="Existing background",
            context_quality_score=0.8
        )
        session.add(existing_context)
        session.commit()

        # Should return existing context without calling OpenAI
        context = generate_article_context(article, analysis, session)

        assert context.id == existing_context.id
        mock_openai.assert_not_called()

    @patch('app.services.context_generator.openai_api.chat.completions.create')
    def test_context_generation_error_handling(self, mock_openai, session: Session):
        """Test error handling in context generation"""
        source = Source(
            name="News",
            url="https://news.com",
            rss_feed_url="https://news.com/feed"
        )
        session.add(source)
        session.commit()

        article = Article(
            source_id=source.id,
            title="Article",
            url="https://news.com/article",
            published_at=datetime.utcnow()
        )
        session.add(article)
        session.commit()

        analysis = ArticleAnalysis(
            article_id=article.id,
            summary="Summary",
            sentiment_score=0,
            political_lean=PoliticalLean.CENTER,
            has_context=False
        )
        session.add(analysis)
        session.commit()

        # Mock OpenAI error
        mock_openai.side_effect = Exception("API Error")

        # Should return None and not crash
        context = generate_article_context(article, analysis, session)
        assert context is None


class TestGetArticleContext:
    """Test retrieving article context"""

    def test_get_context_success(self, session: Session):
        """Test getting context for an article"""
        source = Source(
            name="News",
            url="https://news.com",
            rss_feed_url="https://news.com/feed"
        )
        session.add(source)
        session.commit()

        article = Article(
            source_id=source.id,
            title="Article",
            url="https://news.com/article",
            published_at=datetime.utcnow()
        )
        session.add(article)
        session.commit()

        context = ArticleContext(
            article_id=article.id,
            background="Background info",
            key_players=json.dumps(["Player 1", "Player 2"]),
            timeline=json.dumps([
                {"date": "2024-01", "event": "Event 1"},
                {"date": "2024-02", "event": "Event 2"}
            ]),
            significance="This matters because...",
            next_developments="What's next...",
            context_quality_score=0.9
        )
        session.add(context)
        session.commit()

        # Get context
        context_data = get_article_context(article.id, session)

        assert context_data is not None
        assert context_data["background"] == "Background info"
        assert len(context_data["key_players"]) == 2
        assert context_data["key_players"][0] == "Player 1"
        assert len(context_data["timeline"]) == 2
        assert context_data["timeline"][0]["date"] == "2024-01"
        assert context_data["significance"] == "This matters because..."
        assert context_data["quality_score"] == 0.9

    def test_get_context_not_found(self, session: Session):
        """Test getting context for article without context"""
        source = Source(
            name="News",
            url="https://news.com",
            rss_feed_url="https://news.com/feed"
        )
        session.add(source)
        session.commit()

        article = Article(
            source_id=source.id,
            title="Article",
            url="https://news.com/article",
            published_at=datetime.utcnow()
        )
        session.add(article)
        session.commit()

        context_data = get_article_context(article.id, session)
        assert context_data is None


class TestFormatContextForNewsletter:
    """Test HTML formatting for newsletters"""

    def test_format_complete_context(self, session: Session):
        """Test formatting context with all fields"""
        context = ArticleContext(
            article_id=1,
            background="Student loan debt crisis background",
            key_players=json.dumps(["Biden", "Congress"]),
            timeline=json.dumps([
                {"date": "2020", "event": "Campaign promise"},
                {"date": "2023", "event": "Court decision"}
            ]),
            significance="Affects millions of borrowers",
            next_developments="Watch for new legislation"
        )

        html = format_context_for_newsletter(context)

        assert "📖 Background" in html
        assert "Student loan debt crisis background" in html
        assert "👥 Key Players" in html
        assert "Biden" in html
        assert "Congress" in html
        assert "⏱️ Timeline" in html
        assert "2020" in html
        assert "Campaign promise" in html
        assert "💡 Why This Matters" in html
        assert "Affects millions" in html
        assert "🔮 What's Next" in html
        assert "new legislation" in html

    def test_format_partial_context(self, session: Session):
        """Test formatting context with some fields missing"""
        context = ArticleContext(
            article_id=1,
            background="Some background",
            key_players=None,
            timeline=None,
            significance="It matters",
            next_developments=None
        )

        html = format_context_for_newsletter(context)

        assert "📖 Background" in html
        assert "Some background" in html
        assert "💡 Why This Matters" in html
        assert "It matters" in html
        # Should not include sections for missing fields
        assert "👥 Key Players" not in html
        assert "⏱️ Timeline" not in html
        assert "🔮 What's Next" not in html

    def test_format_empty_context(self):
        """Test formatting None context"""
        html = format_context_for_newsletter(None)
        assert html == ""


class TestProcessArticleContexts:
    """Test batch context processing"""

    @patch('app.services.context_generator.openai_api.chat.completions.create')
    def test_process_multiple_articles(self, mock_openai, session: Session):
        """Test processing multiple articles"""
        source = Source(
            name="News",
            url="https://news.com",
            rss_feed_url="https://news.com/feed"
        )
        session.add(source)
        session.commit()

        # Create multiple articles without context
        articles = []
        for i in range(3):
            article = Article(
                source_id=source.id,
                title=f"Article {i}",
                url=f"https://news.com/article{i}",
                published_at=datetime.utcnow()
            )
            session.add(article)
            session.commit()

            analysis = ArticleAnalysis(
                article_id=article.id,
                summary=f"Summary {i}",
                sentiment_score=0,
                political_lean=PoliticalLean.CENTER,
                has_context=False
            )
            session.add(analysis)
            session.commit()

            articles.append(article)

        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content=json.dumps({
            "background": "Background",
            "key_players": ["Player"],
            "timeline": [{"date": "2024", "event": "Event"}],
            "significance": "Significant",
            "next_developments": "Next",
            "quality_score": 0.8
        })))]
        mock_response.usage = Mock(total_tokens=500)
        mock_openai.return_value = mock_response

        # Process contexts
        stats = process_article_contexts(session, limit=3)

        assert stats["articles_processed"] == 3
        assert stats["contexts_generated"] == 3
        assert stats["total_tokens"] == 1500  # 500 * 3

    @patch('app.services.context_generator.openai_api.chat.completions.create')
    def test_process_respects_limit(self, mock_openai, session: Session):
        """Test that processing respects the limit parameter"""
        source = Source(
            name="News",
            url="https://news.com",
            rss_feed_url="https://news.com/feed"
        )
        session.add(source)
        session.commit()

        # Create 5 articles
        for i in range(5):
            article = Article(
                source_id=source.id,
                title=f"Article {i}",
                url=f"https://news.com/article{i}",
                published_at=datetime.utcnow()
            )
            session.add(article)
            session.commit()

            analysis = ArticleAnalysis(
                article_id=article.id,
                summary=f"Summary {i}",
                sentiment_score=0,
                political_lean=PoliticalLean.CENTER,
                has_context=False
            )
            session.add(analysis)
            session.commit()

        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content=json.dumps({
            "background": "B",
            "key_players": [],
            "timeline": [],
            "significance": "S",
            "next_developments": "N",
            "quality_score": 0.8
        })))]
        mock_response.usage = Mock(total_tokens=100)
        mock_openai.return_value = mock_response

        # Process with limit of 2
        stats = process_article_contexts(session, limit=2)

        # Should only process 2 articles
        assert stats["articles_processed"] == 2
        assert stats["contexts_generated"] == 2
