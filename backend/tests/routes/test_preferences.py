"""
Preferences tests - would have caught the UserTopicPreference field name bugs.
Run with: pytest backend/tests/test_preferences.py -v
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel, select
from sqlmodel.pool import StaticPool
from app.main import app
from app.database import get_session
from app.models import User, Topic, UserTopicPreference
from app.utils.auth import hash_password


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        # Seed topics
        topics = [
            Topic(id=1, name="general", description="General news"),
            Topic(id=2, name="politics", description="Political news"),
            Topic(id=3, name="technology", description="Tech news"),
        ]
        for topic in topics:
            session.add(topic)

        # Create test user
        user = User(
            id=1,
            email="testuser@example.com",
            hashed_password=hash_password("testpass123"),
            email_verified=False,
            is_active=True
        )
        session.add(user)
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


def test_user_topic_preference_field_names(session: Session):
    """Test UserTopicPreference model has correct field names (catches field name bugs)"""
    pref = UserTopicPreference(
        user_id=1,
        topic_id=1,
        include_in_newsletter=True  # Should be include_in_newsletter, not is_active!
    )

    session.add(pref)
    session.commit()

    # Verify correct field names
    assert hasattr(pref, "include_in_newsletter")

    # Should NOT have these fields:
    assert not hasattr(pref, "is_active")


def test_get_preferences_returns_all_topics(client: TestClient, auth_token: str):
    """Test that GET /preferences returns all topics"""
    response = client.get(
        "/preferences",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 200
    data = response.json()

    assert "topics" in data
    assert len(data["topics"]) == 3  # We seeded 3 topics
    assert all("id" in topic for topic in data["topics"])
    assert all("name" in topic for topic in data["topics"])
    assert all("is_active" in topic for topic in data["topics"])


def test_get_preferences_requires_auth(client: TestClient):
    """Test that preferences endpoint requires authentication"""
    response = client.get("/preferences")
    assert response.status_code == 403


def test_update_preferences_creates_topic_preferences(
    client: TestClient,
    auth_token: str,
    session: Session
):
    """Test that updating preferences creates UserTopicPreference records"""
    response = client.put(
        "/preferences",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "preferences": [
                {"topic_id": 1, "is_active": True},
                {"topic_id": 2, "is_active": True},
            ]
        }
    )

    assert response.status_code == 200

    # Verify database records were created with correct field names
    prefs = session.exec(
        select(UserTopicPreference).where(UserTopicPreference.user_id == 1)
    ).all()

    assert len(prefs) == 2

    # Check that records use include_in_newsletter
    for pref in prefs:
        assert hasattr(pref, "include_in_newsletter")
        assert pref.include_in_newsletter is True


def test_subscribe_to_topic(client: TestClient, auth_token: str, session: Session):
    """Test subscribing to a specific topic"""
    response = client.post(
        "/preferences/topics/1/subscribe",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 200

    # Verify preference was created with correct fields
    pref = session.exec(
        select(UserTopicPreference).where(
            UserTopicPreference.user_id == 1,
            UserTopicPreference.topic_id == 1
        )
    ).first()

    assert pref is not None
    assert pref.include_in_newsletter is True  # Should use include_in_newsletter


def test_unsubscribe_from_topic(client: TestClient, auth_token: str, session: Session):
    """Test unsubscribing from a topic"""
    # First subscribe
    pref = UserTopicPreference(
        user_id=1,
        topic_id=2,
        include_in_newsletter=True
    )
    session.add(pref)
    session.commit()

    # Then unsubscribe
    response = client.post(
        "/preferences/topics/2/unsubscribe",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 200

    # Verify preference was updated (not deleted)
    pref = session.exec(
        select(UserTopicPreference).where(
            UserTopicPreference.user_id == 1,
            UserTopicPreference.topic_id == 2
        )
    ).first()

    assert pref is not None
    assert pref.include_in_newsletter is False  # Should be set to False


def test_subscribe_to_nonexistent_topic(client: TestClient, auth_token: str):
    """Test that subscribing to non-existent topic fails gracefully"""
    response = client.post(
        "/preferences/topics/999/subscribe",  # Fixed: added /preferences prefix
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 404


def test_get_preferences_includes_user_customizations(
    client: TestClient,
    auth_token: str,
    session: Session
):
    """Test that GET /preferences returns user's customized preferences"""
    # Create custom preferences
    pref1 = UserTopicPreference(
        user_id=1,
        topic_id=1,
        include_in_newsletter=True
    )
    pref2 = UserTopicPreference(
        user_id=1,
        topic_id=2,
        include_in_newsletter=False
    )
    session.add(pref1)
    session.add(pref2)
    session.commit()

    response = client.get(
        "/preferences",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 200
    data = response.json()

    # Find the customized topics
    topic1 = next(t for t in data["topics"] if t["id"] == 1)
    topic2 = next(t for t in data["topics"] if t["id"] == 2)

    assert topic1["is_active"] is True
    assert topic2["is_active"] is False
