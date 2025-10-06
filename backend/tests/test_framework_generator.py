"""
Tests for the framework generation and article mapping service.
Tests AI-driven framework discovery and article-to-framework mapping.
"""

import pytest
from unittest.mock import MagicMock, patch
from sqlmodel import Session, select
from .services.framework_generator import (
    map_articles_to_frameworks,
    discover_new_frameworks
)
from .models import (
    Article, ArticleAnalysis, Framework, ArticleFrameworkLink,
    Source, ProcessingStatus, PoliticalLean
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
def sample_framework(session: Session):
    """Create a test framework"""
    framework = Framework(
        name="Privacy vs Security",
        description="Balance between individual privacy and collective security",
        axis_description="privacy protection ←→ security enforcement",
        left_position="Strong privacy protections",
        right_position="Enhanced security measures",
        article_count=0,
        last_active=datetime.utcnow(),
        created_at=datetime.utcnow(),
        is_seed=True
    )
    session.add(framework)
    session.commit()
    session.refresh(framework)
    return framework


@pytest.fixture
def analyzed_article(session: Session, sample_source: Source):
    """Create an article with analysis but no framework mappings"""
    article = Article(
        source_id=sample_source.id,
        title="New Surveillance Law Sparks Privacy Debate",
        url="https://testnews.com/article1",
        content_text="Content about privacy and security",
        published_at=datetime.utcnow(),
        scraped_at=datetime.utcnow(),
        processing_status=ProcessingStatus.COMPLETED
    )
    session.add(article)
    session.commit()
    session.refresh(article)

    analysis = ArticleAnalysis(
        article_id=article.id,
        summary="Government proposes new surveillance measures citing security concerns, while privacy advocates raise alarms.",
        sentiment_score=0,
        political_lean=PoliticalLean.CENTER,
        bias_indicators="neutral",
        processing_cost=0.002,
        processed_at=datetime.utcnow()
    )
    session.add(analysis)
    session.commit()

    return article


@pytest.fixture
def mapped_article(session: Session, analyzed_article: Article, sample_framework: Framework):
    """Create an article that's already mapped to a framework"""
    link = ArticleFrameworkLink(
        article_id=analyzed_article.id,
        framework_id=sample_framework.id,
        relevance_score=0.8,
        position_on_axis=-5,
        ai_explanation="Article discusses privacy concerns",
        created_at=datetime.utcnow()
    )
    session.add(link)
    session.commit()
    return analyzed_article


class TestMapArticlesToFrameworks:
    """Test mapping articles to existing frameworks"""

    @patch('app.services.framework_generator.openai_client')
    def test_successful_mapping(
        self, mock_client, session: Session,
        analyzed_article: Article, sample_framework: Framework
    ):
        """Test successful article-to-framework mapping"""
        mock_client.is_available.return_value = True
        mock_client.map_article_to_frameworks.return_value = [
            {
                'framework_id': sample_framework.id,
                'relevance_score': 0.85,
                'position': -6,
                'explanation': 'Article strongly relates to privacy concerns vs security'
            }
        ]

        count = map_articles_to_frameworks(session, article_ids=[analyzed_article.id])

        assert count == 1

        # Verify mapping was created
        link = session.exec(
            select(ArticleFrameworkLink)
            .where(ArticleFrameworkLink.article_id == analyzed_article.id)
        ).first()

        assert link is not None
        assert link.framework_id == sample_framework.id
        assert link.relevance_score == 0.85
        assert link.position_on_axis == -6

    @patch('app.services.framework_generator.openai_client')
    def test_no_api_key(self, mock_client, session: Session):
        """Test that mapping fails gracefully without API key"""
        mock_client.is_available.return_value = False

        count = map_articles_to_frameworks(session)

        assert count == 0

    @patch('app.services.framework_generator.openai_client')
    def test_no_frameworks_available(self, mock_client, session: Session, analyzed_article: Article):
        """Test handling when no frameworks exist"""
        mock_client.is_available.return_value = True

        count = map_articles_to_frameworks(session, article_ids=[analyzed_article.id])

        assert count == 0
        mock_client.map_article_to_frameworks.assert_not_called()

    @patch('app.services.framework_generator.openai_client')
    def test_no_articles_to_map(self, mock_client, session: Session, sample_framework: Framework):
        """Test handling when no articles need mapping"""
        mock_client.is_available.return_value = True

        count = map_articles_to_frameworks(session)

        assert count == 0
        mock_client.map_article_to_frameworks.assert_not_called()

    @patch('app.services.framework_generator.openai_client')
    def test_skip_already_mapped_articles(
        self, mock_client, session: Session,
        mapped_article: Article, sample_framework: Framework
    ):
        """Test that already mapped articles are skipped"""
        mock_client.is_available.return_value = True

        count = map_articles_to_frameworks(session, limit=10)

        assert count == 0
        mock_client.map_article_to_frameworks.assert_not_called()

    @patch('app.services.framework_generator.openai_client')
    def test_multiple_framework_mappings(
        self, mock_client, session: Session,
        analyzed_article: Article
    ):
        """Test mapping one article to multiple frameworks"""
        # Create multiple frameworks
        fw1 = Framework(
            name="Framework 1",
            description="Test framework 1",
            axis_description="axis 1",
            left_position="left 1",
            right_position="right 1",
            created_at=datetime.utcnow()
        )
        fw2 = Framework(
            name="Framework 2",
            description="Test framework 2",
            axis_description="axis 2",
            left_position="left 2",
            right_position="right 2",
            created_at=datetime.utcnow()
        )
        session.add_all([fw1, fw2])
        session.commit()
        session.refresh(fw1)
        session.refresh(fw2)

        mock_client.is_available.return_value = True
        mock_client.map_article_to_frameworks.return_value = [
            {
                'framework_id': fw1.id,
                'relevance_score': 0.9,
                'position': 5,
                'explanation': 'Related to framework 1'
            },
            {
                'framework_id': fw2.id,
                'relevance_score': 0.7,
                'position': -3,
                'explanation': 'Related to framework 2'
            }
        ]

        count = map_articles_to_frameworks(session, article_ids=[analyzed_article.id])

        assert count == 2

        # Verify both mappings were created
        links = session.exec(
            select(ArticleFrameworkLink)
            .where(ArticleFrameworkLink.article_id == analyzed_article.id)
        ).all()

        assert len(links) == 2

    @patch('app.services.framework_generator.openai_client')
    def test_invalid_framework_id(
        self, mock_client, session: Session,
        analyzed_article: Article, sample_framework: Framework
    ):
        """Test handling of invalid framework IDs in response"""
        mock_client.is_available.return_value = True
        mock_client.map_article_to_frameworks.return_value = [
            {
                'framework_id': 99999,  # Non-existent framework
                'relevance_score': 0.8,
                'position': 0,
                'explanation': 'Invalid mapping'
            }
        ]

        count = map_articles_to_frameworks(session, article_ids=[analyzed_article.id])

        assert count == 0  # Should skip invalid framework

    @patch('app.services.framework_generator.openai_client')
    def test_explanation_truncation(
        self, mock_client, session: Session,
        analyzed_article: Article, sample_framework: Framework
    ):
        """Test that long explanations are truncated to 500 chars"""
        long_explanation = "x" * 1000

        mock_client.is_available.return_value = True
        mock_client.map_article_to_frameworks.return_value = [
            {
                'framework_id': sample_framework.id,
                'relevance_score': 0.8,
                'position': 0,
                'explanation': long_explanation
            }
        ]

        count = map_articles_to_frameworks(session, article_ids=[analyzed_article.id])

        assert count == 1

        link = session.exec(
            select(ArticleFrameworkLink)
            .where(ArticleFrameworkLink.article_id == analyzed_article.id)
        ).first()

        assert len(link.ai_explanation) == 500

    @patch('app.services.framework_generator.openai_client')
    def test_article_without_analysis(
        self, mock_client, session: Session,
        sample_source: Source, sample_framework: Framework
    ):
        """Test handling of articles without analysis"""
        article_no_analysis = Article(
            source_id=sample_source.id,
            title="Article Without Analysis",
            url="https://testnews.com/no-analysis",
            processing_status=ProcessingStatus.COMPLETED,
            published_at=datetime.utcnow(),
            scraped_at=datetime.utcnow()
        )
        session.add(article_no_analysis)
        session.commit()

        mock_client.is_available.return_value = True

        count = map_articles_to_frameworks(session, article_ids=[article_no_analysis.id])

        assert count == 0


class TestDiscoverNewFrameworks:
    """Test AI-driven framework discovery"""

    @patch('app.services.framework_generator.openai_client')
    def test_successful_framework_discovery(self, mock_client, session: Session, sample_source: Source):
        """Test successful discovery of new frameworks"""
        # Create enough recent articles
        for i in range(55):
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
            session.refresh(article)

            analysis = ArticleAnalysis(
                article_id=article.id,
                summary=f"Summary {i}",
                sentiment_score=0,
                political_lean=PoliticalLean.CENTER,
                bias_indicators="neutral",
                processing_cost=0.002,
                processed_at=datetime.utcnow()
            )
            session.add(analysis)
        session.commit()

        mock_client.is_available.return_value = True
        mock_client.generate_frameworks.return_value = [
            {
                'name': 'Human Agency vs Automation',
                'description': 'Debate over human control versus automated systems',
                'axis_description': 'human control ←→ automation',
                'left_position': 'Preserve human decision-making',
                'right_position': 'Embrace automated systems'
            },
            {
                'name': 'Innovation vs Regulation',
                'description': 'Balance between technological innovation and regulatory oversight',
                'axis_description': 'free innovation ←→ strict regulation',
                'left_position': 'Minimal regulation',
                'right_position': 'Strong regulatory frameworks'
            }
        ]

        count = discover_new_frameworks(session, min_articles=50)

        assert count == 2

        # Verify frameworks were created
        frameworks = session.exec(select(Framework)).all()
        assert len(frameworks) == 2
        assert frameworks[0].name == 'Human Agency vs Automation'
        assert frameworks[0].is_seed is False  # AI-generated

    @patch('app.services.framework_generator.openai_client')
    def test_insufficient_articles(self, mock_client, session: Session):
        """Test that discovery requires minimum number of articles"""
        mock_client.is_available.return_value = True

        count = discover_new_frameworks(session, min_articles=50)

        assert count == 0
        mock_client.generate_frameworks.assert_not_called()

    @patch('app.services.framework_generator.openai_client')
    def test_no_api_key(self, mock_client, session: Session):
        """Test that discovery fails gracefully without API key"""
        mock_client.is_available.return_value = False

        count = discover_new_frameworks(session)

        assert count == 0

    @patch('app.services.framework_generator.openai_client')
    def test_no_new_frameworks_generated(
        self, mock_client, session: Session, sample_source: Source
    ):
        """Test handling when AI doesn't find new frameworks"""
        # Create enough articles
        for i in range(55):
            article = Article(
                source_id=sample_source.id,
                title=f"Article {i}",
                url=f"https://testnews.com/article{i}",
                processing_status=ProcessingStatus.COMPLETED,
                published_at=datetime.utcnow(),
                scraped_at=datetime.utcnow()
            )
            session.add(article)
            session.commit()
            session.refresh(article)

            analysis = ArticleAnalysis(
                article_id=article.id,
                summary=f"Summary {i}",
                sentiment_score=0,
                political_lean=PoliticalLean.CENTER,
                bias_indicators="neutral",
                processing_cost=0.002,
                processed_at=datetime.utcnow()
            )
            session.add(analysis)
        session.commit()

        mock_client.is_available.return_value = True
        mock_client.generate_frameworks.return_value = []  # No new frameworks

        count = discover_new_frameworks(session, min_articles=50)

        assert count == 0

    @patch('app.services.framework_generator.openai_client')
    def test_field_truncation(self, mock_client, session: Session, sample_source: Source):
        """Test that long framework fields are truncated"""
        # Create enough articles
        for i in range(55):
            article = Article(
                source_id=sample_source.id,
                title=f"Article {i}",
                url=f"https://testnews.com/article{i}",
                processing_status=ProcessingStatus.COMPLETED,
                published_at=datetime.utcnow(),
                scraped_at=datetime.utcnow()
            )
            session.add(article)
            session.commit()
            session.refresh(article)

            analysis = ArticleAnalysis(
                article_id=article.id,
                summary=f"Summary {i}",
                sentiment_score=0,
                political_lean=PoliticalLean.CENTER,
                bias_indicators="neutral",
                processing_cost=0.002,
                processed_at=datetime.utcnow()
            )
            session.add(analysis)
        session.commit()

        mock_client.is_available.return_value = True
        mock_client.generate_frameworks.return_value = [
            {
                'name': 'x' * 500,  # Too long
                'description': 'y' * 2000,  # Too long
                'axis_description': 'z' * 500,  # Too long
                'left_position': 'a' * 500,  # Too long
                'right_position': 'b' * 500  # Too long
            }
        ]

        count = discover_new_frameworks(session, min_articles=50)

        assert count == 1

        framework = session.exec(select(Framework)).first()
        assert len(framework.name) <= 200
        assert len(framework.description) <= 1000
        assert len(framework.axis_description) <= 200
        assert len(framework.left_position) <= 200
        assert len(framework.right_position) <= 200

    @patch('app.services.framework_generator.openai_client')
    def test_only_recent_articles_analyzed(
        self, mock_client, session: Session, sample_source: Source
    ):
        """Test that only articles from last 7 days are analyzed"""
        # Create old articles (8 days ago)
        old_date = datetime.utcnow() - timedelta(days=8)
        for i in range(30):
            article = Article(
                source_id=sample_source.id,
                title=f"Old Article {i}",
                url=f"https://testnews.com/old{i}",
                published_at=old_date,
                scraped_at=old_date,
                processing_status=ProcessingStatus.COMPLETED
            )
            session.add(article)
            session.commit()
            session.refresh(article)

            analysis = ArticleAnalysis(
                article_id=article.id,
                summary=f"Old summary {i}",
                sentiment_score=0,
                political_lean=PoliticalLean.CENTER,
                bias_indicators="neutral",
                processing_cost=0.002,
                processed_at=old_date
            )
            session.add(analysis)
        session.commit()

        mock_client.is_available.return_value = True

        count = discover_new_frameworks(session, min_articles=50)

        # Should fail because no recent articles
        assert count == 0
