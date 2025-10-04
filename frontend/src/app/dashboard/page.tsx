'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import Navbar from '@/components/Navbar';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface UserStats {
  articles_read: number;
  newsletters_received: number;
  topics_tracked: number;
  sources_subscribed: number;
  views_changed: number;
}

interface SentimentData {
  date: string;
  values: Record<string, number>;
}

interface BiasData {
  week: string;
  left: number;
  center: number;
  right: number;
}

export default function DashboardPage() {
  const router = useRouter();
  const [userStats, setUserStats] = useState<UserStats | null>(null);
  const [sentimentData, setSentimentData] = useState<SentimentData[]>([]);
  const [biasData, setBiasData] = useState<BiasData[]>([]);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState(30);

  useEffect(() => {
    loadDashboardData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [timeRange]);

  const loadDashboardData = async () => {
    try {
      const [stats, sentiment, bias] = await Promise.all([
        api.getUserStats(),
        api.getSentimentOverTime(timeRange),
        api.getBiasDistribution(4),
      ]);

      setUserStats(stats);
      setSentimentData(sentiment);
      setBiasData(bias);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '';
      if (errorMessage.includes('401') || errorMessage.includes('403')) {
        router.push('/login');
      } else {
        console.error('Failed to load dashboard data:', err);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    api.clearToken();
    router.push('/login');
  };

  // Transform sentiment data for Recharts
  const sentimentChartData = sentimentData.map(item => ({
    date: new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    ...item.values
  }));

  // Get unique topic names for chart lines
  const topicNames = sentimentData.length > 0
    ? Object.keys(sentimentData[0].values)
    : [];

  const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

  if (loading) {
    return (
      <>
        <Navbar />
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading dashboard...</p>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <Navbar />
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 py-8">
          {/* Header */}
          <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">📊 Dashboard</h1>
              <p className="text-gray-600 mt-1">Your discourse analytics</p>
            </div>
          </div>

        {/* Stats Overview */}
        {userStats && (
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <div className="text-sm font-medium text-gray-600">Articles Read</div>
              <div className="text-3xl font-bold text-gray-900 mt-2">{userStats.articles_read}</div>
            </div>
            <div className="bg-white rounded-lg shadow-sm p-6">
              <div className="text-sm font-medium text-gray-600">Newsletters</div>
              <div className="text-3xl font-bold text-gray-900 mt-2">{userStats.newsletters_received}</div>
            </div>
            <div className="bg-white rounded-lg shadow-sm p-6">
              <div className="text-sm font-medium text-gray-600">Topics Tracked</div>
              <div className="text-3xl font-bold text-gray-900 mt-2">{userStats.topics_tracked}</div>
            </div>
            <div className="bg-white rounded-lg shadow-sm p-6">
              <div className="text-sm font-medium text-gray-600">Sources</div>
              <div className="text-3xl font-bold text-gray-900 mt-2">{userStats.sources_subscribed}</div>
            </div>
            <div className="bg-white rounded-lg shadow-sm p-6">
              <div className="text-sm font-medium text-gray-600">Views Changed</div>
              <div className="text-3xl font-bold text-gray-900 mt-2">{userStats.views_changed}</div>
            </div>
          </div>
        )}

        {/* Time Range Selector */}
        <div className="flex justify-end mb-4">
          <div className="bg-white rounded-lg shadow-sm p-2 flex gap-2">
            {[7, 30, 90].map((days) => (
              <button
                key={days}
                onClick={() => setTimeRange(days)}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  timeRange === days
                    ? 'bg-indigo-600 text-white'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                {days}d
              </button>
            ))}
          </div>
        </div>

        {/* Sentiment Over Time Chart */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Sentiment Over Time</h2>
          <p className="text-sm text-gray-600 mb-4">
            Track how sentiment changes across your topics
          </p>
          {sentimentChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={350}>
              <LineChart data={sentimentChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis domain={[-10, 10]} />
                <Tooltip />
                <Legend />
                {topicNames.map((topic, idx) => (
                  <Line
                    key={topic}
                    type="monotone"
                    dataKey={topic}
                    stroke={colors[idx % colors.length]}
                    strokeWidth={2}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="text-center py-12 text-gray-500">
              No sentiment data available for this time range
            </div>
          )}
        </div>

        {/* Bias Distribution Chart */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Source Bias Distribution</h2>
          <p className="text-sm text-gray-600 mb-4">
            Weekly breakdown of political lean in your news sources
          </p>
          {biasData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={biasData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="week" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="left"
                  stackId="1"
                  stroke="#3b82f6"
                  fill="#3b82f6"
                  name="Left"
                />
                <Area
                  type="monotone"
                  dataKey="center"
                  stackId="1"
                  stroke="#64748b"
                  fill="#64748b"
                  name="Center"
                />
                <Area
                  type="monotone"
                  dataKey="right"
                  stackId="1"
                  stroke="#ef4444"
                  fill="#ef4444"
                  name="Right"
                />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="text-center py-12 text-gray-500">
              No bias distribution data available
            </div>
          )}
        </div>

        </div>
      </div>
    </>
  );
}
