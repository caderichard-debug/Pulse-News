# Newsletter Challenge System - Implementation Guide

## Overview
Weekly controversial claim challenge system where users select one of 4 ethical framework-level claims on Friday, then receive 7 days of challenging articles to broaden their perspective.

## Feature Requirements (Clarified)

### 1. Claim Generation
- **Auto-generated** from current news topics using AI analysis
- **Political balance**: Ensure spectrum of perspectives (left/center/right)
- **Controversy levels**: Mix from relatively calm to relatively controversial
- **Abstraction level**: Ethical framework level, not specific facts
- **Opinion-based**: No fact-checking required, focus on philosophical/ethical positions
- **Goal**: Help users flesh out their own ethical views

### 2. User Interface
- **Friday newsletter**: Link to dedicated challenge form page
- **Form access**: Only via newsletter link, NOT in navigation
- **Locking mechanism**:
  - Lock form after user submits for current week
  - Unlock automatically when next challenge becomes available
- **Form deadline**: Users must respond by Friday to start 7-day challenge

### 3. Article Selection Algorithm
- **Priority 1**: Use existing article analysis and viewpoint system
- **Priority 2**: Web search function if insufficient database articles
- **Fallback**: Go back in time as needed to find challenging content
- **Challenge criteria**: Articles that oppose user's ethical stance on selected claim

### 4. Data Tracking
- User's claim selections
- Agreement levels (Likert scale)
- Which challenge articles were sent to each user
- User engagement with challenge articles

### 5. User Preferences
- **New setting**: "Challenge Participation" toggle
- **Location**: Preferences page, above "Newsletter Subscription"
- **Label change**: Change "Settings" tab to "Newsletter"

## Phase-by-Phase Implementation

### Phase 1: Database Schema & Models ✅

#### 1.1 New Enums Added
```python
class ChallengeClaimType(str, Enum):
    POLICY = "policy"
    SOCIAL_ISSUE = "social_issue"
    ECONOMIC = "economic"
    TECHNOLOGY = "technology"
    ENVIRONMENT = "environment"
    FOREIGN_POLICY = "foreign_policy"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"

class ChallengeResponseStatus(str, Enum):
    PENDING = "pending"
    RESPONDED = "responded"
    COMPLETED = "completed"
    SKIPPED = "skipped"

class AgreementLevel(str, Enum):
    STRONGLY_DISAGREE = "strongly_disagree"
    DISAGREE = "disagree"
    NEUTRAL = "neutral"
    AGREE = "agree"
    STRONGLY_AGREE = "strongly_agree"
```

#### 1.2 Core Models
- **WeeklyChallenge**: Weekly challenge sets with 4 claims
- **ChallengeClaim**: Individual ethical claims with controversy scoring
- **UserChallengeResponse**: User selections and agreement levels
- **ChallengeArticleAssignment**: Daily challenge articles (7 days)
- **ChallengeEngagement**: Engagement tracking and analytics

#### 1.3 Key Model Features
- **Ethical focus**: Claims at philosophical/ethical level, not factual
- **Political balance**: Tracking of political lean distribution
- **Engagement metrics**: Open/click tracking for challenge articles
- **Web search integration**: Fields for external article sources
- **User control**: Opt-out preferences and feedback collection

#### 1.4 Relationships Added
- User → ChallengeResponse → ChallengeClaim (many-to-one)
- User → ChallengeAssignment → Article (challenge articles)
- WeeklyChallenge → ChallengeClaim (1-to-4)
- ChallengeResponse → ChallengeAssignment (1-to-7)

### Phase 2: Claim Generation & Management

#### 2.1 Challenge Claim Generator Service (`challenge_claim_generator.py`)
**Purpose**: Auto-generate 4 controversial ethical claims from current articles

**Algorithm**:
1. **Article Analysis**: Analyze articles from past 7 days
2. **Topic Extraction**: Identify key ethical dilemmas and frameworks
3. **Claim Generation**: Use GPT-4o-mini to generate ethical-level claims
4. **Controversy Scoring**: Rate claims on controversy (0.0-1.0) and reasonableness (0.0-1.0)
5. **Political Balance**: Ensure distribution across left/center/right perspectives
6. **Quality Filter**: Remove claims that are too factual or too extreme

**AI Prompt Template**:
```
Based on recent news articles about [TOPIC], generate 2-3 controversial ethical claims at the philosophical level.

Requirements:
- Focus on ethical frameworks, not specific facts
- Balance perspectives (left/center/right if applicable)
- Make claims debatable but reasonable
- Avoid misinformation or extreme positions
- Each claim should be max 300 characters

Recent articles context: [ARTICLE_SUMMARIES]
```

#### 2.2 Weekly Challenge Manager (`challenge_manager.py`)
**Purpose**: Orchestrate weekly challenge creation and publishing

**Schedule**: Every Wednesday at 2:00 PM PST
**Process**:
1. **Generate Claims**: Call claim generator for 8-12 candidate claims
2. **Select & Balance**: Choose 4 claims with political/topic diversity
3. **Controversy Mix**: Ensure mix of calm to controversial claims
4. **Review Check**: Flag for admin review if controversy score > 0.8
5. **Create Challenge**: Build WeeklyChallenge record with 4 ChallengeClaim records
6. **Publish**: Set is_published=true for Friday delivery

#### 2.3 Scheduler Integration
**Add to scheduler.py**:
```python
# Job 5: Generate weekly challenges - Wednesdays at 2:00 PM PST
scheduler.add_job(
    func=weekly_challenge_generation_job,
    trigger=CronTrigger(day_of_week=2, hour=14, minute=0, timezone='America/Los_Angeles'),  # Wednesday
    id='generate_weekly_challenges',
    name='Generate Weekly Challenge Claims',
    replace_existing=True,
    max_instances=1,
)
```

### Phase 3: Newsletter Integration

#### 3.1 Newsletter Template Enhancement
**Friday Challenge Section**:
```html
<!-- Challenge Section (Fridays only) -->
{% if challenge and user.challenge_participation_enabled %}
<div class="challenge-section">
    <h2>🤔 Weekly Ethical Challenge</h2>
    <p>This week's ethical dilemma. Choose one claim that resonates with you:</p>

    {% for claim in challenge.claims %}
    <div class="claim-option">
        <p><strong>{{ claim.display_order }}.</strong> {{ claim.claim_text }}</p>
    </div>
    {% endfor %}

    <div class="challenge-cta">
        <a href="{{ frontend_url }}/challenge/{{ challenge.week_start_date.strftime('%Y-%m-%d') }}"
           class="btn-primary">
           Share Your Perspective →
        </a>
    </div>
</div>
{% endif %}
```

#### 3.2 Newsletter Service Integration
**Modify newsletter_service.py**:
```python
def _generate_newsletter_for_user(user: User, session: Session):
    # ... existing code ...

    # Add Friday challenge section if applicable
    template_data["challenge"] = None
    if datetime.utcnow().weekday() == 4 and user.challenge_participation_enabled:  # Friday
        challenge = _get_current_challenge(session)
        if challenge:
            template_data["challenge"] = {
                "id": challenge.id,
                "week_start_date": challenge.week_start_date.strftime('%Y-%m-%d'),
                "title": challenge.title,
                "claims": [
                    {
                        "display_order": claim.display_order,
                        "claim_text": claim.claim_text
                    }
                    for claim in sorted(challenge.claims, key=lambda c: c.display_order)
                ]
            }
```

### Phase 4: Challenge Form & User Response

#### 4.1 Challenge Form Page (`challenge/[date]/page.tsx`)
**Features**:
- **Access control**: Only accessible via newsletter link
- **Locking mechanism**: Prevent duplicate submissions
- **Form validation**: Ensure one claim selected
- **Responsive design**: Mobile-friendly

**Form Structure**:
```tsx
<div className="challenge-form">
    <h1>Weekly Ethical Challenge</h1>
    <p>Select the claim that most aligns with your perspective:</p>

    {claims.map(claim => (
        <label key={claim.id} className="claim-option">
            <input
                type="radio"
                name="selected_claim"
                value={claim.id}
                onChange={() => setSelectedClaim(claim.id)}
            />
            <span>{claim.display_order}. {claim.claim_text}</span>
        </label>
    ))}

    <div className="agreement-section">
        <h3>How strongly do you agree with this claim?</h3>
        <div className="likert-scale">
            {AGREEMENT_OPTIONS.map(option => (
                <label key={option.value}>
                    <input
                        type="radio"
                        name="agreement_level"
                        value={option.value}
                        onChange={() => setAgreementLevel(option.value)}
                    />
                    <span>{option.label}</span>
                </label>
            ))}
        </div>
    </div>

    <button
        type="submit"
        disabled={!selectedClaim || !agreementLevel || isSubmitting}
        className="btn-primary"
    >
        Submit Response
    </button>
</div>
```

#### 4.2 Challenge API Routes (`routes/challenge.py`)
**Endpoints**:
```python
@router.get("/challenge/{week_date}")
def get_challenge_form(week_date: str, current_user: User = Depends(get_current_user)):
    """Get challenge form for specific week"""

@router.post("/challenge/{week_date}/respond")
def submit_challenge_response(
    week_date: str,
    response: ChallengeResponseCreate,
    current_user: User = Depends(get_current_user)
):
    """Submit user's claim selection and agreement level"""

@router.get("/challenge/current")
def get_current_challenge(current_user: User = Depends(get_current_user)):
    """Get current week's challenge for logged-in user"""

@router.get("/challenge/my-responses")
def get_user_challenge_responses(current_user: User = Depends(get_current_user)):
    """Get user's challenge history and current status"""
```

#### 4.3 Response Processing Logic
```python
def process_challenge_response(
    user_id: int,
    weekly_challenge_id: int,
    selected_claim_id: int,
    agreement_level: AgreementLevel,
    response_source: str = "web_form"
):
    """Process user's challenge response and trigger article assignments"""

    # 1. Create UserChallengeResponse
    response = UserChallengeResponse(
        user_id=user_id,
        weekly_challenge_id=weekly_challenge_id,
        selected_claim_id=selected_claim_id,
        agreement_level=agreement_level,
        responded_at=datetime.utcnow(),
        response_source=response_source,
        status=ChallengeResponseStatus.RESPONDED
    )
    session.add(response)
    session.flush()

    # 2. Schedule challenge article assignments
    schedule_challenge_articles(response.id)

    return response
```

### Phase 5: Challenge Article Assignment

#### 5.1 Article Matching Algorithm (`challenge_article_matcher.py`)
**Purpose**: Find articles that challenge user's ethical stance

**Algorithm Steps**:
1. **Analyze User Stance**:
   - Extract ethical position from selected claim
   - Consider agreement level (strongly agree vs disagree changes opposition strength)

2. **Search Strategy**:
   ```python
   def find_challenge_articles(user_stance, user_preferences, max_articles=7):
       # Priority 1: Existing viewpoint analysis
       opposing_articles = find_opposing_viewpoints(
           claim_topic=user_stance.topic,
           user_position=user_stance.position,
           user_sources=user_preferences.subscribed_sources
       )

       # Priority 2: Web search if insufficient
       if len(opposing_articles) < max_articles:
           web_results = search_challenging_articles(
               query=build_challenge_query(user_stance),
               max_results=max_articles - len(opposing_articles)
           )
           opposing_articles.extend(web_results)

       # Priority 3: Historical articles if still insufficient
       if len(opposing_articles) < max_articles:
           historical = find_historical_opposing_articles(
               user_stance=user_stance,
               days_back=30,  # Go back as needed
               max_results=max_articles - len(opposing_articles)
           )
           opposing_articles.extend(historical)

       return opposing_articles[:max_articles]
   ```

3. **Opposition Scoring**: Rate how strongly each article challenges user's stance
4. **Diversity Selection**: Ensure variety of sources and perspectives
5. **Quality Filter**: Prefer articles with complete analysis (frameworks, statistics, context)

#### 5.2 Daily Challenge Processing
**Schedule**: Daily at 6:00 AM PST
**Process**:
```python
def daily_challenge_assignment_job():
    """Assign daily challenge articles to users"""

    # Get users who need today's challenge article
    today = datetime.utcnow().date()
    assignments_needed = session.exec(
        select(UserChallengeResponse)
        .where(UserChallengeResponse.status == ChallengeResponseStatus.RESPONDED)
        .where(UserChallengeResponse.challenge_started_at <= today)
        .where(UserChallengeResponse.challenge_completed_at.is_(None))
        .where(UserChallengeResponse.articles_sent_count < 7)
    ).all()

    for response in assignments_needed:
        day_number = response.articles_sent_count + 1

        # Get assigned article for this day
        article = get_challenge_article_for_day(response.id, day_number)

        if article:
            assignment = ChallengeArticleAssignment(
                user_challenge_response_id=response.id,
                user_id=response.user_id,
                article_id=article.id,
                day_number=day_number,
                assignment_date=today,
                opposition_strength=article.opposition_score,
                match_algorithm=article.match_method,
                match_reasoning=article.reasoning
            )
            session.add(assignment)

            # Update response tracking
            response.articles_sent_count += 1
            if response.articles_sent_count == 7:
                response.challenge_completed_at = datetime.utcnow()
                response.status = ChallengeResponseStatus.COMPLETED
```

#### 5.3 Web Search Integration
**Search Function**:
```python
def search_challenging_articles(query: str, max_results: int = 5):
    """Search web for articles that challenge specific ethical stance"""

    search_query = f"opposing viewpoint {query} debate argument counter"

    # Use existing web search capabilities
    search_results = web_search(search_query, max_results=max_results * 2)  # Get more to filter

    challenging_articles = []
    for result in search_results:
        # Quick analysis to determine if truly challenging
        if is_challenging_perspective(result, query):
            challenging_articles.append(result)

    return challenging_articles[:max_results]
```

### Phase 6: User Interface Updates

#### 6.1 Preferences Page Enhancement
**Add Challenge Participation Toggle**:
```tsx
// In preferences/page.tsx
<div className="preference-section">
    <h2>Newsletter Preferences</h2>

    <div className="preference-item">
        <label className="toggle-label">
            Challenge Participation
            <span className="preference-description">
                Receive weekly ethical challenges to broaden your perspective
            </span>
        </label>
        <Toggle
            checked={userPreferences.challenge_participation_enabled}
            onChange={handleChallengeToggleChange}
        />
    </div>

    <div className="preference-item">
        <label className="toggle-label">
            Newsletter Subscription
            <span className="preference-description">
                Daily digest of personalized news and insights
            </span>
        </label>
        <Toggle
            checked={userPreferences.newsletter_enabled}
            onChange={handleNewsletterToggleChange}
        />
    </div>
</div>
```

#### 6.2 Navigation Tab Rename
**Change "Settings" to "Newsletter"**:
```tsx
// In Navbar.tsx
const navigation = [
    { name: 'Dashboard', href: '/dashboard', current: pathname === '/dashboard' },
    { name: 'Feed', href: '/feed', current: pathname === '/feed' },
    { name: 'Analyze', href: '/analyze', current: pathname === '/analyze' },
    { name: 'Newsletter', href: '/preferences', current: pathname === '/preferences' },  // Changed from 'Settings'
    { name: 'How It Works', href: '/how-it-works', current: pathname === '/how-it-works' },
]
```

#### 6.3 User Model Update
**Add challenge preference to User model**:
```python
# In models.py - User class
challenge_participation_enabled: bool = Field(default=True)  # Opt-in to weekly challenges
```

### Phase 7: Analytics & Engagement Tracking

#### 7.1 Engagement Metrics
**Key Metrics to Track**:
- Challenge participation rate (users who respond vs users who receive)
- Claim selection distribution (which claims are most popular)
- Agreement level distribution
- Article engagement rates (open/click rates for challenge vs regular articles)
- Challenge completion rate (users who complete all 7 days)
- User feedback on challenge value

#### 7.2 Analytics API Extensions
**New endpoints**:
```python
@router.get("/analytics/challenges")
def get_challenge_analytics(current_user: User = Depends(get_current_user)):
    """Get challenge-specific analytics for current user"""

@router.get("/admin/analytics/challenges")
def get_admin_challenge_analytics(current_user: User = Depends(get_current_user)):
    """Get system-wide challenge analytics (admin only)"""
```

#### 7.3 Dashboard Integration
**User Dashboard Additions**:
- Current challenge status
- Challenge history and progress
- Engagement insights for completed challenges

### Phase 8: Testing & Quality Assurance

#### 8.1 Backend Testing
**Test Coverage**:
```python
# tests/test_challenge_system.py
class TestChallengeClaimGeneration:
    def test_generate_balanced_claims(self)
    def test_controversy_scoring(self)
    def test_political_balance_filtering(self)

class TestChallengeResponseProcessing:
    def test_submit_challenge_response(self)
    def test_duplicate_submission_prevention(self)
    def test_challenge_article_assignment(self)

class TestArticleMatching:
    def test_opposing_viewpoint_matching(self)
    def test_web_search_fallback(self)
    def test_historical_article_fallback(self)
```

#### 8.2 Frontend Testing
**Test Coverage**:
```typescript
// src/app/challenge/__tests__/page.test.tsx
describe('Challenge Form', () => {
    test('renders challenge claims correctly')
    test('validates form submission')
    test('prevents duplicate submissions')
    test('handles API errors gracefully')
})
```

#### 8.3 Integration Testing
**End-to-End Scenarios**:
1. User receives Friday newsletter with challenge
2. User clicks link, submits form response
3. User receives 7 days of challenge articles
4. User engages with challenge articles
5. Analytics capture engagement data

### Phase 9: Deployment & Monitoring

#### 9.1 Deployment Checklist
- Database migrations applied
- New scheduler jobs added
- Newsletter template updated
- API routes registered
- Frontend components deployed
- Analytics tracking configured

#### 9.2 Monitoring
**Key Metrics to Monitor**:
- Challenge generation success rate
- User participation rates
- Article assignment success
- Email delivery rates
- Engagement metrics

## Success Metrics

### Participation Goals
- **60%+** of newsletter users engage with challenges
- **40%+** complete full 7-day challenge sequences
- **1.5x** higher engagement for challenge articles vs regular articles

### Quality Goals
- Balanced political perspective distribution
- High-quality claim generation (controversy score 0.3-0.8)
- Effective article matching (opposition score 0.6+)
- Positive user feedback on challenge value

### Technical Goals
- 99%+ uptime for challenge system
- Sub-second response times for challenge form
- Reliable daily article assignment processing
- Comprehensive analytics and reporting

## Timeline

**Week 1**: Database schema + models + basic claim generation
**Week 2**: Challenge management system + scheduler integration
**Week 3**: Newsletter integration + challenge form
**Week 4**: Article matching algorithm + daily processing
**Week 5**: UI updates + preferences integration
**Week 6**: Analytics + testing + deployment prep

## Risk Mitigation

### Technical Risks
- **Claim Quality**: Implement admin review for high-controversy claims
- **Article Availability**: Multi-tier fallback strategy (database → web → historical)
- **Performance**: Optimize database queries, use caching for claim generation

### User Experience Risks
- **Form Accessibility**: Ensure mobile-friendly design, clear instructions
- **Challenge Fatigue**: Allow opt-out, vary difficulty levels
- **Privacy Concerns**: Clear data usage policies, anonymize analytics

This implementation guide provides comprehensive instructions for building the newsletter challenge system with proper ethical considerations, user controls, and technical robustness.