"""
Tests for article detail endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool
from datetime import datetime
from .main import app
from .models import (
    User, Article, ArticleAnalysis, Source,
    Framework, ArticleFrameworkLink, StatisticVerification,
    ArticleCluster, ArticleClusterMember, ArticleContext, PoliticalLean
)
from .database import get_session
from .utils.auth import create_access_token, hash_password


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
def test_article(session: Session):
    """Create test article with full analysis data."""
    # Create source
    source = Source(name="Reuters", url="https://reuters.com", rss_feed_url="https://reuters.com/rss")
    session.add(source)
    session.commit()
    session.refresh(source)

    # Create article
    article = Article(
        title="Test Article",
        url="https://example.com/article",
        source_id=source.id,
        topic_category="Politics",
        published_at=datetime.utcnow(),
        processing_status="completed",
        content_text="This is test content for the article."
    )
    session.add(article)
    session.commit()
    session.refresh(article)

    # Add analysis
    analysis = ArticleAnalysis(
        article_id=article.id,
        summary="This is a test summary of the article.",
        sentiment_score=5.0,
        political_lean=PoliticalLean.CENTER,
    )
    session.add(analysis)
    session.commit()

    # Add framework
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

    # Add framework link
    link = ArticleFrameworkLink(
        article_id=article.id,
        framework_id=framework.id,
        position_on_axis=7,
        relevance_score=0.9,
        ai_explanation="This article leans toward collective welfare."
    )
    session.add(link)
    session.commit()

    # Add statistics
    from .models import VerificationStatus
    stat = StatisticVerification(
        article_id=article.id,
        statistic_text="50% of Americans support this policy",
        verification_status=VerificationStatus.VERIFIED,
        confidence_score=0.85,
        source_name="Pew Research",
        source_url="https://pewresearch.org",
        source_credibility_score=0.9
    )
    session.add(stat)
    session.commit()

    # Add context
    context = ArticleContext(
        article_id=article.id,
        background="This is background information.",
        key_players="John Doe, Jane Smith",
        timeline="Started in 2020, ongoing",
        significance="Important for policy decisions"
    )
    session.add(context)
    session.commit()

    # Create related article in same cluster
    cluster = ArticleCluster(
        cluster_hash="test-cluster-hash-123",
        primary_topic="Politics"
    )
    session.add(cluster)
    session.commit()
    session.refresh(cluster)

    # Add original article to cluster
    member1 = ArticleClusterMember(
        cluster_id=cluster.id,
        article_id=article.id,
        similarity_score=1.0
    )
    session.add(member1)

    # Create related article
    related_article = Article(
        title="Related Article",
        url="https://example.com/related",
        source_id=source.id,
        topic_category="Politics",
        published_at=datetime.utcnow(),
        processing_status="completed",
        content_text="Related content"
    )
    session.add(related_article)
    session.commit()
    session.refresh(related_article)

    # Add related article analysis
    related_analysis = ArticleAnalysis(
        article_id=related_article.id,
        summary="Related summary",
        sentiment_score=-2.0,
        political_lean=PoliticalLean.LEFT
    )
    session.add(related_analysis)

    # Add related article to cluster
    member2 = ArticleClusterMember(
        cluster_id=cluster.id,
        article_id=related_article.id,
        similarity_score=0.85
    )
    session.add(member2)
    session.commit()

    return {
        "article": article,
        "source": source,
        "framework": framework,
        "related_article": related_article
    }


class TestArticleDetailEndpoints:
    """Test article detail endpoints."""

    def test_get_article_detail(self, client, auth_token, test_article):
        """Test getting article detail with all data."""
        article_id = test_article["article"].id
        response = client.get(
            f"/articles/{article_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()

        # Check basic article data
        assert data["id"] == article_id
        assert data["title"] == "Test Article"
        assert data["source_name"] == "Reuters"
        assert data["topic_category"] == "Politics"

        # Check analysis
        assert data["summary"] == "This is a test summary of the article."
        assert data["sentiment_score"] == 5.0
        assert data["political_lean"] == "center"

    def test_article_detail_requires_auth(self, client, test_article):
        """Test that article detail requires authentication."""
        article_id = test_article["article"].id
        response = client.get(f"/articles/{article_id}")
        # FastAPI returns 403 when auth dependency fails
        assert response.status_code == 403

    def test_article_detail_includes_statistics(self, client, auth_token, test_article):
        """Test that article detail includes verified statistics."""
        article_id = test_article["article"].id
        response = client.get(
            f"/articles/{article_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()

        assert "statistics" in data
        assert len(data["statistics"]) == 1
        stat = data["statistics"][0]
        assert stat["statistic"] == "50% of Americans support this policy"
        assert stat["verification_status"] == "verified"
        assert stat["confidence"] == 0.85
        assert stat["source_name"] == "Pew Research"
        assert stat["source_url"] == "https://pewresearch.org"
        assert stat["source_credibility_score"] == 0.9

    def test_article_detail_includes_frameworks(self, client, auth_token, test_article):
        """Test that article detail includes framework positioning."""
        article_id = test_article["article"].id
        response = client.get(
            f"/articles/{article_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()

        assert "frameworks" in data
        assert len(data["frameworks"]) == 1
        fw = data["frameworks"][0]
        assert fw["framework_name"] == "Individual Liberty vs Collective Welfare"
        assert fw["position_on_axis"] == 7
        assert fw["relevance_score"] == 0.9
        assert fw["explanation"] == "This article leans toward collective welfare."
        assert fw["left_position"] == "Individual Liberty"
        assert fw["right_position"] == "Collective Welfare"

    def test_article_detail_includes_context(self, client, auth_token, test_article):
        """Test that article detail includes context information."""
        article_id = test_article["article"].id
        response = client.get(
            f"/articles/{article_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()

        assert "context" in data
        assert data["context"] is not None
        context = data["context"]
        assert context["background"] == "This is background information."
        assert context["key_players"] == "John Doe, Jane Smith"
        assert context["timeline"] == "Started in 2020, ongoing"
        assert context["significance"] == "Important for policy decisions"

    def test_article_detail_includes_related_articles(self, client, auth_token, test_article):
        """Test that article detail includes related articles from same cluster."""
        article_id = test_article["article"].id
        response = client.get(
            f"/articles/{article_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()

        assert "related_articles" in data
        assert len(data["related_articles"]) == 1
        related = data["related_articles"][0]
        assert related["title"] == "Related Article"
        assert related["source_name"] == "Reuters"
        assert related["sentiment_score"] == -2.0
        assert related["political_lean"] == "left"

    def test_article_not_found(self, client, auth_token):
        """Test getting non-existent article returns 404."""
        response = client.get(
            "/articles/99999",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 404

    def test_article_without_analysis(self, client, auth_token, session: Session):
        """Test article detail when analysis is missing."""
        # Create article without analysis
        source = Source(name="Test Source", url="https://test.com", rss_feed_url="https://test.com/rss")
        session.add(source)
        session.commit()
        session.refresh(source)

        article = Article(
            title="No Analysis Article",
            url="https://example.com/no-analysis",
            source_id=source.id,
            processing_status="pending",
            published_at=datetime.utcnow()
        )
        session.add(article)
        session.commit()
        session.refresh(article)

        response = client.get(
            f"/articles/{article.id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["summary"] is None
        assert data["sentiment_score"] is None
        assert data["political_lean"] is None

    def test_article_without_context(self, client, auth_token, session: Session):
        """Test article detail when context is missing."""
        # Create minimal article
        source = Source(name="Test Source", url="https://test.com", rss_feed_url="https://test.com/rss")
        session.add(source)
        session.commit()
        session.refresh(source)

        article = Article(
            title="No Context Article",
            url="https://example.com/no-context",
            source_id=source.id,
            processing_status="completed",
            published_at=datetime.utcnow()
        )
        session.add(article)
        session.commit()
        session.refresh(article)

        response = client.get(
            f"/articles/{article.id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["context"] is None
        assert data["statistics"] == []
        assert data["frameworks"] == []
        assert data["related_articles"] == []
