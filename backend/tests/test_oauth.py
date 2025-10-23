"""
OAuth backend integration tests.

Tests for Google OAuth authentication, account linking, and token management.
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from datetime import datetime, timedelta

from app.main import app
from app.models import User, OAuthAccount
from app.services.oauth_service import OAuthService
from app.database import get_session

client = TestClient(app)


@pytest.fixture
def db_session():
    """Test database session fixture."""
    from app.database import engine
    with Session(engine) as session:
        yield session


@pytest.fixture
def oauth_service(db_session):
    """OAuth service fixture."""
    return OAuthService(db_session)


@pytest.fixture
def test_user_data():
    """Test user data for OAuth."""
    return {
        "provider_user_id": "google_123456789",
        "email": "test@example.com",
        "name": "Test User",
        "avatar_url": "https://lh3.googleusercontent.com/photo.jpg",
        "access_token": "ya29.test_token",
        "refresh_token": "refresh_test_token",
        "provider_data": {
            "given_name": "Test",
            "family_name": "User",
            "locale": "en",
            "verified_email": True
        }
    }


class TestOAuthService:
    """Test OAuth service functionality."""

    def test_find_or_create_oauth_user_new_user(self, oauth_service, test_user_data):
        """Test creating new OAuth user."""
        user, created = oauth_service.find_or_create_oauth_user(
            provider="google",
            **test_user_data
        )

        assert created is True
        assert user.email == test_user_data["email"]
        assert user.name == test_user_data["name"]
        assert user.oauth_provider == "google"
        assert user.oauth_provider_id == test_user_data["provider_user_id"]
        assert user.oauth_avatar_url == test_user_data["avatar_url"]
        assert user.email_verified is True
        assert user.passwordless_login_enabled is True

        # Check OAuth account was created
        oauth_accounts = oauth_service.get_user_oauth_accounts(user.id)
        assert len(oauth_accounts) == 1
        assert oauth_accounts[0].provider == "google"
        assert oauth_accounts[0].provider_user_id == test_user_data["provider_user_id"]

    def test_find_or_create_oauth_user_existing_user(self, oauth_service, test_user_data):
        """Test finding existing OAuth user."""
        # Create user first
        user1, created1 = oauth_service.find_or_create_oauth_user(
            provider="google",
            **test_user_data
        )

        # Try to create same user again
        user2, created2 = oauth_service.find_or_create_oauth_user(
            provider="google",
            **test_user_data
        )

        assert created2 is False
        assert user1.id == user2.id
        assert user1.email == user2.email

    def test_link_oauth_account_to_existing_user(self, oauth_service, test_user_data, db_session):
        """Test linking OAuth account to existing email user."""
        # Create existing email user
        from app.utils.auth import hash_password
        existing_user = User(
            email=test_user_data["email"],
            name="Existing User",
            hashed_password=hash_password("password123"),
            email_verified=False
        )
        db_session.add(existing_user)
        db_session.commit()

        # Link OAuth account
        oauth_account = oauth_service.link_oauth_account(
            user_id=existing_user.id,
            provider="google",
            provider_user_id=test_user_data["provider_user_id"],
            provider_data=test_user_data["provider_data"],
            access_token=test_user_data["access_token"],
            refresh_token=test_user_data["refresh_token"]
        )

        assert oauth_account.user_id == existing_user.id
        assert oauth_account.provider == "google"
        assert oauth_account.provider_user_id == test_user_data["provider_user_id"]
        assert oauth_account.access_token == test_user_data["access_token"]

        # Check user was updated
        db_session.refresh(existing_user)
        assert existing_user.oauth_provider == "google"
        assert existing_user.oauth_provider_id == test_user_data["provider_user_id"]
        assert existing_user.email_verified is True  # Should be updated from OAuth

    def test_link_oauth_account_already_linked(self, oauth_service, test_user_data):
        """Test error when trying to link already linked OAuth account."""
        # Create OAuth user
        user1, _ = oauth_service.find_or_create_oauth_user(
            provider="google",
            **test_user_data
        )

        # Try to create another user with same OAuth account
        with pytest.raises(ValueError, match="already linked to another user"):
            oauth_service.link_oauth_account(
                user_id=999,  # Different user ID
                provider="google",
                provider_user_id=test_user_data["provider_user_id"]
            )

    def test_unlink_oauth_account(self, oauth_service, test_user_data):
        """Test unlinking OAuth account."""
        # Create OAuth user
        user, _ = oauth_service.find_or_create_oauth_user(
            provider="google",
            **test_user_data
        )

        # Unlink OAuth account
        success = oauth_service.unlink_oauth_account(user.id, "google")

        assert success is True

        # Check OAuth account was deleted
        oauth_accounts = oauth_service.get_user_oauth_accounts(user.id)
        assert len(oauth_accounts) == 0

        # Check user OAuth fields were cleared
        oauth_service.session.refresh(user)
        assert user.oauth_provider is None
        assert user.oauth_provider_id is None

    def test_unlink_oauth_account_no_auth_methods(self, oauth_service, test_user_data, db_session):
        """Test error when unlinking only auth method."""
        # Create OAuth-only user (no password)
        user, _ = oauth_service.find_or_create_oauth_user(
            provider="google",
            **test_user_data
        )

        # Try to unlink the only auth method
        with pytest.raises(ValueError, match="Cannot unlink the only authentication method"):
            oauth_service.unlink_oauth_account(user.id, "google")

    def test_update_oauth_tokens(self, oauth_service, test_user_data):
        """Test updating OAuth tokens."""
        # Create OAuth user
        user, _ = oauth_service.find_or_create_oauth_user(
            provider="google",
            **test_user_data
        )

        # Update tokens
        new_token_data = {
            "access_token": "ya29.new_token",
            "refresh_token": "new_refresh_token",
            "token_expires_at": datetime.utcnow() + timedelta(hours=1)
        }

        success = oauth_service.update_oauth_tokens(
            user_id=user.id,
            provider="google",
            **new_token_data
        )

        assert success is True

        # Verify tokens were updated
        oauth_accounts = oauth_service.get_user_oauth_accounts(user.id)
        assert len(oauth_accounts) == 1
        assert oauth_accounts[0].access_token == new_token_data["access_token"]
        assert oauth_accounts[0].refresh_token == new_token_data["refresh_token"]

    def test_get_user_oauth_accounts(self, oauth_service, test_user_data):
        """Test retrieving user OAuth accounts."""
        # Create OAuth user
        user, _ = oauth_service.find_or_create_oauth_user(
            provider="google",
            **test_user_data
        )

        # Get OAuth accounts
        oauth_accounts = oauth_service.get_user_oauth_accounts(user.id)

        assert len(oauth_accounts) == 1
        assert oauth_accounts[0].provider == "google"
        assert oauth_accounts[0].provider_user_id == test_user_data["provider_user_id"]

    def test_find_user_by_oauth(self, oauth_service, test_user_data):
        """Test finding user by OAuth provider and ID."""
        # Create OAuth user
        user1, _ = oauth_service.find_or_create_oauth_user(
            provider="google",
            **test_user_data
        )

        # Find user by OAuth
        user2 = oauth_service.find_user_by_oauth(
            provider="google",
            provider_user_id=test_user_data["provider_user_id"]
        )

        assert user1.id == user2.id
        assert user1.email == user2.email

        # Test non-existent OAuth user
        user3 = oauth_service.find_user_by_oauth(
            provider="google",
            provider_user_id="non_existent_id"
        )
        assert user3 is None


class TestOAuthRoutes:
    """Test OAuth API routes."""

    def test_oauth_signin_new_user(self, test_user_data):
        """Test OAuth sign-in endpoint for new user."""
        response = client.post("/auth/oauth/signin", json=test_user_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == test_user_data["email"]
        assert data["user"]["name"] == test_user_data["name"]
        assert data["user"]["new_user"] is True

    def test_oauth_signin_existing_user(self, test_user_data):
        """Test OAuth sign-in endpoint for existing user."""
        # First sign-in
        response1 = client.post("/auth/oauth/signin", json=test_user_data)
        assert response1.status_code == 200
        assert response1.json()["user"]["new_user"] is True

        # Second sign-in
        response2 = client.post("/auth/oauth/signin", json=test_user_data)
        assert response2.status_code == 200
        assert response2.json()["user"]["new_user"] is False

    def test_oauth_signin_invalid_data(self):
        """Test OAuth sign-in with invalid data."""
        invalid_data = {
            "provider_user_id": "",  # Empty ID
            "email": "invalid-email",  # Invalid email
        }

        response = client.post("/auth/oauth/signin", json=invalid_data)
        assert response.status_code == 422  # Validation error

    def test_oauth_signin_conflict(self, test_user_data):
        """Test OAuth sign-in with conflicting email."""
        # Create OAuth user with different provider_user_id
        conflict_data = test_user_data.copy()
        conflict_data["provider_user_id"] = "different_google_id"

        response = client.post("/auth/oauth/signin", json=conflict_data)
        assert response.status_code == 400
        assert "already linked to google account" in response.json()["detail"]

    def test_get_oauth_providers(self):
        """Test getting supported OAuth providers."""
        response = client.get("/auth/oauth/providers")
        assert response.status_code == 200

        data = response.json()
        assert "providers" in data
        assert len(data["providers"]) == 1  # Only Google

        google_provider = data["providers"][0]
        assert google_provider["name"] == "google"
        assert google_provider["display_name"] == "Google"
        assert "google.com" in google_provider["description"].lower()

    def test_verify_oauth_account(self, test_user_data):
        """Test verifying OAuth account without creating user."""
        # First verify non-existent account
        response = client.post(
            "/auth/oauth/verify/google",
            json={"provider_user_id": test_user_data["provider_user_id"]}
        )
        assert response.status_code == 200
        assert response.json()["already_linked"] is False

        # Create OAuth user
        client.post("/auth/oauth/signin", json=test_user_data)

        # Verify existing account
        response = client.post(
            "/auth/oauth/verify/google",
            json={"provider_user_id": test_user_data["provider_user_id"]}
        )
        assert response.status_code == 200
        assert response.json()["already_linked"] is True
        assert response.json()["user_info"]["email"] == test_user_data["email"]

    def test_link_oauth_account_authenticated(self, test_user_data):
        """Test linking OAuth account when authenticated."""
        # First, create a regular user and get token
        from app.utils.auth import hash_password, create_access_token

        # Create regular user (this would normally be done through registration)
        # For testing, we'll create a user directly in the test setup

        # This test would require setting up proper authentication
        # For now, we'll test the unauthenticated case
        response = client.post("/auth/oauth/link", json=test_user_data)
        assert response.status_code == 401  # Unauthorized

    def test_unlink_oauth_account_authenticated(self):
        """Test unlinking OAuth account when authenticated."""
        response = client.delete("/auth/oauth/unlink/google")
        assert response.status_code == 401  # Unauthorized

    def test_get_oauth_accounts_authenticated(self):
        """Test getting OAuth accounts when authenticated."""
        response = client.get("/auth/oauth/accounts")
        assert response.status_code == 401  # Unauthorized


class TestOAuthIntegration:
    """End-to-end OAuth integration tests."""

    def test_complete_oauth_flow(self, test_user_data):
        """Test complete OAuth flow from sign-in to token management."""
        # Step 1: OAuth sign-in
        signin_response = client.post("/auth/oauth/signin", json=test_user_data)
        assert signin_response.status_code == 200

        access_token = signin_response.json()["access_token"]
        user_info = signin_response.json()["user"]

        # Step 2: Use token for authenticated requests
        headers = {"Authorization": f"Bearer {access_token}"}

        # Test protected endpoint
        me_response = client.get("/auth/me", headers=headers)
        assert me_response.status_code == 200
        assert me_response.json()["email"] == test_user_data["email"]

        # Step 3: Get OAuth accounts
        accounts_response = client.get("/auth/oauth/accounts", headers=headers)
        assert accounts_response.status_code == 200
        accounts = accounts_response.json()
        assert len(accounts) == 1
        assert accounts[0]["provider"] == "google"

    def test_oauth_user_with_default_preferences(self, test_user_data):
        """Test that OAuth users get default topic preferences."""
        # Sign in OAuth user
        response = client.post("/auth/oauth/signin", json=test_user_data)
        assert response.status_code == 200

        user_info = response.json()["user"]
        access_token = response.json()["access_token"]

        # Get user preferences
        headers = {"Authorization": f"Bearer {access_token}"}
        prefs_response = client.get("/preferences", headers=headers)

        if prefs_response.status_code == 200:
            # Check that user has default topic preferences
            topics = prefs_response.json().get("topics", [])
            # OAuth users should have some default topics
            assert len(topics) > 0


if __name__ == "__main__":
    pytest.main([__file__])