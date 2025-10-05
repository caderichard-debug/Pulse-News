import { ApiClient } from '../api';

global.fetch = jest.fn();

describe('ApiClient', () => {
  let api: ApiClient;
  const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;

  beforeEach(() => {
    mockFetch.mockClear();
    localStorage.clear();
    api = new ApiClient('http://localhost:8000');
  });

  describe('Authentication', () => {
    it('should login and return response', async () => {
      const mockResponse = {
        access_token: 'test-token',
        token_type: 'bearer',
        user: { id: 1, email: 'test@example.com' }
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response);

      const result = await api.login({ email: 'test@example.com', password: 'password' });

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/auth/login',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: 'test@example.com', password: 'password' }),
        })
      );

      expect(result).toEqual(mockResponse);

      // Token must be set manually by the caller
      api.setToken(result.access_token);
      expect(localStorage.getItem('token')).toBe('test-token');
    });

    it('should register new user', async () => {
      const mockResponse = {
        access_token: 'test-token',
        token_type: 'bearer',
        user: { id: 1, email: 'new@example.com' }
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response);

      const result = await api.register({ name: 'Test User', email: 'new@example.com', password: 'password' });

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/auth/register',
        expect.objectContaining({
          method: 'POST',
        })
      );

      expect(result).toEqual(mockResponse);
    });

    it('should include auth token in requests', async () => {
      // Set token and recreate api instance so it loads the token
      localStorage.setItem('token', 'test-token');
      api = new ApiClient('http://localhost:8000');

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ topics: [] }),
      } as Response);

      await api.getPreferences();

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/preferences',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token',
          }),
        })
      );
    });

    it('should clear token on logout', () => {
      localStorage.setItem('token', 'test-token');
      api.clearToken();
      expect(localStorage.getItem('token')).toBeNull();
    });
  });

  describe('Preferences', () => {
    beforeEach(() => {
      localStorage.setItem('token', 'test-token');
      api = new ApiClient('http://localhost:8000');
    });

    it('should get preferences', async () => {
      const mockPrefs = {
        user_id: 1,
        topics: [
          { id: 1, name: 'Politics', description: 'Political news', priority: 5, is_active: true }
        ]
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockPrefs,
      } as Response);

      const result = await api.getPreferences();
      expect(result).toEqual(mockPrefs);
    });

    it('should get sources', async () => {
      const mockSources = [
        { source_id: 1, name: 'Reuters', url: 'https://reuters.com', trust_score: 0.95, subscribed: false }
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSources,
      } as Response);

      const result = await api.getSources();
      expect(result).toEqual(mockSources);
    });

    it('should get settings', async () => {
      const mockSettings = {
        source_discovery_mode: 'some',
        article_order_preference: 'mixed',
        articles_per_topic_default: 5
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSettings,
      } as Response);

      const result = await api.getSettings();
      expect(result).toEqual(mockSettings);
    });

    it('should update preferences', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ message: 'Updated' }),
      } as Response);

      await api.updatePreferences([{ topic_id: 1, priority: 8, is_active: true }]);

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/preferences',
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify({ preferences: [{ topic_id: 1, priority: 8, is_active: true }] }),
        })
      );
    });
  });

  describe('Analytics', () => {
    beforeEach(() => {
      localStorage.setItem('token', 'test-token');
      api = new ApiClient('http://localhost:8000');
    });

    it('should get user stats', async () => {
      const mockStats = {
        articles_read: 50,
        newsletters_received: 10,
        topics_tracked: 5,
        sources_subscribed: 8,
        views_changed: 3
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockStats,
      } as Response);

      const result = await api.getUserStats();
      expect(result).toEqual(mockStats);
    });

    it('should get sentiment over time', async () => {
      const mockData = [
        { date: '2025-10-01', values: { Politics: -2.3, Technology: 4.5 } }
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      } as Response);

      const result = await api.getSentimentOverTime(30);
      expect(result).toEqual(mockData);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('days=30'),
        expect.any(Object)
      );
    });
  });

  describe('Feed', () => {
    beforeEach(() => {
      localStorage.setItem('token', 'test-token');
      api = new ApiClient('http://localhost:8000');
    });

    it('should get feed articles with filters', async () => {
      const mockFeed = {
        articles: [
          { id: 1, title: 'Test Article', source_name: 'Reuters', sentiment_score: 5.0 }
        ],
        total_count: 1,
        page: 1,
        page_size: 20
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockFeed,
      } as Response);

      const result = await api.getFeedArticles({
        page: 1,
        topic: 'politics',
        sort_by: 'newest'
      });

      expect(result).toEqual(mockFeed);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('topic=politics'),
        expect.any(Object)
      );
    });

    it('should get article detail', async () => {
      const mockArticle = {
        id: 1,
        title: 'Test Article',
        summary: 'Test summary',
        statistics: [],
        frameworks: [],
        related_articles: [],
        context: null
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockArticle,
      } as Response);

      const result = await api.getArticleDetail(1);
      expect(result).toEqual(mockArticle);
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/articles/1',
        expect.any(Object)
      );
    });
  });

  describe('Error Handling', () => {
    beforeEach(() => {
      localStorage.setItem('token', 'test-token');
      api = new ApiClient('http://localhost:8000');
    });

    it('should throw error on failed request', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
      } as Response);

      await expect(api.getPreferences()).rejects.toThrow();
    });

    it('should throw error on network failure', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      await expect(api.getPreferences()).rejects.toThrow('Network error');
    });
  });
});
