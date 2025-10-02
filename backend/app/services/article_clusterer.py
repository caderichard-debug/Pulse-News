"""
Article Clustering Service

Groups similar articles from different sources to enable cross-source comparison.
"""

import hashlib
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from sqlmodel import Session, select
from app.models import (
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
    topic: str,
    session: Session
) -> ArticleCluster:
    """
    Find existing cluster for topic or create new one.

    Args:
        topic: Primary topic name
        session: Database session

    Returns:
        ArticleCluster object
    """
    cluster_hash = generate_cluster_hash(topic)

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
        primary_topic=topic
    )
    session.add(cluster)
    session.flush()

    logger.info(f"Created new cluster for topic: {topic}")
    return cluster


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
    Add article to appropriate cluster based on similarity.

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
                logger.info(f"Added article {article.id} to existing cluster {cluster.id}")
                return cluster

    # No existing cluster found, create new one
    # Use the article title as primary topic
    cluster = find_or_create_cluster(article.title, session)

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

    logger.info(f"Created new cluster with {len(similar) + 1} articles")
    return cluster


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
