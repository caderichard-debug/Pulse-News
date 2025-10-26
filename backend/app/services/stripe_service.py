"""
Stripe service for handling payment processing and subscription management.
"""

import stripe
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlmodel import select

from app.config import settings
from app.models import (
    User, UserSubscription, SubscriptionPlan,
    DailyUsage, PromoCode, UserPromoCodeUse
)

logger = logging.getLogger(__name__)

# Initialize Stripe with API key
stripe.api_key = settings.stripe_secret_key


class StripeService:
    """Service for handling Stripe operations"""

    @staticmethod
    def create_customer(user: User, payment_method_id: Optional[str] = None) -> stripe.Customer:
        """Create a new Stripe customer for a user"""
        try:
            customer_params = {
                "email": user.email,
                "name": user.name or user.email,
                "metadata": {
                    "user_id": str(user.id),
                    "source": "pulse_app"
                }
            }

            # Add payment method if provided
            if payment_method_id:
                customer_params["payment_method"] = payment_method_id

            customer = stripe.Customer.create(**customer_params)
            logger.info(f"Created Stripe customer {customer.id} for user {user.id}")
            return customer

        except stripe.error.StripeError as e:
            logger.error(f"Error creating Stripe customer for user {user.id}: {str(e)}")
            raise

    @staticmethod
    def get_or_create_customer(user: User, payment_method_id: Optional[str] = None) -> stripe.Customer:
        """Get existing customer or create new one"""
        if user.stripe_customer_id:
            try:
                customer = stripe.Customer.retrieve(user.stripe_customer_id)
                return customer
            except stripe.error.InvalidRequestError:
                logger.warning(f"Customer {user.stripe_customer_id} not found, creating new one")

        # Create new customer
        customer = StripeService.create_customer(user, payment_method_id)

        # Update user with Stripe customer ID
        user.stripe_customer_id = customer.id
        # Note: This should be saved in the calling function

        return customer

    @staticmethod
    def create_subscription(
        customer_id: str,
        price_id: str,
        trial_period_days: Optional[int] = None,
        coupon_id: Optional[str] = None
    ) -> stripe.Subscription:
        """Create a new subscription"""
        try:
            subscription_params = {
                "customer": customer_id,
                "items": [{"price": price_id}],
                "payment_behavior": "default_incomplete",
                "payment_settings": {
                    "save_default_payment_method": "on_subscription",
                    "payment_method_types": ["card"],
                },
                "expand": ["latest_invoice.payment_intent"],
            }

            # Add trial period if specified
            if trial_period_days:
                subscription_params["trial_period_days"] = trial_period_days

            # Add coupon if specified
            if coupon_id:
                subscription_params["coupon"] = coupon_id

            subscription = stripe.Subscription.create(**subscription_params)
            logger.info(f"Created Stripe subscription {subscription.id} for customer {customer_id}")
            return subscription

        except stripe.error.StripeError as e:
            logger.error(f"Error creating subscription for customer {customer_id}: {str(e)}")
            raise

    @staticmethod
    def cancel_subscription(subscription_id: str, at_period_end: bool = True) -> stripe.Subscription:
        """Cancel a subscription"""
        try:
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=at_period_end
            )
            logger.info(f"Cancelled subscription {subscription_id}")
            return subscription

        except stripe.error.StripeError as e:
            logger.error(f"Error cancelling subscription {subscription_id}: {str(e)}")
            raise

    @staticmethod
    def reactivate_subscription(subscription_id: str) -> stripe.Subscription:
        """Reactivate a cancelled subscription"""
        try:
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=False
            )
            logger.info(f"Reactivated subscription {subscription_id}")
            return subscription

        except stripe.error.StripeError as e:
            logger.error(f"Error reactivating subscription {subscription_id}: {str(e)}")
            raise

    @staticmethod
    def update_subscription_payment_method(
        subscription_id: str,
        payment_method_id: str
    ) -> stripe.Subscription:
        """Update the payment method for a subscription"""
        try:
            subscription = stripe.Subscription.modify(
                subscription_id,
                default_payment_method=payment_method_id
            )
            logger.info(f"Updated payment method for subscription {subscription_id}")
            return subscription

        except stripe.error.StripeError as e:
            logger.error(f"Error updating payment method for subscription {subscription_id}: {str(e)}")
            raise

    @staticmethod
    def retrieve_subscription(subscription_id: str) -> stripe.Subscription:
        """Retrieve subscription details from Stripe"""
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            return subscription

        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving subscription {subscription_id}: {str(e)}")
            raise

    @staticmethod
    def retrieve_customer(customer_id: str) -> stripe.Customer:
        """Retrieve customer details from Stripe"""
        try:
            customer = stripe.Customer.retrieve(customer_id)
            return customer

        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving customer {customer_id}: {str(e)}")
            raise

    @staticmethod
    def create_payment_intent(
        amount: int,
        currency: str = "usd",
        customer_id: Optional[str] = None,
        payment_method_id: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> stripe.PaymentIntent:
        """Create a payment intent for one-time payments"""
        try:
            intent_params = {
                "amount": amount,  # Amount in cents
                "currency": currency,
                "automatic_payment_methods": {"enabled": True},
            }

            if customer_id:
                intent_params["customer"] = customer_id

            if payment_method_id:
                intent_params["payment_method"] = payment_method_id

            if metadata:
                intent_params["metadata"] = metadata

            intent = stripe.PaymentIntent.create(**intent_params)
            logger.info(f"Created payment intent {intent.id} for amount {amount} cents")
            return intent

        except stripe.error.StripeError as e:
            logger.error(f"Error creating payment intent: {str(e)}")
            raise

    @staticmethod
    def create_checkout_session(
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        trial_period_days: Optional[int] = None,
        coupon_id: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> stripe.checkout.Session:
        """Create a Stripe Checkout session"""
        try:
            session_params = {
                "customer": customer_id,
                "payment_method_types": ["card"],
                "mode": "subscription",
                "line_items": [{"price": price_id, "quantity": 1}],
                "success_url": success_url,
                "cancel_url": cancel_url,
                "allow_promotion_codes": True,
            }

            if trial_period_days:
                session_params["subscription_data"] = {
                    "trial_period_days": trial_period_days
                }

            if coupon_id:
                if "subscription_data" not in session_params:
                    session_params["subscription_data"] = {}
                session_params["subscription_data"]["coupon"] = coupon_id

            if metadata:
                session_params["metadata"] = metadata

            session = stripe.checkout.Session.create(**session_params)
            logger.info(f"Created checkout session {session.id} for customer {customer_id}")
            return session

        except stripe.error.StripeError as e:
            logger.error(f"Error creating checkout session: {str(e)}")
            raise

    @staticmethod
    def create_customer_portal_session(
        customer_id: str,
        return_url: str
    ) -> stripe.billing_portal.Session:
        """Create a Stripe Customer Portal session"""
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url,
            )
            logger.info(f"Created customer portal session {session.id} for customer {customer_id}")
            return session

        except stripe.error.StripeError as e:
            logger.error(f"Error creating customer portal session: {str(e)}")
            raise

    @staticmethod
    def construct_webhook_event(
        payload: bytes,
        sig_header: str,
        webhook_secret: str
    ) -> stripe.Event:
        """Construct and verify a webhook event"""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
            return event

        except ValueError as e:
            logger.error(f"Invalid payload in webhook: {str(e)}")
            raise
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature in webhook: {str(e)}")
            raise

    @staticmethod
    def list_payment_methods(customer_id: str) -> List[stripe.PaymentMethod]:
        """List payment methods for a customer"""
        try:
            payment_methods = stripe.PaymentMethod.list(
                customer=customer_id,
                type="card",
            )
            return payment_methods.data

        except stripe.error.StripeError as e:
            logger.error(f"Error listing payment methods for customer {customer_id}: {str(e)}")
            raise

    @staticmethod
    def detach_payment_method(payment_method_id: str) -> stripe.PaymentMethod:
        """Detach a payment method from a customer"""
        try:
            payment_method = stripe.PaymentMethod.detach(payment_method_id)
            logger.info(f"Detached payment method {payment_method_id}")
            return payment_method

        except stripe.error.StripeError as e:
            logger.error(f"Error detaching payment method {payment_method_id}: {str(e)}")
            raise

    @staticmethod
    def create_coupon(
        discount_type: str,
        discount_value: int,
        duration: str = "once",
        duration_in_months: Optional[int] = None,
        max_redemptions: Optional[int] = None,
        redeem_by: Optional[datetime] = None
    ) -> stripe.Coupon:
        """Create a Stripe coupon"""
        try:
            coupon_params = {
                "duration": duration,
            }

            if discount_type == "percentage":
                coupon_params["percent_off"] = discount_value
            else:  # fixed_amount
                coupon_params["amount_off"] = discount_value

            if duration_in_months:
                coupon_params["duration_in_months"] = duration_in_months

            if max_redemptions:
                coupon_params["max_redemptions"] = max_redemptions

            if redeem_by:
                coupon_params["redeem_by"] = int(redeem_by.timestamp())

            coupon = stripe.Coupon.create(**coupon_params)
            logger.info(f"Created Stripe coupon {coupon.id}")
            return coupon

        except stripe.error.StripeError as e:
            logger.error(f"Error creating coupon: {str(e)}")
            raise

    @staticmethod
    def get_invoice(invoice_id: str) -> stripe.Invoice:
        """Retrieve an invoice"""
        try:
            invoice = stripe.Invoice.retrieve(invoice_id)
            return invoice

        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving invoice {invoice_id}: {str(e)}")
            raise

    @staticmethod
    def list_invoices(
        customer_id: str,
        limit: int = 10,
        starting_after: Optional[str] = None
    ) -> List[stripe.Invoice]:
        """List invoices for a customer"""
        try:
            invoice_params = {
                "customer": customer_id,
                "limit": limit,
            }

            if starting_after:
                invoice_params["starting_after"] = starting_after

            invoices = stripe.Invoice.list(**invoice_params)
            return invoices.data

        except stripe.error.StripeError as e:
            logger.error(f"Error listing invoices for customer {customer_id}: {str(e)}")
            raise


# Helper functions for common operations
def is_stripe_configured() -> bool:
    """Check if Stripe is properly configured"""
    return bool(
        settings.stripe_secret_key and
        settings.stripe_publishable_key and
        settings.stripe_secret_key.startswith("sk_")
    )


def get_subscription_status(subscription: stripe.Subscription) -> str:
    """Get simplified subscription status"""
    if subscription.status == "trialing":
        return "trialing"
    elif subscription.status == "active":
        if subscription.cancel_at_period_end:
            return "canceled"
        return "active"
    elif subscription.status == "past_due":
        return "past_due"
    elif subscription.status == "canceled":
        return "canceled"
    elif subscription.status == "incomplete":
        return "incomplete"
    else:
        return "unknown"


def get_trial_end_date(subscription: stripe.Subscription) -> Optional[datetime]:
    """Get trial end date from subscription"""
    if subscription.trial_end:
        return datetime.fromtimestamp(subscription.trial_end)
    return None


def get_period_end_date(subscription: stripe.Subscription) -> datetime:
    """Get period end date from subscription"""
    return datetime.fromtimestamp(subscription.current_period_end)