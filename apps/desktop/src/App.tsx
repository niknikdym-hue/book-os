import { useEffect, useState } from "react";
import { invoke } from "@tauri-apps/api/core";
export type CoreHealth = { status: string; version: string };
export function App() {
  const [health, setHealth] = useState<CoreHealth | null>(null); const [error, setError] = useState<string | null>(null);
  useEffect(() => { void invoke<CoreHealth>("core_health").then(setHealth).catch((reason: unknown) => setError(String(reason))); }, []);
  const label = health ? `Local Core ${health.status}` : error ? "Local Core unavailable" : "Checking Local Core…";
  return <main><section><p className="eyebrow">LOCAL-FIRST EDITORIAL SYSTEM</p><h1>BOOK OS</h1><p className={error ? "health error" : "health"}>{label}</p>{health && <p className="detail">Core version {health.version}</p>}{error && <p className="detail">{error}</p>}</section></main>;
}
