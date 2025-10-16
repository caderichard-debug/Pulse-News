"""
Tests for password reset functionality.
"""

import pytest
from sqlmodel import Session, select
from datetime import datetime, timedelta
from app.models import User, PasswordResetToken
from app.utils.auth import hash_password, verify_password
from app.routes.password_reset import generate_reset_token, create_password_reset_token


@pytest.fixture
def test_user(session: Session):
    """Create a test user for password reset tests."""
    user = User(
        email="reset_test@example.com",
        name="Reset Test User",
        hashed_password=hash_password("oldpassword123"),
        is_active=True,
        email_verified=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


class TestPasswordResetToken:
    """Test password reset token generation and validation."""

    def test_generate_reset_token(self):
        """Test that reset tokens are cryptographically secure."""
        token1 = generate_reset_token()
        token2 = generate_reset_token()

        # Tokens should be different
        assert token1 != token2

        # Tokens should be reasonable length (URL-safe base64)
        assert len(token1) > 20
        assert len(token2) > 20

    def test_create_password_reset_token(self, session: Session, test_user: User):
        """Test creating a password reset token for a user."""
        token = create_password_reset_token(test_user.id, session)

        # Verify token was created in database
        reset_token = session.exec(
            select(PasswordResetToken).where(PasswordResetToken.token == token)
        ).first()

        assert reset_token is not None
        assert reset_token.user_id == test_user.id
        assert reset_token.used == False
        assert reset_token.expires_at > datetime.utcnow()

    def test_invalidate_existing_tokens(self, session: Session, test_user: User):
        """Test that creating a new token invalidates old ones."""
        # Create first token
        token1 = create_password_reset_token(test_user.id, session)

        # Create second token
        token2 = create_password_reset_token(test_user.id, session)

        # First token should be marked as used
        old_token = session.exec(
            select(PasswordResetToken).where(PasswordResetToken.token == token1)
        ).first()

        assert old_token.used == True

        # Second token should be valid
        new_token = session.exec(
            select(PasswordResetToken).where(PasswordResetToken.token == token2)
        ).first()

        assert new_token.used == False


class TestRequestPasswordReset:
    """Test password reset request endpoint."""

    def test_request_reset_existing_user(self, client, session: Session, test_user: User):
        """Test requesting password reset for existing user."""
        response = client.post(
            "/auth/request-password-reset",
            json={"email": test_user.email}
        )

        assert response.status_code == 200
        data = response.json()
        assert "password reset link has been sent" in data["message"].lower()

        # Verify token was created
        token = session.exec(
            select(PasswordResetToken).where(PasswordResetToken.user_id == test_user.id)
        ).first()

        assert token is not None
        assert token.used == False

    def test_request_reset_nonexistent_user(self, client):
        """Test requesting password reset for non-existent user (no user enumeration)."""
        response = client.post(
            "/auth/request-password-reset",
            json={"email": "nonexistent@example.com"}
        )

        # Should still return success to prevent user enumeration
        assert response.status_code == 200
        data = response.json()
        assert "password reset link has been sent" in data["message"].lower()

    def test_request_reset_inactive_user(self, client, session: Session):
        """Test requesting password reset for inactive user."""
        inactive_user = User(
            email="inactive@example.com",
            hashed_password=hash_password("password123"),
            is_active=False
        )
        session.add(inactive_user)
        session.commit()

        response = client.post(
            "/auth/request-password-reset",
            json={"email": inactive_user.email}
        )

        # Should return success but not create token
        assert response.status_code == 200

    def test_request_reset_invalid_email(self, client):
        """Test requesting password reset with invalid email format."""
        response = client.post(
            "/auth/request-password-reset",
            json={"email": "not-an-email"}
        )

        assert response.status_code == 422  # Validation error


class TestResetPassword:
    """Test password reset endpoint."""

    def test_reset_password_valid_token(self, client, session: Session, test_user: User):
        """Test resetting password with valid token."""
        # Create reset token
        token = create_password_reset_token(test_user.id, session)

        # Reset password
        response = client.post(
            "/auth/reset-password",
            json={
                "token": token,
                "new_password": "newpassword123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "reset successfully" in data["message"].lower()

        # Verify password was changed
        session.refresh(test_user)
        assert verify_password("newpassword123", test_user.hashed_password)
        assert not verify_password("oldpassword123", test_user.hashed_password)

        # Verify token was marked as used
        reset_token = session.exec(
            select(PasswordResetToken).where(PasswordResetToken.token == token)
        ).first()
        assert reset_token.used == True

    def test_reset_password_invalid_token(self, client):
        """Test resetting password with invalid token."""
        response = client.post(
            "/auth/reset-password",
            json={
                "token": "invalid_token_12345",
                "new_password": "newpassword123"
            }
        )

        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()

    def test_reset_password_used_token(self, client, session: Session, test_user: User):
        """Test resetting password with already used token."""
        # Create and use token
        token = create_password_reset_token(test_user.id, session)

        # Use token once
        client.post(
            "/auth/reset-password",
            json={
                "token": token,
                "new_password": "newpassword123"
            }
        )

        # Try to use again
        response = client.post(
            "/auth/reset-password",
            json={
                "token": token,
                "new_password": "anotherpassword456"
            }
        )

        assert response.status_code == 400
        assert "already been used" in response.json()["detail"].lower()

    def test_reset_password_expired_token(self, client, session: Session, test_user: User):
        """Test resetting password with expired token."""
        # Create token
        token_string = generate_reset_token()
        expired_token = PasswordResetToken(
            user_id=test_user.id,
            token=token_string,
            expires_at=datetime.utcnow() - timedelta(hours=2),  # Expired 2 hours ago
            used=False
        )
        session.add(expired_token)
        session.commit()

        # Try to reset with expired token
        response = client.post(
            "/auth/reset-password",
            json={
                "token": token_string,
                "new_password": "newpassword123"
            }
        )

        assert response.status_code == 400
        assert "expired" in response.json()["detail"].lower()

    def test_reset_password_too_short(self, client, session: Session, test_user: User):
        """Test resetting password with password that's too short."""
        token = create_password_reset_token(test_user.id, session)

        response = client.post(
            "/auth/reset-password",
            json={
                "token": token,
                "new_password": "short"
            }
        )

        assert response.status_code == 400
        assert "8 characters" in response.json()["detail"].lower()

    def test_reset_password_inactive_user(self, client, session: Session):
        """Test resetting password for inactive user."""
        inactive_user = User(
            email="inactive2@example.com",
            hashed_password=hash_password("password123"),
            is_active=False
        )
        session.add(inactive_user)
        session.commit()
        session.refresh(inactive_user)

        # Create token
        token = create_password_reset_token(inactive_user.id, session)

        # Try to reset
        response = client.post(
            "/auth/reset-password",
            json={
                "token": token,
                "new_password": "newpassword123"
            }
        )

        assert response.status_code == 403
        assert "inactive" in response.json()["detail"].lower()


class TestVerifyResetToken:
    """Test reset token verification endpoint."""

    def test_verify_valid_token(self, client, session: Session, test_user: User):
        """Test verifying a valid reset token."""
        token = create_password_reset_token(test_user.id, session)

        response = client.get(f"/auth/verify-reset-token/{token}")

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == True
        assert "expires_at" in data

    def test_verify_invalid_token(self, client):
        """Test verifying an invalid token."""
        response = client.get("/auth/verify-reset-token/invalid_token_123")

        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()

    def test_verify_expired_token(self, client, session: Session, test_user: User):
        """Test verifying an expired token."""
        token_string = generate_reset_token()
        expired_token = PasswordResetToken(
            user_id=test_user.id,
            token=token_string,
            expires_at=datetime.utcnow() - timedelta(hours=1),
            used=False
        )
        session.add(expired_token)
        session.commit()

        response = client.get(f"/auth/verify-reset-token/{token_string}")

        assert response.status_code == 400
        assert "expired" in response.json()["detail"].lower()


class TestPasswordResetIntegration:
    """Integration tests for complete password reset flow."""

    def test_complete_password_reset_flow(self, client, session: Session, test_user: User):
        """Test complete password reset flow from request to reset."""
        # 1. Request password reset
        response = client.post(
            "/auth/request-password-reset",
            json={"email": test_user.email}
        )
        assert response.status_code == 200

        # 2. Get the token from database (in real app, user gets this via email)
        token_record = session.exec(
            select(PasswordResetToken)
            .where(PasswordResetToken.user_id == test_user.id)
            .where(PasswordResetToken.used == False)
        ).first()
        assert token_record is not None
        token = token_record.token

        # 3. Verify token is valid
        response = client.get(f"/auth/verify-reset-token/{token}")
        assert response.status_code == 200

        # 4. Reset password
        new_password = "brandnewpassword123"
        response = client.post(
            "/auth/reset-password",
            json={
                "token": token,
                "new_password": new_password
            }
        )
        assert response.status_code == 200

        # 5. Login with new password
        response = client.post(
            "/auth/login",
            json={
                "email": test_user.email,
                "password": new_password
            }
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

        # 6. Old password should not work
        response = client.post(
            "/auth/login",
            json={
                "email": test_user.email,
                "password": "oldpassword123"
            }
        )
        assert response.status_code == 401
