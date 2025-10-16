"""
Password reset routes: request reset, verify token, reset password.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from ..database import get_session
from ..models import User, PasswordResetToken
from ..utils.auth import hash_password
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
import secrets
import logging

router = APIRouter(prefix="/auth", tags=["password-reset"])
logger = logging.getLogger(__name__)


# Request/Response Models
class RequestPasswordResetRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class MessageResponse(BaseModel):
    message: str


# Token expiry time (1 hour)
TOKEN_EXPIRY_HOURS = 1


def generate_reset_token() -> str:
    """Generate a cryptographically secure random token."""
    return secrets.token_urlsafe(32)


def create_password_reset_token(user_id: int, session: Session) -> str:
    """
    Create a new password reset token for a user.
    Invalidates any existing unused tokens.
    """
    # Invalidate any existing unused tokens for this user
    existing_tokens = session.exec(
        select(PasswordResetToken).where(
            PasswordResetToken.user_id == user_id,
            PasswordResetToken.used == False
        )
    ).all()

    for token in existing_tokens:
        token.used = True
        session.add(token)

    # Generate new token
    token_string = generate_reset_token()
    expires_at = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRY_HOURS)

    reset_token = PasswordResetToken(
        user_id=user_id,
        token=token_string,
        expires_at=expires_at,
        used=False
    )

    session.add(reset_token)
    session.commit()
    session.refresh(reset_token)

    return token_string


def verify_reset_token(token: str, session: Session) -> PasswordResetToken:
    """
    Verify a password reset token is valid and not expired.
    Returns the token if valid, raises HTTPException otherwise.
    """
    reset_token = session.exec(
        select(PasswordResetToken).where(PasswordResetToken.token == token)
    ).first()

    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    if reset_token.used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has already been used"
        )

    if datetime.utcnow() > reset_token.expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired"
        )

    return reset_token


@router.post("/request-password-reset", response_model=MessageResponse)
def request_password_reset(
    request: RequestPasswordResetRequest,
    session: Session = Depends(get_session)
):
    """
    Request a password reset email.

    For security, always returns success even if email doesn't exist.
    This prevents user enumeration attacks.
    """
    # Find user by email
    user = session.exec(
        select(User).where(User.email == request.email)
    ).first()

    if user and user.is_active:
        # Generate reset token
        token = create_password_reset_token(user.id, session)

        # Send password reset email
        from ..services.email_service import send_password_reset_email

        email_sent = send_password_reset_email(
            email=user.email,
            user_name=user.name or user.email,
            reset_token=token
        )

        if email_sent:
            logger.info(f"Password reset email sent to {user.email}")
        else:
            logger.warning(f"Failed to send password reset email to {user.email}")
            # Still log the token for development purposes
            logger.info(f"Reset token (DEV ONLY): {token}")
    else:
        # User doesn't exist or inactive, but don't reveal this
        logger.info(f"Password reset requested for non-existent/inactive email: {request.email}")

    # Always return success to prevent user enumeration
    return {
        "message": "If an account with that email exists, a password reset link has been sent."
    }


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(
    request: ResetPasswordRequest,
    session: Session = Depends(get_session)
):
    """
    Reset password using a valid reset token.

    - **token**: Reset token from email
    - **new_password**: New password (minimum 8 characters recommended)
    """
    # Verify token is valid
    reset_token = verify_reset_token(request.token, session)

    # Get user
    user = session.get(User, reset_token.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )

    # Validate new password (basic validation)
    if len(request.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )

    # Update password
    user.hashed_password = hash_password(request.new_password)
    session.add(user)

    # Mark token as used
    reset_token.used = True
    session.add(reset_token)

    session.commit()

    logger.info(f"Password reset successful for user: {user.email}")

    return {
        "message": "Password has been reset successfully. You can now log in with your new password."
    }


@router.get("/verify-reset-token/{token}")
def verify_reset_token_endpoint(
    token: str,
    session: Session = Depends(get_session)
):
    """
    Verify if a reset token is valid (for frontend validation).

    Returns token info if valid, error if not.
    """
    reset_token = verify_reset_token(token, session)

    return {
        "valid": True,
        "expires_at": reset_token.expires_at,
        "message": "Token is valid"
    }
