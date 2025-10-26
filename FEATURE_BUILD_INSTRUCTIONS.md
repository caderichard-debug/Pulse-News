# Subscription/Paywall Feature - Separate Build Instructions

This document explains how to build and test the subscription/paywall feature in a separate Docker environment without affecting the main application build.

## Overview

The subscription system includes:
- Stripe payment integration
- User subscription management
- Daily usage tracking and limits
- Premium feature gating
- Webhook handling for real-time payment updates

## Build Configuration

### Backend Docker Configuration

To build the backend with subscription features:

```bash
# Build the backend container with subscription features
docker-compose -f docker-compose.yml -f docker-compose.subscription.yml up --build backend
```

### Frontend Configuration

To build the frontend with subscription components:

```bash
# Install additional dependencies
cd frontend
npm install @stripe/stripe-js @stripe/react-stripe-js

# Build with subscription features enabled
npm run build:subscription
```

## Environment Configuration

Create a `.env.subscription` file with the following additional variables:

```bash
# Copy existing .env file
cp .env .env.subscription

# Add Stripe configuration
echo "STRIPE_SECRET_KEY=sk_test_..." >> .env.subscription
echo "STRIPE_PUBLISHABLE_KEY=pk_test_..." >> .env.subscription
echo "STRIPE_WEBHOOK_SECRET=whsec_..." >> .env.subscription
echo "STRIPE_WEBHOOK_ENDPOINT_URL=http://localhost:8000/api/webhooks/stripe" >> .env.subscription

# Subscription settings
echo "FREE_DAILY_ANALYSIS_LIMIT=10" >> .env.subscription
echo "FREE_DAILY_API_LIMIT=100" >> .env.subscription
echo "TRIAL_PERIOD_DAYS=14" >> .env.subscription
echo "SUBSCRIPTION_WEBHOOK_PATH=/api/webhooks/stripe" >> .env.subscription
```

## Database Setup

### Run Migration in Separate Environment

```bash
# Use the subscription environment file
docker-compose -f docker-compose.yml -f docker-compose.subscription.yml --env-file .env.subscription exec backend alembic upgrade head
```

### Seed Subscription Plans

```bash
# Seed subscription plans and grandfather existing users
docker-compose -f docker-compose.yml -f docker-compose.subscription.yml --env-file .env.subscription exec backend python seed_subscription_data.py
```

## Testing Configuration

### Stripe Test Mode Setup

1. Log into [Stripe Dashboard](https://dashboard.stripe.com/)
2. Enable test mode (toggle in top-left)
3. Get test API keys from Developers > API keys
4. Create test products and prices:
   - Premium Monthly: $5.00/month
   - Premium Annual: $50.00/year

### Webhook Testing

Use the Stripe CLI to test webhooks locally:

```bash
# Install Stripe CLI
# Then forward webhooks to your local backend
stripe listen --forward-to localhost:8000/api/webhooks/stripe
```

### Payment Testing

Use Stripe test cards for testing:
- Card number: `4242 4242 4242 4242`
- Expiry: Any future date
- CVC: Any 3 digits
- ZIP: Any 5 digits

## API Endpoints

### Subscription Management

- `GET /api/subscriptions/plans` - Get available plans
- `GET /api/subscriptions/current` - Get current subscription
- `POST /api/subscriptions/create` - Create new subscription
- `POST /api/subscriptions/cancel` - Cancel subscription
- `POST /api/subscriptions/reactivate` - Reactivate subscription
- `GET /api/subscriptions/usage` - Get usage statistics
- `GET /api/subscriptions/history` - Get payment history

### Webhooks

- `POST /api/webhooks/stripe` - Stripe webhook endpoint

## Feature Flags

The subscription system includes built-in feature checking:

```python
# Check if user has access to premium features
from app.services.subscription_service import SubscriptionService

# Check specific feature access
can_analyze = SubscriptionService.check_feature_access(db, user_id, "analysis")
is_premium = SubscriptionService.is_user_premium(db, user_id)
```

## Frontend Integration

### Stripe Components

```tsx
// Wrap your app with Stripe provider
import {Elements} from '@stripe/react-stripe-js'
import {loadStripe} from '@stripe/stripe-js'

const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY)

function App() {
  return (
    <Elements stripe={stripePromise}>
      <YourApp />
    </Elements>
  )
}
```

### Usage Tracking

```tsx
// Track usage when users analyze articles
const { incrementUsage } = useSubscription()

await incrementUsage('analysis')
```

## Deployment Considerations

### Environment Variables for Production

```bash
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_... (live webhook secret)
STRIPE_WEBHOOK_ENDPOINT_URL=https://yourdomain.com/api/webhooks/stripe
```

### Webhook Security

- Always verify webhook signatures
- Use HTTPS in production
- Implement proper error handling

## Rollback Plan

To disable subscription features:

1. Remove subscription environment variables
2. Revert to main Docker configuration
3. Database remains unchanged (subscription tables are harmless)
4. All users default to FREE tier

## Monitoring

### Key Metrics to Track

- Conversion rate (free to paid)
- Trial conversion rate
- Churn rate
- Revenue per user
- Feature usage patterns

### Alerting

- Payment failure notifications
- Webhook processing errors
- High usage limit breaches
- Stripe API rate limits

## Support URLs

- Stripe Dashboard: https://dashboard.stripe.com/
- Stripe API Docs: https://stripe.com/docs/api
- Stripe Testing Guide: https://stripe.com/docs/testing

## Troubleshooting

### Common Issues

1. **Migration failures**: Ensure no NULL constraints on existing tables
2. **Webhook verification failures**: Check webhook secret configuration
3. **Payment failures**: Verify Stripe API keys and test mode
4. **Usage tracking not working**: Check middleware configuration

### Debug Mode

Enable debug logging:

```bash
# Set environment variable
DEBUG_SUBSCRIPTION=true

# Or in code
import logging
logging.getLogger('app.services.subscription_service').setLevel(logging.DEBUG)
```

## Feature Dependencies

The subscription system requires:
- PostgreSQL database
- Stripe account (test or live)
- Redis (for caching subscription status)
- Email service (for payment notifications)

## Performance Considerations

- Cache subscription status in Redis
- Batch usage tracking updates
- Implement rate limiting for subscription endpoints
- Monitor database query performance for usage tracking

## Security Notes

- Never expose Stripe secret keys in frontend
- Validate all webhook signatures
- Implement proper access controls on subscription endpoints
- Log all subscription changes for audit trails
- Encrypt sensitive data at rest