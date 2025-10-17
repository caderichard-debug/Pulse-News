'use client';

import { useTheme } from '@/contexts/ThemeContext';

export default function DarkModeToggle() {
  const { theme, toggleTheme } = useTheme();

  const getThemeIcon = () => {
    switch (theme) {
      case 'light':
        return (
          <svg
            className="w-5 h-5 text-foreground"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
            />
          </svg>
        );
      case 'dark':
        return (
          <svg
            className="w-5 h-5 text-foreground"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
            />
          </svg>
        );
      case 'auto':
        return (
          <svg
            className="w-5 h-5 text-foreground"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
            />
          </svg>
        );
    }
  };

  const getThemeLabel = () => {
    switch (theme) {
      case 'light':
        return 'Light';
      case 'dark':
        return 'Dark';
      case 'auto':
        return 'Auto';
    }
  };

  const getNextTheme = () => {
    switch (theme) {
      case 'dark':
        return 'light';
      case 'light':
        return 'auto';
      case 'auto':
        return 'dark';
    }
  };

  return (
    <button
      onClick={toggleTheme}
      className="relative inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg border border-border bg-card hover:bg-accent transition-colors"
      aria-label={`Current theme: ${theme}. Click to switch to ${getNextTheme()} mode`}
      title={`Theme: ${getThemeLabel()} (click to cycle)`}
    >
      {getThemeIcon()}
      <span className="text-sm font-medium text-foreground">{getThemeLabel()}</span>
    </button>
  );
}
