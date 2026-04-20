import { cn } from "@/lib/utils";
import { leanColorVar, leanLabel } from "@/lib/utils";

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
    <div className={cn("flex items-center gap-2", className)} title={`Political lean: ${leanLabel(score)}`}>
      <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium">L</span>
      <div className="w-16 h-px bg-border relative">
        <div className="absolute left-1/2 -top-[2px] h-[5px] w-px bg-border" />
        <div
          className="absolute size-2 rounded-full top-1/2 -translate-y-1/2 -translate-x-1/2 ring-2 ring-background"
          style={{ left: `${left}%`, backgroundColor: color }}
        />
      </div>
      <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium">R</span>
      {showLabel && (
        <span className="text-xs text-muted-foreground ml-1">{leanLabel(score)}</span>
      )}
    </div>
  );
}

export function SentimentDot({ sentiment }: { sentiment?: string }) {
  const s = (sentiment || "").toLowerCase();
  const color =
    s.startsWith("pos")
      ? "var(--sent-pos)"
      : s.startsWith("neg") || s === "alarmist" || s === "critical"
        ? "var(--sent-neg)"
        : "var(--sent-neu)";
  const label = sentiment
    ? sentiment.charAt(0).toUpperCase() + sentiment.slice(1)
    : "Neutral";
  return (
    <div className="flex items-center gap-2 text-xs font-medium" style={{ color }}>
      <span className="size-1.5 rounded-full" style={{ backgroundColor: color }} />
      {label}
    </div>
  );
}

export function VerifiedBadge({ children = "Verified Statistics" }: { children?: React.ReactNode }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-xs font-medium px-2 py-1 rounded text-verified bg-verified/5 border border-verified/15">
      <span className="text-[10px]">✓</span>
      {children}
    </span>
  );
}

export function FrameworkChip({ children }: { children: React.ReactNode }) {
  return (
    <span className="text-xs font-medium text-muted-foreground border border-border px-2 py-1 rounded">
      {children}
    </span>
  );
}
