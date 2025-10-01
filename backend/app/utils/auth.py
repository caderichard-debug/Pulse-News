"""
Authentication utilities: password hashing, JWT tokens, and user verification.
"""

from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import jwt
from app.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Dict with user data to encode (typically {"sub": user_email})
        expires_delta: Token expiration time (default: 7 days)

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm="HS256"
    )

    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and verify a JWT token.

    Returns:
        Dict with token data if valid, None if invalid/expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=["HS256"]
        )
        return payload
    except jwt.PyJWTError:
        return None


def create_verification_token(email: str) -> str:
    """Create a token for email verification (expires in 24 hours)"""
    return create_access_token(
        data={"sub": email, "purpose": "verify_email"},
        expires_delta=timedelta(hours=24)
    )


def create_password_reset_token(email: str) -> str:
    """Create a token for password reset (expires in 1 hour)"""
    return create_access_token(
        data={"sub": email, "purpose": "reset_password"},
        expires_delta=timedelta(hours=1)
    )
