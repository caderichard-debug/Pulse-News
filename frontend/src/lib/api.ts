// Pulse API client. Talks to a FastAPI backend.
// Configure with VITE_API_URL in Project Settings → Environment variables.

const configuredApiUrl = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "");

export const API_BASE =
  configuredApiUrl ||
  (import.meta.env.DEV ? "http://localhost:8000" : "https://api.pulsenews.app");

const TOKEN_KEY = "token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) window.localStorage.setItem(TOKEN_KEY, token);
  else window.localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  status: number;
  detail: unknown;
  constructor(status: number, message: string, detail?: unknown) {
    super(message);
    this.status = status;
    this.detail = detail;
  }
}

type FetchOpts = Omit<RequestInit, "body"> & {
  body?: unknown;
  query?: Record<string, string | number | boolean | undefined | null | (string | number)[]>;
  auth?: boolean;
};

function buildQuery(query?: FetchOpts["query"]): string {
  if (!query) return "";
  const params = new URLSearchParams();
  for (const [k, v] of Object.entries(query)) {
    if (v === undefined || v === null || v === "") continue;
    if (Array.isArray(v)) {
      for (const item of v) params.append(k, String(item));
    } else {
      params.append(k, String(v));
    }
  }
  const s = params.toString();
  return s ? `?${s}` : "";
}

export async function api<T = unknown>(path: string, opts: FetchOpts = {}): Promise<T> {
  const { body, query, auth = true, headers, ...rest } = opts;
  const url = `${API_BASE}${path}${buildQuery(query)}`;
  const finalHeaders: Record<string, string> = {
    Accept: "application/json",
    ...(headers as Record<string, string> | undefined),
  };
  if (body !== undefined && !(body instanceof FormData)) {
    finalHeaders["Content-Type"] = "application/json";
  }
  if (auth) {
    const t = getToken();
    if (t) finalHeaders["Authorization"] = `Bearer ${t}`;
  }

  let res: Response;
  try {
    res = await fetch(url, {
      ...rest,
      headers: finalHeaders,
      body:
        body === undefined
          ? undefined
          : body instanceof FormData
            ? body
            : JSON.stringify(body),
    });
  } catch (e) {
    throw new ApiError(0, "Network error — could not reach Pulse API");
  }

  const contentType = res.headers.get("content-type") || "";
  const isJson = contentType.includes("application/json");
  const payload = isJson ? await res.json().catch(() => null) : await res.text();

  if (!res.ok) {
    if (res.status === 401 && auth) {
      setToken(null);
    }
    const detail =
      isJson && payload && typeof payload === "object" && "detail" in payload
        ? (payload as { detail: unknown }).detail
        : payload;
    const msg =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((d) => (typeof d === "string" ? d : JSON.stringify(d))).join(", ")
          : `Request failed (${res.status})`;
    throw new ApiError(res.status, msg, detail);
  }

  return payload as T;
}
