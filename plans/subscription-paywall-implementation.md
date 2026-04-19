# Subscription/Paywall Feature Implementation Plan

## Overview
This plan outlines the implementation of a subscription system for Pulse with three tiers (Free, Premium, Enterprise) and a community-focused approach. The system will use Stripe for payment processing and implement hard paywalls for premium features.

## Subscription Tiers & Pricing

### Free Tier
- 10 article analyses per day
- Basic analytics dashboard
- Access to article feed
- Email newsletter (without challenge section)

### Premium Tier ($5/month, $50/year)
- Unlimited article analyses
- Advanced analytics dashboard with customizable charts
- Full challenge system access
- Premium newsletter content with challenges
- API access (basic tier)
- 2-week free trial for new users

### Enterprise Tier (Future placeholder)
- Higher API limits
- Advanced features (to be defined later)
- Custom pricing

## Implementation Phases

### Phase 1: Backend Foundation (Stripe Integration & Database Schema)

#### 1.1 Database Schema Changes
**Files to modify:**
- `backend/app/models/` - Add new models
- `backend/alembic/versions/` - Create migration

**New Models to Add:**
```python
# Subscription Plans
class SubscriptionPlan(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True)
    stripe_price_id: str = Field(unique=True)
    price: int  # in cents
    currency: str = Field(default="usd")
    billing_interval: str  # "month" or "year"
    features: List[str] = Field(sa_column=Column(JSON))
    is_active: bool = Field(default=True)
    sort_order: int = Field(default=0)

# User Subscriptions
class UserSubscription(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    stripe_subscription_id: str = Field(unique=True)
    stripe_customer_id: str
    plan_id: int = Field(foreign_key="subscriptionplan.id")
    status: str  # "active", "canceled", "past_due", "trialing"
    current_period_start: datetime
    current_period_end: datetime
    trial_start: Optional[datetime]
    trial_end: Optional[datetime]
    canceled_at: Optional[datetime]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Usage Tracking
class DailyUsage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    date: date = Field(unique=True, index=True)
    analyses_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Promo Codes
class PromoCode(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(unique=True, index=True)
    stripe_coupon_id: str
    discount_type: str  # "percentage" or "fixed_amount"
    discount_value: int
    max_uses: Optional[int]
    used_count: int = Field(default=0)
    expires_at: Optional[datetime]
    is_active: bool = Field(default=True)
    created_by: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

# User Promo Code Uses
class UserPromoCodeUse(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    promo_code_id: int = Field(foreign_key="promocode.id")
    used_at: datetime = Field(default_factory=datetime.utcnow)
```

#### 1.2 Update Existing User Model
**File to modify:** `backend/app/models/user.py`
```python
# Add to existing User model:
stripe_customer_id: Optional[str] = Field(default=None)
subscription_tier: SubscriptionTier = Field(default=SubscriptionTier.FREE)
trial_start: Optional[datetime] = Field(default=None)
trial_end: Optional[datetime] = Field(default=None)
```

#### 1.3 Stripe Integration Setup
**Files to create/modify:**
- `backend/app/services/stripe_service.py` - New Stripe service
- `backend/app/core/config.py` - Add Stripe config
- `backend/.env.example` - Add environment variables

**Environment Variables to Add:**
```bash
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_WEBHOOK_ENDPOINT_URL=https://yourdomain.com/webhooks/stripe
```

**Stripe Dashboard Setup Instructions:**
1. Create Stripe account at https://dashboard.stripe.com/register
2. Get API keys from Dashboard > Developers > API keys
3. Create products:
   - "Premium Monthly" - $5.00/month
   - "Premium Annual" - $50.00/year
4. Get Price IDs from Products section
5. Set up webhook endpoint for real-time updates
6. Enable payment methods: Card, Apple Pay, Google Pay

#### 1.4 Create Subscription Service Layer
**File to create:** `backend/app/services/subscription_service.py`
- Handle subscription creation/cancellation
- Manage trial periods
- Process webhook events
- Usage tracking logic
- Promo code validation

#### 1.5 Add Subscription API Endpoints
**File to create:** `backend/app/api/v1/subscriptions.py`
```python
# New endpoints:
GET  /subscriptions/plans                    # Get available plans
GET  /subscriptions/current                  # Get user's current subscription
POST /subscriptions/create                   # Create new subscription
POST /subscriptions/cancel                   # Cancel subscription
POST /subscriptions/reactivate              # Reactivate canceled subscription
PUT  /subscriptions/payment-method           # Update payment method
GET  /subscriptions/usage                    # Get current usage stats
GET  /subscriptions/history                  # Payment history
POST /subscriptions/validate-promo          # Validate promo code
POST /subscriptions/apply-promo              # Apply promo code
```

#### 1.6 Add Webhook Handler
**File to create:** `backend/app/api/v1/webhooks.py`
- Handle Stripe webhook events
- Update subscription status in real-time
- Send confirmation emails
- Handle failed payments

### Phase 2: Usage Tracking & Limiting System

#### 2.1 Implement Daily Usage Tracking
**Files to modify:**
- `backend/app/services/usage_service.py` - New usage service
- `backend/app/api/v1/analyze.py` - Add usage counting

**Usage Tracking Logic:**
- Increment counter for each article analysis
- Reset counters at midnight UTC
- Check limits before allowing analysis
- Return usage info in API responses

#### 2.2 Add Middleware for Subscription Checks
**File to create:** `backend/app/middleware/subscription_middleware.py`
- Check user subscription status
- Enforce usage limits
- Block access to premium features
- Add subscription info to response headers

#### 2.3 Update Analyze Endpoint
**File to modify:** `backend/app/api/v1/analyze.py`
- Add usage validation before processing
- Return remaining daily analyses
- Handle Chrome extension usage properly

### Phase 3: Frontend Implementation

#### 3.1 Create Subscription Pages
**Files to create:**
- `frontend/app/subscription/page.tsx` - Subscription plans overview
- `frontend/app/subscription/billing/page.tsx` - Payment method management
- `frontend/app/subscription/history/page.tsx` - Payment history
- `frontend/app/subscription/cancel/page.tsx` - Cancellation flow
- `frontend/app/subscription/success/page.tsx` - Success page

#### 3.2 Add Subscription State Management
**Files to modify:**
- `frontend/lib/auth-context.tsx` - Add subscription state
- `frontend/hooks/use-subscription.ts` - New subscription hook
- `frontend/components/subscription-provider.tsx` - Subscription context

#### 3.3 Create Subscription Components
**Components to create:**
- `frontend/components/subscription/plan-card.tsx`
- `frontend/components/subscription/payment-form.tsx`
- `frontend/components/subscription/usage-counter.tsx`
- `frontend/components/subscription/upgrade-prompt.tsx`
- `frontend/components/subscription/trial-banner.tsx`

#### 3.4 Add Stripe Elements Integration
**Dependencies to install:**
```bash
npm install @stripe/stripe-js @stripe/react-stripe-js
```

**Files to create:**
- `frontend/components/stripe/payment-element.tsx`
- `frontend/components/stripe/stripe-provider.tsx`

#### 3.5 Update Preferences Page
**File to modify:** `frontend/app/preferences/page.tsx`
- Add new "Subscription & Usage" tab
- Show current usage statistics
- Display remaining daily analyses
- Show subscription status and billing info

### Phase 4: Feature Gating Implementation

#### 4.1 Update Analytics Dashboard
**Files to modify:**
- `frontend/app/analytics/page.tsx` - Add premium feature checks
- `backend/app/api/v1/analytics.py` - Add subscription-based data access

**Premium Analytics Features:**
- Customizable charts by source/bias
- Additional chart types
- Export functionality
- Advanced filtering options

#### 4.2 Update Challenge System
**Files to modify:**
- `backend/app/services/newsletter_service.py` - Exclude challenges from free emails
- `frontend/app/challenge/page.tsx` - Add subscription check
- `backend/app/api/v1/challenge.py` - Enforce premium access

#### 4.3 Update Analyze Page
**Files to modify:**
- `frontend/app/analyze/page.tsx` - Add usage counter and upgrade prompts
- `backend/app/api/v1/analyze.py` - Implement daily limits

#### 4.4 Create API Access System
**Files to create:**
- `backend/app/api/v1/api-keys.py` - API key management
- `backend/app/services/api_service.py` - API usage tracking
- `frontend/app/api-docs/page.tsx` - API documentation page

### Phase 5: Email & Notification Updates

#### 5.1 Update Newsletter Service
**File to modify:** `backend/app/services/newsletter_service.py`
- Exclude challenge section from free user emails
- Add premium content sections for paid users
- Handle trial expiration notifications

#### 5.2 Create Subscription Email Templates
**Email templates to create:**
- Welcome to premium email
- Trial expiration reminder (3 days, 1 day)
- Payment failed notification
- Subscription canceled confirmation
- Monthly premium newsletter

#### 5.3 Add Email Service Integration
**File to modify:** `backend/app/services/email_service.py`
- Add subscription-related email functions
- Integrate with payment notifications

### Phase 6: Admin Panel & Management

#### 6.1 Add Subscription Management to Admin
**Files to modify:**
- `frontend/app/admin/users/page.tsx` - Add subscription info
- `backend/app/api/v1/admin-panel/users.py` - Add subscription endpoints

**Admin Features:**
- View user subscription status
- Manually grant/revoke premium access
- Create and manage promo codes
- View subscription analytics
- Handle billing issues

#### 6.2 Add Subscription Analytics
**Files to create:**
- `backend/app/api/v1/admin/analytics.py` - Subscription analytics
- `frontend/app/admin/analytics/page.tsx` - Revenue and subscription metrics

### Phase 7: Testing & Deployment

#### 7.1 Unit & Integration Tests
**Test files to create:**
- `backend/tests/test_subscription_service.py`
- `backend/tests/test_stripe_service.py`
- `backend/tests/test_usage_tracking.py`
- `frontend/tests/components/subscription/`

#### 7.2 End-to-End Testing
**E2E tests to implement:**
- Complete subscription flow
- Trial signup and expiration
- Usage limiting enforcement
- Payment method updates
- Cancellation flow

#### 7.3 Deployment Checklist
- Update environment variables
- Run database migrations
- Set up Stripe webhooks
- Update DNS for webhook endpoint
- Monitor initial subscriptions
- Set up payment failure monitoring

## Migration Strategy for Existing Users

### Grandfathering Implementation
1. **Identify existing users** - All users with `created_at < migration_date`
2. **Grant automatic premium** - Set `subscription_tier = PREMIUM` for existing users
3. **Create Stripe customer records** - Batch create customers for grandfathered users
4. **Send notification emails** - Inform users of their premium status
5. **Add upgrade prompts** - Encourage voluntary subscriptions to support the project

### Database Migration Script
```python
# Alembic migration to grandfather existing users
def upgrade():
    # Update existing users to premium
    connection = op.get_bind()
    connection.execute(
        "UPDATE user SET subscription_tier = 'PREMIUM' WHERE created_at < '2025-01-01'"
    )
```

## Success Metrics & Monitoring

### Key Metrics to Track
- Free to premium conversion rate
- Trial to paid conversion rate
- Monthly recurring revenue (MRR)
- Churn rate
- Average revenue per user (ARPU)
- Usage patterns of premium features

### Monitoring Setup
- Stripe payment failure alerts
- Usage limit breach notifications
- Subscription status change alerts
- Revenue milestone notifications

## Future Considerations (Phase 2+)

### Enterprise Tier Features
- Team management and seat-based pricing
- Advanced API access with higher limits
- Custom analytics and reporting
- Dedicated support options
- White-label options

### Advanced Features
- Usage-based pricing for AI features
- Student/educator discount system
- Annual payment discounts
- Referral program
- Community funding goals and progress bars

### External Integrations
- Mailchimp/ConvertKit sync for email marketing
- Google Analytics revenue tracking
- QuickBooks/Xero accounting integration
- CRM integration for customer management

## Security & Compliance

### Security Measures
- Secure storage of Stripe customer IDs
- PCI compliance through Stripe integration
- Rate limiting on subscription endpoints
- Audit logging for all subscription changes

### Compliance Implementation
- GDPR-compliant data handling
- User data export functionality
- Data deletion requests handling
- Privacy policy updates for billing data

## Timeline Estimate

### Phase 1: Backend Foundation (2-3 days)
- Database schema and migrations
- Stripe service integration
- Subscription API endpoints

### Phase 2: Usage Tracking (1-2 days)
- Daily usage implementation
- Middleware and endpoint updates

### Phase 3: Frontend Implementation (3-4 days)
- Subscription pages and components
- Stripe Elements integration
- State management updates

### Phase 4: Feature Gating (2-3 days)
- Analytics and challenge updates
- Analyze page limits
- API access system

### Phase 5: Email & Notifications (1-2 days)
- Newsletter updates
- Email templates
- Notification systems

### Phase 6: Admin Features (1-2 days)
- Admin panel updates
- Analytics and management tools

### Phase 7: Testing & Deployment (2-3 days)
- Comprehensive testing
- Deployment preparation
- Production monitoring setup

**Total Estimated Time: 12-19 days**

## Dependencies

### New Package Dependencies
```bash
# Backend
pip install stripe

# Frontend
npm install @stripe/stripe-js @stripe/react-stripe-js
```

### External Services
- Stripe account setup
- Webhook endpoint configuration
- Email template updates
- DNS configuration for webhooks

This comprehensive plan will transform Pulse into a sustainable platform while maintaining the open-source community vibe you're aiming for. The implementation focuses on creating a smooth user experience that encourages voluntary support while providing real value to premium subscribers.