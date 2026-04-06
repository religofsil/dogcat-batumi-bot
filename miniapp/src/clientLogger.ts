const apiBase = "";

export type ClientLogLevel = "info" | "warning" | "error";

export type BootstrapEvent =
  | "no_init_data"
  | "auth_failed"
  | "window_error"
  | "unhandled_rejection"
  | "boot_failed";

const verbose =
  import.meta.env.VITE_CLIENT_LOG_VERBOSE === "true" ||
  import.meta.env.VITE_CLIENT_LOG_VERBOSE === "1";

/** Short strings for server-side context (no secrets). */
export function truncateForLog(s: string, max = 200): string {
  return s.length <= max ? s : s.slice(0, max);
}

/** Pre-session: POST /api/client-log/bootstrap (no cookie required). */
export function bootstrapLog(
  event: BootstrapEvent,
  context?: Record<string, string | number | boolean | null>,
): void {
  void fetch(`${apiBase}/api/client-log/bootstrap`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ event, context }),
  }).catch(() => {});
}

/** Sends to POST /api/client-log (session required; fails silently if unauthenticated). */
export function clientLog(
  level: ClientLogLevel,
  message: string,
  context?: Record<string, unknown>,
): void {
  if (level === "info" && !verbose) return;
  void fetch(`${apiBase}/api/client-log`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ level, message, context }),
  }).catch(() => {});
}
