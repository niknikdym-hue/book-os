import { invoke } from "@tauri-apps/api/core";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import "./styles.css";

const rootCandidate = document.getElementById("root");
if (!rootCandidate) {
  throw new Error("BOOK OS root element is missing");
}
const rootElement: HTMLElement = rootCandidate;

createRoot(rootElement).render(
  <StrictMode>
    <App />
  </StrictMode>,
);

function announceFrontendReady(attempt = 0) {
  if (rootElement.childElementCount === 0) {
    if (attempt < 100) {
      window.setTimeout(() => announceFrontendReady(attempt + 1), 25);
    }
    return;
  }

  void invoke<boolean>("frontend_ready").catch(() => {
    if (attempt < 100) {
      window.setTimeout(() => announceFrontendReady(attempt + 1), 25);
    }
  });
}

announceFrontendReady();
