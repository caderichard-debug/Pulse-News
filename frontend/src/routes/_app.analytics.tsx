import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  BarChart,
  Bar,
  Cell,
  ScatterChart,
  Scatter,
  ZAxis,
} from "recharts";
import { ApiError, api } from "@/lib/api";
import { toast } from "sonner";

export const Route = createFileRoute("/_app/analytics")({
  head: () => ({ meta: [{ title: "Dashboard — Pulse" }] }),
  component: AnalyticsPage,
});

type SentimentPoint = { date: string; positive?: number; neutral?: number; negative?: number };
type BiasBucket = { lean: string; count: number };
type Stats = {
  articles_read?: number;
  newsletters_received?: number;
  topics_tracked?: number;
  sources_subscribed?: number;
  views_changed?: number;
};

type SentimentApiPoint = {
  date: string;
  values?: { Left?: number; Center?: number; Right?: number };
};
type BiasApiPoint = { week: string; left: number; center: number; right: number };
type FrameworkGlossaryItem = {
  id: number;
  name: string;
  description: string;
  axis_description: string;
  left_position: string;
  right_position: string;
  article_count: number;
  is_seed: boolean;
};
type FrameworkAxis = { id: number; name: string; left_position: string; right_position: string };
type HeatmapCell = { x: number; y: number; article_count: number; avg_sentiment: number };
type ReadingInsights = {
  top_sources: { name: string; count: number }[];
  top_topics: { name: string; count: number }[];
  momentum: { last_7_days: number; previous_7_days: number };
};

function AnalyticsPage() {
  const [stats, setStats] = useState<Stats>({});
  const [sentiment, setSentiment] = useState<SentimentPoint[]>([]);
  const [bias, setBias] = useState<BiasBucket[]>([]);
  const [frameworks, setFrameworks] = useState<FrameworkGlossaryItem[]>([]);
  const [frameworkAxes, setFrameworkAxes] = useState<FrameworkAxis[]>([]);
  const [heatmap, setHeatmap] = useState<HeatmapCell[]>([]);
  const [insights, setInsights] = useState<ReadingInsights | null>(null);

  useEffect(() => {
    const errMsg = (err: unknown, fallback: string) =>
      err instanceof ApiError ? err.message : fallback;

    api<Stats>("/analytics/user-stats")
      .then(setStats)
      .catch((err) => {
        toast.error(errMsg(err, "Could not load dashboard stats"));
      });

    api<SentimentApiPoint[]>("/analytics/sentiment-over-time", {
      query: { days: 30, scope: "user" },
    })
      .then((r) =>
        setSentiment(
          (r || []).map((point) => ({
            date: point.date,
            positive: point.values?.Left ?? 0,
            neutral: point.values?.Center ?? 0,
            negative: point.values?.Right ?? 0,
          })),
        ),
      )
      .catch((err) => {
        toast.error(errMsg(err, "Could not load sentiment over time"));
        setSentiment([]);
      });

    api<BiasApiPoint[]>("/analytics/bias-distribution", {
      query: { weeks: 4, scope: "user" },
    })
      .then((rows) => {
        if (!rows || rows.length === 0) {
          setBias([]);
          return;
        }
        const totals = rows.reduce(
          (acc, row) => ({
            left: acc.left + row.left,
            center: acc.center + row.center,
            right: acc.right + row.right,
          }),
          { left: 0, center: 0, right: 0 },
        );
        setBias([
          { lean: "Left", count: Number((totals.left / rows.length).toFixed(1)) },
          { lean: "Center", count: Number((totals.center / rows.length).toFixed(1)) },
          { lean: "Right", count: Number((totals.right / rows.length).toFixed(1)) },
        ]);
      })
      .catch((err) => {
        toast.error(errMsg(err, "Could not load bias distribution"));
        setBias([]);
      });

    api<FrameworkGlossaryItem[]>("/analytics/frameworks/glossary")
      .then((items) => setFrameworks(items || []))
      .catch((err) => {
        toast.error(errMsg(err, "Could not load framework glossary"));
        setFrameworks([]);
      });

    api<FrameworkAxis[]>("/analytics/frameworks/available")
      .then((axes) => {
        const items = axes || [];
        setFrameworkAxes(items);
        if (items.length >= 2) {
          return api<HeatmapCell[]>("/analytics/framework-heatmap", {
            query: { framework1_id: items[0].id, framework2_id: items[1].id, days: 30 },
          });
        }
        return [];
      })
      .then((cells) => setHeatmap(cells || []))
      .catch((err) => {
        toast.error(errMsg(err, "Could not load framework heatmap"));
        setHeatmap([]);
      });

    api<ReadingInsights>("/analytics/reading-insights", { query: { days: 30 } })
      .then((r) => setInsights(r))
      .catch((err) => {
        toast.error(errMsg(err, "Could not load reading insights"));
        setInsights(null);
      });
  }, []);

  const momentumDelta = insights
    ? insights.momentum.last_7_days - insights.momentum.previous_7_days
    : 0;

  return (
    <div className="max-w-[1100px] mx-auto px-6 py-12">
      <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground mb-3">Your reading</p>
      <h1 className="font-serif text-4xl md:text-5xl font-medium tracking-tight">Dashboard</h1>

      <div className="mt-10 grid grid-cols-2 md:grid-cols-4 gap-4">
        <Stat label="Articles read" value={stats.articles_read ?? 0} />
        <Stat label="Newsletters" value={stats.newsletters_received ?? 0} />
        <Stat label="Topics" value={stats.topics_tracked ?? 0} />
        <Stat label="Sources" value={stats.sources_subscribed ?? 0} />
      </div>
      <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
        <Stat label="Last 7 days" value={insights?.momentum.last_7_days ?? 0} />
        <Stat label="Previous 7 days" value={insights?.momentum.previous_7_days ?? 0} />
        <Stat
          label="Momentum"
          value={momentumDelta > 0 ? `+${momentumDelta}` : momentumDelta}
        />
      </div>

      <Section title="Sentiment over time" subtitle="Average sentiment grouped by political lean">
        <div className="h-72">
          <ResponsiveContainer>
            <LineChart data={sentiment}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="date" stroke="var(--muted-foreground)" fontSize={12} />
              <YAxis stroke="var(--muted-foreground)" fontSize={12} />
              <Tooltip
                contentStyle={{
                  background: "var(--popover)",
                  border: "1px solid var(--border)",
                  borderRadius: 6,
                  color: "var(--popover-foreground)",
                }}
              />
              <Line
                type="monotone"
                dataKey="positive"
                stroke="var(--sent-pos)"
                strokeWidth={2}
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="neutral"
                stroke="var(--sent-neu)"
                strokeWidth={2}
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="negative"
                stroke="var(--sent-neg)"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Section>

      <Section
        title="Political lean distribution"
        subtitle="Where the stories you read sit on the spectrum"
      >
        <div className="h-72">
          <ResponsiveContainer>
            <BarChart data={bias}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="lean" stroke="var(--muted-foreground)" fontSize={12} />
              <YAxis stroke="var(--muted-foreground)" fontSize={12} />
              <Tooltip
                contentStyle={{
                  background: "var(--popover)",
                  border: "1px solid var(--border)",
                  borderRadius: 6,
                  color: "var(--popover-foreground)",
                }}
              />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {bias.map((b, i) => {
                  const l = b.lean.toLowerCase();
                  const c = l.includes("left")
                    ? "var(--lean-l)"
                    : l.includes("right")
                      ? "var(--lean-r)"
                      : "var(--lean-c)";
                  return <Cell key={i} fill={c} />;
                })}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Section>

      <Section
        title="Top sources and topics"
        subtitle="Where your reading attention is concentrated in the last 30 days"
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div>
            <h3 className="text-sm font-medium mb-3">Top sources</h3>
            <div className="space-y-2">
              {(insights?.top_sources || []).length === 0 ? (
                <p className="text-sm text-muted-foreground">No source data yet.</p>
              ) : (
                (insights?.top_sources || []).map((s) => (
                  <div key={s.name} className="flex items-center justify-between text-sm">
                    <span>{s.name}</span>
                    <span className="font-medium tabular-nums">{s.count}</span>
                  </div>
                ))
              )}
            </div>
          </div>
          <div>
            <h3 className="text-sm font-medium mb-3">Top topics</h3>
            <div className="space-y-2">
              {(insights?.top_topics || []).length === 0 ? (
                <p className="text-sm text-muted-foreground">No topic data yet.</p>
              ) : (
                (insights?.top_topics || []).map((t) => (
                  <div key={t.name} className="flex items-center justify-between text-sm">
                    <span>{t.name}</span>
                    <span className="font-medium tabular-nums">{t.count}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </Section>

      <Section
        title="Framework overlap map"
        subtitle={
          frameworkAxes.length >= 2
            ? `How stories map across ${frameworkAxes[0].name} (X) and ${frameworkAxes[1].name} (Y)`
            : "Not enough framework data to render overlap map"
        }
      >
        {frameworkAxes.length < 2 || heatmap.length === 0 ? (
          <p className="text-sm text-muted-foreground">Heatmap is unavailable until enough framework mappings exist.</p>
        ) : (
          <div className="h-80">
            <ResponsiveContainer>
              <ScatterChart margin={{ top: 20, right: 20, left: 10, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis type="number" dataKey="x" domain={[-10, 10]} stroke="var(--muted-foreground)" />
                <YAxis type="number" dataKey="y" domain={[-10, 10]} stroke="var(--muted-foreground)" />
                <ZAxis type="number" dataKey="article_count" range={[80, 400]} />
                <Tooltip
                  cursor={{ strokeDasharray: "3 3" }}
                  formatter={(value: number, name: string) => [value, name === "article_count" ? "Articles" : name]}
                />
                <Scatter data={heatmap} fill="var(--primary)" />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        )}
      </Section>

      <Section
        title="Ethical frameworks explained"
        subtitle="How Pulse maps stories to the core debates that shape policy and public discourse"
      >
        <div className="space-y-3">
          {frameworks.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No framework glossary entries are available yet.
            </p>
          ) : (
            frameworks.map((framework) => (
              <details
                key={framework.id}
                className="rounded-md border border-border bg-background px-4 py-3"
              >
                <summary className="cursor-pointer list-none font-medium">
                  {framework.name}
                  <span className="ml-2 text-xs text-muted-foreground">
                    ({framework.article_count} mapped articles)
                  </span>
                </summary>
                <div className="mt-3 space-y-2 text-sm text-muted-foreground">
                  <p>{framework.description}</p>
                  <p>
                    <span className="font-medium text-foreground">Debate axis:</span>{" "}
                    {framework.axis_description}
                  </p>
                  <p>
                    <span className="font-medium text-foreground">Left position:</span>{" "}
                    {framework.left_position}
                  </p>
                  <p>
                    <span className="font-medium text-foreground">Right position:</span>{" "}
                    {framework.right_position}
                  </p>
                </div>
              </details>
            ))
          )}
        </div>
      </Section>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="border border-border rounded-lg p-5 bg-card">
      <p className="text-xs uppercase tracking-wider text-muted-foreground mb-2">{label}</p>
      <p className="font-serif text-3xl font-medium tabular-nums">{value}</p>
    </div>
  );
}

function Section({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="mt-12">
      <div className="mb-4">
        <h2 className="font-serif text-2xl font-medium">{title}</h2>
        {subtitle && <p className="text-sm text-muted-foreground mt-1">{subtitle}</p>}
      </div>
      <div className="border border-border rounded-lg p-5 bg-card">{children}</div>
    </section>
  );
}
