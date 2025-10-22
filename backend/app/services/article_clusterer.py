"""
Article Clustering Service

Groups similar articles from different sources to enable cross-source comparison.
"""

import hashlib
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from sqlmodel import Session, select
from ..models import (
    Article, ArticleAnalysis, ArticleCluster, ArticleClusterMember, Source
)
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


def normalize_title(title: str) -> str:
    """
    Normalize article title for comparison.

    Args:
        title: Original title

    Returns:
        Normalized title
    """
    # Convert to lowercase
    normalized = title.lower()

    # Remove common punctuation
    for char in ["?", "!", ".", ",", ":", ";", "'", '"']:
        normalized = normalized.replace(char, "")

    # Remove extra whitespace
    normalized = " ".join(normalized.split())

    return normalized


def calculate_similarity(title1: str, title2: str, summary1: str = "", summary2: str = "") -> float:
    """
    Calculate similarity between two articles based on title and summary.

    Args:
        title1: First article title
        title2: Second article title
        summary1: First article summary (optional)
        summary2: Second article summary (optional)

    Returns:
        Similarity score from 0.0 to 1.0
    """
    # Normalize titles
    norm_title1 = normalize_title(title1)
    norm_title2 = normalize_title(title2)

    # Calculate title similarity
    title_similarity = SequenceMatcher(None, norm_title1, norm_title2).ratio()

    # If summaries provided, factor them in
    if summary1 and summary2:
        # Use first 100 chars of summary for comparison
        sum1_short = summary1[:100].lower()
        sum2_short = summary2[:100].lower()
        summary_similarity = SequenceMatcher(None, sum1_short, sum2_short).ratio()

        # Weight: 70% title, 30% summary
        return (title_similarity * 0.7) + (summary_similarity * 0.3)

    return title_similarity


def generate_cluster_hash(topic: str) -> str:
    """
    Generate a unique hash for a cluster based on topic.

    Args:
        topic: The primary topic/theme

    Returns:
        64-character hash string
    """
    normalized = normalize_title(topic)
    return hashlib.sha256(normalized.encode()).hexdigest()


def find_or_create_cluster(
    event_signature: str,
    session: Session
) -> ArticleCluster:
    """
    Find existing cluster for event or create new one.

    Args:
        event_signature: Unique signature identifying the specific event
        session: Database session

    Returns:
        ArticleCluster object
    """
    cluster_hash = generate_cluster_hash(event_signature)

    # Try to find existing cluster
    cluster = session.exec(
        select(ArticleCluster)
        .where(ArticleCluster.cluster_hash == cluster_hash)
    ).first()

    if cluster:
        return cluster

    # Create new cluster
    cluster = ArticleCluster(
        cluster_hash=cluster_hash,
        primary_topic=event_signature[:200],  # Truncate to fit field
        event_signature=event_signature,
        event_date=datetime.utcnow(),  # Will be updated based on article dates
        article_count=0,
        sources_count=0
    )
    session.add(cluster)
    session.flush()

    logger.info(f"Created new cluster for event: {event_signature}")
    return cluster


def extract_event_signature(article: Article, analysis: Optional[ArticleAnalysis] = None) -> str:
    """
    Extract a unique event signature from an article.

    This identifies the specific event being covered, not just the general topic.
    Uses named entities, dates, and key context to create a unique signature.

    Args:
        article: The article to analyze
        analysis: Optional article analysis data

    Returns:
        String signature identifying the specific event
    """
    # Start with title normalization
    normalized_title = normalize_title(article.title)

    # Extract key entities from title (simplified approach)
    # Look for proper nouns, locations, organizations, people
    words = normalized_title.split()
    key_entities = []

    # Simple heuristics for entity extraction
    for word in words:
        if len(word) > 3 and word not in ['says', 'said', 'report', 'reports', 'according', 'news', 'breaking', 'update']:
            key_entities.append(word)

    # Add date context (published date within a reasonable window)
    date_context = article.published_at.strftime("%Y-%m-%d")

    # Create event signature from key entities + date
    if key_entities:
        event_signature = f"{' '.join(key_entities[:4])} {date_context}"  # Limit to top 4 entities
    else:
        event_signature = f"{normalized_title[:50]} {date_context}"  # Fallback to title fragment

    return event_signature.strip()


def detect_similar_articles(
    article: Article,
    session: Session,
    similarity_threshold: float = 0.7,
    time_window_hours: int = 72
) -> List[Tuple[Article, float]]:
    """
    Find articles similar to the given article.

    Args:
        article: The article to find matches for
        session: Database session
        similarity_threshold: Minimum similarity score (0.0 to 1.0)
        time_window_hours: Only consider articles within this time window

    Returns:
        List of (article, similarity_score) tuples
    """
    # Get articles from same time window
    cutoff_time = article.published_at - timedelta(hours=time_window_hours)

    # Get potential matches with analysis
    candidates = session.exec(
        select(Article, ArticleAnalysis)
        .join(ArticleAnalysis)
        .where(Article.id != article.id)
        .where(Article.published_at >= cutoff_time)
        .where(Article.published_at <= article.published_at + timedelta(hours=time_window_hours))
    ).all()

    # Get analysis for source article
    source_analysis = session.exec(
        select(ArticleAnalysis)
        .where(ArticleAnalysis.article_id == article.id)
    ).first()

    source_summary = source_analysis.summary if source_analysis else ""

    # Calculate similarities
    similar_articles = []
    for candidate_article, candidate_analysis in candidates:
        similarity = calculate_similarity(
            article.title,
            candidate_article.title,
            source_summary,
            candidate_analysis.summary
        )

        if similarity >= similarity_threshold:
            similar_articles.append((candidate_article, similarity))

    # Sort by similarity descending
    similar_articles.sort(key=lambda x: x[1], reverse=True)

    return similar_articles


def cluster_article(
    article: Article,
    session: Session,
    similarity_threshold: float = 0.7
) -> Optional[ArticleCluster]:
    """
    Add article to appropriate cluster based on event similarity.

    Args:
        article: The article to cluster
        session: Database session
        similarity_threshold: Minimum similarity for clustering

    Returns:
        ArticleCluster if clustered, None otherwise
    """
    # Check if already clustered
    existing = session.exec(
        select(ArticleClusterMember)
        .where(ArticleClusterMember.article_id == article.id)
    ).first()

    if existing:
        logger.debug(f"Article {article.id} already in cluster")
        return None

    # Get analysis for event signature extraction
    analysis = session.exec(
        select(ArticleAnalysis)
        .where(ArticleAnalysis.article_id == article.id)
    ).first()

    # Extract event signature for this article
    event_signature = extract_event_signature(article, analysis)

    # Find similar articles
    similar = detect_similar_articles(article, session, similarity_threshold)

    if not similar:
        logger.debug(f"No similar articles found for article {article.id}")
        return None

    # Check if any similar articles are already clustered
    for similar_article, similarity_score in similar:
        cluster_member = session.exec(
            select(ArticleClusterMember)
            .where(ArticleClusterMember.article_id == similar_article.id)
        ).first()

        if cluster_member:
            # Add to existing cluster
            cluster = session.exec(
                select(ArticleCluster)
                .where(ArticleCluster.id == cluster_member.cluster_id)
            ).first()

            if cluster:
                # Add current article to this cluster
                new_member = ArticleClusterMember(
                    cluster_id=cluster.id,
                    article_id=article.id,
                    similarity_score=similarity_score
                )
                session.add(new_member)
                logger.info(f"Added article {article.id} to existing event cluster {cluster.id}")
                return cluster

    # No existing cluster found, create new one for this specific event
    cluster = find_or_create_cluster(event_signature, session)

    # Add all similar articles to cluster
    for similar_article, similarity_score in similar[:5]:  # Limit to top 5
        member = ArticleClusterMember(
            cluster_id=cluster.id,
            article_id=similar_article.id,
            similarity_score=similarity_score
        )
        session.add(member)

    # Add the source article
    source_member = ArticleClusterMember(
        cluster_id=cluster.id,
        article_id=article.id,
        similarity_score=1.0
    )
    session.add(source_member)

    logger.info(f"Created new event cluster '{event_signature}' with {len(similar) + 1} articles")
    return cluster


def trigger_realtime_clustering(
    article_id: int,
    session: Session,
    similarity_threshold: float = 0.7
) -> Dict:
    """
    Trigger real-time clustering for a specific article.
    Used when users request coverage analysis for unclustered articles.

    Args:
        article_id: The article to cluster
        session: Database session
        similarity_threshold: Minimum similarity for clustering

    Returns:
        Dict with clustering results
    """
    article = session.exec(
        select(Article).where(Article.id == article_id)
    ).first()

    if not article:
        return {
            "success": False,
            "error": "Article not found",
            "cluster_id": None,
            "coverage_count": 0
        }

    # Check if already has coverage
    existing_member = session.exec(
        select(ArticleClusterMember)
        .where(ArticleClusterMember.article_id == article_id)
    ).first()

    if existing_member:
        # Return existing cluster info
        cluster_coverage = get_enhanced_coverage_comparison(article_id, session)
        return {
            "success": True,
            "cluster_id": existing_member.cluster_id,
            "coverage_count": cluster_coverage.get("coverage_count", 0),
            "message": "Article already has existing coverage"
        }

    # Attempt clustering
    cluster = cluster_article(article, session, similarity_threshold)

    if cluster:
        session.commit()
        cluster_coverage = get_enhanced_coverage_comparison(article_id, session)
        return {
            "success": True,
            "cluster_id": cluster.id,
            "coverage_count": cluster_coverage.get("coverage_count", 0),
            "message": f"Found {cluster_coverage.get('coverage_count', 0)} related articles covering this event"
        }
    else:
        return {
            "success": True,
            "cluster_id": None,
            "coverage_count": 0,
            "message": "No other articles found covering this specific event"
        }


def process_article_clustering(session: Session, limit: int = 20) -> Dict[str, int]:
    """
    Process recent articles for clustering.

    Args:
        session: Database session
        limit: Maximum number of articles to process

    Returns:
        Dict with statistics
    """
    stats = {
        "articles_processed": 0,
        "clusters_created": 0,
        "articles_clustered": 0
    }

    # Get recent articles with analysis that aren't clustered yet
    articles = session.exec(
        select(Article)
        .join(ArticleAnalysis)
        .where(~Article.id.in_(
            select(ArticleClusterMember.article_id)
        ))
        .order_by(Article.published_at.desc())
        .limit(limit)
    ).all()

    logger.info(f"Processing {len(articles)} articles for clustering")

    clusters_before = session.exec(select(ArticleCluster)).all()
    initial_cluster_count = len(clusters_before)

    for article in articles:
        try:
            cluster = cluster_article(article, session)
            stats["articles_processed"] += 1

            if cluster:
                stats["articles_clustered"] += 1

        except Exception as e:
            logger.error(f"Error clustering article {article.id}: {e}", exc_info=True)
            continue

    session.commit()

    # Count new clusters
    clusters_after = session.exec(select(ArticleCluster)).all()
    stats["clusters_created"] = len(clusters_after) - initial_cluster_count

    logger.info(
        f"Clustering complete: {stats['articles_processed']} processed, "
        f"{stats['articles_clustered']} clustered, {stats['clusters_created']} new clusters"
    )

    return stats


def get_cluster_comparison(cluster_id: int, session: Session) -> Optional[Dict]:
    """
    Generate a cross-source comparison for a cluster.

    Args:
        cluster_id: The cluster ID
        session: Database session

    Returns:
        Dict with comparison data
    """
    cluster = session.exec(
        select(ArticleCluster)
        .where(ArticleCluster.id == cluster_id)
    ).first()

    if not cluster:
        return None

    # Get all articles in cluster
    members = session.exec(
        select(ArticleClusterMember, Article, ArticleAnalysis, Source)
        .join(Article, Article.id == ArticleClusterMember.article_id)
        .join(ArticleAnalysis)
        .join(Source, Source.id == Article.source_id)
        .where(ArticleClusterMember.cluster_id == cluster_id)
        .order_by(ArticleClusterMember.similarity_score.desc())
    ).all()

    articles_data = []
    for member, article, analysis, source in members:
        articles_data.append({
            "article_id": article.id,
            "title": article.title,
            "url": article.url,
            "source": source.name,
            "trust_score": source.trust_score,
            "published_at": article.published_at.isoformat(),
            "summary": analysis.summary,
            "political_lean": analysis.political_lean.value,
            "sentiment": analysis.sentiment_score,
            "similarity": member.similarity_score
        })

    return {
        "cluster_id": cluster.id,
        "topic": cluster.primary_topic,
        "article_count": len(articles_data),
        "articles": articles_data,
        "sources": list(set(a["source"] for a in articles_data))
    }


def get_enhanced_coverage_comparison(
    article_id: int,
    session: Session,
    bias_filter: Optional[str] = None,
    sentiment_range: Optional[Tuple[float, float]] = None,
    max_results: int = 10
) -> Dict:
    """
    Get enhanced coverage comparison for an article with filtering options.

    Args:
        article_id: The article ID to find coverage for
        session: Database session
        bias_filter: Optional filter by political lean ('left', 'center', 'right')
        sentiment_range: Optional tuple of (min_sentiment, max_sentiment) for filtering
        max_results: Maximum number of coverage articles to return

    Returns:
        Dict with structured coverage data for frontend consumption
    """
    # Get primary article
    primary_article = session.exec(
        select(Article).where(Article.id == article_id)
    ).first()

    if not primary_article:
        return {
            "success": False,
            "error": "Article not found",
            "coverage_articles": [],
            "coverage_count": 0,
            "primary_article_id": article_id
        }

    # Get cluster member for this article
    member = session.exec(
        select(ArticleClusterMember)
        .where(ArticleClusterMember.article_id == article_id)
    ).first()

    if not member:
        return {
            "success": True,
            "coverage_articles": [],
            "coverage_count": 0,
            "primary_article_id": article_id,
            "has_cluster": False,
            "primary_article": {
                "id": primary_article.id,
                "title": primary_article.title,
                "url": primary_article.url,
                "published_at": primary_article.published_at.isoformat()
            }
        }

    # Get all articles in the same cluster
    query = session.exec(
        select(ArticleClusterMember, Article, ArticleAnalysis, Source)
        .join(Article, Article.id == ArticleClusterMember.article_id)
        .join(ArticleAnalysis)
        .join(Source, Source.id == Article.source_id)
        .where(ArticleClusterMember.cluster_id == member.cluster_id)
        .where(Article.id != article_id)  # Exclude the primary article
        .order_by(ArticleClusterMember.similarity_score.desc())
    ).all()

    coverage_articles = []

    for member, article, analysis, source in query:
        # Apply filters
        if bias_filter and analysis.political_lean.value != bias_filter:
            continue

        if sentiment_range:
            sentiment_score = analysis.sentiment_score / 10.0  # Convert to -1 to 1 scale
            if not (sentiment_range[0] <= sentiment_score <= sentiment_range[1]):
                continue

        # Calculate publication time difference
        time_diff = article.published_at - primary_article.published_at
        hours_diff = abs(time_diff.total_seconds() / 3600)

        coverage_articles.append({
            "id": article.id,
            "title": article.title,
            "url": article.url,
            "source_name": source.name,
            "source_bias": analysis.political_lean.value,
            "source_trust_score": float(source.trust_score) if source.trust_score else None,
            "published_at": article.published_at.isoformat(),
            "sentiment_score": analysis.sentiment_score / 10.0,  # Convert to -1 to 1 scale
            "political_lean": analysis.political_lean.value,
            "similarity_score": float(member.similarity_score),
            "summary": analysis.summary,
            "time_diff_hours": round(hours_diff, 1),
            "published_later": time_diff.total_seconds() > 0
        })

    # Apply max_results limit
    coverage_articles = coverage_articles[:max_results]

    # Get cluster info
    cluster = session.exec(
        select(ArticleCluster).where(ArticleCluster.id == member.cluster_id)
    ).first()

    # Calculate coverage metrics
    if coverage_articles:
        sources_count = len(set(article["source_name"] for article in coverage_articles))
        avg_similarity = sum(article["similarity_score"] for article in coverage_articles) / len(coverage_articles)
        bias_distribution = {}
        for article in coverage_articles:
            bias = article["source_bias"]
            bias_distribution[bias] = bias_distribution.get(bias, 0) + 1
    else:
        sources_count = 0
        avg_similarity = 0.0
        bias_distribution = {}

    return {
        "success": True,
        "coverage_articles": coverage_articles,
        "coverage_count": len(coverage_articles),
        "sources_count": sources_count,
        "avg_similarity": round(avg_similarity, 3),
        "bias_distribution": bias_distribution,
        "cluster_id": member.cluster_id,
        "cluster_topic": cluster.primary_topic if cluster else "Unknown Event",
        "has_cluster": True,
        "primary_article_id": article_id,
        "filters_applied": {
            "bias_filter": bias_filter,
            "sentiment_range": sentiment_range,
            "max_results": max_results
        }
    }


def get_article_cluster(article_id: int, session: Session) -> Optional[Dict]:
    """
    Get cluster information for an article.

    Args:
        article_id: The article ID
        session: Database session

    Returns:
        Cluster comparison data or None
    """
    member = session.exec(
        select(ArticleClusterMember)
        .where(ArticleClusterMember.article_id == article_id)
    ).first()

    if not member:
        return None

    return get_cluster_comparison(member.cluster_id, session)
