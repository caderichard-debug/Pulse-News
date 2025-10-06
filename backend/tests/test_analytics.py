"""
Tests for analytics endpoints.
Run with: pytest backend/tests/test_analytics.py -v
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool
from .main import app
from .database import get_session
from .models import (
    User, Source, Article, ArticleAnalysis, Topic, UserTopicPreference,
    Framework, ArticleFrameworkLink, PoliticalLean
)
from .utils.auth import hash_password
from datetime import datetime, timedelta


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        # Create user
        user = User(
            id=1,
            email="testuser@example.com",
            hashed_password=hash_password("testpass123"),
            email_verified=True,
            is_active=True
        )
        session.add(user)

        # Create source
        source = Source(
            id=1,
            name="Test Source",
            url="https://test.com",
            rss_feed_url="https://test.com/rss",
            trust_score=0.9
        )
        session.add(source)

        # Create topics
        politics = Topic(id=1, name="Politics", description="Political news")
        tech = Topic(id=2, name="Technology", description="Tech news")
        session.add_all([politics, tech])

        # Create user topic preferences
        pref = UserTopicPreference(
            user_id=1,
            topic_id=1,
            priority_level=5,
            include_in_newsletter=True
        )
        session.add(pref)

        # Create frameworks
        framework1 = Framework(
            id=1,
            name="Liberty vs Welfare",
            description="Individual liberty vs collective welfare",
            axis_description="Left: Liberty | Right: Welfare",
            left_position="Individual freedom",
            right_position="Community benefit",
            article_count=10
        )
        framework2 = Framework(
            id=2,
            name="Regulation vs Market",
            description="Government regulation vs free market",
            axis_description="Left: Regulation | Right: Market",
            left_position="More regulation",
            right_position="Free market",
            article_count=8
        )
        session.add_all([framework1, framework2])

        # Create articles with different dates and sentiments
        for i in range(10):
            days_ago = i
            article = Article(
                id=i + 1,
                source_id=1,
                title=f"Article {i+1}",
                url=f"https://test.com/article-{i+1}",
                published_at=datetime.utcnow() - timedelta(days=days_ago),
                topic_category="Politics" if i % 2 == 0 else "Technology",
                processing_status="completed"
            )
            session.add(article)

            # Varying sentiments
            sentiment = (i % 11) - 5  # Range from -5 to +5
            lean = PoliticalLean.LEFT if i < 3 else (PoliticalLean.RIGHT if i > 6 else PoliticalLean.CENTER)

            analysis = ArticleAnalysis(
                article_id=i + 1,
                summary=f"Summary for article {i+1}",
                sentiment_score=sentiment,
                political_lean=lean
            )
            session.add(analysis)

            # Add framework links for some articles
            if i < 5:
                link1 = ArticleFrameworkLink(
                    article_id=i + 1,
                    framework_id=1,
                    relevance_score=0.8,
                    position_on_axis=(i - 2) * 2,  # Range from -4 to +4
                    ai_explanation="Test explanation"
                )
                link2 = ArticleFrameworkLink(
                    article_id=i + 1,
                    framework_id=2,
                    relevance_score=0.7,
                    position_on_axis=(i - 2) * -2,  # Inverse for variety
                    ai_explanation="Test explanation"
                )
                session.add_all([link1, link2])

        session.commit()
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="auth_token")
def auth_token_fixture(client: TestClient):
    """Get authentication token for test user"""
    response = client.post(
        "/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "testpass123"
        }
    )
    return response.json()["access_token"]


class TestAnalyticsEndpoints:
    """Tests for analytics API endpoints"""

    def test_get_user_stats(self, client: TestClient, auth_token: str):
        """Test GET /analytics/user-stats"""
        response = client.get(
            "/analytics/user-stats",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert "articles_read" in data
        assert "newsletters_received" in data
        assert "topics_tracked" in data
        assert "sources_subscribed" in data
        assert "views_changed" in data

        # Should have 1 topic tracked
        assert data["topics_tracked"] == 1

    def test_get_sentiment_over_time(self, client: TestClient, auth_token: str):
        """Test GET /analytics/sentiment-over-time"""
        response = client.get(
            "/analytics/sentiment-over-time?days=30",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        if len(data) > 0:
            assert "date" in data[0]
            assert "values" in data[0]
            assert isinstance(data[0]["values"], dict)

    def test_get_bias_distribution(self, client: TestClient, auth_token: str):
        """Test GET /analytics/bias-distribution"""
        response = client.get(
            "/analytics/bias-distribution?weeks=4",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        if len(data) > 0:
            item = data[0]
            assert "week" in item
            assert "left" in item
            assert "center" in item
            assert "right" in item

            # Percentages should sum to ~100
            total = item["left"] + item["center"] + item["right"]
            assert 99 <= total <= 101  # Allow for rounding

    def test_get_framework_heatmap(self, client: TestClient, auth_token: str):
        """Test GET /analytics/framework-heatmap"""
        response = client.get(
            "/analytics/framework-heatmap?framework1_id=1&framework2_id=2&days=30",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        if len(data) > 0:
            cell = data[0]
            assert "x" in cell
            assert "y" in cell
            assert "article_count" in cell
            assert "avg_sentiment" in cell
            assert "sample_articles" in cell

            assert isinstance(cell["sample_articles"], list)
            if len(cell["sample_articles"]) > 0:
                article = cell["sample_articles"][0]
                assert "id" in article
                assert "title" in article

    def test_get_available_frameworks(self, client: TestClient, auth_token: str):
        """Test GET /analytics/frameworks/available"""
        response = client.get(
            "/analytics/frameworks/available",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) == 2  # We created 2 frameworks

        framework = data[0]
        assert "id" in framework
        assert "name" in framework
        assert "left_position" in framework
        assert "right_position" in framework

    def test_sentiment_over_time_with_topic_filter(self, client: TestClient, auth_token: str):
        """Test sentiment filtering by specific topics"""
        response = client.get(
            "/analytics/sentiment-over-time?days=30&topic_ids=1",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Should only include Politics topic
        if len(data) > 0 and len(data[0]["values"]) > 0:
            assert "Politics" in str(data[0]["values"])

    def test_analytics_require_auth(self, client: TestClient):
        """Test that all analytics endpoints require authentication"""
        endpoints = [
            "/analytics/user-stats",
            "/analytics/sentiment-over-time",
            "/analytics/bias-distribution",
            "/analytics/framework-heatmap?framework1_id=1&framework2_id=2",
            "/analytics/frameworks/available"
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 403, f"Endpoint {endpoint} should require auth"

    def test_framework_heatmap_missing_params(self, client: TestClient, auth_token: str):
        """Test that framework heatmap requires both framework IDs"""
        # Missing framework2_id
        response = client.get(
            "/analytics/framework-heatmap?framework1_id=1",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 422  # Validation error

    def test_sentiment_time_range_validation(self, client: TestClient, auth_token: str):
        """Test that time range is validated"""
        # Days too high
        response = client.get(
            "/analytics/sentiment-over-time?days=100",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 422

        # Days too low
        response = client.get(
            "/analytics/sentiment-over-time?days=0",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 422

    def test_bias_distribution_weeks_validation(self, client: TestClient, auth_token: str):
        """Test that weeks parameter is validated"""
        # Weeks too high
        response = client.get(
            "/analytics/bias-distribution?weeks=20",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 422

        # Valid weeks
        response = client.get(
            "/analytics/bias-distribution?weeks=8",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
