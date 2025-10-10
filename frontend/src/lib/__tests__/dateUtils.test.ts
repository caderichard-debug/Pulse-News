import { formatTimeAgo, formatDate, formatDateTime } from '../dateUtils';

describe('dateUtils', () => {
  // Mock Date.now() to have a consistent baseline for tests
  const mockNow = new Date('2025-10-10T20:00:00Z');

  beforeAll(() => {
    jest.useFakeTimers();
    jest.setSystemTime(mockNow);
  });

  afterAll(() => {
    jest.useRealTimers();
  });

  describe('formatTimeAgo', () => {
    it('should format "Just now" for very recent articles (< 1 minute)', () => {
      const dateString = '2025-10-10 19:59:30'; // 30 seconds ago
      expect(formatTimeAgo(dateString)).toBe('Just now');
    });

    it('should format minutes ago correctly', () => {
      const dateString = '2025-10-10 19:45:00'; // 15 minutes ago
      expect(formatTimeAgo(dateString)).toBe('15m ago');
    });

    it('should format hours ago correctly', () => {
      const dateString = '2025-10-10 15:00:00'; // 5 hours ago
      expect(formatTimeAgo(dateString)).toBe('5h ago');
    });

    it('should format days ago correctly', () => {
      const dateString = '2025-10-08 20:00:00'; // 2 days ago
      expect(formatTimeAgo(dateString)).toBe('2d ago');
    });

    it('should format weeks ago correctly', () => {
      const dateString = '2025-09-26 20:00:00'; // 14 days ago (2 weeks)
      expect(formatTimeAgo(dateString)).toBe('2w ago');
    });

    it('should format old dates as absolute dates (> 30 days)', () => {
      const dateString = '2025-08-01 20:00:00'; // ~70 days ago
      const result = formatTimeAgo(dateString);
      // Should be a formatted date like "Aug 1, 2025"
      expect(result).toMatch(/Aug/);
      expect(result).toMatch(/2025/);
    });

    it('should handle future dates (clock skew)', () => {
      const dateString = '2025-10-11 20:00:00'; // 1 day in the future
      const result = formatTimeAgo(dateString);
      // Should return an absolute date
      expect(result).toMatch(/10\/11\/2025|11\/10\/2025/); // Handles different locale formats
    });

    it('should treat dates as UTC by appending Z', () => {
      // Test that we're correctly treating the date as UTC
      const dateString = '2025-10-10 19:00:00'; // 1 hour ago in UTC
      expect(formatTimeAgo(dateString)).toBe('1h ago');
    });
  });

  describe('formatDate', () => {
    it('should format dates with default options', () => {
      const dateString = '2025-10-09 20:00:00';
      const result = formatDate(dateString);
      expect(result).toMatch(/Oct/);
      expect(result).toMatch(/9/);
      expect(result).toMatch(/2025/);
    });

    it('should format dates with custom options', () => {
      const dateString = '2025-10-09 20:00:00';
      const result = formatDate(dateString, {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
      expect(result).toMatch(/October/);
      expect(result).toMatch(/9/);
      expect(result).toMatch(/2025/);
    });

    it('should treat dates as UTC and convert to local time', () => {
      const dateString = '2025-10-09 12:00:00'; // Noon UTC
      const result = formatDate(dateString);
      // Should contain a date (exact day may vary by timezone, but should be valid)
      expect(result).toMatch(/2025/);
      expect(result).toMatch(/Oct/);
      // The day could be 8 or 9 depending on timezone
      expect(result).toMatch(/[89]/);
    });
  });

  describe('formatDateTime', () => {
    it('should format date and time', () => {
      const dateString = '2025-10-09 14:30:00';
      const result = formatDateTime(dateString);
      expect(result).toMatch(/Oct/);
      expect(result).toMatch(/9/);
      expect(result).toMatch(/2025/);
      // Time formatting can vary by locale, but should have time component
      expect(result.length).toBeGreaterThan(10); // More than just a date
    });
  });
});
