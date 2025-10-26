"""
Middleware for enforcing subscription limits and tracking usage.
"""

import logging
from typing import Callable, Optional
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from time import time

from app.database import get_db
from app.models import User, SubscriptionTier
from app.services.subscription_service import SubscriptionService

logger = logging.getLogger(__name__)


class SubscriptionMiddleware(BaseHTTPMiddleware):
    """Middleware to track usage and enforce subscription limits"""

    def __init__(self, app, exclude_paths: Optional[list] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/docs",
            "/openapi.json",
            "/favicon.ico",
            "/static",
            "/auth/login",
            "/auth/register",
            "/api/subscriptions/current",  # Allow checking subscription status
            "/api/webhooks"  # Webhooks need to work regardless of subscription
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time()

        # Skip middleware for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            response = await call_next(request)
            return response

        # Get user from request (this assumes JWT authentication middleware has run)
        user = getattr(request.state, 'user', None)

        if not user:
            # If no user, proceed without subscription checks
            # (this will be handled by individual endpoints requiring authentication)
            response = await call_next(request)
            return response

        # Get database session
        db: Session = next(get_db())

        try:
            # Check subscription status and add to request state
            subscription_info = SubscriptionService.get_subscription_info(db, user.id)
            request.state.subscription = subscription_info

            # Track usage based on endpoint
            await self.track_usage(request, user, db, subscription_info)

            # Check subscription limits
            await self.check_subscription_limits(request, user, db, subscription_info)

            # Proceed with the request
            response = await call_next(request)

            # Add subscription headers to response
            self.add_subscription_headers(response, subscription_info)

            # Log request duration
            process_time = time() - start_time
            logger.info(
                f"Request: {request.method} {request.url.path} - "
                f"User: {user.email} - "
                f"Tier: {subscription_info['tier']} - "
                f"Duration: {process_time:.4f}s"
            )

            return response

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Middleware error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
        finally:
            db.close()

    async def track_usage(self, request: Request, user: User, db: Session, subscription_info: dict):
        """Track usage based on the request endpoint"""
        path = request.url.path
        method = request.method

        # Track API calls
        if path.startswith("/api/") and method in ["GET", "POST", "PUT", "DELETE"]:
            # Skip tracking for subscription-related endpoints to avoid infinite loops
            if not path.startswith("/api/subscriptions") and not path.startswith("/api/webhooks"):
                SubscriptionService.increment_usage(db, user.id, "api_call")

        # Track specific features
        if path == "/api/analyze" and method == "POST":
            # Check if user can perform analysis
            can_analyze, remaining = SubscriptionService.can_perform_analysis(db, user.id)
            if not can_analyze:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "Daily analysis limit reached",
                        "limit": subscription_info['usage']['today_limit'],
                        "remaining": remaining,
                        "reset_time": "Next day at midnight UTC",
                        "upgrade_url": "/subscription"
                    }
                )

            # Increment usage
            SubscriptionService.increment_usage(db, user.id, "analysis")

    async def check_subscription_limits(self, request: Request, user: User, db: Session, subscription_info: dict):
        """Check if user has access to requested features"""
        path = request.url.path
        method = request.method

        # Premium feature checks
        premium_features = {
            "/api/analytics": "advanced_analytics",
            "/api/challenge": "challenge_system",
        }

        for feature_path, feature_name in premium_features.items():
            if path.startswith(feature_path):
                if not SubscriptionService.check_feature_access(db, user.id, feature_name):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail={
                            "error": "Premium feature required",
                            "feature": feature_name,
                            "tier_required": "PREMIUM",
                            "current_tier": subscription_info['tier'],
                            "upgrade_url": "/subscription",
                            "trial_available": subscription_info['is_in_trial'] == False
                        }
                    )

        # Check for specific premium operations
        if path.startswith("/api/analyze") and method == "POST":
            if not SubscriptionService.check_feature_access(db, user.id, "analysis"):
                # This should be caught by the usage tracking above, but double-check
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Analysis requires Premium subscription"
                )

    def add_subscription_headers(self, response: Response, subscription_info: dict):
        """Add subscription information to response headers"""
        response.headers["X-Subscription-Tier"] = subscription_info['tier']
        response.headers["X-Subscription-Status"] = subscription_info['status']
        response.headers["X-Usage-Remaining"] = str(subscription_info['usage']['today_remaining'])
        response.headers["X-Usage-Limit"] = str(subscription_info['usage']['today_limit'])

        # Add CORS headers for frontend subscription checks
        response.headers["Access-Control-Expose-Headers"] = (
            "X-Subscription-Tier, X-Subscription-Status, X-Usage-Remaining, X-Usage-Limit"
        )


class UsageTrackingMiddleware(BaseHTTPMiddleware):
    """Lightweight middleware for tracking usage without blocking requests"""

    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get user if available
        user = getattr(request.state, 'user', None)

        if user:
            db: Session = next(get_db())
            try:
                # Track general API usage
                if request.url.path.startswith("/api/"):
                    SubscriptionService.increment_usage(db, user.id, "api_call")
            except Exception as e:
                logger.error(f"Usage tracking error: {str(e)}")
            finally:
                db.close()

        response = await call_next(request)
        return response


# Decorator for protecting specific endpoints
def require_subscription(feature: Optional[str] = None):
    """Decorator to require subscription for specific endpoints"""
    def decorator(endpoint):
        async def wrapper(request: Request, *args, **kwargs):
            user = getattr(request.state, 'user', None)

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            db: Session = next(get_db())
            try:
                if feature:
                    if not SubscriptionService.check_feature_access(db, user.id, feature):
                        subscription_info = SubscriptionService.get_subscription_info(db, user.id)
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail={
                                "error": "Premium feature required",
                                "feature": feature,
                                "tier_required": "PREMIUM",
                                "current_tier": subscription_info['tier'],
                                "upgrade_url": "/subscription"
                            }
                        )
                elif not SubscriptionService.is_user_premium(db, user.id):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Premium subscription required"
                    )

                return await endpoint(request, *args, **kwargs)

            finally:
                db.close()

        return wrapper
    return decorator


# Utility functions for subscription checks
def get_user_from_request(request: Request) -> Optional[User]:
    """Extract user from request state"""
    return getattr(request.state, 'user', None)


def get_subscription_info_from_request(request: Request) -> Optional[dict]:
    """Extract subscription info from request state"""
    return getattr(request.state, 'subscription', None)


def check_subscription_in_middleware(feature: str = None):
    """FastAPI dependency for checking subscription in route handlers"""
    def dependency(
        request: Request,
        db: Session = Depends(get_db)
    ):
        user = get_user_from_request(request)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )

        if feature:
            if not SubscriptionService.check_feature_access(db, user.id, feature):
                subscription_info = SubscriptionService.get_subscription_info(db, user.id)
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "Premium feature required",
                        "feature": feature,
                        "tier_required": "PREMIUM",
                        "current_tier": subscription_info['tier'],
                        "upgrade_url": "/subscription",
                        "trial_available": subscription_info['is_in_trial'] == False
                    }
                )
        elif not SubscriptionService.is_user_premium(db, user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Premium subscription required",
                    "upgrade_url": "/subscription"
                }
            )

        return True

    return dependency


# Response models for subscription errors
class SubscriptionErrorResponse(BaseModel):
    error: str
    feature: Optional[str]
    tier_required: Optional[str]
    current_tier: str
    upgrade_url: str
    trial_available: Optional[bool]
    limit: Optional[int]
    remaining: Optional[int]
    reset_time: Optional[str]


class UsageLimitResponse(BaseModel):
    error: str
    limit: int
    remaining: int
    reset_time: str
    upgrade_url: str