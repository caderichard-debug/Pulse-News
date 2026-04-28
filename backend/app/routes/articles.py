"""
Article routes - both public listing and detailed analysis.

Merged from articles.py and article_detail.py to resolve router conflict.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session, select
from ..database import get_session
from ..models import (
    User, Article, ArticleAnalysis, ArticleFrameworkLink,
    Framework, Source, StatisticVerification, ArticleClusterMember,
    ArticleCluster, ArticleContext, ArticleFavorite, ViewpointRelationship
)
from ..routes.auth import get_current_user, get_optional_user
from ..services.viewpoint_analyzer import ViewpointAnalyzer
from ..jobs.tasks import analyze_single_article_viewpoints_job
from ..services.article_clusterer import get_enhanced_coverage_comparison, trigger_realtime_clustering
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Tuple
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
    how_this_opposes: Optional[str] = None  # Enhanced analyzer field
    why_this_opposes: Optional[str] = None  # Enhanced analyzer field
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
    current_user: Optional[User] = Depends(get_optional_user),
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

    # Check if favorited by current user (guests: no token → not favorited)
    is_favorited = False
    if current_user:
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

        # First, check database for existing viewpoint relationships
        from ..models import ViewpointRelationship
        from sqlalchemy import and_

        start_time = datetime.utcnow()

        # Query database for existing viewpoint relationships
        existing_relationships = session.exec(
            select(ViewpointRelationship).where(
                and_(
                    ViewpointRelationship.primary_article_id == article_id,
                    ViewpointRelationship.is_active == True
                )
            ).order_by(ViewpointRelationship.opposition_strength.desc()).limit(max_results)
        ).all()

        # Check if we have complete data (enhanced fields) in the database
        needs_analysis = False
        missing_enhanced_fields = []

        for rel in existing_relationships:
            if not rel.how_this_opposes or not rel.why_this_opposes:
                missing_enhanced_fields.append(rel.id)

        # If we have relationships but missing enhanced fields, trigger on-demand analysis
        if existing_relationships and missing_enhanced_fields:
            logger.info(f"Found {len(existing_relationships)} viewpoint relationships but {len(missing_enhanced_fields)} missing enhanced fields - triggering analysis")
            needs_analysis = True

        # If no relationships exist, trigger analysis
        elif not existing_relationships:
            logger.info(f"No viewpoint relationships found for article {article_id} - triggering analysis")
            needs_analysis = True

        else:
            logger.info(f"Found {len(existing_relationships)} complete viewpoint relationships in database - using existing data")

        # Trigger on-demand analysis if needed
        if needs_analysis:
            from ..services.viewpoint_analyzer_enhanced import ViewpointAnalyzer
            analyzer = ViewpointAnalyzer(session)
            saved_relationships = analyzer.save_opposing_viewpoints(
                article=primary_article,
                session=session,
                max_results=max_results
            )
            # Use the newly saved relationships
            existing_relationships = saved_relationships

        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000  # milliseconds

        # Convert database relationships to opposition format for response building
        oppositions = []
        for rel in existing_relationships:
            # Get opposing article details
            opposing_article = session.exec(select(Article).where(Article.id == rel.opposing_article_id)).first()
            if not opposing_article:
                continue

            # Get analysis and source info
            opp_analysis = session.exec(select(ArticleAnalysis).where(ArticleAnalysis.article_id == rel.opposing_article_id)).first()
            opp_source = session.exec(select(Source).where(Source.id == opposing_article.source_id)).first()

            # Build opposition dict in the expected format
            opposition = {
                "article_id": rel.opposing_article_id,
                "relationship_type": rel.relationship_type,
                "relationship_strength": rel.opposition_strength,
                "opposition_strength": rel.opposition_strength,
                "relevance_score": rel.quality_score,
                "framework_name": rel.framework_name,
                "primary_position": rel.primary_position,
                "opposing_position": rel.opposing_position,
                "how_this_opposes": rel.how_this_opposes,  # From database
                "why_this_opposes": rel.why_this_opposes,  # From database
                "ai_explanation": rel.ai_explanation,
                "title": opposing_article.title,
                "url": opposing_article.url,
                "summary": opp_analysis.summary if opp_analysis else None,
                "sentiment_score": opp_analysis.sentiment_score if opp_analysis else None,
                "source_name": opp_source.name if opp_source else None,
                "published_at": opposing_article.published_at,
                "article": opposing_article,
                "analysis": opp_analysis,
                "source": opp_source
            }
            oppositions.append(opposition)

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

        # Build response - handle both old and enhanced analyzer data structures
        opposing_viewpoints = []
        for i, opposition in enumerate(oppositions):

            # Check if this is from the enhanced analyzer (has article_id key)
            if "article_id" in opposition:
                # Enhanced analyzer data structure
                print(f"  Using enhanced analyzer path")
                viewpoint = OpposingViewpoint(
                    article_id=opposition["article_id"],
                    title=f"Article {opposition['article_id']}",  # Will be populated below if available
                    url="",  # Will be populated below if available
                    source_name="",  # Will be populated below if available
                    source_bias=None,  # Will be populated below if available
                    published_at=datetime.utcnow(),  # Default to now, will be populated below if available
                    sentiment_score=None,
                    political_lean=None,
                    summary=None,
                    relationship_type=opposition["relationship_type"],
                    opposition_strength=opposition["relationship_strength"],
                    reasoning=opposition.get("why_this_opposes", opposition.get("ai_explanation", "")),  # Use why_this_opposes as reasoning
                    ai_explanation=opposition.get("ai_explanation"),
                    how_this_opposes=opposition.get("how_this_opposes"),  # Enhanced analyzer field
                    why_this_opposes=opposition.get("why_this_opposes"),  # Enhanced analyzer field
                    quality_score=opposition.get("relevance_score")  # Use relevance_score as quality proxy
                )

                # Add framework-specific fields from enhanced analyzer
                if opposition["relationship_type"] == "framework_opposition":
                    viewpoint.framework_name = opposition.get("framework_name")
                    viewpoint.primary_position = opposition.get("primary_position")
                    viewpoint.opposing_position = opposition.get("opposing_position")

            else:
                # Original analyzer data structure
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

                # Add framework-specific fields from original analyzer
                if opposition["relationship_type"] == "framework_opposition":
                    framework = opposition.get("framework")
                    if framework:
                        viewpoint.framework_name = framework.name
                        viewpoint.primary_position = opposition.get("primary_position")
                        viewpoint.opposing_position = opposition.get("opposing_position")

            opposing_viewpoints.append(viewpoint)

        # Enhanced analyzer returns article_ids, so we need to fetch the full article details
        if oppositions and "article_id" in oppositions[0]:
            article_ids = [opp["article_id"] for opp in oppositions]
            articles_map = {
                article.id: article
                for article in session.exec(select(Article).where(Article.id.in_(article_ids))).all()
            }

            # Map article sources and analyses
            sources_map = {
                source.id: source
                for source in session.exec(select(Source).where(Source.id.in_([a.source_id for a in articles_map.values()]))).all()
            }

            analyses_map = {
                analysis.article_id: analysis
                for analysis in session.exec(select(ArticleAnalysis).where(ArticleAnalysis.article_id.in_(article_ids))).all()
            }

            # Update viewpoint data with full article information, preserving enhanced fields
            for i, viewpoint in enumerate(opposing_viewpoints):
                if viewpoint.article_id in articles_map:
                    article = articles_map[viewpoint.article_id]
                    # Store enhanced fields to preserve them
                    existing_how_opposes = viewpoint.how_this_opposes
                    existing_why_opposes = viewpoint.why_this_opposes
                    existing_ai_explanation = viewpoint.ai_explanation
                    existing_framework_name = viewpoint.framework_name
                    existing_primary_position = viewpoint.primary_position
                    existing_opposing_position = viewpoint.opposing_position

                    # Update basic fields
                    viewpoint.title = article.title
                    viewpoint.url = article.url
                    viewpoint.published_at = article.published_at

                    # Restore enhanced fields that may have been lost
                    viewpoint.how_this_opposes = existing_how_opposes
                    viewpoint.why_this_opposes = existing_why_opposes
                    viewpoint.ai_explanation = existing_ai_explanation or viewpoint.reasoning  # Fallback to reasoning
                    viewpoint.framework_name = existing_framework_name
                    viewpoint.primary_position = existing_primary_position
                    viewpoint.opposing_position = existing_opposing_position

                    if article.source_id in sources_map:
                        source = sources_map[article.source_id]
                        viewpoint.source_name = source.name
                        viewpoint.source_bias = source.organizational_bias.value if source.organizational_bias else None

                    if viewpoint.article_id in analyses_map:
                        analysis = analyses_map[viewpoint.article_id]
                        viewpoint.sentiment_score = analysis.sentiment_score
                        viewpoint.political_lean = analysis.political_lean.value if analysis.political_lean else None
                        viewpoint.summary = analysis.summary

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


@router.post("/{article_id}/analyze-viewpoints")
def trigger_viewpoint_analysis(
    article_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """
    Trigger on-demand analysis of opposing viewpoints for a specific article.

    This endpoint:
    - Starts background analysis job for the specified article
    - Returns immediately with job information
    - Can be polled for completion status
    - Uses ViewpointAnalyzer to find opposing viewpoints

    Args:
        article_id: ID of the article to analyze
        current_user: Authenticated user
        session: Database session
    """
    try:
        # Verify article exists
        article = session.exec(select(Article).where(Article.id == article_id)).first()
        if not article:
            raise HTTPException(
                status_code=404,
                detail="Article not found"
            )

        # Trigger background analysis
        background_tasks.add_task(
            analyze_single_article_viewpoints_job,
            article_id=article_id
        )

        logger.info(f"Triggered viewpoint analysis for article {article_id} by user {current_user.id}")

        return {
            "status": "triggered",
            "article_id": article_id,
            "message": "Opposing viewpoints analysis started",
            "job_id": f"analyze_single_article_viewpoints_{article_id}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering viewpoint analysis for article {article_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to start viewpoint analysis"
        )
