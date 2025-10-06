"""
Authentication tests - would have caught the field name bugs we fixed.
Run with: pytest backend/tests/test_auth.py -v
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel, select
from sqlmodel.pool import StaticPool
.main import app
.database import get_session
.models import User, Topic
.utils.auth import hash_password


# Create in-memory SQLite database for testing
@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        # Seed topics for testing
        topics = [
            Topic(id=1, name="general", description="General news"),
            Topic(id=2, name="politics", description="Political news"),
            Topic(id=3, name="technology", description="Tech news"),
        ]
        for topic in topics:
            session.add(topic)
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


def test_user_registration_creates_user(client: TestClient, session: Session):
    """Test that registration creates a user with correct field names"""
    response = client.post(
        "/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "testpass123",
        }
    )

    assert response.status_code == 201  # Registration returns 201 Created
    data = response.json()

    # Check response structure
    assert "access_token" in data
    assert "user" in data
    assert data["user"]["email"] == "newuser@example.com"
    assert "email_verified" in data["user"]

    # Check database - verify User model uses correct field names
    user = session.exec(select(User).where(User.email == "newuser@example.com")).first()
    assert user is not None
    assert hasattr(user, "hashed_password")  # Not password_hash!
    assert user.hashed_password is not None
    assert user.hashed_password != "testpass123"  # Should be hashed


def test_user_model_field_names(session: Session):
    """Test that User model has the correct field names (catches field name bugs)"""
    user = User(
        email="test@example.com",
        hashed_password=hash_password("password123"),  # Should be hashed_password, not password_hash
        email_verified=False,
        is_active=True
    )

    session.add(user)
    session.commit()

    # Verify the user was created with correct fields
    assert hasattr(user, "hashed_password")
    assert hasattr(user, "email")
    assert hasattr(user, "email_verified")
    assert hasattr(user, "is_active")
    assert hasattr(user, "name")  # Added for newsletter personalization
    # User model should NOT have these fields:
    assert not hasattr(user, "password_hash")


def test_login_verifies_password_correctly(client: TestClient, session: Session):
    """Test that login uses correct field name (hashed_password not password_hash)"""
    # Create user directly in database
    user = User(
        email="logintest@example.com",
        hashed_password=hash_password("testpass123"),
        email_verified=False,
        is_active=True
    )
    session.add(user)
    session.commit()

    # Test successful login
    response = client.post(
        "/auth/login",
        json={
            "email": "logintest@example.com",
            "password": "testpass123"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "logintest@example.com"


def test_login_fails_with_wrong_password(client: TestClient, session: Session):
    """Test that login properly rejects wrong passwords"""
    user = User(
        email="wrongpass@example.com",
        hashed_password=hash_password("correctpass123"),
        email_verified=False,
        is_active=True
    )
    session.add(user)
    session.commit()

    response = client.post(
        "/auth/login",
        json={
            "email": "wrongpass@example.com",
            "password": "wrongpass123"
        }
    )

    assert response.status_code == 401


def test_bcrypt_handles_long_passwords(client: TestClient):
    """Test that bcrypt properly handles passwords (catches bcrypt initialization bugs)"""
    # Test with normal password
    response = client.post(
        "/auth/register",
        json={
            "email": "normalpass@example.com",
            "password": "testpass123",
        }
    )
    assert response.status_code == 201  # Registration returns 201 Created

    # Test with maximum length password (bcrypt has 72-byte limit)
    long_password = "a" * 100  # 100 characters, more than 72 bytes
    response = client.post(
        "/auth/register",
        json={
            "email": "longpass@example.com",
            "password": long_password,
        }
    )
    # Should handle gracefully, not crash
    assert response.status_code in [201, 400, 422]  # 201 for success, 400/422 for validation errors


def test_register_requires_minimum_password_length(client: TestClient):
    """Test password validation (minimum 8 characters)"""
    response = client.post(
        "/auth/register",
        json={
            "email": "shortpass@example.com",
            "password": "short",  # Only 5 characters
        }
    )
    assert response.status_code == 422  # Validation error


def test_register_validates_email_format(client: TestClient):
    """Test email validation"""
    response = client.post(
        "/auth/register",
        json={
            "email": "invalid-email",  # Not a valid email
            "password": "testpass123",
        }
    )
    assert response.status_code == 422  # Validation error


def test_register_prevents_duplicate_emails(client: TestClient, session: Session):
    """Test that duplicate email registration is prevented"""
    user = User(
        email="duplicate@example.com",
        hashed_password=hash_password("testpass123"),
        email_verified=False,
        is_active=True
    )
    session.add(user)
    session.commit()

    # Try to register with same email
    response = client.post(
        "/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "testpass123",
        }
    )

    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


def test_protected_endpoint_requires_auth(client: TestClient):
    """Test that protected endpoints require authentication"""
    response = client.get("/auth/me")
    assert response.status_code == 403


def test_protected_endpoint_works_with_valid_token(client: TestClient, session: Session):
    """Test that valid JWT tokens grant access"""
    # Create user and login
    user = User(
        email="protected@example.com",
        hashed_password=hash_password("testpass123"),
        email_verified=False,
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)  # Refresh to ensure user is fully loaded

    # Login to get token
    login_response = client.post(
        "/auth/login",
        json={
            "email": "protected@example.com",
            "password": "testpass123"
        }
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # Access protected endpoint with token
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json()["email"] == "protected@example.com"
