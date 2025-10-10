/**
 * Date utility functions for consistent date formatting across the app.
 *
 * The backend stores and sends dates as UTC timestamps without timezone info.
 * We need to explicitly treat them as UTC to avoid timezone conversion issues.
 */

/**
 * Format a date string as a relative time (e.g., "5h ago", "2d ago") or absolute date.
 *
 * @param dateString - ISO date string from backend (UTC without 'Z' suffix)
 * @returns Formatted time string
 */
export function formatTimeAgo(dateString: string): string {
  // Parse the date string and treat it as UTC (backend sends UTC timestamps)
  const date = new Date(dateString + 'Z'); // Append 'Z' to treat as UTC
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMinutes = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);

  // Handle edge cases
  if (diffMs < 0) {
    // Article is from the future (clock skew), show absolute date
    return date.toLocaleDateString();
  }

  if (diffMinutes < 1) return 'Just now';
  if (diffMinutes < 60) return `${diffMinutes}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)}w ago`;

  // For older articles, show absolute date
  return date.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
}

/**
 * Format a date string as a localized date string.
 *
 * @param dateString - ISO date string from backend (UTC without 'Z' suffix)
 * @param options - Intl.DateTimeFormat options
 * @returns Formatted date string
 */
export function formatDate(
  dateString: string,
  options?: Intl.DateTimeFormatOptions
): string {
  // Parse the date string and treat it as UTC
  const date = new Date(dateString + 'Z');

  const defaultOptions: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    ...options
  };

  return date.toLocaleDateString(undefined, defaultOptions);
}

/**
 * Format a date string as a full date and time string.
 *
 * @param dateString - ISO date string from backend (UTC without 'Z' suffix)
 * @returns Formatted date and time string
 */
export function formatDateTime(dateString: string): string {
  const date = new Date(dateString + 'Z');

  return date.toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}
