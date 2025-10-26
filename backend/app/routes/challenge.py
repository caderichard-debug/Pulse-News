"""
Challenge System API Routes

Endpoints for managing weekly challenges, user responses, and challenge participation.
Handles challenge form access, response submission, and user challenge history.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, and_, or_, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from ..database import get_session
from ..models import (
    User, WeeklyChallenge, ChallengeClaim, UserChallengeResponse,
    AgreementLevel, ChallengeResponseStatus
)
from ..routes.auth import get_current_user
from ..services.challenge_manager import ChallengeManager
from ..services.challenge_article_matcher import ChallengeArticleMatcher
from ..services.challenge_analytics import ChallengeAnalytics
from ..services.subscription_service import SubscriptionService
from ..middleware.subscription_middleware import check_subscription_in_middleware

router = APIRouter(prefix="/challenge", tags=["challenge"])


# Pydantic models for request/response
class ChallengeResponse(BaseModel):
    id: int
    week_start_date: str
    title: str
    description: Optional[str]
    claims: List[Dict[str, Any]]


class ChallengeClaimResponse(BaseModel):
    id: int
    display_order: int
    claim_text: str
    claim_type: str
    background_context: Optional[str]


class UserChallengeResponseCreate(BaseModel):
    selected_claim_id: int
    agreement_level: AgreementLevel


class UserChallengeResponseDetails(BaseModel):
    id: int
    weekly_challenge_id: int
    selected_claim_id: int
    agreement_level: AgreementLevel
    status: ChallengeResponseStatus
    responded_at: Optional[datetime]
    challenge_started_at: Optional[datetime]
    challenge_completed_at: Optional[datetime]
    articles_sent_count: int
    articles_engaged_count: int
    found_valuable: Optional[bool]
    feedback_text: Optional[str]


class ChallengeHistoryResponse(BaseModel):
    current_challenge: Optional[ChallengeResponse]
    user_response: Optional[UserChallengeResponseDetails]
    can_respond: bool
    response_reason: str
    past_responses: List[UserChallengeResponseDetails]


@router.get("/current", response_model=Dict[str, Any])
def get_current_challenge(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    _: bool = Depends(check_subscription_in_middleware("challenge_system"))
):
    """
    Get the current week's challenge for the logged-in user.

    Returns challenge details, user's response status, and whether they can respond.
    """
    try:
        manager = ChallengeManager(session)

        # Get current challenge
        current_challenge = manager.get_current_challenge()
        if not current_challenge:
            return {
                "challenge": None,
                "user_response": None,
                "can_respond": False,
                "reason": "No active challenge this week"
            }

        # Check if user can respond
        can_respond, reason = manager.can_user_respond_to_challenge(
            current_user.id, current_challenge.id
        )

        # Get user's existing response (if any)
        user_response = manager.get_user_challenge_response(
            current_user.id, current_challenge.week_start_date
        )

        # Format challenge response
        challenge_data = {
            "id": current_challenge.id,
            "week_start_date": current_challenge.week_start_date.strftime('%Y-%m-%d'),
            "title": current_challenge.title,
            "description": current_challenge.description,
            "challenge_date": current_challenge.challenge_date.strftime('%Y-%m-%d'),
            "claims": []
        }

        # Get claims for this challenge
        claims = session.exec(
            select(ChallengeClaim)
            .where(ChallengeClaim.weekly_challenge_id == current_challenge.id)
            .order_by(ChallengeClaim.display_order)
        ).all()

        for claim in claims:
            challenge_data["claims"].append({
                "id": claim.id,
                "display_order": claim.display_order,
                "claim_text": claim.claim_text,
                "claim_type": claim.claim_type.value,
                "background_context": claim.background_context
            })

        # Format user response if exists
        user_response_data = None
        if user_response:
            user_response_data = {
                "id": user_response.id,
                "selected_claim_id": user_response.selected_claim_id,
                "agreement_level": user_response.agreement_level,
                "status": user_response.status,
                "responded_at": user_response.responded_at,
                "challenge_started_at": user_response.challenge_started_at,
                "challenge_completed_at": user_response.challenge_completed_at,
                "articles_sent_count": user_response.articles_sent_count,
                "articles_engaged_count": user_response.articles_engaged_count,
                "found_valuable": user_response.found_valuable,
                "feedback_text": user_response.feedback_text
            }

        return {
            "challenge": challenge_data,
            "user_response": user_response_data,
            "can_respond": can_respond,
            "reason": reason
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting current challenge: {str(e)}")


@router.get("/{week_date}", response_model=Dict[str, Any])
def get_challenge_by_date(
    week_date: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Get challenge for a specific week date.

    Used for accessing challenge forms via newsletter links.
    Format: YYYY-MM-DD (any day of the challenge week)
    """
    try:
        # Parse the date
        try:
            target_date = datetime.strptime(week_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

        manager = ChallengeManager(session)

        # Get challenge for the week
        challenge = manager.get_challenge_by_date(target_date)
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found for this week")

        # Check if challenge is published
        if not challenge.is_published:
            raise HTTPException(status_code=404, detail="Challenge not yet published")

        # Check if user can respond
        can_respond, reason = manager.can_user_respond_to_challenge(
            current_user.id, challenge.id
        )

        # Get user's existing response
        user_response = manager.get_user_challenge_response(
            current_user.id, challenge.week_start_date
        )

        # Format challenge data
        challenge_data = {
            "id": challenge.id,
            "week_start_date": challenge.week_start_date.strftime('%Y-%m-%d'),
            "title": challenge.title,
            "description": challenge.description,
            "challenge_date": challenge.challenge_date.strftime('%Y-%m-%d'),
            "week_end_date": challenge.week_end_date.strftime('%Y-%m-%d'),
            "claims": []
        }

        # Get claims
        claims = session.exec(
            select(ChallengeClaim)
            .where(ChallengeClaim.weekly_challenge_id == challenge.id)
            .order_by(ChallengeClaim.display_order)
        ).all()

        for claim in claims:
            challenge_data["claims"].append({
                "id": claim.id,
                "display_order": claim.display_order,
                "claim_text": claim.claim_text,
                "claim_type": claim.claim_type.value,
                "background_context": claim.background_context
            })

        # Format user response if exists
        user_response_data = None
        if user_response:
            user_response_data = {
                "id": user_response.id,
                "selected_claim_id": user_response.selected_claim_id,
                "agreement_level": user_response.agreement_level,
                "status": user_response.status,
                "responded_at": user_response.responded_at
            }

        return {
            "challenge": challenge_data,
            "user_response": user_response_data,
            "can_respond": can_respond,
            "reason": reason,
            "user_name": current_user.name
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting challenge: {str(e)}")


@router.post("/{week_date}/respond")
def submit_challenge_response(
    week_date: str,
    response_data: UserChallengeResponseCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    _: bool = Depends(check_subscription_in_middleware("challenge_system"))
):
    """
    Submit user's response to a weekly challenge.

    User selects one claim and indicates their agreement level.
    This triggers the 7-day challenge article sequence.
    """
    try:
        # Parse the date
        try:
            target_date = datetime.strptime(week_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

        manager = ChallengeManager(session)

        # Get challenge for the week
        challenge = manager.get_challenge_by_date(target_date)
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found for this week")

        # Check if user can respond
        can_respond, reason = manager.can_user_respond_to_challenge(
            current_user.id, challenge.id
        )

        if not can_respond:
            raise HTTPException(status_code=400, detail=reason)

        # Validate that the selected claim belongs to this challenge
        selected_claim = session.get(ChallengeClaim, response_data.selected_claim_id)
        if not selected_claim or selected_claim.weekly_challenge_id != challenge.id:
            raise HTTPException(status_code=400, detail="Invalid claim selected")

        # Check for existing response
        existing_response = manager.get_user_challenge_response(
            current_user.id, challenge.week_start_date
        )

        if existing_response:
            raise HTTPException(status_code=400, detail="You have already responded to this challenge")

        # Create user response
        user_response = UserChallengeResponse(
            user_id=current_user.id,
            weekly_challenge_id=challenge.id,
            selected_claim_id=response_data.selected_claim_id,
            agreement_level=response_data.agreement_level,
            responded_at=datetime.utcnow(),
            response_source="web_form",
            status=ChallengeResponseStatus.RESPONDED
        )

        session.add(user_response)
        session.flush()  # Get the ID

        # Update claim selection count
        selected_claim.selection_count += 1

        # Create 7-day article assignments for the user
        article_matcher = ChallengeArticleMatcher(session)
        assignments = article_matcher.create_challenge_articles_for_user(user_response)

        # Update user response with assignment count
        user_response.articles_sent_count = len(assignments)
        user_response.challenge_started_at = datetime.utcnow()

        session.commit()

        return {
            "success": True,
            "response_id": user_response.id,
            "message": f"Your response has been recorded. You will receive {len(assignments)} challenge articles over the next 7 days.",
            "selected_claim": {
                "id": selected_claim.id,
                "claim_text": selected_claim.claim_text
            },
            "agreement_level": response_data.agreement_level,
            "challenge_started": True,
            "articles_assigned": len(assignments)
        }

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error submitting response: {str(e)}")


@router.get("/my-responses", response_model=List[Dict[str, Any]])
def get_user_challenge_history(
    limit: int = Query(default=10, le=50, ge=1),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    _: bool = Depends(check_subscription_in_middleware("challenge_system"))
):
    """
    Get user's challenge response history.

    Returns past challenges the user has responded to with their selections.
    """
    try:
        # Get user's challenge responses with challenge details
        query = select(
            UserChallengeResponse, WeeklyChallenge, ChallengeClaim
        ).join(
            WeeklyChallenge,
            UserChallengeResponse.weekly_challenge_id == WeeklyChallenge.id
        ).join(
            ChallengeClaim,
            UserChallengeResponse.selected_claim_id == ChallengeClaim.id
        ).where(
            UserChallengeResponse.user_id == current_user.id
        ).order_by(
            UserChallengeResponse.responded_at.desc()
        ).limit(limit)

        results = session.exec(query).all()

        history = []
        for user_response, challenge, claim in results:
            history.append({
                "id": user_response.id,
                "week_start_date": challenge.week_start_date.strftime('%Y-%m-%d'),
                "challenge_title": challenge.title,
                "selected_claim": {
                    "id": claim.id,
                    "claim_text": claim.claim_text,
                    "claim_type": claim.claim_type.value
                },
                "agreement_level": user_response.agreement_level,
                "status": user_response.status,
                "responded_at": user_response.responded_at,
                "challenge_completed_at": user_response.challenge_completed_at,
                "articles_sent_count": user_response.articles_sent_count,
                "articles_engaged_count": user_response.articles_engaged_count,
                "found_valuable": user_response.found_valuable
            })

        return history

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting challenge history: {str(e)}")


@router.get("/statistics", response_model=Dict[str, Any])
def get_challenge_statistics(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Get user's personal challenge statistics.

    Returns participation metrics, completion rates, and engagement data.
    """
    try:
        # Get total responses
        total_participated = session.exec(
            select(func.count(UserChallengeResponse.id))
            .where(UserChallengeResponse.user_id == current_user.id)
        ).one()

        if total_participated == 0:
            return {
                "total_participated": 0,
                "average_agreement_level": 0.0,
                "claim_type_breakdown": {},
                "participation_streak": 0,
                "current_week_responded": False
            }

        # Get average agreement level (convert text to number)
        agreement_map = {
            "STRONGLY_DISAGREE": 1,
            "DISAGREE": 2,
            "NEUTRAL": 3,
            "AGREE": 4,
            "STRONGLY_AGREE": 5
        }

        avg_agreement_result = session.exec(
            select(func.avg(UserChallengeResponse.agreement_level))
            .where(UserChallengeResponse.user_id == current_user.id)
        ).first()

        average_agreement_level = 0.0
        if avg_agreement_result:
            # Convert text agreement to numeric average
            text_responses = session.exec(
                select(UserChallengeResponse.agreement_level)
                .where(UserChallengeResponse.user_id == current_user.id)
            ).all()

            numeric_values = [agreement_map.get(response, 3) for response in text_responses]
            average_agreement_level = sum(numeric_values) / len(numeric_values) if numeric_values else 0.0

        # Get claim type breakdown
        claim_type_stats = session.exec(
            select(
                ChallengeClaim.claim_type,
                func.count(UserChallengeResponse.id)
            )
            .join(ChallengeClaim, UserChallengeResponse.claim_id == ChallengeClaim.id)
            .where(UserChallengeResponse.user_id == current_user.id)
            .group_by(ChallengeClaim.claim_type)
        ).all()

        claim_type_breakdown = {
            claim_type: count for claim_type, count in claim_type_stats
        }

        # Calculate participation streak
        responses_with_dates = session.exec(
            select(UserChallengeResponse.week_start_date)
            .where(UserChallengeResponse.user_id == current_user.id)
            .order_by(UserChallengeResponse.week_start_date.desc())
            .limit(10)  # Check last 10 responses for streak
        ).all()

        participation_streak = 0
        if responses_with_dates:
            current_streak = 1
            for i in range(1, len(responses_with_dates)):
                prev_date = datetime.strptime(responses_with_dates[i-1], "%Y-%m-%d").date()
                curr_date = datetime.strptime(responses_with_dates[i], "%Y-%m-%d").date()

                # Check if dates are exactly 7 days apart (consecutive weeks)
                if (prev_date - curr_date).days == 7:
                    current_streak += 1
                else:
                    break
            participation_streak = current_streak

        # Check if user responded to current week
        current_week_start = datetime.now().date() - timedelta(days=datetime.now().weekday())
        current_week_start_str = current_week_start.strftime("%Y-%m-%d")

        current_response = session.exec(
            select(UserChallengeResponse.id)
            .where(
                and_(
                    UserChallengeResponse.user_id == current_user.id,
                    UserChallengeResponse.week_start_date == current_week_start_str
                )
            )
        ).first()

        current_week_responded = current_response is not None

        return {
            "total_participated": total_participated,
            "average_agreement_level": average_agreement_level,
            "claim_type_breakdown": claim_type_breakdown,
            "participation_streak": participation_streak,
            "current_week_responded": current_week_responded
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting challenge statistics: {str(e)}")


@router.get("/assignments", response_model=List[Dict[str, Any]])
def get_user_assignments(
    response_id: str = Query(default=None),
    limit: int = Query(default=50, le=100, ge=1),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Get user's challenge article assignments.

    Returns the articles assigned for active challenges with engagement data.
    Can filter by specific response ID.
    """
    try:
        from ..services.challenge_article_matcher import ChallengeArticleMatcher

        matcher = ChallengeArticleMatcher(session)

        if response_id:
            # Get assignments for specific response
            assignments = session.exec(
                select(ChallengeArticleAssignment)
                .where(ChallengeArticleAssignment.challenge_response_id == response_id)
                .order_by(ChallengeArticleAssignment.sequence_day)
                .limit(limit)
            ).all()
        else:
            # Get all user assignments
            assignments = session.exec(
                select(ChallengeArticleAssignment)
                .join(UserChallengeResponse, ChallengeArticleAssignment.challenge_response_id == UserChallengeResponse.id)
                .where(UserChallengeResponse.user_id == current_user.id)
                .order_by(ChallengeArticleAssignment.sequence_day.desc())
                .limit(limit)
            ).all()

        result = []
        for assignment in assignments:
            # Get article details with opposition score
            article_query = session.exec(
                select(Article, Source)
                .join(Source, Article.source_id == Source.id)
                .where(Article.id == assignment.article_id)
            ).first()

            if article_query:
                article, source = article_query

                # Get opposition score if available
                opposition_score = None
                if hasattr(assignment, 'opposition_score'):
                    opposition_score = assignment.opposition_score

                result.append({
                    "id": str(assignment.id),
                    "challenge_response_id": str(assignment.challenge_response_id),
                    "article_id": article.id,
                    "sequence_day": assignment.sequence_day,
                    "article": {
                        "id": article.id,
                        "title": article.title,
                        "url": article.url,
                        "source": {
                            "name": source.name,
                            "organizational_bias": source.organizational_bias
                        },
                        "published_at": article.published_at.isoformat(),
                        "summary": article.summary,
                        "sentiment_score": None,  # Would need to join with ArticleAnalysis
                        "political_lean": None,  # Would need to join with ArticleAnalysis
                        "opposition_score": opposition_score
                    },
                    "is_completed": assignment.is_completed,
                    "completed_at": assignment.completed_at.isoformat() if assignment.completed_at else None,
                    "engagement_score": assignment.engagement_score
                })

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting assignments: {str(e)}")


@router.get("/responses", response_model=List[Dict[str, Any]])
def get_challenge_responses(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Get user's challenge responses with detailed information.

    Returns all challenge responses with claim details and article counts.
    """
    try:
        responses = session.exec(
            select(UserChallengeResponse, ChallengeClaim)
            .join(ChallengeClaim, UserChallengeResponse.claim_id == ChallengeClaim.id)
            .where(UserChallengeResponse.user_id == current_user.id)
            .order_by(UserChallengeResponse.submitted_at.desc())
        ).all()

        result = []
        for response, claim in responses:
            # Get assignment counts
            assigned_count = session.exec(
                select(func.count(ChallengeArticleAssignment.id))
                .where(ChallengeArticleAssignment.challenge_response_id == str(response.id))
            ).one() or 0

            engaged_count = session.exec(
                select(func.count(ChallengeArticleAssignment.id))
                .where(
                    and_(
                        ChallengeArticleAssignment.challenge_response_id == str(response.id),
                        ChallengeArticleAssignment.is_completed == True
                    )
                )
            ).one() or 0

            result.append({
                "id": str(response.id),
                "week_start_date": response.week_start_date,
                "claim_id": str(response.claim_id),
                "claim_text": claim.claim_text,
                "claim_type": claim.claim_type.value,
                "agreement_level": int(response.agreement_level.value.split('_')[1]) if response.agreement_level else 3,
                "justification": response.justification,
                "submitted_at": response.submitted_at.isoformat() if response.submitted_at else None,
                "assigned_articles_count": assigned_count,
                "engaged_articles_count": engaged_count
            })

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting challenge responses: {str(e)}")


@router.put("/assignments/{assignment_id}", response_model=Dict[str, Any])
def update_assignment(
    assignment_id: str,
    update_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Update a challenge assignment (e.g., mark as completed).

    Users can update their assignment status and engagement.
    """
    try:
        # Get the assignment with user verification
        assignment = session.exec(
            select(ChallengeArticleAssignment)
            .join(UserChallengeResponse, ChallengeArticleAssignment.challenge_response_id == UserChallengeResponse.id)
            .where(
                and_(
                    ChallengeArticleAssignment.id == assignment_id,
                    UserChallengeResponse.user_id == current_user.id
                )
            )
        ).first()

        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")

        # Update assignment
        if "is_completed" in update_data:
            assignment.is_completed = update_data["is_completed"]
            if update_data["is_completed"] and not assignment.completed_at:
                assignment.completed_at = datetime.utcnow()

        session.commit()

        return {
            "success": True,
            "message": "Assignment updated successfully"
        }

    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating assignment: {str(e)}")


@router.get("/analytics", response_model=Dict[str, Any])
def get_challenge_analytics(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Get comprehensive challenge analytics for the current user.

    Returns participation metrics, engagement patterns, and personalized insights.
    """
    try:
        analytics = ChallengeAnalytics(session)
        user_analytics = analytics.get_user_analytics(current_user.id)
        return user_analytics

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting challenge analytics: {str(e)}")


@router.get("/analytics/performance/{challenge_id}", response_model=Dict[str, Any])
def get_challenge_performance_analytics(
    challenge_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Get detailed performance analytics for a specific challenge.

    Returns metrics on claim performance, participation rates, and engagement quality.
    """
    try:
        analytics = ChallengeAnalytics(session)
        performance = analytics.get_challenge_performance(challenge_id)
        return performance

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting challenge performance: {str(e)}")


@router.get("/analytics/trends", response_model=Dict[str, Any])
def get_participation_trends(
    weeks: int = Query(default=12, le=52, ge=1),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Get participation trends over time.

    Returns weekly participation data for analyzing patterns and trends.
    """
    try:
        # Get user's participation over specified weeks
        trends = []
        current_date = datetime.utcnow().date()

        for week_offset in range(weeks - 1, -1, -1):
            week_start = current_date - timedelta(weeks=week_offset, days=current_date.weekday())
            week_start_str = week_start.strftime("%Y-%m-%d")

            # Check if user responded to challenge that week
            response = session.exec(
                select(UserChallengeResponse)
                .where(
                    and_(
                        UserChallengeResponse.user_id == current_user.id,
                        UserChallengeResponse.week_start_date == week_start_str
                    )
                )
            ).first()

            # Get assignment data for that week
            assignments_data = {"assigned": 0, "completed": 0}
            if response:
                assigned_count = session.exec(
                    select(func.count(ChallengeArticleAssignment.id))
                    .where(ChallengeArticleAssignment.challenge_response_id == str(response.id))
                ).one() or 0

                completed_count = session.exec(
                    select(func.count(ChallengeArticleAssignment.id))
                    .where(
                        and_(
                            ChallengeArticleAssignment.challenge_response_id == str(response.id),
                            ChallengeArticleAssignment.is_completed == True
                        )
                    )
                ).one() or 0

                assignments_data = {"assigned": assigned_count, "completed": completed_count}

            trends.append({
                "week_start": week_start_str,
                "participated": response is not None,
                "claim_type": session.get(ChallengeClaim, response.claim_id).claim_type.value if response else None,
                "agreement_level": response.agreement_level.value if response and response.agreement_level else None,
                "assignments": assignments_data,
                "completion_rate": round((assignments_data["completed"] / assignments_data["assigned"] * 100), 1) if assignments_data["assigned"] > 0 else 0
            })

        return {
            "trends": trends,
            "summary": {
                "total_weeks": len(trends),
                "participated_weeks": len([t for t in trends if t["participated"]]),
                "participation_rate": round((len([t for t in trends if t["participated"]]) / len(trends)) * 100, 1),
                "average_completion_rate": round(sum(t["completion_rate"] for t in trends if t["participated"]) / max(len([t for t in trends if t["participated"]]), 1), 1)
            },
            "generated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting participation trends: {str(e)}")


@router.post("/feedback")
def submit_challenge_feedback(
    response_id: int,
    feedback: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Submit feedback for a completed challenge.

    Users can rate whether they found the challenge valuable and provide comments.
    """
    try:
        # Get the user's response
        user_response = session.exec(
            select(UserChallengeResponse)
            .where(
                and_(
                    UserChallengeResponse.id == response_id,
                    UserChallengeResponse.user_id == current_user.id
                )
            )
        ).first()

        if not user_response:
            raise HTTPException(status_code=404, detail="Challenge response not found")

        # Update feedback fields
        if "found_valuable" in feedback:
            user_response.found_valuable = feedback["found_valuable"]

        if "feedback_text" in feedback:
            user_response.feedback_text = feedback["feedback_text"][:1000]  # Limit length

        session.commit()

        return {
            "success": True,
            "message": "Thank you for your feedback!"
        }

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error submitting feedback: {str(e)}")