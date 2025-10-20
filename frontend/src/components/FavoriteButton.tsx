'use client';

import { useState } from 'react';
import { api } from '@/lib/api';

interface FavoriteButtonProps {
  articleId: number;
  initialFavorited?: boolean;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  onToggle?: (isFavorited: boolean) => void;
}

export default function FavoriteButton({
  articleId,
  initialFavorited = false,
  size = 'md',
  showLabel = false,
  onToggle
}: FavoriteButtonProps) {
  const [isFavorited, setIsFavorited] = useState(initialFavorited);
  const [isLoading, setIsLoading] = useState(false);

  // Check authentication
  const isAuthenticated = typeof window !== 'undefined' && !!localStorage.getItem('token');

  const handleToggle = async (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent navigation if inside clickable card
    e.preventDefault();

    if (!isAuthenticated) {
      // Redirect to login
      window.location.href = '/login';
      return;
    }

    setIsLoading(true);
    try {
      if (isFavorited) {
        await api.removeFavorite(articleId);
        setIsFavorited(false);
        onToggle?.(false);
      } else {
        await api.addFavorite(articleId);
        setIsFavorited(true);
        onToggle?.(true);
      }
    } catch (error) {
      console.error('Failed to toggle favorite:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const sizeClasses = {
    sm: 'w-8 h-8 text-sm',
    md: 'w-10 h-10 text-base',
    lg: 'w-12 h-12 text-lg'
  };

  const iconSizes = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6'
  };

  return (
    <button
      onClick={handleToggle}
      disabled={isLoading}
      className={`${showLabel ? 'px-4 py-2' : sizeClasses[size]} rounded-full flex items-center justify-center gap-2
                 transition-all disabled:opacity-50 disabled:cursor-not-allowed
                 ${isFavorited
                   ? 'bg-amber-50 dark:bg-amber-900/20 hover:bg-amber-100 dark:hover:bg-amber-900/30 text-amber-500 dark:text-amber-400 border-2 border-amber-400 dark:border-amber-500'
                   : 'bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-400 dark:text-gray-500 border-2 border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
                 }`}
      title={isFavorited ? 'Remove from favorites' : 'Add to favorites'}
      aria-label={isFavorited ? 'Remove from favorites' : 'Add to favorites'}
    >
      {/* Star Icon */}
      <svg
        className={iconSizes[size]}
        fill={isFavorited ? 'currentColor' : 'none'}
        stroke="currentColor"
        strokeWidth="2"
        viewBox="0 0 24 24"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z"
        />
      </svg>

      {showLabel && (
        <span className="text-sm font-medium">
          {isFavorited ? 'Favorited' : 'Favorite'}
        </span>
      )}
    </button>
  );
}
