'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { api } from '@/lib/api';
import Navbar from '@/components/Navbar';

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

  const loadArticle = useCallback(async () => {
    try {
      setLoading(true);
      const data = await api.getArticleDetail(articleId);
      setArticle(data);
      setError(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load article';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [articleId]);

  useEffect(() => {
    if (articleId) {
      loadArticle();
    }
  }, [articleId, loadArticle]);

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
      <>
        <Navbar />
        <div className="min-h-screen bg-gray-50">
          <div className="max-w-4xl mx-auto px-4 py-8 text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
            <p className="mt-4 text-gray-600">Loading article...</p>
          </div>
        </div>
      </>
    );
  }

  if (error || !article) {
    return (
      <>
        <Navbar />
        <div className="min-h-screen bg-gray-50">
          <div className="max-w-4xl mx-auto px-4 py-8">
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
              {error || 'Article not found'}
            </div>
            <button
              onClick={() => router.push('/feed')}
              className="mt-4 text-indigo-600 hover:underline"
            >
              ← Back to feed
            </button>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <Navbar />
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 py-8">
          {/* Back button */}
          <button
            onClick={() => router.push('/feed')}
            className="mb-6 text-indigo-600 hover:underline flex items-center gap-1 transition-colors"
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

      {/* Ethical Framework Analysis */}
      {article.frameworks.length > 0 && (
        <div className="mb-8">
          <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2">
            <span>⚖️</span>
            <span>Ethical Framework Analysis</span>
          </h2>
          <p className="text-gray-600 mb-4">
            This article relates to underlying ethical debates. Understanding these frameworks helps you think critically about the issues.
          </p>
          <div className="space-y-4">
            {article.frameworks.map((fw) => (
              <div key={fw.framework_id} className="bg-gradient-to-br from-purple-600 to-indigo-700 text-white rounded-lg p-6 shadow-lg">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-xl font-semibold">{fw.framework_name}</h3>
                  <span className="text-xs bg-white/20 px-3 py-1 rounded-full">
                    {(fw.relevance_score * 100).toFixed(0)}% relevant
                  </span>
                </div>

                {fw.explanation && (
                  <p className="text-purple-100 mb-4 text-sm leading-relaxed">{fw.explanation}</p>
                )}

                <div className="flex items-center gap-3 text-sm mb-3">
                  <span className="font-medium">{fw.left_position}</span>
                  <div className="flex-1 h-2 bg-white/30 rounded-full relative overflow-hidden">
                    <div
                      className="absolute inset-0 bg-gradient-to-r from-red-400 via-white to-blue-400 opacity-60"
                    ></div>
                    <div
                      className="absolute top-0 h-4 w-4 -mt-1 bg-white rounded-full shadow-lg transform -translate-x-1/2 border-2 border-purple-300"
                      style={{ left: `${((fw.position_on_axis + 10) / 20) * 100}%` }}
                    ></div>
                  </div>
                  <span className="font-medium">{fw.right_position}</span>
                </div>

                <div className="text-center">
                  <span className="inline-block bg-white/20 px-4 py-2 rounded-lg text-lg font-bold">
                    Position: {fw.position_on_axis > 0 ? '+' : ''}{fw.position_on_axis}
                  </span>
                  <p className="text-xs text-purple-200 mt-2">
                    {fw.position_on_axis < -3 ? 'Strongly aligned with ' + fw.left_position :
                     fw.position_on_axis < 0 ? 'Leans toward ' + fw.left_position :
                     fw.position_on_axis === 0 ? 'Balanced perspective' :
                     fw.position_on_axis < 3 ? 'Leans toward ' + fw.right_position :
                     'Strongly aligned with ' + fw.right_position}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Background & Context */}
      {article.context && (
        <div className="mb-8">
          <div className="bg-blue-50 border border-blue-200 rounded-lg overflow-hidden">
            <div className="bg-blue-100 border-b border-blue-200 px-6 py-4">
              <h2 className="text-2xl font-semibold text-blue-900 flex items-center gap-2">
                <span>📚</span>
                <span>Background & Context</span>
              </h2>
            </div>
            <div className="p-6 space-y-6">
              {article.context.background && (
                <div>
                  <h3 className="font-semibold text-blue-900 mb-2 flex items-center gap-2">
                    <span>📖</span>
                    <span>Background</span>
                  </h3>
                  <p className="text-gray-700 leading-relaxed">{article.context.background}</p>
                </div>
              )}
              {article.context.key_players && (
                <div>
                  <h3 className="font-semibold text-blue-900 mb-2 flex items-center gap-2">
                    <span>👥</span>
                    <span>Key Players</span>
                  </h3>
                  {(() => {
                    try {
                      const players = JSON.parse(article.context.key_players);
                      if (Array.isArray(players)) {
                        return (
                          <ul className="list-disc list-inside text-gray-700 leading-relaxed space-y-1">
                            {players.map((player: string, idx: number) => (
                              <li key={idx}>{player}</li>
                            ))}
                          </ul>
                        );
                      }
                    } catch {
                      // Fall back to plain text if not JSON
                    }
                    return <p className="text-gray-700 leading-relaxed">{article.context.key_players}</p>;
                  })()}
                </div>
              )}
              {article.context.timeline && (
                <div>
                  <h3 className="font-semibold text-blue-900 mb-3 flex items-center gap-2">
                    <span>⏱️</span>
                    <span>Timeline</span>
                  </h3>
                  <div className="relative border-l-2 border-blue-300 pl-6 ml-3 space-y-4">
                    {(() => {
                      try {
                        const timelineData = JSON.parse(article.context.timeline);
                        if (Array.isArray(timelineData)) {
                          return timelineData.reverse().map((item: { date: string; event: string }, idx: number) => (
                            <div key={idx} className="relative">
                              <div className="absolute -left-[1.6rem] top-1 w-3 h-3 bg-blue-500 rounded-full border-2 border-blue-50"></div>
                              <p className="text-gray-700 text-sm leading-relaxed">
                                <strong className="text-blue-800">{item.date}:</strong> {item.event}
                              </p>
                            </div>
                          ));
                        }
                      } catch {
                        // Fall back to splitting by newlines if not JSON
                        return article.context.timeline.split('\n').filter(line => line.trim()).reverse().map((event, idx) => (
                          <div key={idx} className="relative">
                            <div className="absolute -left-[1.6rem] top-1 w-3 h-3 bg-blue-500 rounded-full border-2 border-blue-50"></div>
                            <p className="text-gray-700 text-sm leading-relaxed">{event}</p>
                          </div>
                        ));
                      }
                    })()}
                  </div>
                </div>
              )}
              {article.context.significance && (
                <div>
                  <h3 className="font-semibold text-blue-900 mb-2 flex items-center gap-2">
                    <span>💡</span>
                    <span>Why This Matters</span>
                  </h3>
                  <p className="text-gray-700 leading-relaxed">{article.context.significance}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Coverage Comparison */}
      {article.related_articles.length > 0 && (
        <div className="mb-8">
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-6">
            <h2 className="text-2xl font-semibold mb-2 flex items-center gap-2">
              <span>🔗</span>
              <span>Cross-Source Coverage</span>
            </h2>
            <p className="text-sm text-gray-600 mb-4">
              This story is being covered by {article.related_articles.length + 1} sources. Compare how different outlets frame the same story.
            </p>
            <div className="space-y-3">
              {article.related_articles.map((related) => (
                <div
                  key={related.id}
                  className="bg-white border border-purple-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                  onClick={() => router.push(`/article/${related.id}`)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <p className="font-medium text-gray-900 mb-1">{related.title}</p>
                      <p className="text-sm text-gray-600">
                        {related.source_name} • {new Date(related.published_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="ml-4 text-right text-sm flex flex-col gap-1">
                      {related.sentiment_score !== null && (
                        <span className={`px-2 py-1 rounded text-xs font-medium ${getSentimentColor(related.sentiment_score)}`}>
                          {related.sentiment_score > 0 ? '+' : ''}{related.sentiment_score.toFixed(1)}
                        </span>
                      )}
                      {related.political_lean && (
                        <span className={`px-2 py-1 rounded text-xs font-medium ${getLeanColor(related.political_lean)}`}>
                          {related.political_lean}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
        </div>
      </div>
    </>
  );
}
