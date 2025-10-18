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
from ..routes.auth import get_optional_user
from ..services.url_analyzer import URLAnalyzer

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
    2. Extracts article content
    3. Performs AI analysis (summary, sentiment, bias)
    4. Generates ethical frameworks
    5. Verifies statistics
    6. Generates context

    The article will be saved to the database and can appear in feeds.
    If authenticated, the article will be associated with the user.

    **Returns**: Complete analysis data including article metadata,
    AI analysis, frameworks, statistics, and context.
    """
    try:
        # Initialize analyzer
        analyzer = URLAnalyzer(session)

        # Perform analysis
        result = await analyzer.analyze_url(
            url=str(request.url),
            user_id=current_user.id if current_user else None
        )

        return AnalyzeURLResponse(
            success=True,
            message="Article analyzed successfully",
            data=result,
            article_id=result.get("id")
        )

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
