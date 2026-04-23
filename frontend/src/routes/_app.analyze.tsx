import { createFileRoute } from "@tanstack/react-router";
import { useState, type FormEvent } from "react";
import { toast } from "sonner";
import { api, ApiError } from "@/lib/api";
import type { Article } from "@/lib/types";
import { LeanMeter, SentimentDot, VerifiedBadge, FrameworkChip } from "@/components/Signals";
import { Link2 } from "lucide-react";

export const Route = createFileRoute("/_app/analyze")({
  head: () => ({
    meta: [
      { title: "Analyze a URL — Pulse" },
      {
        name: "description",
        content: "Paste any article URL — Pulse extracts and analyzes it on demand.",
      },
    ],
  }),
  component: AnalyzePage,
});

function AnalyzePage() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<Article | null>(null);

  function normalizeAnalyzeResult(payload: unknown): Article | null {
    if (!payload || typeof payload !== "object") return null;
    const raw = payload as Record<string, unknown>;
    const analysis = (raw.analysis as Record<string, unknown> | undefined) ?? {};
    const frameworks = Array.isArray(raw.frameworks) ? raw.frameworks : [];
    const stats = Array.isArray(raw.statistics) ? raw.statistics : [];

    const rawPoliticalLean = analysis.political_lean;
    const politicalLean =
      typeof rawPoliticalLean === "number"
        ? rawPoliticalLean
        : typeof rawPoliticalLean === "string"
          ? Number(rawPoliticalLean)
          : undefined;

    return {
      id: (raw.id as string | number | undefined) ?? "temp",
      title: String(raw.title ?? "Untitled"),
      summary: typeof analysis.summary === "string" ? analysis.summary : undefined,
      content: typeof raw.content === "string" ? raw.content : undefined,
      url: typeof raw.url === "string" ? raw.url : undefined,
      source:
        raw.source && typeof raw.source === "object"
          ? (raw.source as Article["source"])
          : undefined,
      sentiment_score:
        typeof analysis.sentiment_score === "number" ? analysis.sentiment_score : undefined,
      sentiment: typeof analysis.sentiment === "string" ? analysis.sentiment : undefined,
      political_lean: Number.isFinite(politicalLean) ? politicalLean : undefined,
      has_verified_stats: stats.length > 0,
      frameworks: frameworks.map((f) => {
        const row = (f as Record<string, unknown>) ?? {};
        return {
          framework: {
            id: String(row.id ?? ""),
            name: String(row.name ?? "Unknown framework"),
            description: typeof row.description === "string" ? row.description : undefined,
          },
          position: typeof row.position_on_axis === "number" ? row.position_on_axis : 0,
          relevance: typeof row.relevance_score === "number" ? row.relevance_score : undefined,
          explanation: typeof row.ai_explanation === "string" ? row.ai_explanation : undefined,
        };
      }),
      statistics: stats.map((s) => {
        const row = (s as Record<string, unknown>) ?? {};
        return {
          id: typeof row.id === "number" || typeof row.id === "string" ? row.id : undefined,
          claim: String(row.claim_text ?? ""),
          verdict:
            typeof row.verification_status === "string" ? row.verification_status : undefined,
          source_url: typeof row.source_url === "string" ? row.source_url : undefined,
          confidence: typeof row.credibility_score === "number" ? row.credibility_score : undefined,
        };
      }),
    };
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    const trimmed = url.trim();
    if (!trimmed) {
      toast.error("Please enter a URL to analyze");
      return;
    }
    setLoading(true);
    setResult(null);
    try {
      const response = await api<{ success?: boolean; data?: unknown; message?: string }>(
        "/analyze/url",
        { method: "POST", body: { url: trimmed } },
      );
      const normalized = normalizeAnalyzeResult(response.data);
      if (!normalized) {
        toast.error("Analysis completed but no readable article data was returned");
        return;
      }
      setResult(normalized);
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Could not analyze that URL");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-[760px] mx-auto px-6 py-12">
      <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground mb-3">
        On-demand analysis
      </p>
      <h1 className="font-serif text-4xl md:text-5xl font-medium tracking-tight">
        Drop a URL. Get the receipts.
      </h1>
      <p className="mt-3 text-muted-foreground max-w-2xl">
        Paste any article. Pulse will extract the text, summarize it, score sentiment and political
        lean, and map it to ethical frameworks.
      </p>

      <form onSubmit={onSubmit} className="mt-8 flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Link2 className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
          <input
            type="url"
            required
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com/news/story"
            className="w-full pl-10 pr-3 py-3 bg-background border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="px-5 py-3 rounded-md bg-primary text-primary-foreground font-medium hover:opacity-90 transition-opacity disabled:opacity-60"
        >
          {loading ? "Analyzing…" : "Analyze"}
        </button>
      </form>

      {result && (
        <div className="mt-12 border-t-[3px] border-foreground pt-10">
          <h2 className="font-serif text-3xl font-medium tracking-tight text-balance">
            {result.title}
          </h2>
          {result.summary && (
            <p className="mt-4 text-lg text-muted-foreground leading-relaxed">{result.summary}</p>
          )}
          <div className="mt-6 flex flex-wrap items-center gap-x-5 gap-y-3 pt-4 border-t border-border">
            {result.has_verified_stats && <VerifiedBadge />}
            <SentimentDot sentiment={result.sentiment} />
            <LeanMeter score={result.political_lean} showLabel />
            {result.frameworks?.slice(0, 3).map((fp, i) => (
              <FrameworkChip key={i}>{fp.framework?.name}</FrameworkChip>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
