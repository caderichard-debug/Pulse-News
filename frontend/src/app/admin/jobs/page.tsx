'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';

const JOB_IDS = [
  { id: 'scrape_rss', name: 'Scrape RSS Feeds', description: 'Fetch new articles from RSS feeds' },
  { id: 'extract_articles', name: 'Extract Articles', description: 'Extract full article content' },
  { id: 'analyze_articles', name: 'Analyze Articles', description: 'AI analysis (sentiment, bias, summary)' },
  { id: 'framework_mapping', name: 'Framework Mapping', description: 'Map articles to ethical frameworks' },
  { id: 'verify_statistics', name: 'Verify Statistics', description: 'Extract and verify statistics' },
  { id: 'cluster_articles', name: 'Cluster Articles', description: 'Group similar articles' },
  { id: 'generate_context', name: 'Generate Context', description: 'Generate background context' },
  { id: 'send_newsletters', name: 'Send Newsletters', description: 'Send daily newsletters' },
];

export default function JobsPage() {
  const [jobHistory, setJobHistory] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [triggeringJob, setTriggeringJob] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>('all');
  const [limit, setLimit] = useState(20);

  useEffect(() => {
    loadJobHistory();
  }, [filter, limit]);

  const loadJobHistory = async () => {
    try {
      const params: any = { limit };
      if (filter !== 'all') {
        params.status = filter;
      }
      const data = await api.getJobHistory(params);
      setJobHistory(data.jobs);
    } catch (err) {
      console.error('Failed to load job history:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTriggerJob = async (jobId: string) => {
    if (!confirm(`Trigger ${jobId}? This will run the job immediately.`)) {
      return;
    }

    setTriggeringJob(jobId);
    try {
      const result = await api.triggerJob(jobId);
      alert(
        `Job completed!\nStatus: ${result.result.status}\nDuration: ${result.result.duration_seconds.toFixed(1)}s\nItems: ${result.result.items_processed || 0}`
      );
      await loadJobHistory();
    } catch (err) {
      alert(`Failed to trigger job: ${err}`);
    } finally {
      setTriggeringJob(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Job Management</h1>
        <p className="mt-1 text-sm text-gray-600">
          Trigger background jobs and view execution history
        </p>
      </div>

      {/* Manual Job Triggers */}
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          ⚡ Trigger Jobs Manually
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {JOB_IDS.map((job) => (
            <button
              key={job.id}
              onClick={() => handleTriggerJob(job.id)}
              disabled={triggeringJob === job.id}
              className="relative group bg-gray-50 p-4 rounded-lg border-2 border-gray-200 hover:border-red-400 hover:bg-red-50 transition-all disabled:opacity-50 disabled:cursor-not-allowed text-left"
            >
              <div className="font-medium text-gray-900 group-hover:text-red-600">
                {job.name}
              </div>
              <div className="text-sm text-gray-500 mt-1">{job.description}</div>
              {triggeringJob === job.id && (
                <div className="absolute inset-0 flex items-center justify-center bg-white bg-opacity-90 rounded-lg">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-red-600"></div>
                </div>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Job History */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">
              📋 Job Execution History
            </h2>
            <div className="flex items-center space-x-4">
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="rounded-lg border-gray-300 text-sm"
              >
                <option value="all">All Status</option>
                <option value="success">Success</option>
                <option value="failed">Failed</option>
                <option value="running">Running</option>
              </select>
              <select
                value={limit}
                onChange={(e) => setLimit(Number(e.target.value))}
                className="rounded-lg border-gray-300 text-sm"
              >
                <option value={10}>10 records</option>
                <option value={20}>20 records</option>
                <option value={50}>50 records</option>
                <option value={100}>100 records</option>
              </select>
              <button
                onClick={loadJobHistory}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm font-medium"
              >
                Refresh
              </button>
            </div>
          </div>
        </div>

        <div className="overflow-x-auto">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-red-600"></div>
            </div>
          ) : jobHistory.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              No job history found
            </div>
          ) : (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Job Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Started
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Duration
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Items
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Triggered By
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Error
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {jobHistory.map((job) => (
                  <tr key={job.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {job.job_name}
                      </div>
                      <div className="text-xs text-gray-500">{job.job_id}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          job.status === 'success'
                            ? 'bg-green-100 text-green-800'
                            : job.status === 'failed'
                            ? 'bg-red-100 text-red-800'
                            : job.status === 'running'
                            ? 'bg-blue-100 text-blue-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {job.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(job.started_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {job.duration_seconds
                        ? `${job.duration_seconds.toFixed(1)}s`
                        : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {job.items_processed || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {job.triggered_by}
                    </td>
                    <td className="px-6 py-4 text-sm text-red-600">
                      {job.error_message ? (
                        <details className="cursor-pointer">
                          <summary className="text-red-600 hover:text-red-800">
                            View error
                          </summary>
                          <div className="mt-2 text-xs bg-red-50 p-2 rounded">
                            {job.error_message}
                          </div>
                        </details>
                      ) : (
                        '-'
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
