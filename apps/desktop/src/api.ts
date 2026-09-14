import { invoke } from "@tauri-apps/api/core";
import {
  clearPendingOpenAIWorkLevel,
  getPendingOpenAIWorkLevel,
  type OpenAIWorkLevel,
} from "./openaiWorkLevel";

const DEFAULT_OPENAI_WORK_LEVEL: OpenAIWorkLevel = "high";
const AUDIO_ATTENTION_SEPARATOR = "␟";
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

type AudioAttentionFinding = {
  code: string;
  location: string;
  detail: string;
  severity: string;
};

type AudioApprovalScript = {
  audio_script_id: string;
  status: string;
  quality_checks: Array<{
    findings: AudioAttentionFinding[];
  }>;
};

function attentionFindingKey(finding: AudioAttentionFinding): string {
  return [finding.code, finding.location, finding.detail].join(AUDIO_ATTENTION_SEPARATOR);
}

async function rawCoreRequest<T>(
  method: "GET" | "POST" | "PUT" | "DELETE",
  path: string,
  body: unknown = null,
): Promise<T> {
  return await invoke<T>("core_api", {
    request: { method, path, body },
  });
}

async function audioScriptForApproval(path: string): Promise<AudioApprovalScript | null> {
  const autoMatch = path.match(/^\/api\/projects\/([^/]+)\/auto-book\/audio-script\/approve$/);
  if (autoMatch) {
    return await rawCoreRequest<AudioApprovalScript | null>(
      "GET",
      `/api/projects/${autoMatch[1]}/auto-book/audio-script`,
    );
  }

  const existingMatch = path.match(
    /^\/api\/projects\/([^/]+)\/audio-scripts\/([^/]+)\/approve$/,
  );
  if (!existingMatch) return null;
  const scripts = await rawCoreRequest<AudioApprovalScript[]>(
    "GET",
    `/api/projects/${existingMatch[1]}/audio-scripts`,
  );
  return scripts.find((item) => item.audio_script_id === existingMatch[2]) ?? null;
}

async function withExplicitAudioAttentionReview(
  method: "GET" | "POST" | "PUT" | "DELETE",
  path: string,
  body: unknown,
): Promise<unknown> {
  if (method !== "POST" || !path.endsWith("/approve") || !isRecord(body)) return body;
  if (!path.includes("/audio-script") && !path.includes("/audio-scripts/")) return body;

  const script = await audioScriptForApproval(path);
  if (!script || script.status === "APPROVED") return body;
  const findings = script.quality_checks.flatMap((check) =>
    check.findings.filter((finding) => finding.severity === "ATTENTION"),
  );
  const accepted: string[] = [];
  for (const [index, finding] of findings.entries()) {
    const confirmed = window.confirm(
      [
        `Проверка AudioScript: замечание ${index + 1} из ${findings.length}`,
        "",
        finding.detail,
        `Место: ${finding.location}`,
        `Код: ${finding.code}`,
        "",
        "Подтвердите только если вы действительно проверили именно это замечание.",
      ].join("\n"),
    );
    if (!confirmed) {
      throw new Error(
        `Утверждение AudioScript отменено: не подтверждено замечание ${finding.code} @ ${finding.location}`,
      );
    }
    accepted.push(attentionFindingKey(finding));
  }
  return { ...body, accepted_attention_codes: accepted };
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

  requestBody = await withExplicitAudioAttentionReview(method, path, requestBody);

  try {
    return await rawCoreRequest<T>(method, path, requestBody);
  } finally {
    if (consumeWorkLevel) clearPendingOpenAIWorkLevel();
  }
}
