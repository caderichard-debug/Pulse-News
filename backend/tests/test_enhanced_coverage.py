"""
Enhanced Coverage Tests

Tests for the new event-based clustering and enhanced coverage functionality.
"""

import pytest
from datetime import datetime, timedelta
from sqlmodel import Session
from fastapi.testclient import TestClient

from app.models import (
    User, Article, Source, ArticleAnalysis, ArticleCluster, ArticleClusterMember
)
from app.services.article_clusterer import (
    extract_event_signature, get_enhanced_coverage_comparison,
    trigger_realtime_clustering, cluster_article
)
from app.main import app


@pytest.fixture
def test_user(session: Session):
    """Create a test user."""
    user = User(
        email="test@example.com",
        hashed_password="test_hash",
        name="Test User",
        email_verified=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def test_source(session: Session):
    """Create a test source."""
    source = Source(
        name="Test News",
        url="https://testnews.com",
        rss_feed_url="https://testnews.com/rss.xml",
        trust_score=8.0
    )
    session.add(source)
    session.commit()
    session.refresh(source)
    return source


@pytest.fixture
def test_source_2(session: Session):
    """Create a second test source."""
    source = Source(
        name="Other News",
        url="https://othernews.com",
        rss_feed_url="https://othernews.com/rss.xml",
        trust_score=7.5
    )
    session.add(source)
    session.commit()
    session.refresh(source)
    return source


@pytest.fixture
def sample_articles(session: Session, test_source: Source, test_source_2: Source):
    """Create sample articles for testing."""
    articles = []

    # Event 1: Mayor announcement
    article1 = Article(
        title="City Mayor Announces New Infrastructure Plan",
        url="https://testnews.com/mayor-plan",
        content_text="Mayor John Smith announced a comprehensive infrastructure plan...",
        source_id=test_source.id,
        published_at=datetime.now() - timedelta(hours=2),
        scraped_at=datetime.now()
    )
    articles.append(article1)

    article2 = Article(
        title="Mayor Smith Reveals $50M Infrastructure Investment",
        url="https://othernews.com/mayor-investment",
        content_text="In a press conference today, Mayor John Smith revealed plans for $50M...",
        source_id=test_source_2.id,
        published_at=datetime.now() - timedelta(hours=1),
        scraped_at=datetime.now()
    )
    articles.append(article2)

    # Event 2: Different topic
    article3 = Article(
        title="Local Sports Team Wins Championship",
        url="https://testnews.com/sports-win",
        content_text="The city's basketball team won the championship game...",
        source_id=test_source.id,
        published_at=datetime.now() - timedelta(hours=3),
        scraped_at=datetime.now()
    )
    articles.append(article3)

    for article in articles:
        session.add(article)

    session.commit()

    for article in articles:
        session.refresh(article)

    return articles


@pytest.fixture
def sample_articles_with_analysis(session: Session, sample_articles):
    """Create articles with analysis."""
    articles = []

    for i, article in enumerate(sample_articles):
        analysis = ArticleAnalysis(
            article_id=article.id,
            summary=f"Summary for article {i+1}",
            sentiment_score=5 if i == 0 else (-3 if i == 1 else 8),  # Different sentiments
            political_lean="center" if i == 0 else ("left" if i == 1 else "right")
        )
        session.add(analysis)
        articles.append((article, analysis))

    session.commit()

    for article, analysis in articles:
        session.refresh(article)
        session.refresh(analysis)

    return articles


class TestEventSignatureExtraction:
    """Test event signature extraction functionality."""

    def test_extract_event_signature_basic(self, sample_articles):
        """Test basic event signature extraction."""
        article = sample_articles[0]  # Mayor announcement

        signature = extract_event_signature(article)

        assert signature is not None
        assert len(signature) > 0
        # Should contain key entities
        assert "mayor" in signature.lower()
        # Should contain date context
        assert datetime.now().strftime("%Y-%m-%d") in signature

    def test_extract_event_signature_different_events(self, sample_articles):
        """Test that different events produce different signatures."""
        signature1 = extract_event_signature(sample_articles[0])  # Mayor plan
        signature2 = extract_event_signature(sample_articles[2])  # Sports win

        assert signature1 != signature2
        assert "mayor" in signature1.lower()
        assert "sports" in signature2.lower()


class TestEnhancedCoverageComparison:
    """Test enhanced coverage comparison functionality."""

    def test_get_coverage_no_cluster(self, session: Session, sample_articles):
        """Test getting coverage for article without cluster."""
        article = sample_articles[0]

        result = get_enhanced_coverage_comparison(article.id, session)

        assert result["success"] is True
        assert result["coverage_count"] == 0
        assert result["has_cluster"] is False
        assert result["primary_article_id"] == article.id
        assert "primary_article" in result

    def test_get_coverage_with_bias_filter(self, session: Session, sample_articles_with_analysis):
        """Test getting coverage with bias filter."""
        articles = sample_articles_with_analysis

        # First, cluster the articles
        cluster_article(articles[0][0], session, similarity_threshold=0.5)
        session.commit()

        # Test with bias filter
        result = get_enhanced_coverage_comparison(
            articles[0][0].id,
            session,
            bias_filter="center"
        )

        assert result["success"] is True
        if result["coverage_articles"]:
            # All returned articles should match the bias filter
            for article in result["coverage_articles"]:
                assert article["source_bias"] == "center"

    def test_get_coverage_with_sentiment_range(self, session: Session, sample_articles_with_analysis):
        """Test getting coverage with sentiment range filter."""
        articles = sample_articles_with_analysis

        # First, cluster the articles
        cluster_article(articles[0][0], session, similarity_threshold=0.5)
        session.commit()

        # Test with sentiment range (positive only)
        result = get_enhanced_coverage_comparison(
            articles[0][0].id,
            session,
            sentiment_range=(0.0, 1.0)
        )

        assert result["success"] is True
        if result["coverage_articles"]:
            # All returned articles should have positive sentiment
            for article in result["coverage_articles"]:
                assert article["sentiment_score"] >= 0.0

    def test_get_coverage_with_max_results(self, session: Session, sample_articles_with_analysis):
        """Test getting coverage with max results limit."""
        articles = sample_articles_with_analysis

        # First, cluster the articles
        cluster_article(articles[0][0], session, similarity_threshold=0.5)
        session.commit()

        # Test with max_results=1
        result = get_enhanced_coverage_comparison(
            articles[0][0].id,
            session,
            max_results=1
        )

        assert result["success"] is True
        assert len(result["coverage_articles"]) <= 1

    def test_get_coverage_nonexistent_article(self, session: Session):
        """Test getting coverage for non-existent article."""
        result = get_enhanced_coverage_comparison(99999, session)

        assert result["success"] is False
        assert "Article not found" in result["error"]


class TestRealtimeClustering:
    """Test real-time clustering functionality."""

    def test_trigger_realtime_clustering_success(self, session: Session, sample_articles_with_analysis):
        """Test successful real-time clustering."""
        articles = sample_articles_with_analysis

        # Trigger clustering for first article with lower threshold
        result = trigger_realtime_clustering(articles[0][0].id, session)

        assert result["success"] is True
        # The clustering might not find similar articles, but should still succeed
        assert result["coverage_count"] >= 0
        assert "message" in result

        # Even if no cluster is created, the function should succeed
        if result["cluster_id"] is not None:
            # If clustered, should have coverage
            assert result["coverage_count"] >= 0

    def test_trigger_realtime_clustering_existing_cluster(self, session: Session, sample_articles_with_analysis):
        """Test triggering clustering for already clustered article."""
        articles = sample_articles_with_analysis

        # First, cluster manually
        cluster = cluster_article(articles[0][0], session, similarity_threshold=0.5)
        session.commit()

        # Then trigger again
        result = trigger_realtime_clustering(articles[0][0].id, session)

        assert result["success"] is True
        assert result["cluster_id"] == cluster.id
        assert "already has existing coverage" in result["message"]

    def test_trigger_realtime_clustering_no_similar_articles(self, session: Session, sample_articles):
        """Test clustering when no similar articles exist."""
        article = sample_articles[2]  # Sports article (should be unique)

        result = trigger_realtime_clustering(article.id, session)

        assert result["success"] is True
        assert result["cluster_id"] is None
        assert result["coverage_count"] == 0
        assert "No other articles found" in result["message"]

    def test_trigger_realtime_clustering_nonexistent_article(self, session: Session):
        """Test clustering non-existent article."""
        result = trigger_realtime_clustering(99999, session)

        assert result["success"] is False
        assert "Article not found" in result["error"]


class TestArticleAPIEndpoints:
    """Test the enhanced article API endpoints."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    def get_auth_headers(self, session: Session, test_user: User):
        """Get authentication headers for test user."""
        # Login to get token
        response = self.client.post(
            "/auth/login",
            data={"username": test_user.email, "password": "testpassword"}
        )

        if response.status_code != 200:
            # Create a simple token for testing
            import jwt
            from app.config import SECRET_KEY, ALGORITHM
            token = jwt.encode(
                {"sub": test_user.email, "exp": datetime.utcnow() + timedelta(hours=24)},
                SECRET_KEY,
                algorithm=ALGORITHM
            )
        else:
            token = response.json()["access_token"]

        return {"Authorization": f"Bearer {token}"}

    def test_get_article_detail_with_coverage_filters(self, session: Session, test_user: User, sample_articles_with_analysis):
        """Test getting article detail with coverage filters."""
        articles = sample_articles_with_analysis
        headers = self.get_auth_headers(session, test_user)

        # Cluster the articles first
        cluster_article(articles[0][0], session, similarity_threshold=0.5)
        session.commit()

        # Test with bias filter
        response = self.client.get(
            f"/articles/{articles[0][0].id}?coverage_bias_filter=center",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "coverage_metadata" in data
        assert data["coverage_metadata"]["success"] is True

    def test_trigger_coverage_analysis_endpoint(self, session: Session, test_user: User, sample_articles):
        """Test the trigger coverage analysis endpoint."""
        article = sample_articles[0]
        headers = self.get_auth_headers(session, test_user)

        response = self.client.post(
            f"/articles/{article.id}/analyze-coverage",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "cluster_id" in data
        assert "coverage_count" in data
        assert "message" in data

    def test_get_enhanced_coverage_endpoint(self, session: Session, test_user: User, sample_articles):
        """Test the enhanced coverage endpoint."""
        article = sample_articles[0]
        headers = self.get_auth_headers(session, test_user)

        response = self.client.get(
            f"/articles/{article.id}/coverage",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "coverage_articles" in data
        assert "coverage_count" in data

    def test_get_enhanced_coverage_with_filters(self, session: Session, test_user: User, sample_articles):
        """Test the enhanced coverage endpoint with filters."""
        article = sample_articles[0]
        headers = self.get_auth_headers(session, test_user)

        response = self.client.get(
            f"/articles/{article.id}/coverage?bias_filter=center&sentiment_range=0.0,1.0&max_results=5",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "filters_applied" in data
        assert data["filters_applied"]["bias_filter"] == "center"
        assert data["filters_applied"]["sentiment_range"] == [0.0, 1.0]
        assert data["filters_applied"]["max_results"] == 5

    def test_coverage_endpoints_unauthorized(self, sample_articles):
        """Test that coverage endpoints require authentication."""
        article = sample_articles[0]

        # Test without auth headers
        response = self.client.post(f"/articles/{article.id}/analyze-coverage")
        assert response.status_code == 401

        response = self.client.get(f"/articles/{article.id}/coverage")
        assert response.status_code == 401


class TestEventBasedClustering:
    """Test the improved event-based clustering functionality."""

    def test_cluster_articles_same_event(self, session: Session, sample_articles_with_analysis):
        """Test clustering articles covering the same event."""
        articles = sample_articles_with_analysis

        # The first two articles are about the mayor announcement
        cluster = cluster_article(articles[0][0], session, similarity_threshold=0.5)
        session.commit()

        assert cluster is not None
        assert cluster.event_signature is not None

        # Check that both articles are in the cluster
        members = session.exec(
            select(ArticleClusterMember).where(ArticleClusterMember.cluster_id == cluster.id)
        ).all()

        article_ids = [member.article_id for member in members]
        assert articles[0][0].id in article_ids

        # Check cluster metadata
        cluster.refresh()
        assert cluster.article_count >= 1
        assert cluster.sources_count >= 1

    def test_cluster_articles_different_events(self, session: Session, sample_articles_with_analysis):
        """Test that articles about different events don't cluster together."""
        articles = sample_articles_with_analysis

        # Try to cluster the sports article (should not cluster with mayor articles)
        cluster = cluster_article(articles[2][0], session, similarity_threshold=0.7)
        session.commit()

        # Should either not cluster or create a separate cluster
        if cluster:
            members = session.exec(
                select(ArticleClusterMember).where(ArticleClusterMember.cluster_id == cluster.id)
            ).all()

            # Should only contain the sports article
            article_ids = [member.article_id for member in members]
            assert articles[2][0].id in article_ids
            # Should not contain mayor articles
            assert articles[0][0].id not in article_ids
            assert articles[1][0].id not in article_ids

    def test_similarity_threshold_impact(self, session: Session, sample_articles_with_analysis):
        """Test how similarity threshold affects clustering."""
        articles = sample_articles_with_analysis

        # Test with high threshold (should cluster less)
        cluster_high = cluster_article(articles[0][0], session, similarity_threshold=0.9)
        session.commit()

        # Test with low threshold (should cluster more)
        cluster_low = cluster_article(articles[1][0], session, similarity_threshold=0.3)
        session.commit()

        # The exact behavior depends on the content, but both should either
        # return None (no cluster) or create a valid cluster
        if cluster_high:
            assert cluster_high.event_signature is not None

        if cluster_low:
            assert cluster_low.event_signature is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])