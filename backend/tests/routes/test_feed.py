"""
Tests for feed endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel, select
from sqlmodel.pool import StaticPool
from datetime import datetime, timedelta
from app.main import app
from app.models import (
    User, Article, ArticleAnalysis, Source, Topic,
    Framework, ArticleFrameworkLink, PoliticalLean, ProcessingStatus
)
from app.database import get_session
from app.utils.auth import create_access_token, hash_password


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_token(session: Session):
    """Create test user and return auth token."""
    user = User(
        email="test@example.com",
        hashed_password=hash_password("password"),
        full_name="Test User"
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    token = create_access_token(data={"sub": user.email})
    return token


@pytest.fixture
def test_data(session: Session):
    """Create test articles with analysis."""
    # Create source
    source1 = Source(name="Reuters", url="https://reuters.com", rss_feed_url="https://reuters.com/rss")
    source2 = Source(name="BBC", url="https://bbc.com", rss_feed_url="https://bbc.com/rss")
    session.add(source1)
    session.add(source2)
    session.commit()
    session.refresh(source1)
    session.refresh(source2)

    # Create framework
    framework = Framework(
        name="Individual Liberty vs Collective Welfare",
        left_position="Individual Liberty",
        right_position="Collective Welfare",
        description="Test framework",
        axis_description="Individual freedom ↔ collective welfare"
    )
    session.add(framework)
    session.commit()
    session.refresh(framework)

    # Create articles (3 with analysis, 1 without)
    articles_data = [
        {
            "title": "Article 1",
            "url": "https://example.com/1",
            "source_id": source1.id,
            "topic_category": "Politics",
            "published_at": datetime.utcnow() - timedelta(hours=1),
            "processing_status": ProcessingStatus.COMPLETED,
            "sentiment": 5.0,
            "lean": PoliticalLean.LEFT,
            "has_analysis": True
        },
        {
            "title": "Article 2",
            "url": "https://example.com/2",
            "source_id": source2.id,
            "topic_category": "Technology",
            "published_at": datetime.utcnow() - timedelta(hours=2),
            "processing_status": ProcessingStatus.COMPLETED,
            "sentiment": -3.0,
            "lean": PoliticalLean.RIGHT,
            "has_analysis": True
        },
        {
            "title": "Article 3",
            "url": "https://example.com/3",
            "source_id": source1.id,
            "topic_category": "Politics",
            "published_at": datetime.utcnow() - timedelta(hours=3),
            "processing_status": ProcessingStatus.COMPLETED,
            "sentiment": 0.0,
            "lean": PoliticalLean.CENTER,
            "has_analysis": True
        },
        {
            "title": "Article 4 - No Analysis",
            "url": "https://example.com/4",
            "source_id": source1.id,
            "topic_category": "Politics",
            "published_at": datetime.utcnow() - timedelta(hours=4),
            "processing_status": ProcessingStatus.COMPLETED,
            "has_analysis": False
        },
    ]

    for article_data in articles_data:
        article = Article(
            title=article_data["title"],
            url=article_data["url"],
            source_id=article_data["source_id"],
            topic_category=article_data["topic_category"],
            published_at=article_data["published_at"],
            processing_status=article_data["processing_status"],
            content="Test content"
        )
        session.add(article)
        session.commit()
        session.refresh(article)

        # Add analysis only if specified
        if article_data["has_analysis"]:
            analysis = ArticleAnalysis(
                article_id=article.id,
                summary="Test summary",
                sentiment_score=article_data["sentiment"],
                political_lean=article_data["lean"],
            )
            session.add(analysis)

            # Add framework link
            link = ArticleFrameworkLink(
                article_id=article.id,
                framework_id=framework.id,
                position_on_axis=3,
                relevance_score=0.8,
                ai_explanation="Test explanation"
            )
            session.add(link)

    session.commit()

    return {"source1": source1, "source2": source2, "framework": framework}


class TestFeedEndpoints:
    """Test feed article browsing endpoints."""

    def test_get_feed_articles(self, client, auth_token, test_data):
        """Test getting feed articles."""
        response = client.get(
            "/feed/articles",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "articles" in data
        assert "total_count" in data
        assert data["total_count"] == 4  # Now includes article without analysis
        assert len(data["articles"]) == 4

    def test_feed_allows_unauthenticated_access(self, client, test_data):
        """Test that feed endpoints allow unauthenticated access."""
        response = client.get("/feed/articles")
        assert response.status_code == 200
        data = response.json()
        assert "articles" in data
        assert "total_count" in data

    def test_feed_filter_by_topic(self, client, auth_token, test_data):
        """Test filtering articles by topic."""
        response = client.get(
            "/feed/articles?topic=Politics",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 3  # 2 with analysis + 1 without
        for article in data["articles"]:
            assert article["topic_category"] == "Politics"

    def test_feed_filter_by_source(self, client, auth_token, test_data):
        """Test filtering articles by source."""
        source_id = test_data["source1"].id
        response = client.get(
            f"/feed/articles?source_id={source_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 3  # 2 with analysis + 1 without
        for article in data["articles"]:
            assert article["source_id"] == source_id

    def test_feed_filter_by_political_lean(self, client, auth_token, test_data):
        """Test filtering articles by political lean."""
        response = client.get(
            "/feed/articles?political_lean=left",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert data["articles"][0]["political_lean"] == "left"

    def test_feed_sort_by_newest(self, client, auth_token, test_data):
        """Test sorting articles by newest first."""
        response = client.get(
            "/feed/articles?sort_by=newest",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # Check that articles are in descending order by published_at
        dates = [article["published_at"] for article in data["articles"]]
        assert dates == sorted(dates, reverse=True)

    def test_feed_sort_by_sentiment_high(self, client, auth_token, test_data):
        """Test sorting articles by highest sentiment."""
        response = client.get(
            "/feed/articles?sort_by=sentiment_high&only_analyzed=true",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        sentiments = [article["sentiment_score"] for article in data["articles"]]
        assert sentiments == sorted(sentiments, reverse=True)

    def test_feed_pagination(self, client, auth_token, test_data):
        """Test pagination of feed articles."""
        response = client.get(
            "/feed/articles?page=1&page_size=2",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert len(data["articles"]) == 2
        assert data["total_count"] == 4  # Now includes article without analysis

    def test_get_available_topics(self, client, auth_token, test_data):
        """Test getting available topics."""
        response = client.get(
            "/feed/topics",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        topic_names = [topic["name"] for topic in data]
        assert "Politics" in topic_names
        assert "Technology" in topic_names

    def test_get_available_sources(self, client, auth_token, test_data):
        """Test getting available sources."""
        response = client.get(
            "/feed/sources",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        source_names = [source["name"] for source in data]
        assert "Reuters" in source_names
        assert "BBC" in source_names

    def test_feed_includes_framework_data(self, client, auth_token, test_data):
        """Test that feed articles include framework positioning."""
        response = client.get(
            "/feed/articles",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        article = data["articles"][0]
        assert "primary_framework" in article
        assert "framework_position" in article
        assert article["primary_framework"] is not None

    def test_feed_filter_only_analyzed(self, client, auth_token, test_data):
        """Test filtering to show only articles with analysis."""
        # First, verify we have 4 total articles
        response = client.get(
            "/feed/articles",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 4

        # Now filter to only analyzed articles
        response = client.get(
            "/feed/articles?only_analyzed=true",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 3  # Only articles with analysis
        # Verify all returned articles have analysis data
        for article in data["articles"]:
            assert article["summary"] is not None
            assert article["sentiment_score"] is not None
            assert article["political_lean"] is not None
