# Favorites Feature Implementation Plan

**Status**: Planning
**Estimated Time**: 2-3 hours
**Created**: 2025-10-17

---

## 📋 Overview

Implement a favorites/bookmarking system allowing users to save articles for later reading. Users can favorite articles from both the feed page and article detail page, with favorited articles stored per-user in the database.

---

## 🎯 Goals

1. **User Experience**: Allow users to quickly save interesting articles
2. **Persistence**: Store favorites in database with user association
3. **Discoverability**: Make it easy to access favorited articles
4. **Consistency**: Maintain UI/UX consistency across the application

---

## 📊 Database Schema Changes

### New Model: `ArticleFavorite`

```python
class ArticleFavorite(SQLModel, table=True):
    """Many-to-many relationship between users and favorited articles."""

    __tablename__ = "article_favorites"

    # Composite primary key
    user_id: int = Field(foreign_key="users.id", primary_key=True, ondelete="CASCADE")
    article_id: int = Field(foreign_key="articles.id", primary_key=True, ondelete="CASCADE")

    # Metadata
    favorited_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = Field(default=None, max_length=500)  # Optional user notes (future enhancement)

    # Indexes for performance
    __table_args__ = (
        Index("idx_user_favorites", "user_id", "favorited_at"),
        Index("idx_article_favorites", "article_id"),
    )
```

### Alembic Migration

**File**: `backend/alembic/versions/XXXXX_add_article_favorites.py`

```python
"""Add article favorites table

Revision ID: XXXXX
Revises: 9c422eafa504
Create Date: 2025-10-17

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

revision = 'XXXXX'
down_revision = '9c422eafa504'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create article_favorites table
    op.create_table(
        'article_favorites',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('article_id', sa.Integer(), nullable=False),
        sa.Column('favorited_at', sa.DateTime(), nullable=False),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'article_id')
    )

    # Create indexes
    op.create_index('idx_user_favorites', 'article_favorites', ['user_id', 'favorited_at'])
    op.create_index('idx_article_favorites', 'article_favorites', ['article_id'])


def downgrade() -> None:
    op.drop_index('idx_article_favorites', table_name='article_favorites')
    op.drop_index('idx_user_favorites', table_name='article_favorites')
    op.drop_table('article_favorites')
```

---

## 🔧 Backend Implementation

### 1. Update Models (`backend/app/models.py`)

Add the `ArticleFavorite` model and update related models:

```python
# Add to imports
from datetime import datetime
from sqlalchemy import Index

# New model (add after other models)
class ArticleFavorite(SQLModel, table=True):
    """User's favorited articles."""
    __tablename__ = "article_favorites"

    user_id: int = Field(foreign_key="users.id", primary_key=True, ondelete="CASCADE")
    article_id: int = Field(foreign_key="articles.id", primary_key=True, ondelete="CASCADE")
    favorited_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = Field(default=None, max_length=500)

    __table_args__ = (
        Index("idx_user_favorites", "user_id", "favorited_at"),
        Index("idx_article_favorites", "article_id"),
    )
```

### 2. Create Favorites Routes (`backend/app/routes/favorites.py`)

```python
"""
API endpoints for managing user favorites.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, func
from pydantic import BaseModel
from datetime import datetime
import logging

from ..database import get_session
from ..models import User, Article, ArticleFavorite
from ..routes.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/favorites", tags=["favorites"])


class FavoriteArticleResponse(BaseModel):
    """Response for a favorited article."""
    id: int
    title: str
    url: str
    source_name: str
    published_at: datetime
    favorited_at: datetime
    summary: Optional[str] = None
    sentiment_score: Optional[float] = None
    political_lean: Optional[str] = None


class FavoritesListResponse(BaseModel):
    """Response for list of favorites."""
    favorites: List[FavoriteArticleResponse]
    total_count: int


@router.post("/articles/{article_id}")
async def add_favorite(
    article_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Add an article to user's favorites."""
    # Check if article exists
    article = session.get(Article, article_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )

    # Check if already favorited
    existing = session.exec(
        select(ArticleFavorite).where(
            ArticleFavorite.user_id == current_user.id,
            ArticleFavorite.article_id == article_id
        )
    ).first()

    if existing:
        return {
            "message": "Article already favorited",
            "favorited_at": existing.favorited_at
        }

    # Create favorite
    favorite = ArticleFavorite(
        user_id=current_user.id,
        article_id=article_id
    )
    session.add(favorite)
    session.commit()

    logger.info(f"User {current_user.id} favorited article {article_id}")

    return {
        "message": "Article added to favorites",
        "favorited_at": favorite.favorited_at
    }


@router.delete("/articles/{article_id}")
async def remove_favorite(
    article_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Remove an article from user's favorites."""
    favorite = session.exec(
        select(ArticleFavorite).where(
            ArticleFavorite.user_id == current_user.id,
            ArticleFavorite.article_id == article_id
        )
    ).first()

    if not favorite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Favorite not found"
        )

    session.delete(favorite)
    session.commit()

    logger.info(f"User {current_user.id} unfavorited article {article_id}")

    return {"message": "Article removed from favorites"}


@router.get("", response_model=FavoritesListResponse)
async def get_favorites(
    limit: int = 50,
    offset: int = 0,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get user's favorited articles."""
    # Get total count
    total_count = session.exec(
        select(func.count(ArticleFavorite.article_id)).where(
            ArticleFavorite.user_id == current_user.id
        )
    ).one()

    # Get favorites with article details
    statement = (
        select(Article, ArticleFavorite.favorited_at)
        .join(ArticleFavorite, Article.id == ArticleFavorite.article_id)
        .where(ArticleFavorite.user_id == current_user.id)
        .order_by(ArticleFavorite.favorited_at.desc())
        .offset(offset)
        .limit(limit)
    )

    results = session.exec(statement).all()

    favorites = []
    for article, favorited_at in results:
        # Get source name
        source = session.get(Source, article.source_id)

        # Get analysis
        analysis = session.exec(
            select(ArticleAnalysis).where(ArticleAnalysis.article_id == article.id)
        ).first()

        favorites.append(FavoriteArticleResponse(
            id=article.id,
            title=article.title,
            url=article.url,
            source_name=source.name if source else "Unknown",
            published_at=article.published_at,
            favorited_at=favorited_at,
            summary=analysis.summary if analysis else None,
            sentiment_score=analysis.sentiment_score if analysis else None,
            political_lean=analysis.political_lean if analysis else None
        ))

    return FavoritesListResponse(
        favorites=favorites,
        total_count=total_count
    )


@router.get("/check/{article_id}")
async def check_favorite(
    article_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Check if an article is favorited by the user."""
    favorite = session.exec(
        select(ArticleFavorite).where(
            ArticleFavorite.user_id == current_user.id,
            ArticleFavorite.article_id == article_id
        )
    ).first()

    return {
        "is_favorited": favorite is not None,
        "favorited_at": favorite.favorited_at if favorite else None
    }
```

### 3. Update Feed Endpoint (`backend/app/routes/feed.py`)

Add `is_favorited` field to article responses:

```python
# In get_feed_articles function, add to the article building loop:
is_favorited = False
if current_user:
    favorite = session.exec(
        select(ArticleFavorite).where(
            ArticleFavorite.user_id == current_user.id,
            ArticleFavorite.article_id == article.id
        )
    ).first()
    is_favorited = favorite is not None

# Add to response dict:
"is_favorited": is_favorited
```

### 4. Update Article Detail Endpoint (`backend/app/routes/articles.py`)

Add `is_favorited` to detail response:

```python
# Check if favorited
is_favorited = False
if current_user:
    favorite = session.exec(
        select(ArticleFavorite).where(
            ArticleFavorite.user_id == current_user.id,
            ArticleFavorite.article_id == article_id
        )
    ).first()
    is_favorited = favorite is not None

# Add to response
"is_favorited": is_favorited
```

### 5. Register Router (`backend/app/main.py`)

```python
from .routes import favorites

app.include_router(favorites.router)
```

---

## 🎨 Frontend Implementation

### 1. Update API Client (`frontend/src/lib/api.ts`)

```typescript
// Add to ApiClient class

async addFavorite(articleId: number) {
  return this.request<{
    message: string;
    favorited_at: string;
  }>(`/favorites/articles/${articleId}`, {
    method: 'POST',
  });
}

async removeFavorite(articleId: number) {
  return this.request<{
    message: string;
  }>(`/favorites/articles/${articleId}`, {
    method: 'DELETE',
  });
}

async getFavorites(params?: { limit?: number; offset?: number }) {
  const queryParams = new URLSearchParams();
  if (params?.limit) queryParams.append('limit', params.limit.toString());
  if (params?.offset) queryParams.append('offset', params.offset.toString());

  return this.request<{
    favorites: Array<{
      id: number;
      title: string;
      url: string;
      source_name: string;
      published_at: string;
      favorited_at: string;
      summary: string | null;
      sentiment_score: number | null;
      political_lean: string | null;
    }>;
    total_count: number;
  }>(`/favorites?${queryParams}`);
}

async checkFavorite(articleId: number) {
  return this.request<{
    is_favorited: boolean;
    favorited_at: string | null;
  }>(`/favorites/check/${articleId}`);
}
```

### 2. Create Favorite Button Component (`frontend/src/components/FavoriteButton.tsx`)

```typescript
'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';

interface FavoriteButtonProps {
  articleId: number;
  initialFavorited?: boolean;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  onToggle?: (isFavorited: boolean) => void;
}

export default function FavoriteButton({
  articleId,
  initialFavorited = false,
  size = 'md',
  showLabel = false,
  onToggle
}: FavoriteButtonProps) {
  const [isFavorited, setIsFavorited] = useState(initialFavorited);
  const [isLoading, setIsLoading] = useState(false);

  // Check authentication
  const isAuthenticated = typeof window !== 'undefined' && !!localStorage.getItem('token');

  const handleToggle = async (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent navigation if inside clickable card

    if (!isAuthenticated) {
      // Redirect to login
      window.location.href = '/login';
      return;
    }

    setIsLoading(true);
    try {
      if (isFavorited) {
        await api.removeFavorite(articleId);
        setIsFavorited(false);
        onToggle?.(false);
      } else {
        await api.addFavorite(articleId);
        setIsFavorited(true);
        onToggle?.(true);
      }
    } catch (error) {
      console.error('Failed to toggle favorite:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const sizeClasses = {
    sm: 'w-8 h-8 text-sm',
    md: 'w-10 h-10 text-base',
    lg: 'w-12 h-12 text-lg'
  };

  const iconSizes = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6'
  };

  return (
    <button
      onClick={handleToggle}
      disabled={isLoading}
      className={`${sizeClasses[size]} rounded-full flex items-center justify-center gap-2
                 transition-all disabled:opacity-50 disabled:cursor-not-allowed
                 ${isFavorited
                   ? 'bg-red-50 hover:bg-red-100 text-red-600 border-2 border-red-600'
                   : 'bg-gray-50 hover:bg-gray-100 text-gray-400 border-2 border-gray-300 hover:border-gray-400'
                 }`}
      title={isFavorited ? 'Remove from favorites' : 'Add to favorites'}
      aria-label={isFavorited ? 'Remove from favorites' : 'Add to favorites'}
    >
      {/* Heart Icon */}
      <svg
        className={iconSizes[size]}
        fill={isFavorited ? 'currentColor' : 'none'}
        stroke="currentColor"
        strokeWidth="2"
        viewBox="0 0 24 24"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z"
        />
      </svg>

      {showLabel && (
        <span className="text-sm font-medium">
          {isFavorited ? 'Favorited' : 'Favorite'}
        </span>
      )}
    </button>
  );
}
```

### 3. Update Feed Page (`frontend/src/app/feed/page.tsx`)

```typescript
// Add to article card in the map function:
<div className="flex items-start justify-between gap-4">
  <div className="flex-1">
    {/* Existing article content */}
  </div>

  <FavoriteButton
    articleId={article.id}
    initialFavorited={article.is_favorited}
    size="sm"
  />
</div>
```

### 4. Update Article Detail Page (`frontend/src/app/article/[id]/page.tsx`)

```typescript
// Add import
import FavoriteButton from '@/components/FavoriteButton';

// Add to article header section, after the title:
<div className="flex items-center gap-4 mb-4">
  <h1 className="text-4xl font-bold flex-1 text-foreground">{article.title}</h1>
  <FavoriteButton
    articleId={article.id}
    initialFavorited={article.is_favorited}
    size="lg"
    showLabel
  />
</div>
```

### 5. Add Favorites Page (`frontend/src/app/favorites/page.tsx`)

```typescript
'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { formatDate } from '@/lib/dateUtils';
import Navbar from '@/components/Navbar';
import UnverifiedEmailAlert from '@/components/UnverifiedEmailAlert';
import FavoriteButton from '@/components/FavoriteButton';

interface FavoriteArticle {
  id: number;
  title: string;
  url: string;
  source_name: string;
  published_at: string;
  favorited_at: string;
  summary: string | null;
  sentiment_score: number | null;
  political_lean: string | null;
}

export default function FavoritesPage() {
  const router = useRouter();
  const [favorites, setFavorites] = useState<FavoriteArticle[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [totalCount, setTotalCount] = useState(0);

  const loadFavorites = useCallback(async () => {
    try {
      setLoading(true);
      const data = await api.getFavorites({ limit: 50 });
      setFavorites(data.favorites);
      setTotalCount(data.total_count);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load favorites');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadFavorites();
  }, [loadFavorites]);

  const handleRemoveFavorite = (articleId: number) => {
    // Remove from local state immediately for better UX
    setFavorites(prev => prev.filter(f => f.id !== articleId));
    setTotalCount(prev => prev - 1);
  };

  return (
    <>
      <Navbar />
      <UnverifiedEmailAlert />
      <div className="min-h-screen bg-background">
        <div className="max-w-4xl mx-auto px-4 py-8">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-4xl font-bold text-foreground mb-2">
              Favorite Articles
            </h1>
            <p className="text-muted-foreground">
              {totalCount} {totalCount === 1 ? 'article' : 'articles'} saved for later
            </p>
          </div>

          {/* Loading State */}
          {loading && (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
              <p className="mt-4 text-muted-foreground">Loading favorites...</p>
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-700">{error}</p>
            </div>
          )}

          {/* Empty State */}
          {!loading && !error && favorites.length === 0 && (
            <div className="text-center py-12">
              <svg
                className="mx-auto h-24 w-24 text-gray-400 mb-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z"
                />
              </svg>
              <h3 className="text-xl font-semibold text-foreground mb-2">
                No favorites yet
              </h3>
              <p className="text-muted-foreground mb-6">
                Start saving articles you want to read later
              </p>
              <button
                onClick={() => router.push('/feed')}
                className="px-6 py-3 bg-primary text-white rounded-lg hover:bg-primary-hover transition-colors font-medium"
              >
                Browse Articles
              </button>
            </div>
          )}

          {/* Favorites List */}
          {!loading && !error && favorites.length > 0 && (
            <div className="space-y-4">
              {favorites.map((article) => (
                <div
                  key={article.id}
                  className="bg-card border border-border rounded-lg p-6 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <h2
                        className="text-xl font-semibold text-foreground mb-2 hover:text-primary cursor-pointer"
                        onClick={() => router.push(`/article/${article.id}`)}
                      >
                        {article.title}
                      </h2>

                      <div className="flex items-center gap-2 text-sm text-muted-foreground mb-3">
                        <span>{article.source_name}</span>
                        <span>•</span>
                        <span>{formatDate(article.published_at)}</span>
                        <span>•</span>
                        <span>Saved {formatDate(article.favorited_at)}</span>
                      </div>

                      {article.summary && (
                        <p className="text-card-foreground mb-3 line-clamp-2">
                          {article.summary}
                        </p>
                      )}

                      <button
                        onClick={() => router.push(`/article/${article.id}`)}
                        className="text-primary hover:underline text-sm font-medium"
                      >
                        Read article →
                      </button>
                    </div>

                    <FavoriteButton
                      articleId={article.id}
                      initialFavorited={true}
                      size="md"
                      onToggle={(isFavorited) => {
                        if (!isFavorited) {
                          handleRemoveFavorite(article.id);
                        }
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
```

### 6. Update Navbar (`frontend/src/components/Navbar.tsx`)

Add "Favorites" link to navigation:

```typescript
<Link
  href="/favorites"
  className={`hover:text-primary transition-colors ${
    pathname === '/favorites' ? 'text-primary font-semibold' : ''
  }`}
>
  Favorites
</Link>
```

---

## 🧪 Testing

### Backend Tests (`backend/tests/routes/test_favorites.py`)

```python
"""Tests for favorites endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models import ArticleFavorite


def test_add_favorite(client: TestClient, test_user_token: str, test_article):
    """Test adding article to favorites."""
    response = client.post(
        f"/favorites/articles/{test_article.id}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "favorited_at" in data


def test_add_favorite_already_exists(client: TestClient, test_user_token: str, test_article, session: Session):
    """Test adding already favorited article."""
    # Add favorite first
    client.post(
        f"/favorites/articles/{test_article.id}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )

    # Try adding again
    response = client.post(
        f"/favorites/articles/{test_article.id}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200
    assert "already favorited" in response.json()["message"]


def test_remove_favorite(client: TestClient, test_user_token: str, test_article):
    """Test removing article from favorites."""
    # Add first
    client.post(
        f"/favorites/articles/{test_article.id}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )

    # Remove
    response = client.delete(
        f"/favorites/articles/{test_article.id}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200


def test_get_favorites(client: TestClient, test_user_token: str, test_article):
    """Test getting user's favorites."""
    # Add favorite
    client.post(
        f"/favorites/articles/{test_article.id}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )

    # Get favorites
    response = client.get(
        "/favorites",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] >= 1
    assert len(data["favorites"]) >= 1


def test_check_favorite(client: TestClient, test_user_token: str, test_article):
    """Test checking if article is favorited."""
    # Check before adding
    response = client.get(
        f"/favorites/check/{test_article.id}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200
    assert response.json()["is_favorited"] is False

    # Add favorite
    client.post(
        f"/favorites/articles/{test_article.id}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )

    # Check after adding
    response = client.get(
        f"/favorites/check/{test_article.id}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200
    assert response.json()["is_favorited"] is True
```

### Frontend Tests (`frontend/src/components/__tests__/FavoriteButton.test.tsx`)

```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import FavoriteButton from '../FavoriteButton';
import { api } from '@/lib/api';

jest.mock('@/lib/api');

describe('FavoriteButton', () => {
  beforeEach(() => {
    localStorage.setItem('token', 'test-token');
  });

  afterEach(() => {
    localStorage.clear();
    jest.clearAllMocks();
  });

  it('should render unfavorited state', () => {
    render(<FavoriteButton articleId={1} />);
    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('title', 'Add to favorites');
  });

  it('should render favorited state', () => {
    render(<FavoriteButton articleId={1} initialFavorited={true} />);
    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('title', 'Remove from favorites');
  });

  it('should toggle favorite on click', async () => {
    (api.addFavorite as jest.Mock).mockResolvedValue({ message: 'Added' });

    render(<FavoriteButton articleId={1} />);
    const button = screen.getByRole('button');

    fireEvent.click(button);

    await waitFor(() => {
      expect(api.addFavorite).toHaveBeenCalledWith(1);
    });
  });

  it('should call onToggle callback', async () => {
    const onToggle = jest.fn();
    (api.addFavorite as jest.Mock).mockResolvedValue({ message: 'Added' });

    render(<FavoriteButton articleId={1} onToggle={onToggle} />);
    const button = screen.getByRole('button');

    fireEvent.click(button);

    await waitFor(() => {
      expect(onToggle).toHaveBeenCalledWith(true);
    });
  });
});
```

---

## 📝 Implementation Checklist

### Backend
- [ ] Create `ArticleFavorite` model in `models.py`
- [ ] Generate Alembic migration
- [ ] Apply migration to database
- [ ] Create `routes/favorites.py` with all endpoints
- [ ] Update `routes/feed.py` to include `is_favorited`
- [ ] Update `routes/articles.py` to include `is_favorited`
- [ ] Register favorites router in `main.py`
- [ ] Write backend tests
- [ ] Run all tests to ensure no regressions

### Frontend
- [ ] Update `api.ts` with favorites methods
- [ ] Create `FavoriteButton` component
- [ ] Update feed page with favorite buttons
- [ ] Update article detail page with favorite button
- [ ] Create favorites page
- [ ] Add favorites link to Navbar
- [ ] Write component tests
- [ ] Test user flows end-to-end

### Documentation
- [ ] Update `CHANGELOG.md`
- [ ] Update `CLAUDE.md` with new features
- [ ] Update `API.md` with favorites endpoints

---

## 🎯 Success Criteria

1. ✅ Users can favorite/unfavorite articles from feed
2. ✅ Users can favorite/unfavorite articles from detail page
3. ✅ Favorited status persists across sessions
4. ✅ Favorites page shows all favorited articles
5. ✅ Unfavoriting from favorites page removes immediately
6. ✅ UI is consistent with existing design system
7. ✅ All tests pass (backend and frontend)
8. ✅ Performance is acceptable (<100ms for favorite toggle)

---

## 🚀 Future Enhancements

1. **Collections**: Group favorites into custom collections/folders
2. **Notes**: Add personal notes to favorited articles
3. **Sharing**: Share favorite collections with other users
4. **Export**: Export favorites as reading list (Pocket, Instapaper format)
5. **Reading Progress**: Track reading progress on long articles
6. **Recommendations**: Recommend articles based on favorites
7. **Analytics**: Show stats on favorited articles (bias distribution, topics)

---

**Estimated Implementation Time**: 2-3 hours
**Priority**: Medium
**Dependencies**: None (standalone feature)
