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
      // Handle auth errors by redirecting to login
      if (response.status === 401 || response.status === 403) {
        this.clearToken();
        if (typeof window !== 'undefined'
          && !window.location.pathname.includes('/login')
          && window.location.pathname !== '/') {
          window.location.href = '/login';
        }
      }

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
    try {
      return this.request<{
        id: number;
        email: string;
        name: string;
        is_admin?: boolean;
        is_active?: boolean;
        email_verified?: boolean;
        created_at?: string;
        last_login?: string;
      }>('/auth/me');
    } catch {
      return null;
    }
  }

  async logout() {
    this.clearToken();
    return this.request('/auth/logout', { method: 'POST' });
  }

  async requestPasswordReset(data: { email: string }) {
    return this.request<{ message: string }>('/auth/request-password-reset', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async resetPassword(data: { token: string; new_password: string }) {
    return this.request<{ message: string }>('/auth/reset-password', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async verifyResetToken(token: string) {
    return this.request<{ valid: boolean; expires_at: string; message: string }>(
      `/auth/verify-reset-token/${token}`
    );
  }

  async verifyEmail(token: string) {
    return this.request<{ message: string }>('/auth/verify-email', {
      method: 'POST',
      body: JSON.stringify({ token }),
    });
  }

  async resendVerificationEmail() {
    return this.request<{ message: string }>('/auth/resend-verification-email', {
      method: 'POST',
    });
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
        is_active: boolean;
      }>;
    }>('/preferences');
  }

  async updatePreferences(preferences: Array<{
    topic_id: number;
    is_active: boolean;
  }>) {
    return this.request('/preferences', {
      method: 'PUT',
      body: JSON.stringify({ preferences }),
    });
  }

  async subscribeToTopic(topicId: number) {
    return this.request(`/preferences/topics/${topicId}/subscribe`, {
      method: 'POST',
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
      organizational_bias: string | null;
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

  // Feed endpoints
  async getFeedArticles(params?: {
    page?: number;
    page_size?: number;
    topic?: string;
    source_id?: number;
    political_lean?: string;
    sort_by?: string;
    only_analyzed?: boolean;
    only_verified_stats?: boolean;
  }) {
    const queryParams = new URLSearchParams();
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.page_size) queryParams.append('page_size', params.page_size.toString());
    if (params?.topic) queryParams.append('topic', params.topic);
    if (params?.source_id) queryParams.append('source_id', params.source_id.toString());
    if (params?.political_lean) queryParams.append('political_lean', params.political_lean);
    if (params?.sort_by) queryParams.append('sort_by', params.sort_by);
    if (params?.only_analyzed) queryParams.append('only_analyzed', params.only_analyzed.toString());
    if (params?.only_verified_stats) queryParams.append('only_verified_stats', params.only_verified_stats.toString());

    return this.request<{
      articles: Array<{
        id: number;
        title: string;
        url: string;
        published_at: string;
        source_name: string;
        source_id: number;
        source_bias: string | null;
        topic_category: string | null;
        summary: string | null;
        sentiment_score: number | null;
        political_lean: string | null;
        primary_framework: string | null;
        framework_position: number | null;
        read_time_minutes: number | null;
        stats_count: number;
        stats_verified_count: number;
        has_stats: boolean;
      }>;
      total_count: number;
      page: number;
      page_size: number;
    }>(`/feed/articles?${queryParams}`);
  }

  async getFeedTopics() {
    return this.request<Array<{
      name: string;
      article_count: number;
    }>>('/feed/topics');
  }

  async getFeedSources() {
    return this.request<Array<{
      id: number;
      name: string;
      url: string;
      article_count: number;
    }>>('/feed/sources');
  }

  // Article detail endpoints
  async getArticleDetail(articleId: number) {
    return this.request<{
      id: number;
      title: string;
      url: string;
      published_at: string;
      source_name: string;
      source_url: string;
      source_bias: string | null;
      topic_category: string | null;
      content_preview: string;
      read_time_minutes: number | null;
      summary: string | null;
      sentiment_score: number | null;
      political_lean: string | null;
      statistics: Array<{
        statistic: string;
        verification_status: string;
        confidence: number | null;
        source_name: string | null;
        source_url: string | null;
        source_credibility_score: number | null;
        fact_check_status: string | null;
        fact_check_source: string | null;
      }>;
      frameworks: Array<{
        framework_id: number;
        framework_name: string;
        left_position: string;
        right_position: string;
        position_on_axis: number;
        relevance_score: number;
        explanation: string | null;
      }>;
      related_articles: Array<{
        id: number;
        title: string;
        source_name: string;
        published_at: string;
        sentiment_score: number | null;
        political_lean: string | null;
        url: string;
      }>;
      context: {
        background: string | null;
        key_players: string | null;
        timeline: string | null;
        significance: string | null;
      } | null;
    }>(`/articles/${articleId}`);
  }

  // Sources endpoints
  async getAllSources(params?: {
    bias?: string;
    active_only?: boolean;
    sort_by?: string;
  }) {
    const queryParams = new URLSearchParams();
    if (params?.bias) queryParams.append('bias', params.bias);
    if (params?.active_only !== undefined) queryParams.append('active_only', params.active_only.toString());
    if (params?.sort_by) queryParams.append('sort_by', params.sort_by);

    return this.request<{
      sources: Array<{
        id: number;
        name: string;
        url: string;
        rss_feed_url: string;
        description: string | null;
        trust_score: number;
        organizational_bias: string | null;
        bias_description: string | null;
        is_active: boolean;
        created_at: string;
        article_count: number;
      }>;
      total_count: number;
    }>(`/sources?${queryParams}`);
  }

  async createSource(data: {
    name: string;
    url: string;
    rss_feed_url: string;
    description?: string;
    trust_score?: number;
    fetch_bias?: boolean;
  }) {
    return this.request('/sources', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Admin panel endpoints
  private async adminRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    // Admin requests now use the regular JWT token
    // The backend will verify the user has is_admin=true
    return this.request(endpoint, options);
  }

  async getAdminDashboard() {
    return this.adminRequest<{
      system_stats: {
        users: { total: number; admins: number };
        articles: { total: number; today: number };
        sources: { total: number; active: number };
        frameworks: { total: number };
      };
      recent_jobs: Array<{
        id: number;
        job_id: string;
        job_name: string;
        status: string;
        started_at: string;
        completed_at?: string;
        duration_seconds?: number;
        items_processed?: number;
        error_message?: string;
      }>;
      active_jobs: Array<{
        id: number;
        job_id: string;
        job_name: string;
        started_at: string;
        duration_seconds: number;
      }>;
      error_summary: {
        failed_jobs_24h: number;
      };
      recent_admin_actions: Array<{
        id: number;
        admin_email: string;
        action_type: string;
        resource_type: string;
        timestamp: string;
      }>;
      timestamp: string;
    }>('/admin-panel/dashboard');
  }

  async getJobHistory(params?: {
    limit?: number;
    offset?: number;
    job_id?: string;
    status?: string;
  }) {
    const queryParams = new URLSearchParams();
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.offset) queryParams.append('offset', params.offset.toString());
    if (params?.job_id) queryParams.append('job_id', params.job_id);
    if (params?.status) queryParams.append('status', params.status);

    return this.adminRequest<{
      jobs: Array<{
        id: number;
        job_id: string;
        job_name: string;
        status: string;
        started_at: string;
        completed_at?: string;
        duration_seconds?: number;
        items_processed?: number;
        api_calls_made?: number;
        tokens_used?: number;
        triggered_by: string;
        error_message?: string;
      }>;
      total_count: number;
      limit: number;
      offset: number;
    }>(`/admin-panel/jobs/history?${queryParams}`);
  }

  async triggerJob(jobId: string) {
    return this.adminRequest<{
      status: string;
      job_id: string;
      job_name: string;
      execution_id: number;
      result: {
        status: string;
        duration_seconds: number;
        items_processed?: number;
        error_message?: string;
      };
    }>(`/admin-panel/jobs/trigger/${jobId}`, {
      method: 'POST',
    });
  }

  async getAdminUsers(params?: {
    limit?: number;
    page?: number;
    search?: string;
    is_admin?: boolean;
  }) {
    const queryParams = new URLSearchParams();
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.search) queryParams.append('search', params.search);
    if (params?.is_admin !== undefined) queryParams.append('is_admin', params.is_admin.toString());

    return this.adminRequest<{
      users: Array<{
        id: number;
        email: string;
        name: string;
        is_admin: boolean;
        is_active: boolean;
        email_verified: boolean;
        subscription_tier: string;
        created_at: string;
        last_login?: string;
        admin_notes?: string;
      }>;
      total_count: number;
      page: number;
      page_size: number;
      total_pages: number;
    }>(`/admin-panel/users?${queryParams}`);
  }

  async toggleUserAdmin(userId: number, isAdmin: boolean) {
    return this.adminRequest(`/admin-panel/users/${userId}/admin`, {
      method: 'PUT',
      body: JSON.stringify({ is_admin: isAdmin }),
    });
  }

  async deleteUser(userId: number) {
    return this.adminRequest(`/admin-panel/users/${userId}`, {
      method: 'DELETE',
    });
  }

  async getAdminSources(params?: {
    limit?: number;
    offset?: number;
    is_active?: boolean;
  }) {
    const queryParams = new URLSearchParams();
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.offset) queryParams.append('offset', params.offset.toString());
    if (params?.is_active !== undefined) queryParams.append('is_active', params.is_active.toString());

    return this.adminRequest<{
      sources: Array<{
        id: number;
        name: string;
        url: string;
        rss_feed_url: string;
        is_active: boolean;
        political_lean?: string;
        organizational_bias?: string;
        trust_score: number;
        article_count: number;
      }>;
      total_count: number;
      limit: number;
      offset: number;
    }>(`/admin-panel/sources?${queryParams}`);
  }

  async updateAdminSource(sourceId: number, data: {
    name?: string;
    url?: string;
    rss_feed_url?: string;
    is_active?: boolean;
    trust_score?: number;
  }) {
    return this.adminRequest(`/admin-panel/sources/${sourceId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteAdminSource(sourceId: number) {
    return this.adminRequest(`/admin-panel/sources/${sourceId}`, {
      method: 'DELETE',
    });
  }

  async getAdminArticles(params?: {
    limit?: number;
    offset?: number;
    source_id?: number;
    processing_status?: string;
  }) {
    const queryParams = new URLSearchParams();
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.offset) queryParams.append('offset', params.offset.toString());
    if (params?.source_id) queryParams.append('source_id', params.source_id.toString());
    if (params?.processing_status) queryParams.append('processing_status', params.processing_status);

    return this.adminRequest<{
      articles: Array<{
        id: number;
        title: string;
        source_name: string;
        url: string;
        processing_status: string;
        scraped_at: string;
        published_at?: string;
      }>;
      total_count: number;
      limit: number;
      offset: number;
    }>(`/admin-panel/articles?${queryParams}`);
  }

  async deleteAdminArticle(articleId: number) {
    return this.adminRequest(`/admin-panel/articles/${articleId}`, {
      method: 'DELETE',
    });
  }

  async getAuditLog(params?: {
    limit?: number;
    offset?: number;
    action_type?: string;
    admin_email?: string;
  }) {
    const queryParams = new URLSearchParams();
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.offset) queryParams.append('offset', params.offset.toString());
    if (params?.action_type) queryParams.append('action_type', params.action_type);
    if (params?.admin_email) queryParams.append('admin_email', params.admin_email);

    return this.adminRequest<{
      logs: Array<{
        id: number;
        admin_email: string;
        action_type: string;
        resource_type: string;
        resource_id?: string;
        old_value?: string;
        new_value?: string;
        ip_address?: string;
        timestamp: string;
        notes?: string;
      }>;
      total_count: number;
      limit: number;
      offset: number;
    }>(`/admin-panel/audit?${queryParams}`);
  }
}

export { ApiClient };
export const api = new ApiClient(API_BASE_URL);
