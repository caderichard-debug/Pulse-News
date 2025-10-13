'use client';

import { useState, useEffect } from 'react';
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

export default function AnalyticsPage() {
  const [sentimentData, setSentimentData] = useState<SentimentData[]>([]);
  const [biasData, setBiasData] = useState<BiasData[]>([]);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState(30);

  useEffect(() => {
    loadAnalyticsData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [timeRange]);

  const loadAnalyticsData = async () => {
    try {
      const [sentiment, bias] = await Promise.all([
        api.getSentimentOverTime(timeRange),
        api.getBiasDistribution(4),
      ]);

      setSentimentData(sentiment);
      setBiasData(bias);
    } catch (err) {
      console.error('Failed to load analytics data:', err);
    } finally {
      setLoading(false);
    }
  };


  // Transform sentiment data for Recharts
  const sentimentChartData = sentimentData.map(item => ({
    date: new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    ...item.values
  }));

  // Get all unique lean names across all data points (not just the first one)
  const leanNames = Array.from(
    new Set(
      sentimentData.flatMap(item => Object.keys(item.values))
    )
  ).sort(); // Sort to ensure consistent order: Center, Left, Right

  // Map lean names to colors
  const leanColors: Record<string, string> = {
    'Left': '#3b82f6',    // Blue
    'Center': '#8b5cf6',  // Purple
    'Right': '#ef4444',   // Red
  };

  if (loading) {
    return (
      <>
        <Navbar />
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading analytics...</p>
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
              <h1 className="text-3xl font-bold text-gray-900">📊 Data Analysis</h1>
              <p className="text-gray-600 mt-1">Explore sentiment trends and bias distribution across the news</p>
            </div>
          </div>

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
            Track daily sentiment trends across different political leans. Positive values indicate more optimistic/positive coverage,
            while negative values suggest more critical/negative reporting. Lines show the average sentiment for left-leaning (blue),
            center (purple), and right-leaning (red) news sources.
          </p>
          {sentimentChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={350}>
              <LineChart data={sentimentChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis domain={[-10, 10]} />
                <Tooltip />
                <Legend />
                {leanNames.map((lean) => (
                  <Line
                    key={lean}
                    type="monotone"
                    dataKey={lean}
                    stroke={leanColors[lean] || '#8b5cf6'}
                    strokeWidth={2}
                    connectNulls={true}
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
            This chart shows the political lean of articles from your news sources over the past 4 weeks.
            Each week is represented as a stacked area showing the percentage of articles classified as left-leaning (blue),
            center/neutral (gray), or right-leaning (red). This helps you understand the balance of perspectives in your news consumption.
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
