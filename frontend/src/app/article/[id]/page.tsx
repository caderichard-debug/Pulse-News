'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { api } from '@/lib/api';
import { formatDate } from '@/lib/dateUtils';
import Navbar from '@/components/Navbar';
import SourceBiasBadge from '@/components/SourceBiasBadge';
import UnverifiedEmailAlert from '@/components/UnverifiedEmailAlert';

interface ArticleDetail {
  id: number;
  title: string;
  url: string;
  published_at: string;
  source_name: string;
  source_url: string;
  source_bias: string | null;
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
    context?: string | null;
    fact_check_details?: string | null;
    fact_check_url?: string | null;
    verification_notes?: string | null;
    last_checked?: string | null;
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
      <UnverifiedEmailAlert />
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
        <div className="flex items-center gap-2 text-sm text-gray-600 mb-3 flex-wrap">
          <a href={article.source_url} target="_blank" rel="noopener noreferrer" className="font-medium text-blue-600 hover:underline">
            {article.source_name}
          </a>
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
          <span>{formatDate(article.published_at)}</span>
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
      <div className="bg-gray-100 border border-gray-300 rounded-lg p-6 mb-8">
        <h2 className="text-lg font-semibold mb-4 text-gray-900">Analysis</h2>
        {article.sentiment_score !== null || article.political_lean ? (
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
                <p className="text-sm text-gray-600 mb-1">Article Bias</p>
                <p className={`text-2xl font-bold ${getLeanColor(article.political_lean)}`}>
                  {article.political_lean.charAt(0).toUpperCase() + article.political_lean.slice(1)}
                </p>
                <p className="text-xs text-gray-500 mt-1">Article-level analysis</p>
              </div>
            )}
          </div>
        ) : (
          <p className="text-gray-500 italic text-sm">AI analysis pending... Check back soon for sentiment and bias analysis.</p>
        )}
      </div>

      {/* Summary */}
      {article.summary && (
        <div className="mb-8">
          <h2 className="text-2xl font-semibold mb-3 text-gray-900">Summary</h2>
          <p className="text-gray-700 leading-relaxed">{article.summary}</p>
        </div>
      )}

      {/* Ethical Framework Analysis */}
      {article.frameworks.length > 0 && (
        <div className="mb-8">
          <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2 text-gray-900">
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
            <h2 className="text-2xl font-semibold mb-2 flex items-center gap-2 text-gray-900">
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
                        {related.source_name} • {formatDate(related.published_at)}
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

      {/* Key Statistics - Enhanced with newsletter-style design */}
      {article.statistics.length > 0 && (
        <div className="mb-8">
          <div className="bg-yellow-50 border-l-4 border-yellow-400 rounded-md p-6">
            <h2 className="text-2xl font-semibold mb-6 text-yellow-900">
              Key Statistics
            </h2>

            <div className="space-y-4">
              {article.statistics.map((stat, idx) => {
                // Check if this is an unverified stat with no source found
                const noSourceFound = stat.verification_status === 'unverified' &&
                                     !stat.source_name &&
                                     !stat.source_url &&
                                     stat.verification_notes?.includes('No source found');

                return noSourceFound ? (
                  // Compact card for unverified stats with no source
                  <div key={idx} className="bg-gray-50/50 rounded-lg p-3 border border-gray-200">
                    <div className="text-sm text-gray-800 mb-2 font-medium">
                      {stat.statistic}
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium border bg-gray-100 text-gray-800 border-gray-300">
                        Unverified
                      </span>
                      <span className="text-xs text-gray-600 italic">
                        {stat.verification_notes}
                      </span>
                    </div>
                  </div>
                ) : (
                  // Full card for all other stats
                  <div key={idx} className="bg-yellow-50/50 rounded-lg p-4 border border-yellow-200">
                    {/* Statistic text with context inline */}
                    <div className="text-sm text-gray-800 mb-3 font-medium">
                      {stat.statistic}
                      {stat.context && (
                        <span className="text-xs text-gray-600 italic font-normal ml-2">
                          ({stat.context})
                        </span>
                      )}
                    </div>

                    {/* V2 Verification badge - single line with labels */}
                    <div className="flex items-center gap-3 text-xs flex-wrap">
                      {/* Status badge */}
                      <span className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium border ${
                        stat.verification_status === 'verified'
                          ? 'bg-green-100 text-green-800 border-green-300'
                          : stat.verification_status === 'disputed'
                          ? 'bg-orange-100 text-orange-800 border-orange-300'
                          : stat.verification_status === 'false'
                          ? 'bg-red-100 text-red-800 border-red-300'
                          : 'bg-gray-100 text-gray-800 border-gray-300'
                      }`}>
                        {stat.verification_status === 'verified' && 'Verified'}
                        {stat.verification_status === 'disputed' && 'Disputed'}
                        {stat.verification_status === 'false' && 'False'}
                        {stat.verification_status === 'unverified' && (stat.last_checked ? 'Unverified' : 'Pending')}
                      </span>

                      {/* Source name with link */}
                      <span>
                        {stat.source_name ? (
                          stat.source_url ? (
                            <a
                              href={stat.source_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-700 hover:underline"
                            >
                              {stat.source_name}
                            </a>
                          ) : (
                            <span className="text-blue-700">{stat.source_name}</span>
                          )
                        ) : (
                          <span className="text-gray-500 italic">Source not traced</span>
                        )}
                      </span>

                      {/* Credibility rating (numerical) */}
                      {stat.source_credibility_score !== null && (
                        <span className="text-gray-800">
                          Credibility: <strong>{(stat.source_credibility_score * 5).toFixed(1)}/5</strong>
                        </span>
                      )}

                      {/* Confidence percentage with label */}
                      {stat.confidence !== null && (
                        <span className="text-gray-800 font-semibold ml-auto">
                          Confidence: {(stat.confidence * 100).toFixed(0)}%
                        </span>
                      )}
                    </div>

                    {/* Fact-check details (if available) */}
                    {stat.fact_check_details && (
                      <div className="mt-3 p-3 bg-blue-50 border-l-2 border-blue-700 rounded text-xs text-blue-900">
                        <strong>Fact-check:</strong> {stat.fact_check_details.substring(0, 200)}
                        {stat.fact_check_details.length > 200 && '...'}
                        {stat.fact_check_url && (
                          <a
                            href={stat.fact_check_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="ml-2 text-blue-700 underline hover:text-blue-900"
                          >
                            Read more
                          </a>
                        )}
                      </div>
                    )}

                    {/* Verification notes (failure reason) */}
                    {stat.verification_notes && stat.verification_status === 'unverified' && (
                      <div className="mt-2 text-xs text-gray-600 italic">
                        <strong>Note:</strong> {stat.verification_notes}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
        </div>
      </div>
    </>
  );
}
