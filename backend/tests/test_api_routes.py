"""
Additional tests for API routes (articles and admin endpoints).
Extends test_api.py with more comprehensive coverage.
"""

import pytest
from sqlmodel import Session
from fastapi.testclient import TestClient
from ..models import (
    Article, ArticleAnalysis, Source, Framework, User,
    ProcessingStatus, PoliticalLean
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
        is_active=True,
        trust_score=0.8
    )
    session.add(source)
    session.commit()
    session.refresh(source)
    return source


@pytest.fixture
def analyzed_article(session: Session, sample_source: Source):
    """Create an analyzed article"""
    article = Article(
        source_id=sample_source.id,
        title="Test Article",
        url="https://testnews.com/article",
        content_text="This is the full article content.",
        word_count=100,
        published_at=datetime.utcnow(),
        scraped_at=datetime.utcnow(),
        processing_status=ProcessingStatus.COMPLETED,
        extraction_method="trafilatura"
    )
    session.add(article)
    session.commit()
    session.refresh(article)

    analysis = ArticleAnalysis(
        article_id=article.id,
        summary="Test summary of the article",
        sentiment_score=5,
        political_lean=PoliticalLean.CENTER,
        bias_indicators="neutral",
        key_stats='["stat1", "stat2"]',
        processing_cost=0.002,
        processed_at=datetime.utcnow()
    )
    session.add(analysis)
    session.commit()

    return article


@pytest.fixture
def sample_framework(session: Session):
    """Create a test framework"""
    framework = Framework(
        name="Test Framework",
        description="Test framework description",
        axis_description="test axis",
        left_position="left",
        right_position="right",
        article_count=0,
        is_seed=True,
        created_at=datetime.utcnow()
    )
    session.add(framework)
    session.commit()
    session.refresh(framework)
    return framework


class TestArticlesRoutes:
    """Test /articles endpoints"""

    def test_get_analyzed_articles_success(
        self, client: TestClient, analyzed_article: Article
    ):
        """Test retrieving analyzed articles"""
        response = client.get("/articles/analyzed")

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "articles" in data
        assert data["total"] == 1
        assert len(data["articles"]) == 1

        article_data = data["articles"][0]
        assert article_data["id"] == analyzed_article.id
        assert article_data["title"] == "Test Article"
        assert "analysis" in article_data
        assert article_data["analysis"]["summary"] == "Test summary of the article"

    def test_get_analyzed_articles_pagination(
        self, client: TestClient, session: Session, sample_source: Source
    ):
        """Test pagination parameters"""
        # Create multiple analyzed articles
        for i in range(15):
            article = Article(
                source_id=sample_source.id,
                title=f"Article {i}",
                url=f"https://testnews.com/article{i}",
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

        # Test limit
        response = client.get("/articles/analyzed?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["articles"]) == 5

        # Test offset
        response = client.get("/articles/analyzed?limit=5&offset=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["articles"]) == 5

    def test_get_analyzed_articles_empty(self, client: TestClient):
        """Test when no analyzed articles exist"""
        response = client.get("/articles/analyzed")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["articles"] == []

    def test_get_article_detail_success(
        self, client: TestClient, analyzed_article: Article
    ):
        """Test retrieving single article detail"""
        response = client.get(f"/articles/{analyzed_article.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == analyzed_article.id
        assert data["title"] == "Test Article"
        assert data["word_count"] == 100
        assert data["processing_status"] == "completed"  # Enum value is lowercase
        assert "content_preview" in data
        assert data["has_full_content"] is True
        assert "analysis" in data
        assert data["analysis"]["summary"] == "Test summary of the article"

    def test_get_article_detail_not_found(self, client: TestClient):
        """Test 404 for non-existent article"""
        response = client.get("/articles/99999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_article_detail_without_analysis(
        self, client: TestClient, session: Session, sample_source: Source
    ):
        """Test article detail for article without analysis"""
        article = Article(
            source_id=sample_source.id,
            title="Unanalyzed Article",
            url="https://testnews.com/unanalyzed",
            published_at=datetime.utcnow(),
            scraped_at=datetime.utcnow(),
            processing_status=ProcessingStatus.PENDING
        )
        session.add(article)
        session.commit()
        session.refresh(article)

        response = client.get(f"/articles/{article.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["analysis"] is None


class TestAdminRoutes:
    """Test /admin endpoints"""

    def test_get_system_stats(
        self, client: TestClient, analyzed_article: Article, sample_framework: Framework
    ):
        """Test system stats endpoint"""
        response = client.get("/admin/stats")

        assert response.status_code == 200
        data = response.json()

        # Verify structure
        assert "articles" in data
        assert "sources" in data
        assert "frameworks" in data
        assert "users" in data
        assert "timestamp" in data

        # Verify article stats
        assert data["articles"]["total"] >= 1
        assert "pending" in data["articles"]
        assert "completed" in data["articles"]
        assert "failed" in data["articles"]
        assert "extraction_success_rate" in data["articles"]

        # Verify framework stats
        assert data["frameworks"]["total"] >= 1
        assert "seed" in data["frameworks"]
        assert "ai_generated" in data["frameworks"]

    def test_get_system_stats_empty_database(self, client: TestClient):
        """Test stats with empty database"""
        response = client.get("/admin/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["articles"]["total"] == 0
        assert data["sources"]["total"] == 0
        assert data["frameworks"]["total"] == 0

    def test_get_scheduler_status(self, client: TestClient):
        """Test scheduler status endpoint"""
        response = client.get("/admin/scheduler/status")

        assert response.status_code == 200
        # Just verify it returns valid JSON
        data = response.json()
        assert isinstance(data, dict)

    def test_trigger_scrape_job(self, client: TestClient):
        """Test manual scrape job trigger"""
        response = client.post("/admin/jobs/scrape")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "triggered"
        assert data["job"] == "scrape_rss"
        assert "message" in data

    def test_trigger_extract_job(self, client: TestClient):
        """Test manual extract job trigger"""
        response = client.post("/admin/jobs/extract")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "triggered"
        assert data["job"] == "extract_articles"

    def test_trigger_analyze_job(self, client: TestClient):
        """Test manual analyze job trigger"""
        response = client.post("/admin/jobs/analyze")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "triggered"
        assert data["job"] == "analyze_articles"

    def test_trigger_framework_job(self, client: TestClient):
        """Test manual framework job trigger"""
        response = client.post("/admin/jobs/frameworks")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "triggered"
        assert data["job"] == "update_frameworks"

    def test_get_recent_articles(
        self, client: TestClient, session: Session, sample_source: Source
    ):
        """Test getting recent articles"""
        # Create articles with different timestamps
        old_article = Article(
            source_id=sample_source.id,
            title="Old Article",
            url="https://testnews.com/old",
            published_at=datetime.utcnow() - timedelta(days=7),
            scraped_at=datetime.utcnow() - timedelta(days=7),
            processing_status=ProcessingStatus.COMPLETED
        )
        new_article = Article(
            source_id=sample_source.id,
            title="New Article",
            url="https://testnews.com/new",
            published_at=datetime.utcnow(),
            scraped_at=datetime.utcnow(),
            processing_status=ProcessingStatus.PENDING
        )
        session.add_all([old_article, new_article])
        session.commit()

        response = client.get("/admin/articles/recent")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

        # Most recent should be first
        assert data[0]["title"] == "New Article"

    def test_get_recent_articles_with_limit(
        self, client: TestClient, session: Session, sample_source: Source
    ):
        """Test recent articles limit parameter"""
        # Create 15 articles
        for i in range(15):
            article = Article(
                source_id=sample_source.id,
                title=f"Article {i}",
                url=f"https://testnews.com/article{i}",
                published_at=datetime.utcnow(),
                scraped_at=datetime.utcnow(),
                processing_status=ProcessingStatus.PENDING
            )
            session.add(article)
        session.commit()

        response = client.get("/admin/articles/recent?limit=5")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5

    def test_get_sources_status(
        self, client: TestClient, session: Session, sample_source: Source
    ):
        """Test sources status endpoint"""
        # Create articles for the source
        for i in range(5):
            article = Article(
                source_id=sample_source.id,
                title=f"Article {i}",
                url=f"https://testnews.com/article{i}",
                published_at=datetime.utcnow(),
                scraped_at=datetime.utcnow(),
                processing_status=ProcessingStatus.COMPLETED if i < 3 else ProcessingStatus.PENDING
            )
            session.add(article)
        session.commit()

        response = client.get("/admin/sources/status")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

        # Find our test source
        test_source = next(s for s in data if s["id"] == sample_source.id)
        assert test_source["name"] == "Test News"
        assert test_source["article_count"] == 5
        assert test_source["completed_count"] == 3
        assert test_source["is_active"] is True
        assert test_source["trust_score"] == 0.8

    def test_get_sources_status_empty(self, client: TestClient):
        """Test sources status with no sources"""
        response = client.get("/admin/sources/status")

        assert response.status_code == 200
        data = response.json()
        assert data == []
