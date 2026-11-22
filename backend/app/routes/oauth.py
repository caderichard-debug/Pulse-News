"""
OAuth authentication routes for Google sign-in.
Handles OAuth initiation, callbacks, account linking, and token management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlmodel import Session
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import logging
import urllib.parse
import os
import requests
from ..config import settings

from ..database import get_session
from ..models import User
from ..services.oauth_service import OAuthService
from .auth import get_current_user

router = APIRouter(prefix="/auth/oauth", tags=["oauth authentication"])
logger = logging.getLogger(__name__)


def _get_oauth_backend_base_url() -> str:
    """
    Resolve callback base URL with a safe production fallback.

    In production, AUTH_URL is optional. If it's not explicitly configured,
    use BACKEND_URL so OAuth callbacks still resolve.
    """
    if settings.environment != "production":
        return settings.backend_url

    auth_url = os.getenv("AUTH_URL")
    if auth_url:
        return auth_url.rstrip("/")

    return settings.backend_url.rstrip("/")


@router.get("/google")
def google_oauth_login(
    origin: Optional[str] = "login"
):
    """
    Initiate Google OAuth flow.

    Redirects user to Google OAuth consent screen.
    The origin parameter tracks where the user started (login/signup).
    """
    try:
        # Google OAuth configuration
        client_id = settings.google_auth_client_id
        base_url = _get_oauth_backend_base_url()
        redirect_uri = f"{base_url}/auth/oauth/google/callback"
        scope = "openid email profile"

        # Build Google OAuth URL with state parameter to track origin
        auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "response_type": "code",
            "access_type": "offline",
            "prompt": "consent",
            "state": origin,  # Pass origin (login/signup) in state parameter
        }

        # Construct full authorization URL
        auth_url_with_params = f"{auth_url}?{urllib.parse.urlencode(params)}"

        logger.info(f"Redirecting user to Google OAuth from {origin}: {auth_url}")
        return RedirectResponse(url=auth_url_with_params)

    except Exception as e:
        logger.error(f"Error initiating Google OAuth: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate OAuth flow"
        )


# NOTE: JSON endpoints that accepted client-supplied Google identity (POST /signin,
# POST /link, POST /verify/{provider}) were removed. They trusted unverified
# email/provider IDs from the request body, which allowed signing in as -- or
# linking into -- any account. Google sign-in goes through the server-side
# authorization-code flow (/google -> /google/callback), which gets the identity
# from Google directly.


@router.get("/google/callback")
def google_oauth_callback(
    request: Request,
    code: Optional[str] = None,
    error: Optional[str] = None,
    state: Optional[str] = "login",
    session: Session = Depends(get_session)
):
    """
    Handle Google OAuth callback.

    Exchange authorization code for tokens and create/update user account.
    Handle both successful callbacks and error callbacks (like access_denied).
    """
    try:
        # Handle OAuth errors (e.g., user cancels authorization)
        if error:
            logger.info(f"Google OAuth error: {error}, state: {state}")

            # Determine redirect URL based on origin (state parameter)
            frontend_url = settings.frontend_url if settings.environment == "development" else settings.frontend_custom_url
            origin_page = state if state in ["login", "signup"] else "login"

            if error == "access_denied":
                # User denied access - redirect back to origin page with error
                error_url = f"{frontend_url}/{origin_page}?error=access_denied"
                logger.info(f"Redirecting user to {origin_page} after access denied")
                return RedirectResponse(url=error_url)
            else:
                # Other OAuth errors
                error_url = f"{frontend_url}/{origin_page}?error=oauth_failed"
                return RedirectResponse(url=error_url)

        # If no code parameter, it's an error
        if not code:
            logger.error("No authorization code received in OAuth callback")
            frontend_url = settings.frontend_url if settings.environment == "development" else settings.frontend_custom_url
            origin_page = state if state in ["login", "signup"] else "login"
            error_url = f"{frontend_url}/{origin_page}?error=oauth_failed"
            return RedirectResponse(url=error_url)

        # Exchange authorization code for tokens
        token_url = "https://oauth2.googleapis.com/token"
        base_url = _get_oauth_backend_base_url()
        redirect_uri = f"{base_url}/auth/oauth/google/callback"

        data = {
            "client_id": settings.google_auth_client_id,
            "client_secret": settings.google_auth_client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }

        # Get tokens from Google
        token_response = requests.post(token_url, data=data)
        if not token_response.ok:
            logger.error(f"Failed to exchange code for tokens: {token_response.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange authorization code"
            )

        token_data = token_response.json()
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in")

        # Get user info from Google
        user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}

        user_response = requests.get(user_info_url, headers=headers)
        if not user_response.ok:
            logger.error(f"Failed to get user info: {user_response.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to retrieve user information"
            )

        user_info = user_response.json()

        # Accounts are matched/linked by email, so only accept addresses Google
        # has verified; otherwise an unverified Google account could claim an
        # existing user's email.
        if not user_info.get("verified_email") or not user_info.get("email"):
            logger.warning("Rejected Google sign-in with unverified or missing email")
            frontend_url = settings.frontend_url if settings.environment == "development" else settings.frontend_custom_url
            origin_page = state if state in ["login", "signup"] else "login"
            return RedirectResponse(url=f"{frontend_url}/{origin_page}?error=email_not_verified")

        # Create or update user
        oauth_service = OAuthService(session)
        user, created = oauth_service.find_or_create_oauth_user(
            provider="google",
            provider_user_id=user_info["id"],
            email=user_info["email"],
            name=user_info.get("name"),
            avatar_url=user_info.get("picture"),
            provider_data={
                "verified_email": user_info.get("verified_email", False),
                "locale": user_info.get("locale"),
            }
        )

        # Update OAuth tokens
        token_expires_at = None
        if expires_in:
            token_expires_at = datetime.utcnow().timestamp() + expires_in
            token_expires_at = datetime.fromtimestamp(token_expires_at)

        oauth_service.update_oauth_tokens(
            user_id=user.id,
            provider="google",
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=token_expires_at
        )

        # Update last login
        user.last_login = datetime.utcnow()
        session.add(user)
        session.commit()

        # Create JWT token for frontend
        jwt_token = oauth_service.create_auth_token_for_user(user)

        # Redirect to frontend with token
        frontend_url = settings.frontend_url if settings.environment == "development" else settings.frontend_custom_url
        redirect_url = f"{frontend_url}/login/callback?token={jwt_token}&new_user={created}"

        logger.info(f"User {'created' if created else 'signed in'} via Google OAuth: {user.email}")
        return RedirectResponse(url=redirect_url)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google OAuth callback error: {str(e)}")
        # Redirect to frontend with error - use state to determine origin page
        frontend_url = settings.frontend_url if settings.environment == "development" else settings.frontend_custom_url
        origin_page = state if state in ["login", "signup"] else "login"
        error_url = f"{frontend_url}/{origin_page}?error=oauth_failed"
        return RedirectResponse(url=error_url)


# Request/Response Models




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






@router.delete("/unlink/{provider}")
def unlink_oauth_account(
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
def get_linked_oauth_accounts(
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
def update_oauth_tokens(
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
def get_supported_oauth_providers():
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


