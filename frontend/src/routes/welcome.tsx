import { createFileRoute, Link } from "@tanstack/react-router";
import { useAuth } from "@/lib/auth";

export const Route = createFileRoute("/welcome")({
  head: () => ({ meta: [{ title: "Welcome — Pulse" }] }),
  component: WelcomePage,
});

function WelcomePage() {
  const { user } = useAuth();
  return (
    <div className="min-h-dvh bg-background text-foreground flex items-center justify-center px-6 py-16">
      <div className="max-w-xl text-center">
        <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground mb-6">Welcome aboard</p>
        <h1 className="font-serif text-5xl font-medium tracking-tight">
          Hello{user?.name ? `, ${user.name.split(" ")[0]}` : ""}.
        </h1>
        <p className="mt-6 text-lg text-muted-foreground leading-relaxed">
          Your Pulse feed is ready. We've started tuning it to your topics — it gets sharper the more
          you read.
        </p>
        <div className="mt-10 flex flex-wrap gap-3 justify-center">
          <Link
            to="/feed"
            className="px-5 py-3 rounded-md bg-primary text-primary-foreground font-medium hover:opacity-90 transition-opacity"
          >
            Open my feed
          </Link>
          <Link
            to="/preferences"
            className="px-5 py-3 rounded-md border border-border font-medium hover:bg-accent transition-colors"
          >
            Adjust preferences
          </Link>
        </div>
      </div>
    </div>
  );
}
