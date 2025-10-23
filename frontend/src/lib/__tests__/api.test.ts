import { ApiClient } from '../api';

// Mock fetch
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

  describe('getOpposingViewpoints', () => {
    beforeEach(() => {
      localStorage.setItem('token', 'test-token');
      api = new ApiClient('http://localhost:8000');
    });

    it('should make correct API call with default parameters', async () => {
      const mockResponse = {
        article_id: 1,
        article_title: 'Test Article',
        opposing_viewpoints: [
          {
            article_id: 2,
            title: 'Opposing Article',
            url: 'https://example.com/opposing',
            source_name: 'Test Source',
            relationship_type: 'framework_opposition',
            opposition_strength: 0.85,
            ai_explanation: 'This represents a fundamentally different ideological framework',
            sentiment_score: -2.5,
            published_date: '2025-01-20T10:00:00Z',
            frameworks: [
              {
                name: 'Libertarian Framework',
                position: -8,
                description: 'Emphasizes individual liberty and limited government'
              }
            ]
          }
        ],
        total_count: 1,
        has_ai_explanations: true,
        ai_generation_status: 'completed'
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response);

      const result = await api.getOpposingViewpoints(1);

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/articles/1/opposing-viewpoints',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token',
            'Content-Type': 'application/json',
          }),
        })
      );

      expect(result).toEqual(mockResponse);
    });

    it('should pass all parameters correctly', async () => {
      const mockResponse = { opposing_viewpoints: [], total_count: 0 };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response);

      await api.getOpposingViewpoints(123, {
        maxResults: 10,
        relationshipTypes: ['framework_opposition', 'sentiment_contrast']
      });

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/articles/123/opposing-viewpoints?max_results=10&relationship_types=framework_opposition%2Csentiment_contrast',
        expect.any(Object)
      );
    });

    it('should handle single relationship type', async () => {
      const mockResponse = { opposing_viewpoints: [], total_count: 0 };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response);

      await api.getOpposingViewpoints(456, {
        relationshipTypes: ['source_bias_contrast']
      });

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/articles/456/opposing-viewpoints?relationship_types=source_bias_contrast',
        expect.any(Object)
      );
    });

    it('should handle empty relationship types array', async () => {
      const mockResponse = { opposing_viewpoints: [], total_count: 0 };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response);

      await api.getOpposingViewpoints(789, {
        relationshipTypes: []
      });

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/articles/789/opposing-viewpoints?relationship_types=',
        expect.any(Object)
      );
    });

    it('should handle successful response with complex viewpoints', async () => {
      const mockResponse = {
        article_id: 42,
        article_title: 'Climate Policy Analysis',
        opposing_viewpoints: [
          {
            article_id: 43,
            title: 'Free Market Approach to Climate',
            url: 'https://example.com/free-market-climate',
            source_name: 'Economic Review',
            relationship_type: 'framework_opposition',
            opposition_strength: 0.92,
            ai_explanation: 'Contrasts government regulation with market-based solutions',
            sentiment_score: 3.2,
            published_date: '2025-01-19T15:30:00Z',
            frameworks: [
              {
                name: 'Free Market Framework',
                position: 9,
                description: 'Emphasizes market solutions and minimal regulation'
              },
              {
                name: 'Environmental Protection Framework',
                position: -7,
                description: 'Prioritizes environmental regulation and government action'
              }
            ]
          },
          {
            article_id: 44,
            title: 'Climate Justice Perspective',
            url: 'https://example.com/climate-justice',
            source_name: 'Social Policy Journal',
            relationship_type: 'framework_opposition',
            opposition_strength: 0.78,
            ai_explanation: 'Focuses on social equity and environmental justice',
            sentiment_score: -1.8,
            published_date: '2025-01-20T09:15:00Z',
            frameworks: [
              {
                name: 'Social Justice Framework',
                position: -6,
                description: 'Emphasizes equity and justice in policy decisions'
              }
            ]
          }
        ],
        total_count: 2,
        has_ai_explanations: true,
        ai_generation_status: 'completed'
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response);

      const result = await api.getOpposingViewpoints(42);

      expect(result.opposing_viewpoints).toHaveLength(2);
      expect(result.has_ai_explanations).toBe(true);
      expect(result.opposing_viewpoints[0].frameworks).toHaveLength(2);
      expect(result.opposing_viewpoints[0].opposition_strength).toBe(0.92);
    });

    it('should handle empty results response', async () => {
      const mockResponse = {
        article_id: 999,
        article_title: 'Article with No Opposition',
        opposing_viewpoints: [],
        total_count: 0,
        has_ai_explanations: false,
        ai_generation_status: 'completed'
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response);

      const result = await api.getOpposingViewpoints(999);

      expect(result.opposing_viewpoints).toEqual([]);
      expect(result.total_count).toBe(0);
      expect(result.has_ai_explanations).toBe(false);
    });

    it('should handle OpenAI unavailable error', async () => {
      const mockResponse = {
        detail: 'AI explanations temporarily unavailable. Please try again later.',
        error_code: 'ai_unavailable'
      };

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 503,
        json: async () => mockResponse,
      } as Response);

      await expect(api.getOpposingViewpoints(1)).rejects.toThrow('AI explanations temporarily unavailable. Please try again later.');
    });

    it('should handle rate limit error', async () => {
      const mockResponse = {
        detail: 'Rate limit exceeded for AI analysis. Please try again later.',
        error_code: 'rate_limit_exceeded',
        retry_after: 60
      };

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 429,
        json: async () => mockResponse,
      } as Response);

      await expect(api.getOpposingViewpoints(1)).rejects.toThrow('Rate limit exceeded for AI analysis. Please try again later.');
    });

    it('should handle unauthorized error', async () => {
      const mockResponse = {
        detail: 'Could not validate credentials'
      };

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => mockResponse,
      } as Response);

      await expect(api.getOpposingViewpoints(1)).rejects.toThrow();
    });

    it('should handle article not found error', async () => {
      const mockResponse = {
        detail: 'Article not found'
      };

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => mockResponse,
      } as Response);

      await expect(api.getOpposingViewpoints(99999)).rejects.toThrow();
    });

    it('should handle network errors', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      await expect(api.getOpposingViewpoints(1)).rejects.toThrow('Network error');
    });

    it('should handle malformed JSON response', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => {
          throw new Error('Unexpected token in JSON');
        },
      } as Response);

      await expect(api.getOpposingViewpoints(1)).rejects.toThrow();
    });

    it('should handle timeout errors', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Request timeout'));

      await expect(api.getOpposingViewpoints(1)).rejects.toThrow('Request timeout');
    });

    it('should include authorization header when token is set', async () => {
      localStorage.setItem('token', 'bearer-token-123');
      api = new ApiClient('http://localhost:8000');

      const mockResponse = { opposing_viewpoints: [], total_count: 0 };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response);

      await api.getOpposingViewpoints(1);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer bearer-token-123',
          }),
        })
      );
    });

    it('should handle response without AI explanations (partial data)', async () => {
      const mockResponse = {
        article_id: 1,
        article_title: 'Test Article',
        opposing_viewpoints: [
          {
            article_id: 2,
            title: 'Opposing Article',
            url: 'https://example.com/opposing',
            source_name: 'Test Source',
            relationship_type: 'framework_opposition',
            opposition_strength: 0.75,
            ai_explanation: null, // No AI explanation available
            sentiment_score: 1.2,
            published_date: '2025-01-20T10:00:00Z',
            frameworks: []
          }
        ],
        total_count: 1,
        has_ai_explanations: false,
        ai_generation_status: 'completed'
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response);

      const result = await api.getOpposingViewpoints(1);

      expect(result.opposing_viewpoints[0].ai_explanation).toBeNull();
      expect(result.has_ai_explanations).toBe(false);
    });
  });
});
