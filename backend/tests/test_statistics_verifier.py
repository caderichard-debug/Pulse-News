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
    verify_statistic_cross_reference,
    process_article_statistics,
    get_article_statistics
)
from datetime import datetime


class TestExtractStatistics:
    """Test statistic extraction from articles"""

    @patch('app.services.statistics_verifier.openai.ChatCompletion.create')
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

    @patch('app.services.statistics_verifier.openai.ChatCompletion.create')
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


class TestCrossReferenceVerification:
    """Test cross-reference verification of statistics"""

    def test_verify_with_multiple_sources(self, session: Session):
        """Test verification when statistic appears in multiple sources"""
        source1 = Source(
            name="Source 1",
            url="https://source1.com",
            rss_feed_url="https://source1.com/feed"
        )
        source2 = Source(
            name="Source 2",
            url="https://source2.com",
            rss_feed_url="https://source2.com/feed"
        )
        session.add_all([source1, source2])
        session.commit()

        # Create main article
        article1 = Article(
            source_id=source1.id,
            title="Main Article",
            url="https://source1.com/article",
            published_at=datetime.utcnow(),
            topic_category="Economy"
        )
        session.add(article1)
        session.commit()

        analysis1 = ArticleAnalysis(
            article_id=article1.id,
            summary="Economy grew 50%",
            sentiment_score=5,
            political_lean=PoliticalLean.CENTER,
            key_stats='["50% growth"]'
        )
        session.add(analysis1)

        # Create matching articles
        article2 = Article(
            source_id=source2.id,
            title="Other Article",
            url="https://source2.com/article",
            published_at=datetime.utcnow(),
            topic_category="Economy"
        )
        session.add(article2)
        session.commit()

        analysis2 = ArticleAnalysis(
            article_id=article2.id,
            summary="GDP increased by 50%",
            sentiment_score=5,
            political_lean=PoliticalLean.CENTER,
            key_stats='["50% growth in Q3"]'
        )
        session.add(analysis2)

        article3 = Article(
            source_id=source1.id,
            title="Third Article",
            url="https://source1.com/article3",
            published_at=datetime.utcnow(),
            topic_category="Economy"
        )
        session.add(article3)
        session.commit()

        analysis3 = ArticleAnalysis(
            article_id=article3.id,
            summary="50% economic growth reported",
            sentiment_score=5,
            political_lean=PoliticalLean.CENTER,
            key_stats='["Reports show 50% growth"]'
        )
        session.add(analysis3)
        session.commit()

        # Create verification
        verification = StatisticVerification(
            article_id=article1.id,
            statistic_text="50% growth",
            verification_status=VerificationStatus.UNVERIFIED
        )
        session.add(verification)
        session.commit()

        # Verify cross-reference
        verify_statistic_cross_reference(verification, article1, session)

        assert verification.verification_status == VerificationStatus.VERIFIED
        assert verification.verification_method == VerificationMethod.CROSS_REFERENCE
        assert verification.verified_sources is not None
        assert verification.confidence_score >= 0.7

    def test_no_verification_insufficient_matches(self, session: Session):
        """Test that verification fails with insufficient matches"""
        source = Source(
            name="Single Source",
            url="https://single.com",
            rss_feed_url="https://single.com/feed"
        )
        session.add(source)
        session.commit()

        article = Article(
            source_id=source.id,
            title="Unique Article",
            url="https://single.com/article",
            published_at=datetime.utcnow(),
            topic_category="Tech"
        )
        session.add(article)
        session.commit()

        analysis = ArticleAnalysis(
            article_id=article.id,
            summary="Unique statistic: 99% growth",
            sentiment_score=0,
            political_lean=PoliticalLean.CENTER,
            key_stats='["99%"]'
        )
        session.add(analysis)
        session.commit()

        verification = StatisticVerification(
            article_id=article.id,
            statistic_text="99% growth",
            verification_status=VerificationStatus.UNVERIFIED
        )
        session.add(verification)
        session.commit()

        # Should remain unverified
        verify_statistic_cross_reference(verification, article, session)
        assert verification.verification_status == VerificationStatus.UNVERIFIED


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
