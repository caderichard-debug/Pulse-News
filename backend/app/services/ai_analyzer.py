"""
AI-powered article analysis service.
Generates summaries, sentiment analysis, bias detection, and extracts key statistics.
"""

from sqlmodel import Session, select
from sqlalchemy import or_, func
from ..models import Article, ArticleAnalysis, ProcessingStatus, PoliticalLean, Topic, ArticleTopicLink
from ..database import engine
from ..services.statistics_verifier import process_article_statistics
from ..utils.openai_client import openai_client
from ..utils.pipeline_metrics import incr, TimedStage
from ..config import settings
from datetime import datetime
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

VALID_TOPICS = {
    "general", "politics", "economics", "technology", "science", "culture", "world", "environment"
}


def _normalize_analysis_payload(payload: dict) -> dict:
    summary = (payload.get("summary") or "").strip()
    if not summary:
        summary = "Summary unavailable from model response."
        incr("pipeline.analysis.anomaly.empty_summary")
    sentiment = payload.get("sentiment_score", 0)
    if not isinstance(sentiment, (int, float)):
        sentiment = 0
    sentiment = int(max(-10, min(10, sentiment)))
    topic = (payload.get("topic_category") or "general").strip().lower()
    if topic not in VALID_TOPICS:
        incr("pipeline.analysis.anomaly.unknown_topic")
        topic = "general"
    lean = (payload.get("political_lean") or "center").strip().lower()
    if lean not in {"left", "center", "right"}:
        incr("pipeline.analysis.anomaly.invalid_lean")
        lean = "center"
    return {
        "summary": summary[:1000],
        "sentiment_score": sentiment,
        "topic_category": topic,
        "political_lean": lean,
        "bias_indicators": payload.get("bias_indicators"),
        "key_stats": payload.get("key_stats"),
    }


def analyze_articles_batch(
    session: Session,
    batch_size: int = 5,
    include_failed_status: bool = False,
) -> int:
    """
    Analyze a batch of articles using Claude API.
    Processes articles that have been extracted but not yet analyzed.

    Args:
        session: Database session (injected for testing)
        batch_size: Number of articles to process in one API call (max 5 recommended)

    Returns:
        Number of articles successfully analyzed
    """
    if not openai_client.is_available():
        logger.error("OpenAI API not configured. Set OPENAI_API_KEY in .env")
        return 0

    analyzed_count = 0

    # Get extracted articles that haven't been analyzed yet.
    # Optionally include FAILED rows to recover analysis candidates that still have content.
    status_filter = (
        or_(
            Article.processing_status == ProcessingStatus.COMPLETED,
            Article.processing_status == ProcessingStatus.FAILED,
        )
        if include_failed_status
        else (Article.processing_status == ProcessingStatus.COMPLETED)
    )
    articles_to_analyze = session.exec(
        select(Article)
        .where(status_filter)
        .where(Article.content_text.isnot(None))
        .where(~Article.id.in_(select(ArticleAnalysis.article_id)))
        .limit(batch_size)
    ).all()

    if not articles_to_analyze:
        logger.info("No articles ready for analysis")
        return 0

    logger.info(f"Analyzing {len(articles_to_analyze)} articles...")

    # Prepare articles for batch analysis
    article_data = [
        {
            "title": article.title,
            "content": article.content_text
        }
        for article in articles_to_analyze
    ]

    # Call OpenAI API
    with TimedStage("pipeline.analyze.batch_duration"):
        analyses = openai_client.analyze_articles_batch(
            article_data,
            max_tokens=settings.max_tokens_per_request,
        )

    if not analyses:
        logger.error("Failed to get analyses from OpenAI")
        return 0

    # Get all topics from database for mapping
    all_topics = session.exec(select(Topic)).all()
    topic_map = {topic.name.lower(): topic for topic in all_topics}

    # Process each analysis result
    for article, analysis_data in zip(articles_to_analyze, analyses):
        try:
            normalized = _normalize_analysis_payload(analysis_data)
            # Map political lean string to enum using the enum value (lowercase)
            lean_str = normalized["political_lean"]
            try:
                # Match by enum value, not by enum name
                political_lean = next(
                    (lean for lean in PoliticalLean if lean.value == lean_str),
                    PoliticalLean.CENTER
                )
            except StopIteration:
                logger.warning(f"Invalid political lean '{lean_str}', defaulting to center")
                political_lean = PoliticalLean.CENTER

            # Get topic category from AI response
            topic_category = normalized["topic_category"]

            # Update article's topic_category field for quick filtering
            article.topic_category = topic_category

            # Create ArticleTopicLink if topic exists in database
            if topic_category in topic_map:
                topic = topic_map[topic_category]

                # Check if link already exists
                existing_link = session.exec(
                    select(ArticleTopicLink)
                    .where(ArticleTopicLink.article_id == article.id)
                    .where(ArticleTopicLink.topic_id == topic.id)
                ).first()

                if not existing_link:
                    article_topic_link = ArticleTopicLink(
                        article_id=article.id,
                        topic_id=topic.id
                    )
                    session.add(article_topic_link)
            else:
                logger.warning(f"Topic '{topic_category}' not found in database, using 'general'")
                # Fallback to 'general' topic
                if 'general' in topic_map:
                    topic = topic_map['general']
                    existing_link = session.exec(
                        select(ArticleTopicLink)
                        .where(ArticleTopicLink.article_id == article.id)
                        .where(ArticleTopicLink.topic_id == topic.id)
                    ).first()
                    if not existing_link:
                        article_topic_link = ArticleTopicLink(
                            article_id=article.id,
                            topic_id=topic.id
                        )
                        session.add(article_topic_link)
                    article.topic_category = 'general'

            # Create analysis record
            analysis = ArticleAnalysis(
                article_id=article.id,
                summary=normalized["summary"],
                sentiment_score=normalized["sentiment_score"],
                political_lean=political_lean,
                bias_indicators=normalized.get("bias_indicators"),
                key_stats=str(normalized.get("key_stats")) if normalized.get("key_stats") else None,
                stats_verified=False,
                processing_cost=0.002,  # Approximate cost per article
                tokens_used=None,  # We don't track individual tokens in batch
                processed_at=datetime.utcnow()
            )

            session.add(analysis)
            analyzed_count += 1
            incr("pipeline.analysis.success")

            logger.info(
                f"  ✓ Analyzed: {article.title[:50]}... "
                f"(sentiment: {analysis.sentiment_score}, lean: {analysis.political_lean}, topic: {topic_category})"
            )

        except Exception as e:
            logger.error(f"Error creating analysis for article {article.id}: {e}")
            incr("pipeline.analysis.failed")
            continue

    # Commit all analyses
    session.commit()
    logger.info(f"Successfully analyzed {analyzed_count}/{len(articles_to_analyze)} articles")

    for article in articles_to_analyze:
        try:
            with Session(engine) as stat_session:
                art = stat_session.get(Article, article.id)
                if art:
                    process_article_statistics(art, stat_session)
        except Exception as e:
            logger.warning(
                "Post-analysis statistics pipeline failed for article %s: %s",
                article.id,
                e,
            )

    return analyzed_count


def get_article_analysis(article_id: int, session: Session) -> Optional[ArticleAnalysis]:
    """Get analysis for a specific article"""
    return session.exec(
        select(ArticleAnalysis)
        .where(ArticleAnalysis.article_id == article_id)
    ).first()


def get_unanalyzed_article_count(
    session: Session,
    include_failed_status: bool = False,
) -> int:
    """Get count of extracted articles that haven't been analyzed yet"""
    status_filter = (
        or_(
            Article.processing_status == ProcessingStatus.COMPLETED,
            Article.processing_status == ProcessingStatus.FAILED,
        )
        if include_failed_status
        else (Article.processing_status == ProcessingStatus.COMPLETED)
    )
    return session.exec(
        select(func.count(Article.id))
        .where(status_filter)
        .where(Article.content_text.isnot(None))
        .where(~Article.id.in_(select(ArticleAnalysis.article_id)))
    ).one()


if __name__ == "__main__":
    # Test the analyzer
    with Session(engine) as session:
        count = analyze_articles_batch(session, batch_size=5)
        print(f"Analyzed {count} articles")
