import { Link } from "@tanstack/react-router";
import { Star } from "lucide-react";
import type { Article } from "@/lib/types";
import { timeAgo, cn } from "@/lib/utils";
import { SentimentDot, VerifiedBadge, LeanPill, FrameworkCue } from "./Signals";

export function ArticleCard({
  article,
  onToggleFavorite,
  compact = false,
}: {
  article: Article;
  onToggleFavorite?: (a: Article) => void;
  compact?: boolean;
}) {
  const sourceName = article.source?.name || "Unknown source";
  return (
    <article
      className={cn(
        "grid grid-cols-1 md:grid-cols-[11rem_1fr] gap-5 md:gap-10 motion-safe:transition-transform motion-safe:duration-150 motion-safe:ease-out motion-safe:hover:-translate-y-0.5",
        compact ? "pt-8 border-t border-border" : "pt-8 border-t border-border",
      )}
    >
      <div className="flex flex-row md:flex-col justify-between md:justify-start gap-3 md:gap-4">
        <div className="flex items-center gap-2">
          <div
            className="size-2.5 rounded-full shrink-0"
            style={{ backgroundColor: "var(--ink)" }}
            aria-hidden
          />
          <span className="text-xs font-medium uppercase tracking-wider text-foreground truncate">
            {sourceName}
          </span>
        </div>
        <time className="text-xs text-muted-foreground tabular-nums">
          {timeAgo(article.published_at)}
        </time>
      </div>

      <div className="flex flex-col gap-3.5">
        <div className="flex items-start justify-between gap-6">
          <Link
            to="/article/$id"
            params={{ id: String(article.id) }}
            className="group focus:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-sm"
          >
            <h2
              className={cn(
                "font-serif font-medium tracking-tight text-foreground text-balance leading-[1.1] group-hover:underline decoration-1 underline-offset-4",
                compact ? "text-[1.6rem] md:text-[1.8rem]" : "text-2xl md:text-3xl",
              )}
            >
              {article.title}
            </h2>
          </Link>
          {onToggleFavorite && (
            <button
              onClick={() => onToggleFavorite(article)}
              aria-label={article.is_favorited ? "Remove from saved" : "Save article"}
              aria-pressed={!!article.is_favorited}
              className={cn(
                "shrink-0 mt-1 inline-flex items-center justify-center size-9 rounded-full border transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
                article.is_favorited
                  ? "text-foreground border-border bg-accent/50"
                  : "text-muted-foreground/70 border-border hover:text-foreground hover:bg-accent/50",
              )}
            >
              <Star
                className="size-[18px]"
                fill={article.is_favorited ? "currentColor" : "none"}
                strokeWidth={1.5}
              />
            </button>
          )}
        </div>

        {article.summary && (
          <p className="text-base text-muted-foreground max-w-[65ch] leading-relaxed text-pretty line-clamp-3">
            {article.summary}
          </p>
        )}

        <div className="flex flex-wrap items-center gap-x-2.5 gap-y-2.5 mt-2 pt-3 border-t border-border">
          {article.has_verified_stats && <VerifiedBadge />}
          <LeanPill score={article.political_lean} />
          <SentimentDot sentiment={article.sentiment} />
          <FrameworkCue placement={article.frameworks?.[0]} className="min-w-0" />
        </div>
      </div>
    </article>
  );
}
