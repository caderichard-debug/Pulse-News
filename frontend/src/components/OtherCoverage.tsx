"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { useRouter } from "next/navigation";
import { Eye, Globe, TrendingUp, Minus, TrendingDown, ExternalLink, RefreshCw, AlertCircle, EyeOff } from "lucide-react";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/dateUtils";

interface CoverageArticle {
  id: number;
  title: string;
  url: string;
  source_name: string;
  source_bias: string | null;
  source_trust_score: number | null;
  published_at: string;
  sentiment_score: number;
  political_lean: string | null;
  similarity_score: number;
  summary?: string;
  time_diff_hours: number;
  published_later: boolean;
}

interface CoverageData {
  success: boolean;
  coverage_articles: CoverageArticle[];
  coverage_count: number;
  sources_count: number;
  avg_similarity: number;
  bias_distribution: Record<string, number>;
  cluster_id: number | null;
  cluster_topic: string;
  has_cluster: boolean;
  primary_article_id: number;
  filters_applied: {
    bias_filter: string | null;
    sentiment_range: [number, number] | null;
    max_results: number;
  };
}

interface OtherCoverageProps {
  primaryArticleId: number;
  initialCoverage?: any[];
  className?: string;
}

export default function OtherCoverage({ primaryArticleId, initialCoverage = [], className = "" }: OtherCoverageProps) {
  const [expanded, setExpanded] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [coverageData, setCoverageData] = useState<CoverageData | null>(null);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filter states
  const [biasFilter, setBiasFilter] = useState<string>("all");
  const [similarityThreshold, setSimilarityThreshold] = useState<number>(0.3);
  const [maxResults, setMaxResults] = useState(10);

  const router = useRouter();

  const fetchCoverage = useCallback(async (filters: {
    bias_filter?: string;
    similarity_threshold?: number;
    max_results?: number;
  } = {}) => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.getCoverageAnalysis({
        articleId: primaryArticleId,
        biasFilter: filters.bias_filter,
        sentimentRange: undefined, // Always undefined now
        maxResults: filters.max_results
      });
      setCoverageData(response);
    } catch (err) {
      console.error("Error fetching coverage:", err);
      setError("Failed to load coverage data");
    } finally {
      setLoading(false);
    }
  }, [primaryArticleId]);

  const triggerAnalysis = async () => {
    setAnalyzing(true);
    setError(null);

    try {
      await api.triggerCoverageAnalysis(primaryArticleId);

      // After successful analysis, fetch the updated coverage data
      await fetchCoverage({
        bias_filter: biasFilter !== "all" ? biasFilter : undefined,
        similarity_threshold: similarityThreshold,
        max_results: maxResults
      });
    } catch (err) {
      console.error("Error triggering analysis:", err);
      setError("Failed to analyze coverage");
    } finally {
      setAnalyzing(false);
    }
  };

  
  const getBiasColor = (bias: string | null) => {
    switch (bias) {
      case "left": return "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200";
      case "center": return "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200";
      case "right": return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200";
      default: return "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200";
    }
  };

  const getSentimentColor = (score: number) => {
    if (score > 0.3) return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200";
    if (score < -0.3) return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200";
    return "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200";
  };

  const FilterOptions = [
    { value: 'all', label: 'All Sources', icon: Globe },
    { value: 'left', label: 'Left-Leaning', icon: TrendingUp },
    { value: 'center', label: 'Center', icon: Minus },
    { value: 'right', label: 'Right-Leaning', icon: TrendingDown }
  ];

  // Initial load when component expands
  useEffect(() => {
    if (expanded && !coverageData) {
      fetchCoverage();
    }
  }, [expanded, coverageData, fetchCoverage]);

  // Create stable filters object
  const filters = useMemo(() => {
    return {
      bias_filter: biasFilter !== "all" ? biasFilter : undefined,
      similarity_threshold: similarityThreshold,
      max_results: maxResults
    };
  }, [biasFilter, similarityThreshold, maxResults]);

  // Real-time filtering when filters change
  useEffect(() => {
    if (expanded) {
      setLoading(true);
      setError(null);

      const fetchFilteredCoverage = async () => {
        try {
          const response = await api.getCoverageAnalysis({
            articleId: primaryArticleId,
            biasFilter: filters.bias_filter,
            sentimentRange: undefined,
            maxResults: filters.max_results
          });
          setCoverageData(response);
        } catch (err) {
          console.error("Error fetching coverage:", err);
          setError("Failed to load coverage data");
        } finally {
          setLoading(false);
        }
      };

      fetchFilteredCoverage();
    }
  }, [filters, expanded, primaryArticleId]);

  // If not expanded, show collapsed state
  if (!expanded) {
    return (
      <div className={`mt-6 border-2 border-dashed border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-800 rounded-lg p-6 ${className}`}>
        <div className="text-center">
          <Eye className="h-8 w-8 text-gray-400 dark:text-gray-500 mx-auto mb-3" />
          <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-2">
            Other Coverage
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            {initialCoverage.length > 0
              ? `${initialCoverage.length} other sources cover this story. Compare different perspectives and framing.`
              : "No other coverage found yet. Our system can analyze this story to find related coverage."
            }
          </p>
          <button
            onClick={() => setExpanded(true)}
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Eye className="h-4 w-4 mr-2" />
            View Coverage Details
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`mt-6 ${className}`}>
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
        {/* Header */}
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <Eye className="h-6 w-6 text-blue-600" />
              <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                Other Coverage
              </h3>
            </div>
            <button
              onClick={() => setExpanded(false)}
              className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 p-1"
            >
              <EyeOff className="h-4 w-4" />
            </button>
          </div>

          {/* Coverage Summary */}
          {coverageData && (
            <div className="flex flex-wrap gap-4 text-sm text-gray-600 dark:text-gray-400">
              <span>
                <strong>{coverageData.coverage_count}</strong> articles from <strong>{coverageData.sources_count}</strong> sources
              </span>
              {coverageData.avg_similarity > 0 && (
                <span>Avg similarity: <strong>{(coverageData.avg_similarity * 100).toFixed(0)}%</strong></span>
              )}
              <span>Topic: <strong>{coverageData.cluster_topic}</strong></span>
            </div>
          )}

          {/* Filter Toggle */}
          <div className="mt-4">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
            >
              <span>Filters</span>
              <span className={`transform transition-transform ${showFilters ? 'rotate-180' : ''}`}>▼</span>
            </button>
          </div>
        </div>

        {/* Filters Panel */}
        {showFilters && (
          <div className="p-6 bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Bias Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Political Bias
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {FilterOptions.map((option) => {
                    const Icon = option.icon;
                    return (
                      <button
                        key={option.value}
                        onClick={() => setBiasFilter(option.value)}
                        className={`flex items-center gap-2 px-3 py-2 text-sm rounded-lg border transition-colors ${
                          biasFilter === option.value
                            ? 'bg-blue-600 text-white border-blue-600'
                            : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700'
                        }`}
                      >
                        <Icon className="h-4 w-4" />
                        {option.label}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Similarity Threshold */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Similarity Threshold
                </label>
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Loose</span>
                    <input
                      type="range"
                      min="0.1"
                      max="0.9"
                      step="0.1"
                      value={similarityThreshold}
                      onChange={(e) => setSimilarityThreshold(parseFloat(e.target.value))}
                      className="flex-1"
                    />
                    <span className="text-sm text-gray-600 dark:text-gray-400">Strict</span>
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    {(similarityThreshold * 100).toFixed(0)}% similarity minimum
                  </div>
                </div>
              </div>

              {/* Max Results */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Max Results
                </label>
                <select
                  value={maxResults}
                  onChange={(e) => setMaxResults(parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                >
                  <option value={5}>5 articles</option>
                  <option value={10}>10 articles</option>
                  <option value={20}>20 articles</option>
                  <option value={50}>50 articles</option>
                </select>
              </div>
            </div>

            <div className="mt-4 flex justify-end">
              <button
                onClick={() => {
                  setBiasFilter('all');
                  setSimilarityThreshold(0.3);
                  setMaxResults(10);
                }}
                className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
              >
                Reset
              </button>
            </div>
          </div>
        )}

        {/* Content */}
        <div className="p-6">
          {error && (
            <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <div className="flex items-center gap-2 text-red-600 dark:text-red-400">
                <AlertCircle className="h-5 w-5" />
                <span>{error}</span>
              </div>
            </div>
          )}

          {loading && (
            <div className="text-center py-8">
              <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-2" />
              <p className="text-gray-600 dark:text-gray-400">Loading coverage data...</p>
            </div>
          )}

          {!loading && coverageData && coverageData.coverage_count === 0 && (
            <div className="text-center py-8">
              <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h4 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
                No Other Coverage Found
              </h4>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                Our system couldn&apos;t find other articles covering this specific event. Try analyzing this story to find related coverage.
              </p>
              <button
                onClick={triggerAnalysis}
                disabled={analyzing}
                className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                {analyzing ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Analyze for Coverage
                  </>
                )}
              </button>
            </div>
          )}

          {!loading && coverageData && coverageData.coverage_count > 0 && (
            <div className="space-y-4">
              {/* Bias Distribution */}
              {Object.keys(coverageData.bias_distribution).length > 0 && (
                <div className="flex flex-wrap gap-2 mb-4">
                  {Object.entries(coverageData.bias_distribution).map(([bias, count]) => (
                    <span
                      key={bias}
                      className={`px-3 py-1 rounded-full text-sm font-medium ${getBiasColor(bias)}`}
                    >
                      {bias}: {count}
                    </span>
                  ))}
                </div>
              )}

              {/* Coverage Articles */}
              {coverageData.coverage_articles.map((article) => (
                <div
                  key={article.id}
                  className="bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-2 hover:text-blue-600 dark:hover:text-blue-400 cursor-pointer"
                          onClick={() => router.push(`/article/${article.id}`)}>
                        {article.title}
                      </h4>
                      <div className="flex flex-wrap items-center gap-3 text-sm text-gray-600 dark:text-gray-400">
                        <span className="font-medium">{article.source_name}</span>
                        {article.published_later && (
                          <span className="text-green-600 dark:text-green-400">• Published later</span>
                        )}
                        <span>• {formatDate(article.published_at)}</span>
                        <span>• {article.time_diff_hours}h difference</span>
                      </div>
                    </div>
                    <div className="ml-4 flex flex-col gap-2">
                      {/* Source Trust Score */}
                      {article.source_trust_score && (
                        <div className="text-xs">
                          <span className="text-gray-500 dark:text-gray-400">Trust: </span>
                          <span className={`font-medium ${
                            article.source_trust_score >= 8 ? 'text-green-600 dark:text-green-400' :
                            article.source_trust_score >= 6 ? 'text-yellow-600 dark:text-yellow-400' :
                            'text-red-600 dark:text-red-400'
                          }`}>
                            {article.source_trust_score.toFixed(1)}
                          </span>
                        </div>
                      )}

                      {/* Political Bias */}
                      {article.source_bias && (
                        <span className={`px-2 py-1 rounded text-xs font-medium ${getBiasColor(article.source_bias)}`}>
                          {article.source_bias}
                        </span>
                      )}

                      {/* Sentiment Score */}
                      <span className={`px-2 py-1 rounded text-xs font-medium ${getSentimentColor(article.sentiment_score)}`}>
                        {article.sentiment_score > 0 ? '+' : ''}{article.sentiment_score.toFixed(1)}
                      </span>

                      {/* Similarity Score */}
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        {(article.similarity_score * 100).toFixed(0)}% similar
                      </div>
                    </div>
                  </div>

                  {/* Summary */}
                  {article.summary && (
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">
                      {article.summary}
                    </p>
                  )}

                  {/* Actions */}
                  <div className="flex gap-2">
                    <button
                      onClick={() => router.push(`/article/${article.id}`)}
                      className="flex items-center gap-1 px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                    >
                      <Eye className="h-3 w-3" />
                      View in App
                    </button>
                    <a
                      href={article.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                    >
                      <ExternalLink className="h-3 w-3" />
                      View Original
                    </a>
                  </div>
                </div>
              ))}

              {/* Analyze for More Coverage */}
              <div className="text-center pt-4">
                <button
                  onClick={triggerAnalysis}
                  disabled={analyzing}
                  className="inline-flex items-center px-4 py-2 text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 transition-colors"
                >
                  {analyzing ? (
                    <>
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                      Analyzing for more coverage...
                    </>
                  ) : (
                    <>
                      <RefreshCw className="h-4 w-4 mr-2" />
                      Analyze for More Coverage
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}