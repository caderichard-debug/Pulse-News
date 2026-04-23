import { cn } from "@/lib/utils";
import { leanColorVar, leanLabel } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import type { FrameworkPlacement } from "@/lib/types";
import { Minus, TrendingDown, TrendingUp } from "lucide-react";

export function LeanMeter({
  score,
  className,
  showLabel = false,
}: {
  score?: number;
  className?: string;
  showLabel?: boolean;
}) {
  const s = typeof score === "number" ? Math.max(-1, Math.min(1, score)) : 0;
  const left = ((s + 1) / 2) * 100;
  const color = leanColorVar(score);
  return (
    <div
      className={cn("flex items-center gap-2", className)}
      title={`Political lean: ${leanLabel(score)}`}
    >
      <span className="text-xs uppercase tracking-wide text-muted-foreground font-medium">L</span>
      <div className="w-16 h-px bg-border relative">
        <div className="absolute left-1/2 -top-[2px] h-[5px] w-px bg-border" />
        <div
          className="absolute size-2 rounded-full top-1/2 -translate-y-1/2 -translate-x-1/2 ring-2 ring-background"
          style={{ left: `${left}%`, backgroundColor: color }}
        />
      </div>
      <span className="text-xs uppercase tracking-wide text-muted-foreground font-medium">R</span>
      {showLabel && <span className="text-xs text-muted-foreground ml-1">{leanLabel(score)}</span>}
    </div>
  );
}

export function SentimentDot({ sentiment }: { sentiment?: string }) {
  const s = (sentiment || "").toLowerCase();
  const color = s.startsWith("pos")
    ? "var(--sent-pos)"
    : s.startsWith("neg") || s === "alarmist" || s === "critical"
      ? "var(--sent-neg)"
      : "var(--sent-neu)";
  const label = sentiment ? sentiment.charAt(0).toUpperCase() + sentiment.slice(1) : "Neutral";
  const Icon = s.startsWith("pos")
    ? TrendingUp
    : s.startsWith("neg") || s === "alarmist" || s === "critical"
      ? TrendingDown
      : Minus;
  return (
    <div
      className="inline-flex items-center gap-1.5 text-xs font-medium text-foreground"
      aria-label={`Sentiment: ${label}`}
    >
      <Icon className="size-3.5" style={{ color }} aria-hidden />
      <span>{label}</span>
    </div>
  );
}

export function VerifiedBadge({ children = "Verified" }: { children?: React.ReactNode }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-xs font-medium px-2 py-1 rounded-md text-verified bg-verified/10 border border-verified/30">
      <span className="text-[10px]">✓</span>
      {children}
    </span>
  );
}

export function FrameworkChip({ children }: { children: React.ReactNode }) {
  return (
    <span className="text-xs font-medium text-muted-foreground border border-border px-2 py-1 rounded-md">
      {children}
    </span>
  );
}

export function LeanPill({ score }: { score?: number }) {
  const color = leanColorVar(score);
  const label = leanLabel(score);
  return (
    <Badge
      variant="outline"
      className="h-7 rounded-full border-border/80 bg-background px-2.5 text-xs font-medium text-foreground"
      aria-label={`Political lean: ${label}`}
    >
      <span
        className="size-1.5 rounded-full mr-1.5"
        style={{ backgroundColor: color }}
        aria-hidden
      />
      {label}
    </Badge>
  );
}

export function FrameworkCue({
  placement,
  className,
}: {
  placement?: FrameworkPlacement;
  className?: string;
}) {
  if (!placement?.framework?.name) return null;
  const position = Math.max(-1, Math.min(1, placement.position ?? 0));
  const left = ((position + 1) / 2) * 100;
  const frameworkName = placement.framework.name;
  return (
    <div
      className={cn(
        "inline-flex max-w-full items-center gap-2 text-xs text-muted-foreground",
        className,
      )}
      aria-label={`Framework cue: ${frameworkName}`}
      title={placement.explanation || frameworkName}
    >
      <span className="max-w-[8.5rem] truncate sm:max-w-[11rem]">{frameworkName}</span>
      <span className="relative h-px w-12 shrink-0 bg-border" aria-hidden>
        <span className="absolute left-1/2 -top-[2px] h-[5px] w-px bg-border" />
        <span
          className="absolute top-1/2 size-1.5 -translate-x-1/2 -translate-y-1/2 rounded-full bg-foreground"
          style={{ left: `${left}%` }}
        />
      </span>
      <span className="sr-only">{placement.explanation || frameworkName}</span>
    </div>
  );
}
