import React from "react";
import ReactDOM from "react-dom/client";
import { agentDebugLog } from "./agentDebugLog";
import App from "./App";
import "./i18n";
import "./styles.css";

// #region agent log
window.addEventListener("error", (e) => {
  agentDebugLog({
    location: "main.tsx:window.error",
    message: "uncaught error",
    data: { msg: String(e.message), file: e.filename, lineno: e.lineno },
    hypothesisId: "H3",
  });
});
window.addEventListener("unhandledrejection", (e) => {
  const reason = e.reason instanceof Error ? e.reason.message : String(e.reason);
  agentDebugLog({
    location: "main.tsx:unhandledrejection",
    message: "unhandled rejection",
    data: { reason },
    hypothesisId: "H3",
  });
});
agentDebugLog({
  location: "main.tsx:module-load",
  message: "main module executing",
  data: {
    hasTelegram: typeof (window as unknown as { Telegram?: unknown }).Telegram !== "undefined",
    hasWebApp: !!(window as unknown as { Telegram?: { WebApp?: unknown } }).Telegram?.WebApp,
  },
  hypothesisId: "H2",
});
// #endregion

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
