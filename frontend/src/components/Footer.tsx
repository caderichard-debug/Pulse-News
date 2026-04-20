import { Link } from "@tanstack/react-router";

const DOCS_URL =
  (import.meta.env.VITE_DOCUMENTATION_URL as string | undefined) ||
  "https://docs.pulsenews.app";

export function Footer() {
  return (
    <footer className="border-t border-border mt-24">
      <div className="max-w-[1100px] mx-auto px-6 py-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6 text-sm text-muted-foreground">
        <div className="flex items-baseline gap-3">
          <span className="font-serif text-lg uppercase tracking-tight text-foreground">Pulse</span>
          <span>News aggregation with ethical clarity.</span>
        </div>
        <div className="flex flex-wrap gap-6">
          <a
            href={DOCS_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-foreground transition-colors"
          >
            Documentation
          </a>
          <a
            href="mailto:support@pulsenews.app"
            className="hover:text-foreground transition-colors"
          >
            Contact
          </a>
          <Link to="/how-it-works" className="hover:text-foreground transition-colors">
            How it works
          </Link>
          <Link to="/insights" className="hover:text-foreground transition-colors">
            Insights
          </Link>
          <Link to="/sources" className="hover:text-foreground transition-colors">
            Sources
          </Link>
          <Link to="/privacy-policy" className="hover:text-foreground transition-colors">
            Privacy
          </Link>
        </div>
      </div>
    </footer>
  );
}
