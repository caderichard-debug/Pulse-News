import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Article, Source, Topic, Paginated } from "@/lib/types";
import { ArticleCard } from "@/components/ArticleCard";
import { Search, ChevronLeft, ChevronRight } from "lucide-react";
import { FilterChip } from "@/components/ui/filter-chip";
import { FilterSelect } from "@/components/ui/filter-select";
import { Button } from "@/components/ui/button";

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
    sort: typeof search.sort === "string" ? search.sort : "newest",
    fav: search.fav === true || search.fav === "true",
  }),
  head: () => ({
    meta: [
      { title: "Your feed — Pulse" },
      {
        name: "description",
        content: "Personalized news with summaries, sentiment, and ethical lens analysis.",
      },
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
  const [loadError, setLoadError] = useState<string | null>(null);
  const [searchInput, setSearchInput] = useState(search.q);

  useEffect(() => {
    setSearchInput(search.q);
  }, [search.q]);

  useEffect(() => {
    api<Array<{ name: string; article_count: number }>>("/feed/topics", { auth: false })
      .then((r) =>
        setTopics(
          (r ?? []).map((topic) => ({
            id: topic.name,
            name: topic.name,
          })),
        ),
      )
      .catch(() => {});
    api<Source[] | { items: Source[] }>("/feed/sources", { auth: false })
      .then((r) => setSources(Array.isArray(r) ? r : r?.items || []))
      .catch(() => {});
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setLoadError(null);
    const params: Record<string, string | number | boolean | (string | number)[] | undefined> = {
      page: search.page,
      page_size: PAGE_SIZE,
      search: search.q || undefined,
      sort_by: search.sort,
      favorites_only: search.fav || undefined,
    };
    if (search.topic) params.topics = [search.topic];
    if (search.lean) params.political_leans = [search.lean];

    api<Paginated<Article> | { articles: Article[]; total_count: number } | Article[]>(
      "/feed/articles",
      { query: params },
    )
      .then((res) => {
        if (cancelled) return;
        const items = Array.isArray(res) ? res : "articles" in res ? res.articles : res.items || [];
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
          const msg = err instanceof ApiError ? err.message : "Could not load feed";
          setLoadError(msg);
          toast.error(msg);
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
      search: (prev) => ({
        page: patch.page ?? 1,
        q: patch.q ?? prev.q ?? "",
        topic: patch.topic ?? prev.topic ?? "",
        lean: patch.lean ?? prev.lean ?? "",
        sort: patch.sort ?? prev.sort ?? "newest",
        fav: patch.fav ?? prev.fav ?? false,
      }),
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
    <div className="max-w-[1024px] mx-auto px-6 py-8 md:py-10">
      <header className="flex flex-col gap-5 mb-8 md:mb-10">
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
          <label htmlFor="feed-search" className="sr-only">
            Search stories
          </label>
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
          <input
            id="feed-search"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search stories…"
            className="w-full pl-10 pr-3 py-2.5 bg-background border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-ring text-sm"
          />
        </form>

        <div className="flex flex-col gap-4">
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <span className="text-muted-foreground mr-2 uppercase tracking-wide text-xs">
              Topic
            </span>
            <FilterChip selected={!search.topic} onClick={() => update({ topic: "" })}>
              All
            </FilterChip>
            {topics.slice(0, 8).map((t) => (
              <FilterChip
                key={t.id}
                selected={search.topic === t.name}
                onClick={() => update({ topic: t.name })}
              >
                {t.name}
              </FilterChip>
            ))}
          </div>

          <div className="flex flex-wrap items-center gap-3 text-sm">
            <FilterSelect
              label="Lean"
              value={search.lean}
              onValueChange={(value) => update({ lean: value })}
              options={leanOptions.map((option) => ({ value: option.v, label: option.label }))}
              triggerClassName="h-9 w-[10.5rem] bg-background"
            />
            <FilterSelect
              label="Sort"
              value={search.sort}
              onValueChange={(value) => update({ sort: value })}
              options={[
                { value: "newest", label: "Most recent" },
                { value: "oldest", label: "Oldest first" },
                { value: "sentiment_high", label: "Most positive" },
                { value: "sentiment_low", label: "Most negative" },
              ]}
              triggerClassName="h-9 w-[10.5rem] bg-background"
            />
            {user && (
              <FilterChip
                size="md"
                selected={search.fav}
                onClick={() => update({ fav: !search.fav })}
              >
                {search.fav ? "Saved" : "Show saved"}
              </FilterChip>
            )}
          </div>
        </div>
      </header>

      <div className="border-t-[3px] border-foreground" />

      {loading ? (
        <div className="py-20 text-center text-muted-foreground">Loading the day's coverage…</div>
      ) : loadError ? (
        <div className="py-20 text-center">
          <p className="text-destructive mb-3">We couldn't load your feed right now.</p>
          <p className="text-sm text-muted-foreground mb-6">{loadError}</p>
          <Button onClick={() => update({ page: search.page })} variant="outline" size="default">
            Try again
          </Button>
        </div>
      ) : articles.length === 0 ? (
        <div className="py-20 text-center text-muted-foreground">
          <p className="mb-4">No articles match these filters.</p>
          <Button
            onClick={() =>
              navigate({
                to: "/feed",
                search: { page: 1, q: "", topic: "", lean: "", sort: "newest", fav: false },
              })
            }
            variant="outline"
            size="default"
          >
            Clear filters
          </Button>
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
          <Button
            disabled={search.page <= 1}
            onClick={() => update({ page: search.page - 1 })}
            variant="ghost"
            size="sm"
            className="text-muted-foreground"
          >
            <ChevronLeft className="size-4" /> Newer
          </Button>
          <span className="text-muted-foreground tabular-nums text-xs uppercase tracking-wider">
            Page {search.page} of {totalPages}
          </span>
          <Button
            disabled={search.page >= totalPages}
            onClick={() => update({ page: search.page + 1 })}
            variant="ghost"
            size="sm"
            className="text-foreground"
          >
            Older <ChevronRight className="size-4" />
          </Button>
        </div>
      )}
    </div>
  );
}
