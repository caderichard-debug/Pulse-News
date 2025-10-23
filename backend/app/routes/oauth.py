"""
OAuth authentication routes for Google sign-in.
Handles OAuth callbacks, account linking, and token management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import Dict, Any, Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
import logging

from ..database import get_session
from ..models import User, OAuthAccount
from ..services.oauth_service import OAuthService
from .auth import get_current_user

router = APIRouter(prefix="/auth/oauth", tags=["oauth authentication"])
logger = logging.getLogger(__name__)


# Request/Response Models
class OAuthSignInRequest(BaseModel):
    """Request model for Google OAuth sign-in."""
    provider_user_id: str = Field(..., description="Google-specific user ID")
    email: EmailStr = Field(..., description="User email from Google")
    name: Optional[str] = Field(default=None, description="User name from Google")
    avatar_url: Optional[str] = Field(default=None, description="Avatar URL from Google")
    access_token: Optional[str] = Field(default=None, description="OAuth access token")
    refresh_token: Optional[str] = Field(default=None, description="OAuth refresh token")
    token_expires_at: Optional[datetime] = Field(default=None, description="Token expiration time")
    provider_data: Optional[Dict[str, Any]] = Field(default=None, description="Additional Google provider data")


class OAuthLinkRequest(BaseModel):
    """Request model for linking Google OAuth account."""
    provider_user_id: str = Field(..., description="Google-specific user ID")
    access_token: Optional[str] = Field(default=None, description="OAuth access token")
    refresh_token: Optional[str] = Field(default=None, description="OAuth refresh token")
    token_expires_at: Optional[datetime] = Field(default=None, description="Token expiration time")
    provider_data: Optional[Dict[str, Any]] = Field(default=None, description="Additional Google provider data")


class OAuthTokenUpdateRequest(BaseModel):
    """Request model for updating OAuth tokens."""
    access_token: Optional[str] = Field(default=None, description="New access token")
    refresh_token: Optional[str] = Field(default=None, description="New refresh token")
    token_expires_at: Optional[datetime] = Field(default=None, description="New token expiration time")


class OAuthAccountResponse(BaseModel):
    """Response model for OAuth account information."""
    provider: str
    provider_user_id: str
    created_at: datetime
    updated_at: datetime
    has_tokens: bool


class AuthResponse(BaseModel):
    """Standard authentication response."""
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]


@router.post("/signin", response_model=AuthResponse, status_code=status.HTTP_200_OK)
async def oauth_signin(
    request: OAuthSignInRequest,
    session: Session = Depends(get_session)
):
    """
    Sign in or sign up user using Google OAuth.

    Handles both new user creation and existing user sign-in.
    Automatically creates default topic preferences for new users.
    """
    try:
        oauth_service = OAuthService(session)

        # Find or create user (Google is hardcoded as provider)
        user, created = oauth_service.find_or_create_oauth_user(
            provider="google",
            provider_user_id=request.provider_user_id,
            email=request.email,
            name=request.name,
            avatar_url=request.avatar_url,
            provider_data=request.provider_data
        )

        # Update OAuth tokens if provided
        if request.access_token:
            oauth_service.update_oauth_tokens(
                user_id=user.id,
                provider="google",
                access_token=request.access_token,
                refresh_token=request.refresh_token,
                token_expires_at=request.token_expires_at
            )

        # Update last login
        user.last_login = datetime.utcnow()
        session.add(user)
        session.commit()

        # Create JWT token
        access_token = oauth_service.create_auth_token_for_user(user)

        action = "created" if created else "signed in"
        logger.info(f"User {action} via Google OAuth: {user.email}")

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "email_verified": user.email_verified,
                "is_admin": user.is_admin,
                "oauth_provider": user.oauth_provider,
                "oauth_avatar_url": user.oauth_avatar_url,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "new_user": created
            }
        }

    except ValueError as e:
        logger.warning(f"OAuth sign-in validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Google OAuth sign-in error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Google OAuth sign-in failed: {str(e)}"
        )


@router.post("/link", response_model=OAuthAccountResponse)
async def link_oauth_account(
    request: OAuthLinkRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Link Google OAuth account to authenticated user.

    Allows users to connect Google OAuth to their existing account.
    """
    try:
        oauth_service = OAuthService(session)

        # Check if user already has Google linked
        existing_accounts = oauth_service.get_user_oauth_accounts(current_user.id)
        for account in existing_accounts:
            if account.provider == "google":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Google account is already linked"
                )

        # Link Google OAuth account
        oauth_account = oauth_service.link_oauth_account(
            user_id=current_user.id,
            provider="google",
            provider_user_id=request.provider_user_id,
            provider_data=request.provider_data,
            access_token=request.access_token,
            refresh_token=request.refresh_token,
            token_expires_at=request.token_expires_at
        )

        logger.info(f"Linked Google account to user: {current_user.email}")

        return OAuthAccountResponse(
            provider=oauth_account.provider,
            provider_user_id=oauth_account.provider_user_id,
            created_at=oauth_account.created_at,
            updated_at=oauth_account.updated_at,
            has_tokens=bool(oauth_account.access_token)
        )

    except ValueError as e:
        logger.warning(f"OAuth link validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"OAuth link error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to link OAuth account: {str(e)}"
        )


@router.delete("/unlink/{provider}")
async def unlink_oauth_account(
    provider: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Unlink OAuth account from authenticated user.

    Removes the connection between the user account and the OAuth provider.
    Users must have at least one authentication method remaining.
    """
    try:
        # Validate provider
        if provider not in ["google", "apple"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported OAuth provider: {provider}"
            )

        oauth_service = OAuthService(session)

        # Check if provider is linked
        existing_accounts = oauth_service.get_user_oauth_accounts(current_user.id)
        provider_linked = any(account.provider == provider for account in existing_accounts)

        if not provider_linked:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No {provider} account linked to this user"
            )

        # Unlink OAuth account
        success = oauth_service.unlink_oauth_account(current_user.id, provider)

        if success:
            logger.info(f"Unlinked {provider} account from user: {current_user.email}")
            return {"message": f"Successfully unlinked {provider} account"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to unlink OAuth account"
            )

    except ValueError as e:
        logger.warning(f"OAuth unlink validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"OAuth unlink error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unlink OAuth account: {str(e)}"
        )


@router.get("/accounts", response_model=list[OAuthAccountResponse])
async def get_linked_oauth_accounts(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Get all OAuth accounts linked to the authenticated user.
    """
    try:
        oauth_service = OAuthService(session)
        oauth_accounts = oauth_service.get_user_oauth_accounts(current_user.id)

        return [
            OAuthAccountResponse(
                provider=account.provider,
                provider_user_id=account.provider_user_id,
                created_at=account.created_at,
                updated_at=account.updated_at,
                has_tokens=bool(account.access_token)
            )
            for account in oauth_accounts
        ]

    except Exception as e:
        logger.error(f"Error getting OAuth accounts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve OAuth accounts"
        )


@router.put("/tokens/{provider}")
async def update_oauth_tokens(
    provider: str,
    request: OAuthTokenUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Update OAuth tokens for a linked provider account.

    Used for token refresh and updating expired tokens.
    """
    try:
        # Validate provider
        if provider not in ["google", "apple"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported OAuth provider: {provider}"
            )

        oauth_service = OAuthService(session)

        # Update tokens
        success = oauth_service.update_oauth_tokens(
            user_id=current_user.id,
            provider=provider,
            access_token=request.access_token,
            refresh_token=request.refresh_token,
            token_expires_at=request.token_expires_at
        )

        if success:
            logger.info(f"Updated OAuth tokens for {provider}, user: {current_user.email}")
            return {"message": "OAuth tokens updated successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No {provider} account linked to this user"
            )

    except Exception as e:
        logger.error(f"Error updating OAuth tokens: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update OAuth tokens"
        )


@router.get("/providers")
async def get_supported_oauth_providers():
    """
    Get list of supported OAuth providers and their configuration requirements.
    """
    return {
        "providers": [
            {
                "name": "google",
                "display_name": "Google",
                "description": "Sign in with your Google account",
                "scopes": ["openid", "email", "profile"],
                "requires_client_secret": True
            },
            {
                "name": "apple",
                "display_name": "Apple",
                "description": "Sign in with your Apple ID",
                "scopes": ["name", "email"],
                "requires_client_secret": True
            }
        ]
    }


@router.post("/verify/{provider}")
async def verify_oauth_account(
    provider: str,
    provider_data: Dict[str, Any],
    session: Session = Depends(get_session)
):
    """
    Verify OAuth account information without creating user account.

    Used to check if an OAuth account is already linked to another user
    before proceeding with account linking.
    """
    try:
        # Validate provider
        if provider not in ["google", "apple"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported OAuth provider: {provider}"
            )

        provider_user_id = provider_data.get("provider_user_id")
        if not provider_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="provider_user_id is required"
            )

        oauth_service = OAuthService(session)
        existing_user = oauth_service.find_user_by_oauth(provider, provider_user_id)

        if existing_user:
            return {
                "already_linked": True,
                "user_info": {
                    "id": existing_user.id,
                    "email": existing_user.email,
                    "name": existing_user.name
                }
            }
        else:
            return {"already_linked": False}

    except Exception as e:
        logger.error(f"Error verifying OAuth account: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify OAuth account"
        )