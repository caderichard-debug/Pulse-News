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
      const errorMessage = err instanceof Error ? err.message : 'Failed to load favorites';
      if (errorMessage.includes('401')) {
        router.push('/login');
      } else {
        setError(errorMessage);
      }
    } finally {
      setLoading(false);
    }
  }, [router]);

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
      <div className="min-h-screen bg-background transition-colors">
        <div className="max-w-4xl mx-auto px-4 py-8">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-4xl font-bold text-foreground mb-2">
              ⭐ Favorite Articles
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
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
              <p className="text-red-700 dark:text-red-400">{error}</p>
            </div>
          )}

          {/* Empty State */}
          {!loading && !error && favorites.length === 0 && (
            <div className="text-center py-12">
              <svg
                className="mx-auto h-24 w-24 text-amber-400 dark:text-amber-500 mb-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z"
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
