/**
 * Telegram WebApp.showAlert may treat message content as HTML on some clients.
 * Strip angle brackets so API / network error bodies cannot inject tags.
 */
export function safeAlertText(raw: string): string {
  return raw.replace(/[<>]/g, "");
}

/** Only serve cat photos from our uploads path (relative to app origin). */
export function safeCatPhotoUrl(url: string | null | undefined): string | undefined {
  if (!url || typeof url !== "string") return undefined;
  return url.startsWith("/uploads/") ? url : undefined;
}
