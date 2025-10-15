'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';

interface DashboardData {
  system_stats: {
    users: { total: number; admins: number };
    articles: { total: number; today: number };
    sources: { total: number; active: number };
    frameworks: { total: number };
  };
  recent_jobs: Array<{
    id: number;
    job_id: string;
    job_name: string;
    status: string;
    started_at: string;
    completed_at?: string;
    duration_seconds?: number;
    items_processed?: number;
    error_message?: string;
  }>;
  active_jobs: Array<{
    id: number;
    job_id: string;
    job_name: string;
    started_at: string;
    duration_seconds: number;
  }>;
  error_summary: {
    failed_jobs_24h: number;
  };
  recent_admin_actions: Array<{
    id: number;
    admin_email: string;
    action_type: string;
    resource_type: string;
    timestamp: string;
  }>;
  timestamp: string;
}

export default function AdminPage() {
  const [adminToken, setAdminToken] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('admin_token');
      if (token) {
        try {
          await api.verifyAdminToken(token);
          setIsAuthenticated(true);
          loadDashboard();
        } catch {
          localStorage.removeItem('admin_token');
        }
      }
    };
    checkAuth();
  }, []);

  const loadDashboard = async () => {
    try {
      const data = await api.getAdminDashboard();
      setDashboardData(data);
    } catch {
      console.error('Failed to load dashboard');
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      await api.verifyAdminToken(adminToken);
      localStorage.setItem('admin_token', adminToken);
      setIsAuthenticated(true);
      await loadDashboard();
    } catch {
      setError('Invalid admin token. Please check and try again.');
    } finally {
      setIsLoading(false);
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8">
          <div className="text-center">
            <div className="flex justify-center mb-4">
              <div className="p-3 bg-red-100 rounded-full">
                <svg
                  className="h-12 w-12 text-red-600"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                  />
                </svg>
              </div>
            </div>
            <h2 className="text-3xl font-extrabold text-gray-900">
              Admin Panel Access
            </h2>
            <p className="mt-2 text-sm text-gray-600">
              Enter your admin token to access the control panel
            </p>
          </div>

          <form className="mt-8 space-y-6" onSubmit={handleLogin}>
            <div>
              <label htmlFor="admin-token" className="sr-only">
                Admin Token
              </label>
              <input
                id="admin-token"
                name="admin-token"
                type="password"
                required
                value={adminToken}
                onChange={(e) => setAdminToken(e.target.value)}
                className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-lg focus:outline-none focus:ring-red-500 focus:border-red-500 focus:z-10 sm:text-sm"
                placeholder="Enter admin token"
              />
            </div>

            {error && (
              <div className="rounded-md bg-red-50 p-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg
                      className="h-5 w-5 text-red-400"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                    >
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm text-red-800">{error}</p>
                  </div>
                </div>
              </div>
            )}

            <div>
              <button
                type="submit"
                disabled={isLoading}
                className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-lg text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? (
                  <span className="flex items-center">
                    <svg
                      className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      ></circle>
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      ></path>
                    </svg>
                    Verifying...
                  </span>
                ) : (
                  'Access Admin Panel'
                )}
              </button>
            </div>

            <div className="text-center">
              <a
                href="/dashboard"
                className="text-sm text-gray-600 hover:text-gray-900"
              >
                ← Back to Dashboard
              </a>
            </div>
          </form>

          <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <p className="text-xs text-yellow-800">
              <strong>Security Note:</strong> This token grants full administrative
              access to the Pulse system. Never share it with anyone.
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-600">
          System overview and monitoring
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Users"
          value={dashboardData.system_stats.users.total}
          subtitle={`${dashboardData.system_stats.users.admins} admins`}
          icon="👥"
          color="blue"
        />
        <StatCard
          title="Total Articles"
          value={dashboardData.system_stats.articles.total}
          subtitle={`${dashboardData.system_stats.articles.today} today`}
          icon="📄"
          color="green"
        />
        <StatCard
          title="Active Sources"
          value={dashboardData.system_stats.sources.active}
          subtitle={`of ${dashboardData.system_stats.sources.total} total`}
          icon="📰"
          color="purple"
        />
        <StatCard
          title="Frameworks"
          value={dashboardData.system_stats.frameworks.total}
          subtitle="ethical frameworks"
          icon="🎯"
          color="yellow"
        />
      </div>

      {/* Active Jobs */}
      {dashboardData.active_jobs.length > 0 && (
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            🔄 Active Jobs
          </h2>
          <div className="space-y-3">
            {dashboardData.active_jobs.map((job) => (
              <div
                key={job.job_id}
                className="flex items-center justify-between p-3 bg-blue-50 rounded-lg"
              >
                <div>
                  <p className="font-medium text-gray-900">{job.job_name}</p>
                  <p className="text-sm text-gray-600">
                    Running for {Math.floor(job.duration_seconds)}s
                  </p>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Jobs */}
      {dashboardData.recent_jobs.length > 0 && (
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">
              📋 Recent Jobs
            </h2>
            <a
              href="/admin/jobs"
              className="text-sm text-red-600 hover:text-red-700 font-medium"
            >
              View all →
            </a>
          </div>
          <div className="space-y-3">
            {dashboardData.recent_jobs.slice(0, 5).map((job) => (
              <div
                key={job.job_id}
                className="flex items-center justify-between p-3 border border-gray-200 rounded-lg"
              >
                <div className="flex-1">
                  <p className="font-medium text-gray-900">{job.job_name}</p>
                  <p className="text-sm text-gray-600">
                    {new Date(job.started_at).toLocaleString()}
                  </p>
                </div>
                <div className="flex items-center space-x-4">
                  {job.items_processed && (
                    <span className="text-sm text-gray-600">
                      {job.items_processed} items
                    </span>
                  )}
                  {job.duration_seconds && (
                    <span className="text-sm text-gray-600">
                      {job.duration_seconds.toFixed(1)}s
                    </span>
                  )}
                  <span
                    className={`px-2 py-1 text-xs font-semibold rounded-full ${
                      job.status === 'success'
                        ? 'bg-green-100 text-green-800'
                        : job.status === 'failed'
                        ? 'bg-red-100 text-red-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {job.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Error Summary */}
      {dashboardData.error_summary.failed_jobs_24h > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg
                className="h-5 w-5 text-red-400"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">
                {dashboardData.error_summary.failed_jobs_24h} failed jobs in the
                last 24 hours
              </h3>
              <p className="mt-1 text-sm text-red-700">
                <a href="/admin/jobs" className="underline">
                  View job history to investigate
                </a>
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({
  title,
  value,
  subtitle,
  icon,
  color,
}: {
  title: string;
  value: number;
  subtitle: string;
  icon: string;
  color: 'blue' | 'green' | 'purple' | 'yellow';
}) {
  const colorClasses = {
    blue: 'bg-blue-500',
    green: 'bg-green-500',
    purple: 'bg-purple-500',
    yellow: 'bg-yellow-500',
  };

  return (
    <div className="bg-white overflow-hidden shadow rounded-lg">
      <div className="p-5">
        <div className="flex items-center">
          <div className={`flex-shrink-0 rounded-md p-3 ${colorClasses[color]}`}>
            <span className="text-2xl">{icon}</span>
          </div>
          <div className="ml-5 w-0 flex-1">
            <dl>
              <dt className="text-sm font-medium text-gray-500 truncate">
                {title}
              </dt>
              <dd className="flex items-baseline">
                <div className="text-2xl font-semibold text-gray-900">
                  {value.toLocaleString()}
                </div>
              </dd>
              <dd className="text-sm text-gray-500">{subtitle}</dd>
            </dl>
          </div>
        </div>
      </div>
    </div>
  );
}
