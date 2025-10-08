"""
User preferences routes: manage topic subscriptions and notification settings.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from ..database import get_session
from ..models import User, UserTopicPreference, Topic, Source, UserSourceSubscription, Article, ArticleAnalysis, PoliticalLean
from ..routes.auth import get_current_user
from pydantic import BaseModel, Field
from typing import List, Optional
import logging

router = APIRouter(prefix="/preferences", tags=["preferences"])
logger = logging.getLogger(__name__)


# Request/Response Models
class TopicPreference(BaseModel):
    topic_id: int
    priority: int = Field(default=5, ge=1, le=10, description="Priority 1-10 (10 is highest)")
    is_active: bool = Field(default=True)


class UpdatePreferencesRequest(BaseModel):
    preferences: List[TopicPreference]


class TopicInfo(BaseModel):
    id: int
    name: str
    description: Optional[str]
    priority: int
    is_active: bool


class PreferencesResponse(BaseModel):
    user_id: int
    topics: List[TopicInfo]


@router.get("", response_model=PreferencesResponse)
def get_user_preferences(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Get current user's topic preferences.

    Returns all topics with user's priority settings.
    """
    # Get user's preferences
    user_prefs = session.exec(
        select(UserTopicPreference)
        .where(UserTopicPreference.user_id == current_user.id)
    ).all()

    # Create a map of topic_id -> preference
    prefs_map = {pref.topic_id: pref for pref in user_prefs}

    # Get all available topics
    all_topics = session.exec(select(Topic)).all()

    topics = []
    for topic in all_topics:
        pref = prefs_map.get(topic.id)
        topics.append({
            "id": topic.id,
            "name": topic.name,
            "description": topic.description,
            "priority": pref.priority_level if pref else 5,
            "is_active": pref.include_in_newsletter if pref else False
        })

    return {
        "user_id": current_user.id,
        "topics": topics
    }


@router.put("", response_model=PreferencesResponse)
def update_user_preferences(
    request: UpdatePreferencesRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Update user's topic preferences.

    - **preferences**: List of topic preferences with priority and active status
    - Priority: 1-10 (10 is highest priority)
    - Active: Whether to include this topic in newsletters
    """
    # Delete existing preferences
    existing_prefs = session.exec(
        select(UserTopicPreference)
        .where(UserTopicPreference.user_id == current_user.id)
    ).all()

    for pref in existing_prefs:
        session.delete(pref)

    # Create new preferences
    for pref_data in request.preferences:
        # Verify topic exists
        topic = session.get(Topic, pref_data.topic_id)
        if not topic:
            logger.warning(f"Topic {pref_data.topic_id} not found, skipping")
            continue

        new_pref = UserTopicPreference(
            user_id=current_user.id,
            topic_id=pref_data.topic_id,
            priority_level=pref_data.priority,
            include_in_newsletter=pref_data.is_active
        )
        session.add(new_pref)

    session.commit()

    logger.info(f"Updated preferences for user {current_user.email}")

    # Return updated preferences
    return get_user_preferences(current_user, session)


@router.get("/topics", response_model=List[dict])
def get_available_topics(
    session: Session = Depends(get_session)
):
    """
    Get all available topics for subscription.

    Public endpoint - doesn't require authentication.
    """
    topics = session.exec(select(Topic)).all()

    return [
        {
            "id": topic.id,
            "name": topic.name,
            "description": topic.description
        }
        for topic in topics
    ]


@router.post("/topics/{topic_id}/subscribe")
def subscribe_to_topic(
    topic_id: int,
    priority: int = Query(default=5, ge=1, le=10),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Subscribe to a specific topic.

    - **topic_id**: ID of the topic to subscribe to
    - **priority**: Priority level 1-10 (default: 5)
    """
    # Verify topic exists
    topic = session.get(Topic, topic_id)
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic {topic_id} not found"
        )

    # Check if already subscribed
    existing_pref = session.exec(
        select(UserTopicPreference)
        .where(UserTopicPreference.user_id == current_user.id)
        .where(UserTopicPreference.topic_id == topic_id)
    ).first()

    if existing_pref:
        # Update existing preference
        existing_pref.include_in_newsletter = True
        existing_pref.priority_level = priority
        session.add(existing_pref)
    else:
        # Create new preference
        new_pref = UserTopicPreference(
            user_id=current_user.id,
            topic_id=topic_id,
            priority_level=priority,  # Fixed: was priority
            include_in_newsletter=True
        )
        session.add(new_pref)

    session.commit()

    logger.info(f"User {current_user.email} subscribed to topic {topic.name}")

    return {
        "message": f"Subscribed to {topic.name}",
        "topic_id": topic_id,
        "priority": priority
    }


@router.post("/topics/{topic_id}/unsubscribe")
def unsubscribe_from_topic(
    topic_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Unsubscribe from a specific topic.

    - **topic_id**: ID of the topic to unsubscribe from
    """
    # Find preference
    preference = session.exec(
        select(UserTopicPreference)
        .where(UserTopicPreference.user_id == current_user.id)
        .where(UserTopicPreference.topic_id == topic_id)
    ).first()

    if not preference:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Not subscribed to topic {topic_id}"
        )

    # Mark as inactive (don't delete, keep history)
    preference.include_in_newsletter = False
    session.add(preference)
    session.commit()

    topic = session.get(Topic, topic_id)
    logger.info(f"User {current_user.email} unsubscribed from topic {topic.name if topic else topic_id}")

    return {
        "message": f"Unsubscribed from topic",
        "topic_id": topic_id
    }


from typing import Optional


@router.get("/newsletter-preview")
def get_newsletter_preview(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Preview what articles would be in today's newsletter based on current preferences.

    Useful for testing preferences before committing.
    """
    from ..services.newsletter_service import _generate_newsletter_for_user

    try:
        newsletter_data = _generate_newsletter_for_user(current_user, session)

        if not newsletter_data:
            return {
                "message": "No articles available for your preferences",
                "article_count": 0
            }

        return {
            "message": "Preview generated",
            "article_count": len(newsletter_data.get("article_ids", [])),
            "html_preview": newsletter_data["html"][:500] + "..."  # First 500 chars
        }

    except Exception as e:
        logger.error(f"Error generating preview: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate preview"
        )


# Source Preference Models
class SourcePreferenceInfo(BaseModel):
    source_id: int
    name: str
    url: str
    trust_score: float
    political_lean: Optional[str]
    subscribed: bool


class UpdateSourcePreferencesRequest(BaseModel):
    source_ids: List[int] = Field(description="List of source IDs to subscribe to")


class UpdateUserSettingsRequest(BaseModel):
    source_discovery_mode: Optional[str] = Field(None, description="'none', 'some', or 'open'")
    article_order_preference: Optional[str] = Field(None, description="'good_first', 'good_last', or 'mixed'")
    articles_per_topic_default: Optional[int] = Field(None, ge=1, le=10)


@router.get("/sources", response_model=List[SourcePreferenceInfo])
def get_source_preferences(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Get all sources with user's subscription status and aggregated political lean.

    Returns:
    - source_id, name, url, trust_score
    - political_lean: aggregated from article_analysis
    - subscribed: whether user is subscribed
    """
    # Get user's subscriptions
    user_subs = session.exec(
        select(UserSourceSubscription)
        .where(UserSourceSubscription.user_id == current_user.id)
    ).all()

    subs_map = {sub.source_id: sub.subscribed for sub in user_subs}

    # Get all sources
    sources = session.exec(select(Source)).all()

    result = []
    for source in sources:
        # Calculate aggregated political lean (most common lean from articles)
        from sqlalchemy import func
        lean_query = session.exec(
            select(ArticleAnalysis.political_lean, func.count())
            .join(Article)
            .where(Article.source_id == source.id)
            .group_by(ArticleAnalysis.political_lean)
            .order_by(func.count().desc())
        )

        most_common_lean = None
        for lean, count in lean_query:
            most_common_lean = lean.value if lean else None
            break

        result.append(SourcePreferenceInfo(
            source_id=source.id,
            name=source.name,
            url=source.url,
            trust_score=source.trust_score,
            political_lean=most_common_lean,
            subscribed=subs_map.get(source.id, False)
        ))

    return result


@router.put("/sources")
def update_source_preferences(
    request: UpdateSourcePreferencesRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Update user's source subscriptions.

    Replaces all existing subscriptions with the provided list.
    """
    # Delete existing subscriptions
    existing_subs = session.exec(
        select(UserSourceSubscription)
        .where(UserSourceSubscription.user_id == current_user.id)
    ).all()

    for sub in existing_subs:
        session.delete(sub)

    # Create new subscriptions
    subscribed_count = 0
    for source_id in request.source_ids:
        # Verify source exists
        source = session.get(Source, source_id)
        if not source:
            logger.warning(f"Source {source_id} not found, skipping")
            continue

        new_sub = UserSourceSubscription(
            user_id=current_user.id,
            source_id=source_id,
            subscribed=True
        )
        session.add(new_sub)
        subscribed_count += 1

    session.commit()
    logger.info(f"Updated source subscriptions for user {current_user.email}: {subscribed_count} sources")

    return {
        "message": "Source preferences updated successfully",
        "subscribed_count": subscribed_count
    }


@router.put("/settings")
def update_user_settings(
    request: UpdateUserSettingsRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Update user's general preferences (discovery mode, article ordering, etc.).
    """
    updated_fields = []

    if request.source_discovery_mode is not None:
        if request.source_discovery_mode not in ['none', 'some', 'open']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="source_discovery_mode must be 'none', 'some', or 'open'"
            )
        current_user.source_discovery_mode = request.source_discovery_mode
        updated_fields.append("source_discovery_mode")

    if request.article_order_preference is not None:
        if request.article_order_preference not in ['good_first', 'good_last', 'mixed']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="article_order_preference must be 'good_first', 'good_last', or 'mixed'"
            )
        current_user.article_order_preference = request.article_order_preference
        updated_fields.append("article_order_preference")

    if request.articles_per_topic_default is not None:
        current_user.articles_per_topic_default = request.articles_per_topic_default
        updated_fields.append("articles_per_topic_default")

    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    logger.info(f"Updated settings for user {current_user.email}: {updated_fields}")

    return {
        "message": "Settings updated successfully",
        "updated_fields": updated_fields,
        "settings": {
            "source_discovery_mode": current_user.source_discovery_mode,
            "article_order_preference": current_user.article_order_preference,
            "articles_per_topic_default": current_user.articles_per_topic_default
        }
    }


@router.get("/settings")
def get_user_settings(
    current_user: User = Depends(get_current_user)
):
    """
    Get user's general preference settings.
    """
    return {
        "source_discovery_mode": current_user.source_discovery_mode,
        "article_order_preference": current_user.article_order_preference,
        "articles_per_topic_default": current_user.articles_per_topic_default
    }
