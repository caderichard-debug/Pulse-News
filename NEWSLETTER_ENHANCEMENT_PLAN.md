# Newsletter Enhancement Plan

**Created**: October 2, 2025
**Goal**: Enhance newsletter with framework mapping, statistics verification, cross-source comparisons, and contextual issue summaries

---

## Current Newsletter Format

The current newsletter includes:
- 5 articles with summaries
- Basic metadata (source, bias, sentiment)
- Key statistics (unverified)
- Framework connections (listed separately at bottom)

## Proposed Enhancements

### 1. **Show Framework Axes Per Article**
Display which frameworks each article relates to directly in the article card, with:
- Framework name
- Position on axis (-10 to +10)
- Visual indicator (color-coded bar)
- Brief explanation of relevance

### 2. **Statistics Verification Architecture**
Add verification system for key statistics:
- Extract statistics from article
- Cross-reference with other sources
- Verify against known data sources (APIs, databases)
- Mark as: Verified ✓, Unverified ?, Disputed ⚠️, False ✗

### 3. **Cross-Source Comparisons**
When multiple sources cover the same story:
- Detect duplicate/similar stories
- Compare how different sources frame the issue
- Show bias differences
- Highlight unique facts from each source

### 4. **Issue Summary (Contextual Dropdown)**
For each article, provide expandable context:
- Background: What led to this?
- Key players: Who's involved?
- Timeline: When did this start?
- Why it matters: Impact and significance
- What's next: Expected developments

---

## Database Schema Changes

### New Tables

#### 1. `statistic_verifications`
```sql
CREATE TABLE statistic_verifications (
    id SERIAL PRIMARY KEY,
    article_id INTEGER REFERENCES articles(id),
    statistic_text TEXT NOT NULL,           -- "50% increase in Q3"
    verification_status VARCHAR(20),         -- verified, unverified, disputed, false
    verification_method VARCHAR(50),         -- cross_reference, api_check, manual
    verified_sources TEXT[],                 -- Array of source URLs
    confidence_score FLOAT,                  -- 0.0 to 1.0
    verified_at TIMESTAMP,
    verified_by VARCHAR(50),                 -- ai, human, api
    notes TEXT
);
```

#### 2. `article_clusters` (for cross-source comparison)
```sql
CREATE TABLE article_clusters (
    id SERIAL PRIMARY KEY,
    cluster_hash VARCHAR(64) UNIQUE,        -- Hash of normalized title/topic
    primary_topic TEXT,                      -- "Student Loan Forgiveness"
    detected_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE article_cluster_members (
    cluster_id INTEGER REFERENCES article_clusters(id),
    article_id INTEGER REFERENCES articles(id),
    similarity_score FLOAT,                  -- How similar to cluster
    PRIMARY KEY (cluster_id, article_id)
);
```

#### 3. `article_context` (issue summaries)
```sql
CREATE TABLE article_context (
    id SERIAL PRIMARY KEY,
    article_id INTEGER REFERENCES articles(id) UNIQUE,
    background TEXT,                         -- "Student loan debt crisis began..."
    key_players TEXT[],                      -- ["Biden", "Supreme Court"]
    timeline JSONB,                          -- [{"date": "2023-06", "event": "..."}]
    significance TEXT,                       -- Why this matters
    next_developments TEXT,                  -- What to expect
    sources_consulted TEXT[],                -- URLs used for context
    generated_at TIMESTAMP DEFAULT NOW(),
    context_quality_score FLOAT
);
```

### Modified Tables

#### Update `article_analysis`
```sql
ALTER TABLE article_analysis
ADD COLUMN stats_verification_status VARCHAR(20) DEFAULT 'unverified',
ADD COLUMN stats_verification_date TIMESTAMP,
ADD COLUMN has_context BOOLEAN DEFAULT FALSE;
```

---

## Implementation Plan

### Phase 1: Database Schema (Day 1)
- [ ] Create migration for new tables
- [ ] Add new columns to existing tables
- [ ] Create SQLModel models for new tables
- [ ] Add relationships to existing models

### Phase 2: Statistics Verification (Day 2)
- [ ] Create `StatisticsVerifier` service
- [ ] Implement cross-reference checking
- [ ] Add confidence scoring algorithm
- [ ] Create API endpoint for manual verification
- [ ] Update AI analyzer to flag statistics for verification

### Phase 3: Article Clustering (Day 3)
- [ ] Create `ArticleClusterer` service
- [ ] Implement similarity detection (title + content)
- [ ] Add clustering job to scheduler
- [ ] Create cross-source comparison view
- [ ] Update newsletter to show related articles

### Phase 4: Context Generation (Day 4)
- [ ] Create `ContextGenerator` service
- [ ] Build prompts for AI context generation
- [ ] Implement timeline extraction
- [ ] Add context to article analysis pipeline
- [ ] Cache context for performance

### Phase 5: Newsletter Template Updates (Day 5)
- [ ] Redesign article card component
- [ ] Add framework axis visualizations
- [ ] Add verification badges for statistics
- [ ] Add expandable context section
- [ ] Add "See how other sources covered this" section
- [ ] Update email CSS for new layout

### Phase 6: Testing & Integration (Day 6)
- [ ] Write tests for new services
- [ ] Update existing tests
- [ ] Test newsletter generation end-to-end
- [ ] Performance testing (ensure email < 500KB)
- [ ] Mobile responsiveness check

---

## Detailed Design Specs

### Article Card Layout (New)

```
┌─────────────────────────────────────────────────────┐
│ 📰 [SOURCE] • [TRUST SCORE] • [DATE]               │
│                                                     │
│ ARTICLE TITLE                                       │
│ by [Author]                                         │
│                                                     │
│ [100-word summary]                                  │
│                                                     │
│ ━━━ Key Statistics ━━━                             │
│ • "50% increase in Q3" ✓ Verified                  │
│ • "2025 deadline" ? Unverified                     │
│                                                     │
│ ━━━ Related Frameworks ━━━                         │
│ 🧠 Individual Liberty ←──────●───→ Collective Good │
│    Position: +6 (leans collective)                 │
│    "Article emphasizes debt relief benefits..."    │
│                                                     │
│ 🧠 Government Power ←───●────────→ Limited Gov     │
│    Position: +4 (moderate expansion)               │
│                                                     │
│ ━━━ Cross-Source Coverage ━━━                      │
│ ℹ️ 3 other sources covered this story             │
│ [Show comparison ▼]                                │
│                                                     │
│ ━━━ Background & Context ━━━                       │
│ [Why this matters ▼]                               │
│                                                     │
│ [Read Full Article →]                              │
└─────────────────────────────────────────────────────┘
```

### Verification Badge System

- ✓ **Verified** (Green) - Confirmed by 2+ sources or authoritative API
- ? **Unverified** (Yellow) - Not yet checked or insufficient data
- ⚠️ **Disputed** (Orange) - Conflicting information found
- ✗ **False** (Red) - Proven incorrect

### Framework Axis Visualization

```
Individual Liberty ←──────●───→ Collective Welfare
Position: +6/10 (leans right)

Visual: ASCII progress bar with position marker
Color coding:
  -10 to -4: Blue (strong left)
  -3 to +3: Gray (neutral)
  +4 to +10: Orange (strong right)
```

### Context Dropdown Content

```
📖 Background
Student loan debt in the US exceeds $1.7 trillion, affecting
43 million borrowers. Biden campaigned on forgiveness...

👥 Key Players
• President Biden - Announced plan
• Supreme Court - Ruled against 2023 plan
• Republicans - Opposed broader relief

⏱️ Timeline
• 2020: Biden campaigns on relief
• 2022: First plan announced
• 2023: Supreme Court blocks
• 2024: New IDR plan introduced

💡 Why This Matters
This affects voting patterns among young adults and has
major economic implications...

🔮 What's Next
Further legal challenges expected. Watch for Congressional
action in Q4 2025...
```

---

## Technical Architecture

### Service Layer

```python
app/services/
├── statistics_verifier.py
│   ├── extract_statistics()
│   ├── verify_statistic()
│   ├── cross_reference_sources()
│   └── calculate_confidence()
│
├── article_clusterer.py
│   ├── detect_similar_articles()
│   ├── create_cluster()
│   ├── compare_source_framing()
│   └── generate_comparison_view()
│
└── context_generator.py
    ├── generate_context()
    ├── extract_timeline()
    ├── identify_key_players()
    └── predict_developments()
```

### AI Prompts

#### Statistics Verification Prompt
```
Analyze this article and extract all numerical claims:
[Article text]

For each statistic, provide:
1. Exact quote
2. Context needed to verify
3. Likely sources to check
4. Confidence in accuracy (0-1)
```

#### Context Generation Prompt
```
Generate comprehensive context for this news article:
[Article summary]

Provide:
1. Background (3-4 sentences on what led to this)
2. Key players (list main people/organizations)
3. Timeline (5-7 major events leading here)
4. Significance (why this matters, 2-3 sentences)
5. Expected developments (what might happen next)
```

#### Cross-Source Comparison Prompt
```
Compare how these sources covered the same story:
Source 1 (Reuters): [text]
Source 2 (NPR): [text]
Source 3 (Politico): [text]

Identify:
1. Facts unique to each source
2. Framing differences (tone, emphasis)
3. Information gaps in each
4. Bias indicators
```

---

## API Changes

### New Endpoints

```
GET  /api/articles/{id}/context
GET  /api/articles/{id}/verifications
GET  /api/articles/{id}/cluster
POST /api/admin/verify-statistic
GET  /api/clusters/{id}/comparison
```

---

## Configuration Updates

Add to `config.py`:

```python
# Statistics Verification
enable_stat_verification: bool = True
verification_confidence_threshold: float = 0.7
max_verification_sources: int = 5

# Article Clustering
enable_clustering: bool = True
similarity_threshold: float = 0.8
min_cluster_size: int = 2

# Context Generation
enable_context_generation: bool = True
context_max_tokens: int = 1000
```

---

## Testing Strategy

### Unit Tests
- Statistics extraction accuracy
- Clustering similarity algorithm
- Context generation quality
- Verification confidence scoring

### Integration Tests
- Full newsletter generation with all features
- Database relationships
- AI service calls

### Performance Tests
- Newsletter generation time (target: <30s)
- Email size (target: <500KB)
- Database query optimization

---

## Rollout Plan

### Week 1: Core Infrastructure
- Database migrations
- New models and relationships
- Basic service implementations

### Week 2: AI Integration
- Statistics verification prompts
- Context generation prompts
- Clustering algorithms

### Week 3: Newsletter UI
- Template redesign
- Visual components
- Mobile optimization

### Week 4: Testing & Launch
- Comprehensive testing
- Beta user feedback
- Full rollout

---

## Success Metrics

- **Engagement**: Click-through rate increase by 30%
- **Trust**: User satisfaction with verification system > 4.5/5
- **Comprehension**: Users report better understanding of issues
- **Technical**: Newsletter generation time < 30 seconds
- **Quality**: Context accuracy validated by spot checks

---

## Future Enhancements (Post-MVP)

1. **Interactive Framework Explorer** - Let users explore articles by framework
2. **Fact-Check Integration** - API integration with FactCheck.org, Snopes
3. **Historical Context** - Link to related past articles
4. **Expert Commentary** - Curated expert opinions on complex issues
5. **User Feedback Loop** - Let users report incorrect verifications

---

## Risk Mitigation

### Technical Risks
- **AI Hallucination**: Implement confidence scoring and human review flags
- **Performance**: Cache context, use background jobs
- **Email Size**: Implement lazy loading for expandable sections

### Content Risks
- **Verification Errors**: Show confidence scores, allow user reports
- **Bias in Context**: Use multiple sources, clearly label AI-generated content
- **Privacy**: Don't track which dropdown users open

### Operational Risks
- **Cost**: Monitor AI API usage, set daily limits
- **Complexity**: Phase rollout, feature flags for gradual deployment

---

## Estimated Effort

- **Database & Models**: 8 hours
- **Statistics Verification**: 16 hours
- **Article Clustering**: 12 hours
- **Context Generation**: 16 hours
- **Newsletter Template**: 12 hours
- **Testing**: 16 hours
- **Documentation**: 4 hours

**Total**: ~84 hours (~2 weeks of focused development)

---

## Next Steps

1. ✅ Review and approve plan
2. Create feature branch: `feature/newsletter-enhancements`
3. Start with Phase 1: Database schema
4. Implement incrementally with tests
5. Beta test with small user group
6. Full rollout

---

**Questions? Concerns? Ready to proceed?**
