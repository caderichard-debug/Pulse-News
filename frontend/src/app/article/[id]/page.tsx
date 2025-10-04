'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { api } from '@/lib/api';

interface ArticleDetail {
  id: number;
  title: string;
  url: string;
  published_at: string;
  source_name: string;
  source_url: string;
  topic_category: string | null;
  content_preview: string;
  summary: string | null;
  sentiment_score: number | null;
  political_lean: string | null;
  read_time_minutes: number | null;
  statistics: Array<{
    statistic: string;
    verification_status: string;
    confidence: number | null;
    source_name: string | null;
    source_url: string | null;
    source_credibility_score: number | null;
    fact_check_status: string | null;
    fact_check_source: string | null;
  }>;
  frameworks: Array<{
    framework_id: number;
    framework_name: string;
    left_position: string;
    right_position: string;
    position_on_axis: number;
    relevance_score: number;
    explanation: string | null;
  }>;
  related_articles: Array<{
    id: number;
    title: string;
    source_name: string;
    published_at: string;
    sentiment_score: number | null;
    political_lean: string | null;
    url: string;
  }>;
  context: {
    background: string | null;
    key_players: string | null;
    timeline: string | null;
    significance: string | null;
  } | null;
}

export default function ArticleDetailPage() {
  const router = useRouter();
  const params = useParams();
  const articleId = Number(params.id);

  const [article, setArticle] = useState<ArticleDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (articleId) {
      loadArticle();
    }
  }, [articleId]);

  async function loadArticle() {
    try {
      setLoading(true);
      const data = await api.getArticleDetail(articleId);
      setArticle(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load article');
    } finally {
      setLoading(false);
    }
  }

  function getVerificationBadge(status: string) {
    const badges: Record<string, { color: string; text: string; icon: string }> = {
      verified: { color: 'bg-green-100 text-green-800 border-green-300', text: 'Verified', icon: '✓' },
      unverified: { color: 'bg-gray-100 text-gray-800 border-gray-300', text: 'Unverified', icon: '⏳' },
      disputed: { color: 'bg-orange-100 text-orange-800 border-orange-300', text: 'Disputed', icon: '⚠️' },
      false: { color: 'bg-red-100 text-red-800 border-red-300', text: 'False', icon: '❌' },
    };
    const badge = badges[status] || badges.unverified;
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium border ${badge.color}`}>
        <span>{badge.icon}</span>
        {badge.text}
      </span>
    );
  }

  function getCredibilityStars(score: number | null) {
    if (score === null) return null;
    const stars = Math.round(score * 5);
    return '⭐'.repeat(stars);
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

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8 text-center">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <p className="mt-2 text-gray-600">Loading article...</p>
      </div>
    );
  }

  if (error || !article) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          {error || 'Article not found'}
        </div>
        <button
          onClick={() => router.push('/feed')}
          className="mt-4 text-blue-600 hover:underline"
        >
          ← Back to feed
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Back button */}
      <button
        onClick={() => router.push('/feed')}
        className="mb-6 text-blue-600 hover:underline flex items-center gap-1"
      >
        ← Back to feed
      </button>

      {/* Article header */}
      <div className="mb-8">
        <div className="flex items-center gap-2 text-sm text-gray-600 mb-3">
          <a href={article.source_url} target="_blank" rel="noopener noreferrer" className="font-medium text-blue-600 hover:underline">
            {article.source_name}
          </a>
          {article.topic_category && (
            <>
              <span>•</span>
              <span>{article.topic_category}</span>
            </>
          )}
          <span>•</span>
          <span>{new Date(article.published_at).toLocaleDateString()}</span>
          {article.read_time_minutes && (
            <>
              <span>•</span>
              <span>{article.read_time_minutes} min read</span>
            </>
          )}
        </div>

        <h1 className="text-4xl font-bold mb-4 text-gray-900">{article.title}</h1>

        <a
          href={article.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:underline"
        >
          Read original article →
        </a>
      </div>

      {/* Sentiment & Bias */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 mb-8">
        <h2 className="text-lg font-semibold mb-4">Analysis</h2>
        <div className="grid grid-cols-2 gap-4">
          {article.sentiment_score !== null && (
            <div>
              <p className="text-sm text-gray-600 mb-1">Sentiment Score</p>
              <p className={`text-2xl font-bold ${getSentimentColor(article.sentiment_score)}`}>
                {article.sentiment_score > 0 ? '+' : ''}{article.sentiment_score.toFixed(1)}
              </p>
            </div>
          )}
          {article.political_lean && (
            <div>
              <p className="text-sm text-gray-600 mb-1">Political Lean</p>
              <p className={`text-2xl font-bold ${getLeanColor(article.political_lean)}`}>
                {article.political_lean.charAt(0).toUpperCase() + article.political_lean.slice(1)}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Summary */}
      {article.summary && (
        <div className="mb-8">
          <h2 className="text-2xl font-semibold mb-3">Summary</h2>
          <p className="text-gray-700 leading-relaxed">{article.summary}</p>
        </div>
      )}

      {/* Verified Statistics */}
      {article.statistics.length > 0 && (
        <div className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Verified Statistics</h2>
          <div className="space-y-4">
            {article.statistics.map((stat, idx) => (
              <div key={idx} className="bg-white border border-gray-200 rounded-lg p-4">
                <div className="flex items-start justify-between mb-2">
                  <p className="font-medium text-gray-900 flex-1">{stat.statistic}</p>
                  {getVerificationBadge(stat.verification_status)}
                </div>
                {stat.source_name && (
                  <div className="text-sm text-gray-600 mt-2">
                    <span>Source: </span>
                    {stat.source_url ? (
                      <a href={stat.source_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                        {stat.source_name}
                      </a>
                    ) : (
                      <span>{stat.source_name}</span>
                    )}
                    {stat.source_credibility_score !== null && (
                      <span className="ml-2">{getCredibilityStars(stat.source_credibility_score)}</span>
                    )}
                  </div>
                )}
                {stat.confidence !== null && (
                  <div className="text-sm text-gray-600 mt-1">
                    Confidence: {(stat.confidence * 100).toFixed(0)}%
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Framework Positioning */}
      {article.frameworks.length > 0 && (
        <div className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Framework Positioning</h2>
          <div className="space-y-3">
            {article.frameworks.map((fw) => (
              <div key={fw.framework_id} className="bg-white border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold text-gray-900">{fw.framework_name}</h3>
                  <span className="text-sm text-gray-600">
                    Relevance: {(fw.relevance_score * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
                  <span>{fw.left_position}</span>
                  <div className="flex-1 h-2 bg-gray-200 rounded-full relative">
                    <div
                      className="absolute top-0 h-2 w-2 bg-blue-600 rounded-full transform -translate-x-1/2"
                      style={{ left: `${((fw.position_on_axis + 10) / 20) * 100}%` }}
                    ></div>
                  </div>
                  <span>{fw.right_position}</span>
                </div>
                <div className="text-center text-lg font-semibold text-blue-600">
                  {fw.position_on_axis > 0 ? '+' : ''}{fw.position_on_axis}
                </div>
                {fw.explanation && (
                  <p className="text-sm text-gray-700 mt-2">{fw.explanation}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Context */}
      {article.context && (
        <div className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Context</h2>
          <div className="bg-white border border-gray-200 rounded-lg p-6 space-y-4">
            {article.context.background && (
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">Background</h3>
                <p className="text-gray-700">{article.context.background}</p>
              </div>
            )}
            {article.context.key_players && (
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">Key Players</h3>
                <p className="text-gray-700">{article.context.key_players}</p>
              </div>
            )}
            {article.context.timeline && (
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">Timeline</h3>
                <p className="text-gray-700">{article.context.timeline}</p>
              </div>
            )}
            {article.context.significance && (
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">Significance</h3>
                <p className="text-gray-700">{article.context.significance}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Related Articles (Coverage Comparison) */}
      {article.related_articles.length > 0 && (
        <div className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">How Other Sources Covered This Story</h2>
          <div className="space-y-3">
            {article.related_articles.map((related) => (
              <div
                key={related.id}
                className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => router.push(`/article/${related.id}`)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="font-medium text-gray-900 mb-1">{related.title}</p>
                    <p className="text-sm text-gray-600">
                      {related.source_name} • {new Date(related.published_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="ml-4 text-right text-sm">
                    {related.sentiment_score !== null && (
                      <p className={getSentimentColor(related.sentiment_score)}>
                        {related.sentiment_score > 0 ? '+' : ''}{related.sentiment_score.toFixed(1)}
                      </p>
                    )}
                    {related.political_lean && (
                      <p className={getLeanColor(related.political_lean)}>
                        {related.political_lean}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
