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

# Cap per article to keep batch analysis and verification bounded.
MAX_STATISTICS_PER_ARTICLE = 5


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
    logger.info(f"[EXTRACT] Starting extraction for article {article.id}: '{article.title[:80]}'")

    if not settings.openai_api_key:
        logger.warning("[EXTRACT] OpenAI API key not configured, skipping statistics extraction")
        return []

    # Check if we already extracted stats for this article
    existing = session.exec(
        select(StatisticVerification)
        .where(StatisticVerification.article_id == article.id)
    ).all()

    if existing:
        logger.info(f"[EXTRACT] Statistics already extracted for article {article.id} ({len(existing)} stats)")
        return []

    try:
        # Prepare prompt
        existing_stats = analysis.key_stats if analysis.key_stats else "None listed"

        logger.debug(f"[EXTRACT] Article {article.id} - Summary length: {len(analysis.summary) if analysis.summary else 0} chars")
        logger.debug(f"[EXTRACT] Article {article.id} - Key stats from analysis: {existing_stats[:100] if existing_stats != 'None listed' else 'None'}")

        prompt = STATISTICS_EXTRACTION_PROMPT.format(
            title=article.title,
            summary=analysis.summary,
            existing_stats=existing_stats
        )

        # Call OpenAI
        if not openai_api:
            logger.error("[EXTRACT] OpenAI API not configured")
            return []

        logger.debug(f"[EXTRACT] Article {article.id} - Calling OpenAI for extraction...")
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
        logger.debug(f"[EXTRACT] Article {article.id} - AI response length: {len(content)} chars")

        # Remove markdown code blocks if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        statistics = json.loads(content)

        if not isinstance(statistics, list):
            logger.error(f"[EXTRACT] Article {article.id} - Expected list of statistics, got {type(statistics)}")
            return []

        if len(statistics) == 0:
            logger.info(f"[EXTRACT] Article {article.id} - No statistics found by AI")
            return []

        if len(statistics) > MAX_STATISTICS_PER_ARTICLE:
            logger.info(
                f"[EXTRACT] Article {article.id} - Capping statistics "
                f"from {len(statistics)} to {MAX_STATISTICS_PER_ARTICLE}"
            )
            statistics = statistics[:MAX_STATISTICS_PER_ARTICLE]

        # Create StatisticVerification objects
        verifications = []
        for idx, stat in enumerate(statistics):
            stat_text = stat.get("exact_quote", "")
            logger.debug(f"[EXTRACT] Article {article.id} - Stat {idx+1}: '{stat_text[:50]}...' (confidence: {stat.get('confidence', 0.5)})")

            verification = StatisticVerification(
                article_id=article.id,
                statistic_text=stat_text,
                context=stat.get("context", ""),
                verification_status=VerificationStatus.UNVERIFIED,
                confidence_score=stat.get("confidence", 0.5)
            )
            verifications.append(verification)

        logger.info(f"[EXTRACT] ✅ Extracted {len(verifications)} statistics from article {article.id}")
        return verifications

    except json.JSONDecodeError as e:
        logger.error(f"[EXTRACT] ❌ Article {article.id} - Failed to parse AI response as JSON: {e}")
        logger.error(f"[EXTRACT] Raw response: {content[:500]}")
        return []
    except Exception as e:
        logger.error(f"[EXTRACT] ❌ Article {article.id} - Error extracting statistics: {e}", exc_info=True)
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
    stat_preview = verification.statistic_text[:60]
    logger.info(f"[VERIFY] Starting V2 verification for: '{stat_preview}'")

    try:
        # Get article content (prefer full text, fallback to summary)
        article_content = article.content_text
        content_source = "full text"
        if not article_content:
            analysis = session.exec(
                select(ArticleAnalysis)
                .where(ArticleAnalysis.article_id == article.id)
            ).first()
            article_content = analysis.summary if analysis else ""
            content_source = "summary" if article_content else "none"

        logger.debug(f"[VERIFY] Using article content from: {content_source} (length: {len(article_content) if article_content else 0})")

        # Stage 1: Trace source
        logger.info(f"[VERIFY] Stage 1: Tracing source for '{stat_preview}'")
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

            logger.info(f"[VERIFY] ✅ Stage 1: Found source - '{verification.source_name}' via {source_info.get('method', 'unknown')}")
            logger.debug(f"[VERIFY] Source URL: {verification.source_url}")
            logger.debug(f"[VERIFY] Source excerpt: {verification.source_excerpt[:100] if verification.source_excerpt else 'None'}")

            # Stage 2: Rate source credibility
            if verification.source_url and verification.source_name:
                logger.info(f"[VERIFY] Stage 2: Rating credibility for '{verification.source_name}'")
                credibility_rater = get_credibility_rater()
                verification.source_credibility_score = credibility_rater.rate_source_credibility(
                    source_url=verification.source_url,
                    source_name=verification.source_name,
                    session=session
                )
                logger.info(f"[VERIFY] ✅ Stage 2: Credibility score: {verification.source_credibility_score:.2f}")
            else:
                logger.warning(f"[VERIFY] ⚠️ Stage 2: Skipping credibility rating (missing URL or name)")
        else:
            logger.warning(f"[VERIFY] ⚠️ Stage 1: No source found for '{stat_preview}'")

        # Stage 3: Fact-check (regardless of whether we found a source)
        logger.info(f"[VERIFY] Stage 3: Fact-checking '{stat_preview}'")
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
            logger.info(f"[VERIFY] ✅ Stage 3: Fact-check status: {verification.fact_check_status} from {verification.fact_check_source}")
        else:
            logger.debug(f"[VERIFY] Stage 3: No fact-check results available")

        # Set verification notes if no source was found
        if not verification.source_url and not verification.source_name:
            verification.verification_notes = "No source found in article text or web search"
            logger.info(f"[VERIFY] Setting note: No source found")
        elif not verification.source_url and verification.source_name:
            verification.verification_notes = f"Source mentioned ({verification.source_name}) but no URL found"
            logger.info(f"[VERIFY] Setting note: Source mentioned but no URL")

        # Determine final verification status
        verification.verification_status = _determine_final_status(verification)
        verification.confidence_score = _calculate_final_confidence(verification)
        verification.verification_method = _determine_verification_method(verification)
        verification.verified_at = datetime.utcnow()
        verification.last_checked = datetime.utcnow()

        session.add(verification)
        session.commit()

        logger.info(
            f"[VERIFY] ✅ COMPLETE: '{stat_preview}' -> "
            f"Status: {verification.verification_status.value}, "
            f"Confidence: {verification.confidence_score:.2f}, "
            f"Method: {verification.verification_method.value if verification.verification_method else 'none'}"
        )

        return True

    except Exception as e:
        logger.error(f"[VERIFY] ❌ ERROR: Failed to verify '{stat_preview}': {e}", exc_info=True)
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
    analysis.stats_verified = any(
        v.verification_status == VerificationStatus.VERIFIED for v in verifications
    )

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


def reverify_all_statistics(session: Session, limit: int = None) -> Dict[str, int]:
    """
    Re-verify all existing statistics in the database.

    This function will:
    1. Find all statistics in the database
    2. Re-run the V2 verification pipeline on each
    3. Update verification status and metadata

    Args:
        session: Database session
        limit: Optional limit on number of statistics to re-verify (for testing)

    Returns:
        Dict with statistics: total_processed, newly_verified, failed
    """
    stats = {
        "total_processed": 0,
        "newly_verified": 0,
        "improved": 0,
        "failed": 0
    }

    # Get all statistics
    query = select(StatisticVerification).join(Article)
    if limit:
        query = query.limit(limit)

    all_verifications = session.exec(query).all()

    logger.info(f"Re-verifying {len(all_verifications)} statistics")

    for verification in all_verifications:
        try:
            # Get the article for this verification
            article = session.get(Article, verification.article_id)
            if not article:
                logger.warning(f"Article {verification.article_id} not found for verification {verification.id}")
                stats["failed"] += 1
                continue

            # Store old status for comparison
            old_status = verification.verification_status
            old_confidence = verification.confidence_score
            old_source_url = verification.source_url

            # Reset verification fields to re-verify
            verification.source_url = None
            verification.source_name = None
            verification.source_excerpt = None
            verification.source_credibility_score = None
            verification.fact_check_status = None
            verification.fact_check_source = None
            verification.fact_check_url = None
            verification.fact_check_details = None
            verification.verification_notes = None

            # Re-verify using V2 pipeline
            success = verify_statistic_v2(verification, article, session)

            if success:
                stats["total_processed"] += 1

                # Check if verification improved
                if old_status == VerificationStatus.UNVERIFIED and verification.verification_status == VerificationStatus.VERIFIED:
                    stats["newly_verified"] += 1
                    logger.info(f"Newly verified: {verification.statistic_text[:50]}")
                elif verification.source_url != old_source_url or (verification.confidence_score or 0) > (old_confidence or 0):
                    stats["improved"] += 1
                    logger.info(f"Improved verification: {verification.statistic_text[:50]}")
            else:
                stats["failed"] += 1
                logger.warning(f"Failed to re-verify: {verification.statistic_text[:50]}")

        except Exception as e:
            logger.error(f"Error re-verifying statistic {verification.id}: {e}", exc_info=True)
            stats["failed"] += 1
            continue

    logger.info(
        f"Re-verification complete: {stats['total_processed']} processed, "
        f"{stats['newly_verified']} newly verified, {stats['improved']} improved, "
        f"{stats['failed']} failed"
    )

    return stats
