'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowRight, Eye, EyeOff, RefreshCw, Filter, X } from 'lucide-react'
import { api } from '@/lib/api'

interface OpposingViewpoint {
  article_id: number
  title: string
  url: string
  source_name: string
  source_bias?: string
  published_at: string
  sentiment_score?: number
  political_lean?: string
  summary?: string
  relationship_type: string
  opposition_strength: number
  reasoning: string
  ai_explanation?: string
  quality_score?: number
  framework_name?: string
  primary_position?: number
  opposing_position?: number
}

interface OpposingViewpointsResponse {
  primary_article_id: number
  opposing_viewpoints: OpposingViewpoint[]
  total_found: number
  relationship_types_available: string[]
}

interface OpposingViewpointsProps {
  articleId: number
}

export function OpposingViewpoints({ articleId }: OpposingViewpointsProps) {
  const router = useRouter()
  const [viewpoints, setViewpoints] = useState<OpposingViewpoint[]>([])
  const [loading, setLoading] = useState(false)
  const [expanded, setExpanded] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedRelationshipType, setSelectedRelationshipType] = useState<string | null>(null)
  const [showFilters, setShowFilters] = useState(false)
  const [response, setResponse] = useState<OpposingViewpointsResponse | null>(null)
  const [hasTriedAnalysis, setHasTriedAnalysis] = useState(false)
  const [analysisCount, setAnalysisCount] = useState(0)

  const handleViewInFeed = (articleId: number) => {
    router.push(`/article/${articleId}`)
  }

  const relationshipTypes = [
    { value: 'framework_opposition', label: 'Framework Opposition', description: 'Opposite positions on ethical frameworks' },
    { value: 'source_bias', label: 'Source Bias Contrast', description: 'Different source perspectives' },
    { value: 'sentiment_contrast', label: 'Emotional Tone Contrast', description: 'Different emotional tones' },
    { value: 'temporal_evolution', label: 'Coverage Evolution', description: 'How coverage evolved over time' }
  ]

  useEffect(() => {
    if (expanded && articleId) {
      fetchViewpoints()
    }
  }, [expanded, articleId, selectedRelationshipType])

  const fetchViewpoints = async () => {
    setLoading(true)
    setError(null)
    setHasTriedAnalysis(true)

    try {
      const response = await api.getOpposingViewpoints(articleId, {
        relationshipTypes: selectedRelationshipType ? [selectedRelationshipType] : undefined,
        maxResults: 5
      })
      setResponse(response)

      // Filter viewpoints if a specific type is selected
      let filteredViewpoints = response.opposing_viewpoints
      if (selectedRelationshipType) {
        filteredViewpoints = response.opposing_viewpoints.filter(
          vp => vp.relationship_type === selectedRelationshipType
        )
      }

      setViewpoints(filteredViewpoints)
    } catch (err: any) {
      if (err.detail?.includes('OpenAI API is unavailable')) {
        setError('Cannot complete this request right now. OpenAI API is unavailable.')
      } else if (err.detail?.includes('rate limited')) {
        setError('We are being rate limited by OpenAI. Contact support.')
      } else {
        setError('Failed to load opposing viewpoints')
      }
      console.error('Error fetching viewpoints:', err)
    } finally {
      setLoading(false)
    }
  }

  const triggerOnDemandAnalysis = async () => {
    setLoading(true)
    setError(null)

    try {
      // Trigger the backend analysis job
      const analysisResponse = await api.triggerViewpointAnalysis(articleId)
      console.log('Analysis triggered:', analysisResponse)

      // After triggering, wait a moment then check for results
      await new Promise(resolve => setTimeout(resolve, 2000)) // 2 second delay

      // Fetch the updated results
      const response = await api.getOpposingViewpoints(articleId, {
        relationshipTypes: selectedRelationshipType ? [selectedRelationshipType] : undefined,
        maxResults: 10 // Increased max results for analysis
      })
      setResponse(response)

      let filteredViewpoints = response.opposing_viewpoints
      if (selectedRelationshipType) {
        filteredViewpoints = response.opposing_viewpoints.filter(
          vp => vp.relationship_type === selectedRelationshipType
        )
      }

      setViewpoints(filteredViewpoints)
      setHasTriedAnalysis(true)
      setAnalysisCount(prev => prev + 1)

      // If no results after analysis, that's okay - some articles genuinely don't have opposing viewpoints
      if (filteredViewpoints.length === 0) {
        console.log('No opposing viewpoints found after analysis')
      }

    } catch (err: any) {
      if (err.detail?.includes('OpenAI API is unavailable')) {
        setError('Cannot complete analysis right now. OpenAI API is unavailable.')
      } else if (err.detail?.includes('rate limited')) {
        setError('Analysis temporarily unavailable due to rate limiting. Please try again later.')
      } else if (err.detail?.includes('Article not found')) {
        setError('Article not found. Please refresh the page.')
      } else {
        setError('Failed to analyze article for opposing viewpoints')
      }
      console.error('Error triggering analysis:', err)
    } finally {
      setLoading(false)
    }
  }

  const getRelationshipIcon = (type: string) => {
    switch (type) {
      case 'framework_opposition':
        return '⚖️'
      case 'source_bias':
        return '📰'
      case 'sentiment_contrast':
        return '😊😔'
      case 'temporal_evolution':
        return '⏰'
      default:
        return '🔄'
    }
  }

  const getRelationshipLabel = (type: string, frameworkName?: string) => {
    if (type === 'framework_opposition' && frameworkName) {
      return `Framework Opposition: ${frameworkName}`
    }
    const relationship = relationshipTypes.find(rt => rt.value === type)
    return relationship?.label || 'Different Perspective'
  }

  const getSentimentEmoji = (score?: number) => {
    if (!score) return '😐'
    if (score > 5) return '😊'
    if (score > 0) return '🙂'
    if (score < -5) return '😔'
    return '😐'
  }

  const getOppositionStrengthColor = (strength: number) => {
    if (strength > 0.8) return 'bg-red-100 border border-red-200 text-red-800 dark:bg-red-900 dark:border-red-700 dark:text-red-200'
    if (strength > 0.6) return 'bg-orange-100 border border-orange-200 text-orange-800 dark:bg-orange-900 dark:border-orange-700 dark:text-orange-200'
    return 'bg-yellow-100 border border-yellow-200 text-yellow-800 dark:bg-yellow-900 dark:border-yellow-700 dark:text-yellow-200'
  }

  const getSourceBiasColor = (bias?: string) => {
    switch (bias) {
      case 'left':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
      case 'center-left':
        return 'bg-sky-100 text-sky-800 dark:bg-sky-900 dark:text-sky-200'
      case 'center':
        return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
      case 'center-right':
        return 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200'
      case 'right':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
    }
  }

  const getFrameworkPositionVisual = (position?: number) => {
    if (!position) return null

    const normalizedPosition = ((position + 10) / 20) * 100 // Convert -10 to 10 range to 0-100%
    const isLeft = position < 0

    return (
      <div className="flex items-center space-x-2 mt-2">
        <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2 relative">
          <div
            className={`absolute top-0 h-2 rounded-full ${
              isLeft ? 'bg-blue-500' : 'bg-red-500'
            }`}
            style={{
              left: isLeft ? `${normalizedPosition}%` : '0%',
              width: isLeft ? `${100 - normalizedPosition}%` : `${normalizedPosition}%`
            }}
          />
          <div
            className="absolute top-1/2 w-3 h-3 bg-white border-2 border-gray-800 rounded-full"
            style={{ left: `${normalizedPosition}%`, transform: 'translate(-50%, -50%)' }}
          />
        </div>
        <span className="text-xs text-gray-600 dark:text-gray-400 w-12 text-right">
          {position > 0 ? '+' : ''}{position}
        </span>
      </div>
    )
  }

  if (!expanded) {
    return (
      <div className="mt-6 border-2 border-dashed border-gray-300 bg-gray-50 dark:border-gray-600 dark:bg-gray-800 rounded-lg p-6">
        <div className="text-center">
          <div className="flex justify-center mb-3">
            <RefreshCw className="h-8 w-8 text-gray-400 dark:text-gray-500" />
          </div>
          <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-2">
            Explore Different Perspectives
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-4 max-w-md mx-auto">
            See how other news sources are covering this story from different angles
          </p>
          <button
            onClick={() => setExpanded(true)}
            className="bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 px-4 py-2 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors flex items-center mx-auto"
          >
            <Eye className="h-4 w-4 mr-2" />
            View Opposing Viewpoints
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="mt-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <RefreshCw className="h-5 w-5 text-blue-600" />
          <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100">Opposing Viewpoints</h3>
          {viewpoints.length > 0 && (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
              {viewpoints.length} perspectives
            </span>
          )}
        </div>
        <div className="flex items-center space-x-2">
          {response && response.relationship_types_available.length > 1 && (
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
            >
              <Filter className="h-4 w-4 mr-1" />
              Filter
            </button>
          )}
          <button
            onClick={() => setExpanded(false)}
            className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
          >
            <EyeOff className="h-4 w-4 mr-1" />
            Hide
          </button>
        </div>
      </div>

      {/* Filters */}
      {showFilters && response && (
        <div className="mb-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-semibold text-blue-900 dark:text-blue-100">Filter by Relationship Type</h4>
            <button
              onClick={() => setShowFilters(false)}
              className="p-2 text-blue-700 dark:text-blue-300 hover:text-blue-900 dark:hover:text-blue-100 transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
          <div className="flex flex-wrap gap-2 mb-3">
            {relationshipTypes
              .filter(rt => response.relationship_types_available.includes(rt.value))
              .map(rt => (
                <button
                  key={rt.value}
                  onClick={() => setSelectedRelationshipType(
                    selectedRelationshipType === rt.value ? null : rt.value
                  )}
                  className={`px-3 py-1.5 text-xs rounded-md transition-colors ${
                    selectedRelationshipType === rt.value
                      ? 'bg-blue-600 text-white dark:bg-blue-500'
                      : 'bg-white text-gray-700 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600'
                  }`}
                >
                  <span className="mr-1">{getRelationshipIcon(rt.value)}</span>
                  {rt.label}
                </button>
              ))}
          </div>
          {selectedRelationshipType && (
            <p className="text-xs text-blue-700 dark:text-blue-300">
              Showing: {relationshipTypes.find(rt => rt.value === selectedRelationshipType)?.description}
            </p>
          )}
        </div>
      )}

      {error && (
        <div className="mb-4 border border-red-200 bg-red-50 dark:bg-red-900/20 dark:border-red-800 rounded-lg p-4">
          <p className="text-red-700 dark:text-red-300">{error}</p>
        </div>
      )}

      {loading ? (
        <div className="text-center py-8">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-2" />
          <p className="text-gray-600 dark:text-gray-400">Analyzing perspectives...</p>
        </div>
      ) : viewpoints.length > 0 ? (
        <div className="space-y-4">
          {viewpoints.map((viewpoint, index) => (
            <div key={`${viewpoint.article_id}-${index}`} className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
              <div className="p-4 pb-3 border-l-4 border-l-blue-500">
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="text-lg">{getRelationshipIcon(viewpoint.relationship_type)}</span>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-1">{getRelationshipLabel(viewpoint.relationship_type, viewpoint.framework_name)}</h3>
                      <div className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400">
                        <span>{viewpoint.source_name}</span>
                        {viewpoint.source_bias && (
                          <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs ${getSourceBiasColor(viewpoint.source_bias)}`}>
                            {viewpoint.source_bias}
                          </span>
                        )}
                        <span>•</span>
                        <span className="text-xs">
                          {new Date(viewpoint.published_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getOppositionStrengthColor(viewpoint.opposition_strength)}`}>
                      {Math.round(viewpoint.opposition_strength * 100)}% different
                    </span>
                    {viewpoint.sentiment_score !== undefined && (
                      <div className="flex items-center space-x-1 bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded">
                        <span>{getSentimentEmoji(viewpoint.sentiment_score)}</span>
                        <span className="text-xs">{viewpoint.sentiment_score}</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
              <div className="p-4 space-y-3">
                <div>
                  <button
                    onClick={() => handleViewInFeed(viewpoint.article_id)}
                    className="font-semibold text-gray-900 dark:text-gray-100 mb-1 text-left hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                  >
                    {viewpoint.title}
                  </button>
                  {viewpoint.summary && (
                    <p className="text-gray-600 dark:text-gray-400 text-sm mb-2">{viewpoint.summary}</p>
                  )}
                </div>

                {/* Framework position visualization */}
                {viewpoint.relationship_type === 'framework_opposition' && viewpoint.framework_name && (
                  <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded p-3">
                    <div className="flex items-center justify-between mb-2">
                      <h5 className="font-medium text-blue-900 dark:text-blue-100">
                        {viewpoint.framework_name}
                      </h5>
                      {viewpoint.quality_score && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs border border-blue-200 text-blue-700 dark:text-blue-300">
                          Quality: {Math.round(viewpoint.quality_score * 100)}%
                        </span>
                      )}
                    </div>
                    <div className="grid grid-cols-2 gap-4 text-xs">
                      <div>
                        <span className="text-gray-600 dark:text-gray-400">Position Gap:</span>
                        <div className="font-medium">
                          {viewpoint.primary_position} vs {viewpoint.opposing_position}
                        </div>
                      </div>
                    </div>
                    {getFrameworkPositionVisual(viewpoint.opposing_position)}
                  </div>
                )}

                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded p-3">
                  <p className="text-sm text-blue-800 dark:text-blue-200">
                    <strong>Why this opposes:</strong> {viewpoint.ai_explanation || viewpoint.reasoning}
                  </p>
                </div>

                <div className="flex justify-between items-center pt-2">
                  <div className="text-xs text-gray-500 dark:text-gray-400 max-w-[60%]">
                    {viewpoint.ai_explanation || viewpoint.reasoning}
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleViewInFeed(viewpoint.article_id)}
                      className="flex items-center space-x-1 border border-blue-300 dark:border-blue-600 px-3 py-1.5 rounded text-sm text-blue-700 dark:text-blue-300 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
                    >
                      View in Feed
                    </button>
                    <button
                      onClick={() => window.open(viewpoint.url, '_blank')}
                      className="flex items-center space-x-1 border border-gray-300 dark:border-gray-600 px-3 py-1.5 rounded text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
                    >
                      Read Original
                      <ArrowRight className="h-3 w-3 ml-1" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-6">
          <div className="text-center text-gray-600 dark:text-gray-400">
            <RefreshCw className="h-8 w-8 text-gray-300 dark:text-gray-600 mx-auto mb-2" />
            <p className="font-medium text-gray-700 dark:text-gray-300 mb-2">
              {hasTriedAnalysis
                ? analysisCount > 1
                  ? `No opposing viewpoints found after ${analysisCount} analyses.`
                  : "No opposing viewpoints found for this article."
                : "No opposing viewpoints available yet."
              }
            </p>
            <p className="text-sm mb-4">
              {selectedRelationshipType
                ? `No ${getRelationshipLabel(selectedRelationshipType).toLowerCase()} found for this article.`
                : hasTriedAnalysis
                  ? analysisCount > 1
                    ? "This article appears to have limited opposing perspectives in our current database. Try again later as more articles are added."
                    : "This article might not have clear opposing perspectives in our current database, or our analysis hasn't found opposing coverage yet."
                  : "Our system can analyze this article to find opposing perspectives from different sources and frameworks."
              }
            </p>

            <div className="flex flex-col sm:flex-row gap-3 justify-center items-center">
              <button
                onClick={triggerOnDemandAnalysis}
                disabled={loading}
                className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-4 py-2 rounded-md transition-colors"
              >
                {loading ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    <span>Analyzing...</span>
                  </>
                ) : hasTriedAnalysis ? (
                  <>
                    <RefreshCw className="h-4 w-4" />
                    <span>Retry Analysis</span>
                  </>
                ) : (
                  <>
                    <RefreshCw className="h-4 w-4" />
                    <span>Analyze for Opposing Viewpoints</span>
                  </>
                )}
              </button>

              <button
                onClick={() => {
                  setSelectedRelationshipType(null)
                  fetchViewpoints()
                }}
                disabled={loading}
                className="flex items-center space-x-1 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors disabled:opacity-50"
              >
                <RefreshCw className="h-3 w-3" />
                <span>Refresh</span>
              </button>
            </div>

            {hasTriedAnalysis && (
              <div className="mt-4 text-xs text-gray-500 dark:text-gray-500">
                <p>Analysis complete. Our system searched for articles with:</p>
                <ul className="mt-1 space-y-1">
                  <li>• Different political frameworks and ethical positions</li>
                  <li>• Contrasting emotional tones and perspectives</li>
                  <li>• Coverage from diverse news sources</li>
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default OpposingViewpoints