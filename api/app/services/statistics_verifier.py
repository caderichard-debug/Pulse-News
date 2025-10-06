"""
Statistics Verification Service V2

Extracts and verifies numerical claims in articles using a three-stage pipeline:
1. Source Tracing: Identify original source of statistics
2. Credibility Rating: Rate source credibility
3. Fact-Checking: Verify against external fact-checking APIs
"""

import json
import logging
from typing import List, Dict, Optional
from datetime import datetime
from sqlmodel import Session, select
from ..models import (
    Article, ArticleAnalysis, StatisticVerification,
    VerificationStatus, VerificationMethod
)
from ..config import settings
from openai import OpenAI

# Import V2 services
from ..services.source_tracer import get_source_tracer
from ..services.credibility_rater import get_credibility_rater
from ..services.fact_check_integrator import get_fact_check_integrator

# Initialize OpenAI client
openai_api = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

logger = logging.getLogger(__name__)


STATISTICS_EXTRACTION_PROMPT = """Analyze this article and extract ALL quantifiable claims, statistics, and factual assertions.

Article Title: {title}
Article Summary: {summary}
Key Stats (if any): {existing_stats}

IMPORTANT: Extract ALL of the following types of claims:
1. Numerical statistics (percentages, counts, amounts): "50% increase", "$2.5 billion", "10,000 people"
2. Written numbers: "seven patients", "three months", "dozens of cases", "hundreds injured"
3. Quantifiable outcomes: "deaths of seven patients", "killed 12 people", "injured dozens"
4. Time-based claims: "within 24 hours", "over three years", "since 2020"
5. Comparative claims: "twice as many", "half the cost", "tripled in size"
6. Frequency claims: "daily", "every week", "once per month"

For each claim found, provide:
1. exact_quote: The EXACT claim as stated in the article (including written numbers)
2. context: Brief context explaining what the claim refers to
3. verifiable: Whether this can be fact-checked (true/false)
4. confidence: Your confidence in accuracy (0.0 to 1.0)

Return a JSON array of statistics. If no statistics found, return empty array.

Example format:
[
  {{
    "exact_quote": "deaths of seven patients",
    "context": "Patient fatalities attributed to medical failures",
    "verifiable": true,
    "confidence": 0.9
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
                context=stat.get("context", ""),
                verification_status=VerificationStatus.UNVERIFIED,
                confidence_score=stat.get("confidence", 0.5)
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


def verify_statistic_v2(
    verification: StatisticVerification,
    article: Article,
    session: Session
) -> bool:
    """
    Verify a statistic using V2 three-stage pipeline:
    1. Trace source
    2. Rate credibility
    3. Fact-check

    Args:
        verification: The statistic to verify
        article: The source article
        session: Database session

    Returns:
        True if verification was attempted, False otherwise
    """
    try:
        # Get article content (prefer full text, fallback to summary)
        article_content = article.content_text
        if not article_content:
            analysis = session.exec(
                select(ArticleAnalysis)
                .where(ArticleAnalysis.article_id == article.id)
            ).first()
            article_content = analysis.summary if analysis else ""

        # Stage 1: Trace source
        source_tracer = get_source_tracer()
        source_info = source_tracer.trace_statistic_source(
            statistic_text=verification.statistic_text,
            article_content=article_content,
            article_url=article.url,
            session=session
        )

        if source_info:
            verification.source_url = source_info.get("source_url")
            verification.source_name = source_info.get("source_name")
            verification.source_excerpt = source_info.get("source_excerpt")

            # Stage 2: Rate source credibility
            if verification.source_url and verification.source_name:
                credibility_rater = get_credibility_rater()
                verification.source_credibility_score = credibility_rater.rate_source_credibility(
                    source_url=verification.source_url,
                    source_name=verification.source_name,
                    session=session
                )

        # Stage 3: Fact-check (regardless of whether we found a source)
        fact_checker = get_fact_check_integrator()
        fact_check_result = fact_checker.verify_statistic(
            statistic_text=verification.statistic_text,
            source_url=verification.source_url
        )

        if fact_check_result:
            verification.fact_check_status = fact_check_result.get("fact_check_status")
            verification.fact_check_source = fact_check_result.get("fact_check_source")
            verification.fact_check_url = fact_check_result.get("fact_check_url")
            verification.fact_check_details = fact_check_result.get("fact_check_details")

        # Determine final verification status
        verification.verification_status = _determine_final_status(verification)
        verification.confidence_score = _calculate_final_confidence(verification)
        verification.verification_method = _determine_verification_method(verification)
        verification.verified_at = datetime.utcnow()
        verification.last_checked = datetime.utcnow()

        session.add(verification)
        session.commit()

        logger.info(
            f"Verified statistic '{verification.statistic_text[:50]}': "
            f"{verification.verification_status.value} (confidence: {verification.confidence_score:.2f})"
        )

        return True

    except Exception as e:
        logger.error(f"Error in V2 verification: {e}", exc_info=True)
        return False


def _determine_final_status(verification: StatisticVerification) -> VerificationStatus:
    """
    Determine final verification status based on fact-check and source credibility.

    Logic:
    - If fact_check_status == "false" -> FALSE
    - If fact_check_status == "verified" AND source_credibility >= 0.6 -> VERIFIED
    - If source_credibility >= 0.7 AND no contradicting fact-check -> VERIFIED
    - If fact_check_status == "mixed" -> DISPUTED
    - Otherwise -> UNVERIFIED
    """
    if verification.fact_check_status == "false":
        return VerificationStatus.FALSE

    if verification.fact_check_status == "verified":
        if verification.source_credibility_score and verification.source_credibility_score >= 0.6:
            return VerificationStatus.VERIFIED

    if verification.source_credibility_score and verification.source_credibility_score >= 0.7:
        # High credibility source with no contradicting fact-check
        if verification.fact_check_status not in ["false", "mixed"]:
            return VerificationStatus.VERIFIED

    if verification.fact_check_status == "mixed":
        return VerificationStatus.DISPUTED

    return VerificationStatus.UNVERIFIED


def _calculate_final_confidence(verification: StatisticVerification) -> float:
    """
    Calculate overall confidence score (0.0 to 1.0).

    Factors:
    - Source credibility (40% weight)
    - Fact-check confidence (40% weight)
    - Source traceability (20% weight)
    """
    score = 0.0

    # Source credibility contribution (40%)
    if verification.source_credibility_score:
        score += verification.source_credibility_score * 0.4

    # Fact-check contribution (40%)
    if verification.fact_check_status:
        fact_check_confidence = {
            "verified": 1.0,
            "false": 0.0,
            "mixed": 0.5,
            "unverifiable": 0.3
        }.get(verification.fact_check_status, 0.5)
        score += fact_check_confidence * 0.4

    # Source traceability contribution (20%)
    if verification.source_url:
        score += 0.2  # Bonus for having traceable source

    return min(1.0, max(0.0, score))


def _determine_verification_method(verification: StatisticVerification) -> VerificationMethod:
    """Determine which verification method was most influential."""
    if verification.fact_check_source:
        return VerificationMethod.API_CHECK
    elif verification.source_credibility_score and verification.source_credibility_score >= 0.7:
        return VerificationMethod.AI_ANALYSIS
    else:
        return VerificationMethod.AI_ANALYSIS


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

    session.commit()  # Commit to get IDs

    # Attempt V2 verification for each
    for verification in verifications:
        verify_statistic_v2(verification, article, session)

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
            "context": v.context,
            "verified_at": v.verified_at.isoformat() if v.verified_at else None,
            # V2 fields
            "source_name": v.source_name,
            "source_url": v.source_url,
            "source_credibility_score": v.source_credibility_score,
            "fact_check_status": v.fact_check_status,
            "fact_check_source": v.fact_check_source,
            "fact_check_url": v.fact_check_url
        }
        for v in verifications
    ]
