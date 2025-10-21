"""
Enhanced ViewpointAnalyzer with Cross-Framework Analysis

This module provides sophisticated opposing viewpoint analysis that finds
semantically relevant framework oppositions across all possible framework
combinations, rather than limiting searches to the same framework.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict
import re

from sqlmodel import Session, select
from sqlalchemy import text, and_, or_, func

from ..models import (
    Article, ArticleAnalysis, ViewpointRelationship, ArticleFrameworkLink,
    Framework, Source
)

logger = logging.getLogger(__name__)

def extract_event_keywords(title: str) -> str:
    """Extract key event keywords from article title for matching same events."""
    # Remove common stop words and extract key phrases
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
        'before', 'after', 'above', 'below', 'between', 'among', 'is', 'are',
        'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do',
        'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can'
    }

    # Extract proper nouns (capitalized words) and key terms
    words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b|\b[a-z]{4,}\b', title)
    key_terms = [w.lower() for w in words if w.lower() not in stop_words and len(w) > 2]

    # Return most significant terms
    return ' '.join(key_terms[:3]) if key_terms else title.split()[0].lower()

class ViewpointAnalyzer:
    """Enhanced analyzer for finding opposing viewpoints across frameworks."""

    def __init__(self, session: Session):
        self.session = session

    def find_opposing_viewpoints(
        self,
        article: Article,
        max_results: int = 10,
        session: Optional[Session] = None
    ) -> List[Dict[str, Any]]:
        """
        Find articles with opposing viewpoints using enhanced cross-framework analysis.

        This method finds semantically relevant oppositions by:
        1. Looking for same-event articles with opposing frameworks (any framework pair)
        2. Finding same-topic articles with the strongest framework oppositions across ALL framework combinations
        3. Ranking by semantic relevance, position strength, and content similarity
        """
        if session is None:
            from ..database import get_session
            session = next(get_session())

        logger.info(f"Finding cross-framework opposing viewpoints for article {article.id}: {article.title[:50]}...")

        # Get all framework links for the primary article
        primary_frameworks = session.exec(
            select(ArticleFrameworkLink)
            .where(ArticleFrameworkLink.article_id == article.id)
            .where(ArticleFrameworkLink.relevance_score > 0.3)  # Reasonably relevant frameworks
            .order_by(ArticleFrameworkLink.relevance_score.desc())
        ).all()

        if not primary_frameworks:
            logger.warning(f"No frameworks found for article {article.id}")
            return []

        logger.info(f"Found {len(primary_frameworks)} frameworks for primary article:")
        for pf in primary_frameworks:
            framework = session.exec(select(Framework).where(Framework.id == pf.framework_id)).first()
            logger.info(f"  - {framework.name}: position {pf.position_on_axis}, relevance {pf.relevance_score:.2f}")

        candidates = []

        # Get ALL frameworks for cross-framework comparison
        all_frameworks = session.exec(select(Framework)).all()
        framework_dict = {f.id: f for f in all_frameworks}

        # Strategy 1: Same-event articles (highest priority)
        event_keywords = extract_event_keywords(article.title)
        same_event_articles = session.exec(
            select(ArticleFrameworkLink, Article, ArticleAnalysis, Source)
            .join(Article, ArticleFrameworkLink.article_id == Article.id)
            .join(ArticleAnalysis, ArticleAnalysis.article_id == Article.id)
            .join(Source, Source.id == Article.source_id)
            .where(ArticleFrameworkLink.article_id != article.id)
            .where(ArticleFrameworkLink.relevance_score > 0.3)
            .where(
                or_(
                    Article.title.ilike(f"%{event_keywords}%"),
                    ArticleAnalysis.summary.ilike(f"%{event_keywords}%")
                )
            )
            .order_by(ArticleFrameworkLink.relevance_score.desc())
        ).all()

        for opp_link, opp_article, opp_analysis, opp_source in same_event_articles:
            # Find the best framework opposition across ALL possible framework pairs
            best_opposition = self._find_best_framework_opposition(
                primary_frameworks, opp_link, framework_dict, session
            )

            if best_opposition:
                candidates.append(best_opposition)

        # Strategy 2: Same-topic articles with strong cross-framework oppositions
        if len(candidates) < max_results:
            same_topic_articles = session.exec(
                select(ArticleFrameworkLink, Article, ArticleAnalysis, Source)
                .join(Article, ArticleFrameworkLink.article_id == Article.id)
                .join(ArticleAnalysis, ArticleAnalysis.article_id == Article.id)
                .join(Source, Source.id == Article.source_id)
                .where(ArticleFrameworkLink.article_id != article.id)
                .where(ArticleFrameworkLink.relevance_score > 0.4)  # Higher threshold for same-topic
                .where(Article.topic_category == article.topic_category)
                .where(Article.id.notin_([c["article_id"] for c in candidates]))  # Avoid duplicates
                .order_by(ArticleFrameworkLink.relevance_score.desc())
                .limit(max_results * 3)  # Get more candidates to select from
            ).all()

            for opp_link, opp_article, opp_analysis, opp_source in same_topic_articles:
                best_opposition = self._find_best_framework_opposition(
                    primary_frameworks, opp_link, framework_dict, session
                )

                if best_opposition:
                    candidates.append(best_opposition)

        # Strategy 3: Similar topics (politics <--> world <--> economics, etc.)
        if len(candidates) < max_results and article.topic_category:
            similar_topics = self._get_similar_topics(article.topic_category)

            if similar_topics:
                similar_topic_articles = session.exec(
                    select(ArticleFrameworkLink, Article, ArticleAnalysis, Source)
                    .join(Article, ArticleFrameworkLink.article_id == Article.id)
                    .join(ArticleAnalysis, ArticleAnalysis.article_id == Article.id)
                    .join(Source, Source.id == Article.source_id)
                    .where(ArticleFrameworkLink.article_id != article.id)
                    .where(ArticleFrameworkLink.relevance_score > 0.5)  # Even higher threshold
                    .where(Article.topic_category.in_(similar_topics))
                    .where(Article.id.notin_([c["article_id"] for c in candidates]))
                    .order_by(ArticleFrameworkLink.relevance_score.desc())
                    .limit(max_results * 2)
                ).all()

                for opp_link, opp_article, opp_analysis, opp_source in similar_topic_articles:
                    best_opposition = self._find_best_framework_opposition(
                        primary_frameworks, opp_link, framework_dict, session
                    )

                    if best_opposition:
                        candidates.append(best_opposition)

        # Remove duplicates and rank by combined score
        unique_candidates = self._deduplicate_candidates(candidates)
        ranked_candidates = self._rank_candidates(unique_candidates)

        # Generate AI explanations for top candidates and add article metadata
        final_candidates = ranked_candidates[:max_results]

        for candidate in final_candidates:
            explanations = self._generate_framework_explanation(
                candidate, primary_frameworks, session
            )
            candidate["how_this_opposes"] = explanations["how_this_opposes"]
            candidate["why_this_opposes"] = explanations["why_this_opposes"]

            # Add article metadata that frontend expects
            opp_article = session.exec(select(Article).where(Article.id == candidate["article_id"])).first()
            opp_analysis = session.exec(select(ArticleAnalysis).where(ArticleAnalysis.article_id == candidate["article_id"])).first()
            opp_source = session.exec(select(Source).where(Source.id == opp_article.source_id)).first()

            if opp_article:
                candidate.update({
                    "title": opp_article.title,
                    "url": opp_article.url,
                    "summary": opp_analysis.summary if opp_analysis else None,
                    "sentiment_score": opp_analysis.sentiment_score if opp_analysis else None,
                    "source_name": opp_source.name if opp_source else None,
                    "published_at": opp_article.published_at.isoformat() if opp_article.published_at else None
                })

        logger.info(f"Found {len(final_candidates)} cross-framework opposing viewpoints")
        return final_candidates

    def _find_best_framework_opposition(
        self,
        primary_frameworks: List[ArticleFrameworkLink],
        opp_link: ArticleFrameworkLink,
        framework_dict: Dict[int, Framework],
        session: Session
    ) -> Optional[Dict[str, Any]]:
        """
        Find the best framework opposition between primary article frameworks and opposing article framework.

        This is the key innovation: we compare ALL possible framework pairs, not just same frameworks.
        """
        best_opposition = None
        best_score = 0.0

        # Get the opposing article's framework details
        opp_framework = framework_dict[opp_link.framework_id]

        for primary_link in primary_frameworks:
            primary_framework = framework_dict[primary_link.framework_id]

            # Calculate opposition strength
            position_gap = abs(primary_link.position_on_axis - opp_link.position_on_axis)
            relevance_avg = (primary_link.relevance_score + opp_link.relevance_score) / 2

            # Check if positions are actually opposing
            is_opposing = (
                (primary_link.position_on_axis > 2 and opp_link.position_on_axis < -2) or
                (primary_link.position_on_axis < -2 and opp_link.position_on_axis > 2) or
                position_gap >= 6  # Large gap also counts as opposition
            )

            if not is_opposing:
                continue

            # Calculate combined score
            position_score = min(position_gap / 10.0, 1.0)  # Normalize to 0-1
            combined_score = (position_score * 0.6) + (relevance_avg * 0.4)

            logger.info(f"Framework pair analysis:")
            logger.info(f"  Primary: {primary_framework.name} (pos: {primary_link.position_on_axis}, rel: {primary_link.relevance_score:.2f})")
            logger.info(f"  Opposing: {opp_framework.name} (pos: {opp_link.position_on_axis}, rel: {opp_link.relevance_score:.2f})")
            logger.info(f"  Position gap: {position_gap}, Combined score: {combined_score:.3f}")

            if combined_score > best_score:
                best_score = combined_score

                # Determine which framework provides the most meaningful opposition narrative
                if position_gap >= 8 or relevance_avg > 0.8:
                    # Use the framework with stronger relevance
                    chosen_framework = primary_framework if primary_link.relevance_score > opp_link.relevance_score else opp_framework
                    chosen_primary_link = primary_link if chosen_framework == primary_framework else opp_link
                    chosen_opp_link = opp_link if chosen_framework == primary_framework else primary_link
                else:
                    # Use primary article's framework for narrative consistency
                    chosen_framework = primary_framework
                    chosen_primary_link = primary_link
                    chosen_opp_link = opp_link

                best_opposition = {
                    "article_id": opp_link.article_id,
                    "relationship_type": "framework_opposition",
                    "relationship_strength": combined_score,
                    "opposition_strength": combined_score,  # Frontend expects this field
                    "relevance_score": relevance_avg,
                    "framework_name": chosen_framework.name,
                    "primary_position": chosen_primary_link.position_on_axis,
                    "opposing_position": chosen_opp_link.position_on_axis,
                    "position_gap": position_gap,
                    "primary_framework": primary_framework.name,
                    "opposing_framework": opp_framework.name
                }

        return best_opposition

    def _get_similar_topics(self, topic: str) -> List[str]:
        """Get list of topics similar to the given topic."""
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
        return similar_topics.get(topic, [])

    def _deduplicate_candidates(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate candidates (same article_id), keeping the best one."""
        seen_articles = set()
        unique_candidates = []

        for candidate in candidates:
            article_id = candidate["article_id"]
            if article_id not in seen_articles:
                seen_articles.add(article_id)
                unique_candidates.append(candidate)
            else:
                # Keep the candidate with higher relationship_strength
                existing_idx = next(i for i, c in enumerate(unique_candidates) if c["article_id"] == article_id)
                if candidate["relationship_strength"] > unique_candidates[existing_idx]["relationship_strength"]:
                    unique_candidates[existing_idx] = candidate

        return unique_candidates

    def _rank_candidates(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank candidates by combined score of strength and relevance."""
        def combined_score(candidate):
            strength = candidate["relationship_strength"]
            relevance = candidate["relevance_score"]
            position_gap = candidate.get("position_gap", 0)

            # Prioritize large position gaps and high relevance
            return (strength * 0.5) + (relevance * 0.3) + (min(position_gap / 10.0, 1.0) * 0.2)

        return sorted(candidates, key=combined_score, reverse=True)

    def _generate_framework_explanation(
        self,
        candidate: Dict[str, Any],
        primary_frameworks: List[ArticleFrameworkLink],
        session: Session
    ) -> Dict[str, str]:
        """Generate AI explanations for the framework opposition."""
        framework_name = candidate["framework_name"]
        primary_pos = candidate["primary_position"]
        opposing_pos = candidate["opposing_position"]
        position_gap = candidate["position_gap"]
        primary_framework = candidate.get("primary_framework", framework_name)
        opposing_framework = candidate.get("opposing_framework", framework_name)

        # Get article content for more detailed explanations
        opp_article = session.exec(select(Article).where(Article.id == candidate["article_id"])).first()
        opp_analysis = session.exec(select(ArticleAnalysis).where(ArticleAnalysis.article_id == candidate["article_id"])).first()

        # Extract key content themes for more specific explanations
        content_theme = ""
        if opp_analysis and opp_analysis.summary:
            # Extract key themes from summary (simplified approach)
            summary_text = opp_analysis.summary.lower()
            if any(word in summary_text for word in ['trump', 'election', 'political', 'campaign']):
                content_theme = "political leadership"
            elif any(word in summary_text for word in ['war', 'conflict', 'military', 'defense']):
                content_theme = "international conflict"
            elif any(word in summary_text for word in ['economy', 'market', 'financial', 'trade']):
                content_theme = "economic policy"
            elif any(word in summary_text for word in ['rights', 'freedom', 'justice', 'law']):
                content_theme = "civil liberties"
            elif any(word in summary_text for word in ['climate', 'environment', 'energy']):
                content_theme = "environmental policy"
            else:
                content_theme = "current events"

        # Generate "why this opposes" - focused on mechanism (old how_explanation)
        if primary_framework != opposing_framework:
            why_explanation = (
                f"Frames through '{opposing_framework}' lens vs '{primary_framework}' approach; "
                f"different ethical frameworks and value systems"
            )
        else:
            if primary_pos > 0 and opposing_pos < 0:
                why_explanation = f"Direct position reversal: +{primary_pos} → {opposing_pos} on {framework_name}"
            elif primary_pos < 0 and opposing_pos > 0:
                why_explanation = f"Direct position reversal: {primary_pos} → +{opposing_pos} on {framework_name}"
            else:
                why_explanation = f"Position contrast: {primary_pos} vs {opposing_pos} on {framework_name}"

        # Generate "how this opposes" - focused on content-specific reasoning (old why_explanation)
        if primary_framework != opposing_framework:
            how_explanation = (
                f"Regarding {content_theme}, this '{opposing_framework}' perspective (position {opposing_pos}) "
                f"challenges the primary article's '{primary_framework}' approach (position {primary_pos}), "
                f"offering contrasting policy solutions based on different ideological foundations."
            )
        else:
            if primary_pos > 0 and opposing_pos < 0:
                how_explanation = (
                    f"On {content_theme}, this article opposes the primary piece by advocating {framework_name} "
                    f"(position {opposing_pos}) against the positive stance ({primary_pos}), "
                    f"highlighting fundamental disagreements about effective approaches."
                )
            elif primary_pos < 0 and opposing_pos > 0:
                how_explanation = (
                    f"Regarding {content_theme}, this piece supports {framework_name} (position {opposing_pos}) "
                    f"contrasting with the primary article's resistance ({primary_pos}), "
                    f"revealing competing priorities in addressing this issue."
                )
            else:
                how_explanation = (
                    f"On {content_theme}, this article provides alternative {framework_name} insights "
                    f"(position {opposing_pos}) that complement or challenge the primary view (position {primary_pos}), "
                    f"expanding the policy discussion with different considerations."
                )

        # SWITCHED: The old "how" becomes "why" and the enhanced content-focused "how" becomes "how"
        return {
            "how_this_opposes": how_explanation,  # Content-focused explanation
            "why_this_opposes": why_explanation   # Mechanism-focused explanation
        }

    def save_opposing_viewpoints(
        self,
        article: Article,
        max_results: int = 10,
        session: Optional[Session] = None
    ) -> List[ViewpointRelationship]:
        """
        Find and save opposing viewpoints to the database using enhanced cross-framework analysis.

        This method:
        1. Finds opposing viewpoints using enhanced analysis
        2. Saves them as ViewpointRelationship objects in the database
        3. Returns the saved database objects

        Args:
            article: The primary article to find oppositions for
            max_results: Maximum number of viewpoints to find and save
            session: Database session

        Returns:
            List of saved ViewpointRelationship objects
        """
        if session is None:
            from ..database import get_session
            session = next(get_session())
            should_close_session = True
        else:
            should_close_session = False

        try:
            # First, find opposing viewpoints using the existing enhanced analyzer
            oppositions = self.find_opposing_viewpoints(article, max_results, session)

            saved_relationships = []

            for opposition in oppositions:
                # Check if this relationship already exists
                existing = session.exec(
                    select(ViewpointRelationship).where(
                        and_(
                            ViewpointRelationship.primary_article_id == article.id,
                            ViewpointRelationship.opposing_article_id == opposition["article_id"],
                            ViewpointRelationship.relationship_type == opposition["relationship_type"]
                        )
                    )
                ).first()

                if existing:
                    # Update existing relationship with enhanced fields
                    existing.how_this_opposes = opposition.get("how_this_opposes")
                    existing.why_this_opposes = opposition.get("why_this_opposes")
                    existing.framework_name = opposition.get("framework_name")
                    existing.primary_position = opposition.get("primary_position")
                    existing.opposing_position = opposition.get("opposing_position")
                    existing.reasoning = opposition.get("ai_explanation", opposition.get("why_this_opposes"))
                    existing.opposition_strength = opposition.get("opposition_strength", opposition.get("relationship_strength"))
                    existing.quality_score = opposition.get("relevance_score")
                    existing.ai_explanation = opposition.get("ai_explanation")
                    existing.updated_at = datetime.utcnow()

                    saved_relationships.append(existing)
                    logger.info(f"Updated existing viewpoint relationship: {article.id} -> {opposition['article_id']}")
                else:
                    # Create new ViewpointRelationship object
                    relationship = ViewpointRelationship(
                        primary_article_id=article.id,
                        opposing_article_id=opposition["article_id"],
                        relationship_type=opposition["relationship_type"],
                        opposition_strength=opposition.get("opposition_strength", opposition.get("relationship_strength", 0.5)),
                        ai_explanation=opposition.get("ai_explanation"),
                        framework_name=opposition.get("framework_name"),
                        reasoning=opposition.get("ai_explanation", opposition.get("why_this_opposes")),
                        primary_position=opposition.get("primary_position"),
                        opposing_position=opposition.get("opposing_position"),
                        how_this_opposes=opposition.get("how_this_opposes"),  # Enhanced field
                        why_this_opposes=opposition.get("why_this_opposes"),  # Enhanced field
                        quality_score=opposition.get("relevance_score"),
                        generation_method="enhanced_analyzer",
                        ai_model_version="gpt-4o-mini-enhanced",
                        processing_time_ms=opposition.get("processing_time_ms"),
                        is_active=True,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )

                    session.add(relationship)
                    saved_relationships.append(relationship)
                    logger.info(f"Created new viewpoint relationship: {article.id} -> {opposition['article_id']}")

            # Commit all changes
            session.commit()

            logger.info(f"Saved {len(saved_relationships)} viewpoint relationships for article {article.id}")
            return saved_relationships

        except Exception as e:
            session.rollback()
            logger.error(f"Error saving viewpoint relationships for article {article.id}: {e}", exc_info=True)
            raise
        finally:
            if should_close_session:
                session.close()

    @staticmethod
    def analyze_viewpoint_relationships(
        article_id: int,
        relationship_types: Optional[List[str]] = None,
        max_results: int = 10,
        session: Optional[Session] = None
    ) -> List[Dict[str, Any]]:
        """
        Main entry point for analyzing viewpoint relationships.
        """
        if session is None:
            from ..database import get_session
            session = next(get_session())

        if relationship_types is None:
            relationship_types = ["framework_opposition"]

        # Get article and analysis
        article = session.exec(select(Article).where(Article.id == article_id)).first()
        if not article:
            logger.error(f"Article {article_id} not found")
            return []

        analysis = session.exec(
            select(ArticleAnalysis).where(ArticleAnalysis.article_id == article_id)
        ).first()

        # Use enhanced analyzer
        analyzer = ViewpointAnalyzer(session)
        all_oppositions = []

        if "framework_opposition" in relationship_types:
            framework_oppositions = analyzer.find_opposing_viewpoints(
                article, max_results=max_results, session=session
            )
            all_oppositions.extend(framework_oppositions)

        # Note: Other relationship types (sentiment_contrast, temporal_evolution)
        # can be added here as needed

        if not all_oppositions:
            logger.info(f"No opposing viewpoints found for article {article_id}")
            return []

        logger.info(f"Returning {len(all_oppositions)} viewpoint relationships for article {article_id}")
        return all_oppositions[:max_results]