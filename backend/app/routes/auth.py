"""
Authentication routes: user registration, login, and email verification.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select
from ..database import get_session
from ..models import User, UserTopicPreference, Topic
from ..utils.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_verification_token,
    decode_access_token
)
from ..services.email_service import send_verification_email, send_welcome_email
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
    name: Optional[str] = Field(default=None, description="User's full name")
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


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    session: Session = Depends(get_session)
) -> Optional[User]:
    """
    Dependency to optionally get the current user from JWT token.
    Returns None if no token is provided or if token is invalid.
    Usage: current_user: Optional[User] = Depends(get_optional_user)
    """
    if not credentials:
        return None

    try:
        token = credentials.credentials
        payload = decode_access_token(token)

        if not payload:
            return None

        email = payload.get("sub")
        if not email:
            return None

        user = session.exec(select(User).where(User.email == email)).first()

        if not user or not user.is_active:
            return None

        return user
    except Exception:
        return None


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
        name=request.name,
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

    # Send verification email
    verification_token = create_verification_token(user.email)
    verification_sent = send_verification_email(
        email=user.email,
        user_name=user.name or user.email,
        verification_token=verification_token
    )

    # Send welcome email
    welcome_sent = send_welcome_email(
        email=user.email,
        user_name=user.name or user.email
    )

    if verification_sent and welcome_sent:
        logger.info(f"New user registered, verification and welcome emails sent: {user.email}")
    elif verification_sent:
        logger.warning(f"New user registered, verification email sent but welcome email failed: {user.email}")
    elif welcome_sent:
        logger.warning(f"New user registered, welcome email sent but verification email failed: {user.email}")
    else:
        logger.warning(f"New user registered but both emails failed: {user.email}")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "email_verified": user.email_verified,
            "is_admin": user.is_admin
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
            "email_verified": user.email_verified,
            "is_admin": user.is_admin
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
        "is_admin": current_user.is_admin,
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


@router.post("/resend-verification-email")
def resend_verification_email(
    current_user: User = Depends(get_current_user)
):
    """
    Resend email verification link to current user.

    Requires: Authorization header with Bearer token
    """
    if current_user.email_verified:
        return {"message": "Email already verified"}

    # Create and send new verification token
    verification_token = create_verification_token(current_user.email)
    email_sent = send_verification_email(
        email=current_user.email,
        user_name=current_user.name or current_user.email,
        verification_token=verification_token
    )

    if not email_sent:
        # In development, log the verification link for manual testing
        from ..config import settings
        if settings.environment == "development":
            verification_link = f"{settings.frontend_url}/verify-email?token={verification_token}"
            logger.warning(
                f"Email sending failed for {current_user.email}. "
                f"Development verification link: {verification_link}"
            )
            return {
                "message": "Email sending failed (development mode). Check server logs for verification link.",
                "dev_link": verification_link if settings.debug else None
            }

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email. Please try again later."
        )

    logger.info(f"Verification email resent to: {current_user.email}")

    return {"message": "Verification email sent successfully"}


@router.post("/logout")
def logout():
    """
    Logout endpoint (for client-side token deletion).

    Since we're using stateless JWT, actual logout happens client-side
    by deleting the token. This endpoint is provided for consistency.
    """
    return {"message": "Logged out successfully"}


@router.delete("/account", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Delete the authenticated user's account and all associated data.

    This is a permanent, destructive operation that:
    - Deletes user topic preferences
    - Deletes user source subscriptions
    - Deletes newsletters associated with the user
    - Deletes user favorites
    - Deletes password reset tokens
    - Deletes the user account itself

    Requires: Authorization header with Bearer token
    Returns: 204 No Content on success
    """
    from ..models import Newsletter, UserSourceSubscription, ArticleFavorite, PasswordResetToken

    try:
        # Delete user topic preferences
        for pref in session.exec(
            select(UserTopicPreference).where(UserTopicPreference.user_id == current_user.id)
        ):
            session.delete(pref)

        # Delete user source subscriptions
        for subscription in session.exec(
            select(UserSourceSubscription).where(UserSourceSubscription.user_id == current_user.id)
        ):
            session.delete(subscription)

        # Delete user favorites
        for favorite in session.exec(
            select(ArticleFavorite).where(ArticleFavorite.user_id == current_user.id)
        ):
            session.delete(favorite)

        # Delete newsletters
        for newsletter in session.exec(
            select(Newsletter).where(Newsletter.user_id == current_user.id)
        ):
            session.delete(newsletter)

        # Delete password reset tokens
        for token in session.exec(
            select(PasswordResetToken).where(PasswordResetToken.user_id == current_user.id)
        ):
            session.delete(token)

        # Finally, delete the user
        session.delete(current_user)
        session.commit()

        logger.info(f"Account deleted for user: {current_user.email}")

    except Exception as e:
        session.rollback()
        logger.error(f"Error deleting account for user {current_user.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete account. Please try again later."
        )

    return None
