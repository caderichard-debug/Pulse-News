'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import Navbar from '@/components/Navbar';

interface Article {
  id: number;
  title: string;
  url: string;
  published_at: string;
  source_name: string;
  source_id: number;
  topic_category: string | null;
  summary: string | null;
  sentiment_score: number | null;
  political_lean: string | null;
  primary_framework: string | null;
  framework_position: number | null;
  read_time_minutes: number | null;
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

  // Filters
  const [selectedTopic, setSelectedTopic] = useState<string>('');
  const [selectedSource, setSelectedSource] = useState<number | null>(null);
  const [selectedLean, setSelectedLean] = useState<string>('');
  const [sortBy, setSortBy] = useState('newest');
  const [page, setPage] = useState(1);

  useEffect(() => {
    loadFeedData();
    loadFilters();
  }, [selectedTopic, selectedSource, selectedLean, sortBy, page]);

  async function loadFeedData() {
    try {
      setLoading(true);
      const data = await api.getFeedArticles({
        page,
        page_size: 20,
        topic: selectedTopic || undefined,
        source_id: selectedSource || undefined,
        political_lean: selectedLean || undefined,
        sort_by: sortBy,
      });
      setFeedData(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load feed');
    } finally {
      setLoading(false);
    }
  }

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

  function formatTimeAgo(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);

    if (diffHours < 1) return 'Just now';
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  }

  if (error && !feedData) {
    return (
      <>
        <Navbar />
        <div className="min-h-screen bg-gray-50">
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
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 py-8">
          {/* Header */}
          <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
            <h1 className="text-3xl font-bold text-gray-900">📰 Article Feed</h1>
            <p className="text-gray-600 mt-1">Explore news with AI-powered analysis</p>
          </div>

          {/* Filters */}
          <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Topic filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Topic</label>
            <select
              value={selectedTopic}
              onChange={(e) => { setSelectedTopic(e.target.value); setPage(1); }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            >
              <option value="">All Topics</option>
              {topics.map((topic) => (
                <option key={topic.name} value={topic.name}>
                  {topic.name} ({topic.article_count})
                </option>
              ))}
            </select>
          </div>

          {/* Source filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Source</label>
            <select
              value={selectedSource || ''}
              onChange={(e) => { setSelectedSource(e.target.value ? Number(e.target.value) : null); setPage(1); }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            >
              <option value="">All Sources</option>
              {sources.map((source) => (
                <option key={source.id} value={source.id}>
                  {source.name} ({source.article_count})
                </option>
              ))}
            </select>
          </div>

          {/* Political lean filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Political Lean</label>
            <select
              value={selectedLean}
              onChange={(e) => { setSelectedLean(e.target.value); setPage(1); }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            >
              <option value="">All Leans</option>
              <option value="left">Left</option>
              <option value="center">Center</option>
              <option value="right">Right</option>
            </select>
          </div>

          {/* Sort */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Sort By</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            >
              <option value="newest">Newest</option>
              <option value="oldest">Oldest</option>
              <option value="sentiment_high">Most Positive</option>
              <option value="sentiment_low">Most Negative</option>
            </select>
          </div>
            </div>
          </div>

          {/* Results count */}
          {feedData && (
            <div className="mb-4 text-sm font-medium text-gray-600">
              Showing {((feedData.page - 1) * feedData.page_size) + 1} - {Math.min(feedData.page * feedData.page_size, feedData.total_count)} of {feedData.total_count} articles
            </div>
          )}

          {/* Article list */}
          {loading ? (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
              <p className="mt-4 text-gray-600">Loading articles...</p>
            </div>
          ) : feedData && feedData.articles.length > 0 ? (
            <div className="space-y-4">
              {feedData.articles.map((article) => (
                <div
                  key={article.id}
                  className="bg-white rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow cursor-pointer border-l-4 border-indigo-500"
                  onClick={() => router.push(`/article/${article.id}`)}
                >
                  {/* Header */}
                  <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
                    <span className="font-medium text-indigo-600">{article.source_name}</span>
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
                  <h2 className="text-xl font-semibold mb-3 text-gray-900 hover:text-indigo-600 transition-colors">
                    {article.title}
                  </h2>

                  {/* Summary */}
                  {article.summary && (
                    <p className="text-gray-700 mb-4 line-clamp-2">{article.summary}</p>
                  )}

                  {/* Metadata */}
                  <div className="flex flex-wrap items-center gap-4 text-sm">
                    {article.sentiment_score !== null && (
                      <div className="flex items-center gap-1">
                        <span className="text-gray-600">Sentiment:</span>
                        <span className={`font-semibold ${getSentimentColor(article.sentiment_score)}`}>
                          {article.sentiment_score > 0 ? '+' : ''}{article.sentiment_score.toFixed(1)}
                        </span>
                      </div>
                    )}

                    {article.political_lean && (
                      <div className="flex items-center gap-1">
                        <span className="text-gray-600">Lean:</span>
                        <span className={`font-semibold ${getLeanColor(article.political_lean)}`}>
                          {article.political_lean.charAt(0).toUpperCase() + article.political_lean.slice(1)}
                        </span>
                      </div>
                    )}

                    {article.primary_framework && (
                      <div className="flex items-center gap-1">
                        <span className="text-gray-600">Framework:</span>
                        <span className="font-semibold text-purple-600">
                          {article.primary_framework} ({article.framework_position > 0 ? '+' : ''}{article.framework_position})
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 bg-white rounded-lg shadow-sm">
              <p className="text-gray-600 text-lg">No articles found with these filters</p>
              <p className="text-gray-500 text-sm mt-2">Try adjusting your filters or check back later for new content</p>
            </div>
          )}

          {/* Pagination */}
          {feedData && feedData.total_count > feedData.page_size && (
            <div className="mt-8 flex justify-center items-center gap-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-4 py-2 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed font-medium text-gray-700 transition-colors"
              >
                Previous
              </button>
              <span className="px-4 py-2 text-sm font-medium text-gray-700">
                Page {page} of {Math.ceil(feedData.total_count / feedData.page_size)}
              </span>
              <button
                onClick={() => setPage(p => p + 1)}
                disabled={page >= Math.ceil(feedData.total_count / feedData.page_size)}
                className="px-4 py-2 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed font-medium text-gray-700 transition-colors"
              >
                Next
              </button>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
