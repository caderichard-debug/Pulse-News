// Shared types for Pulse. Server is the source of truth — these are best-effort
// shapes for UI rendering; we treat unknown fields defensively.

export type User = {
  id: string | number;
  email: string;
  name?: string;
  avatar_url?: string;
};

export type AuthResponse = {
  access_token: string;
  token_type?: string;
  user: User;
};

export type Topic = {
  id: string | number;
  name: string;
  slug?: string;
  description?: string;
};

export type Source = {
  id: string | number;
  name: string;
  url?: string;
  bias?: "left" | "center-left" | "center" | "center-right" | "right" | string;
  trust_score?: number;
  active?: boolean;
  description?: string;
};

export type Framework = {
  id: string | number;
  name: string;
  axis_left?: string;
  axis_right?: string;
  description?: string;
};

export type FrameworkPlacement = {
  framework: Framework;
  position: number; // -1 to 1
  explanation?: string;
  relevance?: number;
};

export type StatVerification = {
  id?: string | number;
  claim: string;
  verdict?: "verified" | "unverified" | "disputed" | "false" | string;
  source_url?: string;
  confidence?: number;
  notes?: string;
};

export type Article = {
  id: string | number;
  title: string;
  summary?: string;
  content?: string;
  url?: string;
  image_url?: string;
  published_at?: string;
  source?: Source;
  source_id?: string | number;
  topics?: Topic[];
  sentiment?: "positive" | "neutral" | "negative" | string;
  sentiment_score?: number;
  political_lean?: number; // -1..1
  political_lean_label?: string;
  is_favorited?: boolean;
  is_analyzed?: boolean;
  has_verified_stats?: boolean;
  frameworks?: FrameworkPlacement[];
  statistics?: StatVerification[];
  related_articles?: Article[];
  context?: { title?: string; body?: string }[] | { body?: string };
  reading_time_minutes?: number;
};

export type Paginated<T> = {
  items: T[];
  total_count: number;
  page?: number;
  page_size?: number;
};
