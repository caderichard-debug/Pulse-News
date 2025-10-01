"""
Basic API tests to ensure endpoints are working.
Run with: pytest backend/tests/
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint returns API info"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "Pulse" in data["name"]


def test_admin_stats_endpoint():
    """Test admin stats endpoint is accessible"""
    response = client.get("/admin/stats")
    assert response.status_code == 200
    data = response.json()
    assert "articles" in data
    assert "sources" in data


def test_topics_endpoint():
    """Test public topics endpoint"""
    response = client.get("/preferences/topics")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_register_validation():
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


def test_login_with_invalid_credentials():
    """Test login fails with invalid credentials"""
    response = client.post(
        "/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401


def test_protected_route_without_token():
    """Test that protected routes require authentication"""
    response = client.get("/auth/me")
    assert response.status_code == 403  # Forbidden without token


def test_preferences_without_auth():
    """Test preferences endpoint requires authentication"""
    response = client.get("/preferences")
    assert response.status_code == 403


def test_articles_analyzed_endpoint():
    """Test that analyzed articles endpoint is accessible"""
    response = client.get("/articles/analyzed")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "articles" in data
    assert isinstance(data["articles"], list)
