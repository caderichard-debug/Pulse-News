'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';

interface Table {
  name: string;
  description: string;
  icon: string;
  endpoint?: string;
  hasData?: boolean;
}

const TABLES: Table[] = [
  {
    name: 'users',
    description: 'User accounts and authentication',
    icon: '👥',
    endpoint: '/admin-panel/users',
    hasData: true
  },
  {
    name: 'sources',
    description: 'News sources and RSS feeds',
    icon: '📰',
    endpoint: '/admin-panel/sources',
    hasData: true
  },
  {
    name: 'articles',
    description: 'Scraped articles',
    icon: '📄',
    endpoint: '/admin-panel/articles',
    hasData: true
  },
  {
    name: 'topics',
    description: 'Available news topics',
    icon: '🏷️',
    endpoint: '/preferences/topics'
  },
  {
    name: 'frameworks',
    description: 'Ethical frameworks for analysis',
    icon: '🎯',
    hasData: false
  },
  {
    name: 'newsletters',
    description: 'Generated newsletters',
    icon: '📧',
    hasData: false
  },
  {
    name: 'job_execution_history',
    description: 'Background job execution logs',
    icon: '⚙️',
    endpoint: '/admin-panel/jobs/history',
    hasData: true
  },
  {
    name: 'admin_audit_log',
    description: 'Admin action audit trail',
    icon: '📋',
    endpoint: '/admin-panel/audit',
    hasData: true
  },
];

export default function DatabaseBrowserPage() {
  const [selectedTable, setSelectedTable] = useState<string | null>(null);
  const [tableData, setTableData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<any>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [page, setPage] = useState(1);
  const [totalRecords, setTotalRecords] = useState(0);
  const pageSize = 20;

  const loadStats = async () => {
    try {
      const data = await api.getAdminDashboard();
      setStats(data.system_stats);
    } catch (err) {
      console.error('Failed to load stats:', err);
    }
  };

  const loadTableData = async () => {
    if (!selectedTable) return;

    setLoading(true);
    setError(null);

    try {
      const table = TABLES.find(t => t.name === selectedTable);
      if (!table?.endpoint) {
        setError('No API endpoint configured for this table');
        setLoading(false);
        return;
      }

      let data;
      let records: any[] = [];
      let total = 0;

      // Fetch data based on table type
      if (selectedTable === 'users') {
        data = await api.getAdminUsers(page, pageSize);
        records = data.users || [];
        total = data.total || 0;
      } else if (selectedTable === 'sources') {
        data = await api.getAdminSources(page, pageSize);
        records = data.sources || [];
        total = data.total || 0;
      } else if (selectedTable === 'articles') {
        data = await api.getAdminArticles(page, pageSize);
        records = data.articles || [];
        total = data.total || 0;
      } else if (selectedTable === 'topics') {
        records = await api.getTopics();
        total = records.length;
      } else if (selectedTable === 'job_execution_history') {
        data = await api.getJobHistory();
        records = data.jobs || [];
        total = records.length;
      } else if (selectedTable === 'admin_audit_log') {
        data = await api.getAuditLog(page, pageSize);
        records = data.logs || [];
        total = data.total || 0;
      }

      setTableData(records);
      setTotalRecords(total);
    } catch (err: any) {
      setError(err.message || 'Failed to load table data');
    } finally {
      setLoading(false);
    }
  };

  // Load dashboard stats for table counts
  useEffect(() => {
    loadStats();
  }, [loadStats]);

  // Load table data when selection changes
  useEffect(() => {
    if (selectedTable) {
      loadTableData();
    }
  }, [selectedTable, page, loadTableData]);

  const selectTable = (tableName: string) => {
    setSelectedTable(tableName);
    setPage(1);
    setSearchTerm('');
  };

  const getTableIcon = (tableName: string) => {
    return TABLES.find(t => t.name === tableName)?.icon || '📊';
  };

  const formatValue = (value: any): string => {
    if (value === null || value === undefined) return '-';
    if (typeof value === 'boolean') return value ? 'Yes' : 'No';
    if (typeof value === 'object') return JSON.stringify(value);
    if (typeof value === 'string' && value.length > 50) {
      return value.substring(0, 50) + '...';
    }
    return String(value);
  };

  const getTableColumns = (tableName: string): string[] => {
    switch (tableName) {
      case 'users':
        return ['id', 'email', 'name', 'is_admin', 'is_active', 'created_at'];
      case 'sources':
        return ['id', 'name', 'url', 'rss_url', 'is_active'];
      case 'articles':
        return ['id', 'title', 'source_id', 'url', 'scraped_at', 'processing_status'];
      case 'topics':
        return ['id', 'name', 'description'];
      case 'job_execution_history':
        return ['id', 'job_name', 'status', 'started_at', 'duration_seconds', 'items_processed'];
      case 'admin_audit_log':
        return ['id', 'admin_email', 'action_type', 'resource_type', 'timestamp'];
      default:
        return [];
    }
  };

  const filteredData = tableData.filter(record => {
    if (!searchTerm) return true;
    return Object.values(record).some(value =>
      String(value).toLowerCase().includes(searchTerm.toLowerCase())
    );
  });

  const totalPages = Math.ceil(totalRecords / pageSize);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Database Browser</h1>
        <p className="mt-1 text-sm text-gray-600">
          View and explore database tables
        </p>
      </div>

      {/* Database Statistics */}
      {stats && (
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Database Statistics
          </h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-900">{stats.users?.total || 0}</div>
              <div className="text-sm text-blue-600">Users</div>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-900">{stats.articles?.total || 0}</div>
              <div className="text-sm text-green-600">Articles</div>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-900">{stats.sources?.total || 0}</div>
              <div className="text-sm text-purple-600">Sources</div>
            </div>
            <div className="text-center p-4 bg-yellow-50 rounded-lg">
              <div className="text-2xl font-bold text-yellow-900">{stats.frameworks?.total || 0}</div>
              <div className="text-sm text-yellow-600">Frameworks</div>
            </div>
          </div>
        </div>
      )}

      {/* Table Selection Grid */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Select a Table</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {TABLES.map((table) => (
            <button
              key={table.name}
              onClick={() => table.hasData !== false ? selectTable(table.name) : alert('No data available for this table yet')}
              disabled={table.hasData === false}
              className={`
                bg-white overflow-hidden shadow rounded-lg hover:shadow-md transition-all p-5 text-left
                ${selectedTable === table.name ? 'ring-2 ring-red-500 bg-red-50' : ''}
                ${table.hasData === false ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
              `}
            >
              <div className="flex items-center">
                <div className="text-3xl mr-4">{table.icon}</div>
                <div className="flex-1">
                  <div className="text-sm font-medium text-gray-900">
                    {table.name}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    {table.description}
                  </div>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Table Data Viewer */}
      {selectedTable && (
        <div className="bg-white shadow rounded-lg overflow-hidden">
          {/* Table Header */}
          <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <span className="text-2xl">{getTableIcon(selectedTable)}</span>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    {selectedTable}
                  </h3>
                  <p className="text-sm text-gray-600">
                    {totalRecords} records total
                  </p>
                </div>
              </div>

              {/* Search */}
              <div className="w-64">
                <input
                  type="text"
                  placeholder="Search records..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 text-sm"
                />
              </div>
            </div>
          </div>

          {/* Loading State */}
          {loading && (
            <div className="p-12 text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600 mx-auto"></div>
              <p className="mt-4 text-gray-600">Loading table data...</p>
            </div>
          )}

          {/* Error State */}
          {error && !loading && (
            <div className="p-6">
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            </div>
          )}

          {/* Table Content */}
          {!loading && !error && filteredData.length > 0 && (
            <>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      {getTableColumns(selectedTable).map((column) => (
                        <th
                          key={column}
                          className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                        >
                          {column}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {filteredData.map((record, index) => (
                      <tr key={record.id || index} className="hover:bg-gray-50">
                        {getTableColumns(selectedTable).map((column) => (
                          <td
                            key={column}
                            className="px-6 py-4 whitespace-nowrap text-sm text-gray-900"
                          >
                            {formatValue(record[column])}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="text-sm text-gray-600">
                      Showing page {page} of {totalPages}
                    </div>
                    <div className="flex space-x-2">
                      <button
                        onClick={() => setPage(Math.max(1, page - 1))}
                        disabled={page === 1}
                        className="px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Previous
                      </button>
                      <button
                        onClick={() => setPage(Math.min(totalPages, page + 1))}
                        disabled={page === totalPages}
                        className="px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Next
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}

          {/* Empty State */}
          {!loading && !error && filteredData.length === 0 && (
            <div className="p-12 text-center">
              <p className="text-gray-500">
                {searchTerm ? 'No records found matching your search' : 'No records in this table'}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Instructions */}
      {!selectedTable && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-blue-800">
                How to use the Database Browser
              </h3>
              <div className="mt-2 text-sm text-blue-700">
                <ul className="list-disc ml-5 space-y-1">
                  <li>Click on a table card above to view its contents</li>
                  <li>Use the search box to filter records</li>
                  <li>Navigate through pages using the pagination controls</li>
                  <li>For editing operations, use the specific management pages (Users, Sources, Articles)</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
