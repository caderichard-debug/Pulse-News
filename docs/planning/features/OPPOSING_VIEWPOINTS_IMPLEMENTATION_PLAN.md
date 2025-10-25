# Opposing Viewpoints Feature Implementation Plan

**Status**: 📋 Planning Phase
**Created**: 2025-01-20
**Phase**: New Feature Development
**Estimated Time**: 3-4 weeks

---

## 🎯 Feature Overview

The Opposing Viewpoints feature helps users understand how different news sources cover the same story from different angles by:

- **Source Diversity**: Same story from sources with different biases
- **Framework Opposition**: Articles taking opposite positions on ethical frameworks
- **Sentiment Contrast**: Articles with strongly different emotional tones
- **Timeline Perspective**: How coverage evolved over time

**Location**: Integrated into article detail page (`/article/[id]/`)
**UI Pattern**: Expandable section with card-based layout

---

## 🏗️ Architecture Overview

This feature builds on existing Pulse capabilities:

- **Article Clustering** (`article_clusterer.py`) - Groups similar articles
- **Sentiment Analysis** (`ai_analyzer.py`) - Detects emotional tone
- **Framework Mapping** (`framework_generator.py`) - Positions on ethical spectra
- **Source Bias Tracking** (Source model) - Organizational bias labels

### New Components

1. **Database Table**: `ViewpointRelationship` - Stores opposition relationships
2. **Service**: `ViewpointAnalyzer` - Core logic for finding oppositions
3. **API Endpoint**: `GET /articles/{id}/opposing-viewpoints`
4. **Frontend Component**: `OpposingViewpoints.tsx` - UI component

---

## 📋 Implementation Steps

### Phase 1: Database & Backend Foundation

#### ✅ Step 1.1: Database Schema
**File**: `backend/app/models.py` (add at end)

```python
class ViewpointRelationship(SQLModel, table=True):
    __tablename__ = "viewpoint_relationships"

    id: Optional[int] = Field(default=None, primary_key=True)
    primary_article_id: int = Field(foreign_key="articles.id")
    opposing_article_id: int = Field(foreign_key="articles.id")

    # Relationship type and strength
    relationship_type: str = Field(max_length=50)  # "source_bias", "framework_opposition", "sentiment_contrast", "temporal_evolution"
    opposition_strength: float = Field(ge=0.0, le=1.0)  # How different they are

    # AI-generated explanation
    ai_explanation: Optional[str] = Field(default=None, max_length=500)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)

    __table_args__ = (
        Index("idx_primary_article", "primary_article_id"),
        Index("idx_opposing_article", "opposing_article_id"),
        Index("idx_relationship_type", "relationship_type"),
    )
```

**Commands**:
```bash
# Create migration
docker-compose exec backend aleambic revision --autogenerate -m "add_viewpoint_relationships_table"

# Apply migration
docker-compose exec backend alembic upgrade head

# Sync to local (CRITICAL!)
./scripts/sync-local-container.sh
```

#### ✅ Step 1.2: Core Service Implementation
**File**: `backend/app/services/viewpoint_analyzer.py`

- Implement `ViewpointAnalyzer` class with methods:
  - `find_opposing_viewpoints()` - Main entry point
  - `_find_cluster_bias_oppositions()` - Same story, different source bias
  - `_find_framework_oppositions()` - Opposite framework positions
  - `_find_sentiment_contrasts()` - Different emotional tones
  - `_find_temporal_evolution()` - Timeline coverage evolution
  - Helper methods for scoring and ranking

#### ✅ Step 1.3: OpenAI Client Extension
**File**: `backend/app/utils/openai_client.py`

Add method:
```python
def generate_viewpoint_explanation(
    self,
    primary_title: str,
    primary_summary: str,
    primary_sentiment: float,
    opposing_title: str,
    opposing_summary: str,
    opposing_sentiment: float,
    relationship_type: str
) -> str:
```

#### ✅ Step 1.4: API Endpoint
**File**: `backend/app/routes/articles.py`

Add response models and endpoint:
```python
@router.get("/{article_id}/opposing-viewpoints", response_model=OpposingViewpointsResponse)
async def get_opposing_viewpoints(
    article_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    max_results: int = 5
):
```

#### ✅ Step 1.5: Backend Testing
**File**: `backend/tests/test_viewpoint_analyzer.py`

Test cases:
- Source bias opposition detection
- Framework opposition detection
- Sentiment contrast detection
- Temporal evolution detection
- Ranking and deduplication
- Edge cases (no oppositions, single article, etc.)

**Commands**:
```bash
docker-compose exec backend pytest tests/test_viewpoint_analyzer.py -v
```

---

### Phase 2: Frontend Implementation

#### ✅ Step 2.1: UI Component
**File**: `frontend/src/components/OpposingViewpoints.tsx`

Features:
- Collapsible section with "Explore Different Perspectives" CTA
- Card-based layout for each opposing viewpoint
- Visual indicators for relationship type and opposition strength
- AI-generated explanations
- Direct links to opposing articles
- Dark mode support using semantic classes

#### ✅ Step 2.2: API Client Integration
**File**: `frontend/src/lib/api.ts`

Add method:
```typescript
async getOpposingViewpoints(articleId: number, maxResults: number = 5) {
  const response = await this.authenticatedRequest(`/articles/${articleId}/opposing-viewpoints?max_results=${maxResults}`)
  return response
}
```

#### ✅ Step 2.3: Article Detail Integration
**File**: `frontend/src/app/article/[id]/page.tsx`

Import and place component:
```tsx
import { OpposingViewpoints } from '@/components/OpposingViewpoints'

// Add after main article content, before related articles
<OpposingViewpoints articleId={article.id} />
```

#### ✅ Step 2.4: Frontend Testing
**Files**:
- `frontend/src/components/__tests__/OpposingViewpoints.test.tsx`
- Update existing article detail tests

Test cases:
- Component renders correctly
- Expand/collapse functionality
- API integration
- Loading states
- Error states
- Empty states
- Dark mode styling

**Commands**:
```bash
cd frontend && npm test -- OpposingViewpoints
```

---

### Phase 3: Integration & Polish

#### ✅ Step 3.1: Manual Testing
**Test Scenarios**:

1. **Articles with Clusters**: Verify opposing viewpoints appear for clustered articles
2. **Framework Oppositions**: Test with articles having opposite framework positions
3. **Sentiment Contrasts**: Verify sentiment-based oppositions work
4. **Source Bias Differences**: Test with left vs right source coverage
5. **Edge Cases**:
   - Articles with no oppositions
   - Single articles (no clusters)
   - AI service failures
   - Network errors

**Testing Commands**:
```bash
# Get auth token for testing
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}' \
  | jq -r '.access_token')

# Test API endpoint
curl -X GET "http://localhost:8000/articles/123/opposing-viewpoints?max_results=3" \
  -H "Authorization: Bearer $TOKEN" | jq
```

#### ✅ Step 3.2: Performance Optimization
- Cache viewpoint analysis results
- Optimize database queries with proper indexes
- Add response time monitoring
- Implement pagination if needed

#### ✅ Step 3.3: Documentation Updates
**Files to Update**:
- `CHANGELOG.md` - Document feature completion
- `docs/API.md` - Add new endpoint documentation
- `CLAUDE.md` - Update feature list and architecture
- Update any relevant test documentation

---

### Phase 4: Quality Assurance

#### ✅ Step 4.1: Test Coverage Verification
**Goals**:
- Backend: ≥90% test coverage for new service
- Frontend: ≥85% test coverage for new component
- Integration tests for API endpoint
- E2E tests for complete user flow

#### ✅ Step 4.2: Code Review Checklist
- [ ] Database migration applied and synced
- [ ] All new code follows project conventions
- [ ] Dark mode support implemented
- [ ] Error handling comprehensive
- [ ] Loading states appropriate
- [ ] API responses properly typed
- [ ] Security considerations (authentication, input validation)
- [ ] Performance impact assessed

#### ✅ Step 4.3: User Experience Validation
- [ ] Loading time under 2 seconds
- [ ] Clear visual hierarchy
- [ ] Intuitive expand/collapse behavior
- [ ] Mobile-responsive design
- [ ] Accessibility standards met
- [ ] Helpful error messages

---

## 🎯 Success Criteria

### Technical Metrics
- ✅ Backend response time < 2 seconds for viewpoint analysis
- ✅ Frontend component renders in < 100ms
- ✅ API handles 100+ concurrent requests
- ✅ Test coverage: Backend ≥90%, Frontend ≥85%
- ✅ Zero security vulnerabilities

### User Experience Metrics
- ✅ Oppositions found for 80%+ of clustered articles
- ✅ Clear visual distinction between relationship types
- ✅ AI explanations helpful and accurate
- ✅ Non-intrusive UI (expandable design)
- ✅ Mobile-friendly experience

### Content Quality Metrics
- ✅ Supports 4 relationship types: bias, framework, sentiment, temporal
- ✅ Opposition strength scoring accurate and meaningful
- ✅ AI explanations enhance understanding
- ✅ Graceful fallback when AI unavailable

---

## 🔄 Future Enhancements (Post-MVP)

### Phase 4 Features
- User feedback on viewpoint quality
- Personalized viewpoint recommendations based on reading history
- Export/share viewpoint comparisons
- Integration with newsletter system
- Analytics on viewpoint engagement

### Phase 5 Features
- Real-time viewpoint updates as new articles are processed
- Cross-language viewpoint comparisons
- Community-sourced viewpoint annotations
- Advanced filtering options

---

## 🚨 Critical Notes

### Local-Container Parity (CRITICAL)
After ANY migration operation:
```bash
# IMMEDIATELY sync migration files between container and local
docker cp news_backend:/app/alembic/versions/[NEW_FILE].py backend/alembic/versions/

# OR use the automated script
./scripts/sync-local-container.sh
```

### Testing Commands (Always Available)
```bash
# Backend tests
docker-compose exec backend pytest tests/test_viewpoint_analyzer.py -v

# Frontend tests
cd frontend && npm test -- OpposingViewpoints

# Full test suite
docker-compose exec backend pytest
cd frontend && npm test
```

### API Documentation
Update `docs/API.md` with new endpoint after implementation.

---

## 📊 Implementation Timeline

| Week | Tasks | Status |
|------|-------|--------|
| **Week 1** | Database migration, Core service implementation | 📋 Planned |
| **Week 2** | API endpoint, OpenAI integration, Backend testing | 📋 Planned |
| **Week 3** | Frontend component, API client, Article integration | 📋 Planned |
| **Week 4** | Integration testing, Performance optimization, Documentation | 📋 Planned |

**Total Estimated Time**: 3-4 weeks

---

## 🛠️ Quick Reference Commands

```bash
# Database operations
docker-compose exec backend alembic revision --autogenerate -m "description"
docker-compose exec backend alembic upgrade head
./scripts/sync-local-container.sh

# Testing
docker-compose exec backend pytest tests/test_viewpoint_analyzer.py -v
cd frontend && npm test -- OpposingViewpoints

# Manual API testing
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}' \
  | jq -r '.access_token')

curl -X GET "http://localhost:8000/articles/123/opposing-viewpoints?max_results=3" \
  -H "Authorization: Bearer $TOKEN"

# Development server restart
docker-compose restart backend
```

---

**Last Updated**: 2025-01-20
**Next Review**: After Step 1.1 (Database Migration) completion
**Dependencies**: OpenAI API key, existing article clustering data