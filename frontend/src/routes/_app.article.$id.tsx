import { createFileRoute, Link, useParams } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Star, ExternalLink, ArrowLeft } from "lucide-react";
import { toast } from "sonner";
import { api, ApiError } from "@/lib/api";
import type { Article, FrameworkPlacement, StatVerification } from "@/lib/types";
import { LeanMeter, SentimentDot, VerifiedBadge } from "@/components/Signals";
import { ArticleCard } from "@/components/ArticleCard";
import { useAuth } from "@/lib/auth";
import { timeAgo } from "@/lib/utils";

export const Route = createFileRoute("/_app/article/$id")({
  head: () => ({ meta: [{ title: "Article — Pulse" }] }),
  component: ArticlePage,
});

function ArticlePage() {
  const { id } = useParams({ from: "/_app/article/$id" });
  const { user } = useAuth();
  const [article, setArticle] = useState<Article | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api<Article>(`/articles/${id}`)
      .then((a) => !cancelled && setArticle(a))
      .catch((err) => !cancelled && setError(err instanceof ApiError ? err.message : "Could not load article"))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [id]);

  async function toggleFav() {
    if (!article) return;
    if (!user) return toast.message("Sign in to save articles");
    const wasFav = !!article.is_favorited;
    setArticle({ ...article, is_favorited: !wasFav });
    try {
      if (wasFav) await api(`/favorites/articles/${article.id}`, { method: "DELETE" });
      else await api(`/favorites/articles/${article.id}`, { method: "POST" });
    } catch (err) {
      setArticle({ ...article, is_favorited: wasFav });
      toast.error(err instanceof ApiError ? err.message : "Could not update");
    }
  }

  if (loading) {
    return <div className="max-w-[760px] mx-auto px-6 py-20 text-muted-foreground">Loading article…</div>;
  }
  if (error || !article) {
    return (
      <div className="max-w-[760px] mx-auto px-6 py-20 text-center">
        <p className="text-destructive mb-4">{error || "Article not found"}</p>
        <Link to="/feed" className="underline underline-offset-4">
          Back to feed
        </Link>
      </div>
    );
  }

  const ctxBlocks: { title?: string; body?: string }[] = Array.isArray(article.context)
    ? article.context
    : article.context && "body" in article.context && article.context.body
      ? [{ body: article.context.body }]
      : [];

  return (
    <article className="max-w-[760px] mx-auto px-6 py-12">
      <Link
        to="/feed"
        className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground mb-10"
      >
        <ArrowLeft className="size-4" /> Back to feed
      </Link>

      <header className="mb-10">
        <div className="flex flex-wrap items-center gap-3 text-xs uppercase tracking-wider text-muted-foreground mb-6">
          <div className="flex items-center gap-2">
            <span className="size-2 rounded-full bg-foreground" />
            <span className="text-foreground font-medium">{article.source?.name || "Unknown"}</span>
          </div>
          <span>·</span>
          <time>{timeAgo(article.published_at)}</time>
          {article.reading_time_minutes && (
            <>
              <span>·</span>
              <span>{article.reading_time_minutes} min read</span>
            </>
          )}
        </div>

        <h1 className="font-serif text-4xl md:text-6xl font-medium tracking-tight leading-[1.05] text-balance">
          {article.title}
        </h1>

        {article.summary && (
          <p className="mt-6 text-xl text-muted-foreground leading-relaxed text-pretty">
            {article.summary}
          </p>
        )}

        <div className="mt-8 flex flex-wrap items-center gap-4">
          <button
            onClick={toggleFav}
            className={`inline-flex items-center gap-2 px-3 py-2 rounded-md border text-sm transition-colors ${
              article.is_favorited
                ? "bg-primary text-primary-foreground border-primary"
                : "border-border hover:bg-accent"
            }`}
          >
            <Star className="size-4" fill={article.is_favorited ? "currentColor" : "none"} />
            {article.is_favorited ? "Saved" : "Save"}
          </button>
          {article.url && (
            <a
              href={article.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-3 py-2 rounded-md border border-border hover:bg-accent text-sm transition-colors"
            >
              Read original <ExternalLink className="size-3.5" />
            </a>
          )}
        </div>
      </header>

      {/* Analysis bar */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12 p-6 border border-border rounded-lg bg-card">
        <Stat label="Sentiment">
          <SentimentDot sentiment={article.sentiment} />
        </Stat>
        <Stat label="Political lean">
          <LeanMeter score={article.political_lean} showLabel />
        </Stat>
        <Stat label="Verification">
          {article.has_verified_stats ? (
            <VerifiedBadge>Statistics verified</VerifiedBadge>
          ) : (
            <span className="text-sm text-muted-foreground">Not verified</span>
          )}
        </Stat>
      </section>

      {ctxBlocks.length > 0 && (
        <section className="mb-12">
          <SectionTitle>Context</SectionTitle>
          <div className="space-y-4 prose-content">
            {ctxBlocks.map((c, i) => (
              <div key={i}>
                {c.title && <h3 className="font-serif text-xl font-medium mt-4 mb-2">{c.title}</h3>}
                {c.body && <p className="text-base text-foreground/90 leading-relaxed">{c.body}</p>}
              </div>
            ))}
          </div>
        </section>
      )}

      {article.frameworks && article.frameworks.length > 0 && (
        <section className="mb-12">
          <SectionTitle>Ethical frameworks</SectionTitle>
          <div className="space-y-6">
            {article.frameworks.map((fp, i) => (
              <FrameworkAxis key={i} placement={fp} />
            ))}
          </div>
        </section>
      )}

      {article.statistics && article.statistics.length > 0 && (
        <section className="mb-12">
          <SectionTitle>Statistic verification</SectionTitle>
          <div className="space-y-3">
            {article.statistics.map((s, i) => (
              <StatRow key={i} stat={s} />
            ))}
          </div>
        </section>
      )}

      {article.related_articles && article.related_articles.length > 0 && (
        <section className="mt-16 border-t-[3px] border-foreground pt-10">
          <SectionTitle>Related coverage</SectionTitle>
          <div className="flex flex-col">
            {article.related_articles.slice(0, 3).map((a) => (
              <ArticleCard key={a.id} article={a} compact />
            ))}
          </div>
        </section>
      )}
    </article>
  );
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="text-xs uppercase tracking-[0.2em] text-muted-foreground mb-6 pb-3 border-b border-border">
      {children}
    </h2>
  );
}

function Stat({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <p className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground mb-2">{label}</p>
      {children}
    </div>
  );
}

function FrameworkAxis({ placement }: { placement: FrameworkPlacement }) {
  const { framework, position, explanation } = placement;
  const pos = Math.max(-1, Math.min(1, position ?? 0));
  const left = ((pos + 1) / 2) * 100;
  return (
    <div className="border border-border rounded-lg p-5 bg-card">
      <div className="flex items-baseline justify-between mb-3">
        <h3 className="font-serif text-lg font-medium">{framework?.name}</h3>
      </div>
      <div className="flex items-center gap-3 mb-3 text-xs text-muted-foreground">
        <span className="font-medium">{framework?.axis_left || "Left"}</span>
        <div className="flex-1 h-px bg-border relative">
          <div className="absolute left-1/2 -top-[3px] h-[7px] w-px bg-border" />
          <div
            className="absolute size-3 rounded-full bg-foreground top-1/2 -translate-y-1/2 -translate-x-1/2 ring-2 ring-card"
            style={{ left: `${left}%` }}
          />
        </div>
        <span className="font-medium">{framework?.axis_right || "Right"}</span>
      </div>
      {explanation && <p className="text-sm text-muted-foreground leading-relaxed">{explanation}</p>}
    </div>
  );
}

function StatRow({ stat }: { stat: StatVerification }) {
  const verdict = (stat.verdict || "unverified").toLowerCase();
  const color =
    verdict === "verified"
      ? "text-sent-pos border-sent-pos/30 bg-sent-pos/5"
      : verdict === "disputed" || verdict === "false"
        ? "text-sent-neg border-sent-neg/30 bg-sent-neg/5"
        : "text-muted-foreground border-border bg-muted/30";
  return (
    <div className="border border-border rounded-md p-4">
      <div className="flex items-start justify-between gap-4">
        <p className="text-sm leading-relaxed">{stat.claim}</p>
        <span className={`shrink-0 text-[10px] uppercase tracking-wider px-2 py-1 rounded border ${color}`}>
          {stat.verdict || "Unverified"}
        </span>
      </div>
      {(stat.notes || stat.source_url) && (
        <div className="mt-2 flex items-center gap-3 text-xs text-muted-foreground">
          {stat.notes && <span>{stat.notes}</span>}
          {stat.source_url && (
            <a
              href={stat.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 underline underline-offset-2"
            >
              Source <ExternalLink className="size-3" />
            </a>
          )}
        </div>
      )}
    </div>
  );
}
