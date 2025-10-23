'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';

interface ChallengeAssignment {
  id: string;
  challenge_response_id: string;
  article_id: number;
  sequence_day: number;
  article: {
    id: number;
    title: string;
    url: string;
    source: {
      name: string;
      organizational_bias: string;
    };
    published_at: string;
    summary?: string;
    sentiment_score?: number;
    political_lean?: string;
    opposition_score?: number;
  };
  is_completed: boolean;
  completed_at?: string;
  engagement_score?: number;
}

interface ChallengeAssignmentsProps {
  responseId?: string;
  weekStartDate?: string;
}

export default function ChallengeAssignments({ responseId, weekStartDate }: ChallengeAssignmentsProps) {
  const [assignments, setAssignments] = useState<ChallengeAssignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDay, setSelectedDay] = useState<number | null>(null);

  useEffect(() => {
    loadAssignments();
  }, [responseId]);

  const loadAssignments = async () => {
    try {
      setLoading(true);
      const data = await api.getChallengeAssignments(responseId);
      setAssignments(data);
      setError(null);
    } catch (err) {
      console.error('Failed to load challenge assignments:', err);
      setError('Failed to load assigned articles');
    } finally {
      setLoading(false);
    }
  };

  const markAsCompleted = async (assignmentId: string) => {
    try {
      await api.updateChallengeAssignment(assignmentId, { is_completed: true });
      setAssignments(prev =>
        prev.map(assignment =>
          assignment.id === assignmentId
            ? { ...assignment, is_completed: true, completed_at: new Date().toISOString() }
            : assignment
        )
      );
    } catch (err) {
      console.error('Failed to mark assignment as completed:', err);
    }
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'short',
      day: 'numeric'
    });
  };

  const getPoliticalLeanColor = (lean?: string): string => {
    const colors = {
      'left': 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
      'center': 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200',
      'right': 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
      'center-left': 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
      'center-right': 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
    };
    return colors[lean as keyof typeof colors] || 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
  };

  const getSentimentEmoji = (score?: number): string => {
    if (!score) return '📊';
    if (score > 3) return '😊';
    if (score > 1) return '🙂';
    if (score > -1) return '😐';
    if (score > -3) return '😟';
    return '😞';
  };

  const getOppositionStrength = (score?: number): string => {
    if (!score) return 'Unknown';
    if (score > 0.8) return 'Very Strong Opposition';
    if (score > 0.6) return 'Strong Opposition';
    if (score > 0.4) return 'Moderate Opposition';
    if (score > 0.2) return 'Mild Opposition';
    return 'Slight Opposition';
  };

  const getOppositionColor = (score?: number): string => {
    if (!score) return 'text-gray-600';
    if (score > 0.8) return 'text-red-600 dark:text-red-400';
    if (score > 0.6) return 'text-orange-600 dark:text-orange-400';
    if (score > 0.4) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-green-600 dark:text-green-400';
  };

  if (loading) {
    return (
      <div className="bg-card rounded-lg shadow-sm p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded mb-4"></div>
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-24 bg-gray-200 dark:bg-gray-700 rounded"></div>
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
            onClick={loadAssignments}
            className="mt-2 text-sm text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-300"
          >
            Try again
          </button>
        </div>
      </div>
    );
  }

  if (assignments.length === 0) {
    return (
      <div className="bg-card rounded-lg shadow-sm p-6">
        <div className="text-center py-8">
          <div className="text-gray-400 dark:text-gray-500 text-4xl mb-3">📚</div>
          <p className="text-muted-foreground">
            No articles assigned yet for this challenge.
          </p>
          <p className="text-sm text-muted-foreground mt-1">
            Articles will be assigned based on your response to provide diverse perspectives.
          </p>
        </div>
      </div>
    );
  }

  // Group assignments by day
  const assignmentsByDay = assignments.reduce((acc, assignment) => {
    if (!acc[assignment.sequence_day]) {
      acc[assignment.sequence_day] = [];
    }
    acc[assignment.sequence_day].push(assignment);
    return acc;
  }, {} as Record<number, ChallengeAssignment[]>);

  const sortedDays = Object.keys(assignmentsByDay)
    .map(Number)
    .sort((a, b) => a - b);

  const selectedDayAssignments = selectedDay
    ? assignmentsByDay[selectedDay]
    : assignments;

  return (
    <div className="space-y-6">
      {/* Overview */}
      <div className="bg-card rounded-lg shadow-sm p-6">
        <h3 className="text-xl font-semibold text-foreground mb-4">Your 7-Day Perspective Journey</h3>
        <p className="text-muted-foreground mb-4">
          Based on your challenge response, you've been assigned articles that provide diverse perspectives
          on the topic. Each day explores different viewpoints to help you understand the full picture.
        </p>

        {/* Day Selector */}
        <div className="flex flex-wrap gap-2 mb-6">
          <button
            onClick={() => setSelectedDay(null)}
            className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
              selectedDay === null
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300'
            }`}
          >
            All Days ({assignments.length})
          </button>
          {sortedDays.map((day) => (
            <button
              key={day}
              onClick={() => setSelectedDay(day)}
              className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                selectedDay === day
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300'
              }`}
            >
              Day {day} ({assignmentsByDay[day].length})
            </button>
          ))}
        </div>

        {/* Progress Overview */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">
              {assignments.filter(a => a.is_completed).length}
            </div>
            <div className="text-sm text-muted-foreground">Articles Read</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600 dark:text-orange-400">
              {assignments.filter(a => !a.is_completed).length}
            </div>
            <div className="text-sm text-muted-foreground">Remaining</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600 dark:text-green-400">
              {assignments.length > 0 ? Math.round((assignments.filter(a => a.is_completed).length / assignments.length) * 100) : 0}%
            </div>
            <div className="text-sm text-muted-foreground">Progress</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
              {sortedDays.length}
            </div>
            <div className="text-sm text-muted-foreground">Days Active</div>
          </div>
        </div>
      </div>

      {/* Articles */}
      <div className="space-y-4">
        {selectedDayAssignments.map((assignment) => (
          <div
            key={assignment.id}
            className={`bg-card rounded-lg shadow-sm p-6 border-2 transition-all ${
              assignment.is_completed
                ? 'border-green-200 dark:border-green-800 bg-green-50/50 dark:bg-green-950/20'
                : 'border-border hover:shadow-md'
            }`}
          >
            <div className="flex justify-between items-start mb-4">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <span className="px-2 py-1 bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200 rounded text-xs font-medium">
                    Day {assignment.sequence_day}
                  </span>
                  {assignment.is_completed && (
                    <span className="px-2 py-1 bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 rounded text-xs font-medium">
                      ✓ Read
                    </span>
                  )}
                  <span className={`px-2 py-1 rounded text-xs font-medium ${getPoliticalLeanColor(assignment.article.political_lean)}`}>
                    {assignment.article.political_lean?.replace('_', ' ').toUpperCase() || 'UNKNOWN'}
                  </span>
                </div>

                <h4 className="text-lg font-semibold text-foreground mb-2 hover:text-indigo-600 dark:hover:text-indigo-400">
                  <a
                    href={assignment.article.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:underline"
                  >
                    {assignment.article.title}
                  </a>
                </h4>

                <div className="flex items-center gap-4 text-sm text-muted-foreground mb-3">
                  <span>{assignment.article.source.name}</span>
                  <span>•</span>
                  <span>{formatDate(assignment.article.published_at)}</span>
                  {assignment.article.sentiment_score && (
                    <>
                      <span>•</span>
                      <span className="flex items-center gap-1">
                        {getSentimentEmoji(assignment.article.sentiment_score)}
                        Sentiment: {assignment.article.sentiment_score.toFixed(1)}
                      </span>
                    </>
                  )}
                </div>

                {assignment.article.opposition_score && (
                  <div className="mb-3">
                    <span className={`text-sm font-medium ${getOppositionColor(assignment.article.opposition_score)}`}>
                      {getOppositionStrength(assignment.article.opposition_score)}
                      ({(assignment.article.opposition_score * 100).toFixed(0)}% match)
                    </span>
                  </div>
                )}

                {assignment.article.summary && (
                  <p className="text-muted-foreground mb-4 line-clamp-3">
                    {assignment.article.summary}
                  </p>
                )}
              </div>

              <div className="flex flex-col items-end gap-2 ml-4">
                {!assignment.is_completed && (
                  <button
                    onClick={() => markAsCompleted(assignment.id)}
                    className="px-3 py-1 bg-indigo-600 text-white text-sm rounded-md hover:bg-indigo-700 transition-colors"
                  >
                    Mark as Read
                  </button>
                )}
                <a
                  href={assignment.article.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-3 py-1 border border-border text-sm rounded-md hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                >
                  Open Article →
                </a>
              </div>
            </div>

            {assignment.is_completed && assignment.completed_at && (
              <div className="mt-3 pt-3 border-t border-border">
                <p className="text-sm text-green-600 dark:text-green-400">
                  ✓ Completed on {formatDate(assignment.completed_at)}
                  {assignment.engagement_score && (
                    <span className="ml-2">Engagement: {assignment.engagement_score.toFixed(0)}%</span>
                  )}
                </p>
              </div>
            )}
          </div>
        ))}
      </div>

      {assignments.filter(a => !a.is_completed).length > 0 && (
        <div className="bg-info border border-info rounded-lg p-4">
          <p className="text-info text-sm">
            <strong>💡 Tip:</strong> Try to read one article per day to get the most benefit from the perspective journey.
            Each article is selected to provide a different viewpoint on the topic you explored in the challenge.
          </p>
        </div>
      )}
    </div>
  );
}