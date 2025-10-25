# Statistics Verification V2 Architecture Plan

## Overview

Replace the current cross-reference verification system with a source-tracing and fact-checking architecture that:
1. Traces statistics to their original source within the article
2. Rates source credibility
3. Integrates with external fact-checking APIs
4. Displays comprehensive verification badges in newsletters

---

## 1. Database Schema Changes

### 1.1 Update `StatisticVerification` Model

```python
class StatisticVerification(SQLModel, table=True):
    __tablename__ = "statistic_verifications"

    # Existing fields
    id: Optional[int] = Field(default=None, primary_key=True)
    article_id: int = Field(foreign_key="articles.id", index=True)
    statistic_text: str = Field(max_length=500)
    context: Optional[str] = Field(default=None, max_length=1000)
    verification_status: VerificationStatus = Field(default=VerificationStatus.UNVERIFIED)
    verification_method: Optional[VerificationMethod] = Field(default=None)
    confidence_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    verified_at: Optional[datetime] = Field(default=None)
    last_checked: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # NEW FIELDS - Source Tracing
    source_url: Optional[str] = Field(default=None, max_length=500)
    source_name: Optional[str] = Field(default=None, max_length=200)
    source_excerpt: Optional[str] = Field(default=None, max_length=1000)  # Quote from source
    source_credibility_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)

    # NEW FIELDS - Fact-Checking
    fact_check_status: Optional[str] = Field(default=None)  # "verified", "false", "mixed", "unverifiable"
    fact_check_source: Optional[str] = Field(default=None)  # "snopes", "factcheck.org", etc.
    fact_check_url: Optional[str] = Field(default=None, max_length=500)
    fact_check_details: Optional[str] = Field(default=None, max_length=2000)

    # REMOVED FIELD (no longer needed)
    # verified_sources: Optional[str] = Field(default=None)  # Was for cross-reference URLs
```

### 1.2 New `SourceCredibilityRating` Table

Cache credibility scores for domains to avoid re-computation.

```python
class SourceCredibilityRating(SQLModel, table=True):
    __tablename__ = "source_credibility_ratings"

    id: Optional[int] = Field(default=None, primary_key=True)
    domain: str = Field(unique=True, index=True, max_length=200)
    credibility_score: float = Field(ge=0.0, le=1.0)

    # Credibility factors
    is_academic: bool = Field(default=False)
    is_government: bool = Field(default=False)
    is_news_organization: bool = Field(default=False)
    is_think_tank: bool = Field(default=False)

    # Metadata
    rating_method: str = Field(max_length=100)  # "manual", "ai", "mbfc_api", etc.
    notes: Optional[str] = Field(default=None, max_length=1000)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### 1.3 Alembic Migration Script

```python
"""add source tracing and fact checking to statistics

Revision ID: 003
Revises: 002
"""

def upgrade():
    # Add new columns to statistic_verifications
    op.add_column('statistic_verifications', sa.Column('source_url', sa.String(length=500)))
    op.add_column('statistic_verifications', sa.Column('source_name', sa.String(length=200)))
    op.add_column('statistic_verifications', sa.Column('source_excerpt', sa.String(length=1000)))
    op.add_column('statistic_verifications', sa.Column('source_credibility_score', sa.Float()))
    op.add_column('statistic_verifications', sa.Column('fact_check_status', sa.String(length=50)))
    op.add_column('statistic_verifications', sa.Column('fact_check_source', sa.String(length=100)))
    op.add_column('statistic_verifications', sa.Column('fact_check_url', sa.String(length=500)))
    op.add_column('statistic_verifications', sa.Column('fact_check_details', sa.String(length=2000)))

    # Create source_credibility_ratings table
    op.create_table(
        'source_credibility_ratings',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('domain', sa.String(200), unique=True, index=True),
        sa.Column('credibility_score', sa.Float()),
        # ... all other columns
    )

    # Drop old verified_sources column (was JSON array of cross-reference URLs)
    op.drop_column('statistic_verifications', 'verified_sources')

def downgrade():
    # Reverse changes
    op.add_column('statistic_verifications', sa.Column('verified_sources', sa.String()))
    op.drop_table('source_credibility_ratings')
    # Drop new columns...
```

---

## 2. Service Architecture

### 2.1 New Service: `SourceTracer`

**Purpose:** Extract and identify original sources from article content.

**Location:** `backend/app/services/source_tracer.py`

**Key Methods:**

```python
class SourceTracer:
    def trace_statistic_source(
        self,
        statistic_text: str,
        article_content: str,
        article_url: str,
        session: Session
    ) -> Optional[Dict]:
        """
        Use AI to find the original source of a statistic within an article.

        Returns:
        {
            "source_url": "https://example.com/study",
            "source_name": "Johns Hopkins University",
            "source_excerpt": "The study found that 50% of...",
            "extraction_method": "ai_parsing" | "citation_link" | "embedded_url"
        }
        """

        # Step 1: Check if article has embedded links near the statistic
        links_near_stat = self._extract_nearby_links(statistic_text, article_content)

        # Step 2: Use AI to identify source mentions in text
        ai_sources = self._ai_extract_source(statistic_text, article_content)

        # Step 3: Cross-reference with article metadata
        # Step 4: Validate URLs are reachable
        # Step 5: Return best match
```

**AI Prompt for Source Extraction:**

```python
TRACE_SOURCE_PROMPT = """Given this article content and a specific statistic, identify the original source.

Article URL: {article_url}
Statistic: "{statistic_text}"

Article Content:
{article_content}

Identify:
1. source_url: URL of the original source (if mentioned)
2. source_name: Name of organization/publication that produced the statistic
3. source_excerpt: The exact text from the article that mentions the source
4. confidence: Your confidence in this identification (0.0 to 1.0)

Return JSON:
{{
  "source_url": "https://...",
  "source_name": "Organization Name",
  "source_excerpt": "According to a Johns Hopkins study...",
  "confidence": 0.85
}}

If no source is identifiable, return null for the fields.
"""
```

### 2.2 New Service: `CredibilityRater`

**Purpose:** Rate the credibility of sources using domain reputation and heuristics.

**Location:** `backend/app/services/credibility_rater.py`

**Key Methods:**

```python
class CredibilityRater:
    def rate_source_credibility(
        self,
        source_url: str,
        source_name: str,
        session: Session
    ) -> float:
        """
        Rate source credibility (0.0 to 1.0).

        Uses:
        1. Cached ratings from source_credibility_ratings table
        2. Domain heuristics (.gov, .edu, etc.)
        3. Optional: Media Bias/Fact Check API
        4. AI-based assessment
        """

        domain = self._extract_domain(source_url)

        # Check cache first
        cached = session.exec(
            select(SourceCredibilityRating)
            .where(SourceCredibilityRating.domain == domain)
        ).first()

        if cached and self._is_cache_fresh(cached):
            return cached.credibility_score

        # Calculate new score
        score = self._calculate_credibility_score(source_url, source_name)

        # Cache it
        self._cache_credibility_rating(domain, score, session)

        return score

    def _calculate_credibility_score(self, source_url: str, source_name: str) -> float:
        """
        Credibility scoring rubric:

        Base score: 0.5

        Domain TLD:
        +0.3 for .gov
        +0.3 for .edu
        +0.2 for .org (if academic/research)
        +0.1 for established .com news (nytimes.com, washingtonpost.com)
        -0.2 for unknown domains

        Organization type (from name):
        +0.2 for "University", "Institute", "Laboratory"
        +0.2 for government agencies (CDC, FDA, etc.)
        +0.1 for established news organizations
        -0.1 for personal blogs, social media

        Max score: 1.0
        Min score: 0.0
        """
```

**Credibility Tier System:**

```python
CREDIBILITY_TIERS = {
    "very_high": (0.8, 1.0),   # Government, academic, peer-reviewed
    "high": (0.6, 0.8),         # Established news, research institutions
    "medium": (0.4, 0.6),       # Trade publications, specialized press
    "low": (0.2, 0.4),          # Blogs, opinion sites
    "very_low": (0.0, 0.2)      # Unverified, personal sites
}
```

### 2.3 New Service: `FactCheckIntegrator`

**Purpose:** Query external fact-checking APIs to verify statistics.

**Location:** `backend/app/services/fact_check_integrator.py`

**External APIs to Integrate:**

1. **ClaimBuster API** (Free tier available)
   - Endpoint: `https://idir.uta.edu/claimbuster/api/`
   - Checks if a statement is fact-checkable (score 0-1)

2. **Google Fact Check Tools API** (Free)
   - Endpoint: `https://factchecktools.googleapis.com/v1alpha1/claims:search`
   - Aggregates fact-checks from multiple sources

3. **PolitiFact API** (Custom scraping if no API)
   - Search for matching claims
   - Return truth rating (True, Mostly True, Half True, False, etc.)

4. **Snopes** (Custom scraping - no official API)
   - Search for matching claims
   - Return rating (True, False, Mixture, Unproven)

5. **FactCheck.org** (Custom scraping)
   - Search for matching claims

**Key Methods:**

```python
class FactCheckIntegrator:
    def verify_statistic(
        self,
        statistic_text: str,
        source_url: Optional[str] = None,
        session: Session = None
    ) -> Optional[Dict]:
        """
        Check statistic against external fact-checking services.

        Returns:
        {
            "fact_check_status": "verified" | "false" | "mixed" | "unverifiable",
            "fact_check_source": "google_fact_check",
            "fact_check_url": "https://...",
            "fact_check_details": "Full explanation...",
            "confidence": 0.85
        }
        """

        # Try multiple services in order of preference
        results = []

        # 1. Google Fact Check Tools (aggregates multiple sources)
        google_result = self._check_google_fact_check(statistic_text)
        if google_result:
            results.append(google_result)

        # 2. ClaimBuster (fact-checkability score)
        claimbuster_result = self._check_claimbuster(statistic_text)
        if claimbuster_result and claimbuster_result["score"] > 0.5:
            results.append(claimbuster_result)

        # 3. PolitiFact (web scraping)
        politifact_result = self._check_politifact(statistic_text)
        if politifact_result:
            results.append(politifact_result)

        # Return best match
        return self._select_best_fact_check(results)

    def _check_google_fact_check(self, claim: str) -> Optional[Dict]:
        """Query Google Fact Check Tools API"""
        url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
        params = {
            "query": claim,
            "key": settings.google_api_key
        }
        # ... make request, parse response

    def _check_claimbuster(self, claim: str) -> Optional[Dict]:
        """Query ClaimBuster API for fact-checkability score"""
        # ...

    def _check_politifact(self, claim: str) -> Optional[Dict]:
        """Search PolitiFact for matching claims"""
        # Custom web scraping with BeautifulSoup
        # ...
```

**API Configuration (add to settings):**

```python
class Settings(BaseSettings):
    # ... existing fields

    # Fact-checking APIs
    google_fact_check_api_key: Optional[str] = Field(default=None, env="GOOGLE_FACT_CHECK_API_KEY")
    claimbuster_api_key: Optional[str] = Field(default=None, env="CLAIMBUSTER_API_KEY")
```

### 2.4 Update `StatisticsVerifier` Service

Orchestrate the three-stage verification pipeline.

**New Architecture:**

```python
def verify_statistic_with_source_tracing(
    verification: StatisticVerification,
    article: Article,
    session: Session
) -> bool:
    """
    Three-stage verification pipeline:
    1. Trace source
    2. Rate credibility
    3. Fact-check
    """

    # Stage 1: Trace source
    source_tracer = SourceTracer()
    source_info = source_tracer.trace_statistic_source(
        statistic_text=verification.statistic_text,
        article_content=article.full_text or article.summary,
        article_url=article.url,
        session=session
    )

    if source_info:
        verification.source_url = source_info["source_url"]
        verification.source_name = source_info["source_name"]
        verification.source_excerpt = source_info["source_excerpt"]

        # Stage 2: Rate source credibility
        credibility_rater = CredibilityRater()
        verification.source_credibility_score = credibility_rater.rate_source_credibility(
            source_url=source_info["source_url"],
            source_name=source_info["source_name"],
            session=session
        )

    # Stage 3: Fact-check (regardless of whether we found a source)
    fact_checker = FactCheckIntegrator()
    fact_check_result = fact_checker.verify_statistic(
        statistic_text=verification.statistic_text,
        source_url=verification.source_url,
        session=session
    )

    if fact_check_result:
        verification.fact_check_status = fact_check_result["fact_check_status"]
        verification.fact_check_source = fact_check_result["fact_check_source"]
        verification.fact_check_url = fact_check_result["fact_check_url"]
        verification.fact_check_details = fact_check_result["fact_check_details"]

    # Calculate final verification status
    verification.verification_status = _determine_final_status(verification)
    verification.confidence_score = _calculate_final_confidence(verification)
    verification.verified_at = datetime.utcnow()

    session.commit()
    return True

def _determine_final_status(verification: StatisticVerification) -> VerificationStatus:
    """
    Determine final status based on fact-check and source credibility.

    Logic:
    - If fact_check_status == "false" -> DISPUTED or FALSE
    - If fact_check_status == "verified" AND source_credibility >= 0.6 -> VERIFIED
    - If source_credibility >= 0.7 AND no contradicting fact-check -> VERIFIED
    - Otherwise -> UNVERIFIED
    """
    if verification.fact_check_status == "false":
        return VerificationStatus.FALSE

    if verification.fact_check_status == "verified":
        if verification.source_credibility_score and verification.source_credibility_score >= 0.6:
            return VerificationStatus.VERIFIED

    if verification.source_credibility_score and verification.source_credibility_score >= 0.7:
        return VerificationStatus.VERIFIED

    if verification.fact_check_status == "mixed":
        return VerificationStatus.DISPUTED

    return VerificationStatus.UNVERIFIED

def _calculate_final_confidence(verification: StatisticVerification) -> float:
    """
    Calculate overall confidence score (0.0 to 1.0).

    Factors:
    - Source credibility (40% weight)
    - Fact-check confidence (40% weight)
    - Source traceability (20% weight)
    """
    score = 0.0

    if verification.source_credibility_score:
        score += verification.source_credibility_score * 0.4

    if verification.fact_check_status:
        fact_check_confidence = {
            "verified": 1.0,
            "false": 0.0,
            "mixed": 0.5,
            "unverifiable": 0.3
        }.get(verification.fact_check_status, 0.5)
        score += fact_check_confidence * 0.4

    if verification.source_url:
        score += 0.2  # Bonus for having traceable source

    return min(1.0, score)
```

---

## 3. Newsletter Template Updates

### 3.1 New Badge Design (Email-Compatible)

**Badge Components:**
1. **Verification Status Icon:** ✓ (verified) / ⏳ (pending) / ⚠️ (disputed) / ❌ (false)
2. **Source Credibility Stars:** ⭐⭐⭐⭐⭐ (1-5 stars)
3. **Source Name & Link:** "Johns Hopkins University"
4. **Confidence Percentage:** "85% confidence"

**HTML Template (inline styles for email):**

```html
<!-- Statistics with V2 badges -->
{% if article.statistics %}
<div style="margin-top: 15px; padding: 12px; background-color: #FFF9C4; border-left: 4px solid #FBC02D;">
    <div style="font-weight: 600; color: #F57F17; margin-bottom: 8px;">📊 Key Statistics</div>

    {% for stat in article.statistics %}
    <div style="margin-bottom: 10px; padding: 8px; background-color: #FFFDE7; border-radius: 4px;">
        <!-- Statistic text -->
        <div style="font-size: 13px; color: #333; margin-bottom: 6px;">
            {{ stat.statistic_text }}
        </div>

        <!-- Verification badge -->
        <table cellpadding="0" cellspacing="0" border="0" width="100%" style="font-size: 11px;">
            <tr>
                <!-- Status icon -->
                <td width="30" style="vertical-align: top;">
                    {% if stat.verification_status == 'verified' %}
                        <span style="color: #2E7D32; font-size: 16px;">✓</span>
                    {% elif stat.verification_status == 'disputed' %}
                        <span style="color: #F57C00; font-size: 16px;">⚠️</span>
                    {% elif stat.verification_status == 'false' %}
                        <span style="color: #C62828; font-size: 16px;">❌</span>
                    {% else %}
                        <span style="color: #757575; font-size: 16px;">⏳</span>
                    {% endif %}
                </td>

                <!-- Source credibility stars -->
                <td width="100" style="vertical-align: top;">
                    {% if stat.source_credibility_score %}
                        {% set stars = (stat.source_credibility_score * 5) | round(0, 'floor') | int %}
                        <span style="color: #FFB300;">
                            {{ '⭐' * stars }}{{ '☆' * (5 - stars) }}
                        </span>
                    {% endif %}
                </td>

                <!-- Source name with link -->
                <td style="vertical-align: top;">
                    {% if stat.source_name %}
                        <span style="color: #1976D2;">
                            {% if stat.source_url %}
                                <a href="{{ stat.source_url }}" style="color: #1976D2; text-decoration: none;">
                                    {{ stat.source_name }}
                                </a>
                            {% else %}
                                {{ stat.source_name }}
                            {% endif %}
                        </span>
                    {% else %}
                        <span style="color: #9E9E9E; font-style: italic;">Source not traced</span>
                    {% endif %}
                </td>

                <!-- Confidence percentage -->
                <td width="80" align="right" style="vertical-align: top;">
                    {% if stat.confidence_score %}
                        <span style="color: #424242; font-weight: 600;">
                            {{ (stat.confidence_score * 100) | round(0) | int }}%
                        </span>
                    {% endif %}
                </td>
            </tr>
        </table>

        <!-- Fact-check details (if available) -->
        {% if stat.fact_check_details %}
        <div style="margin-top: 6px; padding: 6px; background-color: #E3F2FD; border-left: 2px solid #1976D2; font-size: 11px; color: #0D47A1;">
            <strong>Fact-check:</strong> {{ stat.fact_check_details[:200] }}
            {% if stat.fact_check_url %}
                <a href="{{ stat.fact_check_url }}" style="color: #1976D2;">Read more</a>
            {% endif %}
        </div>
        {% endif %}
    </div>
    {% endfor %}
</div>
{% endif %}
```

### 3.2 Update `newsletter_service.py`

Add new fields to statistics query:

```python
# Get statistics for this article
statistics = session.exec(
    select(StatisticVerification)
    .where(StatisticVerification.article_id == article.id)
    .order_by(StatisticVerification.confidence_score.desc())
    .limit(5)
).all()

statistics_for_article = []
for stat in statistics:
    statistics_for_article.append({
        "statistic_text": stat.statistic_text,
        "context": stat.context,
        "verification_status": stat.verification_status.value,

        # V2 fields
        "source_name": stat.source_name,
        "source_url": stat.source_url,
        "source_credibility_score": stat.source_credibility_score,
        "confidence_score": stat.confidence_score,
        "fact_check_details": stat.fact_check_details,
        "fact_check_url": stat.fact_check_url
    })
```

---

## 4. Scheduler Integration

Update the statistics verification job to use the new three-stage pipeline:

```python
# backend/app/jobs/tasks.py

def statistics_verification_job(session: Session = None):
    """Job 6: Extract and verify statistics using V2 architecture."""
    from app.services.statistics_verifier import process_pending_verifications_v2

    if session is None:
        with Session(engine) as session:
            stats = process_pending_verifications_v2(session, limit=10)
    else:
        stats = process_pending_verifications_v2(session, limit=10)

    logger.info(
        f"Statistics verification V2 job completed: "
        f"{stats['articles_processed']} articles, "
        f"{stats['stats_extracted']} statistics extracted, "
        f"{stats['sources_traced']} sources traced, "
        f"{stats['stats_verified']} verified"
    )

    return {
        "success": True,
        "articles_processed": stats["articles_processed"],
        "statistics_extracted": stats["stats_extracted"],
        "sources_traced": stats["sources_traced"],
        "statistics_verified": stats["stats_verified"]
    }
```

---

## 5. Implementation Phases

### Phase 1: Database Schema & Migration (1-2 hours)
1. Update `models.py` with new fields
2. Create `SourceCredibilityRating` model
3. Generate Alembic migration
4. Test migration on dev database
5. Seed initial credibility ratings (known domains)

### Phase 2: Source Tracing Service (3-4 hours)
1. Implement `SourceTracer` class
2. Create AI prompt for source extraction
3. Add link extraction logic
4. Write unit tests
5. Test with real articles

### Phase 3: Credibility Rating Service (2-3 hours)
1. Implement `CredibilityRater` class
2. Build domain heuristics
3. Create credibility cache system
4. Write unit tests
5. Seed database with known sources

### Phase 4: Fact-Check Integration (4-6 hours)
1. Research and test available APIs
2. Implement `FactCheckIntegrator` class
3. Add Google Fact Check Tools integration
4. Add ClaimBuster integration
5. Add web scraping for PolitiFact/Snopes (if needed)
6. Write integration tests
7. Add rate limiting and caching

### Phase 5: Update Statistics Verifier (2-3 hours)
1. Update `verify_statistic_with_source_tracing()` method
2. Update batch processing logic
3. Update status determination logic
4. Update confidence calculation
5. Write comprehensive tests

### Phase 6: Newsletter Template Updates (2-3 hours)
1. Design badge layout (email-compatible)
2. Update `newsletter.html` template
3. Update `newsletter_service.py` to pass new fields
4. Test email rendering in multiple clients
5. Fine-tune styling

### Phase 7: Testing & Integration (2-3 hours)
1. Run full test suite
2. Test with real articles end-to-end
3. Send test newsletters
4. Monitor API rate limits
5. Optimize performance

### Phase 8: Migration & Deployment (1-2 hours)
1. Run migration on production database
2. Re-process existing statistics (optional)
3. Monitor scheduler jobs
4. Document new architecture

**Total Estimated Time: 17-26 hours**

---

## 6. API Rate Limits & Caching Strategy

### Google Fact Check Tools API
- **Free tier:** 10,000 requests/day
- **Cache strategy:** Cache results by claim text (30 days)
- **Fallback:** Skip if quota exceeded

### ClaimBuster API
- **Free tier:** 100 requests/day
- **Cache strategy:** Cache claim scores (60 days)
- **Fallback:** Use credibility heuristics only

### Web Scraping (PolitiFact, Snopes)
- **Rate limit:** 1 request/second per domain
- **Cache strategy:** Cache results by claim text (60 days)
- **Fallback:** Mark as "unverifiable"

### Caching Implementation

```python
class FactCheckCache(SQLModel, table=True):
    __tablename__ = "fact_check_cache"

    id: Optional[int] = Field(default=None, primary_key=True)
    claim_hash: str = Field(unique=True, index=True)  # SHA256 of normalized claim
    fact_check_status: str
    fact_check_source: str
    fact_check_url: Optional[str]
    fact_check_details: str
    cached_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime  # 30-60 days from cached_at
```

---

## 7. Testing Strategy

### Unit Tests
- `test_source_tracer.py` - Source extraction logic
- `test_credibility_rater.py` - Credibility scoring
- `test_fact_check_integrator.py` - API integration (mocked)

### Integration Tests
- `test_statistics_verifier_v2.py` - Full pipeline with real database
- `test_newsletter_statistics_badges.py` - Template rendering

### End-to-End Tests
- Manually trigger verification job
- Send test newsletter
- Verify badges display correctly

---

## 8. Configuration & Environment Variables

Add to `.env`:

```bash
# Fact-checking APIs
GOOGLE_FACT_CHECK_API_KEY=your_key_here
CLAIMBUSTER_API_KEY=your_key_here

# Optional: Media Bias/Fact Check API (if we integrate it)
MBFC_API_KEY=your_key_here
```

Add to `backend/app/config.py`:

```python
class Settings(BaseSettings):
    # ... existing fields

    # Fact-checking APIs
    google_fact_check_api_key: Optional[str] = Field(default=None, env="GOOGLE_FACT_CHECK_API_KEY")
    claimbuster_api_key: Optional[str] = Field(default=None, env="CLAIMBUSTER_API_KEY")
    mbfc_api_key: Optional[str] = Field(default=None, env="MBFC_API_KEY")
```

---

## 9. Success Metrics

### Verification Coverage
- **Target:** 70%+ of statistics have a traced source
- **Target:** 50%+ of statistics verified via fact-checking APIs
- **Target:** 90%+ of statistics have a credibility score

### Confidence Scores
- **Target:** Average confidence score >= 0.65
- **Target:** 30%+ of statistics with confidence >= 0.8

### Newsletter Engagement
- **Target:** Improved click-through rate on source links
- **Target:** Reduced complaints about misinformation

---

## 10. Risks & Mitigation

### Risk 1: API Rate Limits Exceeded
**Mitigation:**
- Implement aggressive caching (30-60 day TTL)
- Graceful degradation (skip fact-checking if quota exceeded)
- Queue system for delayed verification

### Risk 2: Low Source Traceability
**Mitigation:**
- Improve AI prompts for source extraction
- Add fallback to article metadata (author, publication date)
- Accept "source not traced" as valid state

### Risk 3: False Positives in Fact-Checking
**Mitigation:**
- Use multiple fact-checking services
- Weight credibility scores conservatively
- Allow manual override in admin interface

### Risk 4: Slow Verification Pipeline
**Mitigation:**
- Run verification asynchronously in background
- Batch API calls where possible
- Cache all external API results

---

## 11. Future Enhancements (Post-V2)

1. **User Feedback Loop:** Allow users to flag incorrect verifications
2. **Manual Review Interface:** Admin panel for reviewing disputed statistics
3. **Historical Tracking:** Track changes in verification status over time
4. **Advanced NLP:** Use NER models to improve source extraction
5. **Media Bias Integration:** Rate political bias of sources (MBFC API)
6. **Citation Graph:** Build network of source citations across articles

---

## Summary

This V2 architecture replaces cross-reference verification with a more robust three-stage pipeline:

1. **Source Tracing:** AI-powered extraction of original sources from articles
2. **Credibility Rating:** Automated scoring based on domain reputation
3. **Fact-Checking:** Integration with external APIs (Google, ClaimBuster, PolitiFact)

The result is a comprehensive verification system that provides users with:
- ✓ Verification status badges
- ⭐ Source credibility ratings
- 🔗 Traceable sources
- 📊 Confidence percentages

This approach is more scalable and doesn't require a large article corpus to be effective.
