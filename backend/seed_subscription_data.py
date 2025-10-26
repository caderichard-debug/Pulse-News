"""
Seed subscription data - create subscription plans and grandfather existing users.
"""

import json
import logging
from datetime import datetime, timedelta
from sqlmodel import Session, select
from app.database import engine
from app.models import User, SubscriptionPlan, SubscriptionTier
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_subscription_plans(session: Session):
    """Create subscription plans"""

    plans_data = [
        {
            "name": "Premium Monthly",
            "description": "Unlimited article analyses, advanced analytics, and challenge system access",
            "stripe_price_id": "price_1Placeholder",  # Replace with actual Stripe price ID
            "price": 500,  # $5.00 in cents
            "currency": "usd",
            "billing_interval": "month",
            "features": json.dumps([
                "Unlimited article analyses",
                "Advanced analytics dashboard",
                "Weekly challenge system participation",
                "API access (1000 calls/month)",
                "Premium newsletter content",
                "Priority email support"
            ]),
            "trial_period_days": 14,
            "sort_order": 1
        },
        {
            "name": "Premium Annual",
            "description": "Save 17% with annual billing - all Premium features for a full year",
            "stripe_price_id": "price_2Placeholder",  # Replace with actual Stripe price ID
            "price": 5000,  # $50.00 in cents
            "currency": "usd",
            "billing_interval": "year",
            "features": json.dumps([
                "Unlimited article analyses",
                "Advanced analytics dashboard",
                "Weekly challenge system participation",
                "API access (12000 calls/year)",
                "Premium newsletter content",
                "Priority email support",
                "Annual savings (2 months free)"
            ]),
            "trial_period_days": 14,
            "sort_order": 2
        },
        {
            "name": "Enterprise",
            "description": "Custom solutions for teams and organizations",
            "stripe_price_id": "price_3Placeholder",  # Replace with actual Stripe price ID
            "price": 50000,  # $500.00 in cents
            "currency": "usd",
            "billing_interval": "month",
            "features": json.dumps([
                "Everything in Premium",
                "Team management dashboard",
                "Custom analytics reports",
                "Unlimited API access",
                "Dedicated support manager",
                "Custom integrations",
                "SLA guarantee"
            ]),
            "trial_period_days": 30,
            "sort_order": 3,
            "is_active": False  # Enterprise tier not yet available
        }
    ]

    created_plans = []
    for plan_data in plans_data:
        # Check if plan already exists
        existing = session.exec(
            select(SubscriptionPlan).where(SubscriptionPlan.name == plan_data["name"])
        ).first()

        if existing:
            logger.info(f"Subscription plan '{plan_data['name']}' already exists")
            created_plans.append(existing)
            continue

        plan = SubscriptionPlan(**plan_data)
        session.add(plan)
        created_plans.append(plan)
        logger.info(f"Created subscription plan: {plan.name}")

    session.commit()
    return created_plans


def grandfather_existing_users(session: Session):
    """Grandfather existing users to Premium tier"""

    # Get all users created before the subscription system launch
    # Using a cutoff date - adjust this as needed
    cutoff_date = datetime.utcnow() - timedelta(days=1)  # All users older than 1 day

    existing_users = session.exec(
        select(User).where(
            User.created_at < cutoff_date
        )
    ).all()

    grandfathered_count = 0

    for user in existing_users:
        if user.subscription_tier == SubscriptionTier.FREE:
            user.subscription_tier = SubscriptionTier.PREMIUM
            grandfathered_count += 1
            logger.info(f"Grandfathered user {user.email} to Premium tier")

    session.commit()

    logger.info(f"Grandfathered {grandfathered_count} existing users to Premium tier")
    return grandfathered_count


def create_admin_promo_codes(session: Session):
    """Create promotional codes for admin use"""

    # This would require additional models for promo codes
    # For now, we'll just log that this step needs to be done manually
    logger.info("Note: Create promo codes manually through Stripe Dashboard:")
    logger.info("- FRIENDS20: 20% off for friends")
    logger.info("- BETA50: 50% off for beta testers")
    logger.info("- COMMUNITY15: 15% off for community members")


def verify_setup(session: Session):
    """Verify that the subscription system is properly set up"""

    # Check subscription plans
    plans = session.exec(select(SubscriptionPlan)).all()
    logger.info(f"Found {len(plans)} subscription plans")

    # Check user distribution
    free_users = session.exec(
        select(User).where(User.subscription_tier == SubscriptionTier.FREE)
    ).all()

    premium_users = session.exec(
        select(User).where(User.subscription_tier == SubscriptionTier.PREMIUM)
    ).all()

    logger.info(f"User distribution:")
    logger.info(f"  Free tier: {len(free_users)} users")
    logger.info(f"  Premium tier: {len(premium_users)} users")

    # Check for any users without proper subscription tier
    all_users = session.exec(select(User)).all()
    logger.info(f"Total users in database: {len(all_users)}")

    return {
        "plans_count": len(plans),
        "free_users": len(free_users),
        "premium_users": len(premium_users),
        "total_users": len(all_users)
    }


def main():
    """Main seeding function"""

    logger.info("Starting subscription data seeding...")

    try:
        with Session(engine) as session:
            # Create subscription plans
            logger.info("Creating subscription plans...")
            plans = create_subscription_plans(session)

            # Grandfather existing users
            logger.info("Grandfathering existing users...")
            grandfathered_count = grandfather_existing_users(session)

            # Create admin promo codes (manual step)
            logger.info("Setting up promo code notes...")
            create_admin_promo_codes(session)

            # Verify setup
            logger.info("Verifying setup...")
            stats = verify_setup(session)

            logger.info("Subscription data seeding completed successfully!")
            logger.info(f"Final stats: {stats}")

            # Print instructions for next steps
            logger.info("\n=== NEXT STEPS ===")
            logger.info("1. Update Stripe price IDs in the created plans")
            logger.info("2. Configure webhook endpoints in Stripe Dashboard")
            logger.info("3. Test the subscription flow with Stripe test cards")
            logger.info("4. Monitor the first few subscription conversions")
            logger.info("5. Set up billing and revenue analytics")

    except Exception as e:
        logger.error(f"Error during subscription data seeding: {str(e)}")
        raise


if __name__ == "__main__":
    main()