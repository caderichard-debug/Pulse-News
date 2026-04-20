import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/_app/insights")({
  head: () => ({
    meta: [
      { title: "Insights — Pulse" },
      { name: "description", content: "Lens on discourse: weekly patterns from the Pulse corpus." },
    ],
  }),
  component: InsightsPage,
});

function InsightsPage() {
  return (
    <div className="max-w-[760px] mx-auto px-6 py-16">
      <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground mb-3">Lens on discourse</p>
      <h1 className="font-serif text-5xl font-medium tracking-tight leading-tight">
        Patterns from the week.
      </h1>
      <p className="mt-6 text-lg text-muted-foreground leading-relaxed">
        Weekly aggregations across the Pulse corpus — ethical framework movement, source agreement,
        and statistic-verification trends. Curated essays will appear here as they're published.
      </p>

      <div className="mt-12 border border-dashed border-border rounded-lg p-10 text-center text-muted-foreground">
        <p className="font-serif text-xl text-foreground mb-2">No insights published yet</p>
        <p className="text-sm">
          Check back next week — or read{" "}
          <a href="/how-it-works" className="underline underline-offset-4 text-foreground">
            how Pulse works
          </a>{" "}
          in the meantime.
        </p>
      </div>
    </div>
  );
}
