'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const checkAdminAuth = async () => {
      try {
        // Check if user is logged in
        const token = localStorage.getItem('token');
        if (!token) {
          router.push('/login');
          return;
        }

        // Check if admin token exists
        const adminToken = localStorage.getItem('admin_token');
        if (!adminToken && pathname !== '/admin') {
          setIsLoading(false);
          return;
        }

        if (adminToken) {
          // Verify admin token is still valid
          await api.verifyAdminToken(adminToken);
          setIsAuthenticated(true);
        }
      } catch (error) {
        console.error('Admin auth check failed:', error);
        localStorage.removeItem('admin_token');
        setIsAuthenticated(false);
      } finally {
        setIsLoading(false);
      }
    };

    checkAdminAuth();
  }, [router, pathname]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Verifying admin access...</p>
        </div>
      </div>
    );
  }

  // Show auth page if not authenticated (handled in page.tsx)
  if (!isAuthenticated && pathname === '/admin') {
    return <>{children}</>;
  }

  // Redirect if trying to access admin pages without auth
  if (!isAuthenticated) {
    router.push('/admin');
    return null;
  }

  const navItems = [
    { href: '/admin', label: 'Dashboard', icon: '📊' },
    { href: '/admin/database', label: 'Database', icon: '🗄️' },
    { href: '/admin/jobs', label: 'Jobs', icon: '⚙️' },
    { href: '/admin/users', label: 'Users', icon: '👥' },
    { href: '/admin/sources', label: 'Sources', icon: '📰' },
    { href: '/admin/articles', label: 'Articles', icon: '📄' },
    { href: '/admin/audit', label: 'Audit Log', icon: '📋' },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Admin Header */}
      <header className="bg-red-800 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold">⚡ Pulse Admin Panel</h1>
              <span className="px-3 py-1 bg-red-900 rounded-full text-xs font-semibold">
                ADMIN MODE
              </span>
            </div>
            <div className="flex items-center space-x-4">
              <Link
                href="/dashboard"
                className="px-4 py-2 bg-red-700 hover:bg-red-600 rounded-lg text-sm font-medium transition-colors"
              >
                ← Back to App
              </Link>
              <button
                onClick={() => {
                  localStorage.removeItem('admin_token');
                  router.push('/admin');
                }}
                className="px-4 py-2 bg-red-900 hover:bg-red-800 rounded-lg text-sm font-medium transition-colors"
              >
                Lock Admin Panel
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8 overflow-x-auto">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`
                    flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm whitespace-nowrap transition-colors
                    ${
                      isActive
                        ? 'border-red-600 text-red-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }
                  `}
                >
                  <span>{item.icon}</span>
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>
  );
}
