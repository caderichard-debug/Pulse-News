"""
Authentication routes: user registration, login, and email verification.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select
from app.database import get_session
from app.models import User, UserTopicPreference, Topic
from app.utils.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_verification_token,
    decode_access_token
)
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
import logging

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()
logger = logging.getLogger(__name__)


# Request/Response Models
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    topic_ids: Optional[List[int]] = Field(default=None, description="Initial topic preferences")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class VerifyEmailRequest(BaseModel):
    token: str


# Helper function to get current user from token
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.
    Usage: current_user: User = Depends(get_current_user)
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    email = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    user = session.exec(select(User).where(User.email == email)).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )

    return user


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(
    request: RegisterRequest,
    session: Session = Depends(get_session)
):
    """
    Register a new user account.

    - **name**: User's full name
    - **email**: Valid email address (must be unique)
    - **password**: Minimum 8 characters
    - **topic_ids**: Optional list of topic IDs for initial preferences
    """
    # Check if user already exists
    existing_user = session.exec(
        select(User).where(User.email == request.email)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user
    user = User(
        email=request.email,
        hashed_password=hash_password(request.password),
        is_active=True,
        email_verified=False  # Requires verification
    )

    session.add(user)
    session.flush()  # Get user.id

    # Set up default topic preferences
    topic_ids = request.topic_ids

    if not topic_ids:
        # If no preferences provided, subscribe to all topics
        all_topics = session.exec(select(Topic)).all()
        topic_ids = [topic.id for topic in all_topics]

    for topic_id in topic_ids:
        # Verify topic exists
        topic = session.get(Topic, topic_id)
        if topic:
            preference = UserTopicPreference(
                user_id=user.id,
                topic_id=topic_id,
                priority=5,  # Default priority
                is_active=True
            )
            session.add(preference)

    session.commit()
    session.refresh(user)

    # Create access token
    access_token = create_access_token(data={"sub": user.email})

    # TODO: Send verification email
    logger.info(f"New user registered: {user.email}")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "email_verified": user.email_verified
        }
    }


@router.post("/login", response_model=AuthResponse)
def login(
    request: LoginRequest,
    session: Session = Depends(get_session)
):
    """
    Login with email and password.

    Returns a JWT access token for authenticated requests.
    """
    # Find user
    user = session.exec(
        select(User).where(User.email == request.email)
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Verify password
    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Check if account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )

    # Update last login
    user.last_login = datetime.utcnow()
    session.add(user)
    session.commit()

    # Create access token
    access_token = create_access_token(data={"sub": user.email})

    logger.info(f"User logged in: {user.email}")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "email_verified": user.email_verified
        }
    }


@router.get("/me")
def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user information from JWT token.

    Requires: Authorization header with Bearer token
    """
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "email_verified": current_user.email_verified,
        "created_at": current_user.created_at,
        "last_login": current_user.last_login
    }


@router.post("/verify-email")
def verify_email(
    request: VerifyEmailRequest,
    session: Session = Depends(get_session)
):
    """
    Verify email address using token sent via email.

    Token is valid for 24 hours.
    """
    payload = decode_access_token(request.token)

    if not payload or payload.get("purpose") != "verify_email":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )

    email = payload.get("sub")
    user = session.exec(select(User).where(User.email == email)).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if user.email_verified:
        return {"message": "Email already verified"}

    # Mark as verified
    user.email_verified = True
    session.add(user)
    session.commit()

    logger.info(f"Email verified for user: {user.email}")

    return {"message": "Email verified successfully"}


@router.post("/logout")
def logout():
    """
    Logout endpoint (for client-side token deletion).

    Since we're using stateless JWT, actual logout happens client-side
    by deleting the token. This endpoint is provided for consistency.
    """
    return {"message": "Logged out successfully"}
