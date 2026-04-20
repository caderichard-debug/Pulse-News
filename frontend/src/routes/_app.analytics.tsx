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
} from "recharts";
import { api } from "@/lib/api";

export const Route = createFileRoute("/_app/analytics")({
  head: () => ({ meta: [{ title: "Dashboard — Pulse" }] }),
  component: AnalyticsPage,
});

type SentimentPoint = { date: string; positive?: number; neutral?: number; negative?: number };
type BiasBucket = { lean: string; count: number };
type Stats = {
  articles_read?: number;
  favorites?: number;
  topics_followed?: number;
  weekly_streak?: number;
};

function AnalyticsPage() {
  const [stats, setStats] = useState<Stats>({});
  const [sentiment, setSentiment] = useState<SentimentPoint[]>([]);
  const [bias, setBias] = useState<BiasBucket[]>([]);

  useEffect(() => {
    api<Stats>("/analytics/user-stats").then(setStats).catch(() => {});
    api<{ data?: SentimentPoint[] } | SentimentPoint[]>("/analytics/sentiment-over-time", {
      query: { days: 30 },
    })
      .then((r) => setSentiment(Array.isArray(r) ? r : r?.data || []))
      .catch(() => {});
    api<{ data?: BiasBucket[] } | BiasBucket[]>("/analytics/bias-distribution", {
      query: { weeks: 4 },
    })
      .then((r) => setBias(Array.isArray(r) ? r : r?.data || []))
      .catch(() => {});
  }, []);

  return (
    <div className="max-w-[1100px] mx-auto px-6 py-12">
      <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground mb-3">Your reading</p>
      <h1 className="font-serif text-4xl md:text-5xl font-medium tracking-tight">Dashboard</h1>

      <div className="mt-10 grid grid-cols-2 md:grid-cols-4 gap-4">
        <Stat label="Articles read" value={stats.articles_read ?? 0} />
        <Stat label="Saved" value={stats.favorites ?? 0} />
        <Stat label="Topics" value={stats.topics_followed ?? 0} />
        <Stat label="Weekly streak" value={stats.weekly_streak ?? 0} />
      </div>

      <Section title="Sentiment over time" subtitle="Tone of stories you've read in the last 30 days">
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
              <Line type="monotone" dataKey="positive" stroke="var(--sent-pos)" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="neutral" stroke="var(--sent-neu)" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="negative" stroke="var(--sent-neg)" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Section>

      <Section title="Political lean distribution" subtitle="Where the stories you read sit on the spectrum">
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
