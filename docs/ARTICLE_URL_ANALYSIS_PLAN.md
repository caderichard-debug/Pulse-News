# Article URL Analysis Feature - Implementation Plan

**Feature**: On-Demand Article Analysis via URL Submission

**Overview**: Allow users to submit any article URL for immediate extraction, AI analysis, and comprehensive processing - providing instant insights without waiting for scheduled RSS scraping.

**Status**: 🔨 Planning Phase

**Estimated Time**: 6-8 hours

---

## 📋 Table of Contents

1. [Feature Requirements](#feature-requirements)
2. [Architecture Overview](#architecture-overview)
3. [Backend Implementation](#backend-implementation)
4. [Frontend Implementation](#frontend-implementation)
5. [Testing Strategy](#testing-strategy)
6. [Documentation Updates](#documentation-updates)
7. [Success Criteria](#success-criteria)

---

## Feature Requirements

### Functional Requirements

**Backend:**
- Accept article URL via POST endpoint
- Validate URL format and accessibility
- Extract article content using existing `article_extractor.py`
- Perform AI analysis using existing `ai_analyzer.py`
- Generate ethical frameworks using existing `framework_generator.py`
- Verify statistics using existing `statistics_verifier.py`
- Generate context using existing `context_generator.py`
- Return complete analysis result with all metadata
- Support both authenticated and unauthenticated users (optional requirement)
- Handle errors gracefully (404, paywall, extraction failures)

**Frontend:**
- Dedicated page for URL submission (`/analyze`)
- URL input field with validation
- Submit button with loading state
- Real-time progress indicators (extraction → analysis → frameworks → statistics → context)
- Display full analysis results inline (similar to article detail page)
- Error handling with user-friendly messages
- Option to save analyzed article to user's feed (if authenticated)
- Share analysis link capability

### Non-Functional Requirements

- Response time: < 30 seconds for full analysis (depends on AI API latency)
- Support for common news sites (major publications)
- Handle paywalled content gracefully (show partial extraction)
- Mobile-responsive design
- Accessible UI (WCAG 2.1 AA)

---

## Architecture Overview

### Data Flow

```
User submits URL
    ↓
Frontend validation
    ↓
POST /api/analyze-url
    ↓
Backend validates URL & checks accessibility
    ↓
Extract article content (article_extractor.py)
    ↓
AI analysis (ai_analyzer.py)
    ↓
Generate frameworks (framework_generator.py)
    ↓
Verify statistics (statistics_verifier.py)
    ↓
Generate context (context_generator.py)
    ↓
Return complete analysis JSON
    ↓
Frontend displays results
```

### Database Considerations

**Option 1: Save to Database (Recommended)**
- Create `Article` record with `source_id = NULL` or create a special "User Submitted" source
- Associate with user if authenticated (`user_id`)
- Store all analysis data in existing tables (`ArticleAnalysis`, `ArticleFrameworkLink`, etc.)
- Benefits: Persistent storage, can be shared, searchable, appears in user's feed

**Option 2: Ephemeral Analysis (No DB Storage)**
- Process article in-memory only
- Return JSON response with all analysis data
- Benefits: Faster, no DB overhead, privacy-preserving
- Drawbacks: Cannot be saved, shared, or revisited

**Recommendation**: Use Option 1 with a flag `is_user_submitted = True` on `Article` model to distinguish from RSS-scraped articles.

---

## Backend Implementation

### Step 1: Update Database Models

**File**: `backend/app/models.py`

**Changes**:
1. Add `is_user_submitted` field to `Article` model:
   ```python
   class Article(SQLModel, table=True):
       # ... existing fields ...
       is_user_submitted: bool = Field(default=False, index=True)
       submitted_by_user_id: Optional[int] = Field(default=None, foreign_key="users.id")
   ```

2. Create migration:
   ```bash
   docker-compose exec backend alembic revision --autogenerate -m "add_user_submitted_articles"
   docker cp news_backend:/app/alembic/versions/XXXXX_add_user_submitted_articles.py backend/alembic/versions/
   docker-compose exec backend alembic upgrade head
   ```

**Code Reference**: [models.py:80](backend/app/models.py#L80) (Article model)

---

### Step 2: Create Article Analysis Service

**File**: `backend/app/services/url_analyzer.py` (NEW)

**Purpose**: Orchestrate the full analysis pipeline for a single URL.

**Implementation**:

```python
"""
Service for analyzing articles from user-submitted URLs.
Orchestrates extraction, AI analysis, framework generation, statistics verification, and context generation.
"""

from typing import Optional, Dict, Any
from sqlmodel import Session
import httpx
from urllib.parse import urlparse
import logging

from app.models import Article, Source, User, ArticleAnalysis
from app.services.article_extractor import ArticleExtractor
from app.services.ai_analyzer import AIAnalyzer
from app.services.framework_generator import FrameworkGenerator
from app.services.statistics_verifier import StatisticsVerifier
from app.services.context_generator import ContextGenerator

logger = logging.getLogger(__name__)


class URLAnalyzer:
    """Analyzes articles from user-submitted URLs."""

    def __init__(self, db: Session):
        self.db = db
        self.extractor = ArticleExtractor()
        self.ai_analyzer = AIAnalyzer()
        self.framework_generator = FrameworkGenerator()
        self.statistics_verifier = StatisticsVerifier(db)
        self.context_generator = ContextGenerator()

    async def analyze_url(
        self,
        url: str,
        user_id: Optional[int] = None,
        save_to_db: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze an article from a URL.

        Args:
            url: Article URL to analyze
            user_id: Optional user ID if authenticated
            save_to_db: Whether to persist the article and analysis

        Returns:
            Dictionary containing article data and all analysis results

        Raises:
            ValueError: If URL is invalid or inaccessible
            Exception: If extraction or analysis fails
        """
        # Step 1: Validate URL
        logger.info(f"Starting analysis for URL: {url}")
        await self._validate_url(url)

        # Step 2: Check if article already exists (by URL)
        existing_article = self.db.query(Article).filter(Article.url == url).first()
        if existing_article and existing_article.analysis:
            logger.info(f"Article already exists with ID {existing_article.id}")
            return await self._format_response(existing_article)

        # Step 3: Extract article content
        logger.info("Extracting article content...")
        extraction_result = await self.extractor.extract_article(url)
        if not extraction_result or not extraction_result.get("content"):
            raise ValueError("Failed to extract article content")

        # Step 4: Get or create source
        source = await self._get_or_create_source(url, extraction_result)

        # Step 5: Create article record (if saving)
        article = None
        if save_to_db:
            article = Article(
                title=extraction_result.get("title", "Untitled"),
                url=url,
                content=extraction_result["content"],
                author=extraction_result.get("author"),
                published_date=extraction_result.get("published_date"),
                source_id=source.id,
                is_user_submitted=True,
                submitted_by_user_id=user_id
            )
            self.db.add(article)
            self.db.commit()
            self.db.refresh(article)
            logger.info(f"Created article with ID {article.id}")

        # Step 6: AI Analysis
        logger.info("Performing AI analysis...")
        analysis_result = await self.ai_analyzer.analyze_article(
            title=extraction_result.get("title", ""),
            content=extraction_result["content"]
        )

        if save_to_db and article:
            article_analysis = ArticleAnalysis(
                article_id=article.id,
                summary=analysis_result.get("summary"),
                sentiment_score=analysis_result.get("sentiment_score"),
                bias_score=analysis_result.get("bias_score")
            )
            self.db.add(article_analysis)
            self.db.commit()

        # Step 7: Framework Generation
        logger.info("Generating ethical frameworks...")
        frameworks = await self.framework_generator.generate_frameworks(
            article_id=article.id if article else None,
            content=extraction_result["content"],
            save_to_db=save_to_db
        )

        # Step 8: Statistics Verification
        logger.info("Verifying statistics...")
        statistics = await self.statistics_verifier.verify_article_statistics(
            article_id=article.id if article else None,
            content=extraction_result["content"],
            save_to_db=save_to_db
        )

        # Step 9: Context Generation
        logger.info("Generating article context...")
        context = await self.context_generator.generate_context(
            article_id=article.id if article else None,
            title=extraction_result.get("title", ""),
            content=extraction_result["content"],
            save_to_db=save_to_db
        )

        # Step 10: Format and return response
        logger.info("Analysis complete!")
        if article:
            self.db.refresh(article)
            return await self._format_response(article)
        else:
            # Return ephemeral response without DB persistence
            return {
                "article": {
                    "title": extraction_result.get("title"),
                    "url": url,
                    "content": extraction_result["content"],
                    "author": extraction_result.get("author"),
                    "published_date": extraction_result.get("published_date"),
                    "source": {"name": source.name, "url": source.url}
                },
                "analysis": analysis_result,
                "frameworks": frameworks,
                "statistics": statistics,
                "context": context
            }

    async def _validate_url(self, url: str) -> None:
        """Validate URL format and accessibility."""
        # Parse URL
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("Invalid URL format")
        except Exception as e:
            raise ValueError(f"Invalid URL: {str(e)}")

        # Check accessibility (HEAD request with timeout)
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.head(url, follow_redirects=True)
                if response.status_code >= 400:
                    raise ValueError(f"URL returned status code {response.status_code}")
        except httpx.TimeoutException:
            raise ValueError("URL request timed out")
        except httpx.RequestError as e:
            raise ValueError(f"Failed to access URL: {str(e)}")

    async def _get_or_create_source(
        self,
        url: str,
        extraction_result: Dict[str, Any]
    ) -> Source:
        """Get existing source or create a new one."""
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"

        # Check if source exists
        source = self.db.query(Source).filter(Source.url == domain).first()
        if source:
            return source

        # Create new source
        source = Source(
            name=extraction_result.get("site_name", parsed.netloc),
            url=domain,
            rss_url=None,  # User-submitted articles don't have RSS feeds
            category="User Submitted"
        )
        self.db.add(source)
        self.db.commit()
        self.db.refresh(source)
        return source

    async def _format_response(self, article: Article) -> Dict[str, Any]:
        """Format article with all analysis data for API response."""
        # This should match the structure of the article detail endpoint
        response = {
            "id": article.id,
            "title": article.title,
            "url": article.url,
            "content": article.content,
            "author": article.author,
            "published_date": article.published_date.isoformat() if article.published_date else None,
            "source": {
                "id": article.source.id,
                "name": article.source.name,
                "url": article.source.url,
                "bias_score": article.source.bias_score
            } if article.source else None,
            "is_user_submitted": article.is_user_submitted,
            "analysis": None,
            "frameworks": [],
            "statistics": [],
            "context": None
        }

        # Add analysis data
        if article.analysis:
            response["analysis"] = {
                "summary": article.analysis.summary,
                "sentiment_score": article.analysis.sentiment_score,
                "bias_score": article.analysis.bias_score
            }

        # Add frameworks
        if article.framework_links:
            response["frameworks"] = [
                {
                    "id": link.framework.id,
                    "name": link.framework.name,
                    "description": link.framework.description,
                    "relevance_score": link.relevance_score
                }
                for link in article.framework_links
            ]

        # Add statistics
        if article.statistics:
            response["statistics"] = [
                {
                    "id": stat.id,
                    "claim": stat.claim,
                    "verification_status": stat.verification_status,
                    "source_url": stat.source_url,
                    "credibility_score": stat.credibility_score
                }
                for stat in article.statistics
            ]

        # Add context
        if article.context:
            response["context"] = {
                "background": article.context.background,
                "timeline": article.context.timeline,
                "significance": article.context.significance
            }

        return response
```

**Key Features**:
- Validates URL before processing
- Checks for duplicate articles (by URL)
- Orchestrates all analysis steps
- Supports both persistent (DB) and ephemeral (in-memory) modes
- Returns comprehensive analysis data
- Error handling at each step

**Code Reference**: `backend/app/services/url_analyzer.py` (new file)

---

### Step 3: Create API Endpoint

**File**: `backend/app/routes/analyze.py` (NEW)

**Implementation**:

```python
"""
API endpoints for analyzing user-submitted article URLs.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from pydantic import BaseModel, HttpUrl
import logging

from app.database import get_session
from app.models import User
from app.routes.auth import get_current_user_optional
from app.services.url_analyzer import URLAnalyzer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analyze", tags=["analyze"])


class AnalyzeURLRequest(BaseModel):
    """Request body for URL analysis."""
    url: HttpUrl
    save_to_feed: bool = True  # Whether to save to user's feed (requires auth)


class AnalyzeURLResponse(BaseModel):
    """Response body for URL analysis."""
    success: bool
    message: str
    data: Optional[dict] = None
    article_id: Optional[int] = None


@router.post("/url", response_model=AnalyzeURLResponse)
async def analyze_url(
    request: AnalyzeURLRequest,
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Analyze an article from a user-submitted URL.

    This endpoint:
    1. Validates the URL
    2. Extracts article content
    3. Performs AI analysis (summary, sentiment, bias)
    4. Generates ethical frameworks
    5. Verifies statistics
    6. Generates context

    If `save_to_feed` is True and user is authenticated, the article
    will be saved to the database and appear in the user's feed.

    **Returns**: Complete analysis data including article metadata,
    AI analysis, frameworks, statistics, and context.
    """
    try:
        # Check authentication if user wants to save
        if request.save_to_feed and not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required to save articles"
            )

        # Initialize analyzer
        analyzer = URLAnalyzer(session)

        # Perform analysis
        result = await analyzer.analyze_url(
            url=str(request.url),
            user_id=current_user.id if current_user else None,
            save_to_db=request.save_to_feed
        )

        return AnalyzeURLResponse(
            success=True,
            message="Article analyzed successfully",
            data=result,
            article_id=result.get("id")
        )

    except ValueError as e:
        # URL validation or extraction errors
        logger.warning(f"Invalid URL analysis request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:
        # Unexpected errors
        logger.error(f"Error analyzing URL: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze article. Please try again later."
        )


@router.get("/status/{article_id}")
async def get_analysis_status(
    article_id: int,
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Get the analysis status of a previously submitted article.

    Useful for checking if analysis is complete and retrieving results.
    """
    from app.models import Article

    article = session.get(Article, article_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )

    # Check permissions (if user-submitted, only the submitter can view)
    if article.is_user_submitted and article.submitted_by_user_id:
        if not current_user or current_user.id != article.submitted_by_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this article"
            )

    # Check analysis completion status
    has_analysis = bool(article.analysis)
    has_frameworks = bool(article.framework_links)
    has_statistics = bool(article.statistics)
    has_context = bool(article.context)

    return {
        "article_id": article_id,
        "is_complete": all([has_analysis, has_frameworks, has_statistics, has_context]),
        "status": {
            "extraction": True,  # If article exists, extraction succeeded
            "analysis": has_analysis,
            "frameworks": has_frameworks,
            "statistics": has_statistics,
            "context": has_context
        },
        "url": article.url,
        "title": article.title
    }
```

**Key Features**:
- Supports both authenticated and unauthenticated requests
- Optional database persistence (`save_to_feed`)
- Comprehensive error handling
- Status endpoint for checking analysis progress
- Permission checks for user-submitted articles

**Code Reference**: `backend/app/routes/analyze.py` (new file)

---

### Step 4: Register Router in Main App

**File**: `backend/app/main.py`

**Changes**:

```python
# Add import
from app.routes import analyze

# Register router (add with other routers)
app.include_router(analyze.router, prefix="/api")
```

**Code Reference**: [main.py:30](backend/app/main.py#L30) (router registration)

---

### Step 5: Update Service Methods for Ephemeral Mode

**Files to Update**:
- `backend/app/services/framework_generator.py`
- `backend/app/services/statistics_verifier.py`
- `backend/app/services/context_generator.py`

**Changes**: Add optional `save_to_db` parameter to each service method to support in-memory processing.

**Example** (for `framework_generator.py`):

```python
async def generate_frameworks(
    self,
    article_id: Optional[int] = None,
    content: str = None,
    save_to_db: bool = True
) -> List[Dict[str, Any]]:
    """
    Generate ethical frameworks for an article.

    Args:
        article_id: Article ID (required if save_to_db=True)
        content: Article content (required if article_id not provided)
        save_to_db: Whether to persist to database

    Returns:
        List of framework dictionaries
    """
    # ... existing logic ...

    if save_to_db:
        # Save to database
        # ... existing database save logic ...

    return frameworks  # Return list of dicts
```

**Apply similar changes to**:
- `statistics_verifier.py:verify_article_statistics()`
- `context_generator.py:generate_context()`

**Code References**:
- [framework_generator.py](backend/app/services/framework_generator.py)
- [statistics_verifier.py](backend/app/services/statistics_verifier.py)
- [context_generator.py](backend/app/services/context_generator.py)

---

### Step 6: Create Optional Authentication Dependency

**File**: `backend/app/routes/auth.py`

**Changes**: Add a new dependency that returns `None` if user is not authenticated (instead of raising 401).

```python
async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    session: Session = Depends(get_session)
) -> Optional[User]:
    """
    Get current user from token, or None if not authenticated.
    Does not raise 401 error.
    """
    if not token:
        return None

    try:
        return await get_current_user(token, session)
    except HTTPException:
        return None


# Create optional OAuth2 scheme
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl="auth/login",
    auto_error=False  # Don't raise error if token missing
)
```

**Code Reference**: [auth.py:50](backend/app/routes/auth.py#L50) (authentication functions)

---

## Frontend Implementation

### Step 7: Create API Client Method

**File**: `frontend/src/lib/api.ts`

**Changes**: Add method for URL analysis endpoint.

```typescript
// Add type definitions
export interface AnalyzeURLRequest {
  url: string;
  save_to_feed?: boolean;
}

export interface AnalyzeURLResponse {
  success: boolean;
  message: string;
  data?: {
    id?: number;
    title: string;
    url: string;
    content: string;
    author?: string;
    published_date?: string;
    source?: {
      id: number;
      name: string;
      url: string;
      bias_score?: number;
    };
    is_user_submitted: boolean;
    analysis?: {
      summary: string;
      sentiment_score: number;
      bias_score: number;
    };
    frameworks?: Array<{
      id: number;
      name: string;
      description: string;
      relevance_score: number;
    }>;
    statistics?: Array<{
      id: number;
      claim: string;
      verification_status: string;
      source_url?: string;
      credibility_score?: number;
    }>;
    context?: {
      background: string;
      timeline: string;
      significance: string;
    };
  };
  article_id?: number;
}

export interface AnalysisStatus {
  article_id: number;
  is_complete: boolean;
  status: {
    extraction: boolean;
    analysis: boolean;
    frameworks: boolean;
    statistics: boolean;
    context: boolean;
  };
  url: string;
  title: string;
}

// Add API methods
export const api = {
  // ... existing methods ...

  analyzeURL: async (request: AnalyzeURLRequest): Promise<AnalyzeURLResponse> => {
    const response = await apiClient.post('/analyze/url', request);
    return response.data;
  },

  getAnalysisStatus: async (articleId: number): Promise<AnalysisStatus> => {
    const response = await apiClient.get(`/analyze/status/${articleId}`);
    return response.data;
  },
};
```

**Code Reference**: [api.ts:100](frontend/src/lib/api.ts#L100) (API client methods)

---

### Step 8: Create Analyze Page

**File**: `frontend/src/app/analyze/page.tsx` (NEW)

**Implementation**:

```typescript
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api, type AnalyzeURLResponse } from '@/lib/api';

export default function AnalyzePage() {
  const router = useRouter();
  const [url, setUrl] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalyzeURLResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState<string>('');

  // Check if user is authenticated
  const isAuthenticated = typeof window !== 'undefined' && !!localStorage.getItem('token');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setAnalysisResult(null);

    // Validate URL
    if (!url.trim()) {
      setError('Please enter a valid URL');
      return;
    }

    try {
      new URL(url); // Validate URL format
    } catch {
      setError('Invalid URL format. Please enter a complete URL (e.g., https://example.com/article)');
      return;
    }

    setIsAnalyzing(true);

    try {
      // Simulate progress steps
      setCurrentStep('Extracting article content...');
      await new Promise(resolve => setTimeout(resolve, 500));

      setCurrentStep('Analyzing with AI...');
      await new Promise(resolve => setTimeout(resolve, 500));

      setCurrentStep('Generating ethical frameworks...');
      await new Promise(resolve => setTimeout(resolve, 500));

      setCurrentStep('Verifying statistics...');
      await new Promise(resolve => setTimeout(resolve, 500));

      setCurrentStep('Generating context...');

      // Make actual API call
      const result = await api.analyzeURL({
        url,
        save_to_feed: isAuthenticated, // Only save if authenticated
      });

      setAnalysisResult(result);
      setCurrentStep('Complete!');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to analyze article. Please try again.');
      setCurrentStep('');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleViewInFeed = () => {
    if (analysisResult?.article_id) {
      router.push(`/article/${analysisResult.article_id}`);
    }
  };

  const handleAnalyzeAnother = () => {
    setUrl('');
    setAnalysisResult(null);
    setError(null);
    setCurrentStep('');
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
            Analyze Any Article
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-400">
            Paste any article URL to get instant AI-powered analysis, bias detection,
            fact-checking, and ethical framework mapping.
          </p>
        </div>

        {/* URL Input Form */}
        {!analysisResult && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-6">
            <form onSubmit={handleSubmit}>
              <div className="mb-4">
                <label
                  htmlFor="url"
                  className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
                >
                  Article URL
                </label>
                <input
                  type="text"
                  id="url"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://example.com/article"
                  className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg
                           focus:ring-2 focus:ring-blue-500 focus:border-transparent
                           dark:bg-gray-700 dark:text-white"
                  disabled={isAnalyzing}
                />
              </div>

              {!isAuthenticated && (
                <div className="mb-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200
                              dark:border-yellow-800 rounded-lg">
                  <p className="text-sm text-yellow-800 dark:text-yellow-200">
                    💡 <a href="/login" className="underline font-medium">Log in</a> to save analyzed articles to your feed
                  </p>
                </div>
              )}

              <button
                type="submit"
                disabled={isAnalyzing}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400
                         text-white font-semibold py-3 px-6 rounded-lg transition-colors
                         flex items-center justify-center gap-2"
              >
                {isAnalyzing ? (
                  <>
                    <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                        fill="none"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                    Analyzing...
                  </>
                ) : (
                  'Analyze Article'
                )}
              </button>
            </form>

            {/* Progress Indicator */}
            {isAnalyzing && currentStep && (
              <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="animate-pulse w-2 h-2 bg-blue-600 rounded-full" />
                  <p className="text-sm text-blue-800 dark:text-blue-200">{currentStep}</p>
                </div>
              </div>
            )}

            {/* Error Message */}
            {error && (
              <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200
                            dark:border-red-800 rounded-lg">
                <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
              </div>
            )}
          </div>
        )}

        {/* Analysis Results */}
        {analysisResult?.data && (
          <div className="space-y-6">
            {/* Success Message */}
            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200
                          dark:border-green-800 rounded-lg p-4">
              <p className="text-green-800 dark:text-green-200 font-medium">
                ✅ {analysisResult.message}
              </p>
            </div>

            {/* Article Header */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                {analysisResult.data.title}
              </h2>
              {analysisResult.data.author && (
                <p className="text-gray-600 dark:text-gray-400 mb-2">
                  By {analysisResult.data.author}
                </p>
              )}
              {analysisResult.data.source && (
                <p className="text-sm text-gray-500 dark:text-gray-500 mb-4">
                  Source: {analysisResult.data.source.name}
                </p>
              )}
              <a
                href={analysisResult.data.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline text-sm"
              >
                View original article →
              </a>
            </div>

            {/* AI Analysis */}
            {analysisResult.data.analysis && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                  AI Analysis
                </h3>
                <div className="space-y-4">
                  <div>
                    <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-2">
                      Summary
                    </h4>
                    <p className="text-gray-600 dark:text-gray-400">
                      {analysisResult.data.analysis.summary}
                    </p>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-2">
                        Sentiment Score
                      </h4>
                      <div className="flex items-center gap-2">
                        <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full"
                            style={{
                              width: `${((analysisResult.data.analysis.sentiment_score + 1) / 2) * 100}%`,
                            }}
                          />
                        </div>
                        <span className="text-sm text-gray-600 dark:text-gray-400">
                          {analysisResult.data.analysis.sentiment_score.toFixed(2)}
                        </span>
                      </div>
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-2">
                        Bias Score
                      </h4>
                      <div className="flex items-center gap-2">
                        <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                          <div
                            className="bg-red-600 h-2 rounded-full"
                            style={{
                              width: `${((analysisResult.data.analysis.bias_score + 1) / 2) * 100}%`,
                            }}
                          />
                        </div>
                        <span className="text-sm text-gray-600 dark:text-gray-400">
                          {analysisResult.data.analysis.bias_score.toFixed(2)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Ethical Frameworks */}
            {analysisResult.data.frameworks && analysisResult.data.frameworks.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                  Ethical Frameworks
                </h3>
                <div className="space-y-3">
                  {analysisResult.data.frameworks.map((framework) => (
                    <div
                      key={framework.id}
                      className="border border-gray-200 dark:border-gray-700 rounded-lg p-4"
                    >
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="font-semibold text-gray-900 dark:text-white">
                          {framework.name}
                        </h4>
                        <span className="text-sm text-gray-500 dark:text-gray-400">
                          Relevance: {(framework.relevance_score * 100).toFixed(0)}%
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {framework.description}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Statistics Verification */}
            {analysisResult.data.statistics && analysisResult.data.statistics.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                  Verified Statistics
                </h3>
                <div className="space-y-3">
                  {analysisResult.data.statistics.map((stat) => (
                    <div
                      key={stat.id}
                      className="border border-gray-200 dark:border-gray-700 rounded-lg p-4"
                    >
                      <div className="flex justify-between items-start mb-2">
                        <p className="text-gray-900 dark:text-white">{stat.claim}</p>
                        <span
                          className={`text-sm px-2 py-1 rounded ${
                            stat.verification_status === 'verified'
                              ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-200'
                              : stat.verification_status === 'disputed'
                              ? 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-200'
                              : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-200'
                          }`}
                        >
                          {stat.verification_status}
                        </span>
                      </div>
                      {stat.source_url && (
                        <a
                          href={stat.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm text-blue-600 hover:underline"
                        >
                          View source →
                        </a>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Context */}
            {analysisResult.data.context && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                  Context & Background
                </h3>
                <div className="space-y-4">
                  {analysisResult.data.context.background && (
                    <div>
                      <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-2">
                        Background
                      </h4>
                      <p className="text-gray-600 dark:text-gray-400">
                        {analysisResult.data.context.background}
                      </p>
                    </div>
                  )}
                  {analysisResult.data.context.timeline && (
                    <div>
                      <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-2">
                        Timeline
                      </h4>
                      <p className="text-gray-600 dark:text-gray-400">
                        {analysisResult.data.context.timeline}
                      </p>
                    </div>
                  )}
                  {analysisResult.data.context.significance && (
                    <div>
                      <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-2">
                        Significance
                      </h4>
                      <p className="text-gray-600 dark:text-gray-400">
                        {analysisResult.data.context.significance}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-4">
              <button
                onClick={handleAnalyzeAnother}
                className="flex-1 bg-gray-600 hover:bg-gray-700 text-white font-semibold
                         py-3 px-6 rounded-lg transition-colors"
              >
                Analyze Another Article
              </button>
              {isAuthenticated && analysisResult.article_id && (
                <button
                  onClick={handleViewInFeed}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-semibold
                           py-3 px-6 rounded-lg transition-colors"
                >
                  View in Feed
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
```

**Key Features**:
- URL input with validation
- Loading states with progress indicators
- Comprehensive results display (similar to article detail page)
- Authentication detection (shows login prompt if not authenticated)
- "Analyze Another" and "View in Feed" actions
- Error handling with user-friendly messages
- Dark mode support
- Mobile-responsive design

**Code Reference**: `frontend/src/app/analyze/page.tsx` (new file)

---

### Step 9: Update Navigation

**File**: `frontend/src/components/Navbar.tsx`

**Changes**: Add "Analyze" link to navigation bar.

```typescript
// Add to navigation links array
const navLinks = [
  { href: '/dashboard', label: 'Dashboard' },
  { href: '/feed', label: 'Feed' },
  { href: '/analyze', label: 'Analyze' }, // NEW
  { href: '/preferences', label: 'Preferences' },
  { href: '/how-it-works', label: 'How It Works' },
];
```

**Code Reference**: [Navbar.tsx:20](frontend/src/components/Navbar.tsx#L20)

---

### Step 10: Add Landing Page CTA

**File**: `frontend/src/app/page.tsx`

**Changes**: Add prominent CTA button to analyze articles on the landing page.

```typescript
// Add to hero section (after existing CTAs)
<div className="flex gap-4 justify-center">
  <a
    href="/signup"
    className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-8 rounded-lg"
  >
    Get Started
  </a>
  <a
    href="/analyze"
    className="bg-white hover:bg-gray-100 text-blue-600 font-semibold py-3 px-8 rounded-lg border-2 border-blue-600"
  >
    Try It Now - Analyze Any Article
  </a>
</div>
```

**Code Reference**: [page.tsx:50](frontend/src/app/page.tsx#L50) (hero section)

---

## Testing Strategy

### Step 11: Backend Tests

**File**: `backend/tests/test_analyze.py` (NEW)

**Test Cases**:

```python
"""Tests for article URL analysis endpoint."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models import Article, ArticleAnalysis, User


class TestAnalyzeURL:
    """Test suite for URL analysis endpoint."""

    def test_analyze_url_success_authenticated(
        self,
        client: TestClient,
        session: Session,
        auth_headers: dict
    ):
        """Test successful article analysis with authenticated user."""
        response = client.post(
            "/api/analyze/url",
            json={
                "url": "https://example.com/test-article",
                "save_to_feed": True
            },
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "article_id" in data
        assert data["data"]["title"]
        assert data["data"]["analysis"]

        # Verify article was saved to database
        article = session.query(Article).filter(
            Article.url == "https://example.com/test-article"
        ).first()
        assert article is not None
        assert article.is_user_submitted is True

    def test_analyze_url_success_unauthenticated(
        self,
        client: TestClient
    ):
        """Test successful analysis without authentication (ephemeral mode)."""
        response = client.post(
            "/api/analyze/url",
            json={
                "url": "https://example.com/test-article",
                "save_to_feed": False
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["title"]
        assert data["data"]["analysis"]

    def test_analyze_url_save_requires_auth(
        self,
        client: TestClient
    ):
        """Test that saving to feed requires authentication."""
        response = client.post(
            "/api/analyze/url",
            json={
                "url": "https://example.com/test-article",
                "save_to_feed": True
            }
        )

        assert response.status_code == 401
        assert "Authentication required" in response.json()["detail"]

    def test_analyze_url_invalid_url(
        self,
        client: TestClient
    ):
        """Test error handling for invalid URL."""
        response = client.post(
            "/api/analyze/url",
            json={
                "url": "not-a-valid-url",
                "save_to_feed": False
            }
        )

        assert response.status_code == 400

    def test_analyze_url_inaccessible_url(
        self,
        client: TestClient
    ):
        """Test error handling for inaccessible URL."""
        response = client.post(
            "/api/analyze/url",
            json={
                "url": "https://nonexistent-domain-12345.com/article",
                "save_to_feed": False
            }
        )

        assert response.status_code == 400
        assert "Failed to access URL" in response.json()["detail"]

    def test_analyze_url_duplicate_detection(
        self,
        client: TestClient,
        session: Session,
        auth_headers: dict
    ):
        """Test that duplicate URLs return existing article."""
        # First analysis
        response1 = client.post(
            "/api/analyze/url",
            json={
                "url": "https://example.com/duplicate-test",
                "save_to_feed": True
            },
            headers=auth_headers
        )
        assert response1.status_code == 200
        article_id_1 = response1.json()["article_id"]

        # Second analysis (should return same article)
        response2 = client.post(
            "/api/analyze/url",
            json={
                "url": "https://example.com/duplicate-test",
                "save_to_feed": True
            },
            headers=auth_headers
        )
        assert response2.status_code == 200
        article_id_2 = response2.json()["article_id"]

        assert article_id_1 == article_id_2

    def test_get_analysis_status(
        self,
        client: TestClient,
        session: Session,
        auth_headers: dict
    ):
        """Test analysis status endpoint."""
        # Create article
        response = client.post(
            "/api/analyze/url",
            json={
                "url": "https://example.com/status-test",
                "save_to_feed": True
            },
            headers=auth_headers
        )
        article_id = response.json()["article_id"]

        # Check status
        status_response = client.get(
            f"/api/analyze/status/{article_id}",
            headers=auth_headers
        )

        assert status_response.status_code == 200
        status = status_response.json()
        assert status["article_id"] == article_id
        assert status["is_complete"] is True
        assert status["status"]["extraction"] is True
        assert status["status"]["analysis"] is True
```

**Code Reference**: `backend/tests/test_analyze.py` (new file)

---

### Step 12: Frontend Tests

**File**: `frontend/src/app/analyze/__tests__/page.test.tsx` (NEW)

**Test Cases**:

```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { useRouter } from 'next/navigation';
import AnalyzePage from '../page';
import { api } from '@/lib/api';

jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}));

jest.mock('@/lib/api');

describe('AnalyzePage', () => {
  const mockPush = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue({ push: mockPush });
    Storage.prototype.getItem = jest.fn(() => null); // Not authenticated by default
  });

  it('renders the analyze form', () => {
    render(<AnalyzePage />);

    expect(screen.getByText('Analyze Any Article')).toBeInTheDocument();
    expect(screen.getByLabelText('Article URL')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /analyze article/i })).toBeInTheDocument();
  });

  it('shows login prompt when not authenticated', () => {
    render(<AnalyzePage />);

    expect(screen.getByText(/log in to save analyzed articles/i)).toBeInTheDocument();
  });

  it('validates URL format before submission', async () => {
    render(<AnalyzePage />);

    const input = screen.getByLabelText('Article URL');
    const button = screen.getByRole('button', { name: /analyze article/i });

    fireEvent.change(input, { target: { value: 'invalid-url' } });
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText(/invalid url format/i)).toBeInTheDocument();
    });

    expect(api.analyzeURL).not.toHaveBeenCalled();
  });

  it('submits URL and displays analysis results', async () => {
    const mockResult = {
      success: true,
      message: 'Article analyzed successfully',
      data: {
        id: 1,
        title: 'Test Article',
        url: 'https://example.com/article',
        content: 'Article content...',
        analysis: {
          summary: 'Test summary',
          sentiment_score: 0.5,
          bias_score: -0.2,
        },
        frameworks: [
          {
            id: 1,
            name: 'Utilitarianism',
            description: 'Test framework',
            relevance_score: 0.85,
          },
        ],
        statistics: [],
        context: {
          background: 'Test background',
          timeline: 'Test timeline',
          significance: 'Test significance',
        },
      },
      article_id: 1,
    };

    (api.analyzeURL as jest.Mock).mockResolvedValue(mockResult);

    render(<AnalyzePage />);

    const input = screen.getByLabelText('Article URL');
    const button = screen.getByRole('button', { name: /analyze article/i });

    fireEvent.change(input, { target: { value: 'https://example.com/article' } });
    fireEvent.click(button);

    // Check loading state
    await waitFor(() => {
      expect(screen.getByText(/analyzing.../i)).toBeInTheDocument();
    });

    // Check results
    await waitFor(() => {
      expect(screen.getByText('Test Article')).toBeInTheDocument();
      expect(screen.getByText('Test summary')).toBeInTheDocument();
      expect(screen.getByText('Utilitarianism')).toBeInTheDocument();
    });
  });

  it('handles API errors gracefully', async () => {
    (api.analyzeURL as jest.Mock).mockRejectedValue({
      response: { data: { detail: 'Failed to extract article' } },
    });

    render(<AnalyzePage />);

    const input = screen.getByLabelText('Article URL');
    const button = screen.getByRole('button', { name: /analyze article/i });

    fireEvent.change(input, { target: { value: 'https://example.com/article' } });
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText(/failed to extract article/i)).toBeInTheDocument();
    });
  });

  it('allows analyzing another article', async () => {
    const mockResult = {
      success: true,
      message: 'Success',
      data: { title: 'Test', analysis: {} },
    };

    (api.analyzeURL as jest.Mock).mockResolvedValue(mockResult);

    render(<AnalyzePage />);

    // Submit first analysis
    const input = screen.getByLabelText('Article URL');
    fireEvent.change(input, { target: { value: 'https://example.com/article1' } });
    fireEvent.click(screen.getByRole('button', { name: /analyze article/i }));

    await waitFor(() => {
      expect(screen.getByText('Test')).toBeInTheDocument();
    });

    // Click "Analyze Another"
    const analyzeAnotherBtn = screen.getByRole('button', { name: /analyze another article/i });
    fireEvent.click(analyzeAnotherBtn);

    // Form should be reset
    expect(screen.getByLabelText('Article URL')).toHaveValue('');
    expect(screen.queryByText('Test')).not.toBeInTheDocument();
  });
});
```

**Code Reference**: `frontend/src/app/analyze/__tests__/page.test.tsx` (new file)

---

## Documentation Updates

### Step 13: Update API Documentation

**File**: `docs/API.md`

**Changes**: Add documentation for new `/analyze/url` endpoint.

```markdown
### POST /api/analyze/url

Analyze an article from a user-submitted URL.

**Authentication**: Optional (required if `save_to_feed` is true)

**Request Body**:
```json
{
  "url": "https://example.com/article",
  "save_to_feed": true
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Article analyzed successfully",
  "data": {
    "id": 123,
    "title": "Article Title",
    "url": "https://example.com/article",
    "content": "Full article content...",
    "author": "John Doe",
    "published_date": "2024-01-15T10:00:00Z",
    "source": {
      "id": 5,
      "name": "Example News",
      "url": "https://example.com",
      "bias_score": 0.1
    },
    "is_user_submitted": true,
    "analysis": {
      "summary": "AI-generated summary...",
      "sentiment_score": 0.5,
      "bias_score": -0.2
    },
    "frameworks": [...],
    "statistics": [...],
    "context": {...}
  },
  "article_id": 123
}
```

**Error Responses**:
- `400 Bad Request`: Invalid URL or extraction failed
- `401 Unauthorized`: Authentication required (when save_to_feed is true)
- `500 Internal Server Error`: Analysis pipeline error

### GET /api/analyze/status/{article_id}

Get the analysis status of a previously submitted article.

**Authentication**: Optional (required for user-submitted articles)

**Response** (200 OK):
```json
{
  "article_id": 123,
  "is_complete": true,
  "status": {
    "extraction": true,
    "analysis": true,
    "frameworks": true,
    "statistics": true,
    "context": true
  },
  "url": "https://example.com/article",
  "title": "Article Title"
}
```
```

**Code Reference**: [API.md](docs/API.md)

---

### Step 14: Update CHANGELOG

**File**: `CHANGELOG.md`

**Entry**:

```markdown
## 2025-10-17 XX:XX

**Article URL Analysis Feature** 🔨

### What Changed
- Added backend endpoint `/api/analyze/url` for on-demand article analysis in [analyze.py](backend/app/routes/analyze.py)
- Created `URLAnalyzer` service to orchestrate full analysis pipeline in [url_analyzer.py](backend/app/services/url_analyzer.py)
- Added database support for user-submitted articles with `is_user_submitted` flag in [models.py](backend/app/models.py:80)
- Created frontend `/analyze` page with URL submission form in [analyze/page.tsx](frontend/src/app/analyze/page.tsx)
- Updated navigation to include "Analyze" link in [Navbar.tsx](frontend/src/components/Navbar.tsx:20)
- Added comprehensive tests for both backend and frontend
- Updated API documentation in [API.md](docs/API.md)

### Features
- ✅ Real-time article analysis from any URL
- ✅ Progress indicators during analysis pipeline
- ✅ Support for both authenticated (persistent) and unauthenticated (ephemeral) modes
- ✅ Full analysis display (AI summary, sentiment, bias, frameworks, statistics, context)
- ✅ Duplicate article detection
- ✅ Error handling for invalid/inaccessible URLs
- ✅ Mobile-responsive design with dark mode support

### Test Results
- Backend: X new tests, all passing
- Frontend: X new tests, all passing

**Code References:**
- Backend endpoint: [analyze.py](backend/app/routes/analyze.py)
- Service: [url_analyzer.py](backend/app/services/url_analyzer.py)
- Frontend page: [analyze/page.tsx](frontend/src/app/analyze/page.tsx)
- Tests: [test_analyze.py](backend/tests/test_analyze.py), [page.test.tsx](frontend/src/app/analyze/__tests__/page.test.tsx)
```

**Code Reference**: [CHANGELOG.md](CHANGELOG.md)

---

### Step 15: Update CLAUDE.md

**File**: `CLAUDE.md`

**Changes**:

```markdown
#### Article Analysis (On-Demand)
- **Backend**: [analyze.py](backend/app/routes/analyze.py) - URL submission endpoint
- **Service**: [url_analyzer.py](backend/app/services/url_analyzer.py) - Analysis orchestration
- **Frontend**: [analyze/](frontend/src/app/analyze/)
- **Tests**: [test_analyze.py](backend/tests/test_analyze.py)
```

Add to "Current Implementation Status":

```markdown
### ✅ Completed (Phase 3+)
- **On-demand article analysis**: Users can submit any URL for instant analysis
  - URL validation and accessibility checking
  - Full analysis pipeline (extraction → AI → frameworks → statistics → context)
  - Support for authenticated (persistent) and unauthenticated (ephemeral) modes
  - Real-time progress indicators
  - Comprehensive error handling
```

**Code Reference**: [CLAUDE.md](CLAUDE.md)

---

## Success Criteria

### Functional Requirements ✅

- [ ] Backend endpoint accepts article URLs and returns complete analysis
- [ ] URL validation prevents invalid/inaccessible URLs
- [ ] Article extraction works for major news sites
- [ ] AI analysis generates summary, sentiment, and bias scores
- [ ] Ethical frameworks are mapped to articles
- [ ] Statistics are verified with source tracing
- [ ] Context is generated (background, timeline, significance)
- [ ] Duplicate URLs return existing articles (no re-analysis)
- [ ] Authenticated users can save articles to their feed
- [ ] Unauthenticated users can analyze without saving
- [ ] Frontend displays all analysis results
- [ ] Real-time progress indicators during analysis
- [ ] Error messages are user-friendly
- [ ] "Analyze Another" workflow resets form
- [ ] "View in Feed" navigates to article detail page

### Testing ✅

- [ ] Backend tests: 100% coverage on `url_analyzer.py` and `analyze.py`
- [ ] Frontend tests: All user interactions covered
- [ ] Integration test: Full analysis pipeline (URL → results)
- [ ] Error handling tests: Invalid URLs, extraction failures, API errors
- [ ] Authentication tests: Save requires auth, view works without auth

### Documentation ✅

- [ ] API.md updated with new endpoints
- [ ] CHANGELOG.md entry created
- [ ] CLAUDE.md updated with feature references
- [ ] Inline code comments added to complex logic
- [ ] README.md updated with feature mention (optional)

### Performance ✅

- [ ] Analysis completes in < 30 seconds (typical)
- [ ] Frontend shows progress during long operations
- [ ] Database queries optimized (no N+1 queries)
- [ ] API response size reasonable (< 1MB)

### User Experience ✅

- [ ] Form validation prevents bad submissions
- [ ] Loading states prevent duplicate submissions
- [ ] Error messages suggest next steps
- [ ] Results are readable and well-formatted
- [ ] Mobile-responsive design works on all screen sizes
- [ ] Dark mode support consistent with rest of app
- [ ] Navigation includes prominent "Analyze" link

---

## Implementation Checklist

### Backend (6-8 hours)

- [ ] **Step 1**: Update `Article` model with `is_user_submitted` field (30 min)
- [ ] **Step 2**: Create `url_analyzer.py` service (2 hours)
- [ ] **Step 3**: Create `analyze.py` route (1 hour)
- [ ] **Step 4**: Register router in `main.py` (5 min)
- [ ] **Step 5**: Update service methods for ephemeral mode (1 hour)
- [ ] **Step 6**: Add optional authentication dependency (15 min)
- [ ] **Step 11**: Write backend tests (1.5 hours)

### Frontend (4-6 hours)

- [ ] **Step 7**: Add API client methods (30 min)
- [ ] **Step 8**: Create `/analyze` page component (2.5 hours)
- [ ] **Step 9**: Update Navbar with "Analyze" link (10 min)
- [ ] **Step 10**: Add CTA to landing page (15 min)
- [ ] **Step 12**: Write frontend tests (1.5 hours)

### Documentation (1 hour)

- [ ] **Step 13**: Update API.md (20 min)
- [ ] **Step 14**: Update CHANGELOG.md (20 min)
- [ ] **Step 15**: Update CLAUDE.md (20 min)

### Total Estimated Time: 11-15 hours

---

## Future Enhancements (Post-MVP)

1. **Batch Analysis**: Allow users to submit multiple URLs at once
2. **Browser Extension**: One-click analysis from any webpage
3. **Social Sharing**: Share analysis results with custom URLs
4. **Analysis History**: View previously analyzed articles (for authenticated users)
5. **Export Options**: Download analysis as PDF/Markdown
6. **Real-time Updates**: WebSocket connection for live progress updates
7. **Source Comparison**: Analyze multiple articles on the same topic
8. **Custom Analysis**: Let users specify which analysis steps to run
9. **API Rate Limiting**: Prevent abuse with rate limits
10. **Paywall Handling**: Integrate with services like 12ft.io for paywalled content

---

**Document Status**: ✅ Complete - Ready for Implementation

**Last Updated**: 2025-10-17

**Estimated Implementation Time**: 11-15 hours

**Dependencies**: All existing services (article_extractor, ai_analyzer, framework_generator, statistics_verifier, context_generator)
