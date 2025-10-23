"""
Weekly Challenge Manager Service

Orchestrates the creation, selection, and publishing of weekly challenge sets.
Manages the weekly workflow from claim generation to challenge publication.
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from sqlmodel import Session, select, and_, or_, func
from ..models import (
    WeeklyChallenge, ChallengeClaim, ChallengeClaimType, PoliticalLean,
    User, UserChallengeResponse, ChallengeResponseStatus
)
from .challenge_claim_generator import ChallengeClaimGenerator

logger = logging.getLogger(__name__)


class ChallengeManager:
    """
    Manages the weekly challenge creation and publication workflow.

    Weekly Schedule:
    - Wednesday 2:00 PM PST: Generate claims and select 4 for challenge
    - Friday: Publish challenge in newsletter
    - Following Friday-Sunday: Process user responses
    - Daily: Send challenge articles to respondents
    """

    def __init__(self, session: Session):
        self.session = session
        self.claim_generator = ChallengeClaimGenerator(session)

    def create_weekly_challenge(self, week_start_date: Optional[datetime] = None) -> Optional[WeeklyChallenge]:
        """
        Create a new weekly challenge with 4 balanced claims.

        Args:
            week_start_date: Monday of the challenge week (defaults to next Monday)

        Returns:
            Created WeeklyChallenge or None if creation failed
        """
        if week_start_date is None:
            week_start_date = self._get_next_monday()

        logger.info(f"Creating weekly challenge for week starting {week_start_date}")

        # Check if challenge already exists for this week
        existing = self._get_challenge_for_week(week_start_date)
        if existing:
            logger.warning(f"Challenge already exists for week {week_start_date}")
            return existing

        try:
            # Generate candidate claims
            candidate_claims = self.claim_generator.generate_claims_for_week(target_count=12)

            if len(candidate_claims) < 4:
                logger.error(f"Insufficient claims generated: {len(candidate_claims)}")
                return None

            # Select and balance 4 claims
            selected_claims = self._select_balanced_claims(candidate_claims)

            if len(selected_claims) < 4:
                logger.error(f"Insufficient balanced claims selected: {len(selected_claims)}")
                return None

            # Create weekly challenge record
            weekly_challenge = WeeklyChallenge(
                week_start_date=week_start_date,
                week_end_date=week_start_date + timedelta(days=6),  # Sunday
                challenge_date=week_start_date + timedelta(days=4),  # Friday
                title=self._generate_challenge_title(selected_claims),
                description=self._generate_challenge_description(selected_claims),
                generation_method="automatic",
                ai_model_version="gpt-4o-mini",
                is_published=False  # Will be published after admin review
            )

            self.session.add(weekly_challenge)
            self.session.flush()  # Get the ID

            # Create claim records
            for i, claim_data in enumerate(selected_claims, 1):
                claim = ChallengeClaim(
                    weekly_challenge_id=weekly_challenge.id,
                    claim_text=claim_data['claim_text'],
                    claim_type=claim_data['claim_type'],
                    background_context=claim_data.get('reasoning', ''),
                    political_lean_distribution=claim_data.get('political_lean', 'mixed'),
                    controversy_score=claim_data.get('controversy_estimate', 0.5),
                    reasonableness_score=1.0 - claim_data.get('controversy_estimate', 0.5),
                    source_topic_ids=','.join(map(str, claim_data.get('source_article_ids', []))),
                    display_order=i,
                    generation_method="automatic",
                    ai_prompt_used="standard_claim_generation"
                )
                self.session.add(claim)

            # Check if admin review is needed
            max_controversy = max(claim.get('controversy_estimate', 0.5) for claim in selected_claims)
            if max_controversy > 0.8:
                weekly_challenge.needs_admin_review = True
                weekly_challenge.admin_review_notes = f"High controversy score: {max_controversy:.2f}"

            self.session.commit()
            logger.info(f"Created weekly challenge {weekly_challenge.id} with {len(selected_claims)} claims")

            return weekly_challenge

        except Exception as e:
            logger.error(f"Error creating weekly challenge: {e}")
            self.session.rollback()
            return None

    def publish_weekly_challenge(self, challenge_id: int) -> bool:
        """
        Publish a weekly challenge for delivery in newsletters.

        Args:
            challenge_id: ID of the weekly challenge to publish

        Returns:
            True if successful, False otherwise
        """
        try:
            challenge = self.session.get(WeeklyChallenge, challenge_id)
            if not challenge:
                logger.error(f"Challenge {challenge_id} not found")
                return False

            if challenge.is_published:
                logger.warning(f"Challenge {challenge_id} already published")
                return True

            # Verify the challenge has 4 claims
            claims_query = select(ChallengeClaim).where(
                ChallengeClaim.weekly_challenge_id == challenge_id
            )
            claims = list(self.session.exec(claims_query).all())

            if len(claims) != 4:
                logger.error(f"Challenge {challenge_id} has {len(claims)} claims, expected 4")
                return False

            # Mark as published
            challenge.is_published = True
            challenge.published_at = datetime.utcnow()

            self.session.commit()
            logger.info(f"Published weekly challenge {challenge_id}")
            return True

        except Exception as e:
            logger.error(f"Error publishing weekly challenge {challenge_id}: {e}")
            self.session.rollback()
            return False

    def get_current_challenge(self) -> Optional[WeeklyChallenge]:
        """Get the current week's published challenge."""
        today = datetime.utcnow().date()
        monday = today - timedelta(days=today.weekday())  # Current Monday

        query = select(WeeklyChallenge).where(
            and_(
                WeeklyChallenge.week_start_date == monday,
                WeeklyChallenge.is_published == True
            )
        )

        return self.session.exec(query).first()

    def get_challenge_by_date(self, week_date: datetime) -> Optional[WeeklyChallenge]:
        """Get challenge for a specific week date."""
        monday = week_date.date() - timedelta(days=week_date.weekday())

        query = select(WeeklyChallenge).where(
            and_(
                WeeklyChallenge.week_start_date == monday,
                WeeklyChallenge.is_published == True
            )
        )

        return self.session.exec(query).first()

    def get_user_challenge_response(self, user_id: int, week_date: datetime) -> Optional[UserChallengeResponse]:
        """Get user's response for a specific week."""
        challenge = self.get_challenge_by_date(week_date)
        if not challenge:
            return None

        query = select(UserChallengeResponse).where(
            and_(
                UserChallengeResponse.user_id == user_id,
                UserChallengeResponse.weekly_challenge_id == challenge.id
            )
        )

        return self.session.exec(query).first()

    def can_user_respond_to_challenge(self, user_id: int, challenge_id: int) -> Tuple[bool, str]:
        """
        Check if a user can respond to a challenge.

        Returns:
            Tuple of (can_respond, reason)
        """
        # Check if user has already responded
        existing_response = select(UserChallengeResponse).where(
            and_(
                UserChallengeResponse.user_id == user_id,
                UserChallengeResponse.weekly_challenge_id == challenge_id
            )
        )

        response = self.session.exec(existing_response).first()
        if response:
            if response.status == ChallengeResponseStatus.RESPONDED:
                return False, "You have already responded to this week's challenge"
            elif response.status == ChallengeResponseStatus.COMPLETED:
                return False, "You have already completed this week's challenge"

        # Check if challenge is still active for responses
        challenge = self.session.get(WeeklyChallenge, challenge_id)
        if not challenge:
            return False, "Challenge not found"

        if not challenge.is_published:
            return False, "Challenge is not yet published"

        # Check if it's too late to respond (after Sunday)
        now = datetime.utcnow()
        if now > challenge.week_end_date + timedelta(days=1):  # Give until Monday
            return False, "The response period for this challenge has ended"

        return True, "You can respond to this challenge"

    def get_upcoming_challenges(self, limit: int = 5) -> List[WeeklyChallenge]:
        """Get upcoming challenges for admin review."""
        query = select(WeeklyChallenge).where(
            WeeklyChallenge.is_published == False
        ).order_by(WeeklyChallenge.created_at.desc()).limit(limit)

        return list(self.session.exec(query).all())

    def get_challenge_statistics(self, challenge_id: int) -> Dict:
        """Get participation statistics for a challenge."""
        challenge = self.session.get(WeeklyChallenge, challenge_id)
        if not challenge:
            return {}

        # Count total responses
        responses_query = select(func.count(UserChallengeResponse.id)).where(
            UserChallengeResponse.weekly_challenge_id == challenge_id
        )
        total_responses = self.session.exec(responses_query).one()

        # Count responses by claim
        claim_responses_query = select(
            ChallengeClaim.id,
            ChallengeClaim.claim_text,
            func.count(UserChallengeResponse.id).label('response_count')
        ).join(
            UserChallengeResponse,
            ChallengeClaim.id == UserChallengeResponse.selected_claim_id
        ).where(
            UserChallengeResponse.weekly_challenge_id == challenge_id
        ).group_by(ChallengeClaim.id, ChallengeClaim.claim_text)

        claim_stats = {}
        for claim_id, claim_text, count in self.session.exec(claim_responses_query):
            claim_stats[claim_id] = {
                'claim_text': claim_text,
                'response_count': count
            }

        # Count by agreement level
        agreement_query = select(
            UserChallengeResponse.agreement_level,
            func.count(UserChallengeResponse.id).label('count')
        ).where(
            UserChallengeResponse.weekly_challenge_id == challenge_id
        ).group_by(UserChallengeResponse.agreement_level)

        agreement_stats = {}
        for agreement_level, count in self.session.exec(agreement_query):
            agreement_stats[agreement_level.value] = count

        return {
            'challenge_id': challenge_id,
            'title': challenge.title,
            'week_start_date': challenge.week_start_date,
            'total_responses': total_responses,
            'claim_statistics': claim_stats,
            'agreement_distribution': agreement_stats
        }

    def _get_next_monday(self) -> datetime:
        """Get the next Monday date."""
        today = datetime.utcnow().date()
        days_until_monday = (7 - today.weekday()) % 7 or 7
        next_monday = today + timedelta(days=days_until_monday)
        return datetime.combine(next_monday, datetime.min.time())

    def _get_challenge_for_week(self, week_start_date: datetime) -> Optional[WeeklyChallenge]:
        """Check if a challenge already exists for the given week."""
        query = select(WeeklyChallenge).where(
            WeeklyChallenge.week_start_date == week_start_date
        )
        return self.session.exec(query).first()

    def _select_balanced_claims(self, candidate_claims: List[Dict]) -> List[Dict]:
        """
        Select 4 balanced claims from candidates.

        Selection criteria:
        - Mix of controversy levels (calm to controversial)
        - Political balance if possible
        - Different claim types
        - High quality scores
        """
        if len(candidate_claims) <= 4:
            return candidate_claims

        # Sort by quality score
        sorted_claims = sorted(candidate_claims, key=lambda x: x.get('quality_score', 0), reverse=True)

        # Take top candidates for selection
        top_candidates = sorted_claims[:8]

        # Select claims with diversity
        selected_claims = []
        used_types = set()
        used_leanings = set()

        # First, try to get diversity in claim types
        for claim in top_candidates:
            claim_type = claim.get('claim_type')
            political_lean = claim.get('political_lean', 'mixed')

            # Prioritize diversity
            if (claim_type not in used_types or len(selected_claims) < 2) and len(selected_claims) < 4:
                selected_claims.append(claim)
                used_types.add(claim_type)
                used_leanings.add(political_lean)

        # Fill remaining slots with highest quality claims
        while len(selected_claims) < 4 and len(top_candidates) > len(selected_claims):
            for claim in top_candidates:
                if claim not in selected_claims:
                    selected_claims.append(claim)
                    break

        return selected_claims[:4]

    def _generate_challenge_title(self, claims: List[Dict]) -> str:
        """Generate a title for the weekly challenge."""
        # Extract main themes from claims
        themes = []
        for claim in claims[:3]:  # Use first 3 claims for theme extraction
            claim_type = claim.get('claim_type', 'policy')
            themes.append(claim_type.value.replace('_', ' ').title())

        # Remove duplicates and limit to 2 themes
        unique_themes = list(dict.fromkeys(themes))[:2]

        if len(unique_themes) == 1:
            return f"Wely Ethical Challenge: {unique_themes[0]}"
        elif len(unique_themes) == 2:
            return f"Weekly Ethical Challenge: {unique_themes[0]} & {unique_themes[1]}"
        else:
            return "Weekly Ethical Challenge"

    def _generate_challenge_description(self, claims: List[Dict]) -> str:
        """Generate a description for the weekly challenge."""
        return f"This week's challenge explores {len(claims)} different ethical perspectives. Choose the claim that most aligns with your values and help us understand diverse viewpoints on important issues."

    def publish_pending_challenges(self) -> Dict[str, int]:
        """
        Publish all pending challenges that are ready for Friday delivery.

        Returns:
            Dict with counts of published, skipped, and failed challenges
        """
        results = {"published": 0, "skipped": 0, "failed": 0}

        try:
            # Get unpublished challenges that should be published today
            today = datetime.utcnow().date()
            friday = today + timedelta(days=(4 - today.weekday()) % 7)  # Next Friday

            pending_challenges = self.session.exec(
                select(WeeklyChallenge).where(
                    and_(
                        WeeklyChallenge.is_published == False,
                        WeeklyChallenge.challenge_date == friday
                    )
                )
            ).all()

            for challenge in pending_challenges:
                if self.publish_weekly_challenge(challenge.id):
                    results["published"] += 1
                    logger.info(f"Published weekly challenge {challenge.id}")
                else:
                    results["failed"] += 1
                    logger.error(f"Failed to publish weekly challenge {challenge.id}")

            results["skipped"] = len(pending_challenges) - results["published"] - results["failed"]

            return results

        except Exception as e:
            logger.error(f"Error publishing pending challenges: {e}")
            results["failed"] += 1
            return results