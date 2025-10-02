"""
Statistics Verification Service

Extracts and verifies numerical claims in articles using AI and cross-referencing.
"""

import json
import logging
from typing import List, Dict, Optional
from datetime import datetime
from sqlmodel import Session, select
from app.models import (
    Article, ArticleAnalysis, StatisticVerification,
    VerificationStatus, VerificationMethod
)
from app.config import settings
from openai import OpenAI

# Initialize OpenAI client
openai_api = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

logger = logging.getLogger(__name__)


STATISTICS_EXTRACTION_PROMPT = """Analyze this article and extract all numerical claims and statistics.

Article Title: {title}
Article Summary: {summary}
Key Stats (if any): {existing_stats}

For each statistic found, provide:
1. exact_quote: The exact statistic as stated in the article
2. context: Brief context explaining what the statistic refers to
3. verifiable: Whether this can be fact-checked (true/false)
4. confidence: Your confidence in accuracy (0.0 to 1.0)

Return a JSON array of statistics. If no statistics found, return empty array.

Example format:
[
  {{
    "exact_quote": "50% increase in Q3",
    "context": "Sales growth compared to previous quarter",
    "verifiable": true,
    "confidence": 0.8
  }}
]

Return only the JSON array, no other text.
"""


def extract_statistics_from_article(
    article: Article,
    analysis: ArticleAnalysis,
    session: Session
) -> List[StatisticVerification]:
    """
    Extract statistics from an article using AI.

    Args:
        article: The article to analyze
        analysis: The article's analysis data
        session: Database session

    Returns:
        List of StatisticVerification objects (not yet committed)
    """
    if not settings.openai_api_key:
        logger.warning("OpenAI API key not configured, skipping statistics extraction")
        return []

    # Check if we already extracted stats for this article
    existing = session.exec(
        select(StatisticVerification)
        .where(StatisticVerification.article_id == article.id)
    ).all()

    if existing:
        logger.debug(f"Statistics already extracted for article {article.id}")
        return []

    try:
        # Prepare prompt
        existing_stats = analysis.key_stats if analysis.key_stats else "None listed"

        prompt = STATISTICS_EXTRACTION_PROMPT.format(
            title=article.title,
            summary=analysis.summary,
            existing_stats=existing_stats
        )

        # Call OpenAI
        if not openai_api:
            logger.error("OpenAI API not configured")
            return []

        response = openai_api.chat.completions.create(
            model=settings.ai_model,
            messages=[
                {"role": "system", "content": "You are a fact-checking assistant that extracts verifiable statistics from news articles."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )

        # Parse response
        content = response.choices[0].message.content.strip()

        # Remove markdown code blocks if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        statistics = json.loads(content)

        if not isinstance(statistics, list):
            logger.error(f"Expected list of statistics, got {type(statistics)}")
            return []

        # Create StatisticVerification objects
        verifications = []
        for stat in statistics:
            verification = StatisticVerification(
                article_id=article.id,
                statistic_text=stat.get("exact_quote", ""),
                verification_status=VerificationStatus.UNVERIFIED,
                confidence_score=stat.get("confidence", 0.5),
                notes=stat.get("context", ""),
                verified_by="ai"
            )
            verifications.append(verification)

        logger.info(f"Extracted {len(verifications)} statistics from article {article.id}")
        return verifications

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response as JSON: {e}")
        return []
    except Exception as e:
        logger.error(f"Error extracting statistics: {e}", exc_info=True)
        return []


def verify_statistic_cross_reference(
    verification: StatisticVerification,
    article: Article,
    session: Session
) -> None:
    """
    Verify a statistic by cross-referencing with other articles.

    This is a simple implementation that checks if the same statistic
    appears in other articles about the same topic.

    Args:
        verification: The statistic to verify
        article: The source article
        session: Database session
    """
    # Search for similar statistics in other articles
    # This is a placeholder - real implementation would use more sophisticated matching

    try:
        # Get other articles with analysis
        other_articles = session.exec(
            select(Article, ArticleAnalysis)
            .join(ArticleAnalysis)
            .where(Article.id != article.id)
            .where(Article.topic_category == article.topic_category)
            .limit(10)
        ).all()

        # Check if similar statistics appear
        stat_lower = verification.statistic_text.lower()
        matches = []

        for other_article, other_analysis in other_articles:
            if other_analysis.key_stats:
                # Simple substring matching
                if stat_lower in other_analysis.key_stats.lower():
                    matches.append(other_article.url)

        if len(matches) >= 2:
            # Found in 2+ other sources
            verification.verification_status = VerificationStatus.VERIFIED
            verification.verification_method = VerificationMethod.CROSS_REFERENCE
            verification.verified_sources = json.dumps(matches)
            verification.verified_at = datetime.utcnow()
            verification.confidence_score = min(0.9, 0.6 + (len(matches) * 0.1))
            session.add(verification)
            session.commit()
            logger.info(f"Verified statistic '{verification.statistic_text}' via cross-reference")
        else:
            # Not enough matches to verify
            logger.debug(f"Could not verify statistic via cross-reference: {verification.statistic_text}")

    except Exception as e:
        logger.error(f"Error in cross-reference verification: {e}", exc_info=True)


def process_article_statistics(
    article: Article,
    session: Session
) -> int:
    """
    Extract and verify statistics for a single article.

    Args:
        article: The article to process
        session: Database session

    Returns:
        Number of statistics extracted
    """
    # Get article analysis
    analysis = session.exec(
        select(ArticleAnalysis)
        .where(ArticleAnalysis.article_id == article.id)
    ).first()

    if not analysis:
        logger.warning(f"No analysis found for article {article.id}, skipping statistics")
        return 0

    # Extract statistics
    verifications = extract_statistics_from_article(article, analysis, session)

    if not verifications:
        return 0

    # Add to session
    for verification in verifications:
        session.add(verification)

    # Attempt cross-reference verification for each
    for verification in verifications:
        verify_statistic_cross_reference(verification, article, session)

    # Update article analysis
    analysis.stats_verification_status = VerificationStatus.UNVERIFIED
    if any(v.verification_status == VerificationStatus.VERIFIED for v in verifications):
        analysis.stats_verification_status = VerificationStatus.VERIFIED
    analysis.stats_verification_date = datetime.utcnow()

    session.commit()

    return len(verifications)


def process_pending_verifications(session: Session, limit: int = 10) -> Dict[str, int]:
    """
    Process articles that need statistics extraction and verification.

    Args:
        session: Database session
        limit: Maximum number of articles to process

    Returns:
        Dict with statistics: articles_processed, stats_extracted, stats_verified
    """
    stats = {
        "articles_processed": 0,
        "stats_extracted": 0,
        "stats_verified": 0
    }

    # Find analyzed articles without statistics
    articles = session.exec(
        select(Article)
        .join(ArticleAnalysis)
        .where(ArticleAnalysis.stats_verification_date.is_(None))
        .limit(limit)
    ).all()

    logger.info(f"Processing statistics for {len(articles)} articles")

    for article in articles:
        try:
            count = process_article_statistics(article, session)
            stats["articles_processed"] += 1
            stats["stats_extracted"] += count

            # Count verified stats
            verified = session.exec(
                select(StatisticVerification)
                .where(StatisticVerification.article_id == article.id)
                .where(StatisticVerification.verification_status == VerificationStatus.VERIFIED)
            ).all()
            stats["stats_verified"] += len(verified)

        except Exception as e:
            logger.error(f"Error processing statistics for article {article.id}: {e}", exc_info=True)
            continue

    logger.info(
        f"Statistics processing complete: {stats['articles_processed']} articles, "
        f"{stats['stats_extracted']} stats extracted, {stats['stats_verified']} verified"
    )

    return stats


def get_article_statistics(article_id: int, session: Session) -> List[Dict]:
    """
    Get all statistics for an article with their verification status.

    Args:
        article_id: The article ID
        session: Database session

    Returns:
        List of statistic dictionaries
    """
    verifications = session.exec(
        select(StatisticVerification)
        .where(StatisticVerification.article_id == article_id)
        .order_by(StatisticVerification.confidence_score.desc())
    ).all()

    return [
        {
            "text": v.statistic_text,
            "status": v.verification_status.value,
            "confidence": v.confidence_score,
            "context": v.notes,
            "verified_at": v.verified_at.isoformat() if v.verified_at else None,
            "sources": json.loads(v.verified_sources) if v.verified_sources else []
        }
        for v in verifications
    ]
