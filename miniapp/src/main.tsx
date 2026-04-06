import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { clientLog } from "./clientLogger";
import "./i18n";
import "./styles.css";

window.addEventListener("error", (event) => {
  clientLog("error", "window_error", {
    message: String(event.message),
    filename: event.filename ?? null,
    lineno: event.lineno ?? null,
  });
});

window.addEventListener("unhandledrejection", (event) => {
  const reason = event.reason instanceof Error ? event.reason.message : String(event.reason);
  clientLog("error", "unhandledrejection", { reason });
});

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
