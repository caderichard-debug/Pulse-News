"""
Simplified tests for newsletter service that work with current model structure.
Tests core newsletter generation logic with mocked external dependencies.
"""

import pytest
from unittest.mock import patch, MagicMock
from sqlmodel import Session
from app.models import (
    User, Article, ArticleAnalysis, Source, Topic,
    UserTopicPreference, ProcessingStatus, PoliticalLean
)
from datetime import datetime, timedelta


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
def sample_topic(session: Session):
    """Create a test topic"""
    topic = Topic(
        name="Technology",
        description="Tech news"
    )
    session.add(topic)
    session.commit()
    session.refresh(topic)
    return topic


@pytest.fixture
def active_user(session: Session, sample_topic: Topic):
    """Create an active, verified user with preferences"""
    user = User(
        email="test@example.com",
        name="Test User",
        hashed_password="hashed_password",
        is_active=True,
        email_verified=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    # Add topic preference
    pref = UserTopicPreference(
        user_id=user.id,
        topic_id=sample_topic.id,
        include_in_newsletter=True
    )
    session.add(pref)
    session.commit()

    return user


@pytest.fixture
def recent_article_with_analysis(session: Session, sample_source: Source, sample_topic: Topic):
    """Create a recent article with analysis"""
    # Create article
    article = Article(
        source_id=sample_source.id,
        title="New AI Breakthrough",
        url="https://testnews.com/ai-breakthrough",
        content_text="Article content here",
        published_at=datetime.utcnow(),
        scraped_at=datetime.utcnow(),
        processing_status=ProcessingStatus.COMPLETED
    )
    session.add(article)
    session.commit()
    session.refresh(article)

    # Link to topic
    article.topics = [sample_topic]
    session.add(article)

    # Create analysis
    analysis = ArticleAnalysis(
        article_id=article.id,
        summary="AI researchers achieved a major breakthrough in language processing.",
        sentiment_score=7,
        political_lean=PoliticalLean.CENTER,
        bias_indicators="neutral",
        key_stats='["95% accuracy", "10x faster"]',
        processing_cost=0.002,
        processed_at=datetime.utcnow()
    )
    session.add(analysis)
    session.commit()

    return article


class TestNewsletterServiceBasics:
    """Test basic newsletter service functionality"""

    @patch('app.services.newsletter_service.settings')
    def test_newsletter_requires_api_key(self, mock_settings):
        """Test that newsletter generation fails without API key"""
        from app.services.newsletter_service import generate_and_send_newsletters

        mock_settings.resend_api_key = None

        result = generate_and_send_newsletters()

        assert result["generated"] == 0
        assert result["sent"] == 0
        assert result["failed"] == 0

    @patch('app.services.newsletter_service._generate_newsletter_for_user')
    @patch('app.services.newsletter_service.settings')
    def test_generate_newsletter_for_user_called(
        self, mock_settings, mock_generate, session: Session, active_user: User
    ):
        """Test that newsletter generation is attempted for active users"""
        from app.services.newsletter_service import generate_and_send_newsletters

        mock_settings.resend_api_key = "test_key"
        mock_generate.return_value = None  # No content

        result = generate_and_send_newsletters(session)

        # Should attempt to generate for the active user
        assert mock_generate.called

    @patch('app.services.newsletter_service.settings')
    def test_render_newsletter_template(self, mock_settings):
        """Test newsletter template rendering with basic data"""
        from app.services.newsletter_service import _render_newsletter_template

        data = {
            "user_name": "Test User",
            "date": "January 1, 2025",
            "article_count": 5,
            "framework_count": 2,
            "frameworks": [],
            "articles": [
                {
                    "title": "Test Article",
                    "url": "https://example.com",
                    "source_name": "Test Source",
                    "political_lean": "CENTER",
                    "published_at": "Jan 01",
                    "summary": "Test summary",
                    "key_stats": '["stat1"]',
                    "sentiment_score": 0.5
                }
            ],
            "preferences_url": "https://pulse.news/preferences",
            "website_url": "https://pulse.news",
            "unsubscribe_url": "https://pulse.news/unsubscribe"
        }

        html = _render_newsletter_template(data)

        assert "Test User" in html
        assert "Test Article" in html
        assert "https://example.com" in html
