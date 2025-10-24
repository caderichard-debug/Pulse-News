"""
Challenge System Monitoring Service

Provides comprehensive monitoring and health checks for the newsletter challenge system.
Tracks performance metrics, error rates, and system health indicators.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlmodel import Session, select, func, and_, or_
import json

from ..models import (
    WeeklyChallenge, UserChallengeResponse, ChallengeArticleAssignment,
    ChallengeClaim, User, ChallengeResponseStatus
)

logger = logging.getLogger(__name__)


class ChallengeSystemMonitor:
    """Service for monitoring challenge system health and performance."""

    def __init__(self, session: Session):
        self.session = session

    def get_system_health_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive system health report.

        Returns performance metrics, error rates, and health indicators.
        """
        try:
            # Basic health metrics
            health_metrics = {
                "timestamp": datetime.utcnow().isoformat(),
                "overall_status": "healthy",
                "warnings": [],
                "errors": [],
                "performance_metrics": self.get_performance_metrics(),
                "participation_metrics": self.get_participation_health_metrics(),
                "job_health": self.get_job_health_metrics(),
                "data_quality": self.get_data_quality_metrics(),
                "error_rates": self.get_error_rate_metrics(),
                "capacity_metrics": self.get_capacity_metrics()
            }

            # Determine overall status
            if health_metrics["errors"]:
                health_metrics["overall_status"] = "critical"
            elif health_metrics["warnings"]:
                health_metrics["overall_status"] = "warning"

            return health_metrics

        except Exception as e:
            logger.error(f"Error generating health report: {str(e)}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "overall_status": "critical",
                "error": str(e),
                "monitoring_failed": True
            }

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics."""
        try:
            # API response times (would need request tracking in production)
            # For now, simulate based on database query performance

            # Database performance indicators
            recent_challenge_queries = self.session.exec(
                select(func.count(WeeklyChallenge.id))
                .where(WeeklyChallenge.created_at >= datetime.utcnow() - timedelta(hours=1))
            ).one() or 0

            recent_response_queries = self.session.exec(
                select(func.count(UserChallengeResponse.id))
                .where(UserChallengeResponse.submitted_at >= datetime.utcnow() - timedelta(hours=1))
            ).one() or 0

            # Assignment processing efficiency
            pending_assignments = self.session.exec(
                select(func.count(ChallengeArticleAssignment.id))
                .where(ChallengeArticleAssignment.is_completed == False)
                .where(ChallengeArticleAssignment.created_at <= datetime.utcnow() - timedelta(days=7))
            ).one() or 0

            total_assignments = self.session.exec(
                select(func.count(ChallengeArticleAssignment.id))
            ).one() or 0

            assignment_completion_rate = (
                ((total_assignments - pending_assignments) / total_assignments * 100)
                if total_assignments > 0 else 0
            )

            return {
                "database_performance": {
                    "recent_challenge_queries_per_hour": recent_challenge_queries,
                    "recent_response_queries_per_hour": recent_response_queries,
                    "query_efficiency": "good" if recent_challenge_queries < 100 else "heavy"
                },
                "assignment_processing": {
                    "total_assignments": total_assignments,
                    "pending_assignments": pending_assignments,
                    "completion_rate": round(assignment_completion_rate, 1),
                    "processing_health": "good" if assignment_completion_rate > 80 else "needs_attention"
                },
                "system_load": {
                    "status": "normal",  # Would integrate with actual system monitoring
                    "memory_usage": "normal",
                    "cpu_usage": "normal"
                }
            }

        except Exception as e:
            logger.error(f"Error getting performance metrics: {str(e)}")
            return {"error": str(e), "performance_unavailable": True}

    def get_participation_health_metrics(self) -> Dict[str, Any]:
        """Get participation metrics and health indicators."""
        try:
            # Recent participation trends
            last_7_days = datetime.utcnow() - timedelta(days=7)
            last_30_days = datetime.utcnow() - timedelta(days=30)

            recent_responses = self.session.exec(
                select(func.count(UserChallengeResponse.id))
                .where(UserChallengeResponse.submitted_at >= last_7_days)
            ).one() or 0

            older_responses = self.session.exec(
                select(func.count(UserChallengeResponse.id))
                .where(
                    and_(
                        UserChallengeResponse.submitted_at >= last_30_days,
                        UserChallengeResponse.submitted_at < last_7_days
                    )
                )
            ).one() or 0

            # Participation trend
            participation_trend = "stable"
            if recent_responses > older_responses * 1.2:
                participation_trend = "increasing"
            elif recent_responses < older_responses * 0.8:
                participation_trend = "decreasing"

            # Active challenges health
            total_challenges = self.session.exec(select(func.count(WeeklyChallenge.id))).one() or 0
            published_challenges = self.session.exec(
                select(func.count(WeeklyChallenge.id))
                .where(WeeklyChallenge.status == "PUBLISHED")
            ).one() or 0

            challenge_health = "good"
            if published_challenges == 0:
                challenge_health = "no_active_challenges"
            elif published_challenges < total_challenges * 0.5:
                challenge_health = "few_active"

            # Response completion rates
            total_responses = self.session.exec(select(func.count(UserChallengeResponse.id))).one() or 0
            completed_responses = self.session.exec(
                select(func.count(UserChallengeResponse.id))
                .where(UserChallengeResponse.status == ChallengeResponseStatus.COMPLETED)
            ).one() or 0

            completion_rate = (completed_responses / total_responses * 100) if total_responses > 0 else 0

            return {
                "participation_trends": {
                    "last_7_days": recent_responses,
                    "last_30_days": older_responses,
                    "trend": participation_trend,
                    "health": "good" if participation_trend != "decreasing" else "declining"
                },
                "challenge_health": {
                    "total_challenges": total_challenges,
                    "published_challenges": published_challenges,
                    "health_status": challenge_health
                },
                "completion_metrics": {
                    "total_responses": total_responses,
                    "completed_responses": completed_responses,
                    "completion_rate": round(completion_rate, 1),
                    "health": "good" if completion_rate > 70 else "low_completion"
                },
                "engagement_quality": self.get_engagement_quality_metrics()
            }

        except Exception as e:
            logger.error(f"Error getting participation metrics: {str(e)}")
            return {"error": str(e), "participation_unavailable": True}

    def get_engagement_quality_metrics(self) -> Dict[str, Any]:
        """Get quality metrics for user engagement."""
        try:
            # Justification quality (indicates thoughtful responses)
            responses_with_justification = self.session.exec(
                select(func.count(UserChallengeResponse.id))
                .where(UserChallengeResponse.justification.is_not(None))
                .where(func.length(UserChallengeResponse.justification) > 20)
            ).one() or 0

            total_responses = self.session.exec(select(func.count(UserChallengeResponse.id))).one() or 0
            justification_rate = (responses_with_justification / total_responses * 100) if total_responses > 0 else 0

            # Article engagement quality
            total_assignments = self.session.exec(select(func.count(ChallengeArticleAssignment.id))).one() or 0
            completed_assignments = self.session.exec(
                select(func.count(ChallengeArticleAssignment.id))
                .where(ChallengeArticleAssignment.is_completed == True)
            ).one() or 0

            article_engagement_rate = (completed_assignments / total_assignments * 100) if total_assignments > 0 else 0

            # Response diversity (varied agreement levels indicate engagement)
            agreement_distribution = self.session.exec(
                select(UserChallengeResponse.agreement_level, func.count(UserChallengeResponse.id))
                .group_by(UserChallengeResponse.agreement_level)
            ).all()

            diversity_score = len(agreement_distribution) * 20 if agreement_distribution else 0  # Max 100%

            return {
                "response_quality": {
                    "justification_rate": round(justification_rate, 1),
                    "quality_level": "high" if justification_rate > 60 else "medium" if justification_rate > 30 else "low"
                },
                "article_engagement": {
                    "engagement_rate": round(article_engagement_rate, 1),
                    "quality_level": "high" if article_engagement_rate > 70 else "medium" if article_engagement_rate > 40 else "low"
                },
                "diversity_metrics": {
                    "agreement_level_diversity": diversity_score,
                    "diversity_level": "high" if diversity_score > 80 else "medium" if diversity_score > 40 else "low"
                },
                "overall_quality_score": round((justification_rate + article_engagement_rate + diversity_score) / 3, 1)
            }

        except Exception as e:
            logger.error(f"Error getting engagement quality metrics: {str(e)}")
            return {"error": str(e), "engagement_quality_unavailable": True}

    def get_job_health_metrics(self) -> Dict[str, Any]:
        """Get health metrics for scheduled jobs."""
        try:
            # Check if recent challenges have been generated
            latest_challenge = self.session.exec(
                select(WeeklyChallenge)
                .order_by(WeeklyChallenge.week_start_date.desc())
            ).first()

            challenge_generation_health = "unknown"
            if latest_challenge:
                days_since_latest = (datetime.utcnow() - latest_challenge.created_at).days

                if days_since_latest <= 8:  # Within a week
                    challenge_generation_health = "healthy"
                elif days_since_latest <= 14:  # Within two weeks
                    challenge_generation_health = "warning"
                else:
                    challenge_generation_health = "critical"

            # Check assignment processing
            unprocessed_responses = self.session.exec(
                select(func.count(UserChallengeResponse.id))
                .where(
                    and_(
                        UserChallengeResponse.status == ChallengeResponseStatus.RESPONDED,
                        UserChallengeResponse.submitted_at <= datetime.utcnow() - timedelta(hours=2)
                    )
                )
            ).one() or 0

            assignment_health = "healthy"
            if unprocessed_responses > 50:
                assignment_health = "critical"
            elif unprocessed_responses > 20:
                assignment_health = "warning"

            return {
                "challenge_generation": {
                    "latest_challenge_date": latest_challenge.created_at.isoformat() if latest_challenge else None,
                    "health_status": challenge_generation_health,
                    "days_since_latest": (datetime.utcnow() - latest_challenge.created_at).days if latest_challenge else None
                },
                "assignment_processing": {
                    "unprocessed_responses": unprocessed_responses,
                    "health_status": assignment_health,
                    "processing_lag": "high" if unprocessed_responses > 20 else "normal"
                },
                "newsletter_integration": {
                    "status": "healthy",  # Would check newsletter delivery logs
                    "last_delivery": datetime.utcnow().isoformat()  # Would get actual delivery timestamp
                }
            }

        except Exception as e:
            logger.error(f"Error getting job health metrics: {str(e)}")
            return {"error": str(e), "job_health_unavailable": True}

    def get_data_quality_metrics(self) -> Dict[str, Any]:
        """Get data quality and consistency metrics."""
        try:
            # Check for orphaned records
            orphaned_assignments = self.session.exec(
                select(func.count(ChallengeArticleAssignment.id))
                .where(ChallengeArticleAssignment.challenge_response_id.notin(
                    select(UserChallengeResponse.id)
                ))
            ).one() or 0

            orphaned_responses = self.session.exec(
                select(func.count(UserChallengeResponse.id))
                .where(UserChallengeResponse.weekly_challenge_id.notin(
                    select(WeeklyChallenge.id)
                ))
            ).one() or 0

            # Check data completeness
            claims_without_controversy = self.session.exec(
                select(func.count(ChallengeClaim.id))
                .where(ChallengeClaim.controversy_score.is_(None))
            ).one() or 0

            responses_without_justification = self.session.exec(
                select(func.count(UserChallengeResponse.id))
                .where(
                    and_(
                        UserChallengeResponse.justification.is_(None),
                        UserChallengeResponse.agreement_level.in_(['STRONGLY_AGREE', 'STRONGLY_DISAGREE'])
                    )
                )
            ).one() or 0

            # Check for data consistency
            total_challenges = self.session.exec(select(func.count(WeeklyChallenge.id))).one() or 0
            challenges_with_claims = self.session.exec(
                select(func.count(func.distinct(WeeklyChallenge.id)))
                .join(ChallengeClaim, WeeklyChallenge.id == ChallengeClaim.weekly_challenge_id)
            ).one() or 0

            data_consistency_score = (challenges_with_claims / total_challenges * 100) if total_challenges > 0 else 100

            return {
                "orphaned_records": {
                    "orphaned_assignments": orphaned_assignments,
                    "orphaned_responses": orphaned_responses,
                    "health": "good" if orphaned_assignments == 0 and orphaned_responses == 0 else "needs_cleanup"
                },
                "data_completeness": {
                    "claims_without_scores": claims_without_controversy,
                    "strong_responses_without_justification": responses_without_justification,
                    "completeness_rate": round(
                        (total_challenges - claims_without_controversy) / total_challenges * 100, 1
                    ) if total_challenges > 0 else 100
                },
                "data_consistency": {
                    "total_challenges": total_challenges,
                    "challenges_with_claims": challenges_with_claims,
                    "consistency_score": round(data_consistency_score, 1),
                    "health": "good" if data_consistency_score > 95 else "needs_attention"
                },
                "overall_quality_score": round(
                    (100 - min(orphaned_assignments + orphaned_responses, 100)) * data_consistency_score / 100, 1
                )
            }

        except Exception as e:
            logger.error(f"Error getting data quality metrics: {str(e)}")
            return {"error": str(e), "data_quality_unavailable": True}

    def get_error_rate_metrics(self) -> Dict[str, Any]:
        """Get error rate metrics and patterns."""
        try:
            # This would integrate with application error logging
            # For now, simulate based on database anomalies and edge cases

            # Check for potential error indicators
            failed_assignments = self.session.exec(
                select(func.count(ChallengeArticleAssignment.id))
                .where(ChallengeArticleAssignment.article_id.notin(
                    select(func.distinct(ChallengeArticleAssignment.article_id))
                ))
            ).one() or 0

            # Check for incomplete challenge responses
            incomplete_responses = self.session.exec(
                select(func.count(UserChallengeResponse.id))
                .where(
                    and_(
                        UserChallengeResponse.claim_id.is_(None),
                        UserChallengeResponse.agreement_level.is_not(None)
                    )
                )
            ).one() or 0

            # Calculate error indicators
            total_operations = (
                self.session.exec(select(func.count(WeeklyChallenge.id))).one() or 0 +
                self.session.exec(select(func.count(UserChallengeResponse.id))).one() or 0 +
                self.session.exec(select(func.count(ChallengeArticleAssignment.id))).one() or 0
            )

            error_indicators = failed_assignments + incomplete_responses
            error_rate = (error_indicators / total_operations * 100) if total_operations > 0 else 0

            return {
                "error_indicators": {
                    "failed_assignments": failed_assignments,
                    "incomplete_responses": incomplete_responses,
                    "total_errors": error_indicators
                },
                "error_rate": {
                    "rate": round(error_rate, 2),
                    "level": "low" if error_rate < 1 else "medium" if error_rate < 5 else "high",
                    "health": "good" if error_rate < 2 else "warning" if error_rate < 5 else "critical"
                },
                "error_patterns": {
                    "assignment_failures": failed_assignments,
                    "response_issues": incomplete_responses,
                    "recommendation": self.generate_error_recommendation(error_rate, failed_assignments, incomplete_responses)
                }
            }

        except Exception as e:
            logger.error(f"Error getting error rate metrics: {str(e)}")
            return {"error": str(e), "error_metrics_unavailable": True}

    def get_capacity_metrics(self) -> Dict[str, Any]:
        """Get system capacity and scaling metrics."""
        try:
            # Current system load indicators
            active_users = self.session.exec(
                select(func.count(User.id))
                .where(User.challenge_participation_enabled == True)
            ).one() or 0

            weekly_active_users = self.session.exec(
                select(func.count(func.distinct(UserChallengeResponse.user_id)))
                .where(UserChallengeResponse.submitted_at >= datetime.utcnow() - timedelta(days=7))
            ).one() or 0

            # Resource utilization indicators
            total_challenges = self.session.exec(select(func.count(WeeklyChallenge.id))).one() or 0
            total_responses = self.session.exec(select(func.count(UserChallengeResponse.id))).one() or 0
            total_assignments = self.session.exec(select(func.count(ChallengeArticleAssignment.id))).one() or 0

            # Calculate growth trends
            last_week_responses = self.session.exec(
                select(func.count(UserChallengeResponse.id))
                .where(UserChallengeResponse.submitted_at >= datetime.utcnow() - timedelta(days=7))
            ).one() or 0

            prev_week_responses = self.session.exec(
                select(func.count(UserChallengeResponse.id))
                .where(
                    and_(
                        UserChallengeResponse.submitted_at >= datetime.utcnow() - timedelta(days=14),
                        UserChallengeResponse.submitted_at < datetime.utcnow() - timedelta(days=7)
                    )
                )
            ).one() or 0

            growth_rate = ((last_week_responses - prev_week_responses) / prev_week_responses * 100) if prev_week_responses > 0 else 0

            return {
                "user_capacity": {
                    "total_active_users": active_users,
                    "weekly_active_users": weekly_active_users,
                    "engagement_rate": round((weekly_active_users / active_users * 100), 1) if active_users > 0 else 0,
                    "capacity_utilization": "healthy" if active_users < 10000 else "high"
                },
                "data_volume": {
                    "total_challenges": total_challenges,
                    "total_responses": total_responses,
                    "total_assignments": total_assignments,
                    "growth_trend": "increasing" if growth_rate > 10 else "stable" if growth_rate > -10 else "declining",
                    "weekly_growth_rate": round(growth_rate, 1)
                },
                "scaling_indicators": {
                    "storage_growth": "moderate",  # Would check actual database size
                    "processing_load": "normal",  # Would check CPU/memory usage
                    "network_bandwidth": "normal"  # Would check API request volume
                }
            }

        except Exception as e:
            logger.error(f"Error getting capacity metrics: {str(e)}")
            return {"error": str(e), "capacity_metrics_unavailable": True}

    def generate_error_recommendation(self, error_rate: float, failed_assignments: int, incomplete_responses: int) -> str:
        """Generate recommendations based on error patterns."""
        if error_rate > 5:
            return "High error rate detected. Immediate investigation required."
        elif failed_assignments > 10:
            return "Multiple assignment failures detected. Check article matching algorithm."
        elif incomplete_responses > 10:
            return "Incomplete responses detected. Check response validation logic."
        elif error_rate > 2:
            return "Elevated error rate. Monitor system health closely."
        else:
            return "Error rates within normal parameters."

    def get_alert_conditions(self) -> List[Dict[str, Any]]:
        """Get current alert conditions requiring attention."""
        alerts = []

        try:
            health_report = self.get_system_health_report()

            # Performance alerts
            perf_metrics = health_report.get("performance_metrics", {})
            if isinstance(perf_metrics, dict):
                if perf_metrics.get("assignment_processing", {}).get("completion_rate", 100) < 70:
                    alerts.append({
                        "severity": "warning",
                        "type": "performance",
                        "message": "Low assignment completion rate detected",
                        "metric": f"Assignment completion rate: {perf_metrics.get('assignment_processing', {}).get('completion_rate', 0)}%"
                    })

            # Participation alerts
            part_metrics = health_report.get("participation_metrics", {})
            if isinstance(part_metrics, dict):
                if part_metrics.get("challenge_health", {}).get("health_status") == "no_active_challenges":
                    alerts.append({
                        "severity": "critical",
                        "type": "participation",
                        "message": "No active challenges available",
                        "metric": "Published challenges: 0"
                    })

            # Data quality alerts
            data_metrics = health_report.get("data_quality", {})
            if isinstance(data_metrics, dict):
                if data_metrics.get("overall_quality_score", 100) < 90:
                    alerts.append({
                        "severity": "warning",
                        "type": "data_quality",
                        "message": "Data quality issues detected",
                        "metric": f"Quality score: {data_metrics.get('overall_quality_score', 0)}%"
                    })

            # Error rate alerts
            error_metrics = health_report.get("error_rates", {})
            if isinstance(error_metrics, dict):
                error_rate = error_metrics.get("error_rate", {}).get("rate", 0)
                if error_rate > 3:
                    alerts.append({
                        "severity": "warning" if error_rate < 5 else "critical",
                        "type": "error_rate",
                        "message": "Elevated error rate detected",
                        "metric": f"Error rate: {error_rate}%"
                    })

            return alerts

        except Exception as e:
            logger.error(f"Error generating alerts: {str(e)}")
            return [{
                "severity": "critical",
                "type": "monitoring",
                "message": f"Monitoring system error: {str(e)}",
                "metric": "System unavailable"
            }]

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get executive-level performance summary."""
        try:
            health_report = self.get_system_health_report()

            return {
                "timestamp": health_report.get("timestamp"),
                "overall_status": health_report.get("overall_status"),
                "key_metrics": {
                    "total_active_users": health_report.get("capacity_metrics", {}).get("user_capacity", {}).get("total_active_users", 0),
                    "weekly_participants": health_report.get("participation_metrics", {}).get("participation_trends", {}).get("last_7_days", 0),
                    "engagement_rate": health_report.get("participation_metrics", {}).get("engagement_quality", {}).get("overall_quality_score", 0),
                    "system_health": health_report.get("overall_status"),
                    "active_alerts": len(self.get_alert_conditions())
                },
                "trend_indicators": {
                    "participation_trend": health_report.get("participation_metrics", {}).get("participation_trends", {}).get("trend", "unknown"),
                    "data_quality": health_report.get("data_quality", {}).get("overall_quality_score", 0),
                    "error_rate": health_report.get("error_rates", {}).get("error_rate", {}).get("rate", 0)
                },
                "recommendations": self.generate_executive_recommendations(health_report)
            }

        except Exception as e:
            logger.error(f"Error generating performance summary: {str(e)}")
            return {
                "error": str(e),
                "status": "monitoring_failed",
                "timestamp": datetime.utcnow().isoformat()
            }

    def generate_executive_recommendations(self, health_report: Dict[str, Any]) -> List[str]:
        """Generate executive-level recommendations based on health report."""
        recommendations = []

        # Performance recommendations
        perf_metrics = health_report.get("performance_metrics", {})
        if isinstance(perf_metrics, dict):
            assignment_health = perf_metrics.get("assignment_processing", {}).get("health_status")
            if assignment_health == "needs_attention":
                recommendations.append("Review article assignment algorithm for performance optimization")

        # Participation recommendations
        part_metrics = health_report.get("participation_metrics", {})
        if isinstance(part_metrics, dict):
            trend = part_metrics.get("participation_trends", {}).get("trend")
            if trend == "declining":
                recommendations.append("Investigate declining participation trends and user engagement")

            completion_rate = part_metrics.get("completion_metrics", {}).get("completion_rate", 100)
            if completion_rate < 70:
                recommendations.append("Focus on improving challenge completion rates")

        # Data quality recommendations
        data_metrics = health_report.get("data_quality", {})
        if isinstance(data_metrics, dict):
            orphaned = data_metrics.get("orphaned_records", {})
            if orphaned.get("orphaned_assignments", 0) > 0 or orphaned.get("orphaned_responses", 0) > 0:
                recommendations.append("Clean up orphaned records to improve data integrity")

        # Error rate recommendations
        error_metrics = health_report.get("error_rates", {})
        if isinstance(error_metrics, dict):
            error_rate = error_metrics.get("error_rate", {}).get("rate", 0)
            if error_rate > 2:
                recommendations.append("Address elevated error rates to improve system reliability")

        # Capacity recommendations
        capacity_metrics = health_report.get("capacity_metrics", {})
        if isinstance(capacity_metrics, dict):
            utilization = capacity_metrics.get("user_capacity", {}).get("capacity_utilization")
            if utilization == "high":
                recommendations.append("Plan for system scaling to handle increased user load")

        return recommendations if recommendations else ["System operating within normal parameters"]