import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Source } from "@/lib/types";

export const Route = createFileRoute("/_app/sources")({
  head: () => ({
    meta: [
      { title: "News sources — Pulse" },
      {
        name: "description",
        content: "Browse the outlets behind Pulse: their bias, trust scores, and active status.",
      },
    ],
  }),
  component: SourcesPage,
});

function SourcesPage() {
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api<Source[] | { items: Source[]; sources?: Source[]; total_count?: number }>("/sources", {
      query: { active_only: true, sort_by: "name" },
    })
      .then((r) => setSources(Array.isArray(r) ? r : r?.sources || r?.items || []))
      .catch(() => setSources([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-[1024px] mx-auto px-6 py-12">
      <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground mb-3">The roster</p>
      <h1 className="font-serif text-4xl md:text-5xl font-medium tracking-tight">News sources</h1>
      <p className="mt-3 text-muted-foreground max-w-2xl">
        These are the outlets Pulse reads from. Each one is rated on bias and trust — you can tune
        which ones reach your feed in <strong className="text-foreground">Preferences</strong>.
      </p>

      <div className="mt-12 border-t-[3px] border-foreground">
        {loading ? (
          <p className="py-12 text-muted-foreground">Loading sources…</p>
        ) : sources.length === 0 ? (
          <p className="py-12 text-muted-foreground">No sources yet.</p>
        ) : (
          <ul className="divide-y divide-border">
            {sources.map((s) => (
              <li
                key={s.id}
                className="grid grid-cols-1 md:grid-cols-[1fr_auto_auto] gap-4 py-5 items-center"
              >
                <div>
                  <h3 className="font-serif text-xl font-medium">{s.name}</h3>
                  {s.description && (
                    <p className="text-sm text-muted-foreground mt-1 max-w-xl">{s.description}</p>
                  )}
                </div>
                <span className="text-xs uppercase tracking-wider text-muted-foreground">
                  {s.bias || s.organizational_bias || "Unrated"}
                </span>
                {typeof s.trust_score === "number" && (
                  <span className="text-xs tabular-nums text-foreground border border-border px-2 py-1 rounded">
                    Trust {s.trust_score}
                  </span>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
