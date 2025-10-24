'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';

interface ChallengeAnalyticsData {
  participation_metrics: {
    total_challenges: number;
    completed_challenges: number;
    completion_rate: number;
    current_streak: number;
    longest_streak: number;
    first_participation: string | null;
    last_participation: string | null;
  };
  engagement_metrics: {
    total_articles_assigned: number;
    total_articles_engaged: number;
    engagement_rate: number;
    average_articles_per_challenge: number;
    average_completion_time: number;
  };
  response_patterns: {
    agreement_distribution: Record<string, number>;
    claim_type_preferences: Record<string, any>;
    temporal_patterns: Record<string, any>;
    controversy_engagement: Record<string, any>;
  };
  quality_indicators: {
    response_quality_score: number;
    engagement_consistency: number;
    perspective_diversity_score: number;
    improvement_trend: string;
  };
  recent_performance: Array<{
    week_start_date: string;
    claim_type: string;
    agreement_level: string;
    articles_assigned: number;
    articles_completed: number;
    completion_rate: number;
    status: string;
  }>;
  generated_at: string;
}

interface ParticipationTrendsData {
  trends: Array<{
    week_start: string;
    participated: boolean;
    claim_type: string | null;
    agreement_level: string | null;
    assignments: {
      assigned: number;
      completed: number;
    };
    completion_rate: number;
  }>;
  summary: {
    total_weeks: number;
    participated_weeks: number;
    participation_rate: number;
    average_completion_rate: number;
  };
  generated_at: string;
}

export default function ChallengeAnalyticsDashboard() {
  const [analytics, setAnalytics] = useState<ChallengeAnalyticsData | null>(null);
  const [trends, setTrends] = useState<ParticipationTrendsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState(12);

  useEffect(() => {
    loadAnalyticsData();
  }, [timeRange]);

  const loadAnalyticsData = async () => {
    try {
      setLoading(true);
      const [analyticsData, trendsData] = await Promise.all([
        api.getChallengeAnalytics(),
        api.getChallengeParticipationTrends(timeRange)
      ]);

      setAnalytics(analyticsData);
      setTrends(trendsData);
      setError(null);
    } catch (err) {
      console.error('Failed to load analytics data:', err);
      setError('Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  };

  const getImprovementTrendColor = (trend: string): string => {
    switch (trend) {
      case 'improving': return 'text-green-600 dark:text-green-400';
      case 'declining': return 'text-red-600 dark:text-red-400';
      case 'stable': return 'text-blue-600 dark:text-blue-400';
      default: return 'text-gray-600 dark:text-gray-400';
    }
  };

  const getImprovementTrendIcon = (trend: string): string => {
    switch (trend) {
      case 'improving': return '📈';
      case 'declining': return '📉';
      case 'stable': return '➡️';
      default: return '❓';
    }
  };

  const getQualityScoreColor = (score: number): string => {
    if (score >= 80) return 'text-green-600 dark:text-green-400';
    if (score >= 60) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const getAgreementLevelText = (level: string): string => {
    const levels: Record<string, string> = {
      'STRONGLY_DISAGREE': 'Strongly Disagree',
      'DISAGREE': 'Disagree',
      'NEUTRAL': 'Neutral',
      'AGREE': 'Agree',
      'STRONGLY_AGREE': 'Strongly Agree'
    };
    return levels[level] || level;
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="bg-card rounded-lg shadow-sm p-6">
          <div className="animate-pulse">
            <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded mb-4"></div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-20 bg-gray-200 dark:bg-gray-700 rounded"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-card rounded-lg shadow-sm p-6">
        <div className="text-center text-red-600 dark:text-red-400">
          <p>{error}</p>
          <button
            onClick={loadAnalyticsData}
            className="mt-2 text-sm text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-300"
          >
            Try again
          </button>
        </div>
      </div>
    );
  }

  if (!analytics || !trends) {
    return (
      <div className="bg-card rounded-lg shadow-sm p-6">
        <div className="text-center text-muted-foreground">
          <p>No analytics data available.</p>
          <p className="text-sm mt-1">Start participating in challenges to see your insights!</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Participation Overview */}
      <div className="bg-card rounded-lg shadow-sm p-6">
        <h3 className="text-xl font-semibold text-foreground mb-4">Participation Overview</h3>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">
              {analytics.participation_metrics.total_challenges}
            </div>
            <div className="text-sm text-muted-foreground">Challenges Started</div>
          </div>

          <div className="text-center">
            <div className="text-2xl font-bold text-green-600 dark:text-green-400">
              {analytics.participation_metrics.current_streak}
            </div>
            <div className="text-sm text-muted-foreground">Current Streak</div>
          </div>

          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
              {analytics.participation_metrics.completion_rate}%
            </div>
            <div className="text-sm text-muted-foreground">Completion Rate</div>
          </div>

          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600 dark:text-orange-400">
              {analytics.participation_metrics.longest_streak}
            </div>
            <div className="text-sm text-muted-foreground">Longest Streak</div>
          </div>
        </div>

        {analytics.participation_metrics.first_participation && (
          <div className="text-sm text-muted-foreground text-center">
            First participation: {formatDate(analytics.participation_metrics.first_participation)}
            {analytics.participation_metrics.last_participation && (
              <> • Most recent: {formatDate(analytics.participation_metrics.last_participation)}</>
            )}
          </div>
        )}
      </div>

      {/* Engagement Metrics */}
      <div className="bg-card rounded-lg shadow-sm p-6">
        <h3 className="text-xl font-semibold text-foreground mb-4">Engagement Metrics</h3>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
              {analytics.engagement_metrics.total_articles_assigned}
            </div>
            <div className="text-sm text-muted-foreground">Articles Assigned</div>
          </div>

          <div className="text-center">
            <div className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">
              {analytics.engagement_metrics.total_articles_engaged}
            </div>
            <div className="text-sm text-muted-foreground">Articles Read</div>
          </div>

          <div className="text-center">
            <div className="text-2xl font-bold text-teal-600 dark:text-teal-400">
              {analytics.engagement_metrics.engagement_rate}%
            </div>
            <div className="text-sm text-muted-foreground">Engagement Rate</div>
          </div>

          <div className="text-center">
            <div className="text-2xl font-bold text-cyan-600 dark:text-cyan-400">
              {analytics.engagement_metrics.average_articles_per_challenge}
            </div>
            <div className="text-sm text-muted-foreground">Avg Articles/Challenge</div>
          </div>
        </div>

        {analytics.engagement_metrics.average_completion_time > 0 && (
          <div className="text-center text-sm text-muted-foreground">
            Average completion time: {analytics.engagement_metrics.average_completion_time} days
          </div>
        )}
      </div>

      {/* Quality Indicators */}
      <div className="bg-card rounded-lg shadow-sm p-6">
        <h3 className="text-xl font-semibold text-foreground mb-4">Quality Indicators</h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className={`text-2xl font-bold ${getQualityScoreColor(analytics.quality_indicators.response_quality_score)}`}>
              {analytics.quality_indicators.response_quality_score}%
            </div>
            <div className="text-sm text-muted-foreground">Response Quality</div>
            <div className="text-xs text-muted-foreground mt-1">
              Based on justification depth and completion rates
            </div>
          </div>

          <div className="text-center">
            <div className={`text-2xl font-bold ${getQualityScoreColor(analytics.quality_indicators.engagement_consistency)}`}>
              {analytics.quality_indicators.engagement_consistency}%
            </div>
            <div className="text-sm text-muted-foreground">Engagement Consistency</div>
            <div className="text-xs text-muted-foreground mt-1">
              How regularly you engage with assigned articles
            </div>
          </div>

          <div className="text-center">
            <div className={`text-2xl font-bold ${getQualityScoreColor(analytics.quality_indicators.perspective_diversity_score)}`}>
              {analytics.quality_indicators.perspective_diversity_score}%
            </div>
            <div className="text-sm text-muted-foreground">Perspective Diversity</div>
            <div className="text-xs text-muted-foreground mt-1">
              Variety of political viewpoints you've been exposed to
            </div>
          </div>
        </div>

        {/* Improvement Trend */}
        <div className="mt-6 pt-6 border-t border-border">
          <div className="flex items-center justify-center">
            <span className="text-sm text-muted-foreground mr-2">Performance Trend:</span>
            <span className={`font-medium ${getImprovementTrendColor(analytics.quality_indicators.improvement_trend)}`}>
              {getImprovementTrendIcon(analytics.quality_indicators.improvement_trend)} {analytics.quality_indicators.improvement_trend.charAt(0).toUpperCase() + analytics.quality_indicators.improvement_trend.slice(1)}
            </span>
          </div>
        </div>
      </div>

      {/* Response Patterns */}
      <div className="bg-card rounded-lg shadow-sm p-6">
        <h3 className="text-xl font-semibold text-foreground mb-4">Response Patterns</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Agreement Distribution */}
          <div>
            <h4 className="text-lg font-medium text-foreground mb-3">Agreement Distribution</h4>
            <div className="space-y-2">
              {Object.entries(analytics.response_patterns.agreement_distribution).map(([level, count]) => (
                <div key={level} className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">
                    {getAgreementLevelText(level)}
                  </span>
                  <div className="flex items-center gap-2">
                    <div className="w-20 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                      <div
                        className="bg-indigo-600 h-2 rounded-full"
                        style={{
                          width: `${(count / analytics.participation_metrics.total_challenges) * 100}%`
                        }}
                      ></div>
                    </div>
                    <span className="text-sm font-medium text-foreground">{count}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Claim Type Preferences */}
          <div>
            <h4 className="text-lg font-medium text-foreground mb-3">Claim Type Preferences</h4>
            <div className="space-y-2">
              {Object.entries(analytics.response_patterns.claim_type_preferences.selection_distribution || {}).map(([type, count]) => (
                <div key={type} className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">
                    {type.replace('_', ' ').toLowerCase()}
                  </span>
                  <span className="text-sm font-medium text-foreground">{count as number}</span>
                </div>
              ))}
              {analytics.response_patterns.claim_type_preferences.most_selected && (
                <div className="pt-2 border-t border-border">
                  <span className="text-sm font-medium text-foreground">Most Selected: </span>
                  <span className="text-sm text-muted-foreground">
                    {analytics.response_patterns.claim_type_preferences.most_selected.replace('_', ' ').toLowerCase()}
                  </span>
                </div>
              )}
              {analytics.response_patterns.claim_type_preferences.highest_engagement && (
                <div>
                  <span className="text-sm font-medium text-foreground">Highest Engagement: </span>
                  <span className="text-sm text-muted-foreground">
                    {analytics.response_patterns.claim_type_preferences.highest_engagement.replace('_', ' ').toLowerCase()}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Recent Performance */}
      {analytics.recent_performance.length > 0 && (
        <div className="bg-card rounded-lg shadow-sm p-6">
          <h3 className="text-xl font-semibold text-foreground mb-4">Recent Performance</h3>

          <div className="space-y-3">
            {analytics.recent_performance.map((performance, index) => (
              <div
                key={performance.week_start_date}
                className="flex items-center justify-between p-3 bg-muted rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <div className="text-sm font-medium text-foreground">
                    {formatDate(performance.week_start_date)}
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-1 bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 rounded text-xs font-medium">
                      {performance.claim_type.replace('_', ' ')}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {getAgreementLevelText(performance.agreement_level)}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <div className="text-sm text-muted-foreground">
                    {performance.articles_completed}/{performance.articles_assigned} articles
                  </div>
                  <div className="text-sm font-medium text-foreground">
                    {performance.completion_rate}%
                  </div>
                  <div className={`px-2 py-1 rounded text-xs font-medium ${
                    performance.status === 'COMPLETED'
                      ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                      : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                  }`}>
                    {performance.status.toLowerCase()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Participation Trends */}
      {trends && (
        <div className="bg-card rounded-lg shadow-sm p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-xl font-semibold text-foreground">Participation Trends</h3>
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(Number(e.target.value))}
              className="px-3 py-1 border border-border rounded-md text-sm bg-background"
            >
              <option value={4}>Last 4 weeks</option>
              <option value={12}>Last 12 weeks</option>
              <option value={24}>Last 24 weeks</option>
              <option value={52}>Last year</option>
            </select>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">
                {trends.summary.participated_weeks}/{trends.summary.total_weeks}
              </div>
              <div className="text-sm text-muted-foreground">Weeks Participated</div>
            </div>

            <div className="text-center">
              <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                {trends.summary.participation_rate}%
              </div>
              <div className="text-sm text-muted-foreground">Participation Rate</div>
            </div>

            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                {trends.summary.average_completion_rate}%
              </div>
              <div className="text-sm text-muted-foreground">Avg Completion</div>
            </div>

            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                {trends.trends.filter(t => t.participated).length}
              </div>
              <div className="text-sm text-muted-foreground">Active Periods</div>
            </div>
          </div>

          {/* Recent weeks visualization */}
          <div className="space-y-2">
            {trends.trends.slice(-8).reverse().map((trend) => (
              <div
                key={trend.week_start}
                className={`flex items-center justify-between p-2 rounded ${
                  trend.participated ? 'bg-green-50 dark:bg-green-950/20' : 'bg-gray-50 dark:bg-gray-950/20'
                }`}
              >
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${
                    trend.participated ? 'bg-green-500' : 'bg-gray-300'
                  }`}></div>
                  <span className="text-sm text-foreground">
                    {formatDate(trend.week_start)}
                  </span>
                  {trend.participated && trend.claim_type && (
                    <span className="text-xs text-muted-foreground">
                      ({trend.claim_type.replace('_', ' ')})
                    </span>
                  )}
                </div>

                {trend.participated && (
                  <div className="text-sm text-muted-foreground">
                    {trend.assignments.completed}/{trend.assignments.assigned} articles
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Data freshness */}
      <div className="text-center text-xs text-muted-foreground">
        Analytics generated at {new Date(analytics.generated_at).toLocaleString()}
      </div>
    </div>
  );
}