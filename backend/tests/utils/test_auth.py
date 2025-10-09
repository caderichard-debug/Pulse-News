"""
Unit tests for authentication utilities.
"""

import pytest
from datetime import timedelta
from app.utils.auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    create_verification_token,
    create_password_reset_token,
)


class TestPasswordHashing:
    """Test password hashing and verification"""

    def test_hash_password_returns_string(self):
        """Test that hash_password returns a string"""
        password = "securepassword123"
        hashed = hash_password(password)
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_password_creates_different_hashes(self):
        """Test that same password creates different hashes (due to salt)"""
        password = "securepassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Test that verify_password works with correct password"""
        password = "securepassword123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test that verify_password fails with wrong password"""
        password = "securepassword123"
        hashed = hash_password(password)
        assert verify_password("wrongpassword", hashed) is False

    def test_hash_password_handles_long_passwords(self):
        """Test that passwords longer than 72 bytes are truncated"""
        # Create a password longer than 72 bytes
        long_password = "a" * 100
        hashed = hash_password(long_password)

        # Should verify with the truncated version
        assert verify_password(long_password, hashed) is True

        # Should also verify with just the first 72 characters
        assert verify_password("a" * 72, hashed) is True

    def test_hash_password_handles_unicode(self):
        """Test that unicode characters are handled correctly"""
        password = "pássw0rd🔐"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_empty_string(self):
        """Test verification with empty password"""
        password = "test"
        hashed = hash_password(password)
        assert verify_password("", hashed) is False


class TestJWTTokens:
    """Test JWT token creation and decoding"""

    def test_create_access_token_returns_string(self):
        """Test that create_access_token returns a JWT string"""
        token = create_access_token(data={"sub": "test@example.com"})
        assert isinstance(token, str)
        assert len(token) > 0
        # JWT tokens have 3 parts separated by dots
        assert token.count('.') == 2

    def test_create_access_token_encodes_data(self):
        """Test that token contains encoded data"""
        data = {"sub": "test@example.com", "role": "user"}
        token = create_access_token(data=data)
        decoded = decode_access_token(token)

        assert decoded is not None
        assert decoded["sub"] == "test@example.com"
        assert decoded["role"] == "user"
        assert "exp" in decoded  # Expiration should be added

    def test_create_access_token_with_expiration(self):
        """Test custom expiration time"""
        data = {"sub": "test@example.com"}
        token = create_access_token(data=data, expires_delta=timedelta(minutes=30))
        decoded = decode_access_token(token)

        assert decoded is not None
        assert "exp" in decoded

    def test_decode_access_token_valid(self):
        """Test decoding a valid token"""
        data = {"sub": "test@example.com", "user_id": 123}
        token = create_access_token(data=data)
        decoded = decode_access_token(token)

        assert decoded is not None
        assert decoded["sub"] == "test@example.com"
        assert decoded["user_id"] == 123

    def test_decode_access_token_invalid(self):
        """Test decoding an invalid token"""
        invalid_token = "invalid.token.here"
        decoded = decode_access_token(invalid_token)
        assert decoded is None

    def test_decode_access_token_tampered(self):
        """Test decoding a tampered token"""
        data = {"sub": "test@example.com"}
        token = create_access_token(data=data)

        # Tamper with the token
        tampered_token = token[:-5] + "xxxxx"
        decoded = decode_access_token(tampered_token)
        assert decoded is None

    def test_decode_access_token_expired(self):
        """Test decoding an expired token"""
        data = {"sub": "test@example.com"}
        # Create token that expires immediately
        token = create_access_token(data=data, expires_delta=timedelta(seconds=-1))
        decoded = decode_access_token(token)
        assert decoded is None


class TestSpecializedTokens:
    """Test specialized token creation functions"""

    def test_create_verification_token(self):
        """Test email verification token creation"""
        email = "test@example.com"
        token = create_verification_token(email)

        assert isinstance(token, str)
        decoded = decode_access_token(token)

        assert decoded is not None
        assert decoded["sub"] == email
        assert decoded["purpose"] == "verify_email"

    def test_create_password_reset_token(self):
        """Test password reset token creation"""
        email = "test@example.com"
        token = create_password_reset_token(email)

        assert isinstance(token, str)
        decoded = decode_access_token(token)

        assert decoded is not None
        assert decoded["sub"] == email
        assert decoded["purpose"] == "reset_password"

    def test_verification_token_different_from_reset_token(self):
        """Test that verification and reset tokens are different"""
        email = "test@example.com"
        verify_token = create_verification_token(email)
        reset_token = create_password_reset_token(email)

        assert verify_token != reset_token

        verify_decoded = decode_access_token(verify_token)
        reset_decoded = decode_access_token(reset_token)

        assert verify_decoded["purpose"] == "verify_email"
        assert reset_decoded["purpose"] == "reset_password"


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_hash_password_empty_string(self):
        """Test hashing empty password"""
        hashed = hash_password("")
        assert isinstance(hashed, str)
        assert verify_password("", hashed) is True

    def test_create_token_empty_data(self):
        """Test creating token with empty data"""
        token = create_access_token(data={})
        decoded = decode_access_token(token)
        assert decoded is not None
        assert "exp" in decoded

    def test_decode_token_empty_string(self):
        """Test decoding empty string"""
        decoded = decode_access_token("")
        assert decoded is None

    def test_create_token_with_none_values(self):
        """Test creating token with None values"""
        data = {"sub": "test@example.com", "metadata": None}
        token = create_access_token(data=data)
        decoded = decode_access_token(token)

        assert decoded is not None
        assert decoded["sub"] == "test@example.com"
        assert decoded["metadata"] is None
