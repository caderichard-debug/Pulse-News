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
    ArticleCluster, ArticleContext, ArticleFavorite, ViewpointRelationship
)
from ..routes.auth import get_current_user
from ..services.viewpoint_analyzer import ViewpointAnalyzer
from pydantic import BaseModel
from typing import List, Optional
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


class OpposingViewpoint(BaseModel):
    article_id: int
    title: str
    url: str
    source_name: str
    source_bias: Optional[str]
    published_at: datetime
    sentiment_score: Optional[float]
    political_lean: Optional[str]
    summary: Optional[str]

    # Relationship details
    relationship_type: str
    opposition_strength: float
    reasoning: str
    ai_explanation: Optional[str]
    quality_score: Optional[float]
    framework_name: Optional[str] = None  # For framework opposition type
    primary_position: Optional[int] = None  # For framework opposition type
    opposing_position: Optional[int] = None  # For framework opposition type


class OpposingViewpointsResponse(BaseModel):
    primary_article_id: int
    opposing_viewpoints: List[OpposingViewpoint]
    total_found: int
    relationship_types_available: List[str]


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

    # Get related articles from same cluster
    cluster_member = session.exec(
        select(ArticleClusterMember)
        .where(ArticleClusterMember.article_id == article_id)
    ).first()

    related_articles = []
    if cluster_member:
        # Get other articles in the same cluster
        related_members = session.exec(
            select(ArticleClusterMember, Article, ArticleAnalysis, Source)
            .join(Article, Article.id == ArticleClusterMember.article_id)
            .join(ArticleAnalysis, ArticleAnalysis.article_id == Article.id, isouter=True)
            .join(Source, Source.id == Article.source_id)
            .where(ArticleClusterMember.cluster_id == cluster_member.cluster_id)
            .where(ArticleClusterMember.article_id != article_id)
        ).all()

        related_articles = [
            RelatedArticle(
                id=rel_article.id,
                title=rel_article.title,
                source_name=rel_source.name,
                published_at=rel_article.published_at,
                sentiment_score=rel_analysis.sentiment_score if rel_analysis else None,
                political_lean=rel_analysis.political_lean.value if rel_analysis and rel_analysis.political_lean else None,
                url=rel_article.url
            )
            for _, rel_article, rel_analysis, rel_source in related_members
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
        is_favorited=is_favorited
    )


@router.get("/{article_id}/opposing-viewpoints", response_model=OpposingViewpointsResponse)
async def get_opposing_viewpoints(
    article_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    max_results: int = 5,
    relationship_types: str = None  # Comma-separated list of relationship types
):
    """
    Get articles that represent opposing viewpoints to the given article.

    Currently supported relationship types:
    - framework_opposition: Articles with opposite positions on ethical frameworks (MVP)

    Future relationship types (not yet implemented):
    - source_bias: Same story from sources with different organizational biases
    - sentiment_contrast: Articles with contrasting emotional tones on same topic
    - temporal_evolution: How coverage of the story evolved over time

    Returns:
        - Opposing viewpoints ranked by opposition strength and quality
        - AI-generated explanations for framework oppositions
        - Caching to avoid repeated expensive AI analysis
    """
    try:
        # Verify primary article exists and has analysis
        primary_article = session.exec(select(Article).where(Article.id == article_id)).first()
        if not primary_article:
            raise HTTPException(status_code=404, detail="Article not found")

        # Parse relationship types
        available_types = ["framework_opposition"]  # Only framework_opposition is implemented in MVP
        requested_types = available_types  # Default to available types

        if relationship_types:
            requested = [t.strip() for t in relationship_types.split(",")]
            # Filter to only implemented types
            requested_types = [t for t in requested if t in available_types]

        if not requested_types:
            requested_types = available_types

        # Get opposing viewpoints using the analyzer
        start_time = datetime.utcnow()
        oppositions = ViewpointAnalyzer.find_opposing_viewpoints(
            article_id=article_id,
            session=session,
            max_results=max_results,
            relationship_types=requested_types
        )
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000  # milliseconds

        # Handle rate limiting and API availability issues
        if not oppositions:
            # Check if this is due to API unavailability
            from ..utils.openai_client import openai_client
            if not openai_client.is_available():
                logger.error("OpenAI API unavailable for viewpoint generation")
                raise HTTPException(
                    status_code=503,
                    detail="Cannot complete this request right now. OpenAI API is unavailable."
                )
            else:
                # No viewpoints found, which is normal for some articles
                logger.info(f"No opposing viewpoints found for article {article_id}")

        # Build response
        opposing_viewpoints = []
        for opposition in oppositions:
            opp_article = opposition["article"]
            opp_analysis = opposition["analysis"]
            opp_source = opposition["source"]

            viewpoint = OpposingViewpoint(
                article_id=opp_article.id,
                title=opp_article.title,
                url=opp_article.url,
                source_name=opp_source.name,
                source_bias=opp_source.organizational_bias.value if opp_source.organizational_bias else None,
                published_at=opp_article.published_at,
                sentiment_score=opp_analysis.sentiment_score if opp_analysis else None,
                political_lean=opp_analysis.political_lean.value if opp_analysis and opp_analysis.political_lean else None,
                summary=opp_analysis.summary if opp_analysis else None,
                relationship_type=opposition["relationship_type"],
                opposition_strength=opposition["opposition_strength"],
                reasoning=opposition["reasoning"],
                ai_explanation=opposition.get("ai_explanation"),
                quality_score=opposition.get("quality_score")
            )

            # Add framework-specific fields
            if opposition["relationship_type"] == "framework_opposition":
                framework = opposition.get("framework")
                if framework:
                    viewpoint.framework_name = framework.name
                    viewpoint.primary_position = opposition.get("primary_position")
                    viewpoint.opposing_position = opposition.get("opposing_position")

            opposing_viewpoints.append(viewpoint)

        logger.info(
            f"Generated {len(opposing_viewpoints)} opposing viewpoints for article {article_id} "
            f"in {processing_time:.0f}ms"
        )

        return OpposingViewpointsResponse(
            primary_article_id=article_id,
            opposing_viewpoints=opposing_viewpoints,
            total_found=len(opposing_viewpoints),
            relationship_types_available=available_types
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating opposing viewpoints for article {article_id}: {e}", exc_info=True)

        # Check for rate limiting specifically
        if "rate limit" in str(e).lower():
            raise HTTPException(
                status_code=429,
                detail="We are being rate limited by OpenAI. Contact support."
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Internal server error while generating opposing viewpoints"
            )
