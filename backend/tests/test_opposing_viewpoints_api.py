"""
Comprehensive tests for opposing viewpoints API endpoint.

Tests all aspects of the /articles/{id}/opposing-viewpoints endpoint:
- Happy path scenarios
- Authentication and authorization
- Input validation
- Response format validation
- Error handling
- Performance testing
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, select
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import json

from ..main import app
from ..models import (
    User, Article, ArticleAnalysis, Source, ViewpointRelationship,
    Framework, ArticleFrameworkLink, PoliticalLean
)
from ..database import get_session
from ..routes.auth import create_access_token


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def session():
    """Create test database session"""
    engine = create_engine("sqlite:///:memory:")
    from ..models import SQLModel
    SQLModel.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_user(session):
    """Create a test user"""
    user = User(
        email="test@example.com",
        name="Test User",
        email_verified=True,
        is_admin=False
    )
    session.add(user)
    session.commit()
    return user


@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers"""
    token = create_access_token(data={"sub": test_user.email})
    return {"Authorization": f"Bearer {token}"}


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
def mock_article(session, mock_source):
    """Create a mock article with analysis"""
    article = Article(
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

    analysis = ArticleAnalysis(
        article_id=1,
        summary="Test summary",
        sentiment_score=2.5,
        political_lean=PoliticalLean.CENTER,
        bias_indicators="neutral",
        processed_at=datetime.utcnow()
    )

    session.add_all([article, analysis])
    session.commit()
    return article


@pytest.fixture
def mock_framework(session):
    """Create a mock framework"""
    framework = Framework(
        id=1,
        name="Test Framework",
        description="A test ethical framework",
        left_position="Individual Freedom",
        right_position="Collective Safety",
        axis_description="Freedom vs Safety"
    )
    session.add(framework)
    session.commit()
    return framework


@pytest.fixture
def mock_viewpoint_relationship(session, mock_article):
    """Create a mock viewpoint relationship"""
    viewpoint = ViewpointRelationship(
        primary_article_id=mock_article.id,
        opposing_article_id=2,
        relationship_type="framework_opposition",
        opposition_strength=0.8,
        ai_explanation="Test explanation",
        quality_score=0.7,
        is_active=True,
        expires_at=datetime.utcnow() + timedelta(days=7),
        created_at=datetime.utcnow()
    )
    session.add(viewpoint)
    session.commit()
    return viewpoint


class TestOpposingViewpointsAPIHappyPath:
    """Test successful API responses"""

    def test_get_opposing_viewpoints_with_valid_article(
        self, client, session, mock_article, mock_viewpoint_relationship, auth_headers
    ):
        """Test successful response with valid article"""
        # Mock OpposingViewpoints service
        with patch('backend.services.viewpoint_analyzer.ViewpointAnalyzer.find_opposing_viewpoints') as mock_find:
            mock_find.return_value = [
                {
                    'article_id': 2,
                    'title': 'Opposing Article',
                    'url': 'https://test.com/opposing',
                    'source_name': 'Test Source',
                    'source_bias': 'center',
                    'published_at': datetime.utcnow().isoformat(),
                    'sentiment_score': -2.0,
                    'political_lean': 'left',
                    'summary': 'Opposing summary',
                    'relationship_type': 'framework_opposition',
                    'opposition_strength': 0.8,
                    'reasoning': 'Framework opposition',
                    'ai_explanation': 'AI explanation',
                    'quality_score': 0.7,
                    'framework_name': 'Test Framework',
                    'primary_position': 7,
                    'opposing_position': -6
                }
            ]

            response = client.get(
                "/articles/1/opposing-viewpoints",
                headers=auth_headers
            )

        # Assertions
        assert response.status_code == 200
        data = response.json()

        assert data['primary_article_id'] == 1
        assert data['total_found'] == 1
        assert data['relationship_types_available'] == ['framework_opposition']
        assert len(data['opposing_viewpoints']) == 1

        viewpoint = data['opposing_viewpoints'][0]
        assert viewpoint['article_id'] == 2
        assert viewpoint['title'] == 'Opposing Article'
        assert viewpoint['relationship_type'] == 'framework_opposition'
        assert viewpoint['opposition_strength'] == 0.8
        assert viewpoint['ai_explanation'] == 'AI explanation'
        assert viewpoint['framework_name'] == 'Test Framework'

    def test_get_opposing_viewpoints_with_multiple_viewpoints(
        self, client, session, mock_article, auth_headers
    ):
        """Test response with multiple opposing viewpoints"""
        with patch('backend.services.viewpoint_analyzer.ViewpointAnalyzer.find_opposing_viewpoints') as mock_find:
            mock_find.return_value = [
                {
                    'article_id': 2,
                    'title': 'Opposing Article 1',
                    'url': 'https://test.com/opposing1',
                    'source_name': 'Source 1',
                    'published_at': datetime.utcnow().isoformat(),
                    'relationship_type': 'framework_opposition',
                    'opposition_strength': 0.9,
                    'reasoning': 'Strong opposition'
                },
                {
                    'article_id': 3,
                    'title': 'Opposing Article 2',
                    'url': 'https://test.com/opposing2',
                    'source_name': 'Source 2',
                    'published_at': datetime.utcnow().isoformat(),
                    'relationship_type': 'sentiment_contrast',
                    'opposition_strength': 0.7,
                    'reasoning': 'Sentiment contrast'
                }
            ]

            response = client.get(
                "/articles/1/opposing-viewpoints",
                headers=auth_headers
            )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data['total_found'] == 2
        assert len(data['opposing_viewpoints']) == 2

        # Check both relationship types are available
        relationship_types = [vp['relationship_type'] for vp in data['opposing_viewpoints']]
        assert 'framework_opposition' in relationship_types
        assert 'sentiment_contrast' in relationship_types

    def test_get_opposing_viewpoints_framework_opposition_details(
        self, client, session, mock_article, auth_headers
    ):
        """Test detailed framework opposition data"""
        with patch('backend.services.viewpoint_analyzer.ViewpointAnalyzer.find_opposing_viewpoints') as mock_find:
            mock_find.return_value = [
                {
                    'article_id': 2,
                    'title': 'Framework Opposition Article',
                    'url': 'https://test.com/framework',
                    'source_name': 'Test Source',
                    'published_at': datetime.utcnow().isoformat(),
                    'relationship_type': 'framework_opposition',
                    'opposition_strength': 0.85,
                    'reasoning': 'Framework opposition on ethics',
                    'ai_explanation': 'Individual freedom vs collective safety tension',
                    'quality_score': 0.8,
                    'framework_name': 'Freedom vs Safety',
                    'primary_position': 8,
                    'opposing_position': -7
                }
            ]

            response = client.get(
                "/articles/1/opposing-viewpoints",
                headers=auth_headers
            )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        viewpoint = data['opposing_viewpoints'][0]

        assert viewpoint['framework_name'] == 'Freedom vs Safety'
        assert viewpoint['primary_position'] == 8
        assert viewpoint['opposing_position'] == -7
        assert viewpoint['quality_score'] == 0.8

    def test_get_opposing_viewpoints_empty_results(
        self, client, session, mock_article, auth_headers
    ):
        """Test response when no opposing viewpoints found"""
        with patch('backend.services.viewpoint_analyzer.ViewpointAnalyzer.find_opposing_viewpoints') as mock_find:
            mock_find.return_value = []

            response = client.get(
                "/articles/1/opposing-viewpoints",
                headers=auth_headers
            )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data['primary_article_id'] == 1
        assert data['total_found'] == 0
        assert len(data['opposing_viewpoints']) == 0
        assert data['relationship_types_available'] == ['framework_opposition']

    def test_get_opposing_viewpoints_filter_by_relationship_type(
        self, client, session, mock_article, auth_headers
    ):
        """Test filtering by specific relationship type"""
        with patch('backend.services.viewpoint_analyzer.ViewpointAnalyzer.find_opposing_viewpoints') as mock_find:
            mock_find.return_value = [
                {
                    'article_id': 2,
                    'title': 'Framework Article',
                    'relationship_type': 'framework_opposition',
                    'opposition_strength': 0.8
                }
            ]

            response = client.get(
                "/articles/1/opposing-viewpoints?relationship_types=framework_opposition",
                headers=auth_headers
            )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data['opposing_viewpoints']) == 1
        assert data['opposing_viewpoints'][0]['relationship_type'] == 'framework_opposition'

    def test_get_opposing_viewpoints_max_results_parameter(
        self, client, session, mock_article, auth_headers
    ):
        """Test max_results parameter functionality"""
        with patch('backend.services.viewpoint_analyzer.ViewpointAnalyzer.find_opposing_viewpoints') as mock_find:
            mock_find.return_value = [
                {'article_id': i, 'title': f'Article {i}'}
                for i in range(2, 7)  # 5 results
            ]

            response = client.get(
                "/articles/1/opposing-viewpoints?max_results=3",
                headers=auth_headers
            )

        # Verify service was called with correct max_results
        mock_find.assert_called_once()
        call_kwargs = mock_find.call_args.kwargs
        assert call_kwargs['max_results'] == 3

    def test_get_opposing_viewpoints_response_time_performance(
        self, client, session, mock_article, auth_headers
    ):
        """Test response time meets <20 second requirement"""
        with patch('backend.services.viewpoint_analyzer.ViewpointAnalyzer.find_opposing_viewpoints') as mock_find:
            # Simulate processing time (much faster than 20s)
            mock_find.return_value = [
                {
                    'article_id': 2,
                    'title': 'Fast Article',
                    'relationship_type': 'framework_opposition',
                    'opposition_strength': 0.8
                }
            ]

            import time
            start_time = time.time()

            response = client.get(
                "/articles/1/opposing-viewpoints",
                headers=auth_headers
            )

            response_time = time.time() - start_time

        # Should respond much faster than 20 seconds
        assert response.status_code == 200
        assert response_time < 2.0  # Well under 20 second requirement


class TestOpposingViewpointsAPIAuthentication:
    """Test authentication and authorization"""

    def test_get_opposing_viewpoints_unauthorized(self, client):
        """Test endpoint requires authentication"""
        response = client.get("/articles/1/opposing-viewpoints")

        assert response.status_code == 401
        data = response.json()
        assert data['detail'] == "Not authenticated"

    def test_get_opposing_viewpoints_invalid_token(self, client):
        """Test with invalid JWT token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/articles/1/opposing-viewpoints", headers=headers)

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_get_opposing_viewpoints_expired_token(self, client):
        """Test with expired JWT token"""
        # Create an expired token (in practice, this would be created with an old exp time)
        expired_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0QGV4YW1wbGUuY29tIiwiZXhwIjoxNjAwMDAwMDAwfQ.invalid"
        headers = {"Authorization": f"Bearer {expired_token}"}

        response = client.get("/articles/1/opposing-viewpoints", headers=headers)

        assert response.status_code == 401

    def test_get_opposing_viewpoints_valid_token(self, client, auth_headers):
        """Test with valid JWT token"""
        # Mock ViewpointAnalyzer to avoid database dependencies
        with patch('backend.services.viewpoint_analyzer.ViewpointAnalyzer.find_opposing_viewpoints') as mock_find:
            mock_find.return_value = []

            response = client.get(
                "/articles/1/opposing-viewpoints",
                headers=auth_headers
            )

        # Should pass authentication
        assert response.status_code == 200


class TestOpposingViewpointsAPIInputValidation:
    """Test input validation and edge cases"""

    def test_get_opposing_viewpoints_invalid_article_id(
        self, client, auth_headers
    ):
        """Test with non-existent article ID"""
        with patch('backend.services.viewpoint_analyzer.ViewpointAnalyzer.find_opposing_viewpoints') as mock_find:
            mock_find.return_value = []  # Service handles non-existent gracefully

            response = client.get(
                "/articles/999/opposing-viewpoints",
                headers=auth_headers
            )

        # Should handle gracefully (service returns empty list)
        assert response.status_code == 200
        data = response.json()
        assert data['total_found'] == 0

    def test_get_opposing_viewpoints_negative_article_id(
        self, client, auth_headers
    ):
        """Test with negative article ID"""
        with patch('backend.services.viewpoint_analyzer.ViewpointAnalyzer.find_opposing_viewpoints') as mock_find:
            mock_find.return_value = []

            response = client.get(
                "/articles/-1/opposing-viewpoints",
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert data['total_found'] == 0

    def test_get_opposing_viewpoints_zero_article_id(
        self, client, auth_headers
    ):
        """Test with zero article ID"""
        with patch('backend.services.viewpoint_analyzer.ViewpointAnalyzer.find_opposing_viewpoints') as mock_find:
            mock_find.return_value = []

            response = client.get(
                "/articles/0/opposing-viewpoints",
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert data['total_found'] == 0

    def test_get_opposing_viewpoints_invalid_max_results(
        self, client, auth_headers
    ):
        """Test with invalid max_results values"""
        test_cases = [
            ("-1", "negative"),
            ("0", "zero"),
            ("1001", "excessive"),
            ("abc", "non-numeric")
        ]

        for max_results, description in test_cases:
            with patch('backend.services.viewpoint_analyzer.ViewpointAnalyzer.find_opposing_viewpoints') as mock_find:
                mock_find.return_value = []

                response = client.get(
                    f"/articles/1/opposing-viewpoints?max_results={max_results}",
                    headers=auth_headers
                )

                # Should handle gracefully or validate input
                assert response.status_code in [200, 422]

    def test_get_opposing_viewpoints_invalid_relationship_types(
        self, client, auth_headers
    ):
        """Test with invalid relationship type parameters"""
        invalid_types = [
            "invalid_type",
            "framework_opposition,sentiment_contrast,invalid",
            "",
            "null",
            "undefined"
        ]

        for rel_types in invalid_types:
            with patch('backend.services.viewpoint_analyzer.ViewpointAnalyzer.find_opposing_viewpoints') as mock_find:
                mock_find.return_value = []

                response = client.get(
                    f"/articles/1/opposing-viewpoints?relationship_types={rel_types}",
                    headers=auth_headers
                )

                # Should handle gracefully (filter to available types)
                assert response.status_code == 200


class TestOpposingViewpointsAPIResponseFormat:
    """Test response format validation"""

    def test_response_format_with_viewpoints(self, client, auth_headers):
        """Test response format when viewpoints are present"""
        with patch('backend.services.viewpoint_analyzer.ViewpointAnalyzer.find_opposing_viewpoints') as mock_find:
            mock_find.return_value = [
                {
                    'article_id': 2,
                    'title': 'Test Article',
                    'url': 'https://test.com',
                    'source_name': 'Test Source',
                    'source_bias': 'center',
                    'published_at': datetime.utcnow().isoformat(),
                    'sentiment_score': 1.5,
                    'political_lean': 'center',
                    'summary': 'Test summary',
                    'relationship_type': 'framework_opposition',
                    'opposition_strength': 0.8,
                    'reasoning': 'Test reasoning',
                    'ai_explanation': 'AI explanation',
                    'quality_score': 0.7,
                    'framework_name': 'Test Framework',
                    'primary_position': 5,
                    'opposing_position': -5
                }
            ]

            response = client.get(
                "/articles/1/opposing-viewpoints",
                headers=auth_headers
            )

        # Validate response structure
        assert response.status_code == 200
        data = response.json()

        # Root level fields
        required_fields = ['primary_article_id', 'opposing_viewpoints', 'total_found', 'relationship_types_available']
        for field in required_fields:
            assert field in data, f"Missing field: {field}"

        # Viewpoint fields
        viewpoint = data['opposing_viewpoints'][0]
        viewpoint_fields = [
            'article_id', 'title', 'url', 'source_name', 'published_at',
            'relationship_type', 'opposition_strength', 'reasoning'
        ]
        for field in viewpoint_fields:
            assert field in viewpoint, f"Missing viewpoint field: {field}"

    def test_response_format_empty_results(self, client, auth_headers):
        """Test response format when no viewpoints found"""
        with patch('backend.services.viewpoint_analyzer.ViewpointAnalyzer.find_opposing_viewpoints') as mock_find:
            mock_find.return_value = []

            response = client.get(
                "/articles/1/opposing-viewpoints",
                headers=auth_headers
            )

        # Validate empty response structure
        assert response.status_code == 200
        data = response.json()

        assert data['primary_article_id'] == 1
        assert data['total_found'] == 0
        assert len(data['opposing_viewpoints']) == 0
        assert data['relationship_types_available'] == ['framework_opposition']

    def test_response_format_framework_details(self, client, auth_headers):
        """Test framework-specific fields in response"""
        with patch('backend.services.viewpoint_analyzer.ViewpointAnalyzer.find_opposing_viewpoints') as mock_find:
            mock_find.return_value = [
                {
                    'article_id': 2,
                    'title': 'Framework Article',
                    'relationship_type': 'framework_opposition',
                    'framework_name': 'Ethics Framework',
                    'primary_position': 8,
                    'opposing_position': -7,
                    'quality_score': 0.9
                }
            ]

            response = client.get(
                "/articles/1/opposing-viewpoints",
                headers=auth_headers
            )

        # Validate framework-specific fields
        assert response.status_code == 200
        data = response.json()
        viewpoint = data['opposing_viewpoints'][0]

        assert viewpoint['framework_name'] == 'Ethics Framework'
        assert viewpoint['primary_position'] == 8
        assert viewpoint['opposing_position'] == -7
        assert viewpoint['quality_score'] == 0.9

    def test_response_format_error_responses(self, client, auth_headers):
        """Test error response formats"""
        # Test 401 error format
        response = client.get("/articles/1/opposing-viewpoints")
        assert response.status_code == 401
        data = response.json()
        assert 'detail' in data

        # Test 422 error format (if validation fails)
        response = client.get(
            "/articles/1/opposing-viewpoints?max_results=invalid",
            headers=auth_headers
        )
        if response.status_code == 422:
            data = response.json()
            assert 'detail' in data


class TestOpposingViewpointsAPIErrorHandling:
    """Test error handling and edge cases"""

    @patch('backend.services.viewpoint_analyzer.openai_client')
    def test_api_openai_unavailable_error(self, mock_openai_client, client, auth_headers):
        """Test handling when OpenAI API is unavailable"""
        mock_openai_client.is_available.return_value = False

        response = client.get(
            "/articles/1/opposing-viewpoints",
            headers=auth_headers
        )

        # Should return 503 with appropriate message
        assert response.status_code == 503
        data = response.json()
        assert "OpenAI API is unavailable" in data['detail']

    @patch('backend.services.viewpoint_analyzer.ViewpointAnalyzer')
    def test_api_rate_limit_error(self, mock_analyzer, client, auth_headers):
        """Test handling when OpenAI rate limit is hit"""
        # Simulate rate limit error
        mock_analyzer.find_opposing_viewpoints.side_effect = Exception("rate limit")

        response = client.get(
            "/articles/1/opposing-viewpoints",
            headers=auth_headers
        )

        # Should return 429 with appropriate message
        assert response.status_code == 429
        data = response.json()
        assert "rate limited" in data['detail']

    @patch('backend.services.viewpoint_analyzer.ViewpointAnalyzer')
    def test_api_database_error(self, mock_analyzer, client, auth_headers):
        """Test handling database errors"""
        # Simulate database error
        mock_analyzer.find_opposing_viewpoints.side_effect = Exception("Database connection failed")

        response = client.get(
            "/articles/1/opposing-viewpoints",
            headers=auth_headers
        )

        # Should return 500 with generic error message
        assert response.status_code == 500
        data = response.json()
        assert "Internal server error" in data['detail']

    @patch('backend.services.viewpoint_analyzer.ViewpointAnalyzer')
    def test_api_internal_server_error(self, mock_analyzer, client, auth_headers):
        """Test handling unexpected internal errors"""
        # Simulate unexpected error
        mock_analyzer.find_opposing_viewpoints.side_effect = Exception("Unexpected error")

        response = client.get(
            "/articles/1/opposing-viewpoints",
            headers=auth_headers
        )

        # Should return 500
        assert response.status_code == 500
        data = response.json()
        assert "Internal server error" in data['detail']

    def test_article_not_found_error(self, client, auth_headers):
        """Test when article doesn't exist in database"""
        # Mock session to return None for article
        with patch('backend.database.get_session') as mock_get_session:
            mock_session = MagicMock()
            mock_session.exec.return_value.first.return_value = None
            mock_get_session.return_value = mock_session

            response = client.get(
                "/articles/999/opposing-viewpoints",
                headers=auth_headers
            )

        # Should return 404 for non-existent article
        assert response.status_code == 404
        data = response.json()
        assert data['detail'] == "Article not found"


class TestOpposingViewpointsAPIPerformance:
    """Test performance and load scenarios"""

    def test_endpoint_response_time_under_20_seconds(
        self, client, session, mock_article, auth_headers
    ):
        """Test response time meets <20 second requirement"""
        with patch('backend.services.viewpoint_analyzer.ViewpointAnalyzer.find_opposing_viewpoints') as mock_find:
            # Simulate a longer processing time (but still under 20s)
            def slow_processing(*args, **kwargs):
                import time
                time.sleep(0.1)  # 100ms processing
                return []

            mock_find.side_effect = slow_processing

            import time
            start_time = time.time()

            response = client.get(
                "/articles/1/opposing-viewpoints",
                headers=auth_headers
            )

            response_time = time.time() - start_time

        # Should respond well under 20 seconds
        assert response.status_code == 200
        assert response_time < 5.0  # Should be much faster than 20s

    def test_endpoint_concurrent_requests(
        self, client, session, mock_article, auth_headers
    ):
        """Test handling of concurrent requests"""
        import threading
        import time
        import concurrent.futures

        with patch('backend.services.viewpoint_analyzer.ViewpointAnalyzer.find_opposing_viewpoints') as mock_find:
            mock_find.return_value = [
                {'article_id': 2, 'title': f'Article {i}'}
                for i in range(5)
            ]

            def make_request():
                start_time = time.time()
                response = client.get(
                    "/articles/1/opposing-viewpoints",
                    headers=auth_headers
                )
                return {
                    'status_code': response.status_code,
                    'response_time': time.time() - start_time
                }

            # Make 10 concurrent requests
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(make_request) for _ in range(10)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # All requests should succeed
        assert len(results) == 10
        assert all(r['status_code'] == 200 for r in results)

        # Response times should be reasonable
        response_times = [r['response_time'] for r in results]
        assert max(response_times) < 2.0  # No request should take more than 2 seconds
        assert sum(response_times) / len(response_times) < 1.0  # Average under 1 second

    def test_endpoint_large_result_set_handling(
        self, client, session, mock_article, auth_headers
    ):
        """Test handling of large result sets"""
        with patch('backend.services.viewpoint_analyzer.ViewpointAnalyzer.find_opposing_viewpoints') as mock_find:
            # Simulate large result set (50 viewpoints)
            large_result_set = [
                {
                    'article_id': i,
                    'title': f'Article {i}',
                    'url': f'https://test.com/article{i}',
                    'source_name': f'Source {i}',
                    'published_at': datetime.utcnow().isoformat(),
                    'relationship_type': 'framework_opposition',
                    'opposition_strength': 0.5 + (i % 50) / 100,
                    'reasoning': f'Reasoning {i}'
                }
                for i in range(2, 52)  # 50 viewpoints
            ]
            mock_find.return_value = large_result_set

            response = client.get(
                "/articles/1/opposing-viewpoints?max_results=100",
                headers=auth_headers
            )

        # Should handle large result set
        assert response.status_code == 200
        data = response.json()
        assert data['total_found'] == 50
        assert len(data['opposing_viewpoints']) == 50

        # Verify response size is reasonable (not too large)
        response_content_length = len(response.content)
        assert response_content_length < 100000  # Less than 100KB

    def test_endpoint_memory_efficiency(
        self, client, session, mock_article, auth_headers
    ):
        """Test endpoint doesn't consume excessive memory"""
        import psutil
        import os

        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        with patch('backend.services.viewpoint_analyzer.ViewpointAnalyzer.find_opposing_viewpoints') as mock_find:
            # Simulate large but efficient response
            mock_find.return_value = [
                {
                    'article_id': i,
                    'title': f'Memory Test Article {i}',
                    'url': f'https://test.com/memory{i}',
                    'source_name': f'Memory Source {i}',
                    'published_at': datetime.utcnow().isoformat(),
                    'relationship_type': 'framework_opposition',
                    'opposition_strength': 0.8,
                    'reasoning': f'Memory test reasoning {i}'
                }
                for i in range(100)  # 100 viewpoints
            ]

            response = client.get(
                "/articles/1/opposing-viewpoints",
                headers=auth_headers
            )

        # Check memory usage didn't grow excessively (< 50MB)
        final_memory = process.memory_info().rss
        memory_growth = (final_memory - initial_memory) / (1024 * 1024)  # Convert to MB

        assert response.status_code == 200
        assert memory_growth < 50  # Less than 50MB memory growth


if __name__ == "__main__":
    pytest.main([__file__, "-v"])