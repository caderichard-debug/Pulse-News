import { createFileRoute } from "@tanstack/react-router";
import { Rss, Brain, ShieldCheck, Mail, Filter, Sparkles } from "lucide-react";

export const Route = createFileRoute("/_app/how-it-works")({
  head: () => ({
    meta: [
      { title: "How Pulse works" },
      {
        name: "description",
        content:
          "From RSS aggregation to AI analysis, framework mapping, statistic verification, and the morning newsletter.",
      },
    ],
  }),
  component: HowItWorks,
});

const steps = [
  {
    Icon: Rss,
    title: "Aggregate",
    body: "We pull continuously from a roster of trusted RSS sources, each rated on bias and credibility.",
  },
  {
    Icon: Brain,
    title: "Analyze",
    body: "An LLM generates a summary, sentiment reading, and political lean — surfaced never sensationalized.",
  },
  {
    Icon: Filter,
    title: "Frame",
    body: "Each story is mapped onto ethical frameworks like liberty vs. welfare or sovereignty vs. cooperation.",
  },
  {
    Icon: ShieldCheck,
    title: "Verify",
    body: "Statistical claims are traced through a multi-stage pipeline, scored for confidence and credibility.",
  },
  {
    Icon: Sparkles,
    title: "Personalize",
    body: "Your topics, sources, and reading shape what surfaces in your feed.",
  },
  {
    Icon: Mail,
    title: "Deliver",
    body: "Optional daily newsletter brings the day's signal — not noise — to your inbox.",
  },
];

function HowItWorks() {
  return (
    <div className="max-w-[900px] mx-auto px-6 py-16">
      <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground mb-3">The pipeline</p>
      <h1 className="font-serif text-5xl md:text-6xl font-medium tracking-tight leading-tight text-balance">
        Calm, credible news — engineered for transparency.
      </h1>
      <p className="mt-6 text-lg text-muted-foreground max-w-2xl leading-relaxed">
        Pulse turns the daily flood of headlines into a structured, accountable read. Here's the
        journey every story takes.
      </p>

      <ol className="mt-16 space-y-12">
        {steps.map(({ Icon, title, body }, i) => (
          <li key={title} className="grid grid-cols-[3rem_1fr] gap-6 pt-8 border-t border-border">
            <div>
              <p className="font-serif text-3xl font-medium text-muted-foreground tabular-nums">
                {String(i + 1).padStart(2, "0")}
              </p>
            </div>
            <div>
              <div className="flex items-center gap-3 mb-3">
                <Icon className="size-5" />
                <h2 className="font-serif text-2xl font-medium">{title}</h2>
              </div>
              <p className="text-muted-foreground leading-relaxed text-pretty">{body}</p>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
