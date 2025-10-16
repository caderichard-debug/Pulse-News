'use client';

import { useState } from 'react';

interface Endpoint {
  method: string;
  path: string;
  description: string;
  category: string;
  requiresAuth: boolean;
  requiresAdmin: boolean;
  requestBody?: string;
  responseExample?: string;
}

const endpoints: Endpoint[] = [
  // Authentication
  {
    method: 'POST',
    path: '/auth/register',
    description: 'Register a new user account',
    category: 'Authentication',
    requiresAuth: false,
    requiresAdmin: false,
    requestBody: `{
  "email": "user@example.com",
  "password": "password123",
  "name": "User Name",
  "topic_ids": [1, 2, 3]
}`,
    responseExample: `{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "User Name",
    "email_verified": false,
    "is_admin": false
  }
}`
  },
  {
    method: 'POST',
    path: '/auth/login',
    description: 'Login with email and password',
    category: 'Authentication',
    requiresAuth: false,
    requiresAdmin: false,
    requestBody: `{
  "email": "user@example.com",
  "password": "password123"
}`,
    responseExample: `{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "User Name",
    "email_verified": true,
    "is_admin": false
  }
}`
  },
  {
    method: 'GET',
    path: '/auth/me',
    description: 'Get current user information',
    category: 'Authentication',
    requiresAuth: true,
    requiresAdmin: false,
    responseExample: `{
  "id": 1,
  "email": "user@example.com",
  "name": "User Name",
  "email_verified": true,
  "is_admin": false,
  "created_at": "2025-01-15T10:30:00Z",
  "last_login": "2025-01-16T08:15:00Z"
}`
  },

  // Admin Panel
  {
    method: 'GET',
    path: '/admin-panel/dashboard',
    description: 'Get admin dashboard overview with system stats, recent jobs, and admin actions',
    category: 'Admin Panel',
    requiresAuth: true,
    requiresAdmin: true,
    responseExample: `{
  "system_stats": {
    "users": {"total": 249, "admins": 2},
    "articles": {"total": 626, "today": 197},
    "sources": {"total": 8, "active": 8},
    "frameworks": {"total": 10}
  },
  "recent_jobs": [...],
  "active_jobs": [...],
  "error_summary": {"failed_jobs_24h": 0}
}`
  },
  {
    method: 'GET',
    path: '/admin-panel/jobs/history',
    description: 'Get job execution history with filtering',
    category: 'Admin Panel',
    requiresAuth: true,
    requiresAdmin: true,
    responseExample: `{
  "jobs": [
    {
      "id": 123,
      "job_name": "scrape_rss_feeds",
      "status": "success",
      "started_at": "2025-01-16T03:00:00Z",
      "completed_at": "2025-01-16T03:05:30Z",
      "duration_seconds": 330,
      "items_processed": 45
    }
  ]
}`
  },
  {
    method: 'POST',
    path: '/admin-panel/jobs/trigger/{job_id}',
    description: 'Manually trigger a background job',
    category: 'Admin Panel',
    requiresAuth: true,
    requiresAdmin: true,
    requestBody: `// job_id can be: scrape_rss_feeds, extract_articles, analyze_articles, etc.`,
    responseExample: `{
  "message": "Job triggered successfully",
  "job_id": "scrape_rss_feeds"
}`
  },
  {
    method: 'GET',
    path: '/admin-panel/users',
    description: 'List all users with pagination and filtering',
    category: 'Admin Panel',
    requiresAuth: true,
    requiresAdmin: true,
    responseExample: `{
  "users": [
    {
      "id": 1,
      "email": "user@example.com",
      "name": "User Name",
      "is_admin": false,
      "is_active": true,
      "created_at": "2025-01-15T10:30:00Z"
    }
  ],
  "total": 249,
  "skip": 0,
  "limit": 50
}`
  },
  {
    method: 'PUT',
    path: '/admin-panel/users/{user_id}/admin',
    description: 'Toggle admin status for a user',
    category: 'Admin Panel',
    requiresAuth: true,
    requiresAdmin: true,
    responseExample: `{
  "message": "User admin status updated",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "is_admin": true
  }
}`
  },
  {
    method: 'DELETE',
    path: '/admin-panel/users/{user_id}',
    description: 'Delete a user account',
    category: 'Admin Panel',
    requiresAuth: true,
    requiresAdmin: true,
    responseExample: `{
  "message": "User deleted successfully"
}`
  },
  {
    method: 'GET',
    path: '/admin-panel/sources',
    description: 'List all news sources',
    category: 'Admin Panel',
    requiresAuth: true,
    requiresAdmin: true,
    responseExample: `{
  "sources": [
    {
      "id": 1,
      "name": "BBC News",
      "url": "https://bbc.com",
      "rss_url": "https://feeds.bbci.co.uk/news/rss.xml",
      "is_active": true
    }
  ]
}`
  },
  {
    method: 'PUT',
    path: '/admin-panel/sources/{source_id}',
    description: 'Update a news source',
    category: 'Admin Panel',
    requiresAuth: true,
    requiresAdmin: true,
    requestBody: `{
  "name": "Updated Source Name",
  "url": "https://example.com",
  "rss_url": "https://example.com/feed",
  "is_active": true
}`,
    responseExample: `{
  "message": "Source updated successfully",
  "source": {...}
}`
  },
  {
    method: 'DELETE',
    path: '/admin-panel/sources/{source_id}',
    description: 'Delete a news source',
    category: 'Admin Panel',
    requiresAuth: true,
    requiresAdmin: true,
    responseExample: `{
  "message": "Source deleted successfully"
}`
  },
  {
    method: 'GET',
    path: '/admin-panel/articles',
    description: 'List articles with pagination and filtering',
    category: 'Admin Panel',
    requiresAuth: true,
    requiresAdmin: true,
    responseExample: `{
  "articles": [
    {
      "id": 1,
      "title": "Article Title",
      "url": "https://example.com/article",
      "source_id": 1,
      "scraped_at": "2025-01-16T03:00:00Z",
      "processing_status": "analyzed"
    }
  ],
  "total": 626
}`
  },
  {
    method: 'DELETE',
    path: '/admin-panel/articles/{article_id}',
    description: 'Delete an article',
    category: 'Admin Panel',
    requiresAuth: true,
    requiresAdmin: true,
    responseExample: `{
  "message": "Article deleted successfully"
}`
  },
  {
    method: 'GET',
    path: '/admin-panel/audit',
    description: 'Get audit log with filtering',
    category: 'Admin Panel',
    requiresAuth: true,
    requiresAdmin: true,
    responseExample: `{
  "logs": [
    {
      "id": 1,
      "admin_email": "admin@example.com",
      "action_type": "delete_user",
      "resource_type": "user",
      "resource_id": "123",
      "timestamp": "2025-01-16T10:30:00Z"
    }
  ]
}`
  },

  // Preferences
  {
    method: 'GET',
    path: '/preferences',
    description: 'Get user preferences (topics and sources)',
    category: 'Preferences',
    requiresAuth: true,
    requiresAdmin: false,
    responseExample: `{
  "user_id": 1,
  "topics": [
    {
      "id": 1,
      "name": "Technology",
      "priority": 8,
      "is_active": true
    }
  ],
  "sources": [...]
}`
  },
  {
    method: 'GET',
    path: '/preferences/topics',
    description: 'Get all available topics',
    category: 'Preferences',
    requiresAuth: true,
    requiresAdmin: false,
    responseExample: `[
  {
    "id": 1,
    "name": "Technology",
    "description": "Tech news and updates"
  }
]`
  },

  // Analytics
  {
    method: 'GET',
    path: '/analytics/sentiment',
    description: 'Get sentiment analysis data over time',
    category: 'Analytics',
    requiresAuth: true,
    requiresAdmin: false,
    responseExample: `{
  "data": [
    {
      "date": "2025-01-16",
      "positive": 45,
      "neutral": 30,
      "negative": 25
    }
  ]
}`
  },
  {
    method: 'GET',
    path: '/analytics/bias',
    description: 'Get bias distribution data',
    category: 'Analytics',
    requiresAuth: true,
    requiresAdmin: false,
    responseExample: `{
  "data": [
    {
      "date": "2025-01-16",
      "left": 30,
      "center": 40,
      "right": 30
    }
  ]
}`
  },

  // Feed
  {
    method: 'GET',
    path: '/feed',
    description: 'Get personalized article feed with filtering',
    category: 'Feed',
    requiresAuth: true,
    requiresAdmin: false,
    responseExample: `{
  "articles": [
    {
      "id": 1,
      "title": "Article Title",
      "summary": "Brief summary...",
      "source": "BBC News",
      "published_at": "2025-01-16T10:00:00Z",
      "sentiment": "neutral",
      "bias": "center"
    }
  ],
  "total": 100,
  "page": 1
}`
  },
  {
    method: 'GET',
    path: '/articles/{article_id}',
    description: 'Get detailed article information with analysis',
    category: 'Articles',
    requiresAuth: true,
    requiresAdmin: false,
    responseExample: `{
  "id": 1,
  "title": "Article Title",
  "content": "Full article content...",
  "summary": "AI-generated summary",
  "sentiment": "positive",
  "bias": "center",
  "frameworks": ["utilitarianism", "rights"],
  "statistics": [...]
}`
  },

  // Sources
  {
    method: 'GET',
    path: '/sources',
    description: 'Get all active news sources (public)',
    category: 'Sources',
    requiresAuth: false,
    requiresAdmin: false,
    responseExample: `[
  {
    "id": 1,
    "name": "BBC News",
    "url": "https://bbc.com",
    "description": "British public broadcaster"
  }
]`
  }
];

export default function APIPage() {
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [expandedEndpoint, setExpandedEndpoint] = useState<string | null>(null);

  const categories = ['All', ...Array.from(new Set(endpoints.map(e => e.category)))];

  const filteredEndpoints = endpoints.filter(endpoint => {
    const matchesCategory = selectedCategory === 'All' || endpoint.category === selectedCategory;
    const matchesSearch = searchTerm === '' ||
      endpoint.path.toLowerCase().includes(searchTerm.toLowerCase()) ||
      endpoint.description.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const toggleEndpoint = (path: string) => {
    setExpandedEndpoint(expandedEndpoint === path ? null : path);
  };

  const getMethodColor = (method: string) => {
    switch (method) {
      case 'GET': return 'bg-blue-100 text-blue-800';
      case 'POST': return 'bg-green-100 text-green-800';
      case 'PUT': return 'bg-yellow-100 text-yellow-800';
      case 'DELETE': return 'bg-red-100 text-red-800';
      case 'PATCH': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">API Endpoints</h1>
        <p className="mt-1 text-sm text-gray-600">
          Complete API reference for all Pulse endpoints
        </p>
      </div>

      {/* Filters */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Search */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Search
            </label>
            <input
              type="text"
              placeholder="Search endpoints..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500"
            />
          </div>

          {/* Category Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Category
            </label>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500"
            >
              {categories.map(category => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Results Count */}
      <div className="text-sm text-gray-600">
        Showing {filteredEndpoints.length} of {endpoints.length} endpoints
      </div>

      {/* Endpoints List */}
      <div className="space-y-3">
        {filteredEndpoints.map((endpoint, index) => (
          <div key={index} className="bg-white shadow rounded-lg overflow-hidden">
            {/* Endpoint Header */}
            <button
              onClick={() => toggleEndpoint(endpoint.path)}
              className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors text-left"
            >
              <div className="flex items-center space-x-4 flex-1">
                {/* Method Badge */}
                <span className={`px-3 py-1 rounded-md text-xs font-bold ${getMethodColor(endpoint.method)}`}>
                  {endpoint.method}
                </span>

                {/* Path */}
                <code className="text-sm font-mono text-gray-900 flex-1">
                  {endpoint.path}
                </code>

                {/* Auth Badges */}
                <div className="flex items-center space-x-2">
                  {endpoint.requiresAdmin && (
                    <span className="px-2 py-1 bg-red-100 text-red-800 rounded text-xs font-semibold">
                      ADMIN
                    </span>
                  )}
                  {endpoint.requiresAuth && !endpoint.requiresAdmin && (
                    <span className="px-2 py-1 bg-indigo-100 text-indigo-800 rounded text-xs font-semibold">
                      AUTH
                    </span>
                  )}
                  {!endpoint.requiresAuth && (
                    <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-semibold">
                      PUBLIC
                    </span>
                  )}
                </div>
              </div>

              {/* Expand Icon */}
              <svg
                className={`w-5 h-5 text-gray-400 transition-transform ${
                  expandedEndpoint === endpoint.path ? 'transform rotate-180' : ''
                }`}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            {/* Endpoint Details */}
            {expandedEndpoint === endpoint.path && (
              <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 space-y-4">
                {/* Description */}
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-1">Description</h3>
                  <p className="text-sm text-gray-600">{endpoint.description}</p>
                </div>

                {/* Request Body */}
                {endpoint.requestBody && (
                  <div>
                    <h3 className="text-sm font-semibold text-gray-700 mb-2">Request Body</h3>
                    <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-xs">
                      {endpoint.requestBody}
                    </pre>
                  </div>
                )}

                {/* Response Example */}
                {endpoint.responseExample && (
                  <div>
                    <h3 className="text-sm font-semibold text-gray-700 mb-2">Response Example</h3>
                    <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-xs">
                      {endpoint.responseExample}
                    </pre>
                  </div>
                )}

                {/* cURL Example */}
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-2">cURL Example</h3>
                  <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-xs">
                    {`curl -X ${endpoint.method} http://localhost:8000${endpoint.path}${
                      endpoint.requiresAuth ? ' \\\n  -H "Authorization: Bearer YOUR_TOKEN"' : ''
                    }${
                      endpoint.requestBody ? ' \\\n  -H "Content-Type: application/json" \\\n  -d \'...\'' : ''
                    }`}
                  </pre>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* No Results */}
      {filteredEndpoints.length === 0 && (
        <div className="bg-white shadow rounded-lg p-12 text-center">
          <p className="text-gray-500">No endpoints found matching your criteria</p>
        </div>
      )}
    </div>
  );
}
