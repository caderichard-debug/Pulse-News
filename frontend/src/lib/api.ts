/**
 * API client for Pulse backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ApiError {
  detail: string;
}

class ApiClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
    // Load token from localStorage if available
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('token');
    }
  }

  setToken(token: string) {
    this.token = token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('token', token);
    }
  }

  clearToken() {
    this.token = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token');
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error: ApiError = await response.json().catch(() => ({
        detail: 'An error occurred',
      }));
      throw new Error(error.detail);
    }

    return response.json();
  }

  // Auth endpoints
  async register(data: {
    name: string;
    email: string;
    password: string;
    topic_ids?: number[];
  }) {
    return this.request<{
      access_token: string;
      token_type: string;
      user: Record<string, unknown>;
    }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async login(data: { email: string; password: string }) {
    return this.request<{
      access_token: string;
      token_type: string;
      user: Record<string, unknown>;
    }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getCurrentUser() {
    return this.request<Record<string, unknown>>('/auth/me');
  }

  async logout() {
    this.clearToken();
    return this.request('/auth/logout', { method: 'POST' });
  }

  // Preferences endpoints
  async getTopics() {
    return this.request<
      Array<{ id: number; name: string; description: string }>
    >('/preferences/topics');
  }

  async getPreferences() {
    return this.request<{
      user_id: number;
      topics: Array<{
        id: number;
        name: string;
        description: string;
        priority: number;
        is_active: boolean;
      }>;
    }>('/preferences');
  }

  async updatePreferences(preferences: Array<{
    topic_id: number;
    priority: number;
    is_active: boolean;
  }>) {
    return this.request('/preferences', {
      method: 'PUT',
      body: JSON.stringify({ preferences }),
    });
  }

  async subscribeToTopic(topicId: number, priority: number = 5) {
    return this.request(`/preferences/topics/${topicId}/subscribe`, {
      method: 'POST',
      body: JSON.stringify({ priority }),
    });
  }

  async unsubscribeFromTopic(topicId: number) {
    return this.request(`/preferences/topics/${topicId}/unsubscribe`, {
      method: 'POST',
    });
  }

  // Source preference endpoints
  async getSources() {
    return this.request<Array<{
      source_id: number;
      name: string;
      url: string;
      trust_score: number;
      political_lean: string | null;
      subscribed: boolean;
    }>>('/preferences/sources');
  }

  async updateSourcePreferences(sourceIds: number[]) {
    return this.request('/preferences/sources', {
      method: 'PUT',
      body: JSON.stringify({ source_ids: sourceIds }),
    });
  }

  // User settings endpoints
  async getSettings() {
    return this.request<{
      source_discovery_mode: string;
      article_order_preference: string;
      articles_per_topic_default: number;
    }>('/preferences/settings');
  }

  async updateSettings(settings: {
    source_discovery_mode?: string;
    article_order_preference?: string;
    articles_per_topic_default?: number;
  }) {
    return this.request('/preferences/settings', {
      method: 'PUT',
      body: JSON.stringify(settings),
    });
  }

  // Analytics endpoints
  async getUserStats() {
    return this.request<{
      articles_read: number;
      newsletters_received: number;
      topics_tracked: number;
      sources_subscribed: number;
      views_changed: number;
    }>('/analytics/user-stats');
  }

  async getSentimentOverTime(days: number = 30, topicIds?: string) {
    const params = new URLSearchParams({ days: days.toString() });
    if (topicIds) params.append('topic_ids', topicIds);
    return this.request<Array<{
      date: string;
      values: Record<string, number>;
    }>>(`/analytics/sentiment-over-time?${params}`);
  }

  async getBiasDistribution(weeks: number = 4) {
    return this.request<Array<{
      week: string;
      left: number;
      center: number;
      right: number;
    }>>(`/analytics/bias-distribution?weeks=${weeks}`);
  }

  async getFrameworkHeatmap(framework1Id: number, framework2Id: number, days: number = 30) {
    return this.request<Array<{
      x: number;
      y: number;
      article_count: number;
      avg_sentiment: number;
      sample_articles: Array<{ id: string; title: string }>;
    }>>(`/analytics/framework-heatmap?framework1_id=${framework1Id}&framework2_id=${framework2Id}&days=${days}`);
  }

  async getAvailableFrameworks() {
    return this.request<Array<{
      id: number;
      name: string;
      left_position: string;
      right_position: string;
    }>>('/analytics/frameworks/available');
  }
}

export const api = new ApiClient(API_BASE_URL);
