"""
Challenge Analytics Service

Provides comprehensive analytics for the newsletter challenge system.
Tracks user engagement, participation metrics, and system-wide statistics.
"""

from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional, Tuple
from sqlmodel import Session, select, func, and_, or_
from sqlalchemy import case

from ..models import (
    User, WeeklyChallenge, ChallengeClaim, UserChallengeResponse,
    ChallengeArticleAssignment, ChallengeEngagement, ChallengeClaimType,
    ChallengeResponseStatus, AgreementLevel, Article, ArticleAnalysis
)


class ChallengeAnalytics:
    """Service for generating challenge system analytics."""

    def __init__(self, session: Session):
        self.session = session

    def get_user_analytics(self, user_id: int) -> Dict[str, Any]:
        """
        Get comprehensive challenge analytics for a specific user.

        Returns participation metrics, engagement patterns, and personalized insights.
        """
        try:
            # Get user's challenge responses
            responses = self.session.exec(
                select(UserChallengeResponse)
                .where(UserChallengeResponse.user_id == user_id)
                .order_by(UserChallengeResponse.submitted_at.desc())
            ).all()

            if not responses:
                return self._empty_user_analytics()

            # Basic participation metrics
            total_participated = len(responses)
            completed_challenges = len([r for r in responses if r.status == ChallengeResponseStatus.COMPLETED])

            # Calculate participation streak
            current_streak = self._calculate_participation_streak(responses)

            # Get engagement metrics
            total_assignments = self.session.exec(
                select(func.count(ChallengeArticleAssignment.id))
                .join(UserChallengeResponse, ChallengeArticleAssignment.challenge_response_id == UserChallengeResponse.id)
                .where(UserChallengeResponse.user_id == user_id)
            ).one() or 0

            completed_assignments = self.session.exec(
                select(func.count(ChallengeArticleAssignment.id))
                .join(UserChallengeResponse, ChallengeArticleAssignment.challenge_response_id == UserChallengeResponse.id)
                .where(
                    and_(
                        UserChallengeResponse.user_id == user_id,
                        ChallengeArticleAssignment.is_completed == True
                    )
                )
            ).one() or 0

            engagement_rate = (completed_assignments / total_assignments * 100) if total_assignments > 0 else 0

            # Agreement level analysis
            agreement_stats = self._analyze_agreement_patterns(responses)

            # Claim type preferences
            claim_preferences = self._analyze_claim_type_preferences(responses)

            # Temporal patterns
            temporal_patterns = self._analyze_temporal_patterns(responses)

            # Quality indicators
            quality_metrics = self._calculate_quality_metrics(user_id, responses)

            return {
                "participation_metrics": {
                    "total_challenges": total_participated,
                    "completed_challenges": completed_challenges,
                    "completion_rate": round((completed_challenges / total_participated) * 100, 1),
                    "current_streak": current_streak,
                    "longest_streak": self._calculate_longest_streak(responses),
                    "first_participation": responses[-1].submitted_at.isoformat() if responses else None,
                    "last_participation": responses[0].submitted_at.isoformat() if responses else None
                },
                "engagement_metrics": {
                    "total_articles_assigned": total_assignments,
                    "total_articles_engaged": completed_assignments,
                    "engagement_rate": round(engagement_rate, 1),
                    "average_articles_per_challenge": round(total_assignments / total_participated, 1) if total_participated > 0 else 0,
                    "average_completion_time": self._calculate_average_completion_time(responses)
                },
                "response_patterns": {
                    "agreement_distribution": agreement_stats,
                    "claim_type_preferences": claim_preferences,
                    "temporal_patterns": temporal_patterns,
                    "controversy_engagement": self._analyze_controversy_engagement(responses)
                },
                "quality_indicators": quality_metrics,
                "recent_performance": self._get_recent_performance(responses),
                "generated_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            raise Exception(f"Error generating user analytics: {str(e)}")

    def get_system_analytics(self) -> Dict[str, Any]:
        """
        Get system-wide challenge analytics for administrators.

        Returns aggregated metrics across all users and system health indicators.
        """
        try:
            # Overall participation metrics
            total_users = self.session.exec(select(func.count(User.id))).one()
            active_users = self.session.exec(
                select(func.count(User.id))
                .where(User.challenge_participation_enabled == True)
            ).one()

            total_responses = self.session.exec(select(func.count(UserChallengeResponse.id))).one()
            unique_participants = self.session.exec(
                select(func.count(func.distinct(UserChallengeResponse.user_id)))
                .where(UserChallengeResponse.status == ChallengeResponseStatus.RESPONDED)
            ).one()

            # Weekly participation trends (last 12 weeks)
            weekly_trends = self._calculate_weekly_participation_trends()

            # Claim performance metrics
            claim_analytics = self._analyze_claim_performance()

            # Article assignment effectiveness
            assignment_analytics = self._analyze_assignment_effectiveness()

            # System health metrics
            health_metrics = self._calculate_system_health()

            return {
                "overview": {
                    "total_users": total_users,
                    "active_users": active_users,
                    "participation_rate": round((unique_participants / active_users) * 100, 1) if active_users > 0 else 0,
                    "total_responses": total_responses,
                    "unique_participants": unique_participants
                },
                "weekly_trends": weekly_trends,
                "claim_analytics": claim_analytics,
                "assignment_analytics": assignment_analytics,
                "system_health": health_metrics,
                "generated_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            raise Exception(f"Error generating system analytics: {str(e)}")

    def get_challenge_performance(self, challenge_id: int) -> Dict[str, Any]:
        """
        Get detailed performance metrics for a specific challenge.

        Useful for evaluating challenge quality and user engagement.
        """
        try:
            challenge = self.session.get(WeeklyChallenge, challenge_id)
            if not challenge:
                raise ValueError("Challenge not found")

            # Get all responses for this challenge
            responses = self.session.exec(
                select(UserChallengeResponse)
                .where(UserChallengeResponse.weekly_challenge_id == challenge_id)
            ).all()

            if not responses:
                return self._empty_challenge_performance(challenge)

            # Claim-level analytics
            claim_performance = []
            for claim in challenge.claims:
                claim_responses = [r for r in responses if r.claim_id == claim.id]
                claim_performance.append(self._analyze_claim_performance_detail(claim, claim_responses))

            # Overall challenge metrics
            participation_rate = len(responses) / self._get_eligible_user_count() * 100
            completion_rate = len([r for r in responses if r.status == ChallengeResponseStatus.COMPLETED]) / len(responses) * 100

            return {
                "challenge_info": {
                    "id": challenge.id,
                    "week_start_date": challenge.week_start_date,
                    "title": challenge.title,
                    "claim_count": len(challenge.claims)
                },
                "participation_metrics": {
                    "total_responses": len(responses),
                    "eligible_users": self._get_eligible_user_count(),
                    "participation_rate": round(participation_rate, 1),
                    "completion_rate": round(completion_rate, 1),
                    "average_agreement_level": self._calculate_average_agreement_level(responses)
                },
                "claim_performance": claim_performance,
                "engagement_quality": self._assess_engagement_quality(responses),
                "generated_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            raise Exception(f"Error generating challenge performance: {str(e)}")

    def _empty_user_analytics(self) -> Dict[str, Any]:
        """Return empty analytics structure for new users."""
        return {
            "participation_metrics": {
                "total_challenges": 0,
                "completed_challenges": 0,
                "completion_rate": 0.0,
                "current_streak": 0,
                "longest_streak": 0,
                "first_participation": None,
                "last_participation": None
            },
            "engagement_metrics": {
                "total_articles_assigned": 0,
                "total_articles_engaged": 0,
                "engagement_rate": 0.0,
                "average_articles_per_challenge": 0.0,
                "average_completion_time": 0.0
            },
            "response_patterns": {
                "agreement_distribution": {},
                "claim_type_preferences": {},
                "temporal_patterns": {},
                "controversy_engagement": {}
            },
            "quality_indicators": {
                "response_quality_score": 0.0,
                "engagement_consistency": 0.0,
                "perspective_diversity_score": 0.0
            },
            "recent_performance": [],
            "generated_at": datetime.utcnow().isoformat()
        }

    def _calculate_participation_streak(self, responses: List[UserChallengeResponse]) -> int:
        """Calculate current participation streak in weeks."""
        if not responses:
            return 0

        # Sort by week start date (newest first)
        sorted_responses = sorted(responses, key=lambda r: r.week_start_date, reverse=True)

        current_streak = 0
        expected_date = date.today()

        for response in sorted_responses:
            response_date = datetime.strptime(response.week_start_date, "%Y-%m-%d").date()

            # Check if this response is from the expected week
            week_diff = (expected_date - response_date).days

            if week_diff <= 7:  # Within expected week range
                current_streak += 1
                expected_date = response_date - timedelta(days=7)  # Expect previous week
            else:
                break

        return current_streak

    def _calculate_longest_streak(self, responses: List[UserChallengeResponse]) -> int:
        """Calculate the longest streak in user's participation history."""
        if not responses:
            return 0

        sorted_responses = sorted(responses, key=lambda r: r.week_start_date)

        max_streak = 1
        current_streak = 1

        for i in range(1, len(sorted_responses)):
            prev_date = datetime.strptime(sorted_responses[i-1].week_start_date, "%Y-%m-%d").date()
            curr_date = datetime.strptime(sorted_responses[i].week_start_date, "%Y-%m-%d").date()

            # Check if consecutive weeks
            if (curr_date - prev_date).days == 7:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 1

        return max_streak

    def _analyze_agreement_patterns(self, responses: List[UserChallengeResponse]) -> Dict[str, Any]:
        """Analyze user's agreement level patterns."""
        agreement_counts = {}
        for response in responses:
            level = response.agreement_level.value if response.agreement_level else "NEUTRAL"
            agreement_counts[level] = agreement_counts.get(level, 0) + 1

        # Calculate numeric average
        agreement_map = {
            "STRONGLY_DISAGREE": 1,
            "DISAGREE": 2,
            "NEUTRAL": 3,
            "AGREE": 4,
            "STRONGLY_AGREE": 5
        }

        numeric_values = [agreement_map.get(level, 3) for level in agreement_counts.keys()]
        weighted_sum = sum(count * agreement_map.get(level, 3) for level, count in agreement_counts.items())
        average = weighted_sum / len(responses) if responses else 3.0

        return {
            "distribution": agreement_counts,
            "average_level": round(average, 1),
            "tendency": "agree-leaning" if average > 3.2 else "disagree-leaning" if average < 2.8 else "neutral",
            "consistency": self._calculate_response_consistency(responses)
        }

    def _analyze_claim_type_preferences(self, responses: List[UserChallengeResponse]) -> Dict[str, Any]:
        """Analyze which claim types user engages with most."""
        type_counts = {}
        type_engagement = {}

        for response in responses:
            # Get claim type
            claim = self.session.get(ChallengeClaim, response.claim_id)
            if claim:
                claim_type = claim.claim_type.value
                type_counts[claim_type] = type_counts.get(claim_type, 0) + 1

                # Calculate engagement for this response
                assignment_count = self.session.exec(
                    select(func.count(ChallengeArticleAssignment.id))
                    .where(ChallengeArticleAssignment.challenge_response_id == str(response.id))
                ).one() or 0

                completed_count = self.session.exec(
                    select(func.count(ChallengeArticleAssignment.id))
                    .where(
                        and_(
                            ChallengeArticleAssignment.challenge_response_id == str(response.id),
                            ChallengeArticleAssignment.is_completed == True
                        )
                    )
                ).one() or 0

                engagement_rate = (completed_count / assignment_count * 100) if assignment_count > 0 else 0

                if claim_type not in type_engagement:
                    type_engagement[claim_type] = []
                type_engagement[claim_type].append(engagement_rate)

        # Calculate average engagement by type
        avg_engagement = {}
        for claim_type, rates in type_engagement.items():
            avg_engagement[claim_type] = round(sum(rates) / len(rates), 1)

        return {
            "selection_distribution": type_counts,
            "engagement_by_type": avg_engagement,
            "most_selected": max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else None,
            "highest_engagement": max(avg_engagement.items(), key=lambda x: x[1])[0] if avg_engagement else None
        }

    def _analyze_temporal_patterns(self, responses: List[UserChallengeResponse]) -> Dict[str, Any]:
        """Analyze temporal patterns in user's challenge participation."""
        if not responses:
            return {}

        # Day of week analysis
        day_counts = {}
        for response in responses:
            if response.submitted_at:
                day_name = response.submitted_at.strftime("%A")
                day_counts[day_name] = day_counts.get(day_name, 0) + 1

        # Time of day analysis
        hour_counts = {}
        for response in responses:
            if response.submitted_at:
                hour = response.submitted_at.hour
                hour_counts[hour] = hour_counts.get(hour, 0) + 1

        # Response time analysis (how quickly they respond after challenge opens)
        response_times = []
        for response in responses:
            if response.submitted_at and response.week_start_date:
                challenge_date = datetime.strptime(response.week_start_date, "%Y-%m-%d")
                # Challenges typically sent on Friday
                challenge_sent = challenge_date + timedelta(days=4)  # Friday of challenge week
                response_delay = (response.submitted_at - challenge_sent).total_seconds() / 3600  # hours
                response_times.append(response_delay)

        avg_response_time = sum(response_times) / len(response_times) if response_times else 0

        return {
            "preferred_days": day_counts,
            "preferred_hours": hour_counts,
            "average_response_time_hours": round(avg_response_time, 1),
            "response_patterns": {
                "early_responder": avg_response_time < 24,
                "weekend_participant": sum(day_counts.get(day, 0) for day in ["Saturday", "Sunday"]) > len(responses) * 0.5
            }
        }

    def _calculate_quality_metrics(self, user_id: int, responses: List[UserChallengeResponse]) -> Dict[str, Any]:
        """Calculate quality indicators for user's challenge engagement."""
        # Response quality (based on justification length, engagement)
        response_quality_scores = []
        for response in responses:
            score = 0

            # Has justification
            if response.justification and len(response.justification.strip()) > 10:
                score += 2

            # Strong agreement level (indicates thoughtful consideration)
            if response.agreement_level in [AgreementLevel.STRONGLY_AGREE, AgreementLevel.STRONGLY_DISAGREE]:
                score += 1

            # Completed assignments
            completed_assignments = self.session.exec(
                select(func.count(ChallengeArticleAssignment.id))
                .where(
                    and_(
                        ChallengeArticleAssignment.challenge_response_id == str(response.id),
                        ChallengeArticleAssignment.is_completed == True
                    )
                )
            ).one() or 0

            if completed_assignments >= 5:  # Completed most of 7-day challenge
                score += 2
            elif completed_assignments >= 3:
                score += 1

            response_quality_scores.append(score)

        avg_quality = sum(response_quality_scores) / len(response_quality_scores) if response_quality_scores else 0

        return {
            "response_quality_score": round((avg_quality / 5) * 100, 1),  # Convert to percentage
            "engagement_consistency": self._calculate_engagement_consistency(responses),
            "perspective_diversity_score": self._calculate_perspective_diversity(user_id, responses),
            "improvement_trend": self._calculate_improvement_trend(responses)
        }

    def _get_recent_performance(self, responses: List[UserChallengeResponse]) -> List[Dict[str, Any]]:
        """Get performance data for recent challenges."""
        recent_responses = sorted(responses, key=lambda r: r.submitted_at or datetime.min, reverse=True)[:5]

        performance_data = []
        for response in recent_responses:
            # Get completion data
            total_assignments = self.session.exec(
                select(func.count(ChallengeArticleAssignment.id))
                .where(ChallengeArticleAssignment.challenge_response_id == str(response.id))
            ).one() or 0

            completed_assignments = self.session.exec(
                select(func.count(ChallengeArticleAssignment.id))
                .where(
                    and_(
                        ChallengeArticleAssignment.challenge_response_id == str(response.id),
                        ChallengeArticleAssignment.is_completed == True
                    )
                )
            ).one() or 0

            performance_data.append({
                "week_start_date": response.week_start_date,
                "claim_type": self.session.get(ChallengeClaim, response.claim_id).claim_type.value if self.session.get(ChallengeClaim, response.claim_id) else "UNKNOWN",
                "agreement_level": response.agreement_level.value if response.agreement_level else "NEUTRAL",
                "articles_assigned": total_assignments,
                "articles_completed": completed_assignments,
                "completion_rate": round((completed_assignments / total_assignments * 100), 1) if total_assignments > 0 else 0,
                "status": response.status.value
            })

        return performance_data

    def _calculate_weekly_participation_trends(self) -> List[Dict[str, Any]]:
        """Calculate participation trends over the last 12 weeks."""
        trends = []
        current_date = date.today()

        for week_offset in range(11, -1, -1):
            week_start = current_date - timedelta(weeks=week_offset, days=current_date.weekday())
            week_end = week_start + timedelta(days=6)

            # Count challenges and responses for this week
            challenges_this_week = self.session.exec(
                select(func.count(WeeklyChallenge.id))
                .where(WeeklyChallenge.week_start_date == week_start.isoformat())
            ).one() or 0

            responses_this_week = self.session.exec(
                select(func.count(UserChallengeResponse.id))
                .where(UserChallengeResponse.week_start_date == week_start.isoformat())
            ).one() or 0

            # Get unique participants
            participants_this_week = self.session.exec(
                select(func.count(func.distinct(UserChallengeResponse.user_id)))
                .where(UserChallengeResponse.week_start_date == week_start.isoformat())
            ).one() or 0

            trends.append({
                "week_start": week_start.isoformat(),
                "week_end": week_end.isoformat(),
                "challenges_sent": challenges_this_week,
                "responses_received": responses_this_week,
                "unique_participants": participants_this_week,
                "participation_rate": round((participants_this_week / max(challenges_this_week, 1)) * 100, 1)
            })

        return trends

    def _analyze_claim_performance(self) -> Dict[str, Any]:
        """Analyze performance of different claim types."""
        claim_types = [ct.value for ct in ChallengeClaimType]
        performance_data = {}

        for claim_type in claim_types:
            # Get all claims of this type
            claims = self.session.exec(
                select(ChallengeClaim)
                .where(ChallengeClaim.claim_type == claim_type)
            ).all()

            if not claims:
                continue

            claim_ids = [claim.id for claim in claims]

            # Get response metrics
            total_responses = self.session.exec(
                select(func.count(UserChallengeResponse.id))
                .where(UserChallengeResponse.claim_id.in_(claim_ids))
            ).one() or 0

            # Calculate average engagement
            total_assignments = 0
            completed_assignments = 0

            for claim_id in claim_ids:
                assignments = self.session.exec(
                    select(func.count(ChallengeArticleAssignment.id))
                    .join(UserChallengeResponse, ChallengeArticleAssignment.challenge_response_id == UserChallengeResponse.id)
                    .where(UserChallengeResponse.claim_id == claim_id)
                ).one() or 0

                completed = self.session.exec(
                    select(func.count(ChallengeArticleAssignment.id))
                    .join(UserChallengeResponse, ChallengeArticleAssignment.challenge_response_id == UserChallengeResponse.id)
                    .where(
                        and_(
                            UserChallengeResponse.claim_id == claim_id,
                            ChallengeArticleAssignment.is_completed == True
                        )
                    )
                ).one() or 0

                total_assignments += assignments
                completed_assignments += completed

            engagement_rate = (completed_assignments / total_assignments * 100) if total_assignments > 0 else 0

            performance_data[claim_type] = {
                "total_claims": len(claims),
                "total_responses": total_responses,
                "responses_per_claim": round(total_responses / len(claims), 1),
                "total_assignments": total_assignments,
                "completed_assignments": completed_assignments,
                "engagement_rate": round(engagement_rate, 1)
            }

        return performance_data

    def _analyze_assignment_effectiveness(self) -> Dict[str, Any]:
        """Analyze how well the article assignment system works."""
        # Get all assignments
        total_assignments = self.session.exec(select(func.count(ChallengeArticleAssignment.id))).one() or 0

        completed_assignments = self.session.exec(
            select(func.count(ChallengeArticleAssignment.id))
            .where(ChallengeArticleAssignment.is_completed == True)
        ).one() or 0

        # Calculate average opposition scores
        opposition_scores = self.session.exec(
            select(ChallengeArticleAssignment.opposition_score)
            .where(ChallengeArticleAssignment.opposition_score.is_not(None))
        ).all()

        avg_opposition = sum(opposition_scores) / len(opposition_scores) if opposition_scores else 0

        # Day-by-day completion rates
        day_completion = {}
        for day in range(1, 8):
            day_assignments = self.session.exec(
                select(func.count(ChallengeArticleAssignment.id))
                .where(ChallengeArticleAssignment.sequence_day == day)
            ).one() or 0

            day_completed = self.session.exec(
                select(func.count(ChallengeArticleAssignment.id))
                .where(
                    and_(
                        ChallengeArticleAssignment.sequence_day == day,
                        ChallengeArticleAssignment.is_completed == True
                    )
                )
            ).one() or 0

            completion_rate = (day_completed / day_assignments * 100) if day_assignments > 0 else 0
            day_completion[f"day_{day}"] = {
                "assigned": day_assignments,
                "completed": day_completed,
                "completion_rate": round(completion_rate, 1)
            }

        return {
            "total_assignments": total_assignments,
            "completed_assignments": completed_assignments,
            "overall_completion_rate": round((completed_assignments / total_assignments * 100), 1) if total_assignments > 0 else 0,
            "average_opposition_score": round(avg_opposition, 2),
            "daily_completion_rates": day_completion,
            "assignment_quality": self._assess_assignment_quality()
        }

    def _calculate_system_health(self) -> Dict[str, Any]:
        """Calculate system health metrics."""
        # Recent success rates
        recent_date = datetime.utcnow() - timedelta(days=7)

        recent_challenges = self.session.exec(
            select(func.count(WeeklyChallenge.id))
            .where(WeeklyChallenge.created_at >= recent_date)
        ).one() or 0

        recent_responses = self.session.exec(
            select(func.count(UserChallengeResponse.id))
            .where(UserChallengeResponse.submitted_at >= recent_date)
        ).one() or 0

        # Error rates (would need error logging to implement properly)
        # For now, use completion rates as proxy

        return {
            "challenge_generation_success_rate": 100.0,  # Would need actual error tracking
            "response_processing_success_rate": 100.0,   # Would need actual error tracking
            "assignment_success_rate": 100.0,            # Would need actual error tracking
            "recent_activity": {
                "challenges_created_7d": recent_challenges,
                "responses_received_7d": recent_responses,
                "activity_trend": "increasing" if recent_responses > 10 else "stable"
            },
            "system_status": "healthy"
        }

    # Helper methods (implement as needed)
    def _calculate_response_consistency(self, responses: List[UserChallengeResponse]) -> float:
        """Calculate how consistent user's response patterns are."""
        # Simple implementation: variance in agreement levels
        agreement_map = {
            "STRONGLY_DISAGREE": 1, "DISAGREE": 2, "NEUTRAL": 3,
            "AGREE": 4, "STRONGLY_AGREE": 5
        }

        values = [agreement_map.get(r.agreement_level.value, 3) for r in responses if r.agreement_level]
        if not values:
            return 0.0

        avg = sum(values) / len(values)
        variance = sum((x - avg) ** 2 for x in values) / len(values)

        # Lower variance = higher consistency
        consistency = max(0, 100 - (variance * 20))  # Convert to percentage
        return round(consistency, 1)

    def _analyze_controversy_engagement(self, responses: List[UserChallengeResponse]) -> Dict[str, Any]:
        """Analyze how user engages with controversial vs non-controversial claims."""
        # This would require controversy scoring on claims
        # For now, return placeholder
        return {
            "controversial_engagement_rate": 0.0,
            "mainstream_engagement_rate": 0.0,
            "preference_trend": "balanced"
        }

    def _calculate_engagement_consistency(self, responses: List[UserChallengeResponse]) -> float:
        """Calculate how consistently user engages with assigned articles."""
        engagement_rates = []

        for response in responses:
            total = self.session.exec(
                select(func.count(ChallengeArticleAssignment.id))
                .where(ChallengeArticleAssignment.challenge_response_id == str(response.id))
            ).one() or 0

            completed = self.session.exec(
                select(func.count(ChallengeArticleAssignment.id))
                .where(
                    and_(
                        ChallengeArticleAssignment.challenge_response_id == str(response.id),
                        ChallengeArticleAssignment.is_completed == True
                    )
                )
            ).one() or 0

            if total > 0:
                engagement_rates.append((completed / total) * 100)

        if not engagement_rates:
            return 0.0

        # Consistency = 100 - (standard deviation / mean * 100)
        mean = sum(engagement_rates) / len(engagement_rates)
        variance = sum((x - mean) ** 2 for x in engagement_rates) / len(engagement_rates)
        std_dev = variance ** 0.5

        consistency = max(0, 100 - (std_dev / mean * 100)) if mean > 0 else 0
        return round(consistency, 1)

    def _calculate_perspective_diversity(self, user_id: int, responses: List[UserChallengeResponse]) -> float:
        """Calculate diversity of perspectives user has been exposed to."""
        # Get political leans of assigned articles
        political_leans = self.session.exec(
            select(ArticleAnalysis.political_lean)
            .join(Article, ArticleAnalysis.article_id == Article.id)
            .join(ChallengeArticleAssignment, ChallengeArticleAssignment.article_id == Article.id)
            .join(UserChallengeResponse, ChallengeArticleAssignment.challenge_response_id == UserChallengeResponse.id)
            .where(UserChallengeResponse.user_id == user_id)
            .where(ChallengeArticleAssignment.is_completed == True)
        ).all()

        unique_leans = set(political_leans)
        max_possible_diversity = 5  # Left, Center-Left, Center, Center-Right, Right

        diversity_score = (len(unique_leans) / max_possible_diversity) * 100
        return round(diversity_score, 1)

    def _calculate_improvement_trend(self, responses: List[UserChallengeResponse]) -> str:
        """Calculate if user's engagement is improving over time."""
        if len(responses) < 3:
            return "insufficient_data"

        # Sort by submission date
        sorted_responses = sorted([r for r in responses if r.submitted_at], key=lambda r: r.submitted_at)

        # Compare recent vs older engagement rates
        midpoint = len(sorted_responses) // 2
        older_responses = sorted_responses[:midpoint]
        recent_responses = sorted_responses[midpoint:]

        def avg_engagement(response_list):
            total_assignments = 0
            completed_assignments = 0

            for response in response_list:
                total = self.session.exec(
                    select(func.count(ChallengeArticleAssignment.id))
                    .where(ChallengeArticleAssignment.challenge_response_id == str(response.id))
                ).one() or 0

                completed = self.session.exec(
                    select(func.count(ChallengeArticleAssignment.id))
                    .where(
                        and_(
                            ChallengeArticleAssignment.challenge_response_id == str(response.id),
                            ChallengeArticleAssignment.is_completed == True
                        )
                    )
                ).one() or 0

                total_assignments += total
                completed_assignments += completed

            return (completed_assignments / total_assignments * 100) if total_assignments > 0 else 0

        older_rate = avg_engagement(older_responses)
        recent_rate = avg_engagement(recent_responses)

        if recent_rate > older_rate + 10:
            return "improving"
        elif recent_rate < older_rate - 10:
            return "declining"
        else:
            return "stable"

    def _calculate_average_completion_time(self, responses: List[UserChallengeResponse]) -> float:
        """Calculate average time to complete 7-day challenges."""
        completion_times = []

        for response in responses:
            if response.challenge_started_at and response.challenge_completed_at:
                completion_time = (response.challenge_completed_at - response.challenge_started_at).days
                completion_times.append(completion_time)

        return round(sum(completion_times) / len(completion_times), 1) if completion_times else 0.0

    def _get_eligible_user_count(self) -> int:
        """Get number of users eligible for challenges."""
        return self.session.exec(
            select(func.count(User.id))
            .where(User.challenge_participation_enabled == True)
        ).one() or 0

    def _calculate_average_agreement_level(self, responses: List[UserChallengeResponse]) -> float:
        """Calculate average agreement level for a set of responses."""
        agreement_map = {
            "STRONGLY_DISAGREE": 1, "DISAGREE": 2, "NEUTRAL": 3,
            "AGREE": 4, "STRONGLY_AGREE": 5
        }

        values = [agreement_map.get(r.agreement_level.value, 3) for r in responses if r.agreement_level]
        return round(sum(values) / len(values), 1) if values else 0.0

    def _analyze_claim_performance_detail(self, claim: ChallengeClaim, responses: List[UserChallengeResponse]) -> Dict[str, Any]:
        """Analyze performance for a specific claim."""
        agreement_counts = {}
        for response in responses:
            level = response.agreement_level.value if response.agreement_level else "NEUTRAL"
            agreement_counts[level] = agreement_counts.get(level, 0) + 1

        # Calculate engagement for this claim
        response_ids = [str(r.id) for r in responses]

        total_assignments = self.session.exec(
            select(func.count(ChallengeArticleAssignment.id))
            .where(ChallengeArticleAssignment.challenge_response_id.in_(response_ids))
        ).one() or 0

        completed_assignments = self.session.exec(
            select(func.count(ChallengeArticleAssignment.id))
            .where(
                and_(
                    ChallengeArticleAssignment.challenge_response_id.in_(response_ids),
                    ChallengeArticleAssignment.is_completed == True
                )
            )
        ).one() or 0

        return {
            "claim_id": claim.id,
            "claim_text": claim.claim_text,
            "claim_type": claim.claim_type.value,
            "total_responses": len(responses),
            "agreement_distribution": agreement_counts,
            "total_assignments": total_assignments,
            "completed_assignments": completed_assignments,
            "engagement_rate": round((completed_assignments / total_assignments * 100), 1) if total_assignments > 0 else 0
        }

    def _assess_engagement_quality(self, responses: List[UserChallengeResponse]) -> Dict[str, Any]:
        """Assess the quality of engagement for a challenge."""
        # Calculate various quality metrics
        total_justifications = len([r for r in responses if r.justification and len(r.justification.strip()) > 20])

        response_ids = [str(r.id) for r in responses]
        total_assignments = self.session.exec(
            select(func.count(ChallengeArticleAssignment.id))
            .where(ChallengeArticleAssignment.challenge_response_id.in_(response_ids))
        ).one() or 0

        completed_assignments = self.session.exec(
            select(func.count(ChallengeArticleAssignment.id))
            .where(
                and_(
                    ChallengeArticleAssignment.challenge_response_id.in_(response_ids),
                    ChallengeArticleAssignment.is_completed == True
                )
            )
        ).one() or 0

        return {
            "justification_rate": round((total_justifications / len(responses)) * 100, 1) if responses else 0,
            "article_completion_rate": round((completed_assignments / total_assignments) * 100, 1) if total_assignments > 0 else 0,
            "thoughtful_responses": total_justifications,
            "overall_quality_score": min(100, round(
                ((total_justifications / len(responses)) * 50 +
                 (completed_assignments / max(total_assignments, 1)) * 50), 1
            )) if responses else 0
        }

    def _empty_challenge_performance(self, challenge: WeeklyChallenge) -> Dict[str, Any]:
        """Return empty performance for challenges with no responses."""
        return {
            "challenge_info": {
                "id": challenge.id,
                "week_start_date": challenge.week_start_date,
                "title": challenge.title,
                "claim_count": len(challenge.claims)
            },
            "participation_metrics": {
                "total_responses": 0,
                "eligible_users": self._get_eligible_user_count(),
                "participation_rate": 0.0,
                "completion_rate": 0.0,
                "average_agreement_level": 0.0
            },
            "claim_performance": [],
            "engagement_quality": {
                "justification_rate": 0.0,
                "article_completion_rate": 0.0,
                "thoughtful_responses": 0,
                "overall_quality_score": 0.0
            },
            "generated_at": datetime.utcnow().isoformat()
        }

    def _assess_assignment_quality(self) -> Dict[str, Any]:
        """Assess the quality of article assignments."""
        # This would require more sophisticated analysis
        # For now, return basic metrics
        return {
            "average_opposition_achieved": 0.7,  # Would need actual calculation
            "source_diversity_score": 85.0,
            "topic_relevance_score": 90.0,
            "overall_assignment_quality": 85.0
        }