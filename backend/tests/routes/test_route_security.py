"""Regression tests for route access control and route ordering."""

import pytest
from starlette.routing import Match

from app.main import app
from app.models import User
from app.utils.auth import create_access_token


def _headers(session, email, **fields):
    session.add(User(email=email, hashed_password="x", email_verified=True, **fields))
    session.commit()
    return {"Authorization": f"Bearer {create_access_token({'sub': email})}"}


@pytest.mark.parametrize("path", [
    "/test/send-email",
    "/test/send-newsletter",
    "/test/send-welcome",
])
def test_test_email_routes_are_admin_only(client, session, path):
    """Regular users must not be able to send email to arbitrary addresses."""
    headers = _headers(session, "regular@example.com")
    response = client.post(path, headers=headers, json={"to_email": "anyone@example.com"})
    assert response.status_code == 403


@pytest.mark.parametrize("path,expected", [
    ("/challenge/my-responses", "/challenge/my-responses"),
    ("/challenge/statistics", "/challenge/statistics"),
    ("/challenge/assignments", "/challenge/assignments"),
    ("/challenge/responses", "/challenge/responses"),
    ("/challenge/analytics", "/challenge/analytics"),
    ("/challenge/current", "/challenge/current"),
    ("/challenge/2024-01-15", "/challenge/{week_date}"),
])
def test_challenge_fixed_paths_are_not_captured_by_week_date(path, expected):
    scope = {"type": "http", "path": path, "method": "GET"}
    matched = next(r.path for r in app.routes if r.matches(scope)[0] == Match.FULL)
    assert matched == expected


def test_email_verification_token_is_not_a_login_token(client, session):
    from app.utils.auth import create_verification_token
    session.add(User(email="person@example.com", hashed_password="x", email_verified=False))
    session.commit()

    token = create_verification_token("person@example.com")
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401


def test_password_reset_requests_are_rate_limited(client, monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "auth_rate_limit_max_attempts", 2)
    body = {"email": "someone@example.com"}

    assert client.post("/auth/request-password-reset", json=body).status_code == 200
    assert client.post("/auth/request-password-reset", json=body).status_code == 200
    assert client.post("/auth/request-password-reset", json=body).status_code == 429


def test_reset_token_not_logged_outside_development(client, session, monkeypatch, caplog):
    import logging
    from app.config import settings
    session.add(User(email="reset@example.com", hashed_password="x", email_verified=True, is_active=True))
    session.commit()
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr("app.services.email_service.send_password_reset_email", lambda **kw: False)

    with caplog.at_level(logging.INFO):
        client.post("/auth/request-password-reset", json={"email": "reset@example.com"})

    assert "Reset token" not in caplog.text
