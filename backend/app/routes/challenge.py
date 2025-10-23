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
    session: Session = Depends(get_session)
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
    session: Session = Depends(get_session)
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
        session.commit()

        # TODO: Trigger article assignment for next 7 days
        # This will be implemented in Phase 5

        return {
            "success": True,
            "response_id": user_response.id,
            "message": "Your response has been recorded. You will receive challenge articles over the next 7 days.",
            "selected_claim": {
                "id": selected_claim.id,
                "claim_text": selected_claim.claim_text
            },
            "agreement_level": response_data.agreement_level,
            "challenge_started": True
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
    session: Session = Depends(get_session)
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
        total_responses = session.exec(
            select(func.count(UserChallengeResponse.id))
            .where(UserChallengeResponse.user_id == current_user.id)
        ).one()

        if total_responses == 0:
            return {
                "total_responses": 0,
                "completed_challenges": 0,
                "completion_rate": 0.0,
                "articles_received": 0,
                "articles_engaged": 0,
                "engagement_rate": 0.0,
                "favorite_agreement_levels": [],
                "most_engaged_claims": []
            }

        # Get completed challenges
        completed_challenges = session.exec(
            select(func.count(UserChallengeResponse.id))
            .where(
                and_(
                    UserChallengeResponse.user_id == current_user.id,
                    UserChallengeResponse.status == ChallengeResponseStatus.COMPLETED
                )
            )
        ).one()

        # Get total articles received and engaged
        articles_stats = session.exec(
            select(
                func.sum(UserChallengeResponse.articles_sent_count),
                func.sum(UserChallengeResponse.articles_engaged_count)
            )
            .where(UserChallengeResponse.user_id == current_user.id)
        ).first()

        total_articles_received = articles_stats[0] or 0
        total_articles_engaged = articles_stats[1] or 0

        # Get agreement level distribution
        agreement_dist = session.exec(
            select(
                UserChallengeResponse.agreement_level,
                func.count(UserChallengeResponse.id)
            )
            .where(UserChallengeResponse.user_id == current_user.id)
            .group_by(UserChallengeResponse.agreement_level)
        ).all()

        # Get most engaged claims (where user actually engaged with articles)
        engaged_claims_query = session.exec(
            select(
                ChallengeClaim.claim_text,
                ChallengeClaim.claim_type,
                func.count(UserChallengeResponse.id).label('engagement_count')
            )
            .join(UserChallengeResponse, ChallengeClaim.id == UserChallengeResponse.selected_claim_id)
            .where(
                and_(
                    UserChallengeResponse.user_id == current_user.id,
                    UserChallengeResponse.articles_engaged_count > 0
                )
            )
            .group_by(ChallengeClaim.id, ChallengeClaim.claim_text, ChallengeClaim.claim_type)
            .order_by(func.count(UserChallengeResponse.id).desc())
            .limit(5)
        ).all()

        return {
            "total_responses": total_responses,
            "completed_challenges": completed_challenges,
            "completion_rate": round((completed_challenges / total_responses) * 100, 1),
            "articles_received": total_articles_received,
            "articles_engaged": total_articles_engaged,
            "engagement_rate": round(
                (total_articles_engaged / total_articles_received * 100) if total_articles_received > 0 else 0, 1
            ),
            "agreement_distribution": [
                {"level": level.value, "count": count} for level, count in agreement_dist
            ],
            "most_engaged_claims": [
                {
                    "claim_text": claim.claim_text,
                    "claim_type": claim.claim_type.value,
                    "engagement_count": claim.engagement_count
                }
                for claim in engaged_claims_query
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting challenge statistics: {str(e)}")


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