'use client';


import { useRouter, usePathname } from 'next/navigation';
import { api } from '@/lib/api';
import React, { useEffect, useState } from 'react';


export default function Navbar() {
  const router = useRouter();
  const pathname = usePathname();
  const [userName, setUserName] = useState<string | null>(null);
  const [isAdmin, setIsAdmin] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    let mounted = true;
    api.getCurrentUser()
      .then((user: { name: string; is_admin?: boolean }) => {
        if (mounted && user && typeof user.name === 'string') {
          setUserName(user.name);
          setIsAdmin(user.is_admin || false);
        }
      })
      .catch(() => {})
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => { mounted = false; };
  }, []);

  const handleLogout = () => {
    api.clearToken();
    router.push('/');
  };

  const navItems = [
    { name: 'Feed', path: '/feed', icon: '📰' },
    { name: 'Sources', path: '/sources', icon: '📑' },
    { name: 'Analytics', path: '/analytics', icon: '📊' },
    { name: 'Preferences', path: '/preferences', icon: '⚙️' },
    { name: 'How It Works', path: '/how-it-works', icon: '💡' },
  ];

  return (
    <nav className="bg-white border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo/Brand */}
          <div className="flex items-center">
            <button
              onClick={() => router.push('/feed')}
              className="text-2xl font-bold text-indigo-400 hover:text-indigo-700 transition-colors"
            >
              Pulse
            </button>
          </div>

          {/* Navigation Links */}
          <div className="flex items-center gap-1 absolute left-1/2 transform -translate-x-1/2 flex items-center gap-1">
            {navItems.map((item) => (
              <button
                key={item.path}
                onClick={() => router.push(item.path)}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  pathname === item.path
                    ? 'bg-indigo-50 text-indigo-700'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`}
              >
                <span className="mr-1">{item.icon}</span>
                {item.name}
              </button>
            ))}
          </div>

          {/* User name, Admin Link, and Logout Button */}
          <div className="flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors text-gray-600 hover:text-gray-900">
            <button
              onClick={() => router.push('/preferences')}
              className="ml-1 pl-1 hover:text-gray-600 transition-colors"
            >
            {loading ? null : userName && (
              <span>{userName}</span>
            )}
            </button>
            {!loading && isAdmin && (
              <button
                onClick={() => router.push('/admin')}
                className="px-3 py-1 bg-red-600 text-white rounded-md text-xs font-semibold hover:bg-red-700 transition-colors"
              >
                ⚡ Admin
              </button>
            )}
            <button
              onClick={handleLogout}
              className="px-4 py-2 rounded-md text-sm font-medium transition-colors text-gray-600 hover:bg-gray-50 hover:text-gray-900"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}
