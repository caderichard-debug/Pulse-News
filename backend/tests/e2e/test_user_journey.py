"""
End-to-end tests for complete user journeys through the API.
These tests simulate real user workflows without mocking.
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool
from app.main import app
from app.database import get_session
from app.models import Source, Topic, Framework
import time


@pytest.fixture(name="e2e_session")
def e2e_session_fixture():
    """Create a fresh test database for E2E tests"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        # Seed minimal required data
        topic = Topic(name="Technology", description="Tech news")
        source = Source(
            name="TechCrunch",
            rss_url="https://techcrunch.com/feed/",
            website_url="https://techcrunch.com",
            is_active=True,
            trust_score=8.0
        )
        framework = Framework(
            name="Innovation vs. Regulation",
            description="Balance between technological innovation and regulation",
            axis_description="Level of government regulation on technology",
            left_position="Minimal regulation, maximum innovation",
            right_position="Strong regulation for safety and ethics"
        )

        session.add(topic)
        session.add(source)
        session.add(framework)
        session.commit()
        session.refresh(topic)
        session.refresh(source)
        session.refresh(framework)

        yield session


@pytest.fixture(name="e2e_client")
def e2e_client_fixture(e2e_session: Session):
    """Create test client with E2E session"""

    def get_session_override():
        return e2e_session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


class TestCompleteUserJourney:
    """Test complete user journey from registration to reading articles"""

    def test_full_user_workflow(self, e2e_client: TestClient, e2e_session: Session):
        """
        E2E Test: Complete user journey
        1. User registers
        2. User logs in
        3. User sets topic preferences
        4. User browses feed
        5. User reads article detail
        """

        # Step 1: User Registration
        register_response = e2e_client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "securepassword123",
                "name": "Test User"
            }
        )
        assert register_response.status_code == 200
        user_data = register_response.json()
        assert user_data["email"] == "newuser@example.com"
        assert user_data["name"] == "Test User"
        assert "id" in user_data

        # Step 2: User Login
        login_response = e2e_client.post(
            "/auth/login",
            json={
                "email": "newuser@example.com",
                "password": "securepassword123"
            }
        )
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert "access_token" in login_data
        assert login_data["token_type"] == "bearer"

        token = login_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Step 3: User Sets Topic Preferences
        # Get available topics
        topics_response = e2e_client.get("/preferences/topics", headers=headers)
        assert topics_response.status_code == 200
        topics = topics_response.json()
        assert len(topics) > 0

        # Subscribe to a topic
        topic_id = topics[0]["id"]
        subscribe_response = e2e_client.post(
            f"/preferences/topics/{topic_id}/subscribe",
            headers=headers,
            json={"priority": 5, "articles_per_topic": 5}
        )
        assert subscribe_response.status_code == 200

        # Verify preference was saved
        prefs_response = e2e_client.get("/preferences", headers=headers)
        assert prefs_response.status_code == 200
        prefs_data = prefs_response.json()
        assert len(prefs_data["topics"]) == 1
        assert prefs_data["topics"][0]["topic_id"] == topic_id

        # Step 4: User Updates Settings
        settings_response = e2e_client.put(
            "/preferences/settings",
            headers=headers,
            json={
                "source_discovery_mode": "balanced",
                "article_order_preference": "good_first",
                "articles_per_topic_default": 5
            }
        )
        assert settings_response.status_code == 200

        # Step 5: User Browses Feed (empty but authenticated)
        feed_response = e2e_client.get("/feed/articles", headers=headers)
        assert feed_response.status_code == 200
        feed_data = feed_response.json()
        assert "articles" in feed_data
        assert "total" in feed_data

        # Step 6: Verify User Stats
        stats_response = e2e_client.get("/analytics/user-stats", headers=headers)
        assert stats_response.status_code == 200
        stats_data = stats_response.json()
        assert "topics_tracked" in stats_data
        assert stats_data["topics_tracked"] == 1

    def test_article_pipeline_workflow(self, e2e_client: TestClient, e2e_session: Session):
        """
        E2E Test: Article processing pipeline
        1. Create article (simulating scrape)
        2. Extract content (simulating extraction)
        3. Analyze with AI (simulating analysis)
        4. Map to frameworks
        5. User views article
        """
        from app.models import Article, ArticleAnalysis, ArticleFrameworkLink, ProcessingStatus

        # Setup: Create authenticated user
        register_response = e2e_client.post(
            "/auth/register",
            json={
                "email": "reader@example.com",
                "password": "password123",
                "name": "Article Reader"
            }
        )
        assert register_response.status_code == 200

        login_response = e2e_client.post(
            "/auth/login",
            json={"email": "reader@example.com", "password": "password123"}
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Step 1: Create article (simulating RSS scrape)
        source = e2e_session.query(Source).first()
        topic = e2e_session.query(Topic).first()

        article = Article(
            title="AI Regulation Debate Intensifies",
            url="https://example.com/ai-regulation",
            source_id=source.id,
            description="Government considers new AI regulations",
            published_at="2025-01-01T10:00:00Z",
            status=ProcessingStatus.SCRAPED
        )
        e2e_session.add(article)
        e2e_session.commit()
        e2e_session.refresh(article)

        # Step 2: Simulate extraction
        article.content_text = "Full article content about AI regulation..."
        article.status = ProcessingStatus.EXTRACTED
        e2e_session.add(article)
        e2e_session.commit()

        # Step 3: Simulate AI analysis
        analysis = ArticleAnalysis(
            article_id=article.id,
            summary="Government proposes new regulations for AI development.",
            sentiment_score=0,
            political_lean="CENTER",
            bias_indicators="Neutral reporting",
            key_stats=["50% of AI companies affected", "2025 implementation"]
        )
        e2e_session.add(analysis)

        article.status = ProcessingStatus.ANALYZED
        e2e_session.add(article)
        e2e_session.commit()
        e2e_session.refresh(analysis)

        # Step 4: Map to frameworks
        framework = e2e_session.query(Framework).first()
        framework_link = ArticleFrameworkLink(
            article_id=article.id,
            framework_id=framework.id,
            relevance_score=0.9,
            position_on_axis=-5,
            ai_explanation="Article discusses need for AI regulation"
        )
        e2e_session.add(framework_link)
        e2e_session.commit()

        # Step 5: User views article
        article_response = e2e_client.get(f"/articles/{article.id}", headers=headers)
        assert article_response.status_code == 200

        article_data = article_response.json()
        assert article_data["title"] == "AI Regulation Debate Intensifies"
        assert article_data["summary"] == "Government proposes new regulations for AI development."
        assert len(article_data["frameworks"]) == 1
        assert article_data["frameworks"][0]["framework_name"] == "Innovation vs. Regulation"

    def test_newsletter_generation_workflow(self, e2e_client: TestClient, e2e_session: Session):
        """
        E2E Test: Newsletter generation workflow
        1. User subscribes to topics
        2. Articles are analyzed
        3. Newsletter is generated
        4. User views newsletter
        """
        from app.models import Article, ArticleAnalysis, UserTopicPreference, ProcessingStatus
        from app.services.newsletter_service import generate_newsletter

        # Setup: Create user
        register_response = e2e_client.post(
            "/auth/register",
            json={
                "email": "newsletter@example.com",
                "password": "password123",
                "name": "Newsletter User"
            }
        )
        user_id = register_response.json()["id"]

        login_response = e2e_client.post(
            "/auth/login",
            json={"email": "newsletter@example.com", "password": "password123"}
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Step 1: Subscribe to topic
        topic = e2e_session.query(Topic).first()
        preference = UserTopicPreference(
            user_id=user_id,
            topic_id=topic.id,
            is_subscribed=True,
            priority=5,
            articles_per_topic=3
        )
        e2e_session.add(preference)
        e2e_session.commit()

        # Step 2: Create analyzed articles
        source = e2e_session.query(Source).first()

        for i in range(3):
            article = Article(
                title=f"Tech Article {i+1}",
                url=f"https://example.com/article-{i+1}",
                source_id=source.id,
                description=f"Article {i+1} description",
                published_at="2025-01-01T10:00:00Z",
                status=ProcessingStatus.ANALYZED
            )
            e2e_session.add(article)
            e2e_session.commit()
            e2e_session.refresh(article)

            # Add analysis
            analysis = ArticleAnalysis(
                article_id=article.id,
                summary=f"Summary of article {i+1}",
                sentiment_score=i - 1,  # -1, 0, 1
                political_lean="CENTER",
                bias_indicators="Neutral",
                key_stats=[]
            )
            e2e_session.add(analysis)

            # Link to topic
            from app.models import ArticleTopic
            article_topic = ArticleTopic(article_id=article.id, topic_id=topic.id)
            e2e_session.add(article_topic)

        e2e_session.commit()

        # Step 3: Generate newsletter
        newsletter = generate_newsletter(e2e_session, user_id)
        assert newsletter is not None
        assert newsletter.user_id == user_id

        # Step 4: User views newsletter preview
        preview_response = e2e_client.get("/preferences/newsletter-preview", headers=headers)
        assert preview_response.status_code == 200
        preview_data = preview_response.json()
        assert len(preview_data["articles"]) > 0


class TestAuthenticationWorkflow:
    """Test authentication-related workflows"""

    def test_authentication_flow(self, e2e_client: TestClient):
        """Test complete authentication flow"""

        # Step 1: Registration
        register_response = e2e_client.post(
            "/auth/register",
            json={
                "email": "auth@example.com",
                "password": "strongpassword123",
                "name": "Auth User"
            }
        )
        assert register_response.status_code == 200

        # Step 2: Login
        login_response = e2e_client.post(
            "/auth/login",
            json={"email": "auth@example.com", "password": "strongpassword123"}
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Step 3: Access protected endpoint
        headers = {"Authorization": f"Bearer {token}"}
        me_response = e2e_client.get("/auth/me", headers=headers)
        assert me_response.status_code == 200
        user_data = me_response.json()
        assert user_data["email"] == "auth@example.com"

        # Step 4: Access without token should fail
        no_auth_response = e2e_client.get("/auth/me")
        assert no_auth_response.status_code == 401

    def test_invalid_credentials(self, e2e_client: TestClient):
        """Test handling of invalid credentials"""

        # Register user
        e2e_client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "password": "correctpassword",
                "name": "Test"
            }
        )

        # Try to login with wrong password
        login_response = e2e_client.post(
            "/auth/login",
            json={"email": "test@example.com", "password": "wrongpassword"}
        )
        assert login_response.status_code == 401

        # Try to login with non-existent user
        login_response = e2e_client.post(
            "/auth/login",
            json={"email": "nonexistent@example.com", "password": "password"}
        )
        assert login_response.status_code == 401


class TestErrorHandling:
    """Test error handling in E2E scenarios"""

    def test_handles_database_constraints(self, e2e_client: TestClient):
        """Test handling of database constraint violations"""

        # Register user
        e2e_client.post(
            "/auth/register",
            json={
                "email": "unique@example.com",
                "password": "password123",
                "name": "Unique User"
            }
        )

        # Try to register same email again
        duplicate_response = e2e_client.post(
            "/auth/register",
            json={
                "email": "unique@example.com",
                "password": "password456",
                "name": "Duplicate User"
            }
        )
        assert duplicate_response.status_code == 400
