"""
Tests for source preferences and user settings endpoints.
Run with: pytest backend/tests/test_source_preferences.py -v
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel, select
from sqlmodel.pool import StaticPool
from .main import app
from .database import get_session
from .models import User, Source, UserSourceSubscription, Article, ArticleAnalysis, PoliticalLean
from .utils.auth import hash_password
from datetime import datetime


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        # Seed sources
        sources = [
            Source(id=1, name="Reuters", url="https://reuters.com", rss_feed_url="https://reuters.com/rss", trust_score=0.95),
            Source(id=2, name="NPR", url="https://npr.org", rss_feed_url="https://npr.org/rss", trust_score=0.90),
            Source(id=3, name="Fox News", url="https://foxnews.com", rss_feed_url="https://foxnews.com/rss", trust_score=0.65),
        ]
        for source in sources:
            session.add(source)

        # Create test user with default preferences
        user = User(
            id=1,
            email="testuser@example.com",
            hashed_password=hash_password("testpass123"),
            email_verified=False,
            is_active=True,
            source_discovery_mode="some",
            article_order_preference="mixed",
            articles_per_topic_default=5
        )
        session.add(user)

        # Add some articles with political lean for aggregation testing
        article1 = Article(
            id=1,
            source_id=2,  # NPR
            title="Test Article 1",
            url="https://example.com/1",
            published_at=datetime.utcnow(),
            processing_status="completed"
        )
        session.add(article1)

        analysis1 = ArticleAnalysis(
            article_id=1,
            summary="Test summary",
            sentiment_score=5,
            political_lean=PoliticalLean.CENTER
        )
        session.add(analysis1)

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


class TestSourcePreferences:
    """Tests for source preference endpoints"""

    def test_get_sources_returns_all_sources(self, client: TestClient, auth_token: str):
        """Test GET /preferences/sources returns all sources"""
        response = client.get(
            "/preferences/sources",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 3
        assert all("source_id" in source for source in data)
        assert all("name" in source for source in data)
        assert all("trust_score" in source for source in data)
        assert all("subscribed" in source for source in data)

        # All should be unsubscribed initially
        assert all(source["subscribed"] is False for source in data)

    def test_get_sources_includes_political_lean(self, client: TestClient, auth_token: str):
        """Test that sources include aggregated political lean from articles"""
        response = client.get(
            "/preferences/sources",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # NPR should have "center" lean from the test article
        npr = next(s for s in data if s["name"] == "NPR")
        assert npr["political_lean"] == "center"

    def test_get_sources_requires_auth(self, client: TestClient):
        """Test that sources endpoint requires authentication"""
        response = client.get("/preferences/sources")
        assert response.status_code == 403

    def test_update_source_preferences(
        self,
        client: TestClient,
        auth_token: str,
        session: Session
    ):
        """Test updating source subscriptions"""
        response = client.put(
            "/preferences/sources",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"source_ids": [1, 2]}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["subscribed_count"] == 2

        # Verify database records
        subs = session.exec(
            select(UserSourceSubscription).where(UserSourceSubscription.user_id == 1)
        ).all()

        assert len(subs) == 2
        assert all(sub.subscribed is True for sub in subs)
        assert {sub.source_id for sub in subs} == {1, 2}

    def test_update_source_preferences_replaces_existing(
        self,
        client: TestClient,
        auth_token: str,
        session: Session
    ):
        """Test that updating sources replaces existing subscriptions"""
        # First subscription
        sub1 = UserSourceSubscription(user_id=1, source_id=1, subscribed=True)
        session.add(sub1)
        session.commit()

        # Update to different sources
        response = client.put(
            "/preferences/sources",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"source_ids": [2, 3]}
        )

        assert response.status_code == 200

        # Should only have new subscriptions
        subs = session.exec(
            select(UserSourceSubscription).where(UserSourceSubscription.user_id == 1)
        ).all()

        assert len(subs) == 2
        assert {sub.source_id for sub in subs} == {2, 3}

    def test_update_source_preferences_invalid_source(
        self,
        client: TestClient,
        auth_token: str
    ):
        """Test that invalid source IDs are skipped"""
        response = client.put(
            "/preferences/sources",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"source_ids": [1, 999]}  # 999 doesn't exist
        )

        # Should succeed but only subscribe to valid source
        assert response.status_code == 200
        data = response.json()
        assert data["subscribed_count"] == 1

    def test_get_sources_shows_subscribed_status(
        self,
        client: TestClient,
        auth_token: str,
        session: Session
    ):
        """Test that GET sources reflects subscription status"""
        # Subscribe to source 1
        sub = UserSourceSubscription(user_id=1, source_id=1, subscribed=True)
        session.add(sub)
        session.commit()

        response = client.get(
            "/preferences/sources",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        reuters = next(s for s in data if s["source_id"] == 1)
        npr = next(s for s in data if s["source_id"] == 2)

        assert reuters["subscribed"] is True
        assert npr["subscribed"] is False


class TestUserSettings:
    """Tests for user settings endpoints"""

    def test_get_settings_returns_defaults(self, client: TestClient, auth_token: str):
        """Test GET /preferences/settings returns user settings"""
        response = client.get(
            "/preferences/settings",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["source_discovery_mode"] == "some"
        assert data["article_order_preference"] == "mixed"
        assert data["articles_per_topic_default"] == 5

    def test_update_discovery_mode(
        self,
        client: TestClient,
        auth_token: str,
        session: Session
    ):
        """Test updating source discovery mode"""
        response = client.put(
            "/preferences/settings",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"source_discovery_mode": "open"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["settings"]["source_discovery_mode"] == "open"

        # Verify in database
        user = session.get(User, 1)
        assert user.source_discovery_mode == "open"

    def test_update_article_order_preference(
        self,
        client: TestClient,
        auth_token: str,
        session: Session
    ):
        """Test updating article order preference"""
        response = client.put(
            "/preferences/settings",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"article_order_preference": "good_first"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["settings"]["article_order_preference"] == "good_first"

        # Verify in database
        user = session.get(User, 1)
        assert user.article_order_preference == "good_first"

    def test_update_articles_per_topic(
        self,
        client: TestClient,
        auth_token: str,
        session: Session
    ):
        """Test updating articles per topic default"""
        response = client.put(
            "/preferences/settings",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"articles_per_topic_default": 8}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["settings"]["articles_per_topic_default"] == 8

        # Verify in database
        user = session.get(User, 1)
        assert user.articles_per_topic_default == 8

    def test_update_multiple_settings(
        self,
        client: TestClient,
        auth_token: str,
        session: Session
    ):
        """Test updating multiple settings at once"""
        response = client.put(
            "/preferences/settings",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "source_discovery_mode": "none",
                "article_order_preference": "good_last",
                "articles_per_topic_default": 10
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["updated_fields"]) == 3

        # Verify in database
        user = session.get(User, 1)
        assert user.source_discovery_mode == "none"
        assert user.article_order_preference == "good_last"
        assert user.articles_per_topic_default == 10

    def test_invalid_discovery_mode(self, client: TestClient, auth_token: str):
        """Test that invalid discovery mode is rejected"""
        response = client.put(
            "/preferences/settings",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"source_discovery_mode": "invalid"}
        )

        assert response.status_code == 400
        assert "must be" in response.json()["detail"]

    def test_invalid_article_order(self, client: TestClient, auth_token: str):
        """Test that invalid article order is rejected"""
        response = client.put(
            "/preferences/settings",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"article_order_preference": "invalid"}
        )

        assert response.status_code == 400
        assert "must be" in response.json()["detail"]

    def test_articles_per_topic_validation(self, client: TestClient, auth_token: str):
        """Test that articles_per_topic is validated (1-10)"""
        # Too high
        response = client.put(
            "/preferences/settings",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"articles_per_topic_default": 15}
        )
        assert response.status_code == 422

        # Too low
        response = client.put(
            "/preferences/settings",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"articles_per_topic_default": 0}
        )
        assert response.status_code == 422

        # Valid
        response = client.put(
            "/preferences/settings",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"articles_per_topic_default": 7}
        )
        assert response.status_code == 200

    def test_partial_update_preserves_other_settings(
        self,
        client: TestClient,
        auth_token: str,
        session: Session
    ):
        """Test that updating one setting doesn't change others"""
        # Only update discovery mode
        response = client.put(
            "/preferences/settings",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"source_discovery_mode": "open"}
        )

        assert response.status_code == 200

        # Other settings should remain unchanged
        user = session.get(User, 1)
        assert user.source_discovery_mode == "open"
        assert user.article_order_preference == "mixed"  # unchanged
        assert user.articles_per_topic_default == 5  # unchanged

    def test_settings_require_auth(self, client: TestClient):
        """Test that settings endpoints require authentication"""
        response = client.get("/preferences/settings")
        assert response.status_code == 403

        response = client.put(
            "/preferences/settings",
            json={"source_discovery_mode": "open"}
        )
        assert response.status_code == 403
