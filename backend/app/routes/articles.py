"""
Article routes - both public listing and detailed analysis.

Merged from articles.py and article_detail.py to resolve router conflict.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from ..database import get_session
from ..models import (
    User, Article, ArticleAnalysis, ArticleFrameworkLink,
    Framework, Source, StatisticVerification, ArticleClusterMember,
    ArticleCluster, ArticleContext, ArticleFavorite
)
from ..routes.auth import get_current_user
from ..services.article_clusterer import get_enhanced_coverage_comparison, trigger_realtime_clustering
from pydantic import BaseModel
from typing import List, Optional, Tuple
from datetime import datetime
import logging

router = APIRouter(prefix="/articles", tags=["articles"])
logger = logging.getLogger(__name__)


# Response Models
class VerifiedStatistic(BaseModel):
    statistic: str
    verification_status: str
    confidence: Optional[float]
    source_name: Optional[str]
    source_url: Optional[str]
    source_credibility_score: Optional[float]
    fact_check_status: Optional[str]
    fact_check_source: Optional[str]
    verification_notes: Optional[str]
    last_checked: Optional[str]  # ISO datetime string


class FrameworkPosition(BaseModel):
    framework_id: int
    framework_name: str
    left_position: str
    right_position: str
    position_on_axis: int
    relevance_score: float
    explanation: Optional[str]


class RelatedArticle(BaseModel):
    id: int
    title: str
    source_name: str
    published_at: datetime
    sentiment_score: Optional[float]
    political_lean: Optional[str]
    url: str


class ArticleContextData(BaseModel):
    background: Optional[str]
    key_players: Optional[str]
    timeline: Optional[str]
    significance: Optional[str]


class ArticleDetailResponse(BaseModel):
    # Article basics
    id: int
    title: str
    url: str
    published_at: datetime
    source_name: str
    source_url: str
    source_bias: Optional[str]  # Organizational bias of the source
    topic_category: Optional[str]
    content_preview: str  # First 500 chars
    read_time_minutes: Optional[int]

    # Analysis
    summary: Optional[str]
    sentiment_score: Optional[float]
    political_lean: Optional[str]  # Article-level bias

    # Verified statistics
    statistics: List[VerifiedStatistic]

    # Framework positioning
    frameworks: List[FrameworkPosition]

    # Related coverage
    related_articles: List[RelatedArticle]

    # Context
    context: Optional[ArticleContextData]

    # Favorites
    is_favorited: bool = False

    # Coverage metadata for frontend component
    coverage_metadata: Optional[dict] = None


@router.get("/analyzed")
def get_analyzed_articles(
    limit: int = 10,
    offset: int = 0,
    session: Session = Depends(get_session)
):
    """
    Get articles that have been analyzed with AI summaries.

    Returns article with full analysis including:
    - Summary (100 words)
    - Sentiment score
    - Political lean
    - Bias indicators
    - Key statistics
    """
    # Get analyzed articles with their analysis
    query = (
        select(Article, ArticleAnalysis, Source)
        .join(ArticleAnalysis, Article.id == ArticleAnalysis.article_id)
        .join(Source, Article.source_id == Source.id)
        .order_by(Article.scraped_at.desc())
        .offset(offset)
        .limit(limit)
    )

    results = session.exec(query).all()

    articles_data = []
    for article, analysis, source in results:
        articles_data.append({
            "id": article.id,
            "title": article.title,
            "url": article.url,
            "source": {
                "name": source.name,
                "url": source.url
            },
            "published_at": article.published_at.isoformat() if article.published_at else None,
            "scraped_at": article.scraped_at.isoformat() if article.scraped_at else None,
            "word_count": article.word_count,
            "analysis": {
                "summary": analysis.summary,
                "sentiment_score": analysis.sentiment_score,
                "political_lean": analysis.political_lean.value if analysis.political_lean else None,
                "bias_indicators": analysis.bias_indicators,
                "key_stats": analysis.key_stats,
                "processed_at": analysis.processed_at.isoformat() if analysis.processed_at else None
            }
        })

    return {
        "total": len(articles_data),
        "articles": articles_data
    }


@router.get("/{article_id}", response_model=ArticleDetailResponse)
async def get_article_detail(
    article_id: int,
    coverage_bias_filter: Optional[str] = None,
    coverage_sentiment_range: Optional[str] = None,
    coverage_max_results: int = 10,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Get detailed analysis for a specific article.

    Includes:
    - Full article metadata
    - AI analysis (summary, sentiment, bias)
    - Verified statistics with source tracing
    - Framework positioning
    - Related articles (same cluster)
    - Context information
    """
    # Get article with analysis and source
    result = session.exec(
        select(Article, ArticleAnalysis, Source)
        .join(ArticleAnalysis, ArticleAnalysis.article_id == Article.id, isouter=True)
        .join(Source, Source.id == Article.source_id)
        .where(Article.id == article_id)
    ).first()

    if not result:
        raise HTTPException(status_code=404, detail="Article not found")

    article, analysis, source = result

    # Get verified statistics
    stats = session.exec(
        select(StatisticVerification)
        .where(StatisticVerification.article_id == article_id)
    ).all()

    statistics = [
        VerifiedStatistic(
            statistic=stat.statistic_text,
            verification_status=stat.verification_status.value if hasattr(stat.verification_status, 'value') else stat.verification_status,
            confidence=stat.confidence_score,
            source_name=stat.source_name,
            source_url=stat.source_url,
            source_credibility_score=stat.source_credibility_score,
            fact_check_status=stat.fact_check_status,
            fact_check_source=stat.fact_check_source,
            verification_notes=stat.verification_notes,
            last_checked=stat.last_checked.isoformat() if stat.last_checked else None
        )
        for stat in stats
    ]

    # Get framework positioning
    framework_links = session.exec(
        select(ArticleFrameworkLink, Framework)
        .join(Framework, Framework.id == ArticleFrameworkLink.framework_id)
        .where(ArticleFrameworkLink.article_id == article_id)
        .order_by(ArticleFrameworkLink.relevance_score.desc())
    ).all()

    frameworks = [
        FrameworkPosition(
            framework_id=framework.id,
            framework_name=framework.name,
            left_position=framework.left_position,
            right_position=framework.right_position,
            position_on_axis=link.position_on_axis,
            relevance_score=link.relevance_score,
            explanation=link.ai_explanation
        )
        for link, framework in framework_links
    ]

    # Parse sentiment range if provided
    sentiment_range = None
    if coverage_sentiment_range:
        try:
            min_sent, max_sent = map(float, coverage_sentiment_range.split(','))
            sentiment_range = (min_sent, max_sent)
        except ValueError:
            logger.warning(f"Invalid sentiment range format: {coverage_sentiment_range}")

    # Get enhanced coverage comparison with filtering
    coverage_data = get_enhanced_coverage_comparison(
        article_id=article_id,
        session=session,
        bias_filter=coverage_bias_filter,
        sentiment_range=sentiment_range,
        max_results=coverage_max_results
    )

    related_articles = []
    if coverage_data.get("success") and coverage_data.get("coverage_articles"):
        related_articles = [
            RelatedArticle(
                id=coverage["id"],
                title=coverage["title"],
                source_name=coverage["source_name"],
                published_at=datetime.fromisoformat(coverage["published_at"]),
                sentiment_score=coverage["sentiment_score"],
                political_lean=coverage["political_lean"],
                url=coverage["url"]
            )
            for coverage in coverage_data["coverage_articles"]
        ]

    # Get context
    context_data = session.exec(
        select(ArticleContext)
        .where(ArticleContext.article_id == article_id)
    ).first()

    context = None
    if context_data:
        context = ArticleContextData(
            background=context_data.background,
            key_players=context_data.key_players,
            timeline=context_data.timeline,
            significance=context_data.significance
        )

    # Check if favorited by current user
    is_favorited = False
    favorite = session.exec(
        select(ArticleFavorite).where(
            ArticleFavorite.user_id == current_user.id,
            ArticleFavorite.article_id == article_id
        )
    ).first()
    is_favorited = favorite is not None

    # Build response
    content_preview = article.content_text[:500] if article.content_text else ""

    return ArticleDetailResponse(
        id=article.id,
        title=article.title,
        url=article.url,
        published_at=article.published_at,
        source_name=source.name,
        source_url=source.url,
        source_bias=source.organizational_bias.value if source.organizational_bias else None,
        topic_category=article.topic_category,
        content_preview=content_preview,
        read_time_minutes=article.word_count // 200 if article.word_count else None,
        summary=analysis.summary if analysis else None,
        sentiment_score=analysis.sentiment_score if analysis else None,
        political_lean=analysis.political_lean.value if analysis and analysis.political_lean else None,
        statistics=statistics,
        frameworks=frameworks,
        related_articles=related_articles,
        context=context,
        is_favorited=is_favorited,
        coverage_metadata=coverage_data if coverage_data.get("success") else None
    )


@router.post("/{article_id}/analyze-coverage")
async def trigger_coverage_analysis(
    article_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Trigger real-time analysis to find coverage for articles that don't have existing clusters.
    Uses the article clusterer service to find similar articles and create clusters on-demand.
    """
    logger.info(f"User {current_user.id} triggered coverage analysis for article {article_id}")

    try:
        result = trigger_realtime_clustering(
            article_id=article_id,
            session=session
        )

        if result["success"]:
            return {
                "success": True,
                "message": result["message"],
                "cluster_id": result["cluster_id"],
                "coverage_count": result["coverage_count"],
                "article_id": article_id
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=result.get("error", "Failed to analyze coverage")
            )

    except Exception as e:
        logger.error(f"Error in coverage analysis for article {article_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze coverage: {str(e)}"
        )


@router.get("/{article_id}/coverage")
async def get_enhanced_coverage(
    article_id: int,
    bias_filter: Optional[str] = None,
    sentiment_range: Optional[str] = None,
    max_results: int = 10,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Get enhanced coverage data for an article with filtering options.
    Returns structured data for the Other Coverage component.
    """
    # Parse sentiment range if provided
    parsed_sentiment_range = None
    if sentiment_range:
        try:
            min_sent, max_sent = map(float, sentiment_range.split(','))
            parsed_sentiment_range = (min_sent, max_sent)
        except ValueError:
            logger.warning(f"Invalid sentiment range format: {sentiment_range}")

    try:
        coverage_data = get_enhanced_coverage_comparison(
            article_id=article_id,
            session=session,
            bias_filter=bias_filter,
            sentiment_range=parsed_sentiment_range,
            max_results=max_results
        )

        if coverage_data.get("success"):
            return coverage_data
        else:
            raise HTTPException(
                status_code=404,
                detail=coverage_data.get("error", "Failed to get coverage data")
            )

    except Exception as e:
        logger.error(f"Error getting coverage for article {article_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get coverage data: {str(e)}"
        )
