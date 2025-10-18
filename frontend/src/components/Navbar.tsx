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
  const menuRef = useRef<HTMLDivElement>(null);

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

  // Close menu when pathname changes (user navigates)
  useEffect(() => {
    setIsMenuOpen(false);
  }, [pathname]);

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
              onClick={() => router.push('/feed')}
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
                  <span className="text-lg xl:text-base">{item.icon}</span>
                  <span className="text-xs xl:text-sm whitespace-nowrap">{item.name}</span>
                </button>
              ))}
          </div>

          {/* User name and Logout Button */}
          <div className="flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors text-muted-foreground">
            <button
              onClick={() => router.push('/preferences')}
              className="ml-1 pl-1 hover:text-foreground transition-colors hidden sm:block"
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

        {/* Mobile Menu Dropdown */}
        {isMenuOpen && (
          <div
            className="lg:hidden border-t border-border animate-slideDown"
            aria-hidden={!isMenuOpen}
          >
            <div className="py-2 space-y-1">
              {navItems
                .filter((item) => !item.adminOnly || isAdmin)
                .map((item) => (
                  <button
                    key={item.path}
                    onClick={() => router.push(item.path)}
                    className={`w-full text-left px-4 py-3 text-sm font-medium transition-colors flex items-center gap-2 ${
                      pathname === item.path || (item.path === '/admin' && pathname.startsWith('/admin'))
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
            </div>
          </div>
        )}
      </div>
    </nav>
  );
}
