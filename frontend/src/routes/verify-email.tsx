import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";

export const Route = createFileRoute("/verify-email")({
  head: () => ({ meta: [{ title: "Verify email — Pulse" }] }),
  component: VerifyEmail,
});

function VerifyEmail() {
  const [status, setStatus] = useState<"idle" | "ok" | "err">("idle");
  const [message, setMessage] = useState("Verifying your email...");

  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    const token = params.get("token");
    if (!token) {
      setStatus("err");
      setMessage("Missing verification token.");
      return;
    }
    api("/auth/verify-email", { method: "POST", body: { token }, auth: false })
      .then(() => {
        setStatus("ok");
        setMessage("Your email is verified. You can sign in now.");
      })
      .catch((err) => {
        setStatus("err");
        setMessage(err instanceof ApiError ? err.message : "Verification failed.");
      });
  }, []);

  return (
    <div className="min-h-dvh bg-background flex items-center justify-center px-6">
      <div className="max-w-md text-center">
        <h1 className="font-serif text-4xl font-medium tracking-tight">Email verification</h1>
        <p
          className={`mt-4 text-base ${
            status === "err" ? "text-destructive" : "text-muted-foreground"
          }`}
        >
          {message}
        </p>
        {status !== "idle" && (
          <Link
            to="/login"
            className="mt-8 inline-flex px-4 py-2 rounded-md bg-primary text-primary-foreground"
          >
            Continue to sign in
          </Link>
        )}
      </div>
    </div>
  );
}
