import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function timeAgo(input?: string | number | Date): string {
  if (!input) return "";
  const date = input instanceof Date ? input : new Date(input);
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
  if (Number.isNaN(seconds)) return "";
  if (seconds < 60) return "just now";
  const m = Math.floor(seconds / 60);
  if (m < 60) return `${m} minute${m === 1 ? "" : "s"} ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h} hour${h === 1 ? "" : "s"} ago`;
  const d = Math.floor(h / 24);
  if (d < 7) return `${d} day${d === 1 ? "" : "s"} ago`;
  return date.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

/** Political lean as returned by the API: a -1..1 score or a label such as "left". */
export type LeanValue = number | string | null | undefined;

const LEAN_LABEL_SCORES: Record<string, number> = {
  left: -1,
  "center-left": -0.4,
  center: 0,
  "center-right": 0.4,
  right: 1,
};

/** Normalize an API lean value onto the -1 (left) .. 1 (right) scale. */
export function toLeanScore(value: LeanValue): number | undefined {
  if (value === undefined || value === null) return undefined;
  if (typeof value === "number") return Number.isFinite(value) ? value : undefined;
  const key = value
    .trim()
    .toLowerCase()
    .replace(/[\s_]+/g, "-");
  if (key in LEAN_LABEL_SCORES) return LEAN_LABEL_SCORES[key];
  const n = Number(value);
  return Number.isFinite(n) && value.trim() !== "" ? n : undefined;
}

export function leanLabel(value?: LeanValue): string {
  const score = toLeanScore(value);
  if (score === undefined) return "Unknown";
  if (score < -0.5) return "Left";
  if (score < -0.15) return "Center-Left";
  if (score <= 0.15) return "Center";
  if (score <= 0.5) return "Center-Right";
  return "Right";
}

export function leanColorVar(value?: LeanValue): string {
  const score = toLeanScore(value);
  if (score === undefined) return "var(--lean-c)";
  if (score < -0.15) return "var(--lean-l)";
  if (score > 0.15) return "var(--lean-r)";
  return "var(--lean-c)";
}
