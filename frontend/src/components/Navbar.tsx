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
      .then((user) => {
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
    { name: 'Feed', path: '/feed', icon: '📰', adminOnly: false },
    { name: 'Analyze', path: '/analyze', icon: '🔍', adminOnly: false },
    { name: 'Sources', path: '/sources', icon: '📑', adminOnly: false },
    { name: 'Analytics', path: '/analytics', icon: '📊', adminOnly: false },
    { name: 'Preferences', path: '/preferences', icon: '⚙️', adminOnly: false },
    { name: 'How It Works', path: '/how-it-works', icon: '💡', adminOnly: false },
    { name: 'Admin', path: '/admin', icon: '⚡', adminOnly: true },
  ];

  return (
    <nav className="bg-card border-b border-border transition-colors">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo/Brand */}
          <div className="flex items-center">
            <button
              onClick={() => router.push('/feed')}
              className="text-2xl font-bold text-primary hover:text-primary-hover transition-colors"
            >
              Pulse
            </button>
          </div>

          {/* Navigation Links */}
          <div className="flex items-center gap-1 absolute left-1/2 transform -translate-x-1/2 flex items-center gap-1">
            {navItems
              .filter((item) => !item.adminOnly || isAdmin)
              .map((item) => (
                <button
                  key={item.path}
                  onClick={() => {
                    if (item.path === '/analyze' && pathname === '/analyze') {
                      // Reset the analyze page by navigating to clean URL
                      router.push('/analyze');
                      window.location.href = '/analyze';
                    } else {
                      router.push(item.path);
                    }
                  }}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    pathname === item.path || (item.path === '/admin' && pathname.startsWith('/admin'))
                      ? item.adminOnly
                        ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
                        : 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-400'
                      : item.adminOnly
                      ? 'text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20'
                      : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                  }`}
                >
                  <span className="mr-1">{item.icon}</span>
                  <span className="whitespace-nowrap">{item.name}</span>
                </button>
              ))}
          </div>

          {/* User name and Logout Button */}
          <div className="flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors text-muted-foreground">
            <button
              onClick={() => router.push('/preferences')}
              className="ml-1 pl-1 hover:text-foreground transition-colors"
            >
            {loading ? null : userName && (
              <span>{userName}</span>
            )}
            </button>
            <button
              onClick={handleLogout}
              className="px-4 py-2 rounded-md text-sm font-medium transition-colors text-muted-foreground hover:bg-accent hover:text-accent-foreground"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}
