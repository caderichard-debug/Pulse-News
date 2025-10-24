'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import Navbar from '@/components/Navbar';
import SourceBiasBadge from '@/components/SourceBiasBadge';
import UnverifiedEmailAlert from '@/components/UnverifiedEmailAlert';
import ExtensionBanner from '@/components/ExtensionBanner';
import FavoriteButton from '@/components/FavoriteButton';
import Footer from '@/components/Footer';

// Multi-select component
interface MultiSelectProps<T extends string | number> {
  options: Array<{ value: T; label: string; count?: number }>;
  selected: T[];
  onChange: (selected: T[]) => void;
  placeholder: string;
  className?: string;
}

function MultiSelect<T extends string | number>({ options, selected, onChange, placeholder, className = "" }: MultiSelectProps<T>) {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Filter options based on search
  const filteredOptions = options.filter(option =>
    option.label.toLowerCase().includes(search.toLowerCase())
  );

  // Get display name for selected values
  const getSelectedLabel = (value: T) => {
    const option = options.find(opt => opt.value === value);
    return option ? option.label : value.toString();
  };

  const handleToggle = (value: T) => {
    const newSelected = selected.includes(value)
      ? selected.filter(item => item !== value)
      : [...selected, value];
    onChange(newSelected);
  };

  const handleRemove = (value: T, e: React.MouseEvent) => {
    e.stopPropagation();
    const newSelected = selected.filter(item => item !== value);
    onChange(newSelected);
  };

  const handleClear = () => {
    onChange([]);
  };

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      <div
        className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground cursor-text min-h-[38px] flex items-center gap-1 flex-wrap"
        onClick={() => setIsOpen(true)}
      >
        {selected.length === 0 ? (
          <span className="text-muted-foreground">{placeholder}</span>
        ) : (
          <>
            {selected.map((value) => (
              <span
                key={value.toString()}
                className="inline-flex items-center gap-1 px-2 py-1 bg-primary/10 text-primary rounded text-sm"
              >
                {getSelectedLabel(value)}
                <button
                  onClick={(e) => handleRemove(value, e)}
                  className="hover:text-primary/80"
                >
                  ×
                </button>
              </span>
            ))}
          </>
        )}
      </div>

      {isOpen && (
        <div className="absolute z-10 w-full mt-1 bg-card border border-border rounded-md shadow-lg max-h-60 overflow-hidden">
          {/* Search input */}
          <div className="p-2 border-b border-border">
            <input
              type="text"
              placeholder="Search..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full px-2 py-1 border border-border rounded text-sm bg-background text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
              autoFocus
            />
          </div>

          {/* Clear all button */}
          {selected.length > 0 && (
            <div className="p-2 border-b border-border">
              <button
                onClick={handleClear}
                className="text-sm text-muted-foreground hover:text-foreground"
              >
                Clear all ({selected.length})
              </button>
            </div>
          )}

          {/* Options list */}
          <div className="max-h-48 overflow-y-auto">
            {filteredOptions.length === 0 ? (
              <div className="p-2 text-sm text-muted-foreground">No options found</div>
            ) : (
              filteredOptions.map((option) => {
                const isSelected = selected.includes(option.value);
                return (
                  <label
                    key={option.value.toString()}
                    className="flex items-center gap-2 p-2 hover:bg-secondary cursor-pointer text-sm"
                  >
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => handleToggle(option.value)}
                      className="w-4 h-4 text-primary border-border rounded focus:ring-primary"
                    />
                    <span className="flex-1">{option.label}</span>
                    {option.count !== undefined && (
                      <span className="text-muted-foreground text-xs">({option.count})</span>
                    )}
                  </label>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}

interface Article {
  id: number;
  title: string;
  url: string;
  published_at: string;
  source_name: string;
  source_id: number;
  source_bias: string | null;
  topic_category: string | null;
  summary: string | null;
  sentiment_score: number | null;
  political_lean: string | null;
  primary_framework: string | null;
  framework_position: number | null;
  read_time_minutes: number | null;
  stats_count: number;
  stats_verified_count: number;
  has_stats: boolean;
  is_favorited: boolean;
  has_opposing_viewpoints: boolean;
}

interface FeedResponse {
  articles: Article[];
  total_count: number;
  page: number;
  page_size: number;
}

export default function FeedPage() {
  const router = useRouter();
  const [feedData, setFeedData] = useState<FeedResponse | null>(null);
  const [topics, setTopics] = useState<Array<{ name: string; article_count: number }>>([]);
  const [sources, setSources] = useState<Array<{ id: number; name: string; url: string; article_count: number }>>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load filters from localStorage or use defaults
  const getStoredFilters = () => {
    if (typeof window === 'undefined') return null;
    const stored = localStorage.getItem('feedFilters');
    return stored ? JSON.parse(stored) : null;
  };

  const storedFilters = getStoredFilters();

  // Filters
  const [searchQuery, setSearchQuery] = useState<string>(storedFilters?.searchQuery || '');
  const [selectedTopics, setSelectedTopics] = useState<string[]>(storedFilters?.selectedTopics || []);
  const [selectedSources, setSelectedSources] = useState<number[]>(storedFilters?.selectedSources || []);
  const [selectedLeans, setSelectedLeans] = useState<string[]>(storedFilters?.selectedLeans || []);
  const [dateRange, setDateRange] = useState<string>(storedFilters?.dateRange || '');
  const [sortBy, setSortBy] = useState(storedFilters?.sortBy || 'newest');
  const [onlyAnalyzed, setOnlyAnalyzed] = useState(storedFilters?.onlyAnalyzed ?? true);
  const [onlyVerifiedStats, setOnlyVerifiedStats] = useState(storedFilters?.onlyVerifiedStats ?? false);
  const [favoritesOnly, setFavoritesOnly] = useState(false); // Always default to unchecked
  const [hasOpposingViewpoints, setHasOpposingViewpoints] = useState(storedFilters?.hasOpposingViewpoints ?? false);
  const [page, setPage] = useState(storedFilters?.page || 1);
  const [pageInput, setPageInput] = useState((storedFilters?.page || 1).toString());

  // Save filters AND pagination to localStorage whenever they change
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const filters = {
        searchQuery,
        selectedTopics,
        selectedSources,
        selectedLeans,
        dateRange,
        sortBy,
        onlyAnalyzed,
        onlyVerifiedStats,
        favoritesOnly,
        hasOpposingViewpoints,
        page
      };
      localStorage.setItem('feedFilters', JSON.stringify(filters));
    }
  }, [searchQuery, selectedTopics, selectedSources, selectedLeans, dateRange, sortBy, onlyAnalyzed, onlyVerifiedStats, favoritesOnly, hasOpposingViewpoints, page]);

  const loadFeedData = useCallback(async () => {
    try {
      setLoading(true);
      const data = await api.getFeedArticles({
        page,
        page_size: 20,
        search: searchQuery || undefined,
        topics: selectedTopics.length > 0 ? selectedTopics : undefined,
        source_ids: selectedSources.length > 0 ? selectedSources : undefined,
        political_leans: selectedLeans.length > 0 ? selectedLeans : undefined,
        date_range: dateRange || undefined,
        sort_by: sortBy,
        only_analyzed: onlyAnalyzed,
        only_verified_stats: onlyVerifiedStats,
        favorites_only: favoritesOnly,
        has_opposing_viewpoints: hasOpposingViewpoints,
      });
      setFeedData(data);
      setPageInput(page.toString());
      setError(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load feed';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [page, searchQuery, selectedTopics, selectedSources, selectedLeans, dateRange, sortBy, onlyAnalyzed, onlyVerifiedStats, favoritesOnly, hasOpposingViewpoints]);

  useEffect(() => {
    loadFeedData();
    loadFilters();
  }, [searchQuery, selectedTopics, selectedSources, selectedLeans, dateRange, sortBy, onlyAnalyzed, onlyVerifiedStats, favoritesOnly, hasOpposingViewpoints, page, loadFeedData]);

  async function loadFilters() {
    try {
      const [topicsData, sourcesData] = await Promise.all([
        api.getFeedTopics(),
        api.getFeedSources(),
      ]);
      setTopics(topicsData);
      setSources(sourcesData);
    } catch (err) {
      console.error('Failed to load filters:', err);
    }
  }

  function getSentimentColor(score: number | null): string {
    if (score === null) return 'text-gray-500';
    if (score >= 5) return 'text-green-600';
    if (score >= 0) return 'text-blue-600';
    if (score >= -5) return 'text-orange-600';
    return 'text-red-600';
  }

  function getLeanColor(lean: string | null): string {
    if (!lean) return 'text-gray-500';
    if (lean === 'left') return 'text-blue-600';
    if (lean === 'center') return 'text-purple-600';
    return 'text-red-600';
  }

  function handlePageInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    setPageInput(e.target.value);
  }

  function handlePageInputSubmit(e: React.KeyboardEvent<HTMLInputElement> | React.FocusEvent<HTMLInputElement>) {
    if ('key' in e && e.key !== 'Enter') return;

    const newPage = parseInt(pageInput);
    const maxPage = Math.ceil((feedData?.total_count || 0) / (feedData?.page_size || 20));

    if (!isNaN(newPage) && newPage >= 1 && newPage <= maxPage) {
      setPage(newPage);
    } else {
      // Reset to current page if invalid
      setPageInput(page.toString());
    }
  }

  function formatTimeAgo(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);

    if (diffMinutes < 1) return 'Just now';
    if (diffMinutes < 60) return `${diffMinutes}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)}w ago`;

    // For older articles, show the actual date
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
    });
  }

  if (error && !feedData) {
    return (
      <>
        <Navbar />
        <ExtensionBanner />
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
      <ExtensionBanner />
      <UnverifiedEmailAlert />
      <div className="min-h-screen bg-background">
        <div className="max-w-7xl mx-auto px-4 py-8">
          {/* Header */}
          <div className="bg-card rounded-lg shadow-sm p-6 mb-6">
            <h1 className="text-3xl font-bold text-foreground">Article Feed</h1>
            <p className="text-muted-foreground mt-1">Explore news with AI-powered analysis</p>
          </div>

          {/* Search Bar */}
          <div className="mb-6">
            <input
              type="text"
              placeholder="Search articles by title..."
              value={searchQuery}
              onChange={(e) => { setSearchQuery(e.target.value); setPage(1); }}
              className="w-full px-4 py-3 border border-border rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent bg-background text-foreground placeholder-muted-foreground"
            />
          </div>

          {/* Filters */}
          <div className="bg-card rounded-lg shadow-sm p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-4">
          {/* Topic filter */}
          <div>
            <label className="block text-sm font-medium text-card-foreground mb-1">Topics</label>
            <MultiSelect
              options={topics.map((topic) => ({
                value: topic.name,
                label: topic.name,
                count: topic.article_count
              }))}
              selected={selectedTopics}
              onChange={(topics) => { setSelectedTopics(topics); setPage(1); }}
              placeholder="All Topics"
            />
          </div>

          {/* Source filter */}
          <div>
            <label className="block text-sm font-medium text-card-foreground mb-1">Sources</label>
            <MultiSelect
              options={sources.map((source) => ({
                value: source.id,
                label: source.name,
                count: source.article_count
              }))}
              selected={selectedSources}
              onChange={(sources) => { setSelectedSources(sources); setPage(1); }}
              placeholder="All Sources"
            />
          </div>

          {/* Political lean filter */}
          <div>
            <label className="block text-sm font-medium text-card-foreground mb-1">Political Leans</label>
            <MultiSelect
              options={[
                { value: 'left', label: 'Left' },
                { value: 'center', label: 'Center' },
                { value: 'right', label: 'Right' }
              ]}
              selected={selectedLeans}
              onChange={(leans) => { setSelectedLeans(leans); setPage(1); }}
              placeholder="All Leans"
            />
          </div>

          {/* Date range filter */}
          <div>
            <label className="block text-sm font-medium text-card-foreground mb-1">Date Range</label>
            <select
              value={dateRange}
              onChange={(e) => { setDateRange(e.target.value); setPage(1); }}
              className="w-full px-3 py-2 border border-border rounded-md text-foreground"
            >
              <option value="">All Time</option>
              <option value="today">Today</option>
              <option value="week">Past Week</option>
              <option value="month">Past Month</option>
              <option value="year">Past Year</option>
            </select>
          </div>

          {/* Sort */}
          <div>
            <label className="block text-sm font-medium text-card-foreground mb-1">Sort By</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="w-full px-3 py-2 border border-border rounded-md text-foreground"
            >
              <option value="newest">Newest</option>
              <option value="oldest">Oldest</option>
              <option value="sentiment_high">Most Positive</option>
              <option value="sentiment_low">Most Negative</option>
            </select>
          </div>
            </div>

            {/* Filter checkboxes */}
            <div className="flex flex-wrap items-center gap-6 mb-4">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="only-analyzed"
                  checked={onlyAnalyzed}
                  onChange={(e) => { setOnlyAnalyzed(e.target.checked); setPage(1); }}
                  className="w-4 h-4 text-primary border-border rounded focus:ring-indigo-500"
                />
                <label htmlFor="only-analyzed" className="ml-2 text-sm font-medium text-card-foreground">
                  Show only analyzed articles
                </label>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="only-verified-stats"
                  checked={onlyVerifiedStats}
                  onChange={(e) => { setOnlyVerifiedStats(e.target.checked); setPage(1); }}
                  className="w-4 h-4 text-primary border-border rounded focus:ring-indigo-500"
                />
                <label htmlFor="only-verified-stats" className="ml-2 text-sm font-medium text-card-foreground">
                  Show only articles with verified statistics
                </label>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="favorites-only"
                  checked={favoritesOnly}
                  onChange={(e) => { setFavoritesOnly(e.target.checked); setPage(1); }}
                  className="w-4 h-4 text-primary border-border rounded focus:ring-indigo-500"
                />
                <label htmlFor="favorites-only" className="ml-2 text-sm font-medium text-card-foreground">
                  ⭐ Show only favorite articles
                </label>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="has-opposing-viewpoints"
                  checked={hasOpposingViewpoints}
                  onChange={(e) => { setHasOpposingViewpoints(e.target.checked); setPage(1); }}
                  className="w-4 h-4 text-primary border-border rounded focus:ring-indigo-500"
                />
                <label htmlFor="has-opposing-viewpoints" className="ml-2 text-sm font-medium text-card-foreground">
                  🔄 Show only articles with opposing viewpoint analysis
                </label>
              </div>
            </div>

            {/* Pagination in filter card */}
            {feedData && feedData.total_count > feedData.page_size && (
              <div className="pt-4 border-t border-border">
                <div className="flex justify-center items-center gap-2 flex-wrap">
                  <button
                    onClick={() => setPage(1)}
                    disabled={page === 1}
                    className="px-3 py-1.5 bg-card border border-border rounded-md hover:bg-background disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium text-card-foreground transition-colors"
                  >
                    First
                  </button>
                  <button
                    onClick={() => setPage((p: number) => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="px-3 py-1.5 bg-card border border-border rounded-md hover:bg-background disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium text-card-foreground transition-colors"
                  >
                    Previous
                  </button>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-card-foreground">Page</span>
                    <input
                      type="number"
                      min="1"
                      max={Math.ceil(feedData.total_count / feedData.page_size)}
                      value={pageInput}
                      onChange={handlePageInputChange}
                      onKeyDown={handlePageInputSubmit}
                      onBlur={handlePageInputSubmit}
                      className="w-16 px-2 py-1 border border-border rounded-md text-center text-foreground focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                    <span className="text-sm font-medium text-card-foreground">
                      of {Math.ceil(feedData.total_count / feedData.page_size)}
                    </span>
                  </div>
                  <button
                    onClick={() => setPage((p: number) => p + 1)}
                    disabled={page >= Math.ceil(feedData.total_count / feedData.page_size)}
                    className="px-3 py-1.5 bg-card border border-border rounded-md hover:bg-background disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium text-card-foreground transition-colors"
                  >
                    Next
                  </button>
                  <button
                    onClick={() => setPage(Math.ceil(feedData.total_count / feedData.page_size))}
                    disabled={page >= Math.ceil(feedData.total_count / feedData.page_size)}
                    className="px-3 py-1.5 bg-card border border-border rounded-md hover:bg-background disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium text-card-foreground transition-colors"
                  >
                    Last
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Results count */}
          {feedData && (
            <div className="mb-4 text-sm font-medium text-muted-foreground">
              Showing {((feedData.page - 1) * feedData.page_size) + 1} - {Math.min(feedData.page * feedData.page_size, feedData.total_count)} of {feedData.total_count} articles
            </div>
          )}

          {/* Article list */}
          {loading ? (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
              <p className="mt-4 text-muted-foreground">Loading articles...</p>
            </div>
          ) : feedData && feedData.articles.length > 0 ? (
            <div className="space-y-4">
              {feedData.articles.map((article) => (
                <div
                  key={article.id}
                  className="bg-card rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow border-l-4 border-indigo-500"
                >
                  <div className="flex items-start gap-4">
                    <div
                      className="flex-1 cursor-pointer"
                      onClick={() => router.push(`/article/${article.id}`)}
                    >
                      {/* Header */}
                      <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2 flex-wrap">
                    <span className="font-medium text-primary">{article.source_name}</span>
                    {article.source_bias && (
                      <SourceBiasBadge bias={article.source_bias} size="sm" />
                    )}
                    {article.topic_category && (
                      <>
                        <span>•</span>
                        <span>{article.topic_category}</span>
                      </>
                    )}
                    <span>•</span>
                    <span>{formatTimeAgo(article.published_at)}</span>
                    {article.read_time_minutes && (
                      <>
                        <span>•</span>
                        <span>{article.read_time_minutes} min read</span>
                      </>
                    )}
                  </div>

                  {/* Title */}
                  <h2 className="text-xl font-semibold mb-3 text-foreground hover:text-primary transition-colors">
                    {article.title}
                  </h2>

                  {/* Summary */}
                  {article.summary ? (
                    <p className="text-card-foreground mb-4 line-clamp-2">{article.summary}</p>
                  ) : (
                    <p className="text-muted-foreground italic mb-4 text-sm">Analysis pending...</p>
                  )}

                  {/* Metadata */}
                  <div className="flex flex-wrap items-center gap-4 text-sm">
                    {article.sentiment_score !== null && (
                      <div className="flex items-center gap-1">
                        <span className="text-muted-foreground">Sentiment:</span>
                        <span className={`font-semibold ${getSentimentColor(article.sentiment_score)}`}>
                          {article.sentiment_score > 0 ? '+' : ''}{article.sentiment_score.toFixed(1)}
                        </span>
                      </div>
                    )}

                    {article.political_lean && (
                      <div className="flex items-center gap-1">
                        <span className="text-muted-foreground">Article Bias:</span>
                        <span className={`font-semibold ${getLeanColor(article.political_lean)}`}>
                          {article.political_lean.charAt(0).toUpperCase() + article.political_lean.slice(1)}
                        </span>
                      </div>
                    )}

                    {article.primary_framework && article.framework_position !== null && (
                      <div className="flex items-center gap-1">
                        <span className="text-muted-foreground">Framework:</span>
                        <span className="font-semibold text-purple-600">
                          {article.primary_framework} ({article.framework_position > 0 ? '+' : ''}{article.framework_position})
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Statistics section */}
                  {article.has_stats && (
                    <div className="mt-3 pt-3 border-t border-border">
                      <div className="flex items-center gap-2 text-sm">
                        <span className="text-muted-foreground font-medium">📊 Statistics:</span>
                        <span className="text-card-foreground">
                          {article.stats_count} found
                        </span>
                        {article.stats_verified_count > 0 && (
                          <>
                            <span className="text-gray-400">•</span>
                            <span className="text-green-600 font-medium">
                              {article.stats_verified_count} verified
                            </span>
                          </>
                        )}
                        {article.stats_verified_count === 0 && (
                          <>
                            <span className="text-gray-400">•</span>
                            <span className="text-muted-foreground">
                              none verified
                            </span>
                          </>
                        )}
                      </div>
                    </div>
                  )}
                    </div>

                    <FavoriteButton
                      articleId={article.id}
                      initialFavorited={article.is_favorited}
                      size="sm"
                    />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 bg-card rounded-lg shadow-sm">
              <p className="text-muted-foreground text-lg">No articles found with these filters</p>
              <p className="text-muted-foreground text-sm mt-2">Try adjusting your filters or check back later for new content</p>
            </div>
          )}

          {/* Pagination */}
          {feedData && feedData.total_count > feedData.page_size && (
            <div className="mt-8 flex justify-center items-center gap-2 flex-wrap">
              <button
                onClick={() => setPage(1)}
                disabled={page === 1}
                className="px-4 py-2 bg-card border border-border rounded-md hover:bg-background disabled:opacity-50 disabled:cursor-not-allowed font-medium text-card-foreground transition-colors"
              >
                First
              </button>
              <button
                onClick={() => setPage((p: number) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-4 py-2 bg-card border border-border rounded-md hover:bg-background disabled:opacity-50 disabled:cursor-not-allowed font-medium text-card-foreground transition-colors"
              >
                Previous
              </button>
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-card-foreground">Page</span>
                <input
                  type="number"
                  min="1"
                  max={Math.ceil(feedData.total_count / feedData.page_size)}
                  value={pageInput}
                  onChange={handlePageInputChange}
                  onKeyDown={handlePageInputSubmit}
                  onBlur={handlePageInputSubmit}
                  className="w-16 px-2 py-1 border border-border rounded-md text-center text-foreground focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
                <span className="text-sm font-medium text-card-foreground">
                  of {Math.ceil(feedData.total_count / feedData.page_size)}
                </span>
              </div>
              <button
                onClick={() => setPage((p: number) => p + 1)}
                disabled={page >= Math.ceil(feedData.total_count / feedData.page_size)}
                className="px-4 py-2 bg-card border border-border rounded-md hover:bg-background disabled:opacity-50 disabled:cursor-not-allowed font-medium text-card-foreground transition-colors"
              >
                Next
              </button>
              <button
                onClick={() => setPage(Math.ceil(feedData.total_count / feedData.page_size))}
                disabled={page >= Math.ceil(feedData.total_count / feedData.page_size)}
                className="px-4 py-2 bg-card border border-border rounded-md hover:bg-background disabled:opacity-50 disabled:cursor-not-allowed font-medium text-card-foreground transition-colors"
              >
                Last
              </button>
            </div>
          )}
        </div>
      </div>
      <Footer />
    </>
  );
}
