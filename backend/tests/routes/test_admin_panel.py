"""
Tests for admin panel endpoints.
Tests admin authentication, dashboard, job management, and CRUD operations.
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session
from app.models import User, Article, Source, JobExecutionHistory
from app.main import app
from app.database import get_session
from app.utils.auth import hash_password
from app import config
from datetime import datetime

# Test constants
ADMIN_TOKEN = "test-admin-token-12345"


@pytest.fixture
def admin_user(session: Session):
    """Create an admin user for testing."""
    user = User(
        email="admin@example.com",
        name="Admin User",
        hashed_password=hash_password("password"),
        is_admin=True,
        email_verified=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def admin_token(client: TestClient, admin_user: User):
    """Get JWT token for admin user."""
    response = client.post(
        "/auth/login",
        json={"email": "admin@example.com", "password": "password"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture(autouse=True)
def set_admin_token(monkeypatch):
    """Set admin token in environment and settings for all tests."""
    monkeypatch.setenv("ADMIN_TOKEN", ADMIN_TOKEN)
    # Patch the settings object that admin_auth imports
    monkeypatch.setattr(config.settings, "admin_token", ADMIN_TOKEN)


@pytest.fixture
def admin_headers(admin_token: str):
    """Create headers with both admin token and JWT token."""
    return {
        "Authorization": f"Bearer {admin_token}",
        "X-Admin-Token": ADMIN_TOKEN
    }


class TestAdminAuthentication:
    """Test admin authentication and authorization."""

    def test_verify_admin_token_success(self, client: TestClient, admin_headers: dict):
        """Test successful admin token verification."""
        response = client.get("/admin-panel/verify", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["user"]["email"] == "admin@example.com"
        assert data["user"]["is_admin"] is True

    def test_verify_admin_token_missing_admin_token(self, client: TestClient, admin_token: str):
        """Test verification succeeds for admin user (X-Admin-Token not required for /verify)."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/admin-panel/verify", headers=headers)
        assert response.status_code == 200
        assert response.json()["valid"] is True

    def test_verify_admin_token_invalid_admin_token(self, client: TestClient, admin_token: str):
        """Test verification succeeds for admin user even with invalid X-Admin-Token (not checked by /verify)."""
        headers = {
            "Authorization": f"Bearer {admin_token}",
            "X-Admin-Token": "invalid-token"
        }
        response = client.get("/admin-panel/verify", headers=headers)
        # /verify only checks is_admin, not X-Admin-Token
        assert response.status_code == 200

    def test_verify_admin_token_non_admin_user(self, client: TestClient, session: Session, monkeypatch):
        """Test verification fails for non-admin user."""
        # Create non-admin user
        user = User(
            email="regular@example.com",
            name="Regular User",
            hashed_password=hash_password("password"),
            is_admin=False,
            email_verified=True
        )
        session.add(user)
        session.commit()

        # Login as regular user
        response = client.post(
            "/auth/login",
            json={"email": "regular@example.com", "password": "password"}
        )
        token = response.json()["access_token"]

        # Mock admin token
        monkeypatch.setenv("ADMIN_TOKEN", ADMIN_TOKEN)

        headers = {
            "Authorization": f"Bearer {token}",
            "X-Admin-Token": ADMIN_TOKEN
        }
        response = client.get("/admin-panel/verify", headers=headers)
        assert response.status_code in [401, 403]


class TestAdminDashboard:
    """Test admin dashboard endpoint."""

    def test_get_dashboard(self, client: TestClient, admin_headers: dict, session: Session):
        """Test getting admin dashboard data."""
        response = client.get("/admin-panel/dashboard", headers=admin_headers)
        assert response.status_code == 200

        data = response.json()
        assert "system_stats" in data
        assert "recent_jobs" in data
        assert "active_jobs" in data
        assert "error_summary" in data
        assert "timestamp" in data

        # Check system stats structure
        stats = data["system_stats"]
        assert "users" in stats
        assert "articles" in stats
        assert "sources" in stats
        assert "frameworks" in stats


class TestJobManagement:
    """Test job management endpoints."""

    def test_get_job_history(self, client: TestClient, admin_headers: dict, session: Session):
        """Test getting job execution history."""
        # Create some job history
        job1 = JobExecutionHistory(
            job_id="scrape_rss",
            job_name="Scrape RSS Feeds",
            started_at=datetime.utcnow(),
            status="success",
            triggered_by="scheduler"
        )
        session.add(job1)
        session.commit()

        response = client.get("/admin-panel/jobs/history", headers=admin_headers)
        assert response.status_code == 200

        data = response.json()
        assert "jobs" in data
        assert "total_count" in data
        assert data["total_count"] >= 1

    def test_get_job_history_with_filters(self, client: TestClient, admin_headers: dict, session: Session):
        """Test job history with status filter."""
        response = client.get(
            "/admin-panel/jobs/history?status=success&limit=5",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 5

    def test_get_job_execution_log(self, client: TestClient, admin_headers: dict, session: Session):
        """Test getting a single job execution log entry."""
        job = JobExecutionHistory(
            job_id="extract_articles",
            job_name="Extract Article Content",
            started_at=datetime.utcnow(),
            status="failed",
            error_message="Sample failure",
            result_data="{'success': False}",
            triggered_by="admin",
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        response = client.get(f"/admin-panel/jobs/history/{job.id}", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == job.id
        assert data["job_id"] == "extract_articles"
        assert data["error_message"] == "Sample failure"

    def test_get_scheduler_jobs(self, client: TestClient, admin_headers: dict):
        """Test scheduler job listing endpoint."""
        response = client.get("/admin-panel/jobs/scheduler", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "jobs" in data

    def test_control_scheduler_job_invalid_action(self, client: TestClient, admin_headers: dict):
        """Test scheduler control validation for unsupported action."""
        response = client.post(
            "/admin-panel/jobs/control/scrape_rss?action=invalid",
            headers=admin_headers,
        )
        assert response.status_code == 400

    def test_trigger_job(self, client: TestClient, admin_headers: dict, session: Session):
        """Test manually triggering a job."""
        response = client.post(
            "/admin-panel/jobs/trigger/scrape_rss",
            headers=admin_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert data["job_id"] == "scrape_rss"
        assert "result" in data
        assert "execution_id" in data

    def test_trigger_reanalyze_unanalyzed_failed_job(self, client: TestClient, admin_headers: dict):
        """Test manual trigger for re-analysis recovery job."""
        response = client.post(
            "/admin-panel/jobs/trigger/reanalyze_unanalyzed_failed",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "reanalyze_unanalyzed_failed"


class TestUserManagement:
    """Test user management endpoints."""

    def test_get_users(self, client: TestClient, admin_headers: dict):
        """Test getting list of users."""
        response = client.get("/admin-panel/users", headers=admin_headers)
        assert response.status_code == 200

        data = response.json()
        assert "users" in data
        assert "total_count" in data
        assert len(data["users"]) >= 1  # At least admin user exists

    def test_get_users_with_search(self, client: TestClient, admin_headers: dict):
        """Test user search."""
        response = client.get(
            "/admin-panel/users?search=admin",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "users" in data

    def test_toggle_user_admin(self, client: TestClient, admin_headers: dict, session: Session):
        """Test granting/revoking admin privileges."""
        # Create a regular user
        user = User(
            email="toggle@example.com",
            name="Toggle User",
            hashed_password=hash_password("password"),
            is_admin=False
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        # Grant admin (use query parameter, not JSON body)
        response = client.put(
            f"/admin-panel/users/{user.id}/admin?is_admin=true",
            headers=admin_headers
        )
        assert response.status_code == 200

        # Verify admin granted
        session.refresh(user)
        assert user.is_admin is True

        # Revoke admin
        response = client.put(
            f"/admin-panel/users/{user.id}/admin?is_admin=false",
            headers=admin_headers
        )
        assert response.status_code == 200

        session.refresh(user)
        assert user.is_admin is False

    def test_delete_user(self, client: TestClient, admin_headers: dict, session: Session):
        """Test deleting a user."""
        # Create user to delete
        user = User(
            email="delete@example.com",
            name="Delete User",
            hashed_password=hash_password("password")
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        user_id = user.id

        response = client.delete(
            f"/admin-panel/users/{user_id}",
            headers=admin_headers
        )
        assert response.status_code == 200

        # Verify user soft deleted (is_active = False, not actually deleted)
        session.expire(user)  # Expire to force reload
        deleted_user = session.get(User, user_id)
        assert deleted_user is not None
        assert deleted_user.is_active is False


class TestSourceManagement:
    """Test source management endpoints."""

    def test_get_sources(self, client: TestClient, admin_headers: dict):
        """Test getting list of sources."""
        response = client.get("/admin-panel/sources", headers=admin_headers)
        assert response.status_code == 200

        data = response.json()
        assert "sources" in data
        assert "total_count" in data

    def test_update_source(self, client: TestClient, admin_headers: dict, session: Session):
        """Test updating a source."""
        # Create a source
        source = Source(
            name="Test Source",
            url="https://test.com",
            rss_feed_url="https://test.com/feed",
            is_active=True
        )
        session.add(source)
        session.commit()
        session.refresh(source)

        # Update source (use query parameters, not JSON body)
        response = client.put(
            f"/admin-panel/sources/{source.id}?is_active=false&trust_score=0.8",
            headers=admin_headers
        )
        assert response.status_code == 200

        # Verify update
        session.expire(source)  # Expire to force reload
        session.refresh(source)
        assert source.is_active is False
        assert source.trust_score == 0.8

    def test_delete_source(self, client: TestClient, admin_headers: dict, session: Session):
        """Test deleting a source."""
        # Create source
        source = Source(
            name="Delete Source",
            url="https://delete.com",
            rss_feed_url="https://delete.com/feed"
        )
        session.add(source)
        session.commit()
        session.refresh(source)
        source_id = source.id

        response = client.delete(
            f"/admin-panel/sources/{source_id}",
            headers=admin_headers
        )
        assert response.status_code == 200

        # Verify soft deletion (is_active = False)
        session.expire(source)  # Expire to force reload
        deleted_source = session.get(Source, source_id)
        assert deleted_source is not None
        assert deleted_source.is_active is False


class TestArticleManagement:
    """Test article management endpoints."""

    def test_get_articles(self, client: TestClient, admin_headers: dict):
        """Test getting list of articles."""
        response = client.get("/admin-panel/articles", headers=admin_headers)
        assert response.status_code == 200

        data = response.json()
        assert "articles" in data
        assert "total_count" in data

    def test_get_articles_with_filters(self, client: TestClient, admin_headers: dict):
        """Test article filtering."""
        response = client.get(
            "/admin-panel/articles?processing_status=COMPLETED&page_size=10",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page_size"] == 10

    def test_delete_article(self, client: TestClient, admin_headers: dict, session: Session):
        """Test deleting an article."""
        # Create source and article
        source = Source(
            name="Test Source",
            url="https://test.com",
            rss_feed_url="https://test.com/feed"
        )
        session.add(source)
        session.commit()

        article = Article(
            title="Test Article",
            url="https://test.com/article",
            source_id=source.id,
            published_at=datetime.utcnow(),
            scraped_at=datetime.utcnow()
        )
        session.add(article)
        session.commit()
        session.refresh(article)
        article_id = article.id

        response = client.delete(
            f"/admin-panel/articles/{article_id}",
            headers=admin_headers
        )
        assert response.status_code == 200

        # Verify deletion
        deleted_article = session.get(Article, article_id)
        assert deleted_article is None


class TestAuditLog:
    """Test audit log endpoint."""

    def test_get_audit_log(self, client: TestClient, admin_headers: dict):
        """Test getting audit log."""
        response = client.get("/admin-panel/audit", headers=admin_headers)
        assert response.status_code == 200

        data = response.json()
        assert "audit_logs" in data
        assert "total_count" in data

    def test_get_audit_log_with_filters(self, client: TestClient, admin_headers: dict):
        """Test audit log with filters."""
        response = client.get(
            "/admin-panel/audit?action_type=delete_user&page_size=20",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page_size"] == 20
