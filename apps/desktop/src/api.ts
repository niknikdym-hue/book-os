import { invoke } from "@tauri-apps/api/core";
import {
  clearPendingOpenAIWorkLevel,
  getPendingOpenAIWorkLevel,
} from "./openaiWorkLevel";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function requiresOpenAIWorkLevel(
  method: "GET" | "POST" | "PUT",
  body: unknown,
): body is Record<string, unknown> {
  return method !== "GET" && isRecord(body) && body.provider === "openai";
}

export async function coreApi<T>(
  method: "GET" | "POST" | "PUT",
  path: string,
  body?: unknown,
): Promise<T> {
  let requestBody = body ?? null;
  let consumeWorkLevel = false;

  if (requiresOpenAIWorkLevel(method, body)) {
    const workLevel = getPendingOpenAIWorkLevel();
    if (!workLevel) {
      throw new Error(
        "Выберите уровень работы OpenAI для следующей операции: Medium, High или Extra High.",
      );
    }
    requestBody = { ...body, reasoning_effort: workLevel };
    consumeWorkLevel = true;
  }

  try {
    return await invoke<T>("core_api", {
      request: { method, path, body: requestBody },
    });
  } finally {
    if (consumeWorkLevel) clearPendingOpenAIWorkLevel();
  }
}
