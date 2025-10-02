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
}

export const api = new ApiClient(API_BASE_URL);
