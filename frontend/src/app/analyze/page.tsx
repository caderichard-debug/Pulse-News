'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import Navbar from '@/components/Navbar';
import SourceBiasBadge from '@/components/SourceBiasBadge';
import { formatDate } from '@/lib/dateUtils';

export default function AnalyzePage() {
  const router = useRouter();
  const [url, setUrl] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState<string>('');

  // Check if user is authenticated
  const isAuthenticated = typeof window !== 'undefined' && !!localStorage.getItem('token');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setAnalysisResult(null);

    // Validate URL
    if (!url.trim()) {
      setError('Please enter a valid URL');
      return;
    }

    try {
      new URL(url); // Validate URL format
    } catch {
      setError('Invalid URL format. Please enter a complete URL (e.g., https://example.com/article)');
      return;
    }

    setIsAnalyzing(true);

    try {
      // Simulate progress steps
      setCurrentStep('Validating URL...');
      await new Promise(resolve => setTimeout(resolve, 300));

      setCurrentStep('Extracting article content...');
      await new Promise(resolve => setTimeout(resolve, 500));

      setCurrentStep('Analyzing with AI...');
      await new Promise(resolve => setTimeout(resolve, 500));

      setCurrentStep('Generating ethical frameworks...');
      await new Promise(resolve => setTimeout(resolve, 500));

      setCurrentStep('Verifying statistics...');
      await new Promise(resolve => setTimeout(resolve, 500));

      setCurrentStep('Generating context...');

      // Make actual API call
      const result = await api.analyzeURL(url);

      setAnalysisResult(result);
      setCurrentStep('Complete!');
    } catch (err: any) {
      setError(err.message || 'Failed to analyze article. Please try again.');
      setCurrentStep('');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleViewArticle = () => {
    if (analysisResult?.article_id) {
      router.push(`/article/${analysisResult.article_id}`);
    }
  };

  const handleAnalyzeAnother = () => {
    setUrl('');
    setAnalysisResult(null);
    setError(null);
    setCurrentStep('');
  };

  // Helper functions matching article detail page
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

  return (
    <>
      <Navbar />
      <div className="min-h-screen bg-background">
        <div className="max-w-4xl mx-auto px-4 py-8">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-foreground mb-4">
              Analyze Any Article
            </h1>
            <p className="text-lg text-muted-foreground">
              Paste any article URL to get instant AI-powered analysis, bias detection,
              fact-checking, and ethical framework mapping.
            </p>
          </div>

          {/* URL Input Form */}
          {!analysisResult && (
            <div className="bg-card border border-border rounded-lg shadow-md p-6 mb-6">
              <form onSubmit={handleSubmit}>
                <div className="mb-4">
                  <label
                    htmlFor="url"
                    className="block text-sm font-medium text-foreground mb-2"
                  >
                    Article URL
                  </label>
                  <input
                    type="text"
                    id="url"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    placeholder="https://example.com/article"
                    className="w-full px-4 py-3 border border-border rounded-lg
                             focus:ring-2 focus:ring-primary focus:border-transparent
                             bg-background text-foreground placeholder-muted-foreground"
                    disabled={isAnalyzing}
                  />
                </div>

                {!isAuthenticated && (
                  <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                    <p className="text-sm text-blue-800">
                      💡 <a href="/login" className="underline font-medium">Log in</a> to save analyzed articles to your feed
                    </p>
                  </div>
                )}

                <button
                  type="submit"
                  disabled={isAnalyzing}
                  className="w-full bg-primary hover:bg-primary/90 disabled:bg-muted
                           text-primary-foreground font-semibold py-3 px-6 rounded-lg transition-colors
                           flex items-center justify-center gap-2"
                >
                  {isAnalyzing ? (
                    <>
                      <div className="inline-block animate-spin rounded-full h-5 w-5 border-b-2 border-primary-foreground"></div>
                      Analyzing...
                    </>
                  ) : (
                    'Analyze Article'
                  )}
                </button>
              </form>

              {/* Progress Indicator */}
              {isAnalyzing && currentStep && (
                <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className="animate-pulse w-2 h-2 bg-blue-600 rounded-full" />
                    <p className="text-sm text-blue-800">{currentStep}</p>
                  </div>
                </div>
              )}

              {/* Error Message */}
              {error && (
                <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              )}
            </div>
          )}

          {/* Analysis Results */}
          {analysisResult?.data && (
            <>
              {/* Success Message */}
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
                <p className="text-green-800 font-medium">
                  ✅ {analysisResult.message}
                </p>
                {analysisResult.data?.already_existed && (
                  <p className="text-green-700 text-sm mt-2">
                    This article was already in our database - showing existing analysis.
                  </p>
                )}
              </div>

              {/* Article Header */}
              <div className="mb-8">
                <div className="flex items-center gap-2 text-sm text-muted-foreground mb-3 flex-wrap">
                  {analysisResult.data.source && (
                    <>
                      <a href={analysisResult.data.source.url || '#'} target="_blank" rel="noopener noreferrer" className="font-medium text-blue-600 hover:underline">
                        {analysisResult.data.source.name}
                      </a>
                      {analysisResult.data.source.organizational_bias && (
                        <SourceBiasBadge bias={analysisResult.data.source.organizational_bias} size="sm" />
                      )}
                    </>
                  )}
                  {analysisResult.data.published_at && (
                    <>
                      <span>•</span>
                      <span>{formatDate(analysisResult.data.published_at)}</span>
                    </>
                  )}
                  {analysisResult.data.author && (
                    <>
                      <span>•</span>
                      <span>By {analysisResult.data.author}</span>
                    </>
                  )}
                </div>

                <h1 className="text-4xl font-bold mb-4 text-foreground">{analysisResult.data.title}</h1>

                <a
                  href={analysisResult.data.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline"
                >
                  Read original article →
                </a>
              </div>

              {/* Sentiment & Bias */}
              <div className="bg-secondary border border-border rounded-lg p-6 mb-8">
                <h2 className="text-lg font-semibold mb-4 text-foreground">Analysis</h2>
                {analysisResult.data.analysis ? (
                  <div className="grid grid-cols-2 gap-4">
                    {analysisResult.data.analysis.sentiment_score !== null && analysisResult.data.analysis.sentiment_score !== undefined && (
                      <div>
                        <p className="text-sm text-muted-foreground mb-1">Sentiment Score</p>
                        <p className={`text-2xl font-bold ${getSentimentColor(analysisResult.data.analysis.sentiment_score)}`}>
                          {analysisResult.data.analysis.sentiment_score > 0 ? '+' : ''}{analysisResult.data.analysis.sentiment_score.toFixed(1)}
                        </p>
                      </div>
                    )}
                    {analysisResult.data.analysis.political_lean && (
                      <div>
                        <p className="text-sm text-muted-foreground mb-1">Article Bias</p>
                        <p className={`text-2xl font-bold ${getLeanColor(analysisResult.data.analysis.political_lean)}`}>
                          {analysisResult.data.analysis.political_lean.charAt(0).toUpperCase() + analysisResult.data.analysis.political_lean.slice(1)}
                        </p>
                        <p className="text-xs text-muted-foreground mt-1">Article-level analysis</p>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-muted-foreground italic text-sm">AI analysis pending... Check back soon for sentiment and bias analysis.</p>
                )}
              </div>

              {/* Summary */}
              {analysisResult.data.analysis?.summary && (
                <div className="mb-8">
                  <h2 className="text-2xl font-semibold mb-3 text-foreground">Summary</h2>
                  <p className="text-card-foreground leading-relaxed">{analysisResult.data.analysis.summary}</p>
                </div>
              )}

              {/* Ethical Framework Analysis */}
              {analysisResult.data.frameworks && analysisResult.data.frameworks.length > 0 && (
                <div className="mb-8">
                  <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2 text-foreground">
                    <span>⚖️</span>
                    <span>Ethical Framework Analysis</span>
                  </h2>
                  <p className="text-muted-foreground mb-4">
                    This article relates to underlying ethical debates. Understanding these frameworks helps you think critically about the issues.
                  </p>
                  <div className="space-y-4">
                    {analysisResult.data.frameworks.map((fw: any) => (
                      <div key={fw.id} className="bg-gradient-to-br from-purple-600 to-indigo-700 text-white rounded-lg p-6 shadow-lg">
                        <div className="flex items-center justify-between mb-3">
                          <h3 className="text-xl font-semibold">{fw.name}</h3>
                          <span className="text-xs bg-card/20 px-3 py-1 rounded-full">
                            {(fw.relevance_score * 100).toFixed(0)}% relevant
                          </span>
                        </div>

                        {fw.ai_explanation && (
                          <p className="text-purple-100 mb-4 text-sm leading-relaxed">{fw.ai_explanation}</p>
                        )}

                        {fw.left_position && fw.right_position && fw.position_on_axis !== null && fw.position_on_axis !== undefined && (
                          <>
                            <div className="flex items-center gap-3 text-sm mb-3">
                              <span className="font-medium">{fw.left_position}</span>
                              <div className="flex-1 h-2 bg-card/30 rounded-full relative overflow-hidden">
                                <div className="absolute inset-0 bg-gradient-to-r from-red-400 via-white to-blue-400 opacity-60"></div>
                                <div
                                  className="absolute top-0 h-4 w-4 -mt-1 bg-card rounded-full shadow-lg transform -translate-x-1/2 border-2 border-purple-300"
                                  style={{ left: `${((fw.position_on_axis + 10) / 20) * 100}%` }}
                                ></div>
                              </div>
                              <span className="font-medium">{fw.right_position}</span>
                            </div>

                            <div className="text-center">
                              <span className="inline-block bg-card/20 px-4 py-2 rounded-lg text-lg font-bold">
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
                          </>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Key Statistics */}
              {analysisResult.data.statistics && analysisResult.data.statistics.length > 0 && (
                <div className="mb-8">
                  <div className="bg-yellow-50 border-l-4 border-yellow-400 rounded-md p-6">
                    <h2 className="text-2xl font-semibold mb-6 text-yellow-900">
                      Key Statistics
                    </h2>

                    <div className="space-y-4">
                      {analysisResult.data.statistics.map((stat: any, idx: number) => (
                        <div key={idx} className="bg-yellow-50/50 rounded-lg p-4 border border-yellow-200">
                          <div className="text-sm text-foreground mb-3 font-medium">
                            {stat.claim_text || stat.statistic}
                          </div>

                          <div className="flex items-center gap-3 text-xs flex-wrap">
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
                              {stat.verification_status === 'unverified' && 'Unverified'}
                            </span>

                            {stat.source_name && (
                              <span>
                                {stat.source_url ? (
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
                                )}
                              </span>
                            )}

                            {stat.confidence !== null && stat.confidence !== undefined && (
                              <span className="text-foreground font-semibold ml-auto">
                                Confidence: {(stat.confidence * 100).toFixed(0)}%
                              </span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Background & Context */}
              {analysisResult.data.context && (
                <div className="mb-8">
                  <div className="bg-blue-50 border border-blue-200 rounded-lg overflow-hidden">
                    <div className="bg-blue-100 border-b border-blue-200 px-6 py-4">
                      <h2 className="text-2xl font-semibold text-blue-900 flex items-center gap-2">
                        <span>📚</span>
                        <span>Background & Context</span>
                      </h2>
                    </div>
                    <div className="p-6 space-y-6">
                      {analysisResult.data.context.background && (
                        <div>
                          <h3 className="font-semibold text-blue-900 mb-2 flex items-center gap-2">
                            <span>📖</span>
                            <span>Background</span>
                          </h3>
                          <p className="text-card-foreground leading-relaxed">{analysisResult.data.context.background}</p>
                        </div>
                      )}
                      {analysisResult.data.context.timeline && (
                        <div>
                          <h3 className="font-semibold text-blue-900 mb-2 flex items-center gap-2">
                            <span>⏱️</span>
                            <span>Timeline</span>
                          </h3>
                          <p className="text-card-foreground leading-relaxed">{analysisResult.data.context.timeline}</p>
                        </div>
                      )}
                      {analysisResult.data.context.significance && (
                        <div>
                          <h3 className="font-semibold text-blue-900 mb-2 flex items-center gap-2">
                            <span>💡</span>
                            <span>Why This Matters</span>
                          </h3>
                          <p className="text-card-foreground leading-relaxed">{analysisResult.data.context.significance}</p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex gap-4">
                <button
                  onClick={handleAnalyzeAnother}
                  className="flex-1 px-6 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors font-medium border border-gray-300"
                >
                  Analyze Another Article
                </button>
                {analysisResult.article_id && (
                  <button
                    onClick={handleViewArticle}
                    className="flex-1 px-6 py-3 bg-primary text-white rounded-lg hover:bg-primary-hover transition-colors font-medium"
                  >
                    View in Feed
                  </button>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
}
