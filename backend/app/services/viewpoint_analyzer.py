"""
Opposing Viewpoints Analysis Service

Identifies and analyzes contrasting coverage of the same news story across different sources.
Focuses on framework_opposition first, then expands to other relationship types.
"""

import logging
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from sqlmodel import Session, select, and_, or_, func
from ..models import (
    Article, ArticleAnalysis, Source, ArticleClusterMember,
    ViewpointRelationship, Framework, ArticleFrameworkLink
)
from ..utils.openai_client import openai_client

logger = logging.getLogger(__name__)


class ViewpointAnalyzer:
    """
    Analyzes articles to find opposing viewpoints across different dimensions.

    Relationship Types (in order of implementation):
    1. framework_opposition - Opposite positions on ethical frameworks
    2. source_bias - Same story from sources with different biases
    3. sentiment_contrast - Different emotional tones on same topic
    4. temporal_evolution - How coverage evolved over time
    """

    @staticmethod
    def find_opposing_viewpoints(
        article_id: int,
        session: Session,
        max_results: int = 5,
        relationship_types: List[str] = None
    ) -> List[Dict]:
        """
        Find articles that represent opposing viewpoints to the given article.

        Args:
            article_id: Primary article ID
            session: Database session
            max_results: Maximum number of results to return
            relationship_types: List of relationship types to include (None = all available)

        Returns:
            List of viewpoint relationships with explanations
        """

        # Default to framework_opposition only for MVP
        if relationship_types is None:
            relationship_types = ["framework_opposition"]

        # Skip caching - always run fresh analysis when triggered
        logger.info(f"Running fresh viewpoint analysis for article {article_id}")

        # Get the primary article with analysis and source
        primary_article = session.exec(
            select(Article, ArticleAnalysis, Source)
            .join(ArticleAnalysis)
            .join(Source)
            .where(Article.id == article_id)
        ).first()

        if not primary_article:
            logger.warning(f"Article {article_id} not found or has no analysis")
            return []

        article, analysis, source = primary_article
        logger.info(f"Analyzing viewpoints for article: {article.title[:50]}...")

        # Find opposing viewpoints through available strategies
        all_oppositions = []

        # Strategy 1: Framework opposition (MVP - implemented first)
        if "framework_opposition" in relationship_types:
            framework_oppositions = ViewpointAnalyzer._find_framework_oppositions(
                article, analysis, session
            )
            all_oppositions.extend(framework_oppositions)
            logger.info(f"Found {len(framework_oppositions)} framework oppositions")

        # TODO: Implement other relationship types in future phases
        # if "source_bias" in relationship_types:
        #     source_oppositions = ViewpointAnalyzer._find_source_bias_oppositions(article, session)
        #     all_oppositions.extend(source_oppositions)

        # if "sentiment_contrast" in relationship_types:
        #     sentiment_oppositions = ViewpointAnalyzer._find_sentiment_contrasts(article, analysis, session)
        #     all_oppositions.extend(sentiment_oppositions)

        # if "temporal_evolution" in relationship_types:
        #     temporal_oppositions = ViewpointAnalyzer._find_temporal_evolution(article, session)
        #     all_oppositions.extend(temporal_oppositions)

        if not all_oppositions:
            logger.info(f"No opposing viewpoints found for article {article_id}")
            return []

        # Process and rank results
        processed_oppositions = ViewpointAnalyzer._process_candidates(
            all_oppositions, article, session
        )

        logger.info(f"Returning {len(processed_oppositions)} viewpoint relationships for article {article_id}")
        return processed_oppositions[:max_results]

    @staticmethod
    def _find_framework_oppositions(
        article: Article,
        analysis: ArticleAnalysis,
        session: Session
    ) -> List[Dict]:
        """
        Find articles with opposite positions on shared frameworks.
        This is the MVP implementation.
        """

        if not analysis:
            logger.warning(f"Article {article.id} has no analysis, skipping framework opposition")
            return []

        # Get frameworks for primary article (only strong relationships)
        primary_frameworks = session.exec(
            select(ArticleFrameworkLink, Framework)
            .join(Framework)
            .where(ArticleFrameworkLink.article_id == article.id)
            .where(ArticleFrameworkLink.relevance_score > 0.6)  # Only strong framework relationships
            .order_by(ArticleFrameworkLink.relevance_score.desc())
        ).all()

        if not primary_frameworks:
            logger.debug(f"Article {article.id} has no strong framework relationships")
            return []

        candidates = []

        for link, framework in primary_frameworks:
            logger.debug(f"Searching for oppositions on framework: {framework.name} (position: {link.position_on_axis})")

            # Priority 1: Same-event articles (same cluster) with opposite framework positions
            # First get cluster IDs for the primary article
            primary_clusters = session.exec(
                select(ArticleClusterMember.cluster_id)
                .where(ArticleClusterMember.article_id == article.id)
            ).all()

            same_event_oppositions = []
            if primary_clusters:
                cluster_ids = [cluster_id for cluster_id, in primary_clusters]
                same_event_oppositions = session.exec(
                    select(ArticleFrameworkLink, Article, ArticleAnalysis, Source)
                    .join(Article, ArticleFrameworkLink.article_id == Article.id)
                    .join(ArticleAnalysis, ArticleAnalysis.article_id == Article.id)
                    .join(Source, Source.id == Article.source_id)
                    .join(ArticleClusterMember, Article.id == ArticleClusterMember.article_id)
                    .where(ArticleFrameworkLink.framework_id == framework.id)
                    .where(ArticleFrameworkLink.article_id != article.id)
                    .where(ArticleFrameworkLink.relevance_score > 0.5)
                    .where(ArticleClusterMember.cluster_id.in_(cluster_ids))
                    .where(
                        or_(
                            # Opposite positions on the spectrum
                            and_(
                                ArticleFrameworkLink.position_on_axis < -2,
                                link.position_on_axis > 2
                            ),
                            and_(
                                ArticleFrameworkLink.position_on_axis > 2,
                                link.position_on_axis < -2
                            )
                        )
                    )
                    .order_by(ArticleFrameworkLink.relevance_score.desc())
                ).all()

            # Priority 2: Same-topic, different-event articles with opposite framework positions
            if not same_event_oppositions:
                oppositions = session.exec(
                    select(ArticleFrameworkLink, Article, ArticleAnalysis, Source)
                    .join(Article, ArticleFrameworkLink.article_id == Article.id)
                    .join(ArticleAnalysis, ArticleAnalysis.article_id == Article.id)
                    .join(Source, Source.id == Article.source_id)
                    .where(ArticleFrameworkLink.framework_id == framework.id)
                    .where(ArticleFrameworkLink.article_id != article.id)
                    .where(ArticleFrameworkLink.relevance_score > 0.5)  # Reasonably strong relationship
                    .where(Article.topic_category == article.topic_category)  # SAME TOPIC REQUIRED
                    .where(
                        or_(
                            # Opposite positions on the spectrum (lowered threshold for more matches)
                            and_(
                                ArticleFrameworkLink.position_on_axis < -2,
                                link.position_on_axis > 2
                            ),
                            and_(
                                ArticleFrameworkLink.position_on_axis > 2,
                                link.position_on_axis < -2
                            )
                        )
                    )
                    .order_by(ArticleFrameworkLink.relevance_score.desc())
                ).all()
            else:
                oppositions = same_event_oppositions
                logger.info(f"Found {len(same_event_oppositions)} same-event oppositions for article {article.id}")

            # Fallback: If no same-topic oppositions found, look for similar topics
            if not oppositions and article.topic_category:
                # Define similar topic mappings
                similar_topics = {
                    'politics': ['world', 'economics'],
                    'world': ['politics', 'economics'],
                    'economics': ['politics', 'world'],
                    'technology': ['science', 'economics'],
                    'science': ['technology', 'environment'],
                    'environment': ['science', 'economics'],
                    'culture': ['general'],
                    'general': ['culture']
                }

                similar_topic_list = similar_topics.get(article.topic_category, [])

                if similar_topic_list:
                    oppositions = session.exec(
                        select(ArticleFrameworkLink, Article, ArticleAnalysis, Source)
                        .join(Article, ArticleFrameworkLink.article_id == Article.id)
                        .join(ArticleAnalysis, ArticleAnalysis.article_id == Article.id)
                        .join(Source, Source.id == Article.source_id)
                        .where(ArticleFrameworkLink.framework_id == framework.id)
                        .where(ArticleFrameworkLink.article_id != article.id)
                        .where(ArticleFrameworkLink.relevance_score > 0.5)
                        .where(Article.topic_category.in_(similar_topic_list))  # SIMILAR TOPICS
                        .where(
                            or_(
                                # Opposite positions on the spectrum (lowered threshold for more matches)
                                and_(
                                    ArticleFrameworkLink.position_on_axis < -2,
                                    link.position_on_axis > 2
                                ),
                                and_(
                                    ArticleFrameworkLink.position_on_axis > 2,
                                    link.position_on_axis < -2
                                )
                            )
                        )
                        .order_by(ArticleFrameworkLink.relevance_score.desc())
                    ).all()

            for opp_link, opp_article, opp_analysis, opp_source in oppositions:
                # Calculate opposition strength based on position gap and relevance
                position_gap = abs(link.position_on_axis - opp_link.position_on_axis)
                relevance_avg = (link.relevance_score + opp_link.relevance_score) / 2

                # Strength is combination of position difference and relevance
                strength = min((position_gap / 10.0) * relevance_avg, 1.0)

                # Only include strong oppositions
                if strength >= 0.3:
                    candidates.append({
                        "article_id": opp_article.id,
                        "relationship_type": "framework_opposition",
                        "opposition_strength": strength,
                        "article": opp_article,
                        "analysis": opp_analysis,
                        "source": opp_source,
                        "framework": framework,
                        "primary_position": link.position_on_axis,
                        "opposing_position": opp_link.position_on_axis,
                        "relevance_score": relevance_avg,
                        "reasoning": f"Opposite view on {framework.name}: {link.position_on_axis} vs {opp_link.position_on_axis}"
                    })

        logger.info(f"Found {len(candidates)} framework opposition candidates for article {article.id}")
        return candidates

    @staticmethod
    def _process_candidates(
        candidates: List[Dict],
        primary_article: Article,
        session: Session
    ) -> List[Dict]:
        """
        Process candidates: deduplicate, rank, and enhance with explanations.
        """

        # Deduplicate by article_id - keep the best candidate for each article
        best_candidates = {}

        for candidate in candidates:
            article_id = candidate["article_id"]
            # Calculate combined score (strength + relevance)
            combined_score = (
                candidate["opposition_strength"] * 0.6 +
                candidate.get("relevance_score", 0) * 0.4
            )

            # Keep the candidate with the highest combined score
            if (article_id not in best_candidates or
                combined_score > best_candidates[article_id]["combined_score"]):
                candidate["combined_score"] = combined_score
                best_candidates[article_id] = candidate

        deduplicated = list(best_candidates.values())

        # Sort by opposition strength descending
        deduplicated.sort(key=lambda x: x["opposition_strength"], reverse=True)

        # Generate AI explanations for top candidates
        for candidate in deduplicated[:5]:  # Only generate for top 5 to manage costs
            if not candidate.get("ai_explanation"):
                candidate["ai_explanation"] = ViewpointAnalyzer._generate_framework_explanation(
                    primary_article, candidate["article"], candidate["framework"], session
                )

        # Calculate quality scores
        for candidate in deduplicated:
            candidate["quality_score"] = ViewpointAnalyzer._calculate_quality_score(candidate)

        # Final sort by combined score (strength + quality)
        deduplicated.sort(
            key=lambda x: (x["opposition_strength"] * 0.7) + (x.get("quality_score", 0) * 0.3),
            reverse=True
        )

        return deduplicated

    @staticmethod
    def _generate_framework_explanation(
        primary_article: Article,
        opposing_article: Article,
        framework: Framework,
        session: Session
    ) -> Optional[str]:
        """Generate AI explanation for framework opposition."""

        if not openai_client.is_available():
            logger.warning("OpenAI not available for framework explanation generation")
            return None

        # Get analysis for both articles
        primary_analysis = session.exec(
            select(ArticleAnalysis).where(ArticleAnalysis.article_id == primary_article.id)
        ).first()

        opposing_analysis = session.exec(
            select(ArticleAnalysis).where(ArticleAnalysis.article_id == opposing_article.id)
        ).first()

        if not primary_analysis or not opposing_analysis:
            return None

        try:
            explanation = openai_client.generate_framework_opposition_explanation(
                framework_name=framework.name,
                framework_left=framework.left_position,
                framework_right=framework.right_position,
                primary_title=primary_article.title,
                primary_summary=primary_analysis.summary,
                opposing_title=opposing_article.title,
                opposing_summary=opposing_analysis.summary
            )

            if explanation:
                logger.debug(f"Generated framework explanation for {framework.name}")
                return explanation

        except Exception as e:
            logger.error(f"Error generating framework explanation: {e}")

        return None

    @staticmethod
    def _calculate_quality_score(candidate: Dict) -> float:
        """
        Calculate quality score for a viewpoint relationship.
        Higher scores indicate higher quality relationships.
        """
        score = 0.0

        # Base score from opposition strength
        score += candidate["opposition_strength"] * 0.4

        # Boost for strong framework relevance
        if "relevance_score" in candidate:
            score += min(candidate["relevance_score"], 1.0) * 0.3

        # Boost for articles with analysis
        if candidate.get("analysis"):
            score += 0.2

        # Boost for quality sources (based on trust score)
        source = candidate.get("source")
        if source and hasattr(source, 'trust_score'):
            score += source.trust_score * 0.1

        return min(score, 1.0)

    @staticmethod
    def _get_cached_results(
        article_id: int,
        session: Session,
        relationship_types: List[str],
        max_results: int
    ) -> Optional[List[Dict]]:
        """
        Get cached viewpoint relationships if they exist and are not expired.
        """

        # Look for active, non-expired relationships
        relationships = session.exec(
            select(ViewpointRelationship)
            .where(ViewpointRelationship.primary_article_id == article_id)
            .where(ViewpointRelationship.relationship_type.in_(relationship_types))
            .where(ViewpointRelationship.is_active == True)
            .where(
                or_(
                    ViewpointRelationship.expires_at.is_(None),
                    ViewpointRelationship.expires_at > datetime.utcnow()
                )
            )
            .order_by(ViewpointRelationship.opposition_strength.desc())
            .limit(max_results)
        ).all()

        if not relationships:
            return None

        # Convert to expected format
        cached_results = []
        for rel in relationships:
            # Get the opposing article details
            opp_article = session.exec(
                select(Article, ArticleAnalysis, Source)
                .join(ArticleAnalysis, ArticleAnalysis.article_id == Article.id)
                .join(Source, Source.id == Article.source_id)
                .where(Article.id == rel.opposing_article_id)
            ).first()

            if opp_article:
                article, analysis, source = opp_article
                cached_results.append({
                    "article_id": article.id,
                    "relationship_type": rel.relationship_type,
                    "opposition_strength": rel.opposition_strength,
                    "article": article,
                    "analysis": analysis,
                    "source": source,
                    "ai_explanation": rel.ai_explanation,
                    "quality_score": rel.quality_score,
                    "framework_name": rel.framework_name,
                    "reasoning": rel.reasoning or f"Cached relationship: {rel.relationship_type}",
                    "primary_position": rel.primary_position,
                    "opposing_position": rel.opposing_position,
                    "cached": True
                })

        if cached_results:
            logger.info(f"Found {len(cached_results)} cached viewpoint relationships for article {article_id}")

        return cached_results

    @staticmethod
    def _cache_results(
        article_id: int,
        viewpoints: List[Dict],
        session: Session
    ) -> None:
        """
        Cache viewpoint relationships in the database.
        """

        for viewpoint in viewpoints:
            # Check if relationship already exists
            existing = session.exec(
                select(ViewpointRelationship)
                .where(ViewpointRelationship.primary_article_id == article_id)
                .where(ViewpointRelationship.opposing_article_id == viewpoint["article_id"])
                .where(ViewpointRelationship.relationship_type == viewpoint["relationship_type"])
            ).first()

            if existing:
                # Update existing relationship
                existing.opposition_strength = viewpoint["opposition_strength"]
                existing.ai_explanation = viewpoint.get("ai_explanation")
                existing.quality_score = viewpoint.get("quality_score")
                existing.framework_name = viewpoint.get("framework_name")
                existing.reasoning = viewpoint.get("reasoning")
                existing.primary_position = viewpoint.get("primary_position")
                existing.opposing_position = viewpoint.get("opposing_position")
                existing.updated_at = datetime.utcnow()
                existing.expires_at = datetime.utcnow() + timedelta(days=7)  # Expire in 7 days
                existing.is_active = True
            else:
                # Create new relationship
                new_relationship = ViewpointRelationship(
                    primary_article_id=article_id,
                    opposing_article_id=viewpoint["article_id"],
                    relationship_type=viewpoint["relationship_type"],
                    opposition_strength=viewpoint["opposition_strength"],
                    ai_explanation=viewpoint.get("ai_explanation"),
                    quality_score=viewpoint.get("quality_score"),
                    framework_name=viewpoint.get("framework_name"),
                    reasoning=viewpoint.get("reasoning"),
                    primary_position=viewpoint.get("primary_position"),
                    opposing_position=viewpoint.get("opposing_position"),
                    generation_method="automatic",
                    expires_at=datetime.utcnow() + timedelta(days=7),  # Expire in 7 days
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                session.add(new_relationship)

        try:
            session.commit()
            logger.info(f"Cached {len(viewpoints)} viewpoint relationships for article {article_id}")
        except Exception as e:
            logger.error(f"Error caching viewpoint relationships: {e}")
            session.rollback()

    @staticmethod
    def regenerate_viewpoints_batch(
        session: Session,
        limit: int = 50
    ) -> Dict[str, int]:
        """
        Batch regenerate viewpoints for articles that need refreshing.
        This is for periodic regeneration.
        """

        stats = {
            "articles_processed": 0,
            "relationships_created": 0,
            "errors": 0
        }

        # Find articles with expired viewpoints or no recent viewpoints
        cutoff_date = datetime.utcnow() - timedelta(days=7)

        articles_to_process = session.exec(
            select(Article)
            .join(ArticleAnalysis)
            .where(
                or_(
                    # Articles with no viewpoint relationships
                    ~Article.id.in_(
                        select(ViewpointRelationship.primary_article_id)
                        .where(ViewpointRelationship.is_active == True)
                    ),
                    # Articles with expired relationships
                    Article.id.in_(
                        select(ViewpointRelationship.primary_article_id)
                        .where(ViewpointRelationship.expires_at < cutoff_date)
                        .where(ViewpointRelationship.is_active == True)
                    )
                )
            )
            .order_by(func.random())
            .limit(limit)
        ).all()

        logger.info(f"Batch processing {len(articles_to_process)} articles for viewpoint regeneration")

        for article in articles_to_process:
            try:
                # Find new viewpoints
                viewpoints = ViewpointAnalyzer.find_opposing_viewpoints(
                    article.id, session, max_results=5
                )

                if viewpoints:
                    stats["relationships_created"] += len(viewpoints)

                stats["articles_processed"] += 1

            except Exception as e:
                logger.error(f"Error processing article {article.id}: {e}")
                stats["errors"] += 1
                continue

        logger.info(f"Batch regeneration complete: {stats}")
        return stats