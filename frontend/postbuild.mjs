import { copyFile, access } from "node:fs/promises";
import { constants } from "node:fs";

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
