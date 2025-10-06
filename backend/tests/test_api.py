"""
Basic API tests to ensure endpoints are working.
Run with: pytest backend/tests/
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool
from .main import app
from .database import get_session


@pytest.fixture(name="session")
def session_fixture():
    """Create test database session"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Create test client with overridden database dependency"""
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_root_endpoint(client: TestClient):
    """Test the root endpoint returns API info"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "Pulse" in data["name"]


def test_admin_stats_endpoint(client: TestClient):
    """Test admin stats endpoint is accessible"""
    response = client.get("/admin/stats")
    assert response.status_code == 200
    data = response.json()
    assert "articles" in data
    assert "sources" in data


def test_topics_endpoint(client: TestClient):
    """Test public topics endpoint"""
    response = client.get("/preferences/topics")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_register_validation(client: TestClient):
    """Test user registration validation (removed 'name' - not in User model)"""
    # Test with invalid email
    response = client.post(
        "/auth/register",
        json={
            "email": "invalid-email",
            "password": "password123"
        }
    )
    assert response.status_code == 422  # Validation error

    # Test with short password
    response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "short"
        }
    )
    assert response.status_code == 422  # Should fail validation


def test_login_with_invalid_credentials(client: TestClient):
    """Test login fails with invalid credentials"""
    response = client.post(
        "/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401


def test_protected_route_without_token(client: TestClient):
    """Test that protected routes require authentication"""
    response = client.get("/auth/me")
    assert response.status_code == 403  # Forbidden without token


def test_preferences_without_auth(client: TestClient):
    """Test preferences endpoint requires authentication"""
    response = client.get("/preferences")
    assert response.status_code == 403


def test_articles_analyzed_endpoint(client: TestClient):
    """Test that analyzed articles endpoint is accessible"""
    response = client.get("/articles/analyzed")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "articles" in data
    assert isinstance(data["articles"], list)
