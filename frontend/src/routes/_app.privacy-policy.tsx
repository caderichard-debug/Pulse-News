import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/_app/privacy-policy")({
  head: () => ({ meta: [{ title: "Privacy — Pulse" }] }),
  component: PrivacyPage,
});

function PrivacyPage() {
  return (
    <div className="max-w-[720px] mx-auto px-6 py-16 prose-content">
      <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground mb-3">Policy</p>
      <h1 className="font-serif text-5xl font-medium tracking-tight">Privacy</h1>
      <p className="mt-6 text-muted-foreground leading-relaxed">
        Pulse stores the minimum data required to deliver your personalized feed: your account
        details, topic and source preferences, saved articles, and basic reading analytics used to
        improve relevance.
      </p>
      <h2 className="font-serif text-2xl mt-10 mb-3">What we collect</h2>
      <ul className="list-disc pl-6 text-muted-foreground space-y-2">
        <li>Account: name, email, hashed password, optional avatar.</li>
        <li>Preferences: subscribed topics, enabled sources, newsletter settings.</li>
        <li>Activity: articles you favorite, search queries, challenge responses.</li>
      </ul>
      <h2 className="font-serif text-2xl mt-10 mb-3">What we don't do</h2>
      <p className="text-muted-foreground leading-relaxed">
        We don't sell your data, run third-party ad trackers, or share your reading history with
        publishers.
      </p>
      <h2 className="font-serif text-2xl mt-10 mb-3">Your controls</h2>
      <p className="text-muted-foreground leading-relaxed">
        Export or delete your account at any time from{" "}
        <strong className="text-foreground">Preferences → Settings</strong>. For data requests,
        contact{" "}
        <a
          href="mailto:privacy@pulsenews.app"
          className="underline underline-offset-4 text-foreground"
        >
          privacy@pulsenews.app
        </a>
        .
      </p>
    </div>
  );
}
