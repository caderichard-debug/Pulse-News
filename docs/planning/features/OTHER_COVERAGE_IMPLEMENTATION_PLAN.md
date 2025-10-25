# Other Coverage Implementation Plan

## Overview

This plan outlines the implementation of an enhanced "Other Coverage" feature for the article detail page (`/article/[id]`) that shows other articles covering the same event or topic from different sources and perspectives. This feature will replace the existing "Cross-Source Coverage" section with a more sophisticated, interactive component following the established UI patterns from the opposing viewpoints feature.

## Current State Analysis

### Existing Functionality
- **Basic Related Articles**: The article detail page already includes a "Cross-Source Coverage" section (lines 391-434) that shows related articles
- **Clustering System**: Backend has `ArticleCluster` and `ArticleClusterMember` models for grouping similar articles
- **Article Clusterer Service**: `article_clusterer.py` provides functionality to detect and group similar articles
- **API Response**: The `/articles/{id}` endpoint already returns `related_articles` data

### Limitations of Current Implementation
1. **Static Display**: Related articles are shown in a simple list format
2. **No Interactivity**: Users can't filter or analyze the coverage in different ways
3. **Limited Context**: No comparison of biases, sentiments, or source trustworthiness
4. **No Real-time Analysis**: Can't trigger analysis for articles without existing coverage

## Detailed Implementation Plan

### Phase 1: Backend Enhancements

#### 1.1 Enhance Article Clustering Service
**File**: `backend/app/services/article_clusterer.py`

**Changes**:
- Add new function `get_enhanced_coverage_comparison()` that returns richer data
- Include source bias information, trust scores, and sentiment analysis
- Add filtering capabilities by bias, sentiment range, and source type
- Implement similarity scoring with more nuanced metrics

**New Function**:
```python
def get_enhanced_coverage_comparison(
    article_id: int,
    session: Session,
    bias_filter: Optional[str] = None,
    sentiment_range: Optional[Tuple[float, float]] = None,
    max_results: int = 10
) -> Dict:
    """
    Get enhanced coverage comparison for an article with filtering options.
    Returns structured data for frontend consumption.
    """
```

#### 1.2 Update Article Detail Endpoint
**File**: `backend/app/routes/articles.py`

**Changes**:
- Enhance the `get_article_detail()` function to support coverage filtering
- Add new query parameters for coverage preferences
- Return more detailed coverage information including:
  - Source bias and trust scores
  - Sentiment differences
  - Publication time relationships
  - Similarity scores

**New Query Parameters**:
- `coverage_bias_filter` (optional): Filter by political lean
- `coverage_sentiment_range` (optional): Min/max sentiment range
- `coverage_max_results` (optional): Maximum coverage articles to return

#### 1.3 Add Coverage Analysis Endpoint
**File**: `backend/app/routes/articles.py`

**New Endpoint**:
```python
@router.post("/{article_id}/analyze-coverage")
async def trigger_coverage_analysis(
    article_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Trigger real-time analysis to find coverage for articles that don't have existing clusters.
    Uses the article clusterer service to find similar articles and create clusters on-demand.
    """
```

### Phase 2: Frontend Component Development

#### 2.1 Create Other Coverage Component
**File**: `frontend/src/components/OtherCoverage.tsx`

**Component Structure**:
- Initially collapsed with enticing preview showing coverage count
- Expandable interface following the opposing viewpoints UI pattern
- Filtering options for bias, sentiment, and source type
- Real-time analysis trigger for articles without coverage
- Loading states and error handling

**Key Features**:
- Collapsible interface with preview state
- Bias filtering (Left, Center, Right)
- Sentiment range filtering
- Source trust score filtering
- "Analyze for Coverage" button when no coverage exists
- Coverage metrics and comparison data

#### 2.2 Component Interface
**Props**:
```typescript
interface OtherCoverageProps {
  primaryArticleId: number;
  initialCoverage?: RelatedArticle[];
  onCoverageUpdate?: (coverage: RelatedArticle[]) => void;
}

interface RelatedArticle {
  id: number;
  title: string;
  url: string;
  source_name: string;
  source_bias: string | null;
  source_trust_score: number | null;
  published_at: string;
  sentiment_score: number | null;
  political_lean: string | null;
  similarity_score: number;
  summary?: string;
}
```

#### 2.3 UI Implementation Details

**Collapsed State**:
```tsx
if (!expanded) {
  return (
    <div className="mt-6 border-2 border-dashed border-gray-300 bg-gray-50 dark:border-gray-600 dark:bg-gray-800 rounded-lg p-6">
      <div className="text-center">
        <Newspaper className="h-8 w-8 text-gray-400 dark:text-gray-500 mx-auto mb-3" />
        <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-2">
          Other Coverage
        </h3>
        <p className="text-gray-600 dark:text-gray-400 mb-4">
          {coverageCount > 0
            ? `${coverageCount} other sources cover this story. Compare different perspectives and framing.`
            : "No other coverage found yet. Our system can analyze this story to find related coverage."
          }
        </p>
        <button onClick={() => setExpanded(true)}>
          <Eye className="h-4 w-4 mr-2" />
          View Coverage Details
        </button>
      </div>
    </div>
  )
}
```

**Expanded State Features**:
- Header with coverage count and filter toggle
- Filter panel with bias and sentiment options
- Coverage article cards with comparison metrics
- Real-time analysis option when no coverage exists
- External link and in-app navigation options

#### 2.4 Filter Implementation
```tsx
const FilterOptions = [
  { value: 'all', label: 'All Sources', icon: Globe },
  { value: 'left', label: 'Left-Leaning', icon: TrendingUp },
  { value: 'center', label: 'Center', icon: Minus },
  { value: 'right', label: 'Right-Leaning', icon: TrendingDown }
]
```

#### 2.5 Coverage Article Cards
Each coverage article will display:
- Article title with sentiment score badge
- Source name with bias indicator
- Publication time relative to primary article
- Similarity score
- Trust score indicator
- Quick actions (View in App, View Original)

### Phase 3: Integration

#### 3.1 Update Article Detail Page
**File**: `frontend/src/app/article/[id]/page.tsx`

**Changes**:
- Remove existing "Cross-Source Coverage" section (lines 391-434)
- Import and integrate new `OtherCoverage` component
- Pass article data and handle coverage updates
- Maintain responsive design and accessibility

**Integration Point**:
```tsx
{/* Replace existing Cross-Source Coverage section */}
<OtherCoverage
  primaryArticleId={article.id}
  initialCoverage={article.related_articles}
  onCoverageUpdate={(updatedCoverage) => {
    setArticle(prev => prev ? {
      ...prev,
      related_articles: updatedCoverage
    } : null);
  }}
/>
```

#### 3.2 API Client Updates
**File**: `frontend/src/lib/api.ts`

**New Methods**:
```typescript
async getCoverageAnalysis(params: {
  articleId: number;
  biasFilter?: string;
  sentimentRange?: [number, number];
  maxResults?: number;
}) {
  const queryParams = new URLSearchParams();
  if (params.biasFilter) queryParams.append('coverage_bias_filter', params.biasFilter);
  if (params.sentimentRange) {
    queryParams.append('coverage_sentiment_range',
      `${params.sentimentRange[0]},${params.sentimentRange[1]}`
    );
  }
  if (params.maxResults) queryParams.append('coverage_max_results', params.maxResults.toString());

  return this.request<CoverageResponse>(`/articles/${params.articleId}?${queryParams}`);
}

async triggerCoverageAnalysis(articleId: number) {
  return this.request(`/articles/${articleId}/analyze-coverage`, {
    method: 'POST'
  });
}
```

### Phase 4: Testing

#### 4.1 Backend Tests
**File**: `backend/tests/test_other_coverage.py`

**Test Cases**:
- Test enhanced coverage comparison with different filters
- Test bias filtering functionality
- Test sentiment range filtering
- Test real-time analysis triggering
- Test edge cases (no coverage, single article, large clusters)

#### 4.2 Frontend Tests
**File**: `frontend/src/components/__tests__/OtherCoverage.test.tsx`

**Test Cases**:
- Test component renders in collapsed state
- Test expand/collapse functionality
- Test filter application and state management
- Test coverage analysis trigger
- Test error states and loading indicators
- Test responsive design and accessibility

#### 4.3 Integration Tests
- Test full flow from article load to coverage display
- Test API integration and error handling
- Test user interactions and state persistence

### Phase 5: Styling and Polish

#### 5.1 Dark Mode Support
- Use existing semantic CSS classes from `globals.css`
- Ensure all elements have proper dark mode variants
- Test readability and contrast in both themes

#### 5.2 Responsive Design
- Mobile-optimized layout with stacked filters
- Tablet and desktop layouts with side-by-side comparison
- Touch-friendly interaction targets

#### 5.3 Accessibility
- Proper ARIA labels and roles
- Keyboard navigation support
- Screen reader announcements for dynamic content
- High contrast mode support

## Implementation Timeline

**Week 1**: Backend enhancements and new endpoints
- Enhance clustering service
- Update article detail endpoint
- Add coverage analysis endpoint
- Write backend tests

**Week 2**: Frontend component development
- Create OtherCoverage component
- Implement filtering and UI patterns
- Add API integration
- Write component tests

**Week 3**: Integration and polish
- Integrate component into article page
- Add responsive design
- Implement accessibility features
- End-to-end testing and bug fixes

## Success Metrics

1. **User Engagement**: Increase in time spent on article pages
2. **Cross-Source Exploration**: More users viewing articles from multiple sources
3. **Feature Usage**: Filter usage and analysis trigger rates
4. **Performance**: Minimal impact on page load times
5. **Coverage Quality**: Users find relevant, diverse coverage

## Technical Considerations

### Performance
- Cache coverage analysis results to avoid repeated computations
- Implement lazy loading for coverage articles
- Use efficient database queries with proper indexing

### Scalability
- Limit the number of coverage articles returned per request
- Implement pagination for large coverage sets
- Background job processing for coverage analysis

### Data Quality
- Improve clustering algorithm accuracy over time
- Add user feedback mechanisms for coverage relevance
- Monitor and filter out low-quality sources

## Future Enhancements

1. **Machine Learning**: Implement more sophisticated similarity algorithms
2. **User Preferences**: Allow users to set coverage preferences
3. **Coverage Analytics**: Provide insights into media bias patterns
4. **Real-time Updates**: WebSocket integration for live coverage updates
5. **Export Features**: Allow users to export coverage comparisons

---

This plan provides a comprehensive roadmap for implementing an enhanced "Other Coverage" feature that will significantly improve the user's ability to compare and contrast how different sources cover the same stories. The implementation follows established patterns in the codebase and leverages existing infrastructure while adding substantial new functionality.