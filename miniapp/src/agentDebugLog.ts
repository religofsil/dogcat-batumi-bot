/** Debug-mode NDJSON relay: same-origin API (HTTPS-safe) + local ingest fallback. */
export function agentDebugLog(payload: Record<string, unknown>): void {
  const body = JSON.stringify({
    sessionId: "a5267d",
    timestamp: Date.now(),
    ...payload,
  });
  fetch("/api/__debug/client-log", {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body,
  }).catch(() => {});
  fetch("http://127.0.0.1:7916/ingest/373b3aa8-1f45-495f-95cb-294a19f5c124", {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "a5267d" },
    body,
  }).catch(() => {});
}
