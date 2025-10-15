'use client';

const TABLES = [
  { name: 'users', description: 'User accounts and authentication' },
  { name: 'sources', description: 'News sources and RSS feeds' },
  { name: 'articles', description: 'Scraped articles' },
  { name: 'topics', description: 'Available news topics' },
  { name: 'frameworks', description: 'Ethical frameworks' },
  { name: 'newsletters', description: 'Generated newsletters' },
  { name: 'job_execution_history', description: 'Background job execution logs' },
  { name: 'admin_audit_logs', description: 'Admin action audit trail' },
];

export default function DatabaseBrowserPage() {
  // Reserved for future table selection functionality
  // const [selectedTable, setSelectedTable] = useState<string | null>(null);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Database Browser</h1>
        <p className="mt-1 text-sm text-gray-600">
          View and explore database tables
        </p>
      </div>

      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg
              className="h-5 w-5 text-yellow-400"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                clipRule="evenodd"
              />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-yellow-800">
              Under Construction
            </h3>
            <div className="mt-2 text-sm text-yellow-700">
              <p>
                The generic database browser is planned for Phase 5. For now, use the specific management pages:
              </p>
              <ul className="list-disc ml-5 mt-2">
                <li><a href="/admin/users" className="underline">Users Management</a></li>
                <li><a href="/admin/sources" className="underline">Sources Management</a></li>
                <li><a href="/admin/articles" className="underline">Articles Management</a></li>
                <li><a href="/admin/jobs" className="underline">Jobs Management</a></li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {TABLES.map((table) => (
          <div
            key={table.name}
            className="bg-white overflow-hidden shadow rounded-lg hover:shadow-md transition-shadow cursor-pointer"
            onClick={() => {
              const routes: Record<string, string> = {
                'users': '/admin/users',
                'sources': '/admin/sources',
                'articles': '/admin/articles',
                'job_execution_history': '/admin/jobs',
                'admin_audit_logs': '/admin/audit',
              };
              const route = routes[table.name];
              if (route) {
                window.location.href = route;
              } else {
                alert(`No dedicated page for ${table.name} yet. Coming in Phase 5!`);
              }
            }}
          >
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0 bg-indigo-500 rounded-md p-3">
                  <svg
                    className="h-6 w-6 text-white"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"
                    />
                  </svg>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      {table.name}
                    </dt>
                    <dd className="text-xs text-gray-400 mt-1">
                      {table.description}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Database Statistics
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">8</div>
            <div className="text-sm text-gray-600">Total Tables</div>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">247</div>
            <div className="text-sm text-gray-600">Users</div>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">429</div>
            <div className="text-sm text-gray-600">Articles</div>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">8</div>
            <div className="text-sm text-gray-600">Sources</div>
          </div>
        </div>
      </div>
    </div>
  );
}
