"""
AI-powered article analysis service.
Generates summaries, sentiment analysis, bias detection, and extracts key statistics.
"""

from sqlmodel import Session, select
from ..models import Article, ArticleAnalysis, ProcessingStatus, PoliticalLean
from ..database import engine
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

            # Create analysis record
            analysis = ArticleAnalysis(
                article_id=article.id,
                summary=analysis_data.get('summary', '')[:1000],  # Truncate to max length
                sentiment_score=analysis_data.get('sentiment_score', 0),
                political_lean=political_lean,
                bias_indicators=analysis_data.get('bias_indicators'),
                key_stats=str(analysis_data.get('key_stats')) if analysis_data.get('key_stats') else None,
                stats_verified=None,  # TODO: Implement stats verification
                processing_cost=0.002,  # Approximate cost per article
                tokens_used=None,  # We don't track individual tokens in batch
                processed_at=datetime.utcnow()
            )

            session.add(analysis)
            analyzed_count += 1

            logger.info(
                f"  ✓ Analyzed: {article.title[:50]}... "
                f"(sentiment: {analysis.sentiment_score}, lean: {analysis.political_lean})"
            )

        except Exception as e:
            logger.error(f"Error creating analysis for article {article.id}: {e}")
            continue

    # Commit all analyses
    session.commit()
    logger.info(f"Successfully analyzed {analyzed_count}/{len(articles_to_analyze)} articles")

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
