'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import ChallengeAssignments from './ChallengeAssignments';
import ChallengeAnalyticsDashboard from './ChallengeAnalyticsDashboard';

interface ChallengeResponse {
  id: string;
  week_start_date: string;
  claim_id: string;
  claim_text: string;
  claim_type: string;
  agreement_level: number;
  justification: string;
  submitted_at: string;
  assigned_articles_count: number;
  engaged_articles_count: number;
}

interface ChallengeStatistics {
  total_participated: number;
  average_agreement_level: number;
  claim_type_breakdown: Record<string, number>;
  participation_streak: number;
  current_week_responded: boolean;
}

interface ChallengeHistoryProps {
  userId?: string;
}

export default function ChallengeHistory({ userId }: ChallengeHistoryProps) {
  const [responses, setResponses] = useState<ChallengeResponse[]>([]);
  const [statistics, setStatistics] = useState<ChallengeStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAll, setShowAll] = useState(false);
  const [selectedResponse, setSelectedResponse] = useState<ChallengeResponse | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'analytics' | 'history'>('overview');

  useEffect(() => {
    loadChallengeData();
  }, [userId]);

  const loadChallengeData = async () => {
    try {
      setLoading(true);
      const [responsesData, statsData] = await Promise.all([
        api.getChallengeResponses(),
        api.getChallengeStatistics()
      ]);

      setResponses(responsesData);
      setStatistics(statsData);
      setError(null);
    } catch (err) {
      console.error('Failed to load challenge data:', err);
      setError('Failed to load challenge history');
    } finally {
      setLoading(false);
    }
  };

  const getAgreementLevelText = (level: number): string => {
    const levels = {
      1: 'Strongly Disagree',
      2: 'Disagree',
      3: 'Neutral',
      4: 'Agree',
      5: 'Strongly Agree'
    };
    return levels[level as keyof typeof levels] || 'Unknown';
  };

  const getAgreementLevelColor = (level: number): string => {
    const colors = {
      1: 'text-red-600 dark:text-red-400',
      2: 'text-orange-600 dark:text-orange-400',
      3: 'text-gray-600 dark:text-gray-400',
      4: 'text-green-600 dark:text-green-400',
      5: 'text-emerald-600 dark:text-emerald-400'
    };
    return colors[level as keyof typeof colors] || 'text-gray-600';
  };

  const getClaimTypeColor = (type: string): string => {
    const colors = {
      'MORAL_PRINCIPLE': 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
      'ETHICAL_DILEMMA': 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
      'VALUE_CONFLICT': 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
      'SOCIAL_JUSTICE': 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
      'ECONOMIC_PRINCIPLE': 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      'POLITICAL_STANCE': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
    };
    return colors[type as keyof typeof colors] || 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const displayedResponses = showAll ? responses : responses.slice(0, 5);

  if (loading) {
    return (
      <div className="bg-card rounded-lg shadow-sm p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded mb-4"></div>
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-20 bg-gray-200 dark:bg-gray-700 rounded"></div>
            ))}
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
            onClick={loadChallengeData}
            className="mt-2 text-sm text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-300"
          >
            Try again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Tab Navigation */}
      <div className="bg-card rounded-lg shadow-sm p-6">
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
              onClick={() => setActiveTab('analytics')}
              className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'analytics'
                  ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400'
                  : 'border-transparent text-muted-foreground hover:text-foreground hover:border-gray-300'
              }`}
            >
              Detailed Analytics
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'history'
                  ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400'
                  : 'border-transparent text-muted-foreground hover:text-foreground hover:border-gray-300'
              }`}
            >
              Response History
            </button>
          </nav>
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && statistics && (
        <div className="space-y-6">
          {/* Statistics Overview */}
          <div className="bg-card rounded-lg shadow-sm p-6">
            <h3 className="text-xl font-semibold text-foreground mb-4">Your Challenge Insights</h3>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="text-center">
                <div className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">
                  {statistics.total_participated}
                </div>
                <div className="text-sm text-muted-foreground">Challenges Completed</div>
              </div>

              <div className="text-center">
                <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                  {statistics.participation_streak}
                </div>
                <div className="text-sm text-muted-foreground">Week Streak</div>
              </div>

              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                  {statistics.average_agreement_level.toFixed(1)}/5.0
                </div>
                <div className="text-sm text-muted-foreground">Avg Agreement</div>
              </div>

              <div className="text-center">
                <div className={`text-2xl font-bold ${
                  statistics.current_week_responded
                    ? 'text-emerald-600 dark:text-emerald-400'
                    : 'text-orange-600 dark:text-orange-400'
                }`}>
                  {statistics.current_week_responded ? '✓' : '○'}
                </div>
                <div className="text-sm text-muted-foreground">This Week</div>
              </div>
            </div>

            {/* Claim Type Breakdown */}
            {Object.keys(statistics.claim_type_breakdown).length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-foreground mb-2">Claim Type Preferences</h4>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(statistics.claim_type_breakdown).map(([type, count]) => (
                    <span
                      key={type}
                      className={`px-2 py-1 rounded-full text-xs font-medium ${getClaimTypeColor(type)}`}
                    >
                      {type.replace('_', ' ')} ({count})
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Recent Response Preview */}
          {responses.length > 0 && (
            <div className="bg-card rounded-lg shadow-sm p-6">
              <h3 className="text-xl font-semibold text-foreground mb-4">Recent Response</h3>
              {(() => {
                const recentResponse = responses[0];
                return (
                  <div className="border border-border rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${getClaimTypeColor(recentResponse.claim_type)}`}>
                        {recentResponse.claim_type.replace('_', ' ')}
                      </span>
                      <span className="text-sm text-muted-foreground">
                        {formatDate(recentResponse.week_start_date)}
                      </span>
                    </div>

                    <p className="text-foreground font-medium mb-2">{recentResponse.claim_text}</p>

                    <div className="flex items-center gap-4 text-sm">
                      <div className="flex items-center gap-1">
                        <span className="text-muted-foreground">Your stance:</span>
                        <span className={`font-medium ${getAgreementLevelColor(recentResponse.agreement_level)}`}>
                          {getAgreementLevelText(recentResponse.agreement_level)}
                        </span>
                      </div>

                      {recentResponse.assigned_articles_count > 0 && (
                        <div className="flex items-center gap-1">
                          <span className="text-muted-foreground">Articles read:</span>
                          <span className="font-medium text-foreground">
                            {recentResponse.engaged_articles_count}/{recentResponse.assigned_articles_count}
                          </span>
                        </div>
                      )}
                    </div>

                    {recentResponse.assigned_articles_count > 0 && (
                      <div className="mt-3 pt-3 border-t border-border">
                        <button
                          onClick={() => setActiveTab('history')}
                          className="text-sm text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-300 font-medium"
                        >
                          View Full History →
                        </button>
                      </div>
                    )}
                  </div>
                );
              })()}
            </div>
          )}
        </div>
      )}

      {activeTab === 'analytics' && (
        <ChallengeAnalyticsDashboard />
      )}

      {activeTab === 'history' && (
        <div className="bg-card rounded-lg shadow-sm p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-xl font-semibold text-foreground">Your Response History</h3>
            {responses.length > 5 && (
              <button
                onClick={() => setShowAll(!showAll)}
                className="text-sm text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-300"
              >
                {showAll ? 'Show Less' : `Show All (${responses.length})`}
              </button>
            )}
          </div>

          {displayedResponses.length === 0 ? (
            <div className="text-center py-8">
              <div className="text-gray-400 dark:text-gray-500 text-4xl mb-3">📝</div>
              <p className="text-muted-foreground">
                You haven't responded to any challenges yet.
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                Check your Friday newsletter for this week's challenge!
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {displayedResponses.map((response) => (
                <div
                  key={response.id}
                  className="border border-border rounded-lg p-4 hover:shadow-sm transition-shadow"
                >
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${getClaimTypeColor(response.claim_type)}`}>
                          {response.claim_type.replace('_', ' ')}
                        </span>
                        <span className="text-sm text-muted-foreground">
                          {formatDate(response.week_start_date)}
                        </span>
                      </div>

                      <p className="text-foreground font-medium mb-2">{response.claim_text}</p>

                      <div className="flex items-center gap-4 text-sm">
                        <div className="flex items-center gap-1">
                          <span className="text-muted-foreground">Your stance:</span>
                          <span className={`font-medium ${getAgreementLevelColor(response.agreement_level)}`}>
                            {getAgreementLevelText(response.agreement_level)}
                          </span>
                        </div>

                        {response.assigned_articles_count > 0 && (
                          <div className="flex items-center gap-1">
                            <span className="text-muted-foreground">Articles read:</span>
                            <span className="font-medium text-foreground">
                              {response.engaged_articles_count}/{response.assigned_articles_count}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {response.justification && (
                    <div className="mt-3 p-3 bg-muted rounded-md">
                      <p className="text-sm text-muted-foreground italic">
                        "{response.justification}"
                      </p>
                    </div>
                  )}

                  {response.assigned_articles_count > 0 && (
                    <div className="mt-3 pt-3 border-t border-border">
                      <button
                        onClick={() => setSelectedResponse(
                          selectedResponse?.id === response.id ? null : response
                        )}
                        className="text-sm text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-300 font-medium"
                      >
                        {selectedResponse?.id === response.id ? 'Hide' : 'View'} Assigned Articles
                        ({response.engaged_articles_count}/{response.assigned_articles_count} read)
                      </button>
                    </div>
                  )}
                </div>
              ))}

              {selectedResponse && (
                <div className="mt-6 pt-6 border-t border-border">
                  <ChallengeAssignments
                    responseId={selectedResponse.id}
                    weekStartDate={selectedResponse.week_start_date}
                  />
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}