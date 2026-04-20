import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect } from "react";
import { setToken } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export const Route = createFileRoute("/login/callback")({
  component: OAuthCallback,
});

function OAuthCallback() {
  const navigate = useNavigate();
  const { refresh } = useAuth();

  useEffect(() => {
    if (typeof window === "undefined") return;
    const search = new URLSearchParams(window.location.search);
    const hash = new URLSearchParams(window.location.hash.replace(/^#/, ""));
    const token =
      search.get("access_token") ||
      search.get("token") ||
      hash.get("access_token") ||
      hash.get("token");
    if (token) {
      setToken(token);
      refresh().finally(() => navigate({ to: "/feed" }));
    } else {
      navigate({ to: "/login" });
    }
  }, [navigate, refresh]);

  return (
    <div className="min-h-dvh flex items-center justify-center text-muted-foreground">
      Completing sign in…
    </div>
  );
}
