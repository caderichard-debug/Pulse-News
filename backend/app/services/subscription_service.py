"""
Subscription service for managing user subscriptions, usage tracking, and feature access.
"""

import logging
from typing import Optional, Dict, List, Tuple
from datetime import datetime, date, timedelta, timezone
from sqlalchemy.orm import Session
from sqlmodel import select, and_, or_

from app.models import (
    User, UserSubscription, SubscriptionPlan,
    DailyUsage, PromoCode, UserPromoCodeUse, SubscriptionTier
)
from app.services.stripe_service import StripeService, get_subscription_status
from app.config import settings

logger = logging.getLogger(__name__)


class SubscriptionService:
    """Service for managing subscription-related operations"""

    @staticmethod
    def get_user_subscription(db: Session, user_id: int) -> Optional[UserSubscription]:
        """Get active subscription for a user"""
        statement = select(UserSubscription).where(
            and_(
                UserSubscription.user_id == user_id,
                UserSubscription.status.in_(["active", "trialing", "past_due"])
            )
        ).order_by(UserSubscription.created_at.desc())

        result = db.exec(statement).first()
        return result

    @staticmethod
    def get_subscription_plans(db: Session, active_only: bool = True) -> List[SubscriptionPlan]:
        """Get available subscription plans"""
        statement = select(SubscriptionPlan)
        if active_only:
            statement = statement.where(SubscriptionPlan.is_active == True)
        statement = statement.order_by(SubscriptionPlan.sort_order)

        return db.exec(statement).all()

    @staticmethod
    def get_subscription_plan(db: Session, plan_id: int) -> Optional[SubscriptionPlan]:
        """Get a specific subscription plan"""
        statement = select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id)
        return db.exec(statement).first()

    @staticmethod
    def get_subscription_plan_by_price_id(db: Session, stripe_price_id: str) -> Optional[SubscriptionPlan]:
        """Get subscription plan by Stripe price ID"""
        statement = select(SubscriptionPlan).where(SubscriptionPlan.stripe_price_id == stripe_price_id)
        return db.exec(statement).first()

    @staticmethod
    def create_subscription(
        db: Session,
        user: User,
        plan: SubscriptionPlan,
        stripe_subscription_id: str,
        stripe_customer_id: str,
        status: str,
        trial_start: Optional[datetime] = None,
        trial_end: Optional[datetime] = None,
        current_period_start: Optional[datetime] = None,
        current_period_end: Optional[datetime] = None
    ) -> UserSubscription:
        """Create a new user subscription record"""

        # Set default period dates if not provided
        if not current_period_start:
            current_period_start = datetime.utcnow()
        if not current_period_end:
            current_period_end = current_period_start + timedelta(days=30)

        subscription = UserSubscription(
            user_id=user.id,
            stripe_subscription_id=stripe_subscription_id,
            stripe_customer_id=stripe_customer_id,
            plan_id=plan.id,
            status=status,
            trial_start=trial_start,
            trial_end=trial_end,
            current_period_start=current_period_start,
            current_period_end=current_period_end
        )

        db.add(subscription)

        # Update user's subscription tier
        if status in ["active", "trialing"]:
            user.subscription_tier = SubscriptionTier.PREMIUM

            # Set trial dates on user if applicable
            if trial_start and trial_end:
                user.trial_start = trial_start
                user.trial_end = trial_end

        db.commit()
        db.refresh(subscription)

        logger.info(f"Created subscription {subscription.id} for user {user.id}")
        return subscription

    @staticmethod
    def update_subscription_status(
        db: Session,
        stripe_subscription_id: str,
        status: str,
        current_period_start: Optional[datetime] = None,
        current_period_end: Optional[datetime] = None,
        canceled_at: Optional[datetime] = None,
        cancel_at_period_end: bool = False
    ) -> Optional[UserSubscription]:
        """Update subscription status from webhook"""

        statement = select(UserSubscription).where(
            UserSubscription.stripe_subscription_id == stripe_subscription_id
        )
        subscription = db.exec(statement).first()

        if not subscription:
            logger.warning(f"Subscription {stripe_subscription_id} not found in database")
            return None

        old_status = subscription.status
        subscription.status = status

        if current_period_start:
            subscription.current_period_start = current_period_start
        if current_period_end:
            subscription.current_period_end = current_period_end
        if canceled_at:
            subscription.canceled_at = canceled_at
        if cancel_at_period_end:
            subscription.cancel_at_period_end = cancel_at_period_end

        # Update user's subscription tier based on status
        user = subscription.user
        if status in ["active", "trialing"]:
            user.subscription_tier = SubscriptionTier.PREMIUM
        elif status in ["canceled", "incomplete_expired"]:
            user.subscription_tier = SubscriptionTier.FREE
            user.trial_start = None
            user.trial_end = None

        db.commit()
        db.refresh(subscription)

        logger.info(f"Updated subscription {subscription.id} status from {old_status} to {status}")
        return subscription

    @staticmethod
    def cancel_subscription(
        db: Session,
        user_id: int,
        cancel_at_period_end: bool = True
    ) -> Optional[UserSubscription]:
        """Cancel user's subscription"""

        subscription = SubscriptionService.get_user_subscription(db, user_id)
        if not subscription:
            return None

        try:
            # Cancel in Stripe
            stripe_subscription = StripeService.cancel_subscription(
                subscription.stripe_subscription_id,
                cancel_at_period_end=cancel_at_period_end
            )

            # Update local record
            subscription.status = get_subscription_status(stripe_subscription)
            subscription.canceled_at = datetime.utcnow()
            subscription.cancel_at_period_end = cancel_at_period_end

            db.commit()
            db.refresh(subscription)

            logger.info(f"Cancelled subscription {subscription.id} for user {user_id}")
            return subscription

        except Exception as e:
            logger.error(f"Error cancelling subscription for user {user_id}: {str(e)}")
            raise

    @staticmethod
    def reactivate_subscription(db: Session, user_id: int) -> Optional[UserSubscription]:
        """Reactivate a cancelled subscription"""

        subscription = SubscriptionService.get_user_subscription(db, user_id)
        if not subscription or not subscription.cancel_at_period_end:
            return None

        try:
            # Reactivate in Stripe
            stripe_subscription = StripeService.reactivate_subscription(
                subscription.stripe_subscription_id
            )

            # Update local record
            subscription.status = get_subscription_status(stripe_subscription)
            subscription.canceled_at = None
            subscription.cancel_at_period_end = False

            db.commit()
            db.refresh(subscription)

            logger.info(f"Reactivated subscription {subscription.id} for user {user_id}")
            return subscription

        except Exception as e:
            logger.error(f"Error reactivating subscription for user {user_id}: {str(e)}")
            raise

    @staticmethod
    def get_or_create_daily_usage(db: Session, user_id: int, target_date: date) -> DailyUsage:
        """Get or create daily usage record for a user"""

        # Convert to datetime at midnight UTC
        target_datetime = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)

        statement = select(DailyUsage).where(
            and_(
                DailyUsage.user_id == user_id,
                DailyUsage.date == target_datetime
            )
        )

        usage = db.exec(statement).first()

        if not usage:
            # Get user's subscription tier to set appropriate limits
            user = db.get(User, user_id)

            if user.subscription_tier == SubscriptionTier.PREMIUM:
                daily_limit = 999999  # Effectively unlimited
                api_limit = 999999
            else:
                daily_limit = settings.free_daily_analysis_limit
                api_limit = settings.free_daily_api_limit

            usage = DailyUsage(
                user_id=user_id,
                date=target_datetime,
                daily_analysis_limit=daily_limit,
                daily_api_limit=api_limit
            )

            db.add(usage)
            db.commit()
            db.refresh(usage)

        return usage

    @staticmethod
    def increment_usage(db: Session, user_id: int, usage_type: str = "analysis") -> DailyUsage:
        """Increment daily usage counter"""

        today = date.today()
        usage = SubscriptionService.get_or_create_daily_usage(db, user_id, today)

        if usage_type == "analysis":
            usage.analyses_count += 1
        elif usage_type == "api":
            usage.api_calls_count += 1

        usage.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(usage)

        return usage

    @staticmethod
    def can_perform_analysis(db: Session, user_id: int) -> Tuple[bool, int]:
        """Check if user can perform analysis and return remaining count"""

        today = date.today()
        usage = SubscriptionService.get_or_create_daily_usage(db, user_id, today)

        remaining = usage.daily_analysis_limit - usage.analyses_count
        can_analyze = remaining > 0

        return can_analyze, remaining

    @staticmethod
    def can_make_api_call(db: Session, user_id: int) -> Tuple[bool, int]:
        """Check if user can make API call and return remaining count"""

        today = date.today()
        usage = SubscriptionService.get_or_create_daily_usage(db, user_id, today)

        remaining = usage.daily_api_limit - usage.api_calls_count
        can_call = remaining > 0

        return can_call, remaining

    @staticmethod
    def get_user_usage_stats(db: Session, user_id: int, days: int = 30) -> Dict:
        """Get usage statistics for a user"""

        start_date = date.today() - timedelta(days=days)
        start_datetime = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc)

        statement = select(DailyUsage).where(
            and_(
                DailyUsage.user_id == user_id,
                DailyUsage.date >= start_datetime
            )
        ).order_by(DailyUsage.date.desc())

        usage_records = db.exec(statement).all()

        total_analyses = sum(record.analyses_count for record in usage_records)
        total_api_calls = sum(record.api_calls_count for record in usage_records)

        # Get today's usage
        today_usage = SubscriptionService.get_or_create_daily_usage(db, user_id, date.today())

        return {
            "total_analyses": total_analyses,
            "total_api_calls": total_api_calls,
            "today_analyses": today_usage.analyses_count,
            "today_api_calls": today_usage.api_calls_count,
            "today_limit": today_usage.daily_analysis_limit,
            "today_remaining": max(0, today_usage.daily_analysis_limit - today_usage.analyses_count),
            "usage_history": [
                {
                    "date": record.date.isoformat(),
                    "analyses": record.analyses_count,
                    "api_calls": record.api_calls_count,
                    "limit": record.daily_analysis_limit
                }
                for record in usage_records[:7]  # Last 7 days
            ]
        }

    @staticmethod
    def validate_promo_code(db: Session, code: str, user_id: int) -> Optional[PromoCode]:
        """Validate a promo code for a user"""

        statement = select(PromoCode).where(
            and_(
                PromoCode.code == code.lower(),
                PromoCode.is_active == True
            )
        )
        promo_code = db.exec(statement).first()

        if not promo_code:
            return None

        # Check if expired
        if promo_code.expires_at and promo_code.expires_at < datetime.utcnow():
            return None

        # Check if max uses reached
        if promo_code.max_uses and promo_code.used_count >= promo_code.max_uses:
            return None

        # Check if user has already used this code
        if promo_code.max_uses_per_user:
            user_use_statement = select(UserPromoCodeUse).where(
                and_(
                    UserPromoCodeUse.user_id == user_id,
                    UserPromoCodeUse.promo_code_id == promo_code.id
                )
            )
            existing_use = db.exec(user_use_statement).first()
            if existing_use:
                return None

        return promo_code

    @staticmethod
    def apply_promo_code(
        db: Session,
        user_id: int,
        promo_code: PromoCode,
        subscription_id: Optional[int] = None
    ) -> UserPromoCodeUse:
        """Apply a promo code for a user"""

        # Record the usage
        promo_use = UserPromoCodeUse(
            user_id=user_id,
            promo_code_id=promo_code.id,
            subscription_id=subscription_id,
            discount_applied=promo_code.discount_value
        )

        db.add(promo_use)

        # Update promo code usage count
        promo_code.used_count += 1
        promo_code.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(promo_use)

        logger.info(f"Applied promo code {promo_code.code} for user {user_id}")
        return promo_use

    @staticmethod
    def get_subscription_info(db: Session, user_id: int) -> Dict:
        """Get comprehensive subscription information for a user"""

        user = db.get(User, user_id)
        subscription = SubscriptionService.get_user_subscription(db, user_id)
        usage_stats = SubscriptionService.get_user_usage_stats(db, user_id)

        # Check if user is in trial
        is_in_trial = False
        trial_days_remaining = 0

        if user.trial_end:
            trial_end = user.trial_end.replace(tzinfo=timezone.utc)
            now = datetime.utcnow().replace(tzinfo=timezone.utc)
            is_in_trial = trial_end > now
            trial_days_remaining = max(0, (trial_end - now).days)

        # Calculate subscription status
        if subscription:
            if subscription.status == "trialing":
                sub_status = "trialing"
            elif subscription.status == "active":
                if subscription.cancel_at_period_end:
                    sub_status = "active_canceled"
                else:
                    sub_status = "active"
            elif subscription.status == "past_due":
                sub_status = "past_due"
            else:
                sub_status = subscription.status
        else:
            sub_status = "none"

        return {
            "tier": user.subscription_tier.value,
            "status": sub_status,
            "is_in_trial": is_in_trial,
            "trial_days_remaining": trial_days_remaining,
            "trial_end": user.trial_end.isoformat() if user.trial_end else None,
            "subscription": {
                "id": subscription.id if subscription else None,
                "status": subscription.status if subscription else None,
                "plan_name": subscription.plan.name if subscription and subscription.plan else None,
                "current_period_end": subscription.current_period_end.isoformat() if subscription else None,
                "cancel_at_period_end": subscription.cancel_at_period_end if subscription else False,
                "canceled_at": subscription.canceled_at.isoformat() if subscription and subscription.canceled_at else None,
            } if subscription else None,
            "usage": usage_stats,
            "features": {
                "unlimited_analyses": user.subscription_tier == SubscriptionTier.PREMIUM,
                "advanced_analytics": user.subscription_tier == SubscriptionTier.PREMIUM,
                "challenge_system": user.subscription_tier == SubscriptionTier.PREMIUM,
                "api_access": user.subscription_tier == SubscriptionTier.PREMIUM,
            }
        }

    @staticmethod
    def check_feature_access(db: Session, user_id: int, feature: str) -> bool:
        """Check if user has access to a specific feature"""

        user = db.get(User, user_id)

        # Premium features require premium subscription
        premium_features = [
            "advanced_analytics",
            "unlimited_analyses",
            "challenge_system",
            "api_access"
        ]

        if feature in premium_features:
            return user.subscription_tier == SubscriptionTier.PREMIUM

        # Analysis has daily limits for free users
        if feature == "analysis":
            can_analyze, _ = SubscriptionService.can_perform_analysis(db, user_id)
            return can_analyze

        # API access has daily limits for free users
        if feature == "api_call":
            can_call, _ = SubscriptionService.can_make_api_call(db, user_id)
            return can_call

        # Default to allowing access
        return True

    @staticmethod
    def is_user_premium(db: Session, user_id: int) -> bool:
        """Check if user has premium subscription"""

        user = db.get(User, user_id)
        return user.subscription_tier == SubscriptionTier.PREMIUM

    @staticmethod
    def reset_daily_usage(db: Session) -> int:
        """Reset usage counters for all users (should be run daily)"""

        # This would typically be run as a daily job
        # For now, usage is tracked per day automatically
        # This function could be used to clean up old records or perform maintenance

        # Count records older than 90 days for cleanup
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        statement = select(DailyUsage).where(DailyUsage.date < cutoff_date)
        old_records = db.exec(statement).all()

        # Delete old records
        for record in old_records:
            db.delete(record)

        db.commit()

        logger.info(f"Cleaned up {len(old_records)} old daily usage records")
        return len(old_records)


# Utility functions
def get_feature_limits_for_tier(tier: SubscriptionTier) -> Dict:
    """Get feature limits for a subscription tier"""

    if tier == SubscriptionTier.PREMIUM:
        return {
            "daily_analyses": 999999,  # Unlimited
            "daily_api_calls": 999999,  # Unlimited
            "advanced_analytics": True,
            "challenge_system": True,
            "api_access": True,
        }
    else:  # FREE
        return {
            "daily_analyses": settings.free_daily_analysis_limit,
            "daily_api_calls": settings.free_daily_api_limit,
            "advanced_analytics": False,
            "challenge_system": False,
            "api_access": False,
        }


def get_trial_period_days() -> int:
    """Get the trial period in days"""
    return settings.trial_period_days