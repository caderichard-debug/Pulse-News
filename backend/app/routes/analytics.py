"""
Analytics routes for dashboard data visualization.
"""

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select, func
from ..database import get_session
from ..models import (
    User, Article, ArticleAnalysis, ArticleFrameworkLink,
    Framework, Topic, UserTopicPreference, PoliticalLean
)
from ..routes.auth import get_current_user
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import logging

router = APIRouter(prefix="/analytics", tags=["analytics"])
logger = logging.getLogger(__name__)


# Response Models
class SentimentDataPoint(BaseModel):
    date: str
    values: Dict[str, float]  # topic_name -> avg_sentiment


class BiasDistribution(BaseModel):
    week: str
    left: float
    center: float
    right: float


class HeatmapCell(BaseModel):
    x: int
    y: int
    article_count: int
    avg_sentiment: float
    sample_articles: List[Dict[str, str]]


class FrameworkAxis(BaseModel):
    id: int
    name: str
    left_position: str
    right_position: str


@router.get("/sentiment-over-time")
async def get_sentiment_over_time(
    current_user: User = Depends(get_current_user),
    days: int = Query(default=30, ge=1, le=90),
    topic_ids: Optional[str] = Query(default=None, description="Comma-separated topic IDs (currently unused)"),
    session: Session = Depends(get_session)
):
    """
    Get daily average sentiment scores by political lean.

    Returns data formatted for multi-line charts:
    [
      {
        "date": "2025-10-01",
        "values": {"Left": -2.3, "Center": 1.2, "Right": 3.5}
      },
      ...
    ]

    Note: Currently groups by political lean instead of topics since articles
    don't have topic_category assigned yet.
    """
    # Calculate date range
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days)

    # Get all articles with sentiment in date range
    query = (
        select(Article, ArticleAnalysis)
        .join(ArticleAnalysis)
        .where(Article.published_at >= start_date)
    )

    results = session.exec(query).all()

    # Group by date and political lean in Python
    result_data = {}

    for article, analysis in results:
        date_str = article.published_at.date().isoformat()
        if date_str not in result_data:
            result_data[date_str] = {"left": [], "center": [], "right": []}

        # Group by political lean
        lean_key = analysis.political_lean.value if analysis.political_lean else "center"
        result_data[date_str][lean_key].append(analysis.sentiment_score)

    # Calculate averages and format response
    response = []
    for date_str, lean_data in sorted(result_data.items()):
        values = {}
        for lean in ["left", "center", "right"]:
            sentiments = lean_data[lean]
            if sentiments:
                # Capitalize for display
                lean_display = lean.capitalize()
                values[lean_display] = round(sum(sentiments) / len(sentiments), 2)

        # Only add dates that have at least one data point
        if values:
            response.append({"date": date_str, "values": values})

    return response


@router.get("/bias-distribution")
async def get_bias_distribution(
    current_user: User = Depends(get_current_user),
    weeks: int = Query(default=4, ge=1, le=12),
    session: Session = Depends(get_session)
):
    """
    Get weekly bias distribution (percentage of left/center/right articles).

    Returns:
    [
      {
        "week": "2025-09-25",
        "left": 35.0,
        "center": 40.0,
        "right": 25.0
      },
      ...
    ]
    """
    # Calculate date range
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(weeks=weeks)

    # Get articles with political lean (database-agnostic approach)
    query = (
        select(Article, ArticleAnalysis)
        .join(ArticleAnalysis)
        .where(Article.published_at >= start_date)
    )

    results = session.exec(query).all()

    # Group by week in Python (works with SQLite and PostgreSQL)
    weekly_data = {}
    for article, analysis in results:
        # Calculate week start (Monday) for the article date
        article_date = article.published_at.date()
        days_since_monday = article_date.weekday()
        week_start = article_date - timedelta(days=days_since_monday)
        week_str = week_start.isoformat()

        if week_str not in weekly_data:
            weekly_data[week_str] = {"left": 0, "center": 0, "right": 0, "total": 0}

        lean_key = analysis.political_lean.value if analysis.political_lean else "center"
        weekly_data[week_str][lean_key] += 1
        weekly_data[week_str]["total"] += 1

    # Convert to percentages
    response = []
    for week, data in sorted(weekly_data.items()):
        total = data["total"]
        if total > 0:
            response.append({
                "week": week,
                "left": round((data["left"] / total) * 100, 1),
                "center": round((data["center"] / total) * 100, 1),
                "right": round((data["right"] / total) * 100, 1)
            })

    return response


@router.get("/framework-heatmap")
async def get_framework_heatmap(
    framework1_id: int = Query(..., description="Primary framework ID (X-axis)"),
    framework2_id: int = Query(..., description="Secondary framework ID (Y-axis)"),
    days: int = Query(default=30, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Get heatmap data for two frameworks.

    Returns cells with position, article count, avg sentiment, and sample articles.
    """
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Query for articles mapped to both frameworks
    query = (
        select(
            ArticleFrameworkLink.position_on_axis.label('x_pos'),
            ArticleFrameworkLink,
            Article,
            ArticleAnalysis
        )
        .join(Article, Article.id == ArticleFrameworkLink.article_id)
        .join(ArticleAnalysis, ArticleAnalysis.article_id == Article.id)
        .where(ArticleFrameworkLink.framework_id == framework1_id)
        .where(Article.published_at >= start_date)
    )

    framework1_data = session.exec(query).all()

    # Build article map
    article_positions = {}
    for x_pos, link1, article, analysis in framework1_data:
        article_positions[article.id] = {
            'x': link1.position_on_axis,
            'article': article,
            'analysis': analysis
        }

    # Get framework 2 positions for the same articles
    query2 = (
        select(ArticleFrameworkLink)
        .where(ArticleFrameworkLink.framework_id == framework2_id)
        .where(ArticleFrameworkLink.article_id.in_(list(article_positions.keys())))
    )

    framework2_links = session.exec(query2).all()

    for link2 in framework2_links:
        if link2.article_id in article_positions:
            article_positions[link2.article_id]['y'] = link2.position_on_axis

    # Group into heatmap cells (grid cells)
    heatmap_cells = {}
    for article_id, data in article_positions.items():
        if 'y' not in data:
            continue

        x = data['x']
        y = data['y']

        # Round to nearest grid point (e.g., -10, -8, -6, ... 10)
        x_grid = round(x / 2) * 2
        y_grid = round(y / 2) * 2

        key = (x_grid, y_grid)
        if key not in heatmap_cells:
            heatmap_cells[key] = {
                'articles': [],
                'sentiments': []
            }

        heatmap_cells[key]['articles'].append(data['article'])
        heatmap_cells[key]['sentiments'].append(data['analysis'].sentiment_score)

    # Format response
    response = []
    for (x, y), cell_data in heatmap_cells.items():
        articles = cell_data['articles']
        sentiments = cell_data['sentiments']

        response.append(HeatmapCell(
            x=x,
            y=y,
            article_count=len(articles),
            avg_sentiment=round(sum(sentiments) / len(sentiments), 2) if sentiments else 0,
            sample_articles=[
                {"id": str(a.id), "title": a.title}
                for a in articles[:3]  # First 3 articles
            ]
        ))

    return response


@router.get("/frameworks/available")
async def get_available_frameworks(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Get list of available frameworks for heatmap selection.
    """
    frameworks = session.exec(
        select(Framework)
        .where(Framework.article_count > 0)
        .order_by(Framework.article_count.desc())
    ).all()

    return [
        FrameworkAxis(
            id=f.id,
            name=f.name,
            left_position=f.left_position,
            right_position=f.right_position
        )
        for f in frameworks
    ]


@router.get("/user-stats")
async def get_user_stats(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Get user's personal statistics for dashboard overview.
    """
    from ..models import Newsletter, UserSourceSubscription

    # Count newsletters received
    newsletter_count = session.exec(
        select(func.count())
        .select_from(Newsletter)
        .where(Newsletter.user_id == current_user.id)
    ).one()

    # Count active topics
    topic_count = session.exec(
        select(func.count())
        .select_from(UserTopicPreference)
        .where(UserTopicPreference.user_id == current_user.id)
        .where(UserTopicPreference.include_in_newsletter == True)
    ).one()

    # Count subscribed sources
    source_count = session.exec(
        select(func.count())
        .select_from(UserSourceSubscription)
        .where(UserSourceSubscription.user_id == current_user.id)
        .where(UserSourceSubscription.subscribed == True)
    ).one()

    # Count articles from newsletters (approximate articles read)
    # This is a rough estimate - in production you'd track actual reads
    articles_read = newsletter_count * 5  # Assuming 5 articles per newsletter

    return {
        "articles_read": articles_read,
        "newsletters_received": newsletter_count,
        "topics_tracked": topic_count,
        "sources_subscribed": source_count,
        "views_changed": 0  # Will be implemented with challenge system
    }
