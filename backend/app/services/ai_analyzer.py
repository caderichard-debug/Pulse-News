"""
AI-powered article analysis service.
Generates summaries, sentiment analysis, bias detection, and extracts key statistics.
"""

from sqlmodel import Session, select
from ..models import Article, ArticleAnalysis, ProcessingStatus, PoliticalLean, Topic, ArticleTopicLink
from ..database import engine
from ..services.statistics_verifier import process_article_statistics
from ..utils.openai_client import openai_client
from datetime import datetime
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


def analyze_articles_batch(session: Session, batch_size: int = 5) -> int:
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

    # Get completed articles that haven't been analyzed yet
    articles_to_analyze = session.exec(
        select(Article)
        .where(Article.processing_status == ProcessingStatus.COMPLETED)
        .where(Article.content_text.isnot(None))
        .where(~Article.id.in_(
            select(ArticleAnalysis.article_id)
        ))
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
    analyses = openai_client.analyze_articles_batch(article_data)

    if not analyses:
        logger.error("Failed to get analyses from OpenAI")
        return 0

    # Get all topics from database for mapping
    all_topics = session.exec(select(Topic)).all()
    topic_map = {topic.name.lower(): topic for topic in all_topics}

    # Process each analysis result
    for article, analysis_data in zip(articles_to_analyze, analyses):
        try:
            # Map political lean string to enum using the enum value (lowercase)
            lean_str = analysis_data.get('political_lean', 'center').lower()
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
            topic_category = analysis_data.get('topic_category', 'general').lower()

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
                summary=analysis_data.get('summary', '')[:1000],  # Truncate to max length
                sentiment_score=analysis_data.get('sentiment_score', 0),
                political_lean=political_lean,
                bias_indicators=analysis_data.get('bias_indicators'),
                key_stats=str(analysis_data.get('key_stats')) if analysis_data.get('key_stats') else None,
                stats_verified=False,
                processing_cost=0.002,  # Approximate cost per article
                tokens_used=None,  # We don't track individual tokens in batch
                processed_at=datetime.utcnow()
            )

            session.add(analysis)
            analyzed_count += 1

            logger.info(
                f"  ✓ Analyzed: {article.title[:50]}... "
                f"(sentiment: {analysis.sentiment_score}, lean: {analysis.political_lean}, topic: {topic_category})"
            )

        except Exception as e:
            logger.error(f"Error creating analysis for article {article.id}: {e}")
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


def get_unanalyzed_article_count(session: Session) -> int:
    """Get count of extracted articles that haven't been analyzed yet"""
    return session.exec(
        select(Article)
        .where(Article.processing_status == ProcessingStatus.COMPLETED)
        .where(Article.content_text.isnot(None))
        .where(~Article.id.in_(
            select(ArticleAnalysis.article_id)
        ))
    ).all().__len__()


if __name__ == "__main__":
    # Test the analyzer
    with Session(engine) as session:
        count = analyze_articles_batch(session, batch_size=5)
        print(f"Analyzed {count} articles")
