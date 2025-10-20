'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Image from 'next/image';
import { api } from '@/lib/api';
import Navbar from '@/components/Navbar';
import SourceBiasBadge from '@/components/SourceBiasBadge';
import { formatDate } from '@/lib/dateUtils';
import Footer from '@/components/Footer';

function AnalyzePageContent() {
  const searchParams = useSearchParams();
  const [url, setUrl] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState<string>('');

  // Check if user is authenticated
  const isAuthenticated = typeof window !== 'undefined' && !!localStorage.getItem('token');

  // Check if we're in extension mode (has autoSubmit param)
  const isExtensionMode = searchParams.get('autoSubmit') === 'true';

  // Prefill URL from query params (from Chrome extension)
  useEffect(() => {
    const urlParam = searchParams.get('url');
    if (urlParam) {
      console.log('[Analyze Page] Setting URL from param:', urlParam);
      setUrl(urlParam);

      // Auto-submit if autoSubmit parameter is present
      const autoSubmit = searchParams.get('autoSubmit') === 'true';
      if (autoSubmit && urlParam && !analysisResult && !isAnalyzing) {
        console.log('[Analyze Page] Auto-submitting analysis for:', urlParam);
        // Call analyze directly with the URL parameter to avoid state timing issues
        analyzeArticle(urlParam);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  // Extracted analysis logic for reuse
  const analyzeArticle = async (articleUrl: string) => {
    console.log('[Analyze Page] Starting analysis for URL:', articleUrl);

    // Validate URL
    if (!articleUrl.trim()) {
      setError('Please enter a valid URL');
      return;
    }

    try {
      new URL(articleUrl); // Validate URL format
    } catch (e) {
      console.error('[Analyze Page] Invalid URL format:', articleUrl, e);
      setError('Invalid URL format. Please enter a complete URL (e.g., https://example.com/article)');
      return;
    }

    setIsAnalyzing(true);
    setError(null);
    setAnalysisResult(null);

    try {
      // Make API call first to check if article already exists
      setCurrentStep('Checking article...');
      console.log('[Analyze Page] Calling API with URL:', articleUrl);
      const result = await api.analyzeURL(articleUrl);

      // If article already existed, skip the loading animation
      if (result.data?.already_existed) {
        setAnalysisResult(result);
        setCurrentStep('Complete!');
      } else {
        // Simulate progress steps for new analysis
        setCurrentStep('Extracting article content...');
        await new Promise(resolve => setTimeout(resolve, 500));

        setCurrentStep('Analyzing with AI...');
        await new Promise(resolve => setTimeout(resolve, 500));

        setCurrentStep('Generating ethical frameworks...');
        await new Promise(resolve => setTimeout(resolve, 500));

        setCurrentStep('Verifying statistics...');
        await new Promise(resolve => setTimeout(resolve, 500));

        setCurrentStep('Generating context...');
        await new Promise(resolve => setTimeout(resolve, 500));

        setAnalysisResult(result);
        setCurrentStep('Complete!');
      }

      // Save result to sessionStorage for back button support
      sessionStorage.setItem('analyzeResult', JSON.stringify(result));

      // Debug: Log source data
      console.log('[Analyze Page] Analysis result:', result);
      console.log('[Analyze Page] Source data:', result.data?.source);

    } catch (err: any) {
      setError(err.message || 'Failed to analyze article. Please try again.');
      setCurrentStep('');
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Restore state from sessionStorage on mount (for back button support)
  useEffect(() => {
    const savedResult = sessionStorage.getItem('analyzeResult');
    if (savedResult) {
      try {
        const decoded = JSON.parse(savedResult);
        setAnalysisResult(decoded);
      } catch (e) {
        console.error('Failed to restore analysis result:', e);
        sessionStorage.removeItem('analyzeResult');
      }
    }
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    analyzeArticle(url);
  };

  const handleViewArticle = () => {
    if (analysisResult?.article_id) {
      // Open in new tab (important for Chrome extension iframe usage)
      const url = `${window.location.origin}/article/${analysisResult.article_id}`;
      window.open(url, '_blank', 'noopener,noreferrer');
    }
  };

  const handleAnalyzeAnother = () => {
    if (isExtensionMode) {
      // In extension mode, open analyze page in new tab
      window.open(`${window.location.origin}/analyze`, '_blank', 'noopener,noreferrer');
    } else {
      // Normal behavior: reset form
      setUrl('');
      setAnalysisResult(null);
      setError(null);
      setCurrentStep('');
      // Clear saved result from sessionStorage
      sessionStorage.removeItem('analyzeResult');
    }
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
      {!isExtensionMode && <Navbar />}
      <div className="min-h-screen bg-background">
        <div className="max-w-4xl mx-auto px-4 py-8">
          {/* Extension Mode Header */}
          {isExtensionMode && (
            <div className="mb-6 flex items-center justify-between">
              <button
                onClick={() => window.open(window.location.origin, '_blank', 'noopener,noreferrer')}
                className="flex items-center gap-3 hover:opacity-80 transition-opacity"
              >
                <Image
                  src="/pulse-icon.png"
                  alt="Pulse Logo"
                  width={40}
                  height={40}
                  className="w-10 h-10"
                />
                <h1 className="text-2xl font-bold text-foreground">Pulse AI Analysis</h1>
              </button>

              {/* Refresh Button */}
              {analysisResult && (
                <button
                  onClick={() => analyzeArticle(url)}
                  disabled={isAnalyzing}
                  className="p-2.5 rounded-lg border border-border bg-card hover:bg-secondary
                           transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed
                           hover:shadow-md active:scale-95"
                  title="Refresh analysis"
                  aria-label="Refresh analysis"
                >
                  <svg
                    className={`w-5 h-5 text-foreground ${isAnalyzing ? 'animate-spin' : ''}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                    />
                  </svg>
                </button>
              )}
            </div>
          )}

          {/* Header (only show in non-extension mode) */}
          {!isExtensionMode && (
            <div className="text-center mb-8">
              <h1 className="text-4xl font-bold text-foreground mb-4">
                Analyze Any Article
              </h1>
              <p className="text-lg text-muted-foreground">
                Paste any article URL to get instant AI-powered analysis, bias detection,
                fact-checking, and ethical framework mapping.
              </p>
            </div>
          )}

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
                  <div className="mb-4 p-3 bg-info border border-info rounded-lg">
                    <p className="text-sm text-info">
                      💡 <a href="/login" className="underline font-medium">Log in</a> to save analyzed articles to your feed
                    </p>
                  </div>
                )}

                <button
                  type="submit"
                  disabled={isAnalyzing}
                  className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400
                           text-white font-semibold py-3 px-6 rounded-lg transition-colors
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
                <div className="mt-4 p-4 bg-info border border-info rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className="animate-pulse w-2 h-2 bg-primary rounded-full" />
                    <p className="text-sm text-info">{currentStep}</p>
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
              {/* Success Message with Analyze Another button (hidden in extension mode) */}
              {!isExtensionMode && (
                <div className="bg-success border border-success rounded-lg p-4 mb-6">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <p className="text-success font-medium">
                        ✅ {analysisResult.message}
                      </p>
                      {analysisResult.data?.already_existed && (
                        <p className="text-success-muted text-sm mt-2">
                          This article was already in our database - showing existing analysis.
                        </p>
                      )}
                    </div>
                    <button
                      onClick={handleAnalyzeAnother}
                      className="px-4 py-2 bg-card hover:bg-secondary text-foreground rounded-lg transition-colors font-medium border border-border whitespace-nowrap"
                    >
                      Analyze Another
                    </button>
                  </div>
                </div>
              )}

              {/* Article Header (hidden in extension mode) */}
              {!isExtensionMode && (
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
              )}

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

              {/* Source Analysis - Inline */}
              {analysisResult.data.source && (
                <div className="mb-8">
                  <h2 className="text-2xl font-semibold mb-4 text-foreground">Source Analysis</h2>
                  <div className="bg-card border border-border rounded-lg p-6 space-y-5">
                    {/* Source Name and URL */}
                    <div>
                      <div className="flex items-center gap-2 mb-1 flex-wrap">
                        <h3 className="text-xl font-bold text-foreground">{analysisResult.data.source.name}</h3>
                        {analysisResult.data.source.organizational_bias && (
                          <SourceBiasBadge bias={analysisResult.data.source.organizational_bias} size="sm" />
                        )}
                      </div>
                      <a
                        href={analysisResult.data.source.url || '#'}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
                      >
                        {analysisResult.data.source.url}
                      </a>
                    </div>

                    {/* Organizational Bias */}
                    {analysisResult.data.source.organizational_bias && (
                      <div className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-950/30 dark:to-indigo-950/30 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                        <h4 className="text-sm font-semibold text-foreground mb-2">Organizational Bias</h4>
                        <div className="flex items-center gap-2 mb-3">
                          <SourceBiasBadge bias={analysisResult.data.source.organizational_bias} size="md" />
                          <span className="text-lg font-bold text-foreground capitalize">
                            {analysisResult.data.source.organizational_bias.replace('-', ' ')}
                          </span>
                        </div>
                      </div>
                    )}

                    {/* Trust Score */}
                    {analysisResult.data.source.trust_score !== null && analysisResult.data.source.trust_score !== undefined && (
                      <div>
                        <h4 className="text-sm font-semibold text-foreground mb-2">Trust Score</h4>
                        <div className="flex items-center gap-3">
                          <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-3 overflow-hidden">
                            <div
                              className="h-full bg-gradient-to-r from-blue-500 to-indigo-600 rounded-full transition-all"
                              style={{ width: `${analysisResult.data.source.trust_score * 100}%` }}
                            ></div>
                          </div>
                          <span className="text-xl font-bold text-foreground min-w-[3.5rem]">
                            {(analysisResult.data.source.trust_score * 100).toFixed(0)}%
                          </span>
                        </div>
                        <p className="text-xs text-muted-foreground mt-1.5">
                          Based on credibility, fact-checking record, and editorial standards
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              )}

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
                  <div className="bg-stats-section border-l-4 border-stats-accent rounded-md p-6">
                    <h2 className="text-2xl font-semibold mb-6 text-stats-heading">
                      Key Statistics
                    </h2>

                    <div className="space-y-4">
                      {analysisResult.data.statistics.map((stat: any, idx: number) => (
                        <div key={idx} className="bg-stats-card rounded-lg p-4 border border-stats">
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
                                    className="text-source-link hover:underline"
                                  >
                                    {stat.source_name}
                                  </a>
                                ) : (
                                  <span className="text-source-link">{stat.source_name}</span>
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
                  <div className="bg-context-section border border-context rounded-lg overflow-hidden">
                    <div className="bg-context-header border-b border-context px-6 py-4">
                      <h2 className="text-2xl font-semibold text-context-heading flex items-center gap-2">
                        <span>📚</span>
                        <span>Background & Context</span>
                      </h2>
                    </div>
                    <div className="p-6 space-y-6">
                      {analysisResult.data.context.background && (
                        <div>
                          <h3 className="font-semibold text-context-heading mb-2 flex items-center gap-2">
                            <span>📖</span>
                            <span>Background</span>
                          </h3>
                          <p className="text-card-foreground leading-relaxed">{analysisResult.data.context.background}</p>
                        </div>
                      )}
                      {analysisResult.data.context.timeline && (
                        <div>
                          <h3 className="font-semibold text-context-heading mb-3 flex items-center gap-2">
                            <span>⏱️</span>
                            <span>Timeline</span>
                          </h3>
                          <div className="relative border-l-2 border-context pl-6 ml-3 space-y-4">
                            {(() => {
                              try {
                                const timelineData = JSON.parse(analysisResult.data.context.timeline);
                                if (Array.isArray(timelineData)) {
                                  return timelineData.reverse().map((item: { date: string; event: string }, idx: number) => (
                                    <div key={idx} className="relative">
                                      <div className="absolute -left-[1.6rem] top-1 w-3 h-3 bg-context-timeline-dot rounded-full border-2 border-context-timeline-dot"></div>
                                      <p className="text-card-foreground text-sm leading-relaxed">
                                        <strong className="text-context-body">{item.date}:</strong> {item.event}
                                      </p>
                                    </div>
                                  ));
                                }
                              } catch {
                                // Fall back to splitting by newlines if not JSON
                                return analysisResult.data.context.timeline.split('\n').filter((line: string) => line.trim()).reverse().map((event: string, idx: number) => (
                                  <div key={idx} className="relative">
                                    <div className="absolute -left-[1.6rem] top-1 w-3 h-3 bg-context-timeline-dot rounded-full border-2 border-context-timeline-dot"></div>
                                    <p className="text-card-foreground text-sm leading-relaxed">{event}</p>
                                  </div>
                                ));
                              }
                            })()}
                          </div>
                        </div>
                      )}
                      {analysisResult.data.context.significance && (
                        <div>
                          <h3 className="font-semibold text-context-heading mb-2 flex items-center gap-2">
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
      <Footer />
    </>
  );
}

export default function AnalyzePage() {
  return (
    <Suspense fallback={
      <>
        <Navbar />
        <div className="min-h-screen bg-background">
          <div className="max-w-4xl mx-auto px-4 py-8">
            <div className="text-center">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
              <p className="mt-4 text-muted-foreground">Loading...</p>
            </div>
          </div>
        </div>
      </>
    }>
      <AnalyzePageContent />
    </Suspense>
  );
}
