import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { api, ApiError } from "@/lib/api";
import type { Source, Topic } from "@/lib/types";
import { useAuth } from "@/lib/auth";
import { useTheme } from "@/lib/theme";
import { FilterChip } from "@/components/ui/filter-chip";

type PrefSearch = { tab: "topics" | "sources" | "settings" };
type PreferenceSummary = { topics?: Array<{ id: number; is_active: boolean }> };
type SourcePreference = Source & {
  source_id?: number;
  subscribed?: boolean;
  organizational_bias?: string;
};
type UserSettings = {
  source_discovery_mode?: "none" | "some" | "open";
  article_order_preference?: "good_first" | "good_last" | "mixed";
  articles_per_topic_default?: number;
  theme_preference?: "light" | "dark" | "auto";
  newsletter_enabled?: boolean;
};

export const Route = createFileRoute("/_app/preferences")({
  validateSearch: (s: Record<string, unknown>): PrefSearch => ({
    tab: (s.tab === "sources" || s.tab === "settings" ? s.tab : "topics") as PrefSearch["tab"],
  }),
  head: () => ({ meta: [{ title: "Preferences — Pulse" }] }),
  component: PreferencesPage,
});

function PreferencesPage() {
  const { tab } = Route.useSearch();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { theme, toggle } = useTheme();

  const [topics, setTopics] = useState<Topic[]>([]);
  const [subscribed, setSubscribed] = useState<Set<string | number>>(new Set());
  const [sources, setSources] = useState<Source[]>([]);
  const [activeSources, setActiveSources] = useState<Set<string | number>>(new Set());
  const [settings, setSettings] = useState<UserSettings>({});

  useEffect(() => {
    api<Topic[] | { items: Topic[] }>("/preferences/topics")
      .then((r) => setTopics(Array.isArray(r) ? r : r?.items || []))
      .catch(() => {});
    api<PreferenceSummary>("/preferences")
      .then((p) => {
        const topicIds = (p?.topics || []).filter((t) => t.is_active).map((t) => t.id);
        setSubscribed(new Set(topicIds));
      })
      .catch(() => {});
    api<SourcePreference[] | { items: SourcePreference[] }>("/preferences/sources")
      .then((r) => {
        const list = (Array.isArray(r) ? r : r?.items || []).map((s) => ({
          ...s,
          id: s.id ?? s.source_id ?? 0,
          bias: s.bias ?? s.organizational_bias,
          active: s.active ?? s.subscribed,
        }));
        setSources(list);
        setActiveSources(new Set(list.filter((s) => s.active !== false).map((s) => s.id)));
      })
      .catch(() => {});
    api<typeof settings>("/preferences/settings")
      .then(setSettings)
      .catch(() => {});
  }, []);

  async function toggleTopic(t: Topic) {
    const has = subscribed.has(t.id);
    const next = new Set(subscribed);
    if (has) next.delete(t.id);
    else next.add(t.id);
    setSubscribed(next);
    try {
      await api(`/preferences/topics/${t.id}/${has ? "unsubscribe" : "subscribe"}`, {
        method: "POST",
      });
    } catch (err) {
      // revert
      const rev = new Set(next);
      if (has) rev.add(t.id);
      else rev.delete(t.id);
      setSubscribed(rev);
      toast.error(err instanceof ApiError ? err.message : "Could not update");
    }
  }

  async function saveSources() {
    try {
      await api("/preferences/sources", {
        method: "PUT",
        body: { source_ids: Array.from(activeSources) },
      });
      toast.success("Sources updated");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Could not save");
    }
  }

  async function saveSettings() {
    try {
      await api("/preferences/settings", {
        method: "PUT",
        body: {
          ...settings,
          theme_preference: theme,
        },
      });
      toast.success("Settings saved");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Could not save");
    }
  }

  return (
    <div className="max-w-[900px] mx-auto px-6 py-12">
      <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground mb-3">Account</p>
      <h1 className="font-serif text-4xl md:text-5xl font-medium tracking-tight">Preferences</h1>
      {user && <p className="mt-2 text-muted-foreground">{user.email}</p>}

      <div className="mt-10 border-b border-border flex gap-8 text-sm font-medium">
        {(["topics", "sources", "settings"] as const).map((t) => (
          <button
            key={t}
            onClick={() => navigate({ to: "/preferences", search: { tab: t } })}
            className={`pb-3 -mb-px capitalize border-b-2 transition-colors ${
              tab === t
                ? "border-foreground text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      <div className="mt-10">
        {tab === "topics" && (
          <div>
            <p className="text-muted-foreground mb-6">
              Subscribe to topics to tune your daily Pulse.
            </p>
            <div className="flex flex-wrap gap-2">
              {topics.map((t) => {
                const on = subscribed.has(t.id);
                return (
                  <FilterChip key={t.id} selected={on} size="md" onClick={() => toggleTopic(t)}>
                    {t.name}
                  </FilterChip>
                );
              })}
              {topics.length === 0 && (
                <p className="text-sm text-muted-foreground">No topics available yet.</p>
              )}
            </div>
          </div>
        )}

        {tab === "sources" && (
          <div>
            <p className="text-muted-foreground mb-6">Choose which outlets feed into your Pulse.</p>
            <div className="border border-border rounded-lg divide-y divide-border">
              {sources.map((s) => {
                const on = activeSources.has(s.id);
                return (
                  <label
                    key={s.id}
                    className="flex items-center justify-between p-4 cursor-pointer hover:bg-accent/50"
                  >
                    <div>
                      <p className="font-medium">{s.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {s.bias || "Bias unknown"} {s.trust_score ? `· Trust ${s.trust_score}` : ""}
                      </p>
                    </div>
                    <input
                      type="checkbox"
                      checked={on}
                      onChange={() => {
                        const next = new Set(activeSources);
                        if (on) next.delete(s.id);
                        else next.add(s.id);
                        setActiveSources(next);
                      }}
                      className="size-4 accent-foreground"
                    />
                  </label>
                );
              })}
              {sources.length === 0 && (
                <p className="p-4 text-sm text-muted-foreground">No sources available yet.</p>
              )}
            </div>
            {sources.length > 0 && (
              <button
                onClick={saveSources}
                className="mt-6 px-4 py-2 rounded-md bg-primary text-primary-foreground"
              >
                Save sources
              </button>
            )}
          </div>
        )}

        {tab === "settings" && (
          <div className="space-y-6 max-w-md">
            <Toggle
              label="Daily newsletter"
              hint="A morning briefing of top stories."
              value={!!settings.newsletter_enabled}
              onChange={(v) => setSettings({ ...settings, newsletter_enabled: v })}
            />
            <Toggle
              label="Open source discovery"
              hint="Allow broader source recommendations."
              value={settings.source_discovery_mode === "open"}
              onChange={(v) =>
                setSettings({ ...settings, source_discovery_mode: v ? "open" : "none" })
              }
            />
            <Toggle
              label="Dark theme"
              hint="Switch the Pulse appearance."
              value={theme === "dark"}
              onChange={() => toggle()}
            />
            <div className="pt-2 flex gap-3">
              <button
                onClick={saveSettings}
                className="px-4 py-2 rounded-md bg-primary text-primary-foreground"
              >
                Save settings
              </button>
              <button
                onClick={() => logout()}
                className="px-4 py-2 rounded-md border border-border hover:bg-accent"
              >
                Sign out
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function Toggle({
  label,
  hint,
  value,
  onChange,
}: {
  label: string;
  hint: string;
  value: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <label className="flex items-start justify-between gap-4 cursor-pointer">
      <div>
        <p className="font-medium">{label}</p>
        <p className="text-sm text-muted-foreground">{hint}</p>
      </div>
      <button
        type="button"
        onClick={() => onChange(!value)}
        className={`relative w-11 h-6 rounded-full transition-colors shrink-0 ${
          value ? "bg-primary" : "bg-muted border border-border"
        }`}
        aria-pressed={value}
      >
        <span
          className={`absolute top-0.5 left-0.5 size-5 rounded-full bg-background shadow-sm transition-transform ${
            value ? "translate-x-5" : "translate-x-0"
          }`}
        />
      </button>
    </label>
  );
}
