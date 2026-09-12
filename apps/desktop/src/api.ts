import { invoke } from "@tauri-apps/api/core";
import {
  clearPendingOpenAIWorkLevel,
  getPendingOpenAIWorkLevel,
  type OpenAIWorkLevel,
} from "./openaiWorkLevel";

const DEFAULT_OPENAI_WORK_LEVEL: OpenAIWorkLevel = "high";
let coreReadyPromise: Promise<unknown> | null = null;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isAstraRequest(
  method: "GET" | "POST" | "PUT" | "DELETE",
  body: unknown,
): body is Record<string, unknown> {
  return (
    method !== "GET" &&
    isRecord(body) &&
    body.provider === "openai" &&
    body.model === "gpt-6-astra"
  );
}

function explicitOpenAIWorkLevel(body: Record<string, unknown>): OpenAIWorkLevel | null {
  const value = body.reasoning_effort;
  return value === "medium" || value === "high" || value === "xhigh" ? value : null;
}

export async function coreHealth<T>(): Promise<T> {
  if (coreReadyPromise === null) {
    coreReadyPromise = invoke("core_health").catch((reason: unknown) => {
      coreReadyPromise = null;
      throw reason;
    });
  }
  return (await coreReadyPromise) as T;
}

export async function coreApi<T>(
  method: "GET" | "POST" | "PUT" | "DELETE",
  path: string,
  body?: unknown,
): Promise<T> {
  let requestBody = body ?? null;
  let consumeWorkLevel = false;

  // A newly launched Desktop app may render before the bundled Local Core has
  // announced its port. All desktop callers share this single real health gate.
  // Book actions therefore never race a sidecar that is still starting.
  await coreHealth<unknown>();

  // Reasoning levels are a first-class control for GPT-6 Astra only. Do not
  // silently attach Astra reasoning parameters to Sol or to automatic routing.
  if (isAstraRequest(method, body)) {
    const pendingWorkLevel = getPendingOpenAIWorkLevel();
    const workLevel =
      explicitOpenAIWorkLevel(body) ?? pendingWorkLevel ?? DEFAULT_OPENAI_WORK_LEVEL;
    requestBody = { ...body, reasoning_effort: workLevel };
    consumeWorkLevel = pendingWorkLevel !== null;
  }

  try {
    return await invoke<T>("core_api", {
      request: { method, path, body: requestBody },
    });
  } finally {
    if (consumeWorkLevel) clearPendingOpenAIWorkLevel();
  }
}
