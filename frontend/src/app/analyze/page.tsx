'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';

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

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
            Analyze Any Article
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-400">
            Paste any article URL to get instant AI-powered analysis, bias detection,
            fact-checking, and ethical framework mapping.
          </p>
        </div>

        {/* URL Input Form */}
        {!analysisResult && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-6">
            <form onSubmit={handleSubmit}>
              <div className="mb-4">
                <label
                  htmlFor="url"
                  className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
                >
                  Article URL
                </label>
                <input
                  type="text"
                  id="url"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://example.com/article"
                  className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg
                           focus:ring-2 focus:ring-blue-500 focus:border-transparent
                           dark:bg-gray-700 dark:text-white placeholder-gray-400 dark:placeholder-gray-500"
                  disabled={isAnalyzing}
                />
              </div>

              {!isAuthenticated && (
                <div className="mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200
                              dark:border-blue-800 rounded-lg">
                  <p className="text-sm text-blue-800 dark:text-blue-200">
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
                    <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                        fill="none"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                    Analyzing...
                  </>
                ) : (
                  'Analyze Article'
                )}
              </button>
            </form>

            {/* Progress Indicator */}
            {isAnalyzing && currentStep && (
              <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="animate-pulse w-2 h-2 bg-blue-600 rounded-full" />
                  <p className="text-sm text-blue-800 dark:text-blue-200">{currentStep}</p>
                </div>
              </div>
            )}

            {/* Error Message */}
            {error && (
              <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200
                            dark:border-red-800 rounded-lg">
                <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
              </div>
            )}
          </div>
        )}

        {/* Analysis Results */}
        {analysisResult?.data && (
          <div className="space-y-6">
            {/* Success Message */}
            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200
                          dark:border-green-800 rounded-lg p-4">
              <p className="text-green-800 dark:text-green-200 font-medium">
                ✅ {analysisResult.message}
              </p>
            </div>

            {/* Article Header */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                {analysisResult.data.title}
              </h2>
              {analysisResult.data.author && (
                <p className="text-gray-600 dark:text-gray-400 mb-2">
                  By {analysisResult.data.author}
                </p>
              )}
              {analysisResult.data.source && (
                <p className="text-sm text-gray-500 dark:text-gray-500 mb-4">
                  Source: {analysisResult.data.source.name}
                </p>
              )}
              <a
                href={analysisResult.data.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline text-sm"
              >
                View original article →
              </a>
            </div>

            {/* AI Analysis */}
            {analysisResult.data.analysis && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                  AI Analysis
                </h3>
                <div className="space-y-4">
                  <div>
                    <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-2">
                      Summary
                    </h4>
                    <p className="text-gray-600 dark:text-gray-400">
                      {analysisResult.data.analysis.summary}
                    </p>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-2">
                        Sentiment Score
                      </h4>
                      <div className="flex items-center gap-2">
                        <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full"
                            style={{
                              width: `${((analysisResult.data.analysis.sentiment_score + 1) / 2) * 100}%`,
                            }}
                          />
                        </div>
                        <span className="text-sm text-gray-600 dark:text-gray-400">
                          {analysisResult.data.analysis.sentiment_score.toFixed(2)}
                        </span>
                      </div>
                    </div>
                    {analysisResult.data.analysis.political_lean && (
                      <div>
                        <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-2">
                          Political Lean
                        </h4>
                        <span className="inline-block px-3 py-1 bg-gray-100 dark:bg-gray-700 rounded-full text-sm">
                          {analysisResult.data.analysis.political_lean}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Ethical Frameworks */}
            {analysisResult.data.frameworks && analysisResult.data.frameworks.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                  Ethical Frameworks
                </h3>
                <div className="space-y-3">
                  {analysisResult.data.frameworks.map((framework: any) => (
                    <div
                      key={framework.id}
                      className="border border-gray-200 dark:border-gray-700 rounded-lg p-4"
                    >
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="font-semibold text-gray-900 dark:text-white">
                          {framework.name}
                        </h4>
                        <span className="text-sm text-gray-500 dark:text-gray-400">
                          Relevance: {(framework.relevance_score * 100).toFixed(0)}%
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                        {framework.ai_explanation}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Statistics Verification */}
            {analysisResult.data.statistics && analysisResult.data.statistics.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                  Verified Statistics
                </h3>
                <div className="space-y-3">
                  {analysisResult.data.statistics.map((stat: any) => (
                    <div
                      key={stat.id}
                      className="border border-gray-200 dark:border-gray-700 rounded-lg p-4"
                    >
                      <div className="flex justify-between items-start mb-2">
                        <p className="text-gray-900 dark:text-white">{stat.claim_text}</p>
                        <span
                          className={`text-sm px-2 py-1 rounded ${
                            stat.verification_status === 'verified'
                              ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-200'
                              : stat.verification_status === 'disputed'
                              ? 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-200'
                              : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-200'
                          }`}
                        >
                          {stat.verification_status}
                        </span>
                      </div>
                      {stat.source_url && (
                        <a
                          href={stat.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm text-blue-600 hover:underline"
                        >
                          View source →
                        </a>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Context */}
            {analysisResult.data.context && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                  Context & Background
                </h3>
                <div className="space-y-4">
                  {analysisResult.data.context.background && (
                    <div>
                      <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-2">
                        Background
                      </h4>
                      <p className="text-gray-600 dark:text-gray-400">
                        {analysisResult.data.context.background}
                      </p>
                    </div>
                  )}
                  {analysisResult.data.context.timeline && (
                    <div>
                      <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-2">
                        Timeline
                      </h4>
                      <p className="text-gray-600 dark:text-gray-400">
                        {analysisResult.data.context.timeline}
                      </p>
                    </div>
                  )}
                  {analysisResult.data.context.significance && (
                    <div>
                      <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-2">
                        Significance
                      </h4>
                      <p className="text-gray-600 dark:text-gray-400">
                        {analysisResult.data.context.significance}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-4">
              <button
                onClick={handleAnalyzeAnother}
                className="flex-1 bg-gray-600 hover:bg-gray-700 text-white font-semibold
                         py-3 px-6 rounded-lg transition-colors"
              >
                Analyze Another Article
              </button>
              {analysisResult.article_id && (
                <button
                  onClick={handleViewArticle}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-semibold
                           py-3 px-6 rounded-lg transition-colors"
                >
                  View in Feed
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
