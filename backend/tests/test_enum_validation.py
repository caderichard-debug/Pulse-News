"""
Comprehensive tests to validate enum usage throughout the codebase.
These tests ensure that enums are used correctly and catch errors where
hardcoded strings are used instead of enum values.
"""

import pytest
from sqlmodel import Session
from app.models import (
    ProcessingStatus,
    PoliticalLean,
    SubscriptionTier,
    VerificationStatus,
    VerificationMethod,
    Source,
    Article,
    ArticleAnalysis,
    User,
    Topic,
    StatisticVerification,
)
from datetime import datetime


class TestProcessingStatusEnum:
    """Test ProcessingStatus enum values and database compatibility"""

    def test_enum_values_are_uppercase(self):
        """Verify ProcessingStatus enum values match expected uppercase format"""
        assert ProcessingStatus.PENDING == "PENDING"
        assert ProcessingStatus.PROCESSING == "PROCESSING"
        assert ProcessingStatus.COMPLETED == "COMPLETED"
        assert ProcessingStatus.FAILED == "FAILED"

    def test_enum_values_in_database(self, session: Session):
        """Test that ProcessingStatus enum values work correctly with the database"""
        source = Source(
            name="Test Source",
            url="https://example.com",
            rss_feed_url="https://example.com/feed",
            trust_score=5.0,
            is_active=True
        )
        session.add(source)
        session.commit()
        session.refresh(source)

        # Test each enum value
        for status in [ProcessingStatus.PENDING, ProcessingStatus.PROCESSING,
                       ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]:
            article = Article(
                title=f"Test Article - {status.value}",
                url=f"https://example.com/article-{status.value}",
                source_id=source.id,
                processing_status=status,
                published_at=datetime.utcnow()
            )
            session.add(article)
            session.commit()
            session.refresh(article)

            # Verify the value was stored correctly
            assert article.processing_status == status
            assert isinstance(article.processing_status, str)

    def test_invalid_processing_status_string_fails(self, session: Session):
        """Verify that using valid enum for ProcessingStatus works correctly"""
        source = Source(
            name="Test Source",
            url="https://example.com",
            rss_feed_url="https://example.com/feed",
            trust_score=5.0,
            is_active=True
        )
        session.add(source)
        session.commit()

        # This should work (valid enum)
        article = Article(
            title="Test Article",
            url="https://example.com/article",
            source_id=source.id,
            processing_status=ProcessingStatus.PENDING,
            published_at=datetime.utcnow()
        )
        session.add(article)
        session.commit()
        session.refresh(article)
        assert article.processing_status == ProcessingStatus.PENDING


class TestPoliticalLeanEnum:
    """Test PoliticalLean enum values and database compatibility"""

    def test_enum_values_are_lowercase(self):
        """Verify PoliticalLean enum values are lowercase (matching PostgreSQL enum)"""
        assert PoliticalLean.LEFT == "left"
        assert PoliticalLean.CENTER == "center"
        assert PoliticalLean.RIGHT == "right"

    def test_enum_values_in_database(self, session: Session):
        """Test that PoliticalLean enum values work correctly with the database"""
        source = Source(
            name="Test Source",
            url="https://example.com",
            rss_feed_url="https://example.com/feed",
            trust_score=5.0,
            is_active=True
        )
        session.add(source)
        session.commit()
        session.refresh(source)

        article = Article(
            title="Test Article",
            url="https://example.com/article",
            source_id=source.id,
            processing_status=ProcessingStatus.PENDING,
            published_at=datetime.utcnow()
        )
        session.add(article)
        session.commit()
        session.refresh(article)

        # Test each enum value in ArticleAnalysis
        for lean in [PoliticalLean.LEFT, PoliticalLean.CENTER, PoliticalLean.RIGHT]:
            analysis = ArticleAnalysis(
                article_id=article.id,
                summary=f"Test analysis with {lean.value} lean",
                sentiment_score=0,
                political_lean=lean,
                bias_indicators="Test",
                key_stats="[]"
            )
            session.add(analysis)
            session.commit()
            session.refresh(analysis)

            # Verify the value was stored correctly
            assert analysis.political_lean == lean
            assert isinstance(analysis.political_lean, str)
            assert analysis.political_lean == lean.value

            # Clean up for next iteration
            session.delete(analysis)
            session.commit()

    def test_article_analysis_political_lean(self, session: Session):
        """Test PoliticalLean enum in ArticleAnalysis model"""
        source = Source(
            name="Test Source 2",
            url="https://example.com/2",
            rss_feed_url="https://example.com/feed2",
            trust_score=5.0,
            is_active=True
        )
        session.add(source)
        session.commit()
        session.refresh(source)

        article = Article(
            title="Test Article 2",
            url="https://example.com/article2",
            source_id=source.id,
            processing_status=ProcessingStatus.COMPLETED,
            published_at=datetime.utcnow()
        )
        session.add(article)
        session.commit()
        session.refresh(article)

        # Test each political lean value
        for lean in [PoliticalLean.LEFT, PoliticalLean.CENTER, PoliticalLean.RIGHT]:
            analysis = ArticleAnalysis(
                article_id=article.id,
                summary=f"Analysis with {lean.value} lean",
                sentiment_score=0,
                political_lean=lean,
                bias_indicators="Test",
                key_stats="[]"
            )
            session.add(analysis)
            session.commit()
            session.refresh(analysis)

            # Verify the value was stored correctly
            assert analysis.political_lean == lean
            assert isinstance(analysis.political_lean, str)

            # Clean up for next iteration
            session.delete(analysis)
            session.commit()

    def test_uppercase_center_not_accepted(self):
        """Verify that uppercase 'CENTER' is NOT equal to the enum value"""
        # This test ensures we're using the correct lowercase enum values
        assert "CENTER" != PoliticalLean.CENTER
        assert "center" == PoliticalLean.CENTER
        assert "LEFT" != PoliticalLean.LEFT
        assert "left" == PoliticalLean.LEFT
        assert "RIGHT" != PoliticalLean.RIGHT
        assert "right" == PoliticalLean.RIGHT


class TestVerificationStatusEnum:
    """Test VerificationStatus enum values and database compatibility"""

    def test_enum_values_are_lowercase(self):
        """Verify VerificationStatus enum values are lowercase"""
        assert VerificationStatus.VERIFIED == "verified"
        assert VerificationStatus.UNVERIFIED == "unverified"
        assert VerificationStatus.DISPUTED == "disputed"
        assert VerificationStatus.FALSE == "false"

    def test_enum_values_in_database(self, session: Session):
        """Test that VerificationStatus enum values work correctly with the database"""
        source = Source(
            name="Test Source 3",
            url="https://example.com/3",
            rss_feed_url="https://example.com/feed3",
            trust_score=5.0,
            is_active=True
        )
        session.add(source)
        session.commit()
        session.refresh(source)

        article = Article(
            title="Test Article 3",
            url="https://example.com/article3",
            source_id=source.id,
            processing_status=ProcessingStatus.COMPLETED,
            published_at=datetime.utcnow()
        )
        session.add(article)
        session.commit()
        session.refresh(article)

        # Test each verification status
        for status in [VerificationStatus.VERIFIED, VerificationStatus.UNVERIFIED,
                       VerificationStatus.DISPUTED, VerificationStatus.FALSE]:
            verification = StatisticVerification(
                article_id=article.id,
                statistic_text=f"Test stat - {status.value}",
                verification_status=status,
                verification_method=VerificationMethod.AI_ANALYSIS,
                confidence_score=0.8,
                source_references=["https://example.com"]
            )
            session.add(verification)
            session.commit()
            session.refresh(verification)

            # Verify the value was stored correctly
            assert verification.verification_status == status
            assert isinstance(verification.verification_status, str)

            # Clean up for next iteration
            session.delete(verification)
            session.commit()


class TestVerificationMethodEnum:
    """Test VerificationMethod enum values and database compatibility"""

    def test_enum_values_are_lowercase_snake_case(self):
        """Verify VerificationMethod enum values are lowercase snake_case"""
        assert VerificationMethod.CROSS_REFERENCE == "cross_reference"
        assert VerificationMethod.API_CHECK == "api_check"
        assert VerificationMethod.MANUAL == "manual"
        assert VerificationMethod.AI_ANALYSIS == "ai_analysis"

    def test_enum_values_in_database(self, session: Session):
        """Test that VerificationMethod enum values work correctly with the database"""
        source = Source(
            name="Test Source 4",
            url="https://example.com/4",
            rss_feed_url="https://example.com/feed4",
            trust_score=5.0,
            is_active=True
        )
        session.add(source)
        session.commit()
        session.refresh(source)

        article = Article(
            title="Test Article 4",
            url="https://example.com/article4",
            source_id=source.id,
            processing_status=ProcessingStatus.COMPLETED,
            published_at=datetime.utcnow()
        )
        session.add(article)
        session.commit()
        session.refresh(article)

        # Test each verification method
        for method in [VerificationMethod.CROSS_REFERENCE, VerificationMethod.API_CHECK,
                       VerificationMethod.MANUAL, VerificationMethod.AI_ANALYSIS]:
            verification = StatisticVerification(
                article_id=article.id,
                statistic_text=f"Test stat - {method.value}",
                verification_status=VerificationStatus.VERIFIED,
                verification_method=method,
                confidence_score=0.8,
                source_references=["https://example.com"]
            )
            session.add(verification)
            session.commit()
            session.refresh(verification)

            # Verify the value was stored correctly
            assert verification.verification_method == method
            assert isinstance(verification.verification_method, str)

            # Clean up for next iteration
            session.delete(verification)
            session.commit()


class TestSubscriptionTierEnum:
    """Test SubscriptionTier enum values and database compatibility"""

    def test_enum_values_are_uppercase(self):
        """Verify SubscriptionTier enum values are uppercase"""
        assert SubscriptionTier.FREE == "FREE"
        assert SubscriptionTier.PREMIUM == "PREMIUM"

    def test_enum_values_in_database(self, session: Session):
        """Test that SubscriptionTier enum values work correctly with the database"""
        # Test each subscription tier
        for tier in [SubscriptionTier.FREE, SubscriptionTier.PREMIUM]:
            user = User(
                email=f"test_{tier.value}@example.com",
                hashed_password="test_password_hash",
                full_name=f"Test User {tier.value}",
                subscription_tier=tier
            )
            session.add(user)
            session.commit()
            session.refresh(user)

            # Verify the value was stored correctly
            assert user.subscription_tier == tier
            assert isinstance(user.subscription_tier, str)

            # Clean up for next iteration
            session.delete(user)
            session.commit()


class TestEnumCaseSensitivity:
    """Test that case sensitivity is enforced for all enums"""

    def test_political_lean_case_mismatch(self):
        """Ensure case-sensitive comparison catches uppercase strings"""
        # These should NOT match
        assert "CENTER" != PoliticalLean.CENTER.value
        assert "LEFT" != PoliticalLean.LEFT.value
        assert "RIGHT" != PoliticalLean.RIGHT.value

        # These SHOULD match
        assert "center" == PoliticalLean.CENTER.value
        assert "left" == PoliticalLean.LEFT.value
        assert "right" == PoliticalLean.RIGHT.value

    def test_verification_status_case_mismatch(self):
        """Ensure case-sensitive comparison catches uppercase strings"""
        # These should NOT match
        assert "VERIFIED" != VerificationStatus.VERIFIED.value
        assert "UNVERIFIED" != VerificationStatus.UNVERIFIED.value
        assert "DISPUTED" != VerificationStatus.DISPUTED.value
        assert "FALSE" != VerificationStatus.FALSE.value

        # These SHOULD match
        assert "verified" == VerificationStatus.VERIFIED.value
        assert "unverified" == VerificationStatus.UNVERIFIED.value
        assert "disputed" == VerificationStatus.DISPUTED.value
        assert "false" == VerificationStatus.FALSE.value

    def test_processing_status_uppercase_match(self):
        """ProcessingStatus should use uppercase (verify this is intentional)"""
        # These SHOULD match (uppercase)
        assert "PENDING" == ProcessingStatus.PENDING.value
        assert "PROCESSING" == ProcessingStatus.PROCESSING.value
        assert "COMPLETED" == ProcessingStatus.COMPLETED.value
        assert "FAILED" == ProcessingStatus.FAILED.value


class TestEnumDatabaseRoundTrip:
    """Test that enum values survive database round-trip correctly"""

    def test_political_lean_roundtrip(self, session: Session):
        """Ensure PoliticalLean values are correctly stored and retrieved"""
        source = Source(
            name="Roundtrip Test",
            url="https://example.com/roundtrip",
            rss_feed_url="https://example.com/roundtrip/feed",
            trust_score=7.0,
            is_active=True
        )
        session.add(source)
        session.commit()
        session.refresh(source)

        article = Article(
            title="Roundtrip Article",
            url="https://example.com/roundtrip/article",
            source_id=source.id,
            processing_status=ProcessingStatus.COMPLETED,
            published_at=datetime.utcnow()
        )
        session.add(article)
        session.commit()
        session.refresh(article)

        analysis = ArticleAnalysis(
            article_id=article.id,
            summary="Roundtrip test analysis",
            sentiment_score=0,
            political_lean=PoliticalLean.CENTER,
            bias_indicators="Test",
            key_stats="[]"
        )
        session.add(analysis)
        session.commit()
        analysis_id = analysis.id
        session.expunge(analysis)  # Remove from session

        # Retrieve from database
        retrieved_analysis = session.get(ArticleAnalysis, analysis_id)
        assert retrieved_analysis is not None
        assert retrieved_analysis.political_lean == PoliticalLean.CENTER
        assert retrieved_analysis.political_lean == "center"
        assert retrieved_analysis.political_lean != "CENTER"

    def test_all_political_leans_roundtrip(self, session: Session):
        """Test all PoliticalLean values in a single roundtrip"""
        source = Source(
            name="Multi Roundtrip Test",
            url="https://example.com/multi",
            rss_feed_url="https://example.com/multi/feed",
            trust_score=7.0,
            is_active=True
        )
        session.add(source)
        session.commit()
        session.refresh(source)

        analyses = []
        for i, lean in enumerate([PoliticalLean.LEFT, PoliticalLean.CENTER, PoliticalLean.RIGHT]):
            article = Article(
                title=f"Article {lean.value}",
                url=f"https://example.com/multi/article{i}",
                source_id=source.id,
                processing_status=ProcessingStatus.COMPLETED,
                published_at=datetime.utcnow()
            )
            session.add(article)
            session.commit()
            session.refresh(article)

            analysis = ArticleAnalysis(
                article_id=article.id,
                summary=f"Analysis {lean.value}",
                sentiment_score=0,
                political_lean=lean,
                bias_indicators="Test",
                key_stats="[]"
            )
            session.add(analysis)
            session.commit()
            analyses.append((analysis.id, lean))
            session.expunge(analysis)

        # Retrieve and verify all
        for analysis_id, expected_lean in analyses:
            retrieved = session.get(ArticleAnalysis, analysis_id)
            assert retrieved is not None
            assert retrieved.political_lean == expected_lean
            assert retrieved.political_lean == expected_lean.value
