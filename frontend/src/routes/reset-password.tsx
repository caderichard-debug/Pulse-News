import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useEffect, useState, type FormEvent } from "react";
import { toast } from "sonner";
import { api, ApiError } from "@/lib/api";
import { AuthShell, Field } from "./login";

export const Route = createFileRoute("/reset-password")({
  head: () => ({ meta: [{ title: "Reset password — Pulse" }] }),
  component: ResetPage,
});

function ResetPage() {
  const navigate = useNavigate();
  const [token, setTokenVal] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    setTokenVal(params.get("token") || "");
  }, []);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      await api("/auth/reset-password", {
        method: "POST",
        body: { token, password },
        auth: false,
      });
      toast.success("Password updated. Sign in with your new password.");
      navigate({ to: "/login" });
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Could not reset password");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthShell title="Set a new password" subtitle="Choose something only you would know.">
      {!token ? (
        <div>
          <p className="text-destructive">Reset link is missing or invalid.</p>
          <Link
            to="/forgot-password"
            className="mt-4 inline-flex px-4 py-2 rounded-md border border-border"
          >
            Request a new link
          </Link>
        </div>
      ) : (
        <form onSubmit={onSubmit} className="space-y-5">
          <Field label="New password" id="password">
            <input
              id="password"
              type="password"
              required
              minLength={8}
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2.5 bg-background border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </Field>
          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-md bg-primary text-primary-foreground font-medium hover:opacity-90 transition-opacity disabled:opacity-60"
          >
            {loading ? "Updating..." : "Update password"}
          </button>
        </form>
      )}
    </AuthShell>
  );
}
