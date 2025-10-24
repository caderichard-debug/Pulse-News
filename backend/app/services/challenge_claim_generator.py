"""
Challenge Claim Generator Service

Generates controversial ethical claims from current news articles for weekly challenges.
Uses AI analysis to create balanced, thought-provoking claims across different topics.
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from sqlmodel import Session, select, and_, or_, func
from ..models import (
    Article, ArticleAnalysis, ChallengeClaim, ChallengeClaimType,
    WeeklyChallenge, PoliticalLean, Source, Framework
)
from ..utils.openai_client import openai_client

logger = logging.getLogger(__name__)


class ChallengeClaimGenerator:
    """
    Generates ethical claims for weekly challenges based on current news articles.

    Process:
    1. Analyze articles from past 7 days for ethical dilemmas
    2. Generate claims at philosophical/ethical level (not factual)
    3. Score claims for controversy and reasonableness
    4. Balance political perspectives across claims
    5. Filter for quality and appropriateness
    """

    def __init__(self, session: Session):
        self.session = session
        self.openai_client = openai_client

    def generate_claims_for_week(self, target_count: int = 8) -> List[Dict]:
        """
        Generate candidate claims for the current week.

        Args:
            target_count: Number of claims to generate (default 8 for selection of 4)

        Returns:
            List of claim dictionaries with metadata
        """
        logger.info(f"Generating {target_count} challenge claims for the week")

        # Get recent articles with complete analysis
        recent_articles = self._get_recent_analyzed_articles()

        if not recent_articles:
            logger.warning("No recent articles found for claim generation")
            return []

        # Group articles by topic for focused claim generation
        topic_groups = self._group_articles_by_topic(recent_articles)

        generated_claims = []

        # Generate claims from each topic group
        for topic, articles in topic_groups.items():
            if len(generated_claims) >= target_count:
                break

            topic_claims = self._generate_claims_from_topic(topic, articles)
            generated_claims.extend(topic_claims)

        # If still insufficient claims, generate from general news themes
        if len(generated_claims) < target_count:
            additional_claims = self._generate_general_theme_claims(
                target_count - len(generated_claims),
                recent_articles
            )
            generated_claims.extend(additional_claims)

        # Score and filter claims
        scored_claims = self._score_and_filter_claims(generated_claims)

        logger.info(f"Generated {len(scored_claims)} scored claims")
        return scored_claims[:target_count]

    def _get_recent_analyzed_articles(self, days_back: int = 7) -> List[Article]:
        """Get recent articles with complete analysis."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)

        query = (
            select(Article)
            .join(ArticleAnalysis)
            .where(
                and_(
                    Article.published_at >= cutoff_date,
                    Article.processing_status == "COMPLETED",
                    ArticleAnalysis.sentiment_score.is_not(None),
                    Article.word_count >= 200  # Ensure substantial content
                )
            )
            .order_by(Article.published_at.desc())
            .limit(50)  # Limit to prevent overwhelming the AI
        )

        return list(self.session.exec(query).all())

    def _group_articles_by_topic(self, articles: List[Article]) -> Dict[str, List[Article]]:
        """Group articles by topic category for focused claim generation."""
        topic_groups = {}

        for article in articles:
            # Use topic_category or default to "general"
            topic = article.topic_category or "general"

            if topic not in topic_groups:
                topic_groups[topic] = []
            topic_groups[topic].append(article)

        return topic_groups

    def _generate_claims_from_topic(self, topic: str, articles: List[Article]) -> List[Dict]:
        """Generate claims from articles on a specific topic."""
        if len(articles) < 2:
            return []

        # Prepare article summaries for context
        article_summaries = []
        for article in articles[:5]:  # Limit to prevent context overflow
            if article.analysis:
                summary = f"Title: {article.title}\nSummary: {article.analysis.summary}\n"
                if article.analysis.sentiment_score:
                    sentiment = "positive" if article.analysis.sentiment_score > 0 else "negative"
                    summary += f"Sentiment: {sentiment}\n"
                article_summaries.append(summary)

        if not article_summaries:
            return []

        # Generate claims using AI
        claim_prompt = self._build_claim_generation_prompt(topic, article_summaries)

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at identifying ethical dilemmas and philosophical questions in current events. Generate claims that are debatable but reasonable, focusing on ethical frameworks rather than specific facts."
                    },
                    {
                        "role": "user",
                        "content": claim_prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1000
            )

            claims_text = response.choices[0].message.content
            return self._parse_ai_claims_response(claims_text, topic, articles)

        except Exception as e:
            logger.error(f"Error generating claims for topic {topic}: {e}")
            return []

    def _build_claim_generation_prompt(self, topic: str, article_summaries: List[str]) -> str:
        """Build the prompt for AI claim generation."""
        return f"""
Based on recent news articles about {topic}, generate 2-3 controversial ethical claims at the philosophical level.

Requirements:
- Focus on ethical frameworks, not specific facts or events
- Make claims debatable but reasonable (avoid extreme positions)
- Each claim should be max 300 characters
- Consider multiple perspectives (individual vs collective, freedom vs safety, etc.)
- Avoid misinformation and unverified claims
- Claims should make people think about their ethical positions

Recent articles context:
{chr(10).join(article_summaries)}

Please format your response as a JSON array with objects containing:
- claim_text: the ethical claim
- reasoning: brief explanation of why this is an ethical dilemma
- controversy_estimate: your estimate of controversy (0.0-1.0)
- political_lean: likely political alignment (left/center/right/mixed)

Example format:
[
  {{
    "claim_text": "Individual privacy rights should never be compromised for national security",
    "reasoning": "This pits fundamental privacy against collective security needs",
    "controversy_estimate": 0.8,
    "political_lean": "mixed"
  }}
]
"""

    def _parse_ai_claims_response(self, claims_text: str, topic: str, source_articles: List[Article]) -> List[Dict]:
        """Parse the AI response into structured claim data."""
        import json

        try:
            # Try to parse as JSON first
            claims = json.loads(claims_text)

            # Validate and enrich claims
            validated_claims = []
            for claim in claims:
                if self._validate_claim(claim):
                    enriched_claim = self._enrich_claim_data(claim, topic, source_articles)
                    validated_claims.append(enriched_claim)

            return validated_claims

        except json.JSONDecodeError:
            # Fallback: try to extract claims from text
            return self._extract_claims_from_text(claims_text, topic, source_articles)

    def _validate_claim(self, claim: Dict) -> bool:
        """Validate that a claim meets minimum requirements."""
        required_fields = ['claim_text', 'reasoning']

        if not all(field in claim for field in required_fields):
            return False

        # Check claim text length
        claim_text = claim.get('claim_text', '')
        if len(claim_text) < 20 or len(claim_text) > 300:
            return False

        # Check for obvious factual claims (avoid these)
        factual_indicators = ['study shows', 'research proves', 'data indicates', 'survey found']
        claim_lower = claim_text.lower()

        for indicator in factual_indicators:
            if indicator in claim_lower:
                return False

        return True

    def _enrich_claim_data(self, claim: Dict, topic: str, source_articles: List[Article]) -> Dict:
        """Enrich claim data with additional metadata."""
        enriched = claim.copy()

        # Determine claim type from topic
        enriched['claim_type'] = self._map_topic_to_claim_type(topic)

        # Add source article references
        enriched['source_article_ids'] = [article.id for article in source_articles[:3]]
        enriched['source_topic'] = topic

        # Normalize political lean
        political_lean = claim.get('political_lean', 'mixed').lower()
        if political_lean not in ['left', 'center', 'right', 'mixed']:
            political_lean = 'mixed'
        enriched['political_lean'] = political_lean

        # Set default controversy if not provided
        if 'controversy_estimate' not in enriched:
            enriched['controversy_estimate'] = 0.5

        return enriched

    def _map_topic_to_claim_type(self, topic: str) -> ChallengeClaimType:
        """Map article topic to challenge claim type."""
        topic_mapping = {
            'health': ChallengeClaimType.HEALTHCARE,
            'education': ChallengeClaimType.EDUCATION,
            'environment': ChallengeClaimType.ENVIRONMENT,
            'technology': ChallengeClaimType.TECHNOLOGY,
            'economy': ChallengeClaimType.ECONOMIC,
            'foreign': ChallengeClaimType.FOREIGN_POLICY,
            'social': ChallengeClaimType.SOCIAL_ISSUE,
        }

        topic_lower = topic.lower()
        for key, claim_type in topic_mapping.items():
            if key in topic_lower:
                return claim_type

        return ChallengeClaimType.POLICY  # Default

    def _extract_claims_from_text(self, text: str, topic: str, source_articles: List[Article]) -> List[Dict]:
        """Extract claims from unstructured text response."""
        # This is a fallback method - basic text parsing
        claims = []

        # Split by common claim indicators
        claim_indicators = ['\n', '.', ';']

        for indicator in claim_indicators:
            if indicator in text:
                potential_claims = text.split(indicator)
                break
        else:
            potential_claims = [text]

        for potential in potential_claims:
            potential = potential.strip()
            if len(potential) > 30 and len(potential) < 300:
                # Basic validation
                if self._looks_like_ethical_claim(potential):
                    claim = {
                        'claim_text': potential,
                        'reasoning': f'Ethical claim related to {topic}',
                        'controversy_estimate': 0.5,
                        'political_lean': 'mixed'
                    }
                    enriched = self._enrich_claim_data(claim, topic, source_articles)
                    claims.append(enriched)

        return claims[:3]  # Limit fallback claims

    def _looks_like_ethical_claim(self, text: str) -> bool:
        """Basic heuristic to determine if text looks like an ethical claim."""
        ethical_indicators = [
            'should', 'must', 'never', 'always', 'rights', 'justice', 'fair',
            'moral', 'ethical', 'wrong', 'right', 'principle', 'value'
        ]

        text_lower = text.lower()
        return any(indicator in text_lower for indicator in ethical_indicators)

    def _generate_general_theme_claims(self, target_count: int, articles: List[Article]) -> List[Dict]:
        """Generate claims from general news themes when topic-specific generation is insufficient."""
        # Identify broad themes from articles
        themes = self._identify_broad_themes(articles)

        claims = []
        for theme in themes:
            if len(claims) >= target_count:
                break

            theme_claims = self._generate_claims_from_theme(theme, articles)
            claims.extend(theme_claims)

        return claims[:target_count]

    def _identify_broad_themes(self, articles: List[Article]) -> List[str]:
        """Identify broad themes from article titles and summaries."""
        themes = []

        # Common broad themes in news
        potential_themes = [
            'privacy vs security',
            'individual freedom vs collective good',
            'economic inequality',
            'technological progress vs tradition',
            'environmental protection vs economic growth',
            'free speech vs hate speech regulation'
        ]

        # Simple keyword matching in article titles
        article_texts = [article.title.lower() for article in articles]
        article_texts.extend([article.analysis.summary.lower() if article.analysis else '' for article in articles])

        all_text = ' '.join(article_texts)

        for theme in potential_themes:
            theme_keywords = theme.split(' vs ')
            if any(keyword in all_text for keyword in theme_keywords):
                themes.append(theme)

        return themes

    def _generate_claims_from_theme(self, theme: str, articles: List[Article]) -> List[Dict]:
        """Generate claims from a broad ethical theme."""
        # Create a simplified prompt for theme-based generation
        theme_prompt = f"""
Generate 2 ethical claims related to the theme: {theme}

Requirements:
- Claims should be under 300 characters
- Focus on the ethical tension in this theme
- Make claims thought-provoking but reasonable
- Avoid extreme positions

Format as JSON:
[
  {{
    "claim_text": "claim here",
    "reasoning": "brief explanation",
    "controversy_estimate": 0.6,
    "political_lean": "mixed"
  }}
]
"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at ethical analysis. Generate balanced, thought-provoking claims."
                    },
                    {
                        "role": "user",
                        "content": theme_prompt
                    }
                ],
                temperature=0.7,
                max_tokens=500
            )

            claims_text = response.choices[0].message.content
            return self._parse_ai_claims_response(claims_text, theme, articles)

        except Exception as e:
            logger.error(f"Error generating theme-based claims for {theme}: {e}")
            return []

    def _score_and_filter_claims(self, claims: List[Dict]) -> List[Dict]:
        """Score claims for quality and filter out low-quality ones."""
        scored_claims = []

        for claim in claims:
            score = self._calculate_claim_score(claim)
            claim['quality_score'] = score

            # Filter out low-quality claims
            if score >= 0.3:
                scored_claims.append(claim)

        # Sort by quality score (highest first)
        scored_claims.sort(key=lambda x: x['quality_score'], reverse=True)

        return scored_claims

    def _calculate_claim_score(self, claim: Dict) -> float:
        """Calculate quality score for a claim."""
        score = 0.0

        # Base score for having required fields
        if 'claim_text' in claim and 'reasoning' in claim:
            score += 0.3

        claim_text = claim.get('claim_text', '')

        # Length appropriateness
        if 50 <= len(claim_text) <= 200:
            score += 0.2
        elif 30 <= len(claim_text) <= 300:
            score += 0.1

        # Controversy level (moderate controversy is good)
        controversy = claim.get('controversy_estimate', 0.5)
        if 0.3 <= controversy <= 0.8:
            score += 0.2
        elif 0.2 <= controversy <= 0.9:
            score += 0.1

        # Ethical language indicators
        ethical_words = ['should', 'must', 'rights', 'justice', 'fair', 'moral', 'ethical', 'value']
        if any(word in claim_text.lower() for word in ethical_words):
            score += 0.2

        # Reasoning quality
        reasoning = claim.get('reasoning', '')
        if len(reasoning) > 20 and any(word in reasoning.lower() for word in ['ethical', 'moral', 'principle', 'tension', 'balance']):
            score += 0.1

        return min(score, 1.0)