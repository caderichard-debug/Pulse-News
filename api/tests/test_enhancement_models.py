"""
Tests for newsletter enhancement models.
"""
import pytest
from sqlmodel import Session, select
from ..app.models import (
    Article, Source, ArticleAnalysis, ProcessingStatus, PoliticalLean,
    StatisticVerification, VerificationStatus, VerificationMethod,
    ArticleCluster, ArticleClusterMember,
    ArticleContext
)
from datetime import datetime


class TestStatisticVerification:
    """Test statistic verification model"""

    def test_create_statistic_verification(self, session: Session):
        """Test creating a statistic verification record"""
        # Create source and article
        source = Source(
            name="Test Source",
            url="https://test.com",
            rss_feed_url="https://test.com/feed",
            trust_score=0.9
        )
        session.add(source)
        session.commit()

        article = Article(
            source_id=source.id,
            title="Test Article",
            url="https://test.com/article1",
            published_at=datetime.utcnow(),
            processing_status=ProcessingStatus.COMPLETED
        )
        session.add(article)
        session.commit()

        # Create verification
        verification = StatisticVerification(
            article_id=article.id,
            statistic_text="50% increase in Q3",
            verification_status=VerificationStatus.VERIFIED,
            verification_method=VerificationMethod.CROSS_REFERENCE,
            confidence_score=0.95,
            verified_sources='["https://source1.com", "https://source2.com"]',
            verified_by="ai"
        )
        session.add(verification)
        session.commit()

        # Verify it was created
        db_verification = session.exec(
            select(StatisticVerification).where(StatisticVerification.article_id == article.id)
        ).first()

        assert db_verification is not None
        assert db_verification.statistic_text == "50% increase in Q3"
        assert db_verification.verification_status == VerificationStatus.VERIFIED
        assert db_verification.confidence_score == 0.95

    def test_multiple_verifications_per_article(self, session: Session):
        """Test that an article can have multiple statistic verifications"""
        source = Source(
            name="Test Source",
            url="https://test.com",
            rss_feed_url="https://test.com/feed2"
        )
        session.add(source)
        session.commit()

        article = Article(
            source_id=source.id,
            title="Article with Stats",
            url="https://test.com/article2",
            published_at=datetime.utcnow()
        )
        session.add(article)
        session.commit()

        # Add multiple verifications
        verifications = [
            StatisticVerification(
                article_id=article.id,
                statistic_text="50% increase",
                verification_status=VerificationStatus.VERIFIED
            ),
            StatisticVerification(
                article_id=article.id,
                statistic_text="2025 deadline",
                verification_status=VerificationStatus.UNVERIFIED
            ),
        ]
        for v in verifications:
            session.add(v)
        session.commit()

        # Query all verifications for article
        db_verifications = session.exec(
            select(StatisticVerification).where(StatisticVerification.article_id == article.id)
        ).all()

        assert len(db_verifications) == 2


class TestArticleCluster:
    """Test article clustering models"""

    def test_create_cluster_with_members(self, session: Session):
        """Test creating a cluster with multiple article members"""
        source = Source(
            name="News Source",
            url="https://news.com",
            rss_feed_url="https://news.com/feed"
        )
        session.add(source)
        session.commit()

        # Create articles
        article1 = Article(
            source_id=source.id,
            title="Student Loan Forgiveness Plan",
            url="https://news.com/loans1",
            published_at=datetime.utcnow()
        )
        article2 = Article(
            source_id=source.id,
            title="Biden Announces Student Debt Relief",
            url="https://news.com/loans2",
            published_at=datetime.utcnow()
        )
        session.add(article1)
        session.add(article2)
        session.commit()

        # Create cluster
        cluster = ArticleCluster(
            cluster_hash="abc123def456",
            primary_topic="Student Loan Forgiveness"
        )
        session.add(cluster)
        session.commit()

        # Add members
        member1 = ArticleClusterMember(
            cluster_id=cluster.id,
            article_id=article1.id,
            similarity_score=0.95
        )
        member2 = ArticleClusterMember(
            cluster_id=cluster.id,
            article_id=article2.id,
            similarity_score=0.92
        )
        session.add(member1)
        session.add(member2)
        session.commit()

        # Verify cluster
        db_cluster = session.exec(
            select(ArticleCluster).where(ArticleCluster.cluster_hash == "abc123def456")
        ).first()

        assert db_cluster is not None
        assert db_cluster.primary_topic == "Student Loan Forgiveness"

        # Verify members
        members = session.exec(
            select(ArticleClusterMember).where(ArticleClusterMember.cluster_id == cluster.id)
        ).all()

        assert len(members) == 2
        assert members[0].similarity_score >= 0.9


class TestArticleContext:
    """Test article context model"""

    def test_create_article_context(self, session: Session):
        """Test creating context for an article"""
        source = Source(
            name="Context Source",
            url="https://context.com",
            rss_feed_url="https://context.com/feed"
        )
        session.add(source)
        session.commit()

        article = Article(
            source_id=source.id,
            title="Complex Policy Issue",
            url="https://context.com/policy",
            published_at=datetime.utcnow()
        )
        session.add(article)
        session.commit()

        # Create context
        context = ArticleContext(
            article_id=article.id,
            background="This policy has been debated for years...",
            key_players='["Biden", "Congress", "Supreme Court"]',
            timeline='[{"date": "2023-06", "event": "Plan announced"}]',
            significance="This affects millions of Americans...",
            next_developments="Court ruling expected in Q4...",
            sources_consulted='["https://source1.com", "https://source2.com"]',
            context_quality_score=0.88,
            tokens_used=1200
        )
        session.add(context)
        session.commit()

        # Verify context
        db_context = session.exec(
            select(ArticleContext).where(ArticleContext.article_id == article.id)
        ).first()

        assert db_context is not None
        assert "debated for years" in db_context.background
        assert db_context.context_quality_score == 0.88
        assert db_context.tokens_used == 1200

    def test_one_context_per_article(self, session: Session):
        """Test that an article can only have one context (unique constraint)"""
        source = Source(
            name="Unique Source",
            url="https://unique.com",
            rss_feed_url="https://unique.com/feed"
        )
        session.add(source)
        session.commit()

        article = Article(
            source_id=source.id,
            title="Article",
            url="https://unique.com/article",
            published_at=datetime.utcnow()
        )
        session.add(article)
        session.commit()

        # First context should work
        context1 = ArticleContext(
            article_id=article.id,
            background="First context"
        )
        session.add(context1)
        session.commit()

        # Second context with same article_id should fail (unique constraint)
        context2 = ArticleContext(
            article_id=article.id,
            background="Second context"
        )
        session.add(context2)

        with pytest.raises(Exception):  # Should raise IntegrityError
            session.commit()


class TestArticleAnalysisEnhancements:
    """Test new fields added to ArticleAnalysis"""

    def test_verification_status_default(self, session: Session):
        """Test that new verification fields have correct defaults"""
        source = Source(
            name="Analysis Source",
            url="https://analysis.com",
            rss_feed_url="https://analysis.com/feed"
        )
        session.add(source)
        session.commit()

        article = Article(
            source_id=source.id,
            title="Analyzed Article",
            url="https://analysis.com/article",
            published_at=datetime.utcnow(),
            processing_status=ProcessingStatus.COMPLETED
        )
        session.add(article)
        session.commit()

        # Create analysis
        analysis = ArticleAnalysis(
            article_id=article.id,
            summary="Test summary",
            sentiment_score=5,
            political_lean=PoliticalLean.CENTER
        )
        session.add(analysis)
        session.commit()

        # Check defaults
        db_analysis = session.exec(
            select(ArticleAnalysis).where(ArticleAnalysis.article_id == article.id)
        ).first()

        assert db_analysis.stats_verification_status == VerificationStatus.UNVERIFIED
        assert db_analysis.stats_verification_date is None
        assert db_analysis.has_context is False

    def test_update_verification_fields(self, session: Session):
        """Test updating verification fields"""
        source = Source(
            name="Update Source",
            url="https://update.com",
            rss_feed_url="https://update.com/feed"
        )
        session.add(source)
        session.commit()

        article = Article(
            source_id=source.id,
            title="Updated Article",
            url="https://update.com/article",
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

        # Update verification fields
        analysis.stats_verification_status = VerificationStatus.VERIFIED
        analysis.stats_verification_date = datetime.utcnow()
        analysis.has_context = True
        session.add(analysis)
        session.commit()

        # Verify updates
        db_analysis = session.exec(
            select(ArticleAnalysis).where(ArticleAnalysis.article_id == article.id)
        ).first()

        assert db_analysis.stats_verification_status == VerificationStatus.VERIFIED
        assert db_analysis.stats_verification_date is not None
        assert db_analysis.has_context is True
