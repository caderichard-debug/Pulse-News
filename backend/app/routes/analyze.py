"""
API endpoints for analyzing user-submitted article URLs.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from pydantic import BaseModel, HttpUrl
import logging

from ..database import get_session
from ..models import User
from ..routes.auth import get_optional_user, get_current_user
from ..services.url_analyzer import URLAnalyzer
from ..services.subscription_service import SubscriptionService
from ..middleware.subscription_middleware import check_subscription_in_middleware

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analyze", tags=["analyze"])


class AnalyzeURLRequest(BaseModel):
    """Request body for URL analysis."""
    url: HttpUrl


class AnalyzeURLResponse(BaseModel):
    """Response body for URL analysis."""
    success: bool
    message: str
    data: Optional[dict] = None
    article_id: Optional[int] = None
    usage: Optional[dict] = None


class UsageInfoResponse(BaseModel):
    """Response body for usage information."""
    today_analyses: int
    today_limit: int
    today_remaining: int
    total_analyses: int
    usage_history: list


@router.post("/url", response_model=AnalyzeURLResponse)
async def analyze_url(
    request: AnalyzeURLRequest,
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Analyze an article from a user-submitted URL.

    This endpoint:
    1. Validates the URL
    2. Checks user subscription and usage limits (if authenticated)
    3. Extracts article content
    4. Performs AI analysis (summary, sentiment, bias)
    5. Generates ethical frameworks
    6. Verifies statistics
    7. Generates context
    8. Tracks usage for subscription management

    The article will be saved to the database and can appear in feeds.
    If authenticated, the article will be associated with the user.

    **Usage Limits**: Free users are limited to 10 analyses per day.
    Premium users have unlimited access.

    **Returns**: Complete analysis data including article metadata,
    AI analysis, frameworks, statistics, and context.
    """
    try:
        # Check subscription and usage limits for authenticated users
        if current_user:
            # Check if user can perform analysis
            can_analyze, remaining = SubscriptionService.can_perform_analysis(session, current_user.id)

            if not can_analyze:
                # Get subscription info for detailed error message
                subscription_info = SubscriptionService.get_subscription_info(session, current_user.id)

                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "Daily analysis limit reached",
                        "message": f"You've reached your daily limit of {subscription_info['usage']['today_limit']} article analyses.",
                        "limit": subscription_info['usage']['today_limit'],
                        "remaining": remaining,
                        "reset_time": "Resets at midnight UTC",
                        "tier": subscription_info['tier'],
                        "upgrade_url": "/subscription",
                        "trial_available": not subscription_info['is_in_trial']
                    }
                )

            # Log the analysis request
            logger.info(f"Analysis request from user {current_user.email} (Tier: {current_user.subscription_tier})")

        # Initialize analyzer
        analyzer = URLAnalyzer(session)

        # Perform analysis
        result = await analyzer.analyze_url(
            url=str(request.url),
            user_id=current_user.id if current_user else None
        )

        # Track usage for authenticated users
        if current_user:
            try:
                usage_record = SubscriptionService.increment_usage(session, current_user.id, "analysis")
                logger.info(f"Usage tracked for user {current_user.id}: {usage_record.analyses_count}/{usage_record.daily_analysis_limit} analyses today")
            except Exception as e:
                # Don't fail the request if usage tracking fails
                logger.warning(f"Failed to track usage for user {current_user.id}: {str(e)}")

        # Add usage info to response for authenticated users
        response_data = {
            "success": True,
            "message": "Article analyzed successfully",
            "data": result,
            "article_id": result.get("id")
        }

        if current_user:
            # Get updated usage info
            usage_info = SubscriptionService.get_user_usage_stats(session, current_user.id)
            response_data["usage"] = {
                "today_analyses": usage_info["today_analyses"],
                "today_limit": usage_info["today_limit"],
                "today_remaining": usage_info["today_remaining"]
            }

        return response_data

    except ValueError as e:
        # URL validation or extraction errors
        logger.warning(f"Invalid URL analysis request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:
        # Unexpected errors
        logger.error(f"Error analyzing URL: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze article. Please try again later."
        )


@router.get("/usage", response_model=UsageInfoResponse)
async def get_analysis_usage(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's analysis usage statistics.

    **Returns**: Current usage information including daily limits,
    remaining analyses, and usage history.
    """
    try:
        usage_stats = SubscriptionService.get_user_usage_stats(session, current_user.id)

        return UsageInfoResponse(
            today_analyses=usage_stats["today_analyses"],
            today_limit=usage_stats["today_limit"],
            today_remaining=usage_stats["today_remaining"],
            total_analyses=usage_stats["total_analyses"],
            usage_history=usage_stats["usage_history"]
        )

    except Exception as e:
        logger.error(f"Error getting usage stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage statistics"
        )
