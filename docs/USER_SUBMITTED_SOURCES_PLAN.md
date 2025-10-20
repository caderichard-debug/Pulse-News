# User-Submitted Sources Feature - Implementation Plan

**Created:** 2025-01-19
**Status:** Planning
**Estimated Time:** 6-8 hours

---

## 📋 Overview

Add functionality for users to submit news sources via article URLs. This feature will:
- Extract source domains from article URLs (not just RSS URLs)
- Create a tabbed "Sources" interface (similar to Preferences)
- Distinguish between "Recommended" (curator-approved) and "Community" sources
- Add search functionality to both Sources and Feed pages
- Gracefully handle non-news URLs

---

## 🎯 Goals

1. **Backend:** Create endpoint to accept article URLs and extract source information
2. **Database:** Add `is_recommended` flag to sources, default existing sources to `true`
3. **Frontend:** Build tabbed Sources page with search functionality
4. **Frontend:** Add search bars to Sources and Feed pages
5. **UX:** Provide clear visual distinction between recommended and community sources

---

## 🗄️ Database Changes

### Migration: Add `is_recommended` field to `sources` table

**File:** `backend/alembic/versions/XXXXX_add_is_recommended_to_sources.py`

```python
"""Add is_recommended field to sources

Revision ID: XXXXX
Revises: <previous_revision>
Create Date: 2025-01-19
"""

from alembic import op
import sqlalchemy as sa

def upgrade():
    # Add is_recommended column, default to True for existing sources
    op.add_column('sources', sa.Column('is_recommended', sa.Boolean(), nullable=False, server_default='true'))

    # Future sources added by users will be False by default (handled in application logic)

def downgrade():
    op.drop_column('sources', 'is_recommended')
```

### Update Source Model

**File:** `backend/app/models.py` (line ~121)

```python
class Source(SQLModel, table=True):
    __tablename__ = "sources"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=200, index=True)
    url: str = Field(max_length=500)
    rss_feed_url: str = Field(max_length=500, unique=True)
    description: Optional[str] = Field(default=None, max_length=1000)
    trust_score: float = Field(default=0.8, ge=0.0, le=1.0)

    # Organizational bias
    organizational_bias: Optional[OrganizationalBias] = Field(...)
    bias_description: Optional[str] = Field(default=None, max_length=500)

    # NEW: Curator recommendation flag
    is_recommended: bool = Field(default=False, index=True)  # ← ADD THIS

    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    articles: List["Article"] = Relationship(back_populates="source")
    topics: List["Topic"] = Relationship(...)
```

---

## 🔧 Backend Implementation

### 1. New Service: URL-Based Source Discovery

**File:** `backend/app/services/url_source_extractor.py` (NEW)

```python
"""
URL Source Extractor Service

Extracts source information from article URLs (not RSS feeds).
Uses web scraping to find RSS feeds for discovered sources.
"""

import logging
import feedparser
import requests
from urllib.parse import urlparse
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class URLSourceExtractor:
    """Extract source information from article URLs."""

    def __init__(self):
        self.timeout = 10

    def extract_source_from_article_url(self, article_url: str) -> Dict[str, Any]:
        """
        Extract source information from an article URL.

        Args:
            article_url: Full URL to an article (e.g., https://example.com/article/123)

        Returns:
            Dict containing:
                - domain: Source domain (e.g., "example.com")
                - base_url: Base URL (e.g., "https://example.com")
                - rss_feed_url: Discovered RSS feed URL
                - is_news_site: Whether this appears to be a news site

        Raises:
            ValueError: If URL is invalid or not a news source
        """
        logger.info(f"Extracting source from article URL: {article_url}")

        # Step 1: Parse and validate URL
        try:
            parsed = urlparse(article_url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("Invalid URL format")
        except Exception as e:
            raise ValueError(f"Invalid URL: {str(e)}")

        domain = parsed.netloc
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        # Step 2: Fetch the article page to find RSS feed
        try:
            rss_feed_url = self._discover_rss_feed(base_url, article_url)
            if not rss_feed_url:
                raise ValueError("Could not discover RSS feed for this source")
        except Exception as e:
            logger.error(f"RSS discovery failed for {article_url}: {str(e)}")
            raise ValueError(f"Failed to discover RSS feed: {str(e)}")

        # Step 3: Validate it's a news site by checking RSS feed
        is_news_site = self._validate_news_site(rss_feed_url)
        if not is_news_site:
            raise ValueError("This URL does not appear to be from a news source")

        return {
            "domain": domain,
            "base_url": base_url,
            "rss_feed_url": rss_feed_url,
            "is_news_site": is_news_site
        }

    def _discover_rss_feed(self, base_url: str, article_url: str) -> Optional[str]:
        """
        Discover RSS feed URL from article page or base URL.

        Priority:
        1. Check article page for <link rel="alternate" type="application/rss+xml">
        2. Common RSS feed locations (/rss, /feed, /rss.xml, etc.)
        3. Check base URL for RSS feed links
        """
        logger.info(f"Discovering RSS feed for {base_url}")

        # Try article page first
        try:
            response = requests.get(article_url, timeout=self.timeout, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; PulseBot/1.0)'
            })
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Look for RSS feed link in <head>
            rss_link = soup.find('link', {'type': 'application/rss+xml'})
            if rss_link and rss_link.get('href'):
                rss_url = rss_link['href']
                # Handle relative URLs
                if rss_url.startswith('/'):
                    rss_url = base_url + rss_url
                elif not rss_url.startswith('http'):
                    rss_url = base_url + '/' + rss_url

                # Validate the feed
                if self._validate_rss_feed(rss_url):
                    return rss_url
        except Exception as e:
            logger.warning(f"Failed to check article page for RSS: {str(e)}")

        # Try common RSS feed locations
        common_paths = [
            '/rss',
            '/feed',
            '/rss.xml',
            '/feed.xml',
            '/index.xml',
            '/atom.xml',
            '/?feed=rss2',
            '/feeds/posts/default'  # Blogger
        ]

        for path in common_paths:
            candidate_url = base_url + path
            if self._validate_rss_feed(candidate_url):
                return candidate_url

        return None

    def _validate_rss_feed(self, rss_url: str) -> bool:
        """Check if URL is a valid RSS/Atom feed."""
        try:
            feed = feedparser.parse(rss_url)

            # Check if feed has entries and is not malformed
            if feed.bozo and not feed.entries:
                return False

            if not feed.entries:
                return False

            return True
        except Exception as e:
            logger.debug(f"RSS validation failed for {rss_url}: {str(e)}")
            return False

    def _validate_news_site(self, rss_feed_url: str) -> bool:
        """
        Validate that the RSS feed appears to be from a news source.

        Checks:
        - Has recent entries (published within last 30 days)
        - Entries have titles and links
        - Feed title suggests news content
        """
        try:
            feed = feedparser.parse(rss_feed_url)

            if not feed.entries:
                return False

            # Check feed has basic news characteristics
            # (This is a simple heuristic - can be improved)
            recent_entries = 0
            from datetime import datetime, timedelta
            cutoff = datetime.now() - timedelta(days=30)

            for entry in feed.entries[:10]:  # Check first 10 entries
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_date = datetime(*entry.published_parsed[:6])
                    if pub_date > cutoff:
                        recent_entries += 1

                # Check entry has title and link
                if not entry.get('title') or not entry.get('link'):
                    return False

            # Require at least some recent content
            return recent_entries > 0

        except Exception as e:
            logger.error(f"News site validation failed: {str(e)}")
            return False
```

### 2. New API Endpoint: Create Source from Article URL

**File:** `backend/app/routes/sources.py` (NEW or UPDATE existing)

```python
"""
Sources API Routes

Endpoints for managing news sources.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select, func, or_
from typing import List, Optional

from ..models import Source
from ..database import get_session
from ..auth import get_current_user
from ..services.url_source_extractor import URLSourceExtractor
from ..services.source_analyzer import SourceAnalyzer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sources", tags=["sources"])


# Request/Response Models
class CreateSourceFromURLRequest(BaseModel):
    """Request to create source from article URL."""
    article_url: str


class SourceResponse(BaseModel):
    """Response model for source information."""
    id: int
    name: str
    url: str
    rss_feed_url: str
    description: Optional[str]
    trust_score: float
    organizational_bias: Optional[str]
    bias_description: Optional[str]
    is_recommended: bool
    is_active: bool
    created_at: str
    article_count: int = 0


@router.get("", response_model=List[SourceResponse])
async def list_sources(
    search: Optional[str] = Query(None, description="Search sources by name or URL"),
    recommended_only: bool = Query(False, description="Show only recommended sources"),
    active_only: bool = Query(True, description="Show only active sources"),
    sort_by: str = Query("name", description="Sort by: name, trust_score, article_count"),
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """
    List all news sources with optional filtering and sorting.
    """
    # Build query
    query = select(Source)

    # Apply filters
    if recommended_only:
        query = query.where(Source.is_recommended == True)

    if active_only:
        query = query.where(Source.is_active == True)

    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                Source.name.ilike(search_pattern),
                Source.url.ilike(search_pattern),
                Source.description.ilike(search_pattern)
            )
        )

    # Apply sorting
    if sort_by == "trust_score":
        query = query.order_by(Source.trust_score.desc())
    elif sort_by == "article_count":
        # This requires a subquery - simplified for now
        query = query.order_by(Source.name)
    else:  # name
        query = query.order_by(Source.name)

    sources = session.exec(query).all()

    # Get article counts for each source
    source_responses = []
    for source in sources:
        article_count = session.exec(
            select(func.count()).where(Article.source_id == source.id)
        ).first() or 0

        source_responses.append(SourceResponse(
            id=source.id,
            name=source.name,
            url=source.url,
            rss_feed_url=source.rss_feed_url,
            description=source.description,
            trust_score=source.trust_score,
            organizational_bias=source.organizational_bias.value if source.organizational_bias else None,
            bias_description=source.bias_description,
            is_recommended=source.is_recommended,
            is_active=source.is_active,
            created_at=source.created_at.isoformat(),
            article_count=article_count
        ))

    return source_responses


@router.post("/from-url", status_code=status.HTTP_201_CREATED)
async def create_source_from_article_url(
    request: CreateSourceFromURLRequest,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new source by providing an article URL.

    This endpoint:
    1. Extracts the source domain from the article URL
    2. Discovers the RSS feed for the source
    3. Validates it's a news source
    4. Uses AI to analyze source characteristics (bias, credibility, description)
    5. Creates source entry in database (marked as NOT recommended by default)

    Returns:
        Created source object with full metadata

    Raises:
        400: If URL is invalid, not a news source, or source already exists
        500: If analysis or creation fails
    """
    logger.info(f"User {current_user.get('email')} attempting to add source from URL: {request.article_url}")

    try:
        # Step 1: Extract source information from article URL
        extractor = URLSourceExtractor()
        source_info = extractor.extract_source_from_article_url(request.article_url)

        # Check if source with this RSS feed already exists
        existing_source = session.exec(
            select(Source).where(Source.rss_feed_url == source_info['rss_feed_url'])
        ).first()

        if existing_source:
            return {
                "message": "Source already exists",
                "source": {
                    "id": existing_source.id,
                    "name": existing_source.name,
                    "url": existing_source.url,
                    "rss_feed_url": existing_source.rss_feed_url,
                    "is_recommended": existing_source.is_recommended
                }
            }

        # Step 2: Analyze RSS feed using SourceAnalyzer
        analyzer = SourceAnalyzer(db=session)
        analysis = analyzer.analyze_rss_feed(source_info['rss_feed_url'])

        # Step 3: Create new source (NOT recommended by default)
        new_source = Source(
            name=analysis["name"],
            url=analysis["url"],
            rss_feed_url=source_info['rss_feed_url'],
            description=analysis["description"],
            organizational_bias=analysis["organizational_bias"],
            bias_description=analysis["bias_description"],
            trust_score=analysis["trust_score"],
            is_recommended=False,  # User-submitted sources are NOT recommended by default
            is_active=True
        )

        session.add(new_source)
        session.commit()
        session.refresh(new_source)

        logger.info(f"Created new source from article URL: {new_source.name} ({request.article_url})")

        return {
            "message": "Source created successfully",
            "source": {
                "id": new_source.id,
                "name": new_source.name,
                "url": new_source.url,
                "rss_feed_url": new_source.rss_feed_url,
                "description": new_source.description,
                "organizational_bias": new_source.organizational_bias.value if new_source.organizational_bias else None,
                "bias_description": new_source.bias_description,
                "trust_score": new_source.trust_score,
                "is_recommended": new_source.is_recommended,
                "is_active": new_source.is_active,
                "created_at": new_source.created_at.isoformat()
            }
        }

    except ValueError as e:
        # User-friendly error for invalid URLs or non-news sources
        logger.warning(f"Invalid source submission: {request.article_url} - {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating source from article URL: {request.article_url} - {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create source: {str(e)}"
        )
```

### 3. Register New Route

**File:** `backend/app/main.py`

```python
# Add to imports
from .routes import sources

# Add to router registration
app.include_router(sources.router)
```

---

## 🎨 Frontend Implementation

### 1. Create New Sources Page

**File:** `frontend/src/app/sources/page.tsx` (NEW)

```typescript
'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { api } from '@/lib/api';
import Navbar from '@/components/Navbar';
import SourceBiasBadge from '@/components/SourceBiasBadge';
import UnverifiedEmailAlert from '@/components/UnverifiedEmailAlert';
import Footer from '@/components/Footer';

interface Source {
  id: number;
  name: string;
  url: string;
  rss_feed_url: string;
  description?: string;
  trust_score: number;
  organizational_bias: string | null;
  bias_description?: string;
  is_recommended: boolean;
  is_active: boolean;
  article_count: number;
}

function SourcesContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Tab state
  const getInitialTab = (): 'recommended' | 'community' | 'add' => {
    const tab = searchParams.get('tab');
    if (tab === 'recommended' || tab === 'community' || tab === 'add') {
      return tab;
    }
    return 'recommended';
  };

  const [activeTab, setActiveTab] = useState<'recommended' | 'community' | 'add'>(getInitialTab());

  // Data state
  const [recommendedSources, setRecommendedSources] = useState<Source[]>([]);
  const [communitySources, setCommunitySources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Search state
  const [searchQuery, setSearchQuery] = useState('');

  // Add source state
  const [articleUrl, setArticleUrl] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadSources();
  }, []);

  // Update activeTab when URL changes
  useEffect(() => {
    const tab = searchParams.get('tab');
    if (tab === 'recommended' || tab === 'community' || tab === 'add') {
      setActiveTab(tab);
    }
  }, [searchParams]);

  const handleTabChange = (tab: 'recommended' | 'community' | 'add') => {
    setActiveTab(tab);
    router.push(`/sources?tab=${tab}`, { scroll: false });
  };

  const loadSources = async () => {
    try {
      setLoading(true);

      // Fetch both recommended and community sources
      const [recommended, community] = await Promise.all([
        api.getSources({ recommended_only: true }),
        api.getSources({ recommended_only: false })
      ]);

      setRecommendedSources(recommended.filter((s: Source) => s.is_recommended));
      setCommunitySources(community.filter((s: Source) => !s.is_recommended));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '';
      if (errorMessage.includes('401')) {
        router.push('/login');
      } else {
        setMessage({ type: 'error', text: 'Failed to load sources' });
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitSource = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!articleUrl.trim()) {
      setMessage({ type: 'error', text: 'Please enter an article URL' });
      return;
    }

    try {
      setSubmitting(true);
      setMessage(null);

      const result = await api.createSourceFromURL(articleUrl);

      setMessage({
        type: 'success',
        text: result.message || 'Source added successfully!'
      });

      setArticleUrl('');

      // Reload sources
      await loadSources();

      // Switch to community tab to see the new source
      handleTabChange('community');
    } catch (err) {
      setMessage({
        type: 'error',
        text: err instanceof Error ? err.message : 'Failed to add source'
      });
    } finally {
      setSubmitting(false);
    }
  };

  // Filter sources by search query
  const filterSources = (sources: Source[]) => {
    if (!searchQuery.trim()) return sources;

    const query = searchQuery.toLowerCase();
    return sources.filter(source =>
      source.name.toLowerCase().includes(query) ||
      source.url.toLowerCase().includes(query) ||
      source.description?.toLowerCase().includes(query)
    );
  };

  const filteredRecommended = filterSources(recommendedSources);
  const filteredCommunity = filterSources(communitySources);

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading sources...</p>
        </div>
      </div>
    );
  }

  return (
    <>
      <Navbar />
      <UnverifiedEmailAlert />
      <div className="min-h-screen bg-background transition-colors">
        <div className="max-w-6xl mx-auto px-4 py-8">
          {/* Header */}
          <div className="bg-card rounded-lg shadow-sm p-6 mb-6 border border-border">
            <h1 className="text-3xl font-bold text-foreground">📰 News Sources</h1>
            <p className="text-muted-foreground mt-1">
              Browse official sources or add your own discoveries
            </p>
          </div>

          {/* Tabs */}
          <div className="bg-card rounded-lg shadow-sm mb-6 border border-border">
            <div className="border-b border-border">
              <nav className="-mb-px flex">
                <button
                  onClick={() => handleTabChange('recommended')}
                  className={`py-4 px-6 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === 'recommended'
                      ? 'border-indigo-500 text-indigo-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  ✅ Recommended ({recommendedSources.length})
                </button>
                <button
                  onClick={() => handleTabChange('community')}
                  className={`py-4 px-6 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === 'community'
                      ? 'border-indigo-500 text-indigo-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  🌐 Community ({communitySources.length})
                </button>
                <button
                  onClick={() => handleTabChange('add')}
                  className={`py-4 px-6 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === 'add'
                      ? 'border-indigo-500 text-indigo-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  ➕ Add Source
                </button>
              </nav>
            </div>
          </div>

          {/* Message */}
          {message && (
            <div
              className={`mb-6 p-4 rounded-lg ${
                message.type === 'success'
                  ? 'bg-green-50 dark:bg-green-900/30 text-green-800 dark:text-green-200 border border-green-200 dark:border-green-800'
                  : 'bg-red-50 dark:bg-red-900/30 text-red-800 dark:text-red-200 border border-red-200 dark:border-red-800'
              }`}
            >
              {message.text}
            </div>
          )}

          {/* Search Bar (for Recommended and Community tabs) */}
          {(activeTab === 'recommended' || activeTab === 'community') && (
            <div className="mb-6">
              <input
                type="text"
                placeholder="Search sources by name, URL, or description..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full px-4 py-3 border border-border rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent bg-background text-foreground placeholder-muted-foreground"
              />
            </div>
          )}

          {/* Tab Content */}
          {activeTab === 'recommended' && (
            <SourceList
              sources={filteredRecommended}
              emptyMessage="No recommended sources found"
              isRecommended={true}
            />
          )}

          {activeTab === 'community' && (
            <SourceList
              sources={filteredCommunity}
              emptyMessage="No community sources found. Be the first to add one!"
              isRecommended={false}
            />
          )}

          {activeTab === 'add' && (
            <div className="bg-card rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-semibold text-foreground mb-4">
                Add a News Source
              </h2>
              <p className="text-sm text-muted-foreground mb-6">
                Paste any article URL from a news source you'd like to add. We'll automatically discover
                the source's RSS feed and analyze its credibility and bias.
              </p>

              <form onSubmit={handleSubmitSource}>
                <div className="mb-4">
                  <label htmlFor="article-url" className="block text-sm font-medium text-foreground mb-2">
                    Article URL
                  </label>
                  <input
                    type="url"
                    id="article-url"
                    value={articleUrl}
                    onChange={(e) => setArticleUrl(e.target.value)}
                    placeholder="https://example.com/article/some-news-article"
                    className="w-full px-4 py-3 border border-border rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent bg-background text-foreground placeholder-muted-foreground"
                    disabled={submitting}
                    required
                  />
                  <p className="mt-2 text-xs text-muted-foreground">
                    💡 Tip: Use any article URL from the source you want to add
                  </p>
                </div>

                <div className="mb-4 p-4 bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800 rounded-lg">
                  <h3 className="font-semibold text-blue-900 dark:text-blue-200 mb-2">
                    What happens next?
                  </h3>
                  <ul className="text-sm text-blue-800 dark:text-blue-200 space-y-1 list-disc list-inside">
                    <li>We extract the source domain from your URL</li>
                    <li>We automatically discover the source's RSS feed</li>
                    <li>AI analyzes the source's bias, credibility, and description</li>
                    <li>The source appears in the "Community" tab for all users</li>
                    <li>Moderators may promote it to "Recommended" after review</li>
                  </ul>
                </div>

                <button
                  type="submit"
                  disabled={submitting}
                  className="w-full px-6 py-3 bg-primary text-white rounded-lg hover:bg-primary-hover transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
                >
                  {submitting ? 'Adding Source...' : 'Add Source'}
                </button>
              </form>
            </div>
          )}
        </div>
      </div>
      <Footer />
    </>
  );
}

// Source List Component
function SourceList({
  sources,
  emptyMessage,
  isRecommended
}: {
  sources: Source[];
  emptyMessage: string;
  isRecommended: boolean;
}) {
  if (sources.length === 0) {
    return (
      <div className="bg-card rounded-lg shadow-sm p-8 text-center">
        <p className="text-muted-foreground">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {sources.map((source) => (
        <div
          key={source.id}
          className="bg-card border border-border rounded-lg p-5 hover:shadow-md transition-shadow"
        >
          <div className="flex items-start justify-between mb-2">
            <h3 className="font-semibold text-lg text-foreground">{source.name}</h3>
            {isRecommended && (
              <span className="text-xs bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200 px-2 py-1 rounded-full">
                ✅ Recommended
              </span>
            )}
          </div>

          <a
            href={source.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-blue-600 dark:text-blue-400 hover:underline mb-3 block"
          >
            {source.url}
          </a>

          {source.description && (
            <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
              {source.description}
            </p>
          )}

          <div className="flex items-center gap-3 flex-wrap">
            <div className="text-sm">
              <span className="text-muted-foreground">Trust: </span>
              <span className="font-semibold text-foreground">
                {(source.trust_score * 100).toFixed(0)}%
              </span>
            </div>

            {source.organizational_bias && (
              <SourceBiasBadge bias={source.organizational_bias} size="sm" />
            )}

            <div className="text-sm text-muted-foreground ml-auto">
              {source.article_count} articles
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

export default function SourcesPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading sources...</p>
        </div>
      </div>
    }>
      <SourcesContent />
    </Suspense>
  );
}
```

### 2. Add Search to Feed Page

**File:** `frontend/src/app/feed/page.tsx` (UPDATE existing)

Add search state and input field to the existing feed page. Insert search bar above the filters section:

```typescript
// Add to state (around line 68)
const [searchQuery, setSearchQuery] = useState('');

// Add search bar in JSX (before filters, around line 192)
{/* Search Bar */}
<div className="mb-6">
  <input
    type="text"
    placeholder="Search articles by title..."
    value={searchQuery}
    onChange={(e) => setSearchQuery(e.target.value)}
    className="w-full px-4 py-3 border border-border rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent bg-background text-foreground placeholder-muted-foreground"
  />
</div>

// Update loadFeedData to include search (around line 91)
const data = await api.getFeedArticles({
  page,
  page_size: 20,
  topic: selectedTopic || undefined,
  source_id: selectedSource || undefined,
  political_lean: selectedLean || undefined,
  date_range: dateRange || undefined,
  sort_by: sortBy,
  only_analyzed: onlyAnalyzed,
  only_verified_stats: onlyVerifiedStats,
  favorites_only: favoritesOnly,
  search: searchQuery || undefined,  // ← ADD THIS
});

// Update useEffect dependencies (around line 117)
}, [selectedTopic, selectedSource, selectedLean, dateRange, sortBy, onlyAnalyzed, onlyVerifiedStats, favoritesOnly, page, searchQuery, loadFeedData]);
```

### 3. Update API Client

**File:** `frontend/src/lib/api.ts`

```typescript
// Add to API client methods

// Get sources with filtering
async getSources(params?: {
  search?: string;
  recommended_only?: boolean;
  active_only?: boolean;
  sort_by?: string;
}): Promise<Source[]> {
  const queryParams = new URLSearchParams();
  if (params?.search) queryParams.append('search', params.search);
  if (params?.recommended_only !== undefined) queryParams.append('recommended_only', params.recommended_only.toString());
  if (params?.active_only !== undefined) queryParams.append('active_only', params.active_only.toString());
  if (params?.sort_by) queryParams.append('sort_by', params.sort_by);

  const url = `/sources${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
  const response = await fetch(`${this.baseURL}${url}`, {
    headers: this.getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch sources: ${response.statusText}`);
  }

  return response.json();
}

// Create source from article URL
async createSourceFromURL(articleUrl: string): Promise<any> {
  const response = await fetch(`${this.baseURL}/sources/from-url`, {
    method: 'POST',
    headers: this.getAuthHeaders(),
    body: JSON.stringify({ article_url: articleUrl }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create source');
  }

  return response.json();
}

// Update getFeedArticles to accept search parameter
async getFeedArticles(params: {
  page?: number;
  page_size?: number;
  topic?: string;
  source_id?: number;
  political_lean?: string;
  date_range?: string;
  sort_by?: string;
  only_analyzed?: boolean;
  only_verified_stats?: boolean;
  favorites_only?: boolean;
  search?: string;  // ← ADD THIS
}): Promise<FeedResponse> {
  const queryParams = new URLSearchParams();
  // ... existing params ...
  if (params.search) queryParams.append('search', params.search);

  // ... rest of method ...
}
```

### 4. Update Navbar

**File:** `frontend/src/components/Navbar.tsx`

Add "Sources" link to navigation:

```typescript
<Link
  href="/sources"
  className={`text-foreground hover:text-primary transition-colors ${
    pathname === '/sources' ? 'font-semibold text-primary' : ''
  }`}
>
  Sources
</Link>
```

---

## 🧪 Testing Plan

### Backend Tests

**File:** `backend/tests/test_url_source_extractor.py` (NEW)

```python
"""Tests for URL Source Extractor service."""

import pytest
from app.services.url_source_extractor import URLSourceExtractor


def test_extract_source_from_article_url_valid():
    """Test extracting source from a valid news article URL."""
    extractor = URLSourceExtractor()

    # Use a known news source for testing
    result = extractor.extract_source_from_article_url("https://www.bbc.com/news/world-12345678")

    assert result['domain'] == 'www.bbc.com'
    assert result['base_url'] == 'https://www.bbc.com'
    assert result['rss_feed_url'] is not None
    assert result['is_news_site'] is True


def test_extract_source_from_article_url_invalid():
    """Test extracting source from invalid URL."""
    extractor = URLSourceExtractor()

    with pytest.raises(ValueError, match="Invalid URL"):
        extractor.extract_source_from_article_url("not-a-url")


def test_extract_source_from_non_news_site():
    """Test extracting source from non-news URL."""
    extractor = URLSourceExtractor()

    with pytest.raises(ValueError, match="not appear to be from a news source"):
        extractor.extract_source_from_article_url("https://github.com/some-repo")
```

**File:** `backend/tests/test_sources_routes.py` (NEW)

```python
"""Tests for sources API routes."""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def auth_headers(test_user_token):
    return {"Authorization": f"Bearer {test_user_token}"}


def test_list_sources_recommended_only(client: TestClient, auth_headers):
    """Test listing only recommended sources."""
    response = client.get("/sources?recommended_only=true", headers=auth_headers)
    assert response.status_code == 200
    sources = response.json()
    assert all(source['is_recommended'] for source in sources)


def test_list_sources_with_search(client: TestClient, auth_headers):
    """Test searching sources by name."""
    response = client.get("/sources?search=bbc", headers=auth_headers)
    assert response.status_code == 200
    sources = response.json()
    # Check that results contain search term
    for source in sources:
        assert 'bbc' in source['name'].lower() or 'bbc' in source['url'].lower()


def test_create_source_from_url_valid(client: TestClient, auth_headers):
    """Test creating source from valid article URL."""
    response = client.post(
        "/sources/from-url",
        json={"article_url": "https://www.reuters.com/article/some-article"},
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert 'source' in data
    assert data['source']['is_recommended'] is False  # User-submitted = not recommended


def test_create_source_from_url_invalid(client: TestClient, auth_headers):
    """Test creating source from invalid URL."""
    response = client.post(
        "/sources/from-url",
        json={"article_url": "not-a-url"},
        headers=auth_headers
    )
    assert response.status_code == 400
```

### Frontend Tests

**File:** `frontend/src/app/sources/__tests__/page.test.tsx` (NEW)

```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { useRouter, useSearchParams } from 'next/navigation';
import SourcesPage from '../page';
import { api } from '@/lib/api';

jest.mock('next/navigation');
jest.mock('@/lib/api');

describe('SourcesPage', () => {
  const mockRouter = {
    push: jest.fn(),
  };

  const mockSearchParams = {
    get: jest.fn(() => null),
  };

  beforeEach(() => {
    (useRouter as jest.Mock).mockReturnValue(mockRouter);
    (useSearchParams as jest.Mock).mockReturnValue(mockSearchParams);

    // Mock API responses
    (api.getSources as jest.Mock).mockImplementation(({ recommended_only }) => {
      if (recommended_only) {
        return Promise.resolve([
          { id: 1, name: 'BBC News', is_recommended: true, article_count: 100 },
        ]);
      }
      return Promise.resolve([
        { id: 2, name: 'User Source', is_recommended: false, article_count: 5 },
      ]);
    });
  });

  it('renders recommended sources tab by default', async () => {
    render(<SourcesPage />);

    await waitFor(() => {
      expect(screen.getByText('BBC News')).toBeInTheDocument();
      expect(screen.getByText('✅ Recommended')).toBeInTheDocument();
    });
  });

  it('switches to community tab when clicked', async () => {
    render(<SourcesPage />);

    const communityTab = screen.getByText(/🌐 Community/);
    fireEvent.click(communityTab);

    await waitFor(() => {
      expect(screen.getByText('User Source')).toBeInTheDocument();
    });
  });

  it('filters sources by search query', async () => {
    render(<SourcesPage />);

    await waitFor(() => {
      expect(screen.getByText('BBC News')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText(/Search sources/);
    fireEvent.change(searchInput, { target: { value: 'BBC' } });

    expect(screen.getByText('BBC News')).toBeInTheDocument();
  });

  it('submits new source from article URL', async () => {
    (api.createSourceFromURL as jest.Mock).mockResolvedValue({
      message: 'Source created successfully',
      source: { id: 3, name: 'New Source' },
    });

    render(<SourcesPage />);

    const addTab = screen.getByText('➕ Add Source');
    fireEvent.click(addTab);

    const urlInput = screen.getByLabelText(/Article URL/);
    fireEvent.change(urlInput, { target: { value: 'https://example.com/article' } });

    const submitButton = screen.getByText('Add Source');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(api.createSourceFromURL).toHaveBeenCalledWith('https://example.com/article');
      expect(screen.getByText(/Source created successfully/)).toBeInTheDocument();
    });
  });
});
```

---

## 📋 Implementation Checklist

### Phase 1: Database & Backend Core (2-3 hours)
- [ ] Create migration for `is_recommended` field
- [ ] Update `Source` model with `is_recommended` field
- [ ] Run migration and verify existing sources are marked as recommended
- [ ] Create `URLSourceExtractor` service with RSS discovery
- [ ] Write unit tests for `URLSourceExtractor`
- [ ] Update `SourceAnalyzer` if needed

### Phase 2: Backend API (1-2 hours)
- [ ] Create/update `/sources` route with filtering and search
- [ ] Create `/sources/from-url` POST endpoint
- [ ] Add error handling for invalid URLs and non-news sources
- [ ] Write API route tests
- [ ] Test endpoint manually with Postman/curl

### Phase 3: Frontend Sources Page (2-3 hours)
- [ ] Create `app/sources/page.tsx` with tabbed interface
- [ ] Implement search functionality
- [ ] Create "Add Source" form with validation
- [ ] Add loading states and error handling
- [ ] Style components for light/dark mode
- [ ] Write component tests

### Phase 4: Feed Search & Integration (1 hour)
- [ ] Add search bar to Feed page
- [ ] Update backend feed endpoint to support search
- [ ] Update API client with search parameter
- [ ] Test feed search functionality

### Phase 5: Polish & Testing (1 hour)
- [ ] Add "Sources" link to Navbar
- [ ] Test entire flow end-to-end
- [ ] Verify dark mode compatibility
- [ ] Check responsive design on mobile
- [ ] Update documentation

---

## 🚀 Deployment Notes

1. **Migration**: Must run database migration before deploying backend changes
2. **Backwards Compatibility**: Existing sources will default to `is_recommended=true`
3. **API Dependencies**: Frontend changes depend on backend API being deployed first
4. **Testing**: Test on staging environment before production

---

## 📝 Future Enhancements

1. **Moderation Interface**: Admin panel to promote community sources to recommended
2. **Source Ratings**: Allow users to rate source quality
3. **RSS Feed Validation**: Background job to check if RSS feeds are still active
4. **Source Suggestions**: AI-powered source recommendations based on user interests
5. **Batch Import**: Allow admins to import multiple sources from OPML files

---

## 📚 Related Documentation

- [API.md](./API.md) - API endpoint reference
- [ARCHITECTURE.md](./ARCHITECTURE.md) - System architecture
- [FRONTEND_ARCHITECTURE_PLAN.md](./FRONTEND_ARCHITECTURE_PLAN.md) - Frontend roadmap

---

**End of Implementation Plan**
