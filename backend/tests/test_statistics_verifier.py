"""
Tests for Statistics Verification Service
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlmodel import Session, select
from app.models import (
    Article, Source, ArticleAnalysis, StatisticVerification,
    ProcessingStatus, PoliticalLean, VerificationStatus, VerificationMethod
)
from app.services.statistics_verifier import (
    extract_statistics_from_article,
    verify_statistic_v2,
    process_article_statistics,
    get_article_statistics
)
from datetime import datetime


class TestExtractStatistics:
    """Test statistic extraction from articles"""

    @patch('app.services.statistics_verifier.openai_api.chat.completions.create')
    def test_extract_statistics_success(self, mock_openai, session: Session):
        """Test successful statistic extraction"""
        # Create source and article
        source = Source(
            name="Test News",
            url="https://test.com",
            rss_feed_url="https://test.com/feed"
        )
        session.add(source)
        session.commit()

        article = Article(
            source_id=source.id,
            title="Economic Growth Report",
            url="https://test.com/article1",
            published_at=datetime.utcnow(),
            processing_status=ProcessingStatus.COMPLETED
        )
        session.add(article)
        session.commit()

        analysis = ArticleAnalysis(
            article_id=article.id,
            summary="GDP grew by 50% in Q3 and unemployment fell to 3.5%",
            sentiment_score=5,
            political_lean=PoliticalLean.CENTER,
            key_stats='["50% GDP growth", "3.5% unemployment"]'
        )
        session.add(analysis)
        session.commit()

        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='''[
            {
                "exact_quote": "50% in Q3",
                "context": "GDP growth in third quarter",
                "verifiable": true,
                "confidence": 0.9
            },
            {
                "exact_quote": "3.5%",
                "context": "Unemployment rate",
                "verifiable": true,
                "confidence": 0.85
            }
        ]'''))]
        mock_openai.return_value = mock_response

        # Extract statistics
        verifications = extract_statistics_from_article(article, analysis, session)

        assert len(verifications) == 2
        assert verifications[0].statistic_text == "50% in Q3"
        assert verifications[0].confidence_score == 0.9
        assert verifications[0].verification_status == VerificationStatus.UNVERIFIED
        assert verifications[1].statistic_text == "3.5%"

    @patch('app.services.statistics_verifier.openai_api.chat.completions.create')
    def test_extract_no_statistics(self, mock_openai, session: Session):
        """Test article with no statistics"""
        source = Source(
            name="Test News",
            url="https://test.com",
            rss_feed_url="https://test.com/feed2"
        )
        session.add(source)
        session.commit()

        article = Article(
            source_id=source.id,
            title="Opinion Piece",
            url="https://test.com/article2",
            published_at=datetime.utcnow()
        )
        session.add(article)
        session.commit()

        analysis = ArticleAnalysis(
            article_id=article.id,
            summary="An opinion about current events",
            sentiment_score=0,
            political_lean=PoliticalLean.CENTER
        )
        session.add(analysis)
        session.commit()

        # Mock empty response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='[]'))]
        mock_openai.return_value = mock_response

        verifications = extract_statistics_from_article(article, analysis, session)

        assert len(verifications) == 0

    def test_skip_already_extracted(self, session: Session):
        """Test skipping articles that already have statistics"""
        source = Source(
            name="Test News",
            url="https://test.com",
            rss_feed_url="https://test.com/feed3"
        )
        session.add(source)
        session.commit()

        article = Article(
            source_id=source.id,
            title="Article",
            url="https://test.com/article3",
            published_at=datetime.utcnow()
        )
        session.add(article)
        session.commit()

        analysis = ArticleAnalysis(
            article_id=article.id,
            summary="Summary",
            sentiment_score=0,
            political_lean=PoliticalLean.CENTER
        )
        session.add(analysis)
        session.commit()

        # Add existing verification
        existing = StatisticVerification(
            article_id=article.id,
            statistic_text="Already extracted",
            verification_status=VerificationStatus.VERIFIED
        )
        session.add(existing)
        session.commit()

        # Should return empty list
        verifications = extract_statistics_from_article(article, analysis, session)
        assert len(verifications) == 0


# NOTE: Cross-reference verification has been replaced by V2 verification
# These tests are commented out and should be replaced with V2 tests
# TODO: Write new tests for verify_statistic_v2

# class TestCrossReferenceVerification:
#     """Test cross-reference verification of statistics"""
#     pass


class TestGetArticleStatistics:
    """Test retrieving article statistics"""

    def test_get_statistics_with_verifications(self, session: Session):
        """Test getting statistics for an article"""
        source = Source(
            name="Test",
            url="https://test.com",
            rss_feed_url="https://test.com/feed"
        )
        session.add(source)
        session.commit()

        article = Article(
            source_id=source.id,
            title="Article",
            url="https://test.com/article",
            published_at=datetime.utcnow()
        )
        session.add(article)
        session.commit()

        # Add verifications
        v1 = StatisticVerification(
            article_id=article.id,
            statistic_text="50%",
            verification_status=VerificationStatus.VERIFIED,
            confidence_score=0.9,
            notes="GDP growth",
            verified_at=datetime.utcnow()
        )
        v2 = StatisticVerification(
            article_id=article.id,
            statistic_text="3.5%",
            verification_status=VerificationStatus.UNVERIFIED,
            confidence_score=0.7,
            notes="Unemployment"
        )
        session.add_all([v1, v2])
        session.commit()

        stats = get_article_statistics(article.id, session)

        assert len(stats) == 2
        # Should be ordered by confidence descending
        assert stats[0]["text"] == "50%"
        assert stats[0]["status"] == "verified"
        assert stats[0]["confidence"] == 0.9
        assert stats[0]["context"] == "GDP growth"
        assert stats[1]["text"] == "3.5%"

    def test_get_statistics_no_verifications(self, session: Session):
        """Test getting statistics for article with none"""
        source = Source(
            name="Test",
            url="https://test.com",
            rss_feed_url="https://test.com/feed2"
        )
        session.add(source)
        session.commit()

        article = Article(
            source_id=source.id,
            title="Article",
            url="https://test.com/article2",
            published_at=datetime.utcnow()
        )
        session.add(article)
        session.commit()

        stats = get_article_statistics(article.id, session)
        assert len(stats) == 0
