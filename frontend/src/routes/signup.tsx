import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useEffect, useState, type FormEvent } from "react";
import { toast } from "sonner";
import { useAuth } from "@/lib/auth";
import { api, ApiError } from "@/lib/api";
import type { Topic } from "@/lib/types";
import { AuthShell, Field } from "./login";
import { FilterChip } from "@/components/ui/filter-chip";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/signup")({
  head: () => ({ meta: [{ title: "Join Pulse" }] }),
  component: SignupPage,
});

function SignupPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [topics, setTopics] = useState<Topic[]>([]);
  const [selected, setSelected] = useState<Set<string | number>>(new Set());
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api<Topic[] | { items: Topic[] }>("/preferences/topics", { auth: false })
      .then((res) => {
        const list = Array.isArray(res) ? res : res?.items || [];
        setTopics(list);
      })
      .catch(() => {
        /* topics optional */
      });
  }, []);

  function toggle(id: string | number) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      await register(name, email, password, Array.from(selected));
      toast.success("Welcome to Pulse");
      navigate({ to: "/welcome" });
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Could not create account");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthShell title="Join Pulse" subtitle="Calm, credible, AI-assisted news.">
      <form onSubmit={onSubmit} className="space-y-5">
        <Field label="Name" id="name">
          <input
            id="name"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full px-3 py-2.5 bg-background border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </Field>
        <Field label="Email" id="email">
          <input
            id="email"
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full px-3 py-2.5 bg-background border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </Field>
        <Field label="Password" id="password">
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

        {topics.length > 0 && (
          <div>
            <p className="text-sm font-medium mb-2">Topics you care about</p>
            <p className="text-xs text-muted-foreground mb-3">
              Optional — you can change this later.
            </p>
            <div className="flex flex-wrap gap-2">
              {topics.map((t) => {
                const active = selected.has(t.id);
                return (
                  <FilterChip key={t.id} selected={active} size="md" onClick={() => toggle(t.id)}>
                    {t.name}
                  </FilterChip>
                );
              })}
            </div>
          </div>
        )}

        <Button type="submit" disabled={loading} className="w-full h-10">
          {loading ? "Creating your account..." : "Create account"}
        </Button>
      </form>
      <p className="mt-6 text-sm text-center text-muted-foreground">
        Already a member?{" "}
        <Link to="/login" className="text-foreground underline underline-offset-4">
          Sign in
        </Link>
      </p>
    </AuthShell>
  );
}
