import { Link, useRouterState } from "@tanstack/react-router";
import { Moon, Sun, LogOut, User as UserIcon } from "lucide-react";
import { useAuth } from "@/lib/auth";
import { useTheme } from "@/lib/theme";
import { cn } from "@/lib/utils";

const navLinks = [
  { to: "/feed", label: "Feed" },
  { to: "/analyze", label: "Analyze" },
  { to: "/insights", label: "Insights" },
  { to: "/preferences", label: "Preferences" },
  { to: "/analytics", label: "Dashboard" },
] as const;

export function Header() {
  const { user, logout } = useAuth();
  const { theme, toggle } = useTheme();
  const path = useRouterState({ select: (s) => s.location.pathname });

  return (
    <nav className="sticky top-0 z-30 bg-background/90 backdrop-blur border-b border-border">
      <div className="max-w-[1100px] mx-auto px-6 py-4 flex items-center justify-between gap-6">
        <div className="flex items-baseline gap-10">
          <Link to="/" className="font-serif text-2xl font-medium tracking-tight uppercase">
            Pulse
          </Link>
          <div className="hidden md:flex gap-7 text-sm font-medium text-muted-foreground">
            {navLinks.map((l) => {
              const active = path === l.to || path.startsWith(l.to + "/");
              return (
                <Link
                  key={l.to}
                  to={l.to}
                  className={cn(
                    "pb-1 border-b transition-colors",
                    active
                      ? "text-foreground border-foreground"
                      : "border-transparent hover:text-foreground",
                  )}
                >
                  {l.label}
                </Link>
              );
            })}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={toggle}
            aria-label="Toggle theme"
            className="size-9 inline-flex items-center justify-center rounded-md text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
          >
            {theme === "dark" ? <Sun className="size-4" /> : <Moon className="size-4" />}
          </button>
          {user ? (
            <div className="flex items-center gap-2">
              <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 text-xs text-muted-foreground">
                <UserIcon className="size-3.5" />
                <span className="truncate max-w-[140px]">{user.name || user.email}</span>
              </div>
              <button
                onClick={() => logout()}
                aria-label="Sign out"
                className="size-9 inline-flex items-center justify-center rounded-md text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
              >
                <LogOut className="size-4" />
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-1">
              <Link
                to="/login"
                className="px-3 py-1.5 text-sm font-medium text-foreground hover:bg-accent rounded-md transition-colors"
              >
                Sign in
              </Link>
              <Link
                to="/signup"
                className="px-3 py-1.5 text-sm font-medium bg-primary text-primary-foreground rounded-md hover:opacity-90 transition-opacity"
              >
                Join Pulse
              </Link>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}
