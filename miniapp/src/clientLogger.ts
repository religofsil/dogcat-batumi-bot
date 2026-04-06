const apiBase = "";

export type ClientLogLevel = "info" | "warning" | "error";

const verbose =
  import.meta.env.VITE_CLIENT_LOG_VERBOSE === "true" ||
  import.meta.env.VITE_CLIENT_LOG_VERBOSE === "1";

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
