import { copyFile, access } from "node:fs/promises";
import { constants } from "node:fs";
import { cp, mkdir } from "node:fs/promises";

async function exists(path) {
  try {
    await access(path, constants.F_OK);
    return true;
  } catch {
    return false;
  }
}

async function copyIfMissing(source, destination) {
  if ((await exists(source)) && !(await exists(destination))) {
    await copyFile(source, destination);
    console.log(`[postbuild] copied ${source} -> ${destination}`);
  }
}

// Compatibility for environments still starting TanStack Start via dist/server/index.js.
await copyIfMissing("dist/server/server.js", "dist/server/index.js");

// Compatibility for generic static hosts that expect index.html fallback.
await copyIfMissing("dist/client/_shell.html", "dist/client/index.html");

// Some srvx runtimes resolve static files from dist/server/public.
await mkdir("dist/server/public", { recursive: true });
await cp("dist/client/assets", "dist/server/public/assets", {
  recursive: true,
  force: true,
});
console.log("[postbuild] synced dist/client/assets -> dist/server/public/assets");
