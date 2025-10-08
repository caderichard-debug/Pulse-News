"""
Tests for Statistics Verification Service
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlmodel import Session, select
from ..models import (
    Article, Source, ArticleAnalysis, StatisticVerification,
    ProcessingStatus, PoliticalLean, VerificationStatus, VerificationMethod
)
from ..services.statistics_verifier import (
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


# V2 Verification Tests
class TestV2Verification:
    """Test V2 verification pipeline with source tracing and fact-checking"""

    @patch('app.services.statistics_verifier.get_fact_check_integrator')
    @patch('app.services.statistics_verifier.get_credibility_rater')
    @patch('app.services.statistics_verifier.get_source_tracer')
    def test_verify_v2_full_pipeline_success(
        self, mock_tracer_getter, mock_rater_getter, mock_checker_getter, session: Session
    ):
        """Test full V2 verification pipeline with all stages successful"""
        # Create test data
        source = Source(
            name="Test News",
            url="https://test.com",
            rss_feed_url="https://test.com/feed"
        )
        session.add(source)
        session.commit()

        article = Article(
            source_id=source.id,
            title="Economic Report",
            url="https://test.com/article",
            published_at=datetime.utcnow(),
            content_text="According to the Bureau of Labor Statistics, unemployment is 3.5%"
        )
        session.add(article)
        session.commit()

        analysis = ArticleAnalysis(
            article_id=article.id,
            summary="Unemployment at 3.5%",
            sentiment_score=5,
            political_lean=PoliticalLean.CENTER
        )
        session.add(analysis)
        session.commit()

        verification = StatisticVerification(
            article_id=article.id,
            statistic_text="3.5% unemployment",
            verification_status=VerificationStatus.UNVERIFIED
        )
        session.add(verification)
        session.commit()

        # Mock all three stages
        mock_tracer = Mock()
        mock_tracer.trace_statistic_source.return_value = {
            "source_url": "https://bls.gov/data",
            "source_name": "Bureau of Labor Statistics",
            "source_excerpt": "According to the Bureau of Labor Statistics...",
            "confidence": 0.9
        }
        mock_tracer_getter.return_value = mock_tracer

        mock_rater = Mock()
        mock_rater.rate_source_credibility.return_value = 0.95
        mock_rater_getter.return_value = mock_rater

        mock_checker = Mock()
        mock_checker.verify_statistic.return_value = {
            "fact_check_status": "verified",
            "fact_check_source": "google_fact_check",
            "fact_check_url": "https://factcheck.google.com/result",
            "fact_check_details": "Verified by multiple fact-checkers",
            "confidence": 0.9
        }
        mock_checker_getter.return_value = mock_checker

        # Run verification
        result = verify_statistic_v2(verification, article, session)

        assert result is True
        assert verification.verification_status == VerificationStatus.VERIFIED
        assert verification.source_name == "Bureau of Labor Statistics"
        assert verification.source_url == "https://bls.gov/data"
        assert verification.source_credibility_score == 0.95
        assert verification.fact_check_status == "verified"
        assert verification.confidence_score > 0.7
        assert verification.verified_at is not None

    @patch('app.services.statistics_verifier.get_fact_check_integrator')
    @patch('app.services.statistics_verifier.get_credibility_rater')
    @patch('app.services.statistics_verifier.get_source_tracer')
    def test_verify_v2_no_source_found(
        self, mock_tracer_getter, mock_rater_getter, mock_checker_getter, session: Session
    ):
        """Test V2 verification when no source can be traced"""
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
            published_at=datetime.utcnow(),
            content_text="Some statistic without a clear source."
        )
        session.add(article)
        session.commit()

        verification = StatisticVerification(
            article_id=article.id,
            statistic_text="99%",
            verification_status=VerificationStatus.UNVERIFIED
        )
        session.add(verification)
        session.commit()

        # Mock no source found
        mock_tracer = Mock()
        mock_tracer.trace_statistic_source.return_value = None
        mock_tracer_getter.return_value = mock_tracer

        mock_checker = Mock()
        mock_checker.verify_statistic.return_value = None
        mock_checker_getter.return_value = mock_checker

        result = verify_statistic_v2(verification, article, session)

        assert result is True
        assert verification.verification_status == VerificationStatus.UNVERIFIED
        assert verification.source_name is None


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
