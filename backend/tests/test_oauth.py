"""
OAuth tests: OAuthService behaviour and the Google authorization-code flow.

All tests use the in-memory SQLite session from conftest (never the app database).
"""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlparse

import pytest
from sqlmodel import Session

from app.models import OAuthAccount, User
from app.services.oauth_service import OAuthService
from app.utils.auth import create_access_token, decode_access_token, hash_password


@pytest.fixture
def oauth_service(session: Session) -> OAuthService:
    return OAuthService(session)


@pytest.fixture
def google_user() -> dict:
    return {
        "provider_user_id": "google_123456789",
        "email": "test@example.com",
        "name": "Test User",
        "avatar_url": "https://lh3.googleusercontent.com/photo.jpg",
        "provider_data": {"verified_email": True, "locale": "en"},
    }


def _password_user(session: Session, email: str, verified: bool) -> User:
    user = User(
        email=email,
        name="Existing User",
        hashed_password=hash_password("password123"),
        email_verified=verified,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


class TestOAuthService:
    def test_creates_new_user(self, oauth_service, google_user):
        user, created = oauth_service.find_or_create_oauth_user(provider="google", **google_user)

        assert created is True
        assert user.email == google_user["email"]
        assert user.oauth_provider == "google"
        assert user.oauth_provider_id == google_user["provider_user_id"]
        assert user.email_verified is True
        assert user.passwordless_login_enabled is True
        accounts = oauth_service.get_user_oauth_accounts(user.id)
        assert [a.provider for a in accounts] == ["google"]

    def test_finds_existing_oauth_user(self, oauth_service, google_user):
        user1, _ = oauth_service.find_or_create_oauth_user(provider="google", **google_user)
        user2, created = oauth_service.find_or_create_oauth_user(provider="google", **google_user)

        assert created is False
        assert user1.id == user2.id

    def test_links_into_verified_password_account_and_keeps_password(
        self, oauth_service, google_user, session
    ):
        existing = _password_user(session, google_user["email"], verified=True)
        original_hash = existing.hashed_password

        user, _ = oauth_service.find_or_create_oauth_user(provider="google", **google_user)

        assert user.id == existing.id
        assert user.oauth_provider == "google"
        assert user.hashed_password == original_hash

    def test_linking_unverified_password_account_clears_password(
        self, oauth_service, google_user, session
    ):
        """
        Account pre-hijacking: someone registers the victim's email with a password
        but never verifies it. When the real owner signs in with Google, the account
        must not stay reachable with the squatter's password.
        """
        squatted = _password_user(session, google_user["email"], verified=False)

        user, _ = oauth_service.find_or_create_oauth_user(provider="google", **google_user)

        assert user.id == squatted.id
        assert user.email_verified is True
        assert user.hashed_password == ""

    def test_link_rejects_account_owned_by_other_user(self, oauth_service, google_user):
        oauth_service.find_or_create_oauth_user(provider="google", **google_user)

        with pytest.raises(ValueError, match="already linked to another user"):
            oauth_service.link_oauth_account(
                user_id=999, provider="google", provider_user_id=google_user["provider_user_id"]
            )

    def test_unlink_when_user_has_password(self, oauth_service, google_user, session):
        _password_user(session, google_user["email"], verified=True)
        user, _ = oauth_service.find_or_create_oauth_user(provider="google", **google_user)

        assert oauth_service.unlink_oauth_account(user.id, "google") is True
        assert oauth_service.get_user_oauth_accounts(user.id) == []
        session.refresh(user)
        assert user.oauth_provider is None
        assert user.oauth_provider_id is None

    def test_cannot_unlink_only_auth_method(self, oauth_service, google_user):
        user, _ = oauth_service.find_or_create_oauth_user(provider="google", **google_user)

        with pytest.raises(ValueError, match="Cannot unlink the only authentication method"):
            oauth_service.unlink_oauth_account(user.id, "google")

    def test_update_tokens(self, oauth_service, google_user):
        user, _ = oauth_service.find_or_create_oauth_user(provider="google", **google_user)

        assert oauth_service.update_oauth_tokens(
            user_id=user.id,
            provider="google",
            access_token="ya29.new_token",
            refresh_token="new_refresh_token",
            token_expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        account = oauth_service.get_user_oauth_accounts(user.id)[0]
        assert account.access_token == "ya29.new_token"
        assert account.refresh_token == "new_refresh_token"

    def test_find_user_by_oauth(self, oauth_service, google_user):
        user, _ = oauth_service.find_or_create_oauth_user(provider="google", **google_user)

        assert oauth_service.find_user_by_oauth("google", google_user["provider_user_id"]).id == user.id
        assert oauth_service.find_user_by_oauth("google", "non_existent_id") is None


def _google_responses(user_info: dict):
    token_response = Mock(ok=True)
    token_response.json.return_value = {
        "access_token": "ya29.token",
        "refresh_token": "refresh",
        "expires_in": 3600,
    }
    userinfo_response = Mock(ok=True)
    userinfo_response.json.return_value = user_info
    return token_response, userinfo_response


class TestGoogleCallback:
    def _callback(self, client, user_info):
        token_response, userinfo_response = _google_responses(user_info)
        with patch("app.routes.oauth.requests.post", return_value=token_response), \
             patch("app.routes.oauth.requests.get", return_value=userinfo_response):
            return client.get(
                "/auth/oauth/google/callback?code=abc&state=login", follow_redirects=False
            )

    def test_successful_sign_in_redirects_with_token(self, client, session):
        response = self._callback(client, {
            "id": "g-1", "email": "new@example.com", "name": "New", "verified_email": True,
        })

        assert response.status_code in (302, 307)
        query = parse_qs(urlparse(response.headers["location"]).query)
        payload = decode_access_token(query["token"][0])
        assert payload["sub"] == "new@example.com"
        assert query["new_user"] == ["True"]
        account = session.query(OAuthAccount).one()
        assert account.access_token == "ya29.token"

    def test_unverified_google_email_is_rejected(self, client, session):
        victim = _password_user(session, "victim@example.com", verified=True)

        response = self._callback(client, {
            "id": "attacker", "email": "victim@example.com", "verified_email": False,
        })

        assert "error=email_not_verified" in response.headers["location"]
        assert "token=" not in response.headers["location"]
        session.refresh(victim)
        assert victim.oauth_provider is None

    def test_user_cancelled(self, client):
        response = client.get(
            "/auth/oauth/google/callback?error=access_denied&state=signup", follow_redirects=False
        )
        assert response.headers["location"].endswith("/signup?error=access_denied")


class TestOAuthRoutes:
    @pytest.mark.parametrize("method,path", [
        ("post", "/auth/oauth/signin"),
        ("post", "/auth/oauth/link"),
        ("post", "/auth/oauth/verify/google"),
    ])
    def test_unverified_identity_endpoints_are_gone(self, client, session, method, path):
        """These accepted client-supplied identity and allowed account takeover."""
        victim = _password_user(session, "victim@example.com", verified=True)
        body = {"provider_user_id": "x", "email": "victim@example.com"}

        response = getattr(client, method)(path, json=body)

        assert response.status_code in (404, 405)
        assert "access_token" not in response.text
        session.refresh(victim)
        assert victim.oauth_provider is None

    def test_get_providers(self, client):
        response = client.get("/auth/oauth/providers")
        assert response.status_code == 200
        names = [p["name"] for p in response.json()["providers"]]
        assert "google" in names

    @pytest.mark.parametrize("method,path", [
        ("delete", "/auth/oauth/unlink/google"),
        ("get", "/auth/oauth/accounts"),
    ])
    def test_account_endpoints_require_auth(self, client, method, path):
        assert getattr(client, method)(path).status_code == 403

    def test_accounts_lists_linked_google(self, client, session, oauth_service, google_user):
        user, _ = oauth_service.find_or_create_oauth_user(provider="google", **google_user)
        headers = {"Authorization": f"Bearer {create_access_token({'sub': user.email})}"}

        response = client.get("/auth/oauth/accounts", headers=headers)

        assert response.status_code == 200
        assert [a["provider"] for a in response.json()] == ["google"]


class TestPasswordLoginForOAuthUsers:
    def test_password_login_for_oauth_only_user_is_401_not_500(
        self, client, oauth_service, google_user
    ):
        oauth_service.find_or_create_oauth_user(provider="google", **google_user)

        response = client.post(
            "/auth/login", json={"email": google_user["email"], "password": "anything"}
        )

        assert response.status_code == 401
