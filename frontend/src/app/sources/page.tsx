'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { api } from '@/lib/api';
import Navbar from '@/components/Navbar';
import SourceBiasBadge from '@/components/SourceBiasBadge';
import UnverifiedEmailAlert from '@/components/UnverifiedEmailAlert';
import ExtensionBanner from '@/components/ExtensionBanner';
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
  is_recommended: boolean;
  is_active: boolean;
  created_at: string;
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

  // Search and filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCredibility, setSelectedCredibility] = useState<string>('');
  const [selectedBias, setSelectedBias] = useState<string>('');

  // Add source state
  const [articleUrl, setArticleUrl] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadSources();
  // eslint-disable-next-line react-hooks/exhaustive-deps
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

      // Fetch all sources
      const data = await api.getAllSources({});
      const allSources = data.sources || [];

      setRecommendedSources(allSources.filter((s: Source) => s.is_recommended));
      setCommunitySources(allSources.filter((s: Source) => !s.is_recommended));
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
      if (!result.already_existed) {
        handleTabChange('community');
      }
    } catch (err) {
      setMessage({
        type: 'error',
        text: err instanceof Error ? err.message : 'Failed to add source'
      });
    } finally {
      setSubmitting(false);
    }
  };

  // Filter sources by search query and filters
  const filterSources = (sources: Source[]) => {
    let filtered = sources;

    // Filter by search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(source =>
        source.name.toLowerCase().includes(query) ||
        source.url.toLowerCase().includes(query) ||
        source.description?.toLowerCase().includes(query)
      );
    }

    // Filter by credibility (trust score)
    if (selectedCredibility) {
      filtered = filtered.filter(source => {
        const trustScore = source.trust_score * 100;
        switch (selectedCredibility) {
          case 'high':
            return trustScore >= 80;
          case 'medium':
            return trustScore >= 60 && trustScore < 80;
          case 'low':
            return trustScore < 60;
          default:
            return true;
        }
      });
    }

    // Filter by political bias
    if (selectedBias) {
      filtered = filtered.filter(source =>
        source.organizational_bias === selectedBias
      );
    }

    return filtered;
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
      <ExtensionBanner />
      <UnverifiedEmailAlert />
      <div className="min-h-screen bg-background transition-colors">
        <div className="max-w-6xl mx-auto px-4 py-8">
          {/* Header */}
          <div className="bg-card rounded-lg shadow-sm p-6 mb-6">
            <h1 className="text-3xl font-bold text-foreground">Supported News Sources</h1>
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
                      ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400'
                      : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300'
                  }`}
                >
                  ✅ Recommended ({recommendedSources.length})
                </button>
                <button
                  onClick={() => handleTabChange('community')}
                  className={`py-4 px-6 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === 'community'
                      ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400'
                      : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300'
                  }`}
                >
                  🌐 Community ({communitySources.length})
                </button>
                <button
                  onClick={() => handleTabChange('add')}
                  className={`py-4 px-6 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === 'add'
                      ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400'
                      : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300'
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

          {/* Search Bar and Filters (for Recommended and Community tabs) */}
          {(activeTab === 'recommended' || activeTab === 'community') && (
            <div className="mb-6">
              {/* Search Bar */}
              <div className="mb-4">
                <input
                  type="text"
                  placeholder="Search sources by name, URL, or description..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full px-4 py-3 border border-border rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent bg-background text-foreground placeholder-muted-foreground"
                />
              </div>

              {/* Filters */}
              <div className="flex flex-col sm:flex-row gap-4">
                {/* Credibility Filter */}
                <div className="flex-1">
                  <label htmlFor="credibility-filter" className="block text-sm font-medium text-foreground mb-2">
                    Credibility
                  </label>
                  <select
                    id="credibility-filter"
                    value={selectedCredibility}
                    onChange={(e) => setSelectedCredibility(e.target.value)}
                    className="w-full px-4 py-2 border border-border rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent bg-background text-foreground"
                  >
                    <option value="">All Credibility Levels</option>
                    <option value="high">High (80%+)</option>
                    <option value="medium">Medium (60-79%)</option>
                    <option value="low">Low (&lt;60%)</option>
                  </select>
                </div>

                {/* Political Lean Filter */}
                <div className="flex-1">
                  <label htmlFor="bias-filter" className="block text-sm font-medium text-foreground mb-2">
                    Political Lean
                  </label>
                  <select
                    id="bias-filter"
                    value={selectedBias}
                    onChange={(e) => setSelectedBias(e.target.value)}
                    className="w-full px-4 py-2 border border-border rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent bg-background text-foreground"
                  >
                    <option value="">All Political Leans</option>
                    <option value="left">Left</option>
                    <option value="center-left">Center-Left</option>
                    <option value="center">Center</option>
                    <option value="center-right">Center-Right</option>
                    <option value="right">Right</option>
                  </select>
                </div>

                {/* Clear Filters */}
                <div className="flex items-end">
                  <button
                    onClick={() => {
                      setSelectedCredibility('');
                      setSelectedBias('');
                      setSearchQuery('');
                    }}
                    className="px-4 py-2 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80 transition-colors font-medium"
                  >
                    Clear Filters
                  </button>
                </div>
              </div>
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
            <div className="bg-card rounded-lg shadow-sm p-6 border border-border">
              <h2 className="text-xl font-semibold text-foreground mb-4">
                Add a News Source
              </h2>
              <p className="text-sm text-muted-foreground mb-6">
                Paste any article URL from a news source you&apos;d like to add. We&apos;ll automatically discover
                the source&apos;s RSS feed and analyze its credibility and bias.
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
                    <li>We automatically discover the source&apos;s RSS feed</li>
                    <li>AI analyzes the source&apos;s bias, credibility, and description</li>
                    <li>The source appears in the &quot;Community&quot; tab for all users</li>
                    <li>Moderators may promote it to &quot;Recommended&quot; after review</li>
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
      <div className="bg-card rounded-lg shadow-sm p-8 text-center border border-border">
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
