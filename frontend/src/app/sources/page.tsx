'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
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
  description: string | null;
  trust_score: number;
  organizational_bias: string | null;
  bias_description: string | null;
  is_active: boolean;
  created_at: string;
  article_count: number;
}

export default function SourcesPage() {
  const router = useRouter();
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [selectedBias, setSelectedBias] = useState<string>('');
  const [sortBy, setSortBy] = useState('name');

  useEffect(() => {
    loadSources();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedBias, sortBy]);

  async function loadSources() {
    try {
      setLoading(true);
      const data = await api.getAllSources({
        bias: selectedBias || undefined,
        active_only: true,
        sort_by: sortBy,
      });
      setSources(data.sources);
      setError(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load sources';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }

  function getTrustScoreColor(score: number): string {
    if (score >= 0.9) return 'text-green-600';
    if (score >= 0.7) return 'text-blue-600';
    if (score >= 0.5) return 'text-yellow-600';
    return 'text-red-600';
  }

  if (error && !sources.length) {
    return (
      <>
        <Navbar />
        <div className="min-h-screen bg-background">
          <div className="max-w-7xl mx-auto px-4 py-8">
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
              {error}
            </div>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <Navbar />
      <UnverifiedEmailAlert />
      <div className="min-h-screen bg-background">
        <div className="max-w-7xl mx-auto px-4 py-8">
          {/* Header */}
          <div className="bg-card rounded-lg shadow-sm p-6 mb-6">
            <h1 className="text-3xl font-bold text-foreground">Supported News Sources</h1>
            <p className="text-muted-foreground mt-1">
              Explore the news sources we monitor and their organizational bias ratings
            </p>
          </div>

          {/* Filters */}
          <div className="bg-card rounded-lg shadow-sm p-6 mb-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Bias filter */}
              <div>
                <label className="block text-sm font-medium text-card-foreground mb-1">
                  Filter by Bias
                </label>
                <select
                  value={selectedBias}
                  onChange={(e) => setSelectedBias(e.target.value)}
                  className="w-full px-3 py-2 border border-border rounded-md text-foreground"
                >
                  <option value="">All Biases</option>
                  <option value="left">Left</option>
                  <option value="center-left">Center-Left</option>
                  <option value="center">Center</option>
                  <option value="center-right">Center-Right</option>
                  <option value="right">Right</option>
                </select>
              </div>

              {/* Sort */}
              <div>
                <label className="block text-sm font-medium text-card-foreground mb-1">
                  Sort By
                </label>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="w-full px-3 py-2 border border-border rounded-md text-foreground"
                >
                  <option value="name">Name (A-Z)</option>
                  <option value="trust_score">Trust Score</option>
                  <option value="article_count">Article Count</option>
                </select>
              </div>
            </div>
          </div>

          {/* Results count */}
          <div className="mb-4 text-sm font-medium text-muted-foreground">
            {sources.length} {sources.length === 1 ? 'source' : 'sources'}
          </div>

          {/* Sources grid */}
          {loading ? (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
              <p className="mt-4 text-muted-foreground">Loading sources...</p>
            </div>
          ) : sources.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {sources.map((source) => (
                <div
                  key={source.id}
                  className="bg-card rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow border border-border"
                >
                  {/* Source header */}
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-foreground mb-1">
                        {source.name}
                      </h3>
                      {source.organizational_bias && (
                        <SourceBiasBadge bias={source.organizational_bias} size="sm" />
                      )}
                    </div>
                  </div>

                  {/* Description */}
                  {source.bias_description && (
                    <p className="text-sm text-muted-foreground mb-4 leading-relaxed">
                      {source.bias_description}
                    </p>
                  )}

                  {/* Details */}
                  <div className="space-y-2 text-sm mb-4">
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Trust Score:</span>
                      <span className={`font-semibold ${getTrustScoreColor(source.trust_score)}`}>
                        {(source.trust_score * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Articles:</span>
                      <span className="font-semibold text-foreground">
                        {source.article_count}
                      </span>
                    </div>
                  </div>

                  {/* Links */}
                  <div className="pt-4 border-t border-border space-y-2">
                    <a
                      href={source.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block text-sm text-blue-600 hover:underline"
                      onClick={(e) => e.stopPropagation()}
                    >
                      Visit website →
                    </a>
                    <button
                      onClick={() => router.push(`/feed?source_id=${source.id}`)}
                      className="block text-sm text-primary hover:underline"
                    >
                      View articles from this source →
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 bg-card rounded-lg shadow-sm">
              <p className="text-muted-foreground text-lg">No sources found with these filters</p>
              <p className="text-muted-foreground text-sm mt-2">
                Try adjusting your filters to see more sources
              </p>
            </div>
          )}

          {/* Info box */}
          <div className="mt-8 bg-blue-50 dark:bg-slate-800 border border-blue-200 dark:border-slate-700 rounded-lg p-6 transition-colors">
            <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-200 mb-2">
              About Source Bias Ratings
            </h3>
            <p className="text-blue-800 dark:text-blue-200 text-sm leading-relaxed mb-3">
              Organizational bias ratings reflect the general editorial perspective of each news
              source. These are separate from our article-level bias analysis, which examines
              individual articles regardless of their source.
            </p>
            <p className="text-blue-800 dark:text-blue-200 text-sm leading-relaxed">
              <strong>Note:</strong> A source&apos;s organizational bias doesn&apos;t mean individual articles
              are biased. Many sources with clear editorial stances still produce objective news reporting.
            </p>
          </div>
        </div>
      </div>
      <Footer />
    </>
  );
}
