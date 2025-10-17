'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { api } from '@/lib/api';

type Theme = 'light' | 'dark';

interface ThemeContextType {
  theme: Theme;
  toggleTheme: () => void;
  setTheme: (theme: Theme) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<Theme>('light');
  const [mounted, setMounted] = useState(false);

  // Initialize theme from localStorage or system preference
  useEffect(() => {
    console.log('🚀 ThemeProvider initializing...');
    setMounted(true);
    const savedTheme = localStorage.getItem('theme') as Theme | null;
    console.log('💾 Theme from localStorage:', savedTheme);

    if (savedTheme) {
      console.log('✅ Using saved theme:', savedTheme);
      setThemeState(savedTheme);
      applyTheme(savedTheme);
    } else {
      // Check system preference
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      const initialTheme = prefersDark ? 'dark' : 'light';
      console.log('🖥️ System preference:', prefersDark ? 'dark' : 'light');
      console.log('✅ Using system theme:', initialTheme);
      setThemeState(initialTheme);
      applyTheme(initialTheme);
    }
  }, []);

  // Apply theme to document root
  const applyTheme = (newTheme: Theme) => {
    const root = document.documentElement;
    console.log('🎨 Applying theme:', newTheme);
    console.log('📋 Before - classList:', Array.from(root.classList));

    if (newTheme === 'dark') {
      root.classList.add('dark');
      root.classList.remove('light');
    } else {
      root.classList.add('light');
      root.classList.remove('dark');
    }

    console.log('📋 After - classList:', Array.from(root.classList));
    console.log('✅ Theme applied successfully');
  };

  const setTheme = async (newTheme: Theme) => {
    console.log('🔄 setTheme called with:', newTheme);
    console.log('💾 Current theme in state:', theme);

    setThemeState(newTheme);
    localStorage.setItem('theme', newTheme);
    console.log('💾 Saved to localStorage:', newTheme);

    applyTheme(newTheme);

    // Sync with backend (best effort, don't block on failure)
    try {
      await api.updateSettings({ theme_preference: newTheme });
      console.log('☁️ Synced with backend successfully');
    } catch (error) {
      console.warn('Failed to sync theme preference with backend:', error);
    }
  };

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    console.log('🔀 Toggle theme - current:', theme, '→ new:', newTheme);
    setTheme(newTheme);
  };

  // Prevent flash of unstyled content
  if (!mounted) {
    return null;
  }

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
