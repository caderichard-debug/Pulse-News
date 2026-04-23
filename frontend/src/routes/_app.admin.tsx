import { Link, createFileRoute } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";

type AdminTab = "dashboard" | "jobs" | "users" | "sources" | "articles" | "audit";

type AdminDashboardResponse = {
  system_stats?: {
    users?: { total?: number; admins?: number };
    articles?: { total?: number; today?: number };
    sources?: { total?: number; active?: number };
    frameworks?: { total?: number };
  };
  error_summary?: { failed_jobs_24h?: number };
  recent_jobs?: Array<AdminJob>;
};

type AdminJob = {
  id: number;
  job_id: string;
  job_name: string;
  status: string;
  started_at: string;
  duration_seconds?: number;
  items_processed?: number;
  error_message?: string | null;
  result_data?: string | null;
};

type AdminJobsResponse = {
  jobs: AdminJob[];
};

type JobExecutionLog = {
  id: number;
  job_id: string;
  job_name: string;
  status: string;
  started_at: string;
  completed_at?: string | null;
  duration_seconds?: number | null;
  items_processed?: number | null;
  error_message?: string | null;
  result_data?: string | null;
};

type SchedulerJob = {
  id: string;
  name: string;
  next_run?: string | null;
  trigger: string;
  is_paused: boolean;
};

type SchedulerJobsResponse = {
  status: string;
  jobs: SchedulerJob[];
};

type AdminUser = {
  id: number;
  email: string;
  name?: string;
  is_admin: boolean;
  is_active: boolean;
  created_at: string;
  last_login?: string | null;
};

type AdminUsersResponse = {
  users: AdminUser[];
};

type AdminSource = {
  id: number;
  name: string;
  trust_score?: number;
  organizational_bias?: string | null;
  is_active: boolean;
  article_count: number;
};

type AdminSourcesResponse = {
  sources: AdminSource[];
};

type AdminArticle = {
  id: number;
  title: string;
  processing_status: string;
  source_id: number;
  scraped_at: string;
};

type AdminArticlesResponse = {
  articles: AdminArticle[];
};

type AuditLog = {
  id: number;
  admin_email: string;
  action_type: string;
  resource_type: string;
  resource_id?: string;
  timestamp: string;
};

type AdminAuditResponse = {
  audit_logs: AuditLog[];
};

const JOB_TRIGGER_IDS = [
  "scrape_rss",
  "extract_articles",
  "analyze_articles",
  "update_frameworks",
  "verify_statistics",
  "cluster_articles",
  "generate_context",
  "send_newsletters",
  "reanalyze_unanalyzed_failed",
] as const;

export const Route = createFileRoute("/_app/admin")({
  validateSearch: (search: Record<string, unknown>) => {
    const tab = search.tab;
    if (
      tab === "dashboard" ||
      tab === "jobs" ||
      tab === "users" ||
      tab === "sources" ||
      tab === "articles" ||
      tab === "audit"
    ) {
      return { tab };
    }
    return { tab: "dashboard" as AdminTab };
  },
  head: () => ({ meta: [{ title: "Admin Dashboard — Pulse" }] }),
  component: AdminPage,
});

function AdminPage() {
  const search = Route.useSearch();
  const navigate = Route.useNavigate();
  const { user } = useAuth();
  const tab = (search.tab ?? "dashboard") as AdminTab;
  const [dashboard, setDashboard] = useState<AdminDashboardResponse | null>(null);
  const [jobs, setJobs] = useState<AdminJob[]>([]);
  const [schedulerJobs, setSchedulerJobs] = useState<SchedulerJob[]>([]);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [sources, setSources] = useState<AdminSource[]>([]);
  const [articles, setArticles] = useState<AdminArticle[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedJobId, setExpandedJobId] = useState<number | null>(null);
  const [jobLogMap, setJobLogMap] = useState<Record<number, JobExecutionLog>>({});
  const [jobLogLoadingId, setJobLogLoadingId] = useState<number | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    const req =
      tab === "dashboard"
        ? api<AdminDashboardResponse>("/admin-panel/dashboard").then(setDashboard)
        : tab === "jobs"
          ? Promise.all([
              api<AdminJobsResponse>("/admin-panel/jobs/history", { query: { limit: 30 } }),
              api<SchedulerJobsResponse>("/admin-panel/jobs/scheduler"),
            ]).then(([history, scheduler]) => {
              setJobs(history.jobs || []);
              setSchedulerJobs(scheduler.jobs || []);
            })
          : tab === "users"
            ? api<AdminUsersResponse>("/admin-panel/users", { query: { page_size: 50 } }).then(
                (r) => setUsers(r.users || []),
              )
            : tab === "sources"
              ? api<AdminSourcesResponse>("/admin-panel/sources", {
                  query: { page_size: 50, active_only: false },
                }).then((r) => setSources(r.sources || []))
              : tab === "articles"
                ? api<AdminArticlesResponse>("/admin-panel/articles", {
                    query: { page_size: 50 },
                  }).then((r) => setArticles(r.articles || []))
                : api<AdminAuditResponse>("/admin-panel/audit", { query: { page_size: 50 } }).then(
                    (r) => setAuditLogs(r.audit_logs || []),
                  );

    req
      .catch((err) => {
        if (err instanceof ApiError && err.status === 403) {
          setError("Your account does not currently have admin access.");
          return;
        }
        setError(err instanceof ApiError ? err.message : "Could not load admin panel");
      })
      .finally(() => setLoading(false));
  }, [tab]);

  const tabs = useMemo(
    () =>
      [
        { id: "dashboard", label: "Dashboard" },
        { id: "jobs", label: "Jobs" },
        { id: "users", label: "Users" },
        { id: "sources", label: "Sources" },
        { id: "articles", label: "Articles" },
        { id: "audit", label: "Audit" },
      ] as const,
    [],
  );

  async function refreshJobs() {
    const [history, scheduler] = await Promise.all([
      api<AdminJobsResponse>("/admin-panel/jobs/history", { query: { limit: 30 } }),
      api<SchedulerJobsResponse>("/admin-panel/jobs/scheduler"),
    ]);
    setJobs(history.jobs || []);
    setSchedulerJobs(scheduler.jobs || []);
  }

  async function triggerJob(jobId: (typeof JOB_TRIGGER_IDS)[number]) {
    try {
      await api(`/admin-panel/jobs/trigger/${jobId}`, { method: "POST" });
      if (tab === "jobs") {
        await refreshJobs();
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not trigger job");
    }
  }

  async function controlSchedulerJob(
    jobId: string,
    action: "pause" | "resume" | "stop" | "trigger",
  ) {
    try {
      await api(`/admin-panel/jobs/control/${jobId}`, {
        method: "POST",
        query: { action },
      });
      if (tab === "jobs") {
        await refreshJobs();
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not control scheduler job");
    }
  }

  async function toggleJobLog(jobId: number) {
    if (expandedJobId === jobId) {
      setExpandedJobId(null);
      return;
    }
    setExpandedJobId(jobId);
    if (jobLogMap[jobId]) return;

    try {
      setJobLogLoadingId(jobId);
      const log = await api<JobExecutionLog>(`/admin-panel/jobs/history/${jobId}`);
      setJobLogMap((prev) => ({ ...prev, [jobId]: log }));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load job log");
    } finally {
      setJobLogLoadingId(null);
    }
  }

  async function toggleAdmin(target: AdminUser) {
    try {
      await api(`/admin-panel/users/${target.id}/admin`, {
        method: "PUT",
        query: { is_admin: !target.is_admin },
      });
      setUsers((prev) =>
        prev.map((u) => (u.id === target.id ? { ...u, is_admin: !u.is_admin } : u)),
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not update admin role");
    }
  }

  async function deactivateSource(sourceId: number) {
    try {
      await api(`/admin-panel/sources/${sourceId}`, {
        method: "PUT",
        query: { is_active: false },
      });
      setSources((prev) => prev.map((s) => (s.id === sourceId ? { ...s, is_active: false } : s)));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not update source");
    }
  }

  async function deleteArticle(articleId: number) {
    try {
      await api(`/admin-panel/articles/${articleId}`, { method: "DELETE" });
      setArticles((prev) => prev.filter((a) => a.id !== articleId));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not delete article");
    }
  }

  return (
    <div className="max-w-[1100px] mx-auto px-6 py-12">
      <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground mb-3">Operations</p>
      <h1 className="font-serif text-4xl md:text-5xl font-medium tracking-tight">
        Admin dashboard
      </h1>
      {user?.email && <p className="mt-2 text-muted-foreground">{user.email}</p>}

      <div className="mt-8 flex flex-wrap gap-2">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => navigate({ to: "/admin", search: { tab: t.id } })}
            className={`px-3 py-1.5 rounded-md text-sm border ${
              tab === t.id
                ? "bg-primary text-primary-foreground border-primary"
                : "border-border text-muted-foreground hover:text-foreground"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {loading ? (
        <p className="mt-10 text-muted-foreground">Loading admin metrics…</p>
      ) : error ? (
        <div className="mt-10 border border-border rounded-lg p-5 bg-card">
          <p className="text-destructive font-medium">Admin access error</p>
          <p className="mt-2 text-sm text-muted-foreground">{error}</p>
        </div>
      ) : (
        <>
          {tab === "dashboard" && (
            <>
              <div className="mt-10 grid grid-cols-2 md:grid-cols-4 gap-4">
                <Stat label="Users" value={dashboard?.system_stats?.users?.total ?? 0} />
                <Stat label="Admins" value={dashboard?.system_stats?.users?.admins ?? 0} />
                <Stat label="Articles" value={dashboard?.system_stats?.articles?.total ?? 0} />
                <Stat
                  label="Failed jobs (24h)"
                  value={dashboard?.error_summary?.failed_jobs_24h ?? 0}
                />
              </div>

              <section className="mt-10 border border-border rounded-lg p-5 bg-card">
                <h2 className="font-serif text-2xl font-medium">Recent jobs</h2>
                <div className="mt-4 divide-y divide-border">
                  {(dashboard?.recent_jobs ?? []).slice(0, 8).map((job) => (
                    <div key={job.id} className="py-3 flex items-center justify-between gap-3">
                      <div>
                        <Link
                          to="/admin"
                          search={{ tab: "jobs" }}
                          className="font-medium hover:underline"
                        >
                          {job.job_name}
                        </Link>
                        <p className="text-xs text-muted-foreground">
                          {new Date(job.started_at).toLocaleString()}
                        </p>
                      </div>
                      <span className="text-xs uppercase tracking-wider text-muted-foreground">
                        {job.status}
                      </span>
                    </div>
                  ))}
                  {(dashboard?.recent_jobs?.length ?? 0) === 0 && (
                    <p className="py-3 text-sm text-muted-foreground">No recent jobs found.</p>
                  )}
                </div>
              </section>
            </>
          )}

          {tab === "jobs" && (
            <section className="mt-10 border border-border rounded-lg p-5 bg-card">
              <h2 className="font-serif text-2xl font-medium">Jobs</h2>
              <div className="mt-4 flex flex-wrap gap-2">
                {JOB_TRIGGER_IDS.map((jobId) => (
                  <button
                    key={jobId}
                    onClick={() => triggerJob(jobId)}
                    className="px-3 py-1.5 rounded-md border border-border text-sm hover:bg-accent"
                  >
                    Trigger {jobId}
                  </button>
                ))}
              </div>
              <h3 className="mt-8 text-sm uppercase tracking-wider text-muted-foreground">
                Scheduler controls
              </h3>
              <div className="mt-3 divide-y divide-border">
                {schedulerJobs.map((job) => (
                  <div key={job.id} className="py-3 flex items-center justify-between gap-3">
                    <div>
                      <p className="font-medium">{job.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {job.id} • {job.is_paused ? "paused" : "scheduled"}
                        {job.next_run ? ` • next ${new Date(job.next_run).toLocaleString()}` : ""}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => controlSchedulerJob(job.id, "trigger")}
                        className="px-3 py-1.5 rounded-md border border-border text-sm hover:bg-accent"
                      >
                        Trigger
                      </button>
                      {job.is_paused ? (
                        <button
                          onClick={() => controlSchedulerJob(job.id, "resume")}
                          className="px-3 py-1.5 rounded-md border border-border text-sm hover:bg-accent"
                        >
                          Resume
                        </button>
                      ) : (
                        <button
                          onClick={() => controlSchedulerJob(job.id, "pause")}
                          className="px-3 py-1.5 rounded-md border border-border text-sm hover:bg-accent"
                        >
                          Pause
                        </button>
                      )}
                      <button
                        onClick={() => controlSchedulerJob(job.id, "stop")}
                        className="px-3 py-1.5 rounded-md border border-border text-sm hover:bg-accent"
                      >
                        Stop
                      </button>
                    </div>
                  </div>
                ))}
                {schedulerJobs.length === 0 && (
                  <p className="py-3 text-sm text-muted-foreground">No scheduler jobs found.</p>
                )}
              </div>
              <div className="mt-6 divide-y divide-border">
                {jobs.map((job) => (
                  <div key={job.id} className="py-3">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <button
                          type="button"
                          onClick={() => toggleJobLog(job.id)}
                          className="font-medium hover:underline text-left"
                        >
                          {job.job_name}
                        </button>
                        <p className="text-xs text-muted-foreground">
                          {new Date(job.started_at).toLocaleString()}{" "}
                          {job.duration_seconds ? `• ${job.duration_seconds.toFixed(1)}s` : ""}
                        </p>
                      </div>
                      <span className="text-xs uppercase tracking-wider text-muted-foreground">
                        {job.status}
                      </span>
                    </div>

                    {expandedJobId === job.id && (
                      <div className="mt-3 ml-2 border-l border-border pl-3">
                        {jobLogLoadingId === job.id ? (
                          <p className="text-xs text-muted-foreground">Loading log…</p>
                        ) : (
                          <>
                            {jobLogMap[job.id]?.error_message && (
                              <pre className="text-xs whitespace-pre-wrap rounded-md border border-border p-3 bg-card">
                                {jobLogMap[job.id]?.error_message}
                              </pre>
                            )}
                            {jobLogMap[job.id]?.result_data ? (
                              <pre className="mt-2 text-xs whitespace-pre-wrap rounded-md border border-border p-3 bg-card max-h-72 overflow-auto">
                                {jobLogMap[job.id]?.result_data}
                              </pre>
                            ) : (
                              <p className="text-xs text-muted-foreground">No stored log output.</p>
                            )}
                          </>
                        )}
                      </div>
                    )}
                  </div>
                ))}
                {jobs.length === 0 && (
                  <p className="py-3 text-sm text-muted-foreground">No job history found.</p>
                )}
              </div>
            </section>
          )}

          {tab === "users" && (
            <section className="mt-10 border border-border rounded-lg p-5 bg-card">
              <h2 className="font-serif text-2xl font-medium">Users</h2>
              <div className="mt-4 divide-y divide-border">
                {users.map((u) => (
                  <div key={u.id} className="py-3 flex items-center justify-between gap-3">
                    <div>
                      <p className="font-medium">{u.name || u.email}</p>
                      <p className="text-xs text-muted-foreground">{u.email}</p>
                    </div>
                    <button
                      onClick={() => toggleAdmin(u)}
                      className="px-3 py-1.5 rounded-md border border-border text-sm hover:bg-accent"
                    >
                      {u.is_admin ? "Revoke admin" : "Make admin"}
                    </button>
                  </div>
                ))}
                {users.length === 0 && (
                  <p className="py-3 text-sm text-muted-foreground">No users found.</p>
                )}
              </div>
            </section>
          )}

          {tab === "sources" && (
            <section className="mt-10 border border-border rounded-lg p-5 bg-card">
              <h2 className="font-serif text-2xl font-medium">Sources</h2>
              <div className="mt-4 divide-y divide-border">
                {sources.map((s) => (
                  <div key={s.id} className="py-3 flex items-center justify-between gap-3">
                    <div>
                      <p className="font-medium">{s.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {s.organizational_bias || "unrated"} • trust {s.trust_score ?? 0} •{" "}
                        {s.article_count} articles
                      </p>
                    </div>
                    <button
                      onClick={() => deactivateSource(s.id)}
                      disabled={!s.is_active}
                      className="px-3 py-1.5 rounded-md border border-border text-sm hover:bg-accent disabled:opacity-50"
                    >
                      {s.is_active ? "Deactivate" : "Inactive"}
                    </button>
                  </div>
                ))}
                {sources.length === 0 && (
                  <p className="py-3 text-sm text-muted-foreground">No sources found.</p>
                )}
              </div>
            </section>
          )}

          {tab === "articles" && (
            <section className="mt-10 border border-border rounded-lg p-5 bg-card">
              <h2 className="font-serif text-2xl font-medium">Articles</h2>
              <div className="mt-4 divide-y divide-border">
                {articles.map((a) => (
                  <div key={a.id} className="py-3 flex items-center justify-between gap-3">
                    <div className="min-w-0">
                      <Link
                        to="/article/$id"
                        params={{ id: String(a.id) }}
                        className="font-medium truncate hover:underline block"
                      >
                        {a.title}
                      </Link>
                      <p className="text-xs text-muted-foreground">
                        {a.processing_status} • source {a.source_id} •{" "}
                        {new Date(a.scraped_at).toLocaleString()}
                      </p>
                    </div>
                    <button
                      onClick={() => deleteArticle(a.id)}
                      className="px-3 py-1.5 rounded-md border border-border text-sm hover:bg-accent"
                    >
                      Delete
                    </button>
                  </div>
                ))}
                {articles.length === 0 && (
                  <p className="py-3 text-sm text-muted-foreground">No articles found.</p>
                )}
              </div>
            </section>
          )}

          {tab === "audit" && (
            <section className="mt-10 border border-border rounded-lg p-5 bg-card">
              <h2 className="font-serif text-2xl font-medium">Audit log</h2>
              <div className="mt-4 divide-y divide-border">
                {auditLogs.map((log) => (
                  <div key={log.id} className="py-3">
                    <p className="font-medium">
                      {log.action_type} on {log.resource_type}
                      {log.resource_id ? ` #${log.resource_id}` : ""}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {log.admin_email} • {new Date(log.timestamp).toLocaleString()}
                    </p>
                  </div>
                ))}
                {auditLogs.length === 0 && (
                  <p className="py-3 text-sm text-muted-foreground">No audit events found.</p>
                )}
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="border border-border rounded-lg p-5 bg-card">
      <p className="text-xs uppercase tracking-wider text-muted-foreground mb-2">{label}</p>
      <p className="font-serif text-3xl font-medium tabular-nums">{value}</p>
    </div>
  );
}
