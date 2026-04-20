import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Article, Source, Topic, Paginated } from "@/lib/types";
import { ArticleCard } from "@/components/ArticleCard";
import { Search, ChevronLeft, ChevronRight } from "lucide-react";

type FeedSearch = {
  page: number;
  q: string;
  topic: string;
  lean: string;
  sort: string;
  fav: boolean;
};

export const Route = createFileRoute("/_app/feed")({
  validateSearch: (search: Record<string, unknown>): FeedSearch => ({
    page: Number(search.page) || 1,
    q: typeof search.q === "string" ? search.q : "",
    topic: typeof search.topic === "string" ? search.topic : "",
    lean: typeof search.lean === "string" ? search.lean : "",
    sort: typeof search.sort === "string" ? search.sort : "recent",
    fav: search.fav === true || search.fav === "true",
  }),
  head: () => ({
    meta: [
      { title: "Your feed — Pulse" },
      { name: "description", content: "Personalized news with summaries, sentiment, and ethical lens analysis." },
    ],
  }),
  component: FeedPage,
});

const PAGE_SIZE = 10;

function FeedPage() {
  const search = Route.useSearch();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [articles, setArticles] = useState<Article[]>([]);
  const [total, setTotal] = useState(0);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchInput, setSearchInput] = useState(search.q);

  useEffect(() => {
    setSearchInput(search.q);
  }, [search.q]);

  useEffect(() => {
    api<Topic[] | { items: Topic[] }>("/feed/topics", { auth: false })
      .then((r) => setTopics(Array.isArray(r) ? r : r?.items || []))
      .catch(() => {});
    api<Source[] | { items: Source[] }>("/feed/sources", { auth: false })
      .then((r) => setSources(Array.isArray(r) ? r : r?.items || []))
      .catch(() => {});
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    const params: Record<string, string | number | boolean | (string | number)[] | undefined> = {
      page: search.page,
      page_size: PAGE_SIZE,
      search: search.q || undefined,
      sort_by: search.sort,
      favorites_only: search.fav || undefined,
    };
    if (search.topic) params.topics = [search.topic];
    if (search.lean) params.political_leans = [search.lean];

    api<Paginated<Article> | Article[]>("/feed/articles", { query: params })
      .then((res) => {
        if (cancelled) return;
        const items = Array.isArray(res) ? res : res.items || [];
        const count = Array.isArray(res) ? items.length : res.total_count || items.length;
        setArticles(items);
        setTotal(count);
      })
      .catch((err) => {
        if (cancelled) return;
        if (err instanceof ApiError && err.status === 0) {
          // Backend not configured yet — show empty state silently
          setArticles([]);
          setTotal(0);
        } else {
          toast.error(err instanceof ApiError ? err.message : "Could not load feed");
        }
      })
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [search.page, search.q, search.topic, search.lean, search.sort, search.fav]);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  function update(patch: Partial<FeedSearch>) {
    navigate({
      to: "/feed",
      search: (prev: FeedSearch) => ({ ...prev, ...patch, page: patch.page ?? 1 }),
    });
  }

  async function toggleFav(article: Article) {
    if (!user) {
      toast.message("Sign in to save articles");
      return;
    }
    const wasFav = !!article.is_favorited;
    setArticles((prev) =>
      prev.map((a) => (a.id === article.id ? { ...a, is_favorited: !wasFav } : a)),
    );
    try {
      if (wasFav) {
        await api(`/favorites/articles/${article.id}`, { method: "DELETE" });
      } else {
        await api(`/favorites/articles/${article.id}`, { method: "POST" });
      }
    } catch (err) {
      setArticles((prev) =>
        prev.map((a) => (a.id === article.id ? { ...a, is_favorited: wasFav } : a)),
      );
      toast.error(err instanceof ApiError ? err.message : "Could not update favorite");
    }
  }

  const leanOptions = useMemo(
    () => [
      { v: "", label: "All spectrum" },
      { v: "left", label: "Left" },
      { v: "center-left", label: "Center-Left" },
      { v: "center", label: "Center" },
      { v: "center-right", label: "Center-Right" },
      { v: "right", label: "Right" },
    ],
    [],
  );

  return (
    <div className="max-w-[1024px] mx-auto px-6 py-12">
      <header className="flex flex-col gap-6 mb-12">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground mb-3">
            {search.fav ? "Saved articles" : "Today's coverage"}
          </p>
          <h1 className="font-serif text-4xl md:text-5xl font-medium tracking-tight">
            {search.fav ? "Your library" : "The Pulse"}
          </h1>
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            update({ q: searchInput });
          }}
          className="relative max-w-md"
        >
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
          <input
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search stories…"
            className="w-full pl-10 pr-3 py-2.5 bg-background border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-ring text-sm"
          />
        </form>

        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <span className="text-muted-foreground mr-2 uppercase tracking-wider text-xs">
              Topic
            </span>
            <button
              onClick={() => update({ topic: "" })}
              className={chip(!search.topic)}
            >
              All
            </button>
            {topics.slice(0, 8).map((t) => (
              <button
                key={t.id}
                onClick={() => update({ topic: String(t.slug || t.id) })}
                className={chip(search.topic === String(t.slug || t.id))}
              >
                {t.name}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-4 text-sm">
            <label className="flex items-center gap-2 text-muted-foreground">
              <span className="uppercase tracking-wider text-xs">Lean</span>
              <select
                value={search.lean}
                onChange={(e) => update({ lean: e.target.value })}
                className="bg-transparent border-b border-border pb-0.5 focus:outline-none text-foreground"
              >
                {leanOptions.map((o) => (
                  <option key={o.v} value={o.v}>
                    {o.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex items-center gap-2 text-muted-foreground">
              <span className="uppercase tracking-wider text-xs">Sort</span>
              <select
                value={search.sort}
                onChange={(e) => update({ sort: e.target.value })}
                className="bg-transparent border-b border-border pb-0.5 focus:outline-none text-foreground"
              >
                <option value="recent">Most recent</option>
                <option value="impact">Impact</option>
                <option value="trending">Trending</option>
              </select>
            </label>
            {user && (
              <button
                onClick={() => update({ fav: !search.fav })}
                className={`text-xs uppercase tracking-wider px-2 py-1 rounded border ${
                  search.fav
                    ? "border-foreground text-foreground"
                    : "border-border text-muted-foreground hover:text-foreground"
                }`}
              >
                {search.fav ? "Saved" : "Show saved"}
              </button>
            )}
          </div>
        </div>
      </header>

      <div className="border-t-[3px] border-foreground" />

      {loading ? (
        <div className="py-20 text-center text-muted-foreground">Loading the day's coverage…</div>
      ) : articles.length === 0 ? (
        <div className="py-20 text-center text-muted-foreground">
          No articles match these filters.
        </div>
      ) : (
        <div className="flex flex-col">
          {articles.map((a) => (
            <ArticleCard key={a.id} article={a} onToggleFavorite={toggleFav} />
          ))}
        </div>
      )}

      {sources.length > 0 && articles.length > 0 && (
        <div className="mt-16 pt-6 border-t-[3px] border-border flex items-center justify-between text-sm font-medium">
          <button
            disabled={search.page <= 1}
            onClick={() => update({ page: search.page - 1 })}
            className="text-muted-foreground hover:text-foreground transition-colors flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <ChevronLeft className="size-4" /> Newer
          </button>
          <span className="text-muted-foreground tabular-nums text-xs uppercase tracking-wider">
            Page {search.page} of {totalPages}
          </span>
          <button
            disabled={search.page >= totalPages}
            onClick={() => update({ page: search.page + 1 })}
            className="text-foreground hover:text-muted-foreground transition-colors flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Older <ChevronRight className="size-4" />
          </button>
        </div>
      )}
    </div>
  );
}

function chip(active: boolean) {
  return `px-3 py-1 rounded-full transition-colors ${
    active
      ? "bg-primary text-primary-foreground"
      : "border border-border text-muted-foreground hover:border-foreground hover:text-foreground"
  }`;
}
