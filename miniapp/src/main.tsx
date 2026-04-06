import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { bootstrapLog, truncateForLog } from "./clientLogger";
import "./i18n";
import "./styles.css";

window.addEventListener("error", (event) => {
  bootstrapLog("window_error", {
    message: truncateForLog(String(event.message)),
    filename: event.filename ?? null,
    lineno: event.lineno ?? null,
  });
});

window.addEventListener("unhandledrejection", (event) => {
  const reason = event.reason instanceof Error ? event.reason.message : String(event.reason);
  bootstrapLog("unhandled_rejection", { reason: truncateForLog(reason) });
});

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
