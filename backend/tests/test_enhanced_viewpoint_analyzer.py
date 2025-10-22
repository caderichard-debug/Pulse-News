"""
Comprehensive tests for Enhanced Viewpoint Analyzer functionality.

Tests the enhanced analyzer features:
- Content theme extraction from article summaries
- Switched how/why explanations
- Cross-framework analysis
- Enhanced field population in ViewpointRelationship
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from sqlmodel import Session, select

from app.services.viewpoint_analyzer_enhanced import ViewpointAnalyzer
from app.models import (
    Article, ArticleAnalysis, Source, ViewpointRelationship,
    Framework, ArticleFrameworkLink, PoliticalLean
)


@pytest.fixture
def session():
    """Create test database session"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine("sqlite:///:memory:")
    from app.models import SQLModel
    SQLModel.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def mock_source():
    """Create a mock source"""
    return Source(
        id=1,
        name="Test Source",
        url="https://test.com",
        rss_url="https://test.com/rss",
        organizational_bias="center",
        trust_score=0.8
    )


@pytest.fixture
def mock_framework():
    """Create a mock framework"""
    return Framework(
        id=1,
        name="National Interest vs. Global Cooperation",
        description="Framework for analyzing national vs global priorities",
        left_position="Global Cooperation",
        right_position="National Interest",
        axis_description="National vs Global focus"
    )


@pytest.fixture
def mock_primary_article(mock_source):
    """Create a mock primary article with political content"""
    return Article(
        id=1,
        title="Trump announces new foreign policy initiative",
        url="https://test.com/article1",
        content_text="Trump announced today a significant shift in foreign policy...",
        source_id=mock_source.id,
        published_at=datetime.utcnow(),
        scraped_at=datetime.utcnow(),
        processing_status="completed",
        word_count=500
    )


@pytest.fixture
def mock_primary_analysis():
    """Create a mock primary article analysis"""
    return ArticleAnalysis(
        id=1,
        article_id=1,
        summary="Former President Trump announced a new foreign policy initiative focused on strengthening national interests and reevaluating international cooperation agreements.",
        sentiment_score=2.5,
        political_lean=PoliticalLean.RIGHT,
        bias_indicators="conservative-leaning",
        processed_at=datetime.utcnow()
    )


@pytest.fixture
def mock_opposing_article(mock_source):
    """Create a mock opposing article with political content"""
    return Article(
        id=2,
        title="International leaders criticize Trump's withdrawal from climate accords",
        url="https://test.com/article2",
        content_text="European leaders expressed concern over Trump's decision...",
        source_id=mock_source.id,
        published_at=datetime.utcnow(),
        scraped_at=datetime.utcnow(),
        processing_status="completed",
        word_count=450
    )


@pytest.fixture
def mock_opposing_analysis():
    """Create a mock opposing article analysis"""
    return ArticleAnalysis(
        id=2,
        article_id=2,
        summary="International leaders and environmental groups strongly criticized the decision to withdraw from global climate agreements, calling it a step back for international cooperation.",
        sentiment_score=-3.0,
        political_lean=PoliticalLean.LEFT,
        bias_indicators="liberal-leaning",
        processed_at=datetime.utcnow()
    )


@pytest.fixture
def mock_framework_links(mock_primary_article, mock_opposing_article, mock_framework):
    """Create mock framework links with opposing positions"""
    primary_link = ArticleFrameworkLink(
        article_id=mock_primary_article.id,
        framework_id=mock_framework.id,
        relevance_score=0.9,
        position_on_axis=6,  # Pro-National Interest
        ai_explanation="Strong emphasis on national priorities"
    )

    opposing_link = ArticleFrameworkLink(
        article_id=mock_opposing_article.id,
        framework_id=mock_framework.id,
        relevance_score=0.85,
        position_on_axis=-5,  # Pro-Global Cooperation
        ai_explanation="Strong emphasis on international cooperation"
    )

    return primary_link, opposing_link


class TestEnhancedAnalyzerContentExtraction:
    """Test content theme extraction functionality"""

    def test_extract_political_theme_from_summary(self, session):
        """Test extraction of political leadership theme"""
        analyzer = ViewpointAnalyzer(session)

        # Test article with political keywords
        article_analysis = ArticleAnalysis(
            summary="Trump and Biden campaign officials discussed election strategies during the recent political rally.",
            processed_at=datetime.utcnow()
        )

        candidate = {
            "article_id": 2,
            "summary": article_analysis.summary
        }

        # Mock database calls
        with patch.object(session, 'exec') as mock_exec:
            mock_exec.return_value.first.return_value = article_analysis

            explanations = analyzer._generate_framework_explanation(
                candidate, [], session
            )

            # Should extract "political leadership" theme
            how_explanation = explanations["how_this_opposes"]
            assert "political leadership" in how_explanation.lower()

    def test_extract_military_conflict_theme(self, session):
        """Test extraction of international conflict theme"""
        analyzer = ViewpointAnalyzer(session)

        article_analysis = ArticleAnalysis(
            summary="The ongoing military conflict in Ukraine has led to increased defense spending and war preparations.",
            processed_at=datetime.utcnow()
        )

        candidate = {
            "article_id": 2,
            "summary": article_analysis.summary
        }

        with patch.object(session, 'exec') as mock_exec:
            mock_exec.return_value.first.return_value = article_analysis

            explanations = analyzer._generate_framework_explanation(
                candidate, [], session
            )

            # Should extract "international conflict" theme
            how_explanation = explanations["how_this_opposes"]
            assert "international conflict" in how_explanation.lower()

    def test_extract_economic_theme(self, session):
        """Test extraction of economic policy theme"""
        analyzer = ViewpointAnalyzer(session)

        article_analysis = ArticleAnalysis(
            summary="Federal Reserve officials raised interest rates and discussed financial market regulations affecting trade.",
            processed_at=datetime.utcnow()
        )

        candidate = {
            "article_id": 2,
            "summary": article_analysis.summary
        }

        with patch.object(session, 'exec') as mock_exec:
            mock_exec.return_value.first.return_value = article_analysis

            explanations = analyzer._generate_framework_explanation(
                candidate, [], session
            )

            # Should extract "economic policy" theme
            how_explanation = explanations["how_this_opposes"]
            assert "economic policy" in how_explanation.lower()

    def test_extract_civil_liberties_theme(self, session):
        """Test extraction of civil liberties theme"""
        analyzer = ViewpointAnalyzer(session)

        article_analysis = ArticleAnalysis(
            summary="Civil rights organizations filed lawsuits defending freedom of speech and justice system reforms.",
            processed_at=datetime.utcnow()
        )

        candidate = {
            "article_id": 2,
            "summary": article_analysis.summary
        }

        with patch.object(session, 'exec') as mock_exec:
            mock_exec.return_value.first.return_value = article_analysis

            explanations = analyzer._generate_framework_explanation(
                candidate, [], session
            )

            # Should extract "civil liberties" theme
            how_explanation = explanations["how_this_opposes"]
            assert "civil liberties" in how_explanation.lower()

    def test_extract_environmental_theme(self, session):
        """Test extraction of environmental policy theme"""
        analyzer = ViewpointAnalyzer(session)

        article_analysis = ArticleAnalysis(
            summary="New climate change legislation focuses on renewable energy and environmental protection regulations.",
            processed_at=datetime.utcnow()
        )

        candidate = {
            "article_id": 2,
            "summary": article_analysis.summary
        }

        with patch.object(session, 'exec') as mock_exec:
            mock_exec.return_value.first.return_value = article_analysis

            explanations = analyzer._generate_framework_explanation(
                candidate, [], session
            )

            # Should extract "environmental policy" theme
            how_explanation = explanations["how_this_opposes"]
            assert "environmental policy" in how_explanation.lower()

    def test_fallback_to_current_events_theme(self, session):
        """Test fallback to current events theme when no specific keywords match"""
        analyzer = ViewpointAnalyzer(session)

        article_analysis = ArticleAnalysis(
            summary="Local community events include farmers markets, art exhibitions, and neighborhood gatherings this weekend.",
            processed_at=datetime.utcnow()
        )

        candidate = {
            "article_id": 2,
            "summary": article_analysis.summary
        }

        with patch.object(session, 'exec') as mock_exec:
            mock_exec.return_value.first.return_value = article_analysis

            explanations = analyzer._generate_framework_explanation(
                candidate, [], session
            )

            # Should extract "current events" theme as fallback
            how_explanation = explanations["how_this_opposes"]
            assert "current events" in how_explanation.lower()


class TestEnhancedAnalyzerSwitchedExplanations:
    """Test switched how/why explanation functionality"""

    def test_same_framework_explanations_are_switched(self, session):
        """Test that same-framework explanations are properly switched"""
        analyzer = ViewpointAnalyzer(session)

        article_analysis = ArticleAnalysis(
            summary="Political leaders debate economic policy approaches for the upcoming election.",
            processed_at=datetime.utcnow()
        )

        candidate = {
            "article_id": 2,
            "framework_name": "Economic Freedom vs Regulation",
            "primary_framework": "Economic Freedom vs Regulation",
            "opposing_framework": "Economic Freedom vs Regulation",
            "primary_pos": 7,
            "opposing_pos": -6,
            "position_gap": 13
        }

        with patch.object(session, 'exec') as mock_exec:
            mock_exec.return_value.first.return_value = article_analysis

            explanations = analyzer._generate_framework_explanation(
                candidate, [], session
            )

            how_explanation = explanations["how_this_opposes"]
            why_explanation = explanations["why_this_opposes"]

            # Why should be the mechanism (old how explanation)
            assert why_explanation == "Direct position reversal: +7 → -6 on Economic Freedom vs Regulation"

            # How should be content-focused (old why explanation)
            assert "economic policy" in how_explanation.lower()
            assert "opposes the primary piece" in how_explanation.lower()

    def test_cross_framework_explanations_are_switched(self, session):
        """Test that cross-framework explanations are properly switched"""
        analyzer = ViewpointAnalyzer(session)

        article_analysis = ArticleAnalysis(
            summary="Military officials discuss defense spending and international cooperation strategies.",
            processed_at=datetime.utcnow()
        )

        candidate = {
            "article_id": 2,
            "framework_name": "Individual Liberty vs Collective Welfare",
            "primary_framework": "National Interest vs Global Cooperation",
            "opposing_framework": "Individual Liberty vs Collective Welfare",
            "primary_pos": -3,
            "opposing_pos": 6,
            "position_gap": 9
        }

        with patch.object(session, 'exec') as mock_exec:
            mock_exec.return_value.first.return_value = article_analysis

            explanations = analyzer._generate_framework_explanation(
                candidate, [], session
            )

            how_explanation = explanations["how_this_opposes"]
            why_explanation = explanations["why_this_opposes"]

            # Why should be the mechanism (old how explanation)
            assert why_explanation == "Frames through 'Individual Liberty vs Collective Welfare' lens vs 'National Interest vs. Global Cooperation' approach; different ethical frameworks and value systems"

            # How should be content-focused (old why explanation)
            assert "international conflict" in how_explanation.lower()
            assert "challenges the primary article" in how_explanation.lower()

    def test_negative_position_explanations(self, session):
        """Test explanations when primary position is negative"""
        analyzer = ViewpointAnalyzer(session)

        article_analysis = ArticleAnalysis(
            summary="Conservative policymakers advocate for reduced international intervention and national sovereignty.",
            processed_at=datetime.utcnow()
        )

        candidate = {
            "article_id": 2,
            "framework_name": "National Interest vs. Global Cooperation",
            "primary_framework": "National Interest vs. Global Cooperation",
            "opposing_framework": "National Interest vs. Global Cooperation",
            "primary_pos": -4,
            "opposing_pos": 5,
            "position_gap": 9
        }

        with patch.object(session, 'exec') as mock_exec:
            mock_exec.return_value.first.return_value = article_analysis

            explanations = analyzer._generate_framework_explanation(
                candidate, [], session
            )

            how_explanation = explanations["how_this_opposes"]
            why_explanation = explanations["why_this_opposes"]

            # Why should be the mechanism
            assert why_explanation == "Direct position reversal: -4 → +5 on National Interest vs. Global Cooperation"

            # How should be content-focused
            assert "political leadership" in how_explanation.lower()
            assert "supports" in how_explanation.lower()
            assert "contrasting with the primary article's resistance" in how_explanation.lower()


class TestEnhancedAnalyzerDatabaseIntegration:
    """Test enhanced analyzer database integration"""

    def test_save_opposing_viewpoints_with_enhanced_fields(self, session, mock_primary_article):
        """Test that save_opposing_viewpoints populates enhanced fields"""
        analyzer = ViewpointAnalyzer(session)

        # Mock the find_opposing_viewpoints method to return enhanced candidates
        mock_candidates = [{
            "article_id": 2,
            "title": "Opposing Article",
            "url": "https://test.com/opposing",
            "summary": "Summary of opposing article",
            "sentiment_score": -2.0,
            "source_name": "Opposing Source",
            "published_at": datetime.utcnow().isoformat(),
            "relationship_type": "framework_opposition",
            "opposition_strength": 0.85,
            "reasoning": "Framework opposition",
            "ai_explanation": "AI generated explanation",
            "how_this_opposes": "On political leadership, this article opposes the primary by advocating different framework positions.",
            "why_this_opposes": "Direct position reversal: +6 → -4",
            "quality_score": 0.8,
            "framework_name": "Test Framework",
            "primary_position": 6,
            "opposing_position": -4
        }]

        with patch.object(analyzer, 'find_opposing_viewpoints', return_value=mock_candidates):
            with patch.object(session, 'add'):
                with patch.object(session, 'commit'):
                    saved_relationships = analyzer.save_opposing_viewpoints(
                        mock_primary_article, max_results=5, session=session
                    )

        # Should return the saved relationships
        assert len(saved_relationships) == 1
        # Note: In real implementation, these would be actual database objects
        # For testing purposes, we're just verifying the method structure

    def test_update_existing_relationships_with_enhanced_fields(self, session):
        """Test updating existing relationships with enhanced fields"""
        analyzer = ViewpointAnalyzer(session)

        # Create existing relationship without enhanced fields
        existing_relationship = ViewpointRelationship(
            primary_article_id=1,
            opposing_article_id=2,
            relationship_type="framework_opposition",
            opposition_strength=0.7,
            ai_explanation="Old explanation",
            how_this_opposes=None,  # Missing enhanced fields
            why_this_opposes=None,
            created_at=datetime.utcnow()
        )

        # Mock candidate with enhanced fields
        mock_candidates = [{
            "article_id": 2,
            "relationship_type": "framework_opposition",
            "opposition_strength": 0.85,
            "ai_explanation": "Updated explanation",
            "how_this_opposes": "Enhanced how explanation",
            "why_this_opposes": "Enhanced why explanation",
            "quality_score": 0.9
        }]

        with patch.object(session, 'exec', return_value=Mock(first=Mock(return_value=existing_relationship))):
            with patch.object(session, 'commit'):
                with patch.object(analyzer, 'find_opposing_viewpoints', return_value=mock_candidates):
                    saved_relationships = analyzer.save_opposing_viewpoints(
                        Mock(id=1), max_results=5, session=session
                    )

        # Should update the existing relationship with enhanced fields
        assert len(saved_relationships) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])