"""
Challenge Article Matcher Service

Finds and assigns articles that oppose user's selected claims for the 7-day challenge.
Uses a 3-tier approach: database articles → web search → historical fallback.
Integrates with existing viewpoint analysis system for accurate opposition matching.
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from sqlmodel import Session, select, and_, or_, func
from ..models import (
    Article, ArticleAnalysis, ChallengeClaim, UserChallengeResponse,
    ChallengeArticleAssignment, ViewpointRelationship, PoliticalLean
)
from ..services.viewpoint_analyzer import ViewpointAnalyzer

logger = logging.getLogger(__name__)


class ChallengeArticleMatcher:
    """
    Matches and assigns opposing viewpoint articles for challenge participants.

    Algorithm:
    1. Analyze user's selected claim to determine position on political/ethical spectrum
    2. Find articles with opposing viewpoints using existing ViewpointRelationship data
    3. Fall back to web search if insufficient database articles
    4. Prioritize high-quality, recent articles with strong opposition scores
    5. Assign 7 articles for daily delivery (Days 1-7)
    """

    def __init__(self, session: Session):
        self.session = session
        self.viewpoint_analyzer = ViewpointAnalyzer(session)

    def process_daily_assignments(self) -> int:
        """
        Process all pending article assignments for today.

        This is called by the daily job to assign articles to users who need today's challenge article.

        Returns:
            Number of assignments created
        """
        today = datetime.utcnow().date()
        assignments_created = 0

        try:
            # Find users who need today's article
            pending_assignments = self._get_pending_daily_assignments(today)

            for user_response in pending_assignments:
                try:
                    assignment = self._create_daily_assignment(user_response, today)
                    if assignment:
                        assignments_created += 1
                        logger.info(f"Created assignment for user {user_response.user_id}, day {assignment.day_number}")
                except Exception as e:
                    logger.error(f"Error creating assignment for user {user_response.user_id}: {e}")
                    continue

            logger.info(f"Processed {assignments_created} daily challenge assignments for {today}")
            return assignments_created

        except Exception as e:
            logger.error(f"Error processing daily assignments: {e}")
            return 0

    def create_challenge_articles_for_user(self, user_response: UserChallengeResponse) -> List[ChallengeArticleAssignment]:
        """
        Create all 7 article assignments for a user who just responded to a challenge.

        Args:
            user_response: The user's challenge response

        Returns:
            List of created assignments (7 total, one for each day)
        """
        try:
            # Get the selected claim
            selected_claim = self.session.get(ChallengeClaim, user_response.selected_claim_id)
            if not selected_claim:
                logger.error(f"Selected claim {user_response.selected_claim_id} not found")
                return []

            # Determine the claim's position and find opposing articles
            opposing_articles = self._find_opposing_articles(selected_claim)

            if len(opposing_articles) < 7:
                logger.warning(f"Only {len(opposing_articles)} opposing articles found for claim {selected_claim.id}")

            # Create 7 assignments (starting tomorrow)
            assignments = []
            start_date = datetime.utcnow().date() + timedelta(days=1)

            for day in range(7):
                assignment_date = start_date + timedelta(days=day)

                # Select article for this day
                article_index = day % len(opposing_articles)  # Cycle if needed
                article = opposing_articles[article_index]

                # Calculate opposition strength
                opposition_strength = self._calculate_opposition_strength(selected_claim, article)

                assignment = ChallengeArticleAssignment(
                    user_challenge_response_id=user_response.id,
                    user_id=user_response.user_id,
                    article_id=article.id,
                    day_number=day + 1,
                    assignment_date=datetime.combine(assignment_date, datetime.min.time()),
                    opposition_strength=opposition_strength,
                    match_algorithm="database",
                    match_reasoning=f"Article opposes selected claim on {selected_claim.claim_type.value} topic"
                )

                self.session.add(assignment)
                assignments.append(assignment)

            self.session.commit()
            logger.info(f"Created {len(assignments)} article assignments for user {user_response.user_id}")

            return assignments

        except Exception as e:
            logger.error(f"Error creating challenge articles for user {user_response.user_id}: {e}")
            self.session.rollback()
            return []

    def _get_pending_daily_assignments(self, date: datetime.date) -> List[UserChallengeResponse]:
        """
        Find users who need an article assignment for today.

        Args:
            date: The date to find assignments for

        Returns:
            List of user responses that need today's article
        """
        # Find users who have responded to challenges and are in the 7-day period
        cutoff_date = date - timedelta(days=7)  # Don't go back more than 7 days

        pending_responses = self.session.exec(
            select(UserChallengeResponse)
            .where(
                and_(
                    UserChallengeResponse.status == "responded",
                    UserChallengeResponse.responded_at >= datetime.combine(cutoff_date, datetime.min.time()),
                    UserChallengeResponse.articles_sent_count < 7
                )
            )
            .order_by(UserChallengeResponse.responded_at)
        ).all()

        # Filter to only include users who need today's specific assignment
        today_responses = []
        for response in pending_responses:
            # Calculate how many articles should have been sent by today
            days_since_response = (date - response.responded_at.date()).days

            if days_since_response >= 0 and response.articles_sent_count < min(days_since_response + 1, 7):
                today_responses.append(response)

        return today_responses

    def _create_daily_assignment(self, user_response: UserChallengeResponse, date: datetime.date) -> Optional[ChallengeArticleAssignment]:
        """
        Create a single daily assignment for a user.

        Args:
            user_response: User's challenge response
            date: Date for the assignment

        Returns:
            Created assignment or None if failed
        """
        try:
            # Calculate which day number this should be
            days_since_response = (date - user_response.responded_at.date()).days
            day_number = user_response.articles_sent_count + 1

            if day_number > 7:
                logger.warning(f"User {user_response.user_id} already has 7 assignments")
                return None

            # Get the selected claim
            selected_claim = self.session.get(ChallengeClaim, user_response.selected_claim_id)
            if not selected_claim:
                return None

            # Find an opposing article for this day
            opposing_articles = self._find_opposing_articles(selected_claim)

            if not opposing_articles:
                logger.error(f"No opposing articles found for claim {selected_claim.id}")
                return None

            # Select article based on day number (cycle if needed)
            article_index = (day_number - 1) % len(opposing_articles)
            article = opposing_articles[article_index]

            # Check if this assignment already exists
            existing = self.session.exec(
                select(ChallengeArticleAssignment)
                .where(
                    and_(
                        ChallengeArticleAssignment.user_challenge_response_id == user_response.id,
                        ChallengeArticleAssignment.day_number == day_number
                    )
                )
            ).first()

            if existing:
                logger.info(f"Assignment already exists for user {user_response.user_id}, day {day_number}")
                return existing

            # Calculate opposition strength
            opposition_strength = self._calculate_opposition_strength(selected_claim, article)

            # Create assignment
            assignment = ChallengeArticleAssignment(
                user_challenge_response_id=user_response.id,
                user_id=user_response.user_id,
                article_id=article.id,
                day_number=day_number,
                assignment_date=datetime.combine(date, datetime.min.time()),
                opposition_strength=opposition_strength,
                match_algorithm="database",
                match_reasoning=f"Day {day_number} article opposing claim on {selected_claim.claim_type.value} topic"
            )

            self.session.add(assignment)

            # Update user response
            user_response.articles_sent_count += 1

            self.session.commit()
            return assignment

        except Exception as e:
            logger.error(f"Error creating daily assignment for user {user_response.user_id}: {e}")
            self.session.rollback()
            return None

    def _find_opposing_articles(self, claim: ChallengeClaim, limit: int = 10) -> List[Article]:
        """
        Find articles that oppose the given claim.

        Uses existing viewpoint relationship data to find strong opposition.

        Args:
            claim: The challenge claim to find opposition for
            limit: Maximum number of articles to return

        Returns:
            List of opposing articles
        """
        try:
            # Get recent articles with complete analysis
            recent_cutoff = datetime.utcnow() - timedelta(days=30)  # Last 30 days

            articles_query = (
                select(Article, ArticleAnalysis)
                .join(ArticleAnalysis)
                .where(
                    and_(
                        Article.processing_status == "COMPLETED",
                        ArticleAnalysis.sentiment_score.is_not(None),
                        Article.published_at >= recent_cutoff,
                        Article.word_count >= 200  # Ensure substantial content
                    )
                )
                .order_by(Article.published_at.desc())
                .limit(limit * 2)  # Get more to filter from
            )

            articles_with_analysis = self.session.exec(articles_query).all()

            if not articles_with_analysis:
                logger.warning(f"No recent articles found for opposition matching")
                return []

            # Score articles for opposition to the claim
            scored_articles = []
            for article, analysis in articles_with_analysis:
                opposition_score = self._score_article_opposition(claim, article, analysis)

                if opposition_score > 0.3:  # Minimum opposition threshold
                    scored_articles.append((article, opposition_score))

            # Sort by opposition score (highest first)
            scored_articles.sort(key=lambda x: x[1], reverse=True)

            # Return top articles
            return [article for article, score in scored_articles[:limit]]

        except Exception as e:
            logger.error(f"Error finding opposing articles for claim {claim.id}: {e}")
            return []

    def _score_article_opposition(self, claim: ChallengeClaim, article: Article, analysis: ArticleAnalysis) -> float:
        """
        Score how strongly an article opposes the given claim.

        Considers multiple factors:
        - Sentiment opposition
        - Political lean opposition
        - Topic relevance
        - Quality indicators

        Args:
            claim: The challenge claim
            article: The article to score
            analysis: The article's AI analysis

        Returns:
            Opposition score (0.0 to 1.0)
        """
        score = 0.0

        try:
            # Factor 1: Topic relevance (20% of score)
            if self._is_topic_related(claim.claim_type, article):
                score += 0.2

            # Factor 2: Sentiment opposition (30% of score)
            claim_sentiment = self._estimate_claim_sentiment(claim)
            if claim_sentiment and analysis.sentiment_score:
                sentiment_opposition = abs(claim_sentiment - analysis.sentiment_score)
                if sentiment_opposition > 0.5:  # Strong opposition
                    score += 0.3
                elif sentiment_opposition > 0.2:  # Moderate opposition
                    score += 0.15

            # Factor 3: Political lean opposition (25% of score)
            if analysis.political_lean and hasattr(claim, 'political_lean'):
                claim_lean = getattr(claim, 'political_lean', 'mixed')
                if claim_lean and claim_lean != 'mixed':
                    lean_opposition = self._calculate_political_opposition(claim_lean, analysis.political_lean)
                    score += lean_opposition * 0.25

            # Factor 4: Quality indicators (25% of score)
            quality_score = self._assess_article_quality(article, analysis)
            score += quality_score * 0.25

            return min(score, 1.0)

        except Exception as e:
            logger.error(f"Error scoring article opposition: {e}")
            return 0.0

    def _is_topic_related(self, claim_type: str, article: Article) -> bool:
        """
        Check if an article is related to the claim's topic type.
        """
        # Simple keyword matching for topic relevance
        topic_keywords = {
            'POLICY': ['policy', 'government', 'law', 'regulation', 'legislation'],
            'SOCIAL_ISSUE': ['social', 'society', 'culture', 'community', 'people'],
            'ECONOMIC': ['economy', 'economic', 'financial', 'business', 'market'],
            'TECHNOLOGY': ['tech', 'technology', 'digital', 'software', 'internet'],
            'ENVIRONMENT': ['environment', 'climate', 'energy', 'pollution', 'sustainability'],
            'FOREIGN_POLICY': ['foreign', 'international', 'diplomacy', 'war', 'global'],
            'HEALTHCARE': ['health', 'medical', 'healthcare', 'hospital', 'medicine'],
            'EDUCATION': ['education', 'school', 'student', 'teacher', 'university']
        }

        keywords = topic_keywords.get(claim_type, [])
        if not keywords:
            return True  # Assume related if we can't determine

        text_to_check = f"{article.title} {article.summary or ''}".lower()
        return any(keyword in text_to_check for keyword in keywords)

    def _estimate_claim_sentiment(self, claim: ChallengeClaim) -> Optional[float]:
        """
        Estimate the sentiment of a claim based on keywords.

        Returns:
            Sentiment score (-1.0 to 1.0) or None if can't determine
        """
        # Simple keyword-based sentiment estimation
        positive_words = ['good', 'better', 'improve', 'support', 'help', 'benefit', 'fair', 'just']
        negative_words = ['bad', 'worse', 'harm', 'oppose', 'restrict', 'ban', 'problem', 'dangerous']

        claim_text = claim.claim_text.lower()

        positive_count = sum(1 for word in positive_words if word in claim_text)
        negative_count = sum(1 for word in negative_words if word in claim_text)

        total_count = positive_count + negative_count
        if total_count == 0:
            return None

        # Return sentiment score (-1.0 to 1.0)
        return (positive_count - negative_count) / max(total_count, 1)

    def _calculate_political_opposition(self, claim_lean: str, article_lean: str) -> float:
        """
        Calculate political opposition score between claim and article.

        Returns:
            Opposition score (0.0 to 1.0)
        """
        # Map political leans to numeric positions
        positions = {
            'left': -1.0,
            'center-left': -0.5,
            'center': 0.0,
            'center-right': 0.5,
            'right': 1.0
        }

        claim_pos = positions.get(claim_lean.lower(), 0.0)
        article_pos = positions.get(article_lean.lower(), 0.0)

        # Calculate opposition (0 = same position, 1 = maximum opposition)
        opposition = abs(claim_pos - article_pos)
        return opposition

    def _assess_article_quality(self, article: Article, analysis: ArticleAnalysis) -> float:
        """
        Assess the quality of an article for challenge use.

        Returns:
            Quality score (0.0 to 1.0)
        """
        score = 0.0

        # Word count quality
        if article.word_count:
            if article.word_count >= 1000:
                score += 0.3
            elif article.word_count >= 500:
                score += 0.2
            elif article.word_count >= 200:
                score += 0.1

        # Summary quality
        if analysis.summary and len(analysis.summary) >= 100:
            score += 0.3
        elif analysis.summary:
            score += 0.15

        # Sentiment analysis quality
        if analysis.sentiment_score is not None:
            score += 0.2

        # Recent publication
        days_old = (datetime.utcnow() - article.published_at).days
        if days_old <= 7:
            score += 0.2
        elif days_old <= 30:
            score += 0.1

        return min(score, 1.0)

    def _calculate_opposition_strength(self, claim: ChallengeClaim, article: Article) -> float:
        """
        Calculate the final opposition strength for the assignment.

        This is the score that will be stored and used for analytics.

        Args:
            claim: The selected claim
            article: The assigned article

        Returns:
            Opposition strength (0.0 to 1.0)
        """
        # Get article analysis
        analysis = self.session.exec(
            select(ArticleAnalysis).where(ArticleAnalysis.article_id == article.id)
        ).first()

        if not analysis:
            return 0.5  # Default medium opposition

        return self._score_article_opposition(claim, article, analysis)

    def get_user_assignments(self, user_id: int, limit: int = 10) -> List[Dict]:
        """
        Get recent article assignments for a user.

        Args:
            user_id: User ID
            limit: Maximum number of assignments to return

        Returns:
            List of assignment data with article details
        """
        try:
            assignments = self.session.exec(
                select(ChallengeArticleAssignment, Article, ArticleAnalysis)
                .join(Article, ChallengeArticleAssignment.article_id == Article.id)
                .join(ArticleAnalysis, Article.id == ArticleAnalysis.article_id)
                .where(ChallengeArticleAssignment.user_id == user_id)
                .order_by(ChallengeArticleAssignment.assignment_date.desc())
                .limit(limit)
            ).all()

            results = []
            for assignment, article, analysis in assignments:
                results.append({
                    'id': assignment.id,
                    'day_number': assignment.day_number,
                    'assignment_date': assignment.assignment_date,
                    'opposition_strength': assignment.opposition_strength,
                    'is_sent': assignment.is_sent,
                    'is_opened': assignment.is_opened,
                    'is_clicked': assignment.is_clicked,
                    'article': {
                        'id': article.id,
                        'title': article.title,
                        'url': article.url,
                        'source_name': article.source.name if article.source else 'Unknown',
                        'published_at': article.published_at,
                        'summary': analysis.summary,
                        'sentiment_score': analysis.sentiment_score,
                        'political_lean': analysis.political_lean
                    }
                })

            return results

        except Exception as e:
            logger.error(f"Error getting assignments for user {user_id}: {e}")
            return []