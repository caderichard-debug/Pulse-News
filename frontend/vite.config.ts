// @lovable.dev/vite-tanstack-config already includes the following — do NOT add them manually
// or the app will break with duplicate plugins:
//   - tanstackStart, viteReact, tailwindcss, tsConfigPaths, cloudflare (build-only),
//     componentTagger (dev-only), VITE_* env injection, @ path alias, React/TanStack dedupe,
//     error logger plugins, and sandbox detection (port/host/strictPort).
// You can pass additional config via defineConfig({ vite: { ... } }) if needed.
import { defineConfig } from "@lovable.dev/vite-tanstack-config";

export default defineConfig({
  cloudflare: false,
  tanstackStart: {
    spa: {
      enabled: true,
    },
  },
  vite: {
    server: {
      allowedHosts: ["pulsenews.app", "www.pulsenews.app", "pulse-frontend-pfrt.onrender.com"],
    },
    preview: {
      // Bind IPv4 explicitly: the SPA prerender step starts a preview server, and the
      // default "::" bind fails on hosts/CI runners without IPv6.
      host: "127.0.0.1",
      allowedHosts: ["pulsenews.app", "www.pulsenews.app", "pulse-frontend-pfrt.onrender.com"],
    },
  },
});
