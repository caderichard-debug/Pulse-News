"""
API endpoints for managing user favorites.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, func
from pydantic import BaseModel
from datetime import datetime
import logging

from ..database import get_session
from ..models import User, Article, ArticleFavorite, Source, ArticleAnalysis
from ..routes.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/favorites", tags=["favorites"])


class FavoriteArticleResponse(BaseModel):
    """Response for a favorited article."""
    id: int
    title: str
    url: str
    source_name: str
    published_at: datetime
    favorited_at: datetime
    summary: Optional[str] = None
    sentiment_score: Optional[float] = None
    political_lean: Optional[str] = None


class FavoritesListResponse(BaseModel):
    """Response for list of favorites."""
    favorites: List[FavoriteArticleResponse]
    total_count: int


@router.post("/articles/{article_id}")
async def add_favorite(
    article_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Add an article to user's favorites."""
    # Check if article exists
    article = session.get(Article, article_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )

    # Check if already favorited
    existing = session.exec(
        select(ArticleFavorite).where(
            ArticleFavorite.user_id == current_user.id,
            ArticleFavorite.article_id == article_id
        )
    ).first()

    if existing:
        return {
            "message": "Article already favorited",
            "favorited_at": existing.favorited_at
        }

    # Create favorite
    favorite = ArticleFavorite(
        user_id=current_user.id,
        article_id=article_id
    )
    session.add(favorite)
    session.commit()

    logger.info(f"User {current_user.id} favorited article {article_id}")

    return {
        "message": "Article added to favorites",
        "favorited_at": favorite.favorited_at
    }


@router.delete("/articles/{article_id}")
async def remove_favorite(
    article_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Remove an article from user's favorites."""
    favorite = session.exec(
        select(ArticleFavorite).where(
            ArticleFavorite.user_id == current_user.id,
            ArticleFavorite.article_id == article_id
        )
    ).first()

    if not favorite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Favorite not found"
        )

    session.delete(favorite)
    session.commit()

    logger.info(f"User {current_user.id} unfavorited article {article_id}")

    return {"message": "Article removed from favorites"}


@router.get("", response_model=FavoritesListResponse)
async def get_favorites(
    limit: int = 50,
    offset: int = 0,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get user's favorited articles."""
    # Get total count
    total_count = session.exec(
        select(func.count(ArticleFavorite.article_id)).where(
            ArticleFavorite.user_id == current_user.id
        )
    ).one()

    # Get favorites with article details
    statement = (
        select(Article, ArticleFavorite.favorited_at)
        .join(ArticleFavorite, Article.id == ArticleFavorite.article_id)
        .where(ArticleFavorite.user_id == current_user.id)
        .order_by(ArticleFavorite.favorited_at.desc())
        .offset(offset)
        .limit(limit)
    )

    results = session.exec(statement).all()

    favorites = []
    for article, favorited_at in results:
        # Get source name
        source = session.get(Source, article.source_id)

        # Get analysis
        analysis = session.exec(
            select(ArticleAnalysis).where(ArticleAnalysis.article_id == article.id)
        ).first()

        favorites.append(FavoriteArticleResponse(
            id=article.id,
            title=article.title,
            url=article.url,
            source_name=source.name if source else "Unknown",
            published_at=article.published_at,
            favorited_at=favorited_at,
            summary=analysis.summary if analysis else None,
            sentiment_score=analysis.sentiment_score if analysis else None,
            political_lean=analysis.political_lean if analysis else None
        ))

    return FavoritesListResponse(
        favorites=favorites,
        total_count=total_count
    )


@router.get("/check/{article_id}")
async def check_favorite(
    article_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Check if an article is favorited by the user."""
    favorite = session.exec(
        select(ArticleFavorite).where(
            ArticleFavorite.user_id == current_user.id,
            ArticleFavorite.article_id == article_id
        )
    ).first()

    return {
        "is_favorited": favorite is not None,
        "favorited_at": favorite.favorited_at if favorite else None
    }
