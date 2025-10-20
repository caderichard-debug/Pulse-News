'use client';


import { useRouter, usePathname } from 'next/navigation';
import { api } from '@/lib/api';
import React, { useEffect, useState, useRef } from 'react';
import Image from 'next/image';
import { Menu, X } from 'lucide-react';


export default function Navbar() {
  const router = useRouter();
  const pathname = usePathname();
  const [userName, setUserName] = useState<string | null>(null);
  const [isAdmin, setIsAdmin] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [isMenuOpen, setIsMenuOpen] = useState<boolean>(false);
  const [insightsDropdownOpen, setInsightsDropdownOpen] = useState<boolean>(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const insightsRef = useRef<HTMLDivElement>(null);

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

  // Close menu when clicking outside
  useEffect(() => {
    if (!isMenuOpen) return;

    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsMenuOpen(false);
      }
    };

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleEscape);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isMenuOpen]);

  // Close insights dropdown when clicking outside
  useEffect(() => {
    if (!insightsDropdownOpen) return;

    const handleClickOutside = (event: MouseEvent) => {
      if (insightsRef.current && !insightsRef.current.contains(event.target as Node)) {
        setInsightsDropdownOpen(false);
      }
    };

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setInsightsDropdownOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleEscape);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [insightsDropdownOpen]);

  // Close menu when pathname changes (user navigates)
  useEffect(() => {
    setIsMenuOpen(false);
    setInsightsDropdownOpen(false);
  }, [pathname]);

  const handleLogout = () => {
    api.clearToken();
    router.push('/');
  };

  // Check if user is authenticated
  const isAuthenticated = !!userName;

  // Navigation items - simplified for all users
  const navItems = [
    { name: 'Feed', path: '/feed', icon: '📰', authRequired: true, adminOnly: false },
    { name: 'Insights', path: '/insights', icon: '🔍', authRequired: false, adminOnly: false },
    { name: 'Preferences', path: '/preferences', icon: '⚙️', authRequired: true, adminOnly: false },
    { name: 'How It Works', path: '/how-it-works', icon: '💡', authRequired: false, adminOnly: false },
    { name: 'Admin', path: '/admin', icon: '⚡', authRequired: true, adminOnly: true },
  ];

  return (
    <nav className="bg-card border-b border-border transition-colors" ref={menuRef}>
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Mobile Menu Button (far left) */}
          <button
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            className="lg:hidden p-2 rounded-md text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
            aria-label="Navigation menu"
            aria-expanded={isMenuOpen}
          >
            {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>

          {/* Logo/Brand */}
          <div className="flex items-center">
            <button
              onClick={() => router.push('/')}
              className="flex items-center gap-2 text-2xl font-bold text-primary hover:text-primary-hover transition-colors"
            >
              <Image
                src="/pulse-icon.png"
                alt="Pulse Logo"
                width={32}
                height={32}
                className="w-8 h-8 object-contain"
              />
              <span className="hidden sm:inline">Pulse</span>
            </button>
          </div>

          {/* Desktop Navigation Links (hidden on mobile) */}
          <div className="hidden lg:flex items-center gap-1 absolute left-1/2 transform -translate-x-1/2">
            {navItems
              .filter((item) => (!item.authRequired || isAuthenticated) && (!item.adminOnly || isAdmin))
              .map((item) => {
                // Special handling for Insights dropdown
                if (item.path === '/insights') {
                  const isActive = pathname === '/insights' || pathname === '/analyze' || pathname === '/sources' || pathname === '/analytics';
                  return (
                    <div key={item.path} className="relative" ref={insightsRef}>
                      <button
                        onClick={() => setInsightsDropdownOpen(!insightsDropdownOpen)}
                        className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex flex-col xl:flex-row xl:gap-1 items-center ${
                          isActive
                            ? 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-400'
                            : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                        }`}
                      >
                        <span className="text-lg xl:text-base">{item.icon}</span>
                        <span className="text-xs xl:text-sm whitespace-nowrap">{item.name}</span>
                        <span className="text-xs">▼</span>
                      </button>

                      {/* Dropdown Menu */}
                      {insightsDropdownOpen && (
                        <div className="absolute top-full left-0 mt-1 w-48 bg-card border border-border rounded-lg shadow-lg py-2 z-50">
                          <button
                            onClick={() => router.push('/analyze')}
                            className="w-full text-left px-4 py-2 text-sm text-foreground hover:bg-accent transition-colors flex items-center gap-2"
                          >
                            <span>🔍</span>
                            <span>Analyze</span>
                          </button>
                          <button
                            onClick={() => router.push('/sources')}
                            className="w-full text-left px-4 py-2 text-sm text-foreground hover:bg-accent transition-colors flex items-center gap-2"
                          >
                            <span>📑</span>
                            <span>Sources</span>
                          </button>
                          <button
                            onClick={() => router.push('/analytics')}
                            className="w-full text-left px-4 py-2 text-sm text-foreground hover:bg-accent transition-colors flex items-center gap-2"
                          >
                            <span>📊</span>
                            <span>Analytics</span>
                          </button>
                          <div className="border-t border-border my-1"></div>
                          <button
                            onClick={() => router.push('/insights')}
                            className="w-full text-left px-4 py-2 text-sm text-muted-foreground hover:bg-accent hover:text-foreground transition-colors flex items-center gap-2"
                          >
                            <span>🏠</span>
                            <span>Insights Home</span>
                          </button>
                        </div>
                      )}
                    </div>
                  );
                }

                // Regular nav items
                return (
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
                    className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex flex-col xl:flex-row xl:gap-1 items-center ${
                      pathname === item.path || (item.path === '/admin' && pathname.startsWith('/admin'))
                        ? item.adminOnly
                          ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
                          : 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-400'
                        : item.adminOnly
                        ? 'text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20'
                        : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                    }`}
                  >
                    <span className="text-lg xl:text-base">{item.icon}</span>
                    <span className="text-xs xl:text-sm whitespace-nowrap">{item.name}</span>
                  </button>
                );
              })}
          </div>

          {/* Right side - Auth buttons or user menu */}
          <div className="flex items-center gap-2">
            {loading ? (
              // Loading state
              <div className="w-20 h-8"></div>
            ) : isAuthenticated ? (
              // Authenticated user
              <>
                <button
                  onClick={() => router.push('/preferences')}
                  className="px-4 py-2 rounded-md text-sm font-medium transition-colors text-muted-foreground hover:bg-accent hover:text-accent-foreground hidden sm:block"
                >
                  {userName}
                </button>
                <button
                  onClick={handleLogout}
                  className="px-4 py-2 rounded-md text-sm font-medium transition-colors text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                >
                  Logout
                </button>
              </>
            ) : (
              // Unauthenticated user
              <button
                onClick={() => router.push('/login')}
                className="px-4 py-2 rounded-md text-sm font-medium transition-colors bg-primary text-white hover:bg-primary-hover"
              >
                Log In
              </button>
            )}
          </div>
        </div>

        {/* Mobile Menu Dropdown */}
        {isMenuOpen && (
          <div
            className="lg:hidden border-t border-border animate-slideDown"
            aria-hidden={!isMenuOpen}
          >
            <div className="py-2 space-y-1">
              {navItems
                .filter((item) => (!item.authRequired || isAuthenticated) && (!item.adminOnly || isAdmin))
                .map((item) => (
                  <button
                    key={item.path}
                    onClick={() => router.push(item.path)}
                    className={`w-full text-left px-4 py-3 text-sm font-medium transition-colors flex items-center gap-2 ${
                      pathname === item.path ||
                      (item.path === '/admin' && pathname.startsWith('/admin')) ||
                      (item.path === '/insights' && (pathname === '/analyze' || pathname === '/sources' || pathname === '/analytics'))
                        ? item.adminOnly
                          ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
                          : 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-400'
                        : item.adminOnly
                        ? 'text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20'
                        : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                    }`}
                  >
                    <span>{item.icon}</span>
                    <span>{item.name}</span>
                  </button>
                ))}
              {/* Contact us link in mobile menu */}
              <a
                href="mailto:support@pulsenews.app"
                className="w-full text-left px-4 py-3 text-sm font-medium transition-colors flex items-center gap-2 text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              >
                <span>✉️</span>
                <span>Contact us</span>
              </a>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
}
