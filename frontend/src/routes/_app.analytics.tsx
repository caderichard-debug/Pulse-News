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

type SentimentApiPoint = { date: string; values?: { Left?: number; Center?: number; Right?: number } };
type BiasApiPoint = { week: string; left: number; center: number; right: number };

function AnalyticsPage() {
  const [stats, setStats] = useState<Stats>({});
  const [sentiment, setSentiment] = useState<SentimentPoint[]>([]);
  const [bias, setBias] = useState<BiasBucket[]>([]);

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
  }, []);

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
