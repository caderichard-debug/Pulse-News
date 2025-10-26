"""
Webhook handlers for processing external service events.
"""

import logging
import json
from typing import Dict, Any
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException, status, Depends
from sqlalchemy.orm import Session
from sqlmodel import select

from app.database import get_db
from app.models import User, UserSubscription, SubscriptionPlan
from app.services.stripe_service import StripeService, get_trial_end_date
from app.services.subscription_service import SubscriptionService
from app.services.email_service import EmailService
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle Stripe webhook events"""
    if not settings.stripe_webhook_secret:
        logger.error("Stripe webhook secret not configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Webhook not configured"
        )

    try:
        # Get the raw payload
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature")

        if not sig_header:
            logger.error("No Stripe signature header")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No signature provided"
            )

        # Construct and verify the event
        event = StripeService.construct_webhook_event(
            payload, sig_header, settings.stripe_webhook_secret
        )

        logger.info(f"Received Stripe webhook: {event.type}")

        # Handle different event types
        await handle_stripe_event(event, db)

        return {"status": "success"}

    except ValueError as e:
        logger.error(f"Invalid webhook payload: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payload"
        )
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )


async def handle_stripe_event(event: Dict[str, Any], db: Session):
    """Handle different types of Stripe events"""
    event_type = event["type"]
    event_data = event["data"]["object"]

    if event_type == "invoice.payment_succeeded":
        await handle_invoice_payment_succeeded(event_data, db)

    elif event_type == "invoice.payment_failed":
        await handle_invoice_payment_failed(event_data, db)

    elif event_type == "customer.subscription.created":
        await handle_subscription_created(event_data, db)

    elif event_type == "customer.subscription.updated":
        await handle_subscription_updated(event_data, db)

    elif event_type == "customer.subscription.deleted":
        await handle_subscription_deleted(event_data, db)

    elif event_type == "invoice.finalized":
        await handle_invoice_finalized(event_data, db)

    elif event_type == "payment_method.attached":
        await handle_payment_method_attached(event_data, db)

    else:
        logger.info(f"Unhandled Stripe event type: {event_type}")


async def handle_invoice_payment_succeeded(invoice: Dict[str, Any], db: Session):
    """Handle successful invoice payment"""
    try:
        subscription_id = invoice.get("subscription")
        customer_id = invoice.get("customer")

        if not subscription_id:
            return

        logger.info(f"Payment succeeded for subscription {subscription_id}")

        # Update subscription status in our database
        subscription = SubscriptionService.update_subscription_status(
            db=db,
            stripe_subscription_id=subscription_id,
            status="active",
            current_period_start=datetime.fromtimestamp(invoice["period_start"]),
            current_period_end=datetime.fromtimestamp(invoice["period_end"])
        )

        if subscription:
            # Send confirmation email
            user = subscription.user
            try:
                await send_payment_success_email(user, invoice)
            except Exception as e:
                logger.error(f"Failed to send payment success email: {str(e)}")

    except Exception as e:
        logger.error(f"Error handling invoice payment succeeded: {str(e)}")


async def handle_invoice_payment_failed(invoice: Dict[str, Any], db: Session):
    """Handle failed invoice payment"""
    try:
        subscription_id = invoice.get("subscription")

        if not subscription_id:
            return

        logger.warning(f"Payment failed for subscription {subscription_id}")

        # Update subscription status
        subscription = SubscriptionService.update_subscription_status(
            db=db,
            stripe_subscription_id=subscription_id,
            status="past_due"
        )

        if subscription:
            # Send payment failure notification
            user = subscription.user
            try:
                await send_payment_failed_email(user, invoice)
            except Exception as e:
                logger.error(f"Failed to send payment failed email: {str(e)}")

    except Exception as e:
        logger.error(f"Error handling invoice payment failed: {str(e)}")


async def handle_subscription_created(subscription_data: Dict[str, Any], db: Session):
    """Handle subscription creation"""
    try:
        stripe_subscription_id = subscription_data["id"]
        customer_id = subscription_data["customer"]

        logger.info(f"Subscription created: {stripe_subscription_id}")

        # Check if we already have this subscription
        existing = SubscriptionService.get_subscription_by_stripe_id(db, stripe_subscription_id)
        if existing:
            logger.info(f"Subscription {stripe_subscription_id} already exists")
            return

        # Find user by Stripe customer ID
        user_statement = select(User).where(User.stripe_customer_id == customer_id)
        user = db.exec(user_statement).first()

        if not user:
            logger.error(f"No user found for Stripe customer {customer_id}")
            return

        # Get subscription plan
        price_id = subscription_data["items"]["data"][0]["price"]["id"]
        plan = SubscriptionService.get_subscription_plan_by_price_id(db, price_id)

        if not plan:
            logger.error(f"No plan found for price ID {price_id}")
            return

        # Create subscription record
        subscription = SubscriptionService.create_subscription(
            db=db,
            user=user,
            plan=plan,
            stripe_subscription_id=stripe_subscription_id,
            stripe_customer_id=customer_id,
            status=subscription_data["status"],
            trial_start=datetime.fromtimestamp(subscription_data["trial_start"]) if subscription_data.get("trial_start") else None,
            trial_end=datetime.fromtimestamp(subscription_data["trial_end"]) if subscription_data.get("trial_end") else None,
            current_period_start=datetime.fromtimestamp(subscription_data["current_period_start"]),
            current_period_end=datetime.fromtimestamp(subscription_data["current_period_end"])
        )

        # Send welcome email
        try:
            await send_subscription_welcome_email(user, subscription)
        except Exception as e:
            logger.error(f"Failed to send welcome email: {str(e)}")

    except Exception as e:
        logger.error(f"Error handling subscription created: {str(e)}")


async def handle_subscription_updated(subscription_data: Dict[str, Any], db: Session):
    """Handle subscription updates"""
    try:
        stripe_subscription_id = subscription_data["id"]

        logger.info(f"Subscription updated: {stripe_subscription_id}")

        # Update subscription in our database
        subscription = SubscriptionService.update_subscription_status(
            db=db,
            stripe_subscription_id=stripe_subscription_id,
            status=subscription_data["status"],
            current_period_start=datetime.fromtimestamp(subscription_data["current_period_start"]),
            current_period_end=datetime.fromtimestamp(subscription_data["current_period_end"]),
            canceled_at=datetime.fromtimestamp(subscription_data["canceled_at"]) if subscription_data.get("canceled_at") else None,
            cancel_at_period_end=subscription_data.get("cancel_at_period_end", False)
        )

        if subscription and subscription_data.get("cancel_at_period_end"):
            # Send cancellation notice
            user = subscription.user
            try:
                await send_subscription_cancellation_email(user, subscription)
            except Exception as e:
                logger.error(f"Failed to send cancellation email: {str(e)}")

    except Exception as e:
        logger.error(f"Error handling subscription updated: {str(e)}")


async def handle_subscription_deleted(subscription_data: Dict[str, Any], db: Session):
    """Handle subscription deletion"""
    try:
        stripe_subscription_id = subscription_data["id"]

        logger.info(f"Subscription deleted: {stripe_subscription_id}")

        # Update subscription status
        subscription = SubscriptionService.update_subscription_status(
            db=db,
            stripe_subscription_id=stripe_subscription_id,
            status="canceled"
        )

        if subscription:
            # Send subscription ended email
            user = subscription.user
            try:
                await send_subscription_ended_email(user, subscription)
            except Exception as e:
                logger.error(f"Failed to send subscription ended email: {str(e)}")

    except Exception as e:
        logger.error(f"Error handling subscription deleted: {str(e)}")


async def handle_invoice_finalized(invoice: Dict[str, Any], db: Session):
    """Handle invoice finalization"""
    try:
        logger.info(f"Invoice finalized: {invoice['id']}")

        # Could be used to send advance invoice notices
        subscription_id = invoice.get("subscription")
        if subscription_id:
            logger.info(f"Invoice finalized for subscription {subscription_id}")

    except Exception as e:
        logger.error(f"Error handling invoice finalized: {str(e)}")


async def handle_payment_method_attached(payment_method: Dict[str, Any], db: Session):
    """Handle payment method attachment"""
    try:
        customer_id = payment_method.get("customer")
        logger.info(f"Payment method attached for customer {customer_id}")

        # Update user's payment method information if needed
        # This could be used to track payment methods or send notifications

    except Exception as e:
        logger.error(f"Error handling payment method attached: {str(e)}")


# Email notification functions
async def send_payment_success_email(user: User, invoice: Dict[str, Any]):
    """Send payment success notification"""
    try:
        # Import here to avoid circular imports
        from app.services.email_service import EmailService

        subject = "Payment Successful - Pulse Premium"
        html_content = f"""
        <h2>Payment Successful!</h2>
        <p>Hi {user.name or user.email},</p>
        <p>Your payment of ${invoice['amount'] / 100:.2f} has been processed successfully.</p>
        <p>Thank you for supporting Pulse!</p>
        <p>You can view your invoice <a href="{invoice.get('hosted_invoice_url', '#')}">here</a>.</p>
        <br>
        <p>Best regards,<br>The Pulse Team</p>
        """

        # EmailService would need to be implemented
        # await EmailService.send_email(user.email, subject, html_content)
        logger.info(f"Payment success email would be sent to {user.email}")

    except Exception as e:
        logger.error(f"Error sending payment success email: {str(e)}")


async def send_payment_failed_email(user: User, invoice: Dict[str, Any]):
    """Send payment failure notification"""
    try:
        subject = "Payment Failed - Action Required"
        html_content = f"""
        <h2>Payment Failed</h2>
        <p>Hi {user.name or user.email},</p>
        <p>We were unable to process your payment of ${invoice['amount'] / 100:.2f}.</p>
        <p>Please update your payment information to avoid service interruption.</p>
        <p>You can update your payment method in your account settings.</p>
        <br>
        <p>Best regards,<br>The Pulse Team</p>
        """

        # await EmailService.send_email(user.email, subject, html_content)
        logger.info(f"Payment failed email would be sent to {user.email}")

    except Exception as e:
        logger.error(f"Error sending payment failed email: {str(e)}")


async def send_subscription_welcome_email(user: User, subscription: UserSubscription):
    """Send subscription welcome email"""
    try:
        subject = "Welcome to Pulse Premium!"
        html_content = f"""
        <h2>Welcome to Pulse Premium!</h2>
        <p>Hi {user.name or user.email},</p>
        <p>Thank you for subscribing to Pulse Premium! Your subscription is now active.</p>

        <h3>What's included:</h3>
        <ul>
            <li>Unlimited article analyses</li>
            <li>Advanced analytics dashboard</li>
            <li>Access to the challenge system</li>
            <li>API access</li>
        </ul>

        <p>Thank you for supporting independent journalism and ethical news analysis!</p>
        <br>
        <p>Best regards,<br>The Pulse Team</p>
        """

        # await EmailService.send_email(user.email, subject, html_content)
        logger.info(f"Welcome email would be sent to {user.email}")

    except Exception as e:
        logger.error(f"Error sending welcome email: {str(e)}")


async def send_subscription_cancellation_email(user: User, subscription: UserSubscription):
    """Send subscription cancellation notice"""
    try:
        subject = "Subscription Cancellation Notice"
        html_content = f"""
        <h2>Subscription Cancellation Notice</h2>
        <p>Hi {user.name or user.email},</p>
        <p>Your Pulse Premium subscription has been cancelled.</p>
        <p>You will continue to have access to premium features until {subscription.current_period_end.strftime('%B %d, %Y')}.</p>

        <p>If you change your mind, you can reactivate your subscription anytime before then.</p>

        <p>Thank you for being part of the Pulse community!</p>
        <br>
        <p>Best regards,<br>The Pulse Team</p>
        """

        # await EmailService.send_email(user.email, subject, html_content)
        logger.info(f"Cancellation notice email would be sent to {user.email}")

    except Exception as e:
        logger.error(f"Error sending cancellation email: {str(e)}")


async def send_subscription_ended_email(user: User, subscription: UserSubscription):
    """Send subscription ended email"""
    try:
        subject = "Your Pulse Premium Subscription Has Ended"
        html_content = f"""
        <h2>Subscription Ended</h2>
        <p>Hi {user.name or user.email},</p>
        <p>Your Pulse Premium subscription has ended.</p>

        <p>You can resubscribe anytime to regain access to premium features:</p>
        <ul>
            <li>Unlimited article analyses</li>
            <li>Advanced analytics</li>
            <li>Challenge system</li>
            <li>API access</li>
        </ul>

        <p>Thank you for your support!</p>
        <br>
        <p>Best regards,<br>The Pulse Team</p>
        """

        # await EmailService.send_email(user.email, subject, html_content)
        logger.info(f"Subscription ended email would be sent to {user.email}")

    except Exception as e:
        logger.error(f"Error sending subscription ended email: {str(e)}")