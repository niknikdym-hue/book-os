export type OpenAIWorkLevel = "medium" | "high" | "xhigh";

// Validated against this account's non-billable OpenAI Models metadata on 2026-09-10.
// Model identity and reasoning effort are separate API fields.
export const OPENAI_ASTRA_MODELS = [
  {
    id: "gpt-6-astra",
    label: "GPT-6 Astra",
    workLevels: ["medium", "high", "xhigh"] as const,
  },
] as const;

export const OPENAI_WORK_LEVEL_OPTIONS: ReadonlyArray<{
  value: OpenAIWorkLevel;
  label: string;
}> = [
  { value: "medium", label: "Medium" },
  { value: "high", label: "High" },
  { value: "xhigh", label: "Extra High" },
];

const CHANGE_EVENT = "book-os:openai-work-level-change";
let pendingWorkLevel: OpenAIWorkLevel | null = null;

function emitChange() {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent(CHANGE_EVENT, { detail: pendingWorkLevel }));
  }
}

export function getPendingOpenAIWorkLevel(): OpenAIWorkLevel | null {
  return pendingWorkLevel;
}

export function setPendingOpenAIWorkLevel(level: OpenAIWorkLevel): void {
  pendingWorkLevel = level;
  emitChange();
}

export function clearPendingOpenAIWorkLevel(): void {
  pendingWorkLevel = null;
  emitChange();
}

export function subscribeOpenAIWorkLevel(
  listener: (level: OpenAIWorkLevel | null) => void,
): () => void {
  if (typeof window === "undefined") return () => undefined;
  const handler = (event: Event) => {
    listener((event as CustomEvent<OpenAIWorkLevel | null>).detail ?? null);
  };
  window.addEventListener(CHANGE_EVENT, handler);
  return () => window.removeEventListener(CHANGE_EVENT, handler);
}

export function openAIWorkLevelLabel(level: string | null | undefined): string {
  return OPENAI_WORK_LEVEL_OPTIONS.find((item) => item.value === level)?.label ?? "Не выбран";
}
