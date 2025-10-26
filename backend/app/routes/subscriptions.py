"""
Subscription management routes for handling user subscriptions, billing, and usage.
"""

import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from datetime import datetime, date

from app.database import get_db
from app.models import (
    User, UserSubscription, SubscriptionPlan,
    SubscriptionTier, PromoCode
)
from app.services.subscription_service import SubscriptionService
from app.services.stripe_service import (
    StripeService, is_stripe_configured, get_trial_end_date
)
from app.routes.auth import get_current_user
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models for request/response
class SubscriptionPlanResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: int
    currency: str
    billing_interval: str
    features: Optional[List[str]]
    trial_period_days: Optional[int]
    stripe_price_id: str

    class Config:
        from_attributes = True


class SubscriptionResponse(BaseModel):
    id: int
    status: str
    plan_name: str
    current_period_end: str
    cancel_at_period_end: bool
    canceled_at: Optional[str]
    trial_end: Optional[str]

    class Config:
        from_attributes = True


class CurrentSubscriptionResponse(BaseModel):
    tier: str
    status: str
    is_in_trial: bool
    trial_days_remaining: int
    trial_end: Optional[str]
    subscription: Optional[SubscriptionResponse]
    usage: Dict[str, Any]
    features: Dict[str, bool]


class UsageResponse(BaseModel):
    total_analyses: int
    total_api_calls: int
    today_analyses: int
    today_api_calls: int
    today_limit: int
    today_remaining: int
    usage_history: List[Dict]


class CreateSubscriptionRequest(BaseModel):
    price_id: str = Field(..., description="Stripe price ID")
    payment_method_id: Optional[str] = Field(None, description="Payment method ID")
    promo_code: Optional[str] = Field(None, description="Promotional code")


class CreateSubscriptionResponse(BaseModel):
    client_secret: str
    subscription_id: str


class CancelSubscriptionRequest(BaseModel):
    cancel_at_period_end: bool = Field(True, description="Cancel at period end")


class ReactivateSubscriptionResponse(BaseModel):
    success: bool
    message: str


class PaymentHistoryResponse(BaseModel):
    id: str
    date: str
    amount: int
    currency: str
    status: str
    invoice_url: Optional[str]


class ValidatePromoCodeRequest(BaseModel):
    code: str = Field(..., description="Promotional code")


class ValidatePromoCodeResponse(BaseModel):
    valid: bool
    discount_type: Optional[str]
    discount_value: Optional[int]
    display_name: Optional[str]
    description: Optional[str]


# Helper function to check if Stripe is configured
def check_stripe_config():
    if not is_stripe_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment system is not configured"
        )


@router.get("/plans", response_model=List[SubscriptionPlanResponse])
async def get_subscription_plans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get available subscription plans"""
    try:
        plans = SubscriptionService.get_subscription_plans(db)

        # Parse features JSON for each plan
        plan_responses = []
        for plan in plans:
            features = None
            if plan.features:
                try:
                    import json
                    features = json.loads(plan.features)
                except json.JSONDecodeError:
                    pass

            plan_responses.append(SubscriptionPlanResponse(
                id=plan.id,
                name=plan.name,
                description=plan.description,
                price=plan.price,
                currency=plan.currency,
                billing_interval=plan.billing_interval,
                features=features,
                trial_period_days=plan.trial_period_days,
                stripe_price_id=plan.stripe_price_id
            ))

        return plan_responses

    except Exception as e:
        logger.error(f"Error getting subscription plans: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve subscription plans"
        )


@router.get("/current", response_model=CurrentSubscriptionResponse)
async def get_current_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's subscription information"""
    try:
        subscription_info = SubscriptionService.get_subscription_info(db, current_user.id)

        # Format subscription response
        subscription_response = None
        if subscription_info["subscription"]:
            sub = subscription_info["subscription"]
            subscription_response = SubscriptionResponse(
                id=sub["id"],
                status=sub["status"],
                plan_name=sub["plan_name"],
                current_period_end=sub["current_period_end"],
                cancel_at_period_end=sub["cancel_at_period_end"],
                canceled_at=sub["canceled_at"],
                trial_end=subscription_info.get("trial_end")
            )

        return CurrentSubscriptionResponse(
            tier=subscription_info["tier"],
            status=subscription_info["status"],
            is_in_trial=subscription_info["is_in_trial"],
            trial_days_remaining=subscription_info["trial_days_remaining"],
            trial_end=subscription_info.get("trial_end"),
            subscription=subscription_response,
            usage=subscription_info["usage"],
            features=subscription_info["features"]
        )

    except Exception as e:
        logger.error(f"Error getting current subscription: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve subscription information"
        )


@router.post("/create", response_model=CreateSubscriptionResponse)
async def create_subscription(
    request: CreateSubscriptionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new subscription"""
    check_stripe_config()

    try:
        # Get the subscription plan
        plan = SubscriptionService.get_subscription_plan_by_price_id(db, request.price_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription plan not found"
            )

        # Validate promo code if provided
        coupon_id = None
        if request.promo_code:
            promo_code = SubscriptionService.validate_promo_code(
                db, request.promo_code, current_user.id
            )
            if not promo_code:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired promotional code"
                )
            coupon_id = promo_code.stripe_coupon_id

        # Get or create Stripe customer
        customer = StripeService.get_or_create_customer(
            current_user, request.payment_method_id
        )

        # Update user's Stripe customer ID
        current_user.stripe_customer_id = customer.id
        db.commit()

        # Determine trial period
        trial_days = plan.trial_period_days or settings.trial_period_days

        # Create Stripe subscription
        stripe_subscription = StripeService.create_subscription(
            customer_id=customer.id,
            price_id=request.price_id,
            trial_period_days=trial_days if current_user.subscription_tier == SubscriptionTier.FREE else None,
            coupon_id=coupon_id
        )

        # Create local subscription record
        subscription = SubscriptionService.create_subscription(
            db=db,
            user=current_user,
            plan=plan,
            stripe_subscription_id=stripe_subscription.id,
            stripe_customer_id=customer.id,
            status=stripe_subscription.status,
            trial_start=datetime.fromtimestamp(stripe_subscription.trial_start) if stripe_subscription.trial_start else None,
            trial_end=datetime.fromtimestamp(stripe_subscription.trial_end) if stripe_subscription.trial_end else None,
            current_period_start=datetime.fromtimestamp(stripe_subscription.current_period_start),
            current_period_end=datetime.fromtimestamp(stripe_subscription.current_period_end)
        )

        # Apply promo code if used
        if request.promo_code:
            promo_code = SubscriptionService.validate_promo_code(
                db, request.promo_code, current_user.id
            )
            if promo_code:
                SubscriptionService.apply_promo_code(
                    db, current_user.id, promo_code, subscription.id
                )

        # Return client secret for frontend confirmation
        client_secret = stripe_subscription.latest_invoice.payment_intent.client_secret

        return CreateSubscriptionResponse(
            client_secret=client_secret,
            subscription_id=stripe_subscription.id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating subscription: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create subscription"
        )


@router.post("/cancel")
async def cancel_subscription(
    request: CancelSubscriptionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel user's subscription"""
    check_stripe_config()

    try:
        subscription = SubscriptionService.cancel_subscription(
            db, current_user.id, request.cancel_at_period_end
        )

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active subscription found"
            )

        return {"success": True, "message": "Subscription cancelled successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling subscription: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel subscription"
        )


@router.post("/reactivate", response_model=ReactivateSubscriptionResponse)
async def reactivate_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reactivate a cancelled subscription"""
    check_stripe_config()

    try:
        subscription = SubscriptionService.reactivate_subscription(db, current_user.id)

        if not subscription:
            return ReactivateSubscriptionResponse(
                success=False,
                message="No cancellable subscription found"
            )

        return ReactivateSubscriptionResponse(
            success=True,
            message="Subscription reactivated successfully"
        )

    except Exception as e:
        logger.error(f"Error reactivating subscription: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reactivate subscription"
        )


@router.get("/usage", response_model=UsageResponse)
async def get_usage_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's usage statistics"""
    try:
        usage_stats = SubscriptionService.get_user_usage_stats(db, current_user.id)

        return UsageResponse(**usage_stats)

    except Exception as e:
        logger.error(f"Error getting usage stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage statistics"
        )


@router.get("/history", response_model=List[PaymentHistoryResponse])
async def get_payment_history(
    limit: int = 10,
    starting_after: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's payment history"""
    check_stripe_config()

    try:
        if not current_user.stripe_customer_id:
            return []

        invoices = StripeService.list_invoices(
            customer_id=current_user.stripe_customer_id,
            limit=limit,
            starting_after=starting_after
        )

        payment_history = []
        for invoice in invoices:
            payment_history.append(PaymentHistoryResponse(
                id=invoice.id,
                date=datetime.fromtimestamp(invoice.created).isoformat(),
                amount=invoice.total,
                currency=invoice.currency,
                status=invoice.status,
                invoice_url=invoice.hosted_invoice_url
            ))

        return payment_history

    except Exception as e:
        logger.error(f"Error getting payment history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve payment history"
        )


@router.post("/validate-promo", response_model=ValidatePromoCodeResponse)
async def validate_promo_code(
    request: ValidatePromoCodeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Validate a promotional code"""
    try:
        promo_code = SubscriptionService.validate_promo_code(
            db, request.code, current_user.id
        )

        if not promo_code:
            return ValidatePromoCodeResponse(valid=False)

        return ValidatePromoCodeResponse(
            valid=True,
            discount_type=promo_code.discount_type,
            discount_value=promo_code.discount_value,
            display_name=promo_code.display_name,
            description=promo_code.description
        )

    except Exception as e:
        logger.error(f"Error validating promo code: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate promotional code"
        )


@router.get("/billing-portal")
async def get_billing_portal_url(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get Stripe Customer Portal URL"""
    check_stripe_config()

    try:
        if not current_user.stripe_customer_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No customer account found"
            )

        # Create return URL
        return_url = f"{settings.frontend_url}/subscription/billing"

        # Create portal session
        portal_session = StripeService.create_customer_portal_session(
            customer_id=current_user.stripe_customer_id,
            return_url=return_url
        )

        return {"url": portal_session.url}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating billing portal session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create billing portal session"
        )


@router.get("/payment-methods")
async def get_payment_methods(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's payment methods"""
    check_stripe_config()

    try:
        if not current_user.stripe_customer_id:
            return []

        payment_methods = StripeService.list_payment_methods(
            customer_id=current_user.stripe_customer_id
        )

        formatted_methods = []
        for pm in payment_methods:
            if pm.type == "card":
                card = pm.card
                formatted_methods.append({
                    "id": pm.id,
                    "type": "card",
                    "brand": card.brand,
                    "last4": card.last4,
                    "exp_month": card.exp_month,
                    "exp_year": card.exp_year,
                    "is_default": pm.metadata.get("default", "false") == "true"
                })

        return formatted_methods

    except Exception as e:
        logger.error(f"Error getting payment methods: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve payment methods"
        )


@router.delete("/payment-methods/{payment_method_id}")
async def delete_payment_method(
    payment_method_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a payment method"""
    check_stripe_config()

    try:
        StripeService.detach_payment_method(payment_method_id)
        return {"success": True}

    except Exception as e:
        logger.error(f"Error deleting payment method: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete payment method"
        )


@router.post("/apply-promo")
async def apply_promo_code(
    request: ValidatePromoCodeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Apply a promotional code to current subscription"""
    try:
        subscription = SubscriptionService.get_user_subscription(db, current_user.id)
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active subscription found"
            )

        promo_code = SubscriptionService.validate_promo_code(
            db, request.code, current_user.id
        )

        if not promo_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired promotional code"
            )

        # Apply promo code
        SubscriptionService.apply_promo_code(
            db, current_user.id, promo_code, subscription.id
        )

        # Note: For existing subscriptions, you would need to update the Stripe subscription
        # This is a simplified version that just records the usage

        return {"success": True, "message": "Promotional code applied successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying promo code: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to apply promotional code"
        )