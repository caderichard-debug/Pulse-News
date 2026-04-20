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

export function leanLabel(score?: number): string {
  if (score === undefined || score === null || Number.isNaN(score)) return "Unknown";
  if (score < -0.5) return "Left";
  if (score < -0.15) return "Center-Left";
  if (score <= 0.15) return "Center";
  if (score <= 0.5) return "Center-Right";
  return "Right";
}

export function leanColorVar(score?: number): string {
  if (score === undefined || score === null) return "var(--lean-c)";
  if (score < -0.15) return "var(--lean-l)";
  if (score > 0.15) return "var(--lean-r)";
  return "var(--lean-c)";
}
