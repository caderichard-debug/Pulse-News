import { Link } from "@tanstack/react-router";
import { Star } from "lucide-react";
import type { Article } from "@/lib/types";
import { timeAgo, cn } from "@/lib/utils";
import { LeanMeter, SentimentDot, VerifiedBadge, FrameworkChip } from "./Signals";

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
        "grid grid-cols-1 md:grid-cols-[12rem_1fr] gap-6 md:gap-12",
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

      <div className="flex flex-col gap-4">
        <div className="flex items-start justify-between gap-6">
          <Link
            to="/article/$id"
            params={{ id: String(article.id) }}
            className="group"
          >
            <h2
              className={cn(
                "font-serif font-medium tracking-tight text-foreground text-balance leading-[1.1] group-hover:underline decoration-1 underline-offset-4",
                compact ? "text-2xl md:text-[1.6rem]" : "text-3xl md:text-4xl",
              )}
            >
              {article.title}
            </h2>
          </Link>
          {onToggleFavorite && (
            <button
              onClick={() => onToggleFavorite(article)}
              aria-label={article.is_favorited ? "Remove from saved" : "Save article"}
              className={cn(
                "shrink-0 mt-1 transition-colors",
                article.is_favorited
                  ? "text-foreground"
                  : "text-muted-foreground/50 hover:text-foreground",
              )}
            >
              <Star
                className="size-5"
                fill={article.is_favorited ? "currentColor" : "none"}
                strokeWidth={1.5}
              />
            </button>
          )}
        </div>

        {article.summary && (
          <p className="text-base md:text-lg text-muted-foreground max-w-[65ch] leading-relaxed text-pretty">
            {article.summary}
          </p>
        )}

        <div className="flex flex-wrap items-center gap-x-5 gap-y-3 mt-2 pt-4 border-t border-border">
          {article.has_verified_stats && <VerifiedBadge />}
          <SentimentDot sentiment={article.sentiment} />
          <LeanMeter score={article.political_lean} />
          {article.frameworks?.slice(0, 2).map((fp, i) => (
            <FrameworkChip key={i}>{fp.framework?.name}</FrameworkChip>
          ))}
        </div>
      </div>
    </article>
  );
}
