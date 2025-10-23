"""
Feed routes for home page article browsing.
"""

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select, func, or_, and_
from ..database import get_session
from ..models import (
    User, Article, ArticleAnalysis, ArticleFrameworkLink,
    Framework, Source, Topic, UserTopicPreference,
    UserSourceSubscription, PoliticalLean, ProcessingStatus, StatisticVerification,
    ArticleFavorite, ViewpointRelationship
)
from ..routes.auth import get_optional_user
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import logging

router = APIRouter(prefix="/feed", tags=["feed"])
logger = logging.getLogger(__name__)


# Response Models
class ArticleFeedItem(BaseModel):
    id: int
    title: str
    url: str
    published_at: datetime
    source_name: str
    source_id: int
    source_bias: Optional[str]  # Organizational bias of the source
    topic_category: Optional[str]
    read_time_minutes: Optional[int]

    # Analysis data
    summary: Optional[str]
    sentiment_score: Optional[float]
    political_lean: Optional[str]  # Article-level bias

    # Framework positioning (top framework)
    primary_framework: Optional[str]
    framework_position: Optional[int]

    # Statistics summary
    stats_count: int
    stats_verified_count: int
    has_stats: bool

    # Favorites
    is_favorited: bool = False

    # Opposing viewpoints
    has_opposing_viewpoints: bool = False


class FeedResponse(BaseModel):
    articles: List[ArticleFeedItem]
    total_count: int
    page: int
    page_size: int


@router.get("/articles", response_model=FeedResponse)
async def get_feed_articles(
    current_user: Optional[User] = Depends(get_optional_user),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: Optional[str] = Query(default=None, description="Search articles by title"),
    topics: Optional[List[str]] = Query(default=None, description="Filter by topic names (multiple)"),
    source_ids: Optional[List[int]] = Query(default=None, description="Filter by source IDs (multiple)"),
    political_leans: Optional[List[str]] = Query(default=None, description="Filter by political leans: left, center, right (multiple)"),
    date_from: Optional[datetime] = Query(default=None, description="Filter articles published on or after this date"),
    date_to: Optional[datetime] = Query(default=None, description="Filter articles published on or before this date"),
    date_range: Optional[str] = Query(default=None, description="Preset date range: today, week, month, year"),
    sort_by: str = Query(default="newest", description="Sort order: newest, oldest, sentiment_high, sentiment_low"),
    only_analyzed: bool = Query(default=False, description="Show only articles with analysis"),
    only_verified_stats: bool = Query(default=False, description="Show only articles with verified statistics"),
    favorites_only: bool = Query(default=False, description="Show only favorited articles (requires authentication)"),
    has_opposing_viewpoints: bool = Query(default=False, description="Show only articles with opposing viewpoint analysis"),
    session: Session = Depends(get_session)
):
    """
    Get article feed with filtering and sorting (public access).

    Returns paginated list of articles with analysis data.
    """
    # Build base query (LEFT JOIN so articles without analysis still show, unless filtered)
    query = (
        select(Article, ArticleAnalysis, Source)
        .join(Source, Source.id == Article.source_id)
        .outerjoin(ArticleAnalysis, ArticleAnalysis.article_id == Article.id)
        .where(Article.processing_status == ProcessingStatus.COMPLETED)
    )

    # Handle preset date ranges
    if date_range:
        now = datetime.utcnow()
        if date_range == "today":
            date_from = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif date_range == "week":
            date_from = now - timedelta(days=7)
        elif date_range == "month":
            date_from = now - timedelta(days=30)
        elif date_range == "year":
            date_from = now - timedelta(days=365)

    # Apply filters
    if search:
        search_pattern = f"%{search}%"
        query = query.where(Article.title.ilike(search_pattern))

    if topics:
        # Filter by multiple topics (OR logic - articles matching any topic)
        topic_conditions = [Article.topic_category == topic for topic in topics]
        query = query.where(or_(*topic_conditions))

    if source_ids:
        # Filter by multiple source IDs (OR logic - articles from any selected source)
        source_conditions = [Article.source_id == source_id for source_id in source_ids]
        query = query.where(or_(*source_conditions))

    if political_leans:
        # Filter by multiple political leans (OR logic - articles matching any lean)
        # Convert strings to enums and build conditions
        lean_enums = []
        for lean in political_leans:
            try:
                lean_enums.append(PoliticalLean(lean))
            except ValueError:
                continue  # Skip invalid political lean values

        if lean_enums:
            lean_conditions = [ArticleAnalysis.political_lean == lean_enum for lean_enum in lean_enums]
            query = query.where(or_(*lean_conditions))

    if date_from:
        query = query.where(Article.published_at >= date_from)

    if date_to:
        query = query.where(Article.published_at <= date_to)

    if only_analyzed:
        query = query.where(ArticleAnalysis.id.isnot(None))

    if only_verified_stats:
        # Filter for articles that have at least one verified statistic
        verified_articles_subquery = (
            select(StatisticVerification.article_id)
            .where(StatisticVerification.verification_status == 'verified')
            .distinct()
        )
        query = query.where(Article.id.in_(verified_articles_subquery))

    if favorites_only:
        # Filter for only favorited articles (requires authentication)
        if not current_user:
            # Return empty result if not authenticated
            return FeedResponse(
                articles=[],
                total_count=0,
                page=page,
                page_size=page_size
            )

        favorited_articles_subquery = (
            select(ArticleFavorite.article_id)
            .where(ArticleFavorite.user_id == current_user.id)
            .distinct()
        )
        query = query.where(Article.id.in_(favorited_articles_subquery))

    if has_opposing_viewpoints:
        # Filter for articles that have opposing viewpoint analysis
        articles_with_opposing_viewpoints = (
            select(ViewpointRelationship.primary_article_id)
            .where(ViewpointRelationship.expires_at > datetime.utcnow())
            .distinct()
        )
        query = query.where(Article.id.in_(articles_with_opposing_viewpoints))

    # Get total count before pagination
    count_query = select(func.count()).select_from(query.subquery())
    total_count = session.exec(count_query).one()

    # Apply sorting
    if sort_by == "newest":
        query = query.order_by(Article.published_at.desc())
    elif sort_by == "oldest":
        query = query.order_by(Article.published_at.asc())
    elif sort_by == "sentiment_high":
        query = query.order_by(ArticleAnalysis.sentiment_score.desc())
    elif sort_by == "sentiment_low":
        query = query.order_by(ArticleAnalysis.sentiment_score.asc())

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    results = session.exec(query).all()

    # Get framework data for articles
    article_ids = [article.id for article, _, _ in results]
    framework_links = session.exec(
        select(ArticleFrameworkLink, Framework)
        .join(Framework, Framework.id == ArticleFrameworkLink.framework_id)
        .where(ArticleFrameworkLink.article_id.in_(article_ids))
        .order_by(ArticleFrameworkLink.relevance_score.desc())
    ).all()

    # Map frameworks to articles (get top framework per article)
    article_frameworks: Dict[int, tuple] = {}
    for link, framework in framework_links:
        if link.article_id not in article_frameworks:
            article_frameworks[link.article_id] = (framework.name, link.position_on_axis)

    # Get statistics data for articles
    stats_data = session.exec(
        select(
            StatisticVerification.article_id,
            func.count(StatisticVerification.id).label('total'),
            func.count(func.nullif(StatisticVerification.verification_status == 'verified', False)).label('verified')
        )
        .where(StatisticVerification.article_id.in_(article_ids))
        .group_by(StatisticVerification.article_id)
    ).all()

    # Map statistics to articles
    article_stats: Dict[int, tuple] = {}
    for article_id, total, verified in stats_data:
        article_stats[article_id] = (total, verified or 0)

    # Get favorites for current user (if logged in)
    article_favorites: set = set()
    if current_user:
        favorites = session.exec(
            select(ArticleFavorite.article_id).where(
                ArticleFavorite.user_id == current_user.id,
                ArticleFavorite.article_id.in_(article_ids)
            )
        ).all()
        article_favorites = set(favorites)

    # Get opposing viewpoints data for articles
    articles_with_opposing_viewpoints = session.exec(
        select(ViewpointRelationship.primary_article_id)
        .where(ViewpointRelationship.primary_article_id.in_(article_ids))
        .where(ViewpointRelationship.expires_at > datetime.utcnow())
        .distinct()
    ).all()
    opposing_viewpoints_set = set(articles_with_opposing_viewpoints)

    # Build response
    articles = []
    for article, analysis, source in results:
        framework_data = article_frameworks.get(article.id)
        stats = article_stats.get(article.id, (0, 0))

        # Calculate read time from word count (assuming 200 words per minute)
        read_time = None
        if article.word_count:
            read_time = max(1, article.word_count // 200)

        articles.append(ArticleFeedItem(
            id=article.id,
            title=article.title,
            url=article.url,
            published_at=article.published_at,
            source_name=source.name,
            source_id=source.id,
            source_bias=source.organizational_bias.value if source.organizational_bias else None,
            topic_category=article.topic_category,
            read_time_minutes=read_time,
            summary=analysis.summary if analysis else None,
            sentiment_score=analysis.sentiment_score if analysis else None,
            political_lean=analysis.political_lean.value if analysis and analysis.political_lean else None,
            primary_framework=framework_data[0] if framework_data else None,
            framework_position=framework_data[1] if framework_data else None,
            stats_count=stats[0],
            stats_verified_count=stats[1],
            has_stats=stats[0] > 0,
            is_favorited=article.id in article_favorites,
            has_opposing_viewpoints=article.id in opposing_viewpoints_set
        ))

    return FeedResponse(
        articles=articles,
        total_count=total_count,
        page=page,
        page_size=page_size
    )


@router.get("/topics")
async def get_available_topics(
    current_user: Optional[User] = Depends(get_optional_user),
    session: Session = Depends(get_session)
):
    """
    Get list of topics that have articles available (public access).
    """
    topics = session.exec(
        select(Article.topic_category, func.count(Article.id).label('count'))
        .where(Article.topic_category.isnot(None))
        .where(Article.processing_status == ProcessingStatus.COMPLETED)
        .group_by(Article.topic_category)
        .order_by(func.count(Article.id).desc())
    ).all()

    return [
        {"name": topic, "article_count": count}
        for topic, count in topics
    ]


@router.get("/sources")
async def get_available_sources(
    current_user: Optional[User] = Depends(get_optional_user),
    session: Session = Depends(get_session)
):
    """
    Get list of sources that have articles available (public access).
    """
    sources = session.exec(
        select(Source, func.count(Article.id).label('count'))
        .join(Article, Article.source_id == Source.id)
        .where(Article.processing_status == ProcessingStatus.COMPLETED)
        .group_by(Source.id)
        .order_by(func.count(Article.id).desc())
    ).all()

    return [
        {
            "id": source.id,
            "name": source.name,
            "url": source.url,
            "organizational_bias": source.organizational_bias.value if source.organizational_bias else None,
            "article_count": count
        }
        for source, count in sources
    ]
