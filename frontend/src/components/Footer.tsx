'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';

export default function Footer() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;

    const checkAuth = async () => {
      try {
        const user = await api.getCurrentUser();
        if (mounted && user) {
          setIsAuthenticated(true);
        }
      } catch {
        if (mounted) {
          setIsAuthenticated(false);
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    // Wrap the async state updates in setTimeout to avoid React act() warnings in tests
    const timer = setTimeout(() => {
      checkAuth();
    }, 0);

    return () => {
      mounted = false;
      clearTimeout(timer);
    };
  }, []);

  if (loading) {
    return (
      <footer className="mt-auto w-full border-t border-border bg-card">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="text-center text-xs text-muted-foreground">
            © {new Date().getFullYear()} Pulse News. All rights reserved.
          </div>
        </div>
      </footer>
    );
  }

  return (
    <footer className="mt-auto w-full border-t border-border bg-card">
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Links Row */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-2 sm:gap-6 text-sm text-muted-foreground">
          <a
            href={process.env.NEXT_PUBLIC_DOCUMENTATION_URL || "https://docs.pulsenews.app"}
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-foreground transition-colors"
          >
            Documentation
          </a>

          <span className="hidden sm:inline">•</span>
          <a
            href="mailto:support@pulsenews.app"
            className="hover:text-foreground transition-colors"
          >
            Contact Us
          </a>

          {isAuthenticated && (
            <>
              <span className="hidden sm:inline">•</span>
              <a
                href="/preferences?tab=account"
                className="hover:text-foreground transition-colors"
              >
                Account Settings
              </a>
              <span className="hidden sm:inline">•</span>
              <a
                href="/preferences?tab=topics"
                className="hover:text-foreground transition-colors"
              >
                Newsletter Preferences
              </a>
            </>
          )}

          <span className="hidden sm:inline">•</span>
          <a
            href="/how-it-works"
            className="hover:text-foreground transition-colors"
          >
            How It Works
          </a>
          <span className="hidden sm:inline">•</span>
          <a
            href="/privacy-policy"
            className="hover:text-foreground transition-colors"
          >
            Privacy Policy
          </a>
        </div>

        {/* Copyright Row */}
        <div className="text-center text-xs text-muted-foreground mt-4">
          © {new Date().getFullYear()} Pulse News. All rights reserved.
        </div>
      </div>
    </footer>
  );
}
