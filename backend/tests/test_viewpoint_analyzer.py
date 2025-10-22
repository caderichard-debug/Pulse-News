"""
Comprehensive tests for ViewpointAnalyzer service.

Covers all major functionality:
- Framework opposition detection
- Candidate processing and ranking
- Caching system
- AI explanation generation
- Error handling
- Performance scenarios
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from sqlmodel import Session, select
from sqlalchemy.orm import sessionmaker

from app.services.viewpoint_analyzer import ViewpointAnalyzer
from app.models import (
    Article, ArticleAnalysis, Source, ViewpointRelationship,
    Framework, ArticleFrameworkLink, PoliticalLean
)
from app.database import engine


@pytest.fixture
def session():
    """Create a test database session"""
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
def mock_article(mock_source):
    """Create a mock article"""
    return Article(
        id=1,
        title="Test Article",
        url="https://test.com/article",
        content_text="Test content here",
        source_id=mock_source.id,
        published_at=datetime.utcnow(),
        scraped_at=datetime.utcnow(),
        processing_status="completed",
        word_count=500
    )


@pytest.fixture
def mock_analysis():
    """Create a mock article analysis"""
    return ArticleAnalysis(
        id=1,
        article_id=1,
        summary="Test summary",
        sentiment_score=2.5,
        political_lean=PoliticalLean.CENTER,
        bias_indicators="neutral",
        processed_at=datetime.utcnow()
    )


@pytest.fixture
def mock_framework():
    """Create a mock framework"""
    return Framework(
        id=1,
        name="Test Framework",
        description="A test ethical framework",
        left_position="Individual Freedom",
        right_position="Collective Safety",
        axis_description="Freedom vs Safety"
    )


@pytest.fixture
def mock_framework_link(mock_article, mock_framework):
    """Create a mock framework link"""
    return ArticleFrameworkLink(
        article_id=mock_article.id,
        framework_id=mock_framework.id,
        relevance_score=0.8,
        position_on_axis=7,  # Right position
        ai_explanation="Test explanation"
    )


@pytest.fixture
def mock_opposing_article(mock_source):
    """Create a mock opposing article"""
    return Article(
        id=2,
        title="Opposing Article",
        url="https://test.com/opposing",
        content_text="Opposing content here",
        source_id=mock_source.id,
        published_at=datetime.utcnow(),
        scraped_at=datetime.utcnow(),
        processing_status="completed",
        word_count=500
    )


@pytest.fixture
def mock_opposing_analysis():
    """Create a mock opposing article analysis"""
    return ArticleAnalysis(
        id=2,
        article_id=2,
        summary="Opposing summary",
        sentiment_score=-3.0,
        political_lean=PoliticalLean.LEFT,
        bias_indicators="liberal",
        processed_at=datetime.utcnow()
    )


@pytest.fixture
def mock_opposing_framework_link(mock_opposing_article, mock_framework):
    """Create a mock opposing framework link"""
    return ArticleFrameworkLink(
        article_id=mock_opposing_article.id,
        framework_id=mock_framework.id,
        relevance_score=0.7,
        position_on_axis=-6,  # Left position (opposite)
        ai_explanation="Opposing explanation"
    )


class TestViewpointAnalyzerFrameworkOpposition:
    """Test framework opposition detection functionality"""

    def test_find_framework_oppositions_with_valid_data(
        self, session, mock_article, mock_analysis, mock_framework,
        mock_framework_link, mock_opposing_article, mock_opposing_analysis,
        mock_opposing_framework_link
    ):
        """Test successful framework opposition detection"""
        # Setup test data
        session.add_all([
            mock_article, mock_analysis, mock_framework, mock_framework_link,
            mock_opposing_article, mock_opposing_analysis, mock_opposing_framework_link
        ])
        session.commit()

        # Test the method
        oppositions = ViewpointAnalyzer._find_framework_oppositions(
            mock_article, mock_analysis, session
        )

        # Assertions
        assert len(oppositions) == 1
        assert oppositions[0]['article_id'] == mock_opposing_article.id
        assert oppositions[0]['relationship_type'] == 'framework_opposition'
        assert oppositions[0]['opposition_strength'] > 0.6  # Should be high for opposite positions
        assert oppositions[0]['framework'] == mock_framework
        assert oppositions[0]['primary_position'] == 7
        assert oppositions[0]['opposing_position'] == -6

    def test_find_framework_oppositions_no_frameworks(
        self, session, mock_article, mock_analysis
    ):
        """Test case when article has no framework relationships"""
        # Setup test data (no frameworks)
        session.add_all([mock_article, mock_analysis])
        session.commit()

        # Test the method
        oppositions = ViewpointAnalyzer._find_framework_oppositions(
            mock_article, mock_analysis, session
        )

        # Should return empty list
        assert oppositions == []

    def test_find_framework_oppositions_no_analysis(
        self, session, mock_article, mock_framework
    ):
        """Test case when article has no analysis"""
        # Setup test data (no analysis)
        session.add_all([mock_article, mock_framework])
        session.commit()

        # Test the method
        oppositions = ViewpointAnalyzer._find_framework_oppositions(
            mock_article, None, session
        )

        # Should return empty list
        assert oppositions == []

    def test_find_framework_oppositions_weak_relevance_threshold(
        self, session, mock_article, mock_analysis, mock_framework
    ):
        """Test that weak framework relationships are filtered out"""
        # Create weak framework link (below 0.6 threshold)
        weak_link = ArticleFrameworkLink(
            article_id=mock_article.id,
            framework_id=mock_framework.id,
            relevance_score=0.4,  # Below threshold
            position_on_axis=7
        )

        session.add_all([mock_article, mock_analysis, mock_framework, weak_link])
        session.commit()

        # Test the method
        oppositions = ViewpointAnalyzer._find_framework_oppositions(
            mock_article, mock_analysis, session
        )

        # Should return empty list (weak relationship filtered out)
        assert oppositions == []

    def test_find_framework_oppositions_position_gap_calculation(
        self, session, mock_article, mock_analysis, mock_framework,
        mock_framework_link, mock_opposing_article, mock_opposing_analysis
    ):
        """Test position gap calculation affects opposition strength"""
        # Create opposing article with moderate position difference
        moderate_link = ArticleFrameworkLink(
            article_id=mock_opposing_article.id,
            framework_id=mock_framework.id,
            relevance_score=0.7,
            position_on_axis=3,  # Moderate difference from 7
            ai_explanation="Moderate opposition"
        )

        session.add_all([
            mock_article, mock_analysis, mock_framework, mock_framework_link,
            mock_opposing_article, mock_opposing_analysis, moderate_link
        ])
        session.commit()

        # Test the method
        oppositions = ViewpointAnalyzer._find_framework_oppositions(
            mock_article, mock_analysis, session
        )

        # Should have lower strength than extreme opposition
        assert len(oppositions) == 1
        assert oppositions[0]['opposition_strength'] < 0.8  # Moderate opposition

    def test_find_framework_oppositions_not_opposite_positions(
        self, session, mock_article, mock_analysis, mock_framework,
        mock_framework_link, mock_opposing_article, mock_opposing_analysis
    ):
        """Test that similar positions are not considered oppositions"""
        # Create article with similar position
        similar_link = ArticleFrameworkLink(
            article_id=mock_opposing_article.id,
            framework_id=mock_framework.id,
            relevance_score=0.7,
            position_on_axis=6,  # Similar to 7 (not opposite)
            ai_explanation="Similar position"
        )

        session.add_all([
            mock_article, mock_analysis, mock_framework, mock_framework_link,
            mock_opposing_article, mock_opposing_analysis, similar_link
        ])
        session.commit()

        # Test the method
        oppositions = ViewpointAnalyzer._find_framework_oppositions(
            mock_article, mock_analysis, session
        )

        # Should return empty list (positions not opposite enough)
        assert oppositions == []


class TestViewpointAnalyzerCandidateProcessing:
    """Test candidate processing and ranking functionality"""

    @patch('app.services.viewpoint_analyzer.ViewpointAnalyzer._generate_framework_explanation')
    def test_process_candidates_deduplication(self, mock_generate_explanation):
        """Test duplicate articles are removed"""
        mock_generate_explanation.return_value = "Mock AI explanation"

        # Create duplicate candidates
        candidates = [
            {
                'article_id': 2,
                'relationship_type': 'framework_opposition',
                'opposition_strength': 0.8,
                'article': Mock(id=2),
                'framework': Mock(name='Test Framework', description='A test framework'),
                'reasoning': 'Test 1'
            },
            {
                'article_id': 2,  # Same article_id
                'relationship_type': 'sentiment_contrast',
                'opposition_strength': 0.7,
                'article': Mock(id=2),
                'framework': Mock(name='Test Framework', description='A test framework'),
                'reasoning': 'Test 2'
            },
            {
                'article_id': 3,  # Different article
                'relationship_type': 'framework_opposition',
                'opposition_strength': 0.6,
                'article': Mock(id=3),
                'framework': Mock(name='Test Framework', description='A test framework'),
                'reasoning': 'Test 3'
            }
        ]

        # Test processing
        processed = ViewpointAnalyzer._process_candidates(
            candidates, Mock(id=1), None
        )

        # Should have only 2 candidates (duplicate removed)
        assert len(processed) == 2
        article_ids = [c['article_id'] for c in processed]
        assert 2 in article_ids
        assert 3 in article_ids

    @patch('app.services.viewpoint_analyzer.ViewpointAnalyzer._generate_framework_explanation')
    def test_process_candidates_ranking_by_strength(self, mock_generate_explanation):
        """Test candidates are ranked by opposition strength"""
        mock_generate_explanation.return_value = "Mock AI explanation"
        candidates = [
            {
                'article_id': 2,
                'relationship_type': 'framework_opposition',
                'opposition_strength': 0.6,
                'article': Mock(id=2),
                'framework': Mock(name='Test Framework', description='A test framework'),
                'reasoning': 'Low strength'
            },
            {
                'article_id': 3,
                'relationship_type': 'framework_opposition',
                'opposition_strength': 0.9,
                'article': Mock(id=3),
                'framework': Mock(name='Test Framework', description='A test framework'),
                'reasoning': 'High strength'
            },
            {
                'article_id': 4,
                'relationship_type': 'framework_opposition',
                'opposition_strength': 0.7,
                'article': Mock(id=4),
                'framework': Mock(name='Test Framework', description='A test framework'),
                'reasoning': 'Medium strength'
            }
        ]

        # Test processing
        processed = ViewpointAnalyzer._process_candidates(
            candidates, Mock(id=1), None
        )

        # Should be sorted by strength (highest first)
        assert len(processed) == 3
        assert processed[0]['opposition_strength'] == 0.9
        assert processed[1]['opposition_strength'] == 0.7
        assert processed[2]['opposition_strength'] == 0.6

    @patch('app.services.viewpoint_analyzer.ViewpointAnalyzer._generate_framework_explanation')
    def test_process_candidates_quality_score_calculation(self, mock_generate_explanation):
        """Test quality score calculation"""
        mock_generate_explanation.return_value = "Mock AI explanation"
        # Create candidate with high quality components
        high_quality_candidate = {
            'article_id': 2,
            'relationship_type': 'framework_opposition',
            'opposition_strength': 0.8,
            'relevance_score': 0.9,
            'article': Mock(id=2),
            'analysis': Mock(),  # Has analysis
            'source': Mock(trust_score=0.8),  # Trusted source
            'framework': Mock(name='Test Framework', description='A test framework'),
            'reasoning': 'High quality'
        }

        # Create candidate with low quality components
        low_quality_candidate = {
            'article_id': 3,
            'relationship_type': 'framework_opposition',
            'opposition_strength': 0.8,
            'relevance_score': 0.4,
            'article': Mock(id=3),
            'analysis': None,  # No analysis
            'source': Mock(trust_score=0.3),  # Untrusted source
            'framework': Mock(name='Test Framework', description='A test framework'),
            'reasoning': 'Low quality'
        }

        candidates = [high_quality_candidate, low_quality_candidate]

        # Test processing
        processed = ViewpointAnalyzer._process_candidates(
            candidates, Mock(id=1), None
        )

        # High quality candidate should have higher quality score
        high_quality = next(c for c in processed if c['article_id'] == 2)
        low_quality = next(c for c in processed if c['article_id'] == 3)

        assert high_quality['quality_score'] > low_quality['quality_score']

    def test_process_candidates_empty_candidates(self):
        """Test processing empty candidates list"""
        processed = ViewpointAnalyzer._process_candidates([], Mock(id=1), None)
        assert processed == []

    @patch('app.services.viewpoint_analyzer.ViewpointAnalyzer._generate_framework_explanation')
    def test_process_candidates_mixed_relationship_types(self, mock_generate_explanation):
        """Test processing different relationship types"""
        mock_generate_explanation.return_value = "Mock AI explanation"
        candidates = [
            {
                'article_id': 2,
                'relationship_type': 'framework_opposition',
                'opposition_strength': 0.8,
                'article': Mock(id=2),
                'framework': Mock(name='Test Framework', description='A test framework'),
                'reasoning': 'Framework opposition'
            },
            {
                'article_id': 3,
                'relationship_type': 'sentiment_contrast',
                'opposition_strength': 0.7,
                'article': Mock(id=3),
                'framework': Mock(name='Test Framework', description='A test framework'),
                'reasoning': 'Sentiment contrast'
            }
        ]

        # Test processing
        processed = ViewpointAnalyzer._process_candidates(
            candidates, Mock(id=1), None
        )

        # Should handle both types correctly
        assert len(processed) == 2
        relationship_types = [c['relationship_type'] for c in processed]
        assert 'framework_opposition' in relationship_types
        assert 'sentiment_contrast' in relationship_types


class TestViewpointAnalyzerCaching:
    """Test caching system functionality"""

    def test_get_cached_results_with_valid_cache(self, session):
        """Test retrieving cached results"""
        # Create cached relationship
        cached_rel = ViewpointRelationship(
            primary_article_id=1,
            opposing_article_id=2,
            relationship_type='framework_opposition',
            opposition_strength=0.8,
            ai_explanation='Cached explanation',
            is_active=True,
            expires_at=datetime.utcnow() + timedelta(days=1),
            created_at=datetime.utcnow()
        )

        session.add(cached_rel)
        session.commit()

        # Mock article data for expected format
        mock_article = Mock(id=2)
        mock_analysis = Mock()
        mock_source = Mock(name="Test Source")

        with patch.object(session, 'exec', return_value=[
            (mock_article, mock_analysis, mock_source)
        ]):
            # Test getting cached results
            cached = ViewpointAnalyzer._get_cached_results(
                1, session, ['framework_opposition'], 5
            )

            # Should return cached data
            assert len(cached) == 1
            assert cached[0]['article_id'] == 2
            assert cached[0]['relationship_type'] == 'framework_opposition'
            assert cached[0]['cached'] is True

    def test_get_cached_results_expired_cache(self, session):
        """Test expired cache is not returned"""
        # Create expired relationship
        expired_rel = ViewpointRelationship(
            primary_article_id=1,
            opposing_article_id=2,
            relationship_type='framework_opposition',
            opposition_strength=0.8,
            is_active=True,
            expires_at=datetime.utcnow() - timedelta(days=1),  # Expired
            created_at=datetime.utcnow()
        )

        session.add(expired_rel)
        session.commit()

        # Test getting cached results
        cached = ViewpointAnalyzer._get_cached_results(
            1, session, ['framework_opposition'], 5
        )

        # Should return None (cache expired)
        assert cached is None

    def test_get_cached_results_no_cache(self, session):
        """Test when no cache exists"""
        # Test getting cached results
        cached = ViewpointAnalyzer._get_cached_results(
            1, session, ['framework_opposition'], 5
        )

        # Should return None (no cache)
        assert cached is None

    def test_cache_results_new_relationships(self, session):
        """Test caching new relationships"""
        # Create mock viewpoints
        viewpoints = [
            {
                'article_id': 2,
                'relationship_type': 'framework_opposition',
                'opposition_strength': 0.8,
                'ai_explanation': 'New explanation',
                'quality_score': 0.7
            }
        ]

        # Test caching
        ViewpointAnalyzer._cache_results(1, viewpoints, session)
        session.commit()

        # Verify cache was created
        cached_rel = session.exec(
            select(ViewpointRelationship).where(
                ViewpointRelationship.primary_article_id == 1
            )
        ).first()

        assert cached_rel is not None
        assert cached_rel.opposing_article_id == 2
        assert cached_rel.relationship_type == 'framework_opposition'
        assert cached_rel.ai_explanation == 'New explanation'
        assert cached_rel.quality_score == 0.7

    def test_cache_results_existing_relationships_update(self, session):
        """Test updating existing cached relationships"""
        # Create existing relationship
        existing_rel = ViewpointRelationship(
            primary_article_id=1,
            opposing_article_id=2,
            relationship_type='framework_opposition',
            opposition_strength=0.6,  # Old strength
            ai_explanation='Old explanation',
            quality_score=0.5,
            is_active=True,
            expires_at=datetime.utcnow() + timedelta(days=1),
            created_at=datetime.utcnow()
        )

        session.add(existing_rel)
        session.commit()

        # Create updated viewpoint
        viewpoints = [
            {
                'article_id': 2,
                'relationship_type': 'framework_opposition',
                'opposition_strength': 0.9,  # Updated strength
                'ai_explanation': 'Updated explanation',
                'quality_score': 0.8  # Updated quality
            }
        ]

        # Test caching (should update existing)
        ViewpointAnalyzer._cache_results(1, viewpoints, session)
        session.commit()

        # Verify update
        updated_rel = session.exec(
            select(ViewpointRelationship).where(
                ViewpointRelationship.primary_article_id == 1
            )
        ).first()

        assert updated_rel.opposition_strength == 0.9
        assert updated_rel.ai_explanation == 'Updated explanation'
        assert updated_rel.quality_score == 0.8


class TestViewpointAnalyzerAIIntegration:
    """Test AI integration for explanations"""

    @patch('backend.services.viewpoint_analyzer.openai_client')
    def test_generate_framework_explanation_with_valid_data(
        self, mock_openai_client, session
    ):
        """Test successful AI explanation generation"""
        # Setup mock OpenAI response
        mock_openai_client.generate_framework_opposition_explanation.return_value = (
            "This article emphasizes individual freedom while the opposing article prioritizes collective safety."
        )

        # Create mock data
        primary_article = Mock(id=1, title="Primary Article")
        opposing_article = Mock(id=2, title="Opposing Article")
        framework = Mock(
            name="Freedom vs Safety",
            left_position="Individual Freedom",
            right_position="Collective Safety"
        )

        # Test explanation generation
        explanation = ViewpointAnalyzer._generate_framework_explanation(
            primary_article, opposing_article, framework, session
        )

        # Verify AI client was called correctly
        mock_openai_client.generate_framework_opposition_explanation.assert_called_once()

        # Verify explanation was returned
        assert explanation == "This article emphasizes individual freedom while the opposing article prioritizes collective safety."

    @patch('backend.services.viewpoint_analyzer.openai_client')
    def test_generate_framework_explanation_missing_data(
        self, mock_openai_client, session
    ):
        """Test explanation generation with missing data"""
        # Mock OpenAI client available
        mock_openai_client.is_available.return_value = True

        # Test with missing framework
        explanation = ViewpointAnalyzer._generate_framework_explanation(
            Mock(), Mock(), None, session
        )

        # Should return None for missing framework
        assert explanation is None

    @patch('backend.services.viewpoint_analyzer.openai_client')
    def test_generate_framework_explanation_openai_unavailable(
        self, mock_openai_client, session
    ):
        """Test when OpenAI is unavailable"""
        # Mock OpenAI client unavailable
        mock_openai_client.is_available.return_value = False

        # Test explanation generation
        explanation = ViewpointAnalyzer._generate_framework_explanation(
            Mock(), Mock(), Mock(), session
        )

        # Should return None when OpenAI unavailable
        assert explanation is None

    @patch('backend.services.viewpoint_analyzer.openai_client')
    def test_generate_framework_explanation_invalid_response(
        self, mock_openai_client, session
    ):
        """Test handling invalid OpenAI response"""
        # Mock OpenAI returning None
        mock_openai_client.generate_framework_opposition_explanation.return_value = None

        # Test explanation generation
        explanation = ViewpointAnalyzer._generate_framework_explanation(
            Mock(), Mock(), Mock(), session
        )

        # Should return None for invalid response
        assert explanation is None

    @patch('backend.services.viewpoint_analyzer.openai_client')
    def test_generate_framework_explanation_exception_handling(
        self, mock_openai_client, session
    ):
        """Test exception handling in AI calls"""
        # Mock OpenAI raising exception
        mock_openai_client.generate_framework_opposition_explanation.side_effect = Exception(
            "OpenAI API error"
        )

        # Test explanation generation
        explanation = ViewpointAnalyzer._generate_framework_explanation(
            Mock(), Mock(), Mock(), session
        )

        # Should return None when exception occurs
        assert explanation is None


class TestViewpointAnalyzerMainMethods:
    """Test main public methods"""

    def test_find_opposing_viewpoints_with_valid_data(
        self, session, mock_article, mock_analysis, mock_framework,
        mock_framework_link, mock_opposing_article, mock_opposing_analysis,
        mock_opposing_framework_link
    ):
        """Test successful viewpoint finding"""
        # Setup test data
        session.add_all([
            mock_article, mock_analysis, mock_framework, mock_framework_link,
            mock_opposing_article, mock_opposing_analysis, mock_opposing_framework_link
        ])
        session.commit()

        # Test main method
        with patch.object(ViewpointAnalyzer, '_generate_framework_explanation') as mock_explain:
            mock_explain.return_value = "AI generated explanation"

            viewpoints = ViewpointAnalyzer.find_opposing_viewpoints(
                1, session, max_results=5
            )

        # Assertions
        assert len(viewpoints) == 1
        assert viewpoints[0]['article_id'] == mock_opposing_article.id
        assert viewpoints[0]['relationship_type'] == 'framework_opposition'
        assert viewpoints[0]['ai_explanation'] == "AI generated explanation"

    def test_find_opposing_viewpoints_no_article(self, session):
        """Test with non-existent article"""
        viewpoints = ViewpointAnalyzer.find_opposing_viewpoints(
            999, session, max_results=5
        )

        # Should return empty list
        assert viewpoints == []

    def test_find_opposing_viewpoints_with_relationship_type_filter(
        self, session, mock_article, mock_analysis, mock_framework,
        mock_framework_link, mock_opposing_article, mock_opposing_analysis,
        mock_opposing_framework_link
    ):
        """Test filtering by relationship type"""
        # Setup test data
        session.add_all([
            mock_article, mock_analysis, mock_framework, mock_framework_link,
            mock_opposing_article, mock_opposing_analysis, mock_opposing_framework_link
        ])
        session.commit()

        # Test with specific relationship type
        viewpoints = ViewpointAnalyzer.find_opposing_viewpoints(
            1, session, max_results=5, relationship_types=['framework_opposition']
        )

        # Should find framework oppositions
        assert len(viewpoints) == 1
        assert viewpoints[0]['relationship_type'] == 'framework_opposition'

        # Test with different relationship type
        viewpoints = ViewpointAnalyzer.find_opposing_viewpoints(
            1, session, max_results=5, relationship_types=['source_bias']
        )

        # Should return empty (no source bias relationships)
        assert viewpoints == []

    def test_find_opposing_viewpoints_uses_cached_results(
        self, session, mock_article, mock_analysis
    ):
        """Test that cached results are used when available"""
        # Create cached relationship
        cached_rel = ViewpointRelationship(
            primary_article_id=1,
            opposing_article_id=2,
            relationship_type='framework_opposition',
            opposition_strength=0.8,
            ai_explanation='Cached explanation',
            is_active=True,
            expires_at=datetime.utcnow() + timedelta(days=1),
            created_at=datetime.utcnow()
        )

        session.add_all([mock_article, mock_analysis, cached_rel])
        session.commit()

        # Mock article data for expected format
        mock_opposing_article = Mock(id=2)
        mock_opposing_analysis = Mock()
        mock_source = Mock(name="Test Source")

        with patch.object(session, 'exec', return_value=[
            (mock_opposing_article, mock_opposing_analysis, mock_source)
        ]):
            # Test viewpoint finding (should use cache)
            viewpoints = ViewpointAnalyzer.find_opposing_viewpoints(
                1, session, max_results=5
            )

        # Should return cached data
        assert len(viewpoints) == 1
        assert viewpoints[0]['cached'] is True


class TestViewpointAnalyzerErrorHandling:
    """Test error handling scenarios"""

    def test_database_error_handling(self, session):
        """Test graceful handling of database errors"""
        # Mock database session to raise error
        with patch.object(session, 'exec', side_effect=Exception("Database error")):
            # Should not raise exception, but handle gracefully
            try:
                ViewpointAnalyzer.find_opposing_viewpoints(1, session)
            except Exception:
                pytest.fail("Should handle database errors gracefully")

    def test_sqlalchemy_ambiguous_join_handling(self, session):
        """Test handling of SQLAlchemy ambiguous joins"""
        # This was an actual issue we encountered
        # Test that explicit join conditions prevent ambiguity
        mock_article = Mock(id=1)
        mock_analysis = Mock()

        with patch('backend.services.viewpoint_analyzer.select') as mock_select:
            # Simulate SQLAlchemy ambiguity error
            mock_select.side_effect = Exception("Can't determine which FROM clause to join from")

            try:
                ViewpointAnalyzer._find_framework_oppositions(mock_article, mock_analysis, session)
            except Exception as e:
                # Should be caught and logged, not crash
                assert "Can't determine which FROM clause" in str(e)

    def test_invalid_data_handling(self, session):
        """Test handling of invalid or malformed data"""
        # Test with completely invalid article
        viewpoints = ViewpointAnalyzer.find_opposing_viewpoints(-1, session)
        assert viewpoints == []

        # Test with max_results edge cases
        try:
            ViewpointAnalyzer.find_opposing_viewpoints(1, session, max_results=-1)
        except Exception:
            pytest.fail("Should handle invalid max_results gracefully")

        try:
            ViewpointAnalyzer.find_opposing_viewpoints(1, session, max_results=1000)
        except Exception:
            pytest.fail("Should handle large max_results gracefully")


class TestViewpointAnalyzerPerformance:
    """Test performance and efficiency scenarios"""

    def test_large_dataset_performance(self, session):
        """Test performance with large number of candidates"""
        # Create many mock candidates
        candidates = []
        for i in range(100):  # 100 candidates
            candidates.append({
                'article_id': i + 2,
                'relationship_type': 'framework_opposition',
                'opposition_strength': 0.5 + (i % 50) / 100,
                'article': Mock(id=i + 2),
                'reasoning': f'Candidate {i + 2}'
            })

        import time
        start_time = time.time()

        # Test processing large dataset
        processed = ViewpointAnalyzer._process_candidates(
            candidates, Mock(id=1), None
        )

        processing_time = time.time() - start_time

        # Should process quickly (< 1 second)
        assert processing_time < 1.0
        assert len(processed) == 100

    def test_memory_usage_with_many_articles(self, session):
        """Test memory usage doesn't grow excessively"""
        import psutil
        import os

        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Create and process many candidates
        candidates = []
        for i in range(500):  # 500 candidates
            candidates.append({
                'article_id': i + 2,
                'relationship_type': 'framework_opposition',
                'opposition_strength': 0.8,
                'article': Mock(id=i + 2),
                'reasoning': f'Candidate {i + 2}'
            })

        # Process candidates
        processed = ViewpointAnalyzer._process_candidates(
            candidates, Mock(id=1), None
        )

        # Check memory usage didn't grow excessively (< 50MB)
        final_memory = process.memory_info().rss
        memory_growth = (final_memory - initial_memory) / (1024 * 1024)  # Convert to MB

        assert memory_growth < 50  # Less than 50MB growth
        assert len(processed) == 500

    def test_concurrent_processing_safety(self, session):
        """Test that processing is thread-safe"""
        import threading
        import time

        # Create test candidates
        candidates = [
            {
                'article_id': i + 2,
                'relationship_type': 'framework_opposition',
                'opposition_strength': 0.8,
                'article': Mock(id=i + 2),
                'reasoning': f'Candidate {i + 2}'
            }
            for i in range(10)
        ]

        results = []
        errors = []

        def process_candidates():
            try:
                processed = ViewpointAnalyzer._process_candidates(
                    candidates, Mock(id=1), None
                )
                results.append(len(processed))
            except Exception as e:
                errors.append(e)

        # Run multiple threads concurrently
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=process_candidates)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=5)  # 5 second timeout

        # Should have processed successfully without errors
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 5
        assert all(r == 10 for r in results)  # All should process 10 candidates


if __name__ == "__main__":
    pytest.main([__file__, "-v"])