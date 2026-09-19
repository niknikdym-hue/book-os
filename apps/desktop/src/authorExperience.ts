import type { ProjectView } from "./types";

export type BookStageId =
  | "intent"
  | "plan"
  | "architecture"
  | "writing"
  | "editing"
  | "check"
  | "release";

export type BookStageState = "done" | "current" | "locked";

export type AutoBookSummary = {
  run_id: string;
  status: "RUNNING" | "DONE" | "FAILED" | "STOPPED" | "AWAITING_FINAL_ACCEPTANCE" | "AWAITING_AUDIO_APPROVAL";
  phase: string;
  current_stage?: string;
  progress_completed?: number;
  progress_total?: number;
  current_chapter_ordinal?: number | null;
  requests_used?: number;
  max_requests?: number;
  estimated_cost_usd?: number;
  reserved_cost_usd?: number;
  confirmed_cost_usd?: number;
  unknown_cost_usd?: number;
  max_total_cost_usd?: number;
  last_action?: string;
  error?: string | null;
};

export const BOOK_STAGES: ReadonlyArray<{
  id: BookStageId;
  label: string;
  description: string;
}> = [
  { id: "intent", label: "Замысел", description: "Идея, читатель и обещание книги" },
  { id: "plan", label: "План", description: "Границы, исследования и место в серии" },
  { id: "architecture", label: "Архитектура", description: "Части, главы и движение мысли" },
  { id: "writing", label: "Написание", description: "Работа с главами и версиями текста" },
  { id: "editing", label: "Редактура", description: "Содержание, факты, стиль и повторы" },
  { id: "check", label: "Проверка", description: "Финальные независимые проверки" },
  { id: "release", label: "Выпуск", description: "Master, форматы и аудиоверсия" },
];

const INTERNAL_STAGE_RANK: Record<string, number> = {
  "BOOK DEFINITION": 0,
  ARCHITECTURE: 1,
  WRITING: 2,
  "WHOLE-BOOK EDIT": 3,
  "FINAL REVIEW": 4,
  "LITERARY MASTER": 5,
};

function isApproved(status?: string | null) {
  return status === "APPROVED" || status === "LOCKED";
}

export function bookStageStates(project: ProjectView, autoBook: AutoBookSummary | null) {
  const contractExists = Boolean(project.book_contract);
  const contractApproved = isApproved(project.book_contract?.authority_status);
  const architectureApproved = isApproved(project.architecture?.authority_status);
  const allChapterContractsApproved =
    project.chapters.length > 0 &&
    project.chapters.every((chapter) => isApproved(chapter.chapter_contract?.authority_status));
  const rank = INTERNAL_STAGE_RANK[project.workflow_stage] ?? 0;
  const runDone = autoBook?.status === "DONE";

  const states: Record<BookStageId, BookStageState> = {
    intent: contractExists ? "done" : "current",
    plan: !contractExists ? "locked" : contractApproved ? "done" : "current",
    architecture: !contractApproved
      ? "locked"
      : architectureApproved
        ? "done"
        : "current",
    writing: !architectureApproved
      ? "locked"
      : rank >= 3 || runDone
        ? "done"
        : "current",
    editing: !allChapterContractsApproved && rank < 3
      ? "locked"
      : rank >= 4 || runDone
        ? "done"
        : "current",
    check: rank < 4 && !runDone ? "locked" : rank >= 5 || runDone ? "done" : "current",
    release: rank < 5 && !runDone && !["AWAITING_FINAL_ACCEPTANCE", "AWAITING_AUDIO_APPROVAL"].includes(autoBook?.status ?? "")
      ? "locked"
      : "current",
  };

  return states;
}

export function currentBookStage(
  project: ProjectView,
  autoBook: AutoBookSummary | null,
): BookStageId {
  const states = bookStageStates(project, autoBook);
  return BOOK_STAGES.find((stage) => states[stage.id] === "current")?.id ?? "release";
}

export function bookProgress(project: ProjectView, autoBook: AutoBookSummary | null): number {
  if (autoBook?.status === "DONE") return 100;
  if (autoBook?.status === "AWAITING_AUDIO_APPROVAL") return 96;
  if (autoBook?.status === "AWAITING_FINAL_ACCEPTANCE") return 94;
  if (autoBook?.progress_total && autoBook.progress_total > 0) {
    return Math.min(
      99,
      Math.round(((autoBook.progress_completed ?? 0) * 100) / autoBook.progress_total),
    );
  }
  const states = bookStageStates(project, autoBook);
  const done = BOOK_STAGES.filter((stage) => states[stage.id] === "done").length;
  return Math.round((done / BOOK_STAGES.length) * 100);
}

export function humanAutoBookActivity(state: AutoBookSummary): string {
  const stageLabels: Record<string, string> = {
    DEFINITION: "уточняю замысел книги",
    RESEARCH: "собираю и проверяю источники",
    ARCHITECTURE: "строю архитектуру книги",
    CHAPTER_CONTRACTS: "готовлю задачи глав",
    WRITING: "пишу главы",
    CHAPTER_REVIEW: "проверяю и дорабатываю главы",
    MIDBOOK_AUDIT: "проверяю сквозную логику книги",
    WHOLE_BOOK_EDIT: "редактирую книгу как единое целое",
    FACT_CHECK: "проверяю факты и источники",
    LITERARY_EDIT: "выполняю литературную редактуру",
    VISUALS: "готовлю полезные визуальные материалы",
    INDEPENDENT_CRITIQUE: "провожу независимую критику",
    CORRECTION: "исправляю найденные замечания",
    MASTER_AND_EXPORTS: "собираю финальную версию и файлы",
  };
  if (state.current_chapter_ordinal) {
    return `создаю главу ${state.current_chapter_ordinal}`;
  }
  return stageLabels[state.current_stage ?? ""] ?? state.last_action ?? "продолжаю создание книги";
}

export function money(value?: number | null) {
  return `$${(value ?? 0).toFixed(2)}`;
}
