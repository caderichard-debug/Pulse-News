import { createFileRoute, Link, redirect } from "@tanstack/react-router";
import { getToken } from "@/lib/api";
import { ArrowRight, Sparkles, ShieldCheck, Compass } from "lucide-react";

export const Route = createFileRoute("/_app/")({
  beforeLoad: () => {
    if (typeof window !== "undefined" && getToken()) {
      throw redirect({
        to: "/feed",
        search: { page: 1, q: "", topic: "", lean: "", sort: "newest", fav: false },
      });
    }
  },
  head: () => ({
    meta: [
      { title: "Pulse — News aggregation with ethical clarity" },
      {
        name: "description",
        content:
          "Aggregated news, AI-assisted analysis, ethical framework lenses, and statistic verification — in one calm, credible reading experience.",
      },
    ],
  }),
  component: Landing,
});

function Landing() {
  return (
    <>
      <section className="max-w-[1100px] mx-auto px-6 pt-24 pb-32">
        <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground mb-6">
          News, with the receipts
        </p>
        <h1 className="font-serif text-5xl md:text-7xl font-medium tracking-tight leading-[1.02] text-balance max-w-4xl">
          The day's stories — analyzed, contextualized, and{" "}
          <span className="italic">held to account.</span>
        </h1>
        <p className="mt-8 max-w-[60ch] text-lg md:text-xl text-muted-foreground leading-relaxed text-pretty">
          Pulse aggregates trusted sources, summarizes coverage, surfaces sentiment and political
          lean, maps each article to ethical frameworks, and verifies the statistics behind the
          claims.
        </p>
        <div className="mt-10 flex flex-wrap gap-3">
          <Link
            to="/signup"
            className="inline-flex items-center gap-2 px-5 py-3 rounded-md bg-primary text-primary-foreground font-medium hover:opacity-90 transition-opacity"
          >
            Start reading <ArrowRight className="size-4" />
          </Link>
          <Link
            to="/how-it-works"
            className="inline-flex items-center gap-2 px-5 py-3 rounded-md border border-border font-medium hover:bg-accent transition-colors"
          >
            How it works
          </Link>
        </div>
      </section>

      <section className="border-t border-border bg-muted/30">
        <div className="max-w-[1100px] mx-auto px-6 py-20 grid md:grid-cols-3 gap-12">
          <Feature
            Icon={Sparkles}
            title="AI-assisted analysis"
            body="Every article gets a calm summary, sentiment reading, and political lean — surfaced, never sensationalized."
          />
          <Feature
            Icon={Compass}
            title="Ethical lenses"
            body="See where a story sits across competing frameworks — liberty vs. welfare, sovereignty vs. cooperation, and more."
          />
          <Feature
            Icon={ShieldCheck}
            title="Verified statistics"
            body="Numerical claims are traced to sources with confidence and credibility — uncertainty isn't hidden, it's shown."
          />
        </div>
      </section>
    </>
  );
}

function Feature({
  Icon,
  title,
  body,
}: {
  Icon: React.ComponentType<{ className?: string }>;
  title: string;
  body: string;
}) {
  return (
    <div>
      <Icon className="size-5 text-foreground mb-4" />
      <h3 className="font-serif text-2xl font-medium mb-2">{title}</h3>
      <p className="text-muted-foreground leading-relaxed text-pretty">{body}</p>
    </div>
  );
}
