'use client';

import { useState, useEffect } from 'react';
// import { api } from '@/lib/api'; // TODO: Implement monitoring APIs

interface SystemHealth {
  status: 'healthy' | 'warning' | 'critical';
  timestamp: string;
  version: string;
  database_connected: boolean;
  challenge_system_status: string;
  uptime: string;
}

interface SystemAlert {
  severity: 'critical' | 'warning' | 'info';
  type: string;
  message: string;
  metric?: string;
  timestamp?: string;
}

interface PerformanceMetrics {
  database_performance: {
    recent_challenge_queries_per_hour: number;
    recent_response_queries_per_hour: number;
    query_efficiency: string;
  };
  assignment_processing: {
    total_assignments: number;
    pending_assignments: number;
    completion_rate: number;
    processing_health: string;
  };
  system_load: {
    status: string;
    memory_usage: string;
    cpu_usage: string;
  };
}

interface ParticipationMetrics {
  participation_trends: {
    last_7_days: number;
    last_30_days: number;
    trend: string;
    health: string;
  };
  challenge_health: {
    total_challenges: number;
    published_challenges: number;
    health_status: string;
  };
  completion_metrics: {
    total_responses: number;
    completed_responses: number;
    completion_rate: number;
    health: string;
  };
  engagement_quality: {
    response_quality: {
      justification_rate: number;
      quality_level: string;
    };
    article_engagement: {
      engagement_rate: number;
      quality_level: string;
    };
    diversity_metrics: {
      agreement_level_diversity: number;
      diversity_level: string;
    };
    overall_quality_score: number;
  };
}

interface ExecutiveSummary {
  timestamp: string;
  overall_status: string;
  key_metrics: {
    total_active_users: number;
    weekly_participants: number;
    engagement_rate: number;
    system_health: string;
    active_alerts: number;
  };
  trend_indicators: {
    participation_trend: string;
    data_quality: number;
    error_rate: number;
  };
  recommendations: string[];
}

export default function SystemMonitor() {
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [alerts, setAlerts] = useState<SystemAlert[]>([]);
  const [performanceMetrics, setPerformanceMetrics] = useState<PerformanceMetrics | null>(null);
  const [participationMetrics, setParticipationMetrics] = useState<ParticipationMetrics | null>(null);
  const [executiveSummary, setExecutiveSummary] = useState<ExecutiveSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'performance' | 'participation' | 'alerts'>('overview');

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      loadMonitoringData();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    loadMonitoringData();
  }, []);

  const loadMonitoringData = async () => {
    try {
      setLoading(true);
      setError(null);

      // TODO: Implement monitoring API endpoints
      // For now, using mock data to prevent build errors
      const [healthData, alertsData, perfData, participationData, summaryData] = await Promise.all([
        Promise.resolve(null), // api.getMonitoringHealth().catch(() => null),
        Promise.resolve([]), // api.getSystemAlerts().catch(() => []),
        Promise.resolve(null), // api.getPerformanceMetrics().catch(() => null),
        Promise.resolve(null), // api.getParticipationMetrics().catch(() => null),
        Promise.resolve(null) // api.getExecutiveSummary().catch(() => null)
      ]);

      setSystemHealth(healthData);
      setAlerts(alertsData || []);
      setPerformanceMetrics(perfData);
      setParticipationMetrics(participationData);
      setExecutiveSummary(summaryData);
      setLastRefresh(new Date());

    } catch (err) {
      console.error('Failed to load monitoring data:', err);
      setError('Failed to load monitoring data');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-600 dark:text-green-400';
      case 'warning': return 'text-yellow-600 dark:text-yellow-400';
      case 'critical': return 'text-red-600 dark:text-red-400';
      default: return 'text-gray-600 dark:text-gray-400';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return '✅';
      case 'warning': return '⚠️';
      case 'critical': return '🚨';
      default: return '❓';
    }
  };

  const getQualityLevelColor = (level: string) => {
    switch (level) {
      case 'high': return 'text-green-600 dark:text-green-400';
      case 'medium': return 'text-yellow-600 dark:text-yellow-400';
      case 'low': return 'text-red-600 dark:text-red-400';
      default: return 'text-gray-600 dark:text-gray-400';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const formatRelativeTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));

    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${diffInMinutes} minutes ago`;
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)} hours ago`;
    return `${Math.floor(diffInMinutes / 1440)} days ago`;
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'increasing': return '📈';
      case 'decreasing': return '📉';
      case 'stable': return '➡️';
      default: return '❓';
    }
  };

  if (loading && !systemHealth) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading system monitor...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-600 dark:text-red-400 text-4xl mb-4">⚠️</div>
          <h2 className="text-xl font-semibold text-foreground mb-2">Monitoring System Error</h2>
          <p className="text-muted-foreground mb-4">{error}</p>
          <button
            onClick={loadMonitoringData}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="bg-card rounded-lg shadow-sm p-6 mb-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-foreground">System Monitor</h1>
              <p className="text-muted-foreground mt-1">
                Real-time monitoring of the challenge system health and performance
              </p>
            </div>

            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div className={`w-3 h-3 rounded-full ${systemHealth?.status === 'healthy' ? 'bg-green-500' : systemHealth?.status === 'warning' ? 'bg-yellow-500' : 'bg-red-500'}`}></div>
                <span className={`text-sm font-medium ${getStatusColor(systemHealth?.status || 'unknown')}`}>
                  {systemHealth?.status?.toUpperCase() || 'UNKNOWN'}
                </span>
              </div>

              <button
                onClick={loadMonitoringData}
                className="px-3 py-2 border border-border rounded-md text-sm hover:bg-gray-50 dark:hover:bg-gray-800"
                disabled={loading}
              >
                {loading ? 'Refreshing...' : 'Refresh'}
              </button>

              {lastRefresh && (
                <span className="text-sm text-muted-foreground">
                  Last updated: {formatRelativeTime(lastRefresh.toISOString())}
                </span>
              )}
            </div>
          </div>

          {/* Quick Stats */}
          {executiveSummary && (
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mt-4 pt-4 border-t border-border">
              <div className="text-center">
                <div className="text-2xl font-bold text-foreground">
                  {executiveSummary.key_metrics.total_active_users}
                </div>
                <div className="text-sm text-muted-foreground">Active Users</div>
              </div>

              <div className="text-center">
                <div className="text-2xl font-bold text-foreground">
                  {executiveSummary.key_metrics.weekly_participants}
                </div>
                <div className="text-sm text-muted-foreground">Weekly Participants</div>
              </div>

              <div className="text-center">
                <div className="text-2xl font-bold text-foreground">
                  {executiveSummary.key_metrics.engagement_rate.toFixed(1)}%
                </div>
                <div className="text-sm text-muted-foreground">Engagement Rate</div>
              </div>

              <div className="text-center">
                <div className={`text-2xl font-bold ${getStatusColor(executiveSummary.key_metrics.system_health)}`}>
                  {executiveSummary.key_metrics.active_alerts}
                </div>
                <div className="text-sm text-muted-foreground">Active Alerts</div>
              </div>

              <div className="text-center">
                <div className={`text-2xl font-bold ${getStatusColor(executiveSummary.overall_status)}`}>
                  {getStatusIcon(executiveSummary.overall_status)}
                </div>
                <div className="text-sm text-muted-foreground">System Status</div>
              </div>
            </div>
          )}
        </div>

        {/* Navigation Tabs */}
        <div className="bg-card rounded-lg shadow-sm p-6 mb-6">
          <div className="border-b border-border">
            <nav className="flex space-x-8">
              <button
                onClick={() => setActiveTab('overview')}
                className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === 'overview'
                    ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400'
                    : 'border-transparent text-muted-foreground hover:text-foreground hover:border-gray-300'
                }`}
              >
                Overview
              </button>
              <button
                onClick={() => setActiveTab('performance')}
                className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === 'performance'
                    ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400'
                    : 'border-transparent text-muted-foreground hover:text-foreground hover:border-gray-300'
                }`}
              >
                Performance
              </button>
              <button
                onClick={() => setActiveTab('participation')}
                className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === 'participation'
                    ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400'
                    : 'border-transparent text-muted-foreground hover:text-foreground hover:border-gray-300'
                }`}
              >
                Participation
              </button>
              <button
                onClick={() => setActiveTab('alerts')}
                className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === 'alerts'
                    ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400'
                    : 'border-transparent text-muted-foreground hover:text-foreground hover:border-gray-300'
                }`}
              >
                Alerts {alerts.length > 0 && (
                <span className="ml-1 px-2 py-1 bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200 rounded-full text-xs font-medium">
                  {alerts.length}
                </span>
              )}
              </button>
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Executive Summary */}
            {executiveSummary && (
              <div className="bg-card rounded-lg shadow-sm p-6">
                <h2 className="text-xl font-semibold text-foreground mb-4">Executive Summary</h2>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div>
                    <h3 className="text-lg font-medium text-foreground mb-3">System Health</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-muted-foreground">Status:</span>
                        <span className={`text-sm font-medium ${getStatusColor(executiveSummary.overall_status)}`}>
                          {executiveSummary.overall_status.toUpperCase()}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-muted-foreground">Uptime:</span>
                        <span className="text-sm font-medium text-green-600 dark:text-green-400">
                          Operational
                        </span>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-lg font-medium text-foreground mb-3">Key Metrics</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-muted-foreground">Active Users:</span>
                        <span className="text-sm font-medium text-foreground">
                          {executiveSummary.key_metrics.total_active_users.toLocaleString()}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-muted-foreground">Weekly Participants:</span>
                        <span className="text-sm font-medium text-foreground">
                          {executiveSummary.key_metrics.weekly_participants.toLocaleString()}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-lg font-medium text-foreground mb-3">Trends</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-muted-foreground">Participation:</span>
                        <span className="text-sm font-medium">
                          {getTrendIcon(executiveSummary.trend_indicators.participation_trend)}{' '}
                          {executiveSummary.trend_indicators.participation_trend}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-muted-foreground">Data Quality:</span>
                        <span className={`text-sm font-medium ${getQualityLevelColor(
                          executiveSummary.trend_indicators.data_quality > 80 ? 'high' :
                          executiveSummary.trend_indicators.data_quality > 60 ? 'medium' : 'low'
                        )}`}>
                          {executiveSummary.trend_indicators.data_quality.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Recommendations */}
                {executiveSummary.recommendations && (
                  <div className="mt-6 pt-6 border-t border-border">
                    <h3 className="text-lg font-medium text-foreground mb-3">Recommendations</h3>
                    <div className="space-y-2">
                      {executiveSummary.recommendations.map((recommendation, index) => (
                        <div key={index} className="flex items-start gap-2">
                          <span className="text-blue-600 dark:text-blue-400 mt-0.5">•</span>
                          <span className="text-sm text-foreground">{recommendation}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Active Alerts */}
            {alerts.length > 0 && (
              <div className="bg-card rounded-lg shadow-sm p-6">
                <h2 className="text-xl font-semibold text-foreground mb-4">Active Alerts</h2>

                <div className="space-y-3">
                  {alerts.map((alert, index) => (
                    <div
                      key={index}
                      className={`p-4 rounded-lg border-l-4 ${
                        alert.severity === 'critical'
                          ? 'bg-red-50 border-red-500 dark:bg-red-950/20'
                          : alert.severity === 'warning'
                          ? 'bg-yellow-50 border-yellow-500 dark:bg-yellow-950/20'
                          : 'bg-blue-50 border-blue-500 dark:bg-blue-950/20'
                      }`}
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <span className={`text-sm font-medium ${
                              alert.severity === 'critical'
                                ? 'text-red-800 dark:text-red-200'
                                : alert.severity === 'warning'
                                ? 'text-yellow-800 dark:text-yellow-200'
                                : 'text-blue-800 dark:text-blue-200'
                            }`}>
                              {alert.type.toUpperCase()}
                            </span>
                            <span className={`text-xs px-2 py-1 rounded ${
                              alert.severity === 'critical'
                                ? 'bg-red-100 text-red-800'
                                : alert.severity === 'warning'
                                ? 'bg-yellow-100 text-yellow-800'
                                : 'bg-blue-100 text-blue-800'
                            }`}>
                              {alert.severity.toUpperCase()}
                            </span>
                          </div>
                          <p className="text-foreground font-medium">{alert.message}</p>
                          {alert.metric && (
                            <p className="text-sm text-muted-foreground mt-1">
                              Metric: {alert.metric}
                            </p>
                          )}
                        </div>
                        <div className="text-right">
                          {alert.timestamp && (
                            <p className="text-xs text-muted-foreground">
                              {formatRelativeTime(alert.timestamp)}
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
        )}

        {activeTab === 'performance' && performanceMetrics && (
          <div className="space-y-6">
            {/* Performance Overview */}
            <div className="bg-card rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-semibold text-foreground mb-4">Performance Overview</h2>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <h3 className="text-lg font-medium text-foreground mb-3">Database Performance</h3>
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-muted-foreground">Query Efficiency:</span>
                      <span className={`text-sm font-medium ${
                        performanceMetrics.database_performance.query_efficiency === 'good'
                          ? 'text-green-600 dark:text-green-400'
                          : 'text-yellow-600 dark:text-yellow-400'
                      }`}>
                        {performanceMetrics.database_performance.query_efficiency.toUpperCase()}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-muted-foreground">Challenge Queries/hr:</span>
                      <span className="text-sm font-medium text-foreground">
                        {performanceMetrics.database_performance.recent_challenge_queries_per_hour}
                      </span>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-medium text-foreground mb-3">Assignment Processing</h3>
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-muted-foreground">Completion Rate:</span>
                      <span className={`text-sm font-medium ${getQualityLevelColor(
                        performanceMetrics.assignment_processing.completion_rate > 80 ? 'high' :
                        performanceMetrics.assignment_processing.completion_rate > 60 ? 'medium' : 'low'
                      )}`}>
                        {performanceMetrics.assignment_processing.completion_rate}%
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-muted-foreground">Pending Assignments:</span>
                      <span className="text-sm font-medium text-foreground">
                        {performanceMetrics.assignment_processing.pending_assignments}
                      </span>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-medium text-foreground mb-3">System Load</h3>
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-muted-foreground">Status:</span>
                      <span className={`text-sm font-medium ${
                        performanceMetrics.system_load.status === 'normal'
                          ? 'text-green-600 dark:text-green-400'
                          : 'text-yellow-600 dark:text-yellow-400'
                      }`}>
                        {performanceMetrics.system_load.status.toUpperCase()}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-muted-foreground">Memory Usage:</span>
                      <span className="text-sm font-medium text-foreground">
                        {performanceMetrics.system_load.memory_usage}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-muted-foreground">CPU Usage:</span>
                      <span className="text-sm font-medium text-foreground">
                        {performanceMetrics.system_load.cpu_usage}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'participation' && participationMetrics && (
          <div className="space-y-6">
            {/* Participation Overview */}
            <div className="bg-card rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-semibold text-foreground mb-4">Participation Overview</h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="text-lg font-medium text-foreground mb-3">Participation Trends</h3>
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-muted-foreground">Trend:</span>
                      <span className="text-sm font-medium">
                        {getTrendIcon(participationMetrics.participation_trends.trend)}{' '}
                        {participationMetrics.participation_trends.trend}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-muted-foreground">Health:</span>
                      <span className={`text-sm font-medium ${getQualityLevelColor(
                        participationMetrics.participation_trends.health === 'good' ? 'high' :
                        participationMetrics.participation_trends.health === 'declining' ? 'low' : 'medium'
                      )}`}>
                        {participationMetrics.participation_trends.health.charAt(0).toUpperCase() + participationMetrics.participation_trends.health.slice(1)}
                      </span>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-medium text-foreground mb-3">Challenge Health</h3>
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-muted-foreground">Active Challenges:</span>
                      <span className="text-sm font-medium text-foreground">
                        {participationMetrics.challenge_health.published_challenges} / {participationMetrics.challenge_health.total_challenges}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-muted-foreground">Health Status:</span>
                      <span className={`text-sm font-medium ${getQualityLevelColor(
                        participationMetrics.challenge_health.health_status === 'good' ? 'high' :
                        participationMetrics.challenge_health.health_status === 'warning' ? 'medium' : 'low'
                      )}`}>
                        {participationMetrics.challenge_health.health_status.charAt(0).toUpperCase() + participationMetrics.challenge_health.health_status.slice(1)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Engagement Quality */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <h3 className="text-lg font-medium text-foreground mb-3">Response Quality</h3>
                  <div className="text-center">
                    <div className={`text-2xl font-bold ${getQualityLevelColor(
                      participationMetrics.engagement_quality.response_quality.quality_level
                    )}`}>
                      {participationMetrics.engagement_quality.response_quality.justification_rate.toFixed(1)}%
                    </div>
                    <div className="text-sm text-muted-foreground">Justification Rate</div>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-medium text-foreground mb-3">Article Engagement</h3>
                  <div className="text-center">
                    <div className={`text-2xl font-bold ${getQualityLevelColor(
                      participationMetrics.engagement_quality.article_engagement.quality_level
                    )}`}>
                      {participationMetrics.engagement_quality.article_engagement.engagement_rate.toFixed(1)}%
                    </div>
                    <div className="text-sm text-muted-foreground">Engagement Rate</div>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-medium text-foreground mb-3">Diversity Score</h3>
                  <div className="text-center">
                    <div className={`text-2xl font-bold ${getQualityLevelColor(
                      participationMetrics.engagement_quality.diversity_metrics.diversity_level
                    )}`}>
                      {participationMetrics.engagement_quality.diversity_metrics.agreement_level_diversity}
                    </div>
                    <div className="text-sm text-muted-foreground">Perspective Diversity</div>
                  </div>
                </div>
              </div>

              {/* Completion Metrics */}
              <div className="mt-6">
                <h3 className="text-lg font-medium text-foreground mb-3">Completion Metrics</h3>
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Total Responses:</span>
                    <span className="text-sm font-medium text-foreground">
                      {participationMetrics.completion_metrics.total_responses}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Completed:</span>
                    <span className="text-sm font-medium text-foreground">
                      {participationMetrics.completion_metrics.completed_responses}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Completion Rate:</span>
                    <span className={`text-sm font-medium ${getQualityLevelColor(
                      participationMetrics.completion_metrics.health === 'good' ? 'high' :
                      participationMetrics.completion_metrics.health === 'low_completion' ? 'low' : 'medium'
                    )}`}>
                      {participationMetrics.completion_metrics.completion_rate}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'alerts' && (
          <div className="space-y-6">
            {alerts.length === 0 ? (
              <div className="bg-card rounded-lg shadow-sm p-12 text-center">
                <div className="text-green-600 dark:text-green-400 text-4xl mb-4">✅</div>
                <h3 className="text-xl font-semibold text-foreground mb-2">No Active Alerts</h3>
                <p className="text-muted-foreground">
                  All systems are operating normally. Check back later for any issues.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {alerts.map((alert, index) => (
                  <div
                    key={index}
                    className={`p-6 rounded-lg border-l-4 ${
                      alert.severity === 'critical'
                        ? 'bg-red-50 border-red-500 dark:bg-red-950/20'
                        : alert.severity === 'warning'
                        ? 'bg-yellow-50 border-yellow-500 dark:bg-yellow-950/20'
                        : 'bg-blue-50 border-blue-500 dark:bg-blue-950/20'
                    }`}
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <span className={`text-sm font-bold ${
                            alert.severity === 'critical'
                              ? 'text-red-800 dark:text-red-200'
                              : alert.severity === 'warning'
                              ? 'text-yellow-800 dark:text-yellow-200'
                              : 'text-blue-800 dark:text-blue-200'
                          }`}>
                            {alert.type.toUpperCase()}
                          </span>
                          <span className={`text-xs px-2 py-1 rounded ${
                            alert.severity === 'critical'
                              ? 'bg-red-100 text-red-800'
                              : alert.severity === 'warning'
                              ? 'bg-yellow-100 text-yellow-800'
                              : 'bg-blue-100 text-blue-800'
                          }`}>
                            {alert.severity.toUpperCase()}
                          </span>
                        </div>

                        <h3 className="text-lg font-semibold text-foreground mb-1">
                          {alert.message}
                        </h3>

                        {alert.metric && (
                          <p className="text-sm text-muted-foreground mb-2">
                            <strong>Related Metric:</strong> {alert.metric}
                          </p>
                        )}

                        {alert.timestamp && (
                          <p className="text-xs text-muted-foreground">
                            <strong>Detected:</strong> {formatTimestamp(alert.timestamp)}
                          </p>
                        )}

                        <div className="mt-3 p-3 bg-muted rounded-md">
                          <p className="text-sm text-muted-foreground">
                            <strong>Recommended Action:</strong> Based on this alert type, please investigate the underlying issue and take appropriate corrective action.
                          </p>
                        </div>
                      </div>

                      <div className="text-right ml-4">
                        {alert.timestamp && (
                          <button
                            className="text-xs text-muted-foreground hover:text-foreground"
                            onClick={() => alert.timestamp && navigator.clipboard.writeText(formatTimestamp(alert.timestamp))}
                          >
                            Copy Timestamp
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Alert Summary */}
            <div className="bg-card rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-semibold text-foreground mb-4">Alert Summary</h3>

              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="text-center">
                  <div className={`text-2xl font-bold ${getStatusColor(
                    alerts.filter(a => a.severity === 'critical').length > 0 ? 'critical' :
                    alerts.filter(a => a.severity === 'warning').length > 0 ? 'warning' : 'info'
                  )}`}>
                    {alerts.filter(a => a.severity === 'critical').length}
                  </div>
                  <div className="text-sm text-muted-foreground">Critical</div>
                </div>

                <div className="text-center">
                  <div className={`text-2xl font-bold ${getStatusColor(
                    alerts.filter(a => a.severity === 'warning').length > 0 ? 'warning' : 'info'
                  )}`}>
                    {alerts.filter(a => a.severity === 'warning').length}
                  </div>
                  <div className="text-sm text-muted-foreground">Warnings</div>
                </div>

                <div className="text-center">
                  <div className={`text-2xl font-bold ${getStatusColor('info')}`}>
                    {alerts.filter(a => a.severity === 'info').length}
                  </div>
                  <div className="text-sm text-muted-foreground">Info</div>
                </div>

                <div className="text-center">
                  <div className="text-2xl font-bold text-foreground">
                    {alerts.length}
                  </div>
                  <div className="text-sm text-muted-foreground">Total Alerts</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="mt-8 pt-6 border-t border-border">
          <div className="text-center text-sm text-muted-foreground">
            <p>
              System monitoring refreshes every 30 seconds. Last update: {lastRefresh && formatTimestamp(lastRefresh.toISOString())}
            </p>
            <p className="mt-1">
              For detailed system information, check the API endpoints or contact your system administrator.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}