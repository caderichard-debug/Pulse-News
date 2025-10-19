'use client';

export default function Footer() {
  return (
    <footer className="border-t border-border bg-card mt-auto">
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="flex flex-col sm:flex-row items-center justify-center gap-2 sm:gap-6 text-sm text-muted-foreground">
          <a
            href="mailto:support@pulsenews.app"
            className="hover:text-foreground transition-colors"
          >
            Contact Us
          </a>
          <span className="hidden sm:inline">•</span>
          <a
            href="/preferences?tab=account"
            className="hover:text-foreground transition-colors"
          >
            Account Settings
          </a>
          <span className="hidden sm:inline">•</span>
          <a
            href="/preferences?tab=topics"
            className="hover:text-foreground transition-colors"
          >
            Newsletter Preferences
          </a>
          <span className="hidden sm:inline">•</span>
          <a
            href="/how-it-works"
            className="hover:text-foreground transition-colors"
          >
            How It Works
          </a>
          <span className="hidden sm:inline">•</span>
          <a
            href="/privacy-policy"
            className="hover:text-foreground transition-colors"
          >
            Privacy Policy
          </a>
        </div>
        <div className="text-center text-xs text-muted-foreground mt-4">
          © {new Date().getFullYear()} Pulse News. All rights reserved.
        </div>
      </div>
    </footer>
  );
}
