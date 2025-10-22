"""
OAuth service for managing OAuth authentication and account linking.
Supports Google and Apple OAuth providers.
"""

from sqlmodel import Session, select
from typing import Optional, Dict, Any, List
import json
import logging
from datetime import datetime

from ..models import User, OAuthAccount
from ..utils.auth import create_access_token

logger = logging.getLogger(__name__)


class OAuthService:
    """Service for handling OAuth authentication flows and account management."""

    def __init__(self, session: Session):
        self.session = session

    def find_or_create_oauth_user(
        self,
        provider: str,
        provider_user_id: str,
        email: str,
        name: Optional[str] = None,
        avatar_url: Optional[str] = None,
        provider_data: Optional[Dict[str, Any]] = None
    ) -> tuple[User, bool]:
        """
        Find existing OAuth user or create new one.

        Returns:
            tuple: (User object, created: bool)

        Raises:
            ValueError: If email is already registered with different auth method
        """
        # First, check if there's an existing OAuth account with this provider and ID
        existing_oauth = self.session.exec(
            select(OAuthAccount).where(
                OAuthAccount.provider == provider,
                OAuthAccount.provider_user_id == provider_user_id
            )
        ).first()

        if existing_oauth:
            # Update OAuth account data and timestamps
            existing_oauth.updated_at = datetime.utcnow()
            if provider_data:
                existing_oauth.provider_data = json.dumps(provider_data)
            if avatar_url:
                # Also update user's avatar if provided
                existing_oauth.user.oauth_avatar_url = avatar_url

            self.session.commit()
            logger.info(f"Found existing OAuth user: {email} via {provider}")
            return existing_oauth.user, False

        # Check if user exists with this email (might be regular email/password user)
        existing_user = self.session.exec(
            select(User).where(User.email == email)
        ).first()

        if existing_user:
            # User exists with email - check if they already have OAuth
            if existing_user.oauth_provider:
                # User already has OAuth with different provider
                if existing_user.oauth_provider != provider:
                    raise ValueError(
                        f"Email {email} is already linked to {existing_user.oauth_provider} account. "
                        f"Cannot link to {provider}."
                    )
                else:
                    # User has same OAuth provider but no account record (edge case)
                    logger.warning(f"User {email} has OAuth provider set but no OAuth account record")
            else:
                # Regular email/password user - can link OAuth
                logger.info(f"Linking OAuth provider {provider} to existing user: {email}")

        # Create new user or update existing user with OAuth info
        if not existing_user:
            user = User(
                email=email,
                name=name or email.split('@')[0],  # Default to part before @
                email_verified=True,  # OAuth providers verify email
                hashed_password="",  # No password for OAuth-only users
                is_active=True,
                oauth_provider=provider,
                oauth_provider_id=provider_user_id,
                oauth_avatar_url=avatar_url,
                passwordless_login_enabled=True,
                created_at=datetime.utcnow()
            )
            self.session.add(user)
            self.session.flush()  # Get user.id

            # Set up default topic preferences for new OAuth users
            from ..models import Topic, UserTopicPreference
            all_topics = self.session.exec(select(Topic)).all()
            for topic in all_topics:
                preference = UserTopicPreference(
                    user_id=user.id,
                    topic_id=topic.id,
                    articles_per_topic=5,
                    include_in_newsletter=True
                )
                self.session.add(preference)

            logger.info(f"Created new OAuth user: {email} via {provider}")

        else:
            user = existing_user
            # Update existing user with OAuth info
            user.oauth_provider = provider
            user.oauth_provider_id = provider_user_id
            if avatar_url and not user.oauth_avatar_url:
                user.oauth_avatar_url = avatar_url
            if not user.email_verified:
                user.email_verified = True  # Trust OAuth provider verification

            logger.info(f"Updated existing user with OAuth: {email} via {provider}")

        # Create OAuth account record
        oauth_account = OAuthAccount(
            user_id=user.id,
            provider=provider,
            provider_user_id=provider_user_id,
            provider_data=json.dumps(provider_data) if provider_data else None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.session.add(oauth_account)

        self.session.commit()
        self.session.refresh(user)

        return user, True

    def link_oauth_account(
        self,
        user_id: int,
        provider: str,
        provider_user_id: str,
        provider_data: Optional[Dict[str, Any]] = None,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        token_expires_at: Optional[datetime] = None
    ) -> OAuthAccount:
        """
        Link OAuth account to existing user.

        Args:
            user_id: Existing user ID
            provider: OAuth provider name ('google', 'apple')
            provider_user_id: Provider-specific user ID
            provider_data: Additional provider data
            access_token: OAuth access token
            refresh_token: OAuth refresh token
            token_expires_at: Token expiration time

        Returns:
            OAuthAccount: Created OAuth account record

        Raises:
            ValueError: If OAuth account already exists or conflicts
        """
        # Check if OAuth account already exists
        existing_oauth = self.session.exec(
            select(OAuthAccount).where(
                OAuthAccount.provider == provider,
                OAuthAccount.provider_user_id == provider_user_id
            )
        ).first()

        if existing_oauth:
            if existing_oauth.user_id != user_id:
                raise ValueError(
                    f"This {provider} account is already linked to another user. "
                    f"Please unlink it first or contact support."
                )
            # Update existing OAuth account
            existing_oauth.access_token = access_token
            existing_oauth.refresh_token = refresh_token
            existing_oauth.token_expires_at = token_expires_at
            existing_oauth.updated_at = datetime.utcnow()
            if provider_data:
                existing_oauth.provider_data = json.dumps(provider_data)

            self.session.commit()
            return existing_oauth

        # Create new OAuth account link
        oauth_account = OAuthAccount(
            user_id=user_id,
            provider=provider,
            provider_user_id=provider_user_id,
            provider_data=json.dumps(provider_data) if provider_data else None,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=token_expires_at,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.session.add(oauth_account)

        # Update user's OAuth info
        user = self.session.get(User, user_id)
        if user:
            user.oauth_provider = provider
            user.oauth_provider_id = provider_user_id
            user.passwordless_login_enabled = True

        self.session.commit()
        self.session.refresh(oauth_account)

        logger.info(f"Linked {provider} account to user ID {user_id}")
        return oauth_account

    def unlink_oauth_account(self, user_id: int, provider: str) -> bool:
        """
        Unlink OAuth account from user.

        Args:
            user_id: User ID
            provider: OAuth provider to unlink

        Returns:
            bool: True if successfully unlinked
        """
        oauth_account = self.session.exec(
            select(OAuthAccount).where(
                OAuthAccount.user_id == user_id,
                OAuthAccount.provider == provider
            )
        ).first()

        if not oauth_account:
            return False

        # Check if user has other OAuth providers or password
        user = self.session.get(User, user_id)
        if user:
            # Count remaining OAuth accounts
            remaining_oauth = self.session.exec(
                select(OAuthAccount).where(
                    OAuthAccount.user_id == user_id,
                    OAuthAccount.provider != provider
                )
            ).all()

            if not remaining_oauth and not user.hashed_password:
                raise ValueError(
                    "Cannot unlink the only authentication method. "
                    "Please add a password or link another OAuth account first."
                )

            # Update user's OAuth info
            if not remaining_oauth:
                user.oauth_provider = None
                user.oauth_provider_id = None
                user.passwordless_login_enabled = False
            else:
                # Switch to another OAuth provider
                user.oauth_provider = remaining_oauth[0].provider
                user.oauth_provider_id = remaining_oauth[0].provider_user_id

        # Delete OAuth account
        self.session.delete(oauth_account)
        self.session.commit()

        logger.info(f"Unlinked {provider} account from user ID {user_id}")
        return True

    def update_oauth_tokens(
        self,
        user_id: int,
        provider: str,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        token_expires_at: Optional[datetime] = None
    ) -> bool:
        """
        Update OAuth tokens for user.

        Args:
            user_id: User ID
            provider: OAuth provider
            access_token: New access token
            refresh_token: New refresh token
            token_expires_at: New token expiration

        Returns:
            bool: True if tokens updated successfully
        """
        oauth_account = self.session.exec(
            select(OAuthAccount).where(
                OAuthAccount.user_id == user_id,
                OAuthAccount.provider == provider
            )
        ).first()

        if not oauth_account:
            return False

        oauth_account.access_token = access_token
        oauth_account.refresh_token = refresh_token
        oauth_account.token_expires_at = token_expires_at
        oauth_account.updated_at = datetime.utcnow()

        self.session.commit()
        logger.info(f"Updated OAuth tokens for {provider} account, user ID {user_id}")
        return True

    def get_user_oauth_accounts(self, user_id: int) -> List[OAuthAccount]:
        """
        Get all OAuth accounts linked to user.

        Args:
            user_id: User ID

        Returns:
            List[OAuthAccount]: List of OAuth accounts
        """
        return self.session.exec(
            select(OAuthAccount).where(OAuthAccount.user_id == user_id)
        ).all()

    def find_user_by_oauth(self, provider: str, provider_user_id: str) -> Optional[User]:
        """
        Find user by OAuth provider and user ID.

        Args:
            provider: OAuth provider name
            provider_user_id: Provider-specific user ID

        Returns:
            Optional[User]: User if found
        """
        oauth_account = self.session.exec(
            select(OAuthAccount).where(
                OAuthAccount.provider == provider,
                OAuthAccount.provider_user_id == provider_user_id
            )
        ).first()

        return oauth_account.user if oauth_account else None

    def create_auth_token_for_user(self, user: User) -> str:
        """
        Create JWT access token for OAuth user.

        Args:
            user: User object

        Returns:
            str: JWT access token
        """
        return create_access_token(data={"sub": user.email})