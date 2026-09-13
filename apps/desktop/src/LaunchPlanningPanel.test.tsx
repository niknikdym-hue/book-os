import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import { LaunchPlanningPanel } from "./LaunchPlanningPanel";
import type { ProjectView } from "./types";

const project: ProjectView = {
  book_id: "01JBOOK000000000000000000",
  working_title: "Пробная книга",
  primary_subtype: "Strategy",
  secondary_subtype: null,
  workflow_stage: "BOOK DEFINITION",
  mode: "BOOK_FROM_ZERO",
  domain: "BUSINESS_NONFICTION",
  profile_version: "business-nonfiction-v0.1",
  book_contract: null,
  architecture: null,
  chapters: [],
};

const author = {
  profile_id: "01JAUTHOR0000000000000000",
  kind: "AUTHOR" as const,
  name: "Елена Дилон",
  status: "APPROVED" as const,
};

type RunningState = {
  run_id: string;
  status: "RUNNING" | "DONE" | "FAILED" | "STOPPED" | "AWAITING_AUDIO_APPROVAL";
  phase: string;
  requests_used: number;
  max_requests: number;
  authorized_cost_usd: number;
  max_total_cost_usd: number;
  current_chapter_ordinal: number | null;
  last_action: string;
  output_path: string | null;
  error: string | null;
  audio_script_id?: string | null;
};

function fakeApi(autoState: RunningState | null = null, audioScript: object | null = null) {
  return async function api<T>(method: "GET" | "POST" | "PUT", path: string): Promise<T> {
    if (method === "GET" && path === "/api/launch/readiness") {
      return { openai_credential_state: "AVAILABLE" } as T;
    }
    if (method === "GET" && path.endsWith("/auto-book")) return autoState as T;
    if (method === "GET" && path.endsWith("/auto-book/audio-script")) return audioScript as T;
    if (method === "GET" && path.endsWith("/context")) {
      return {
        author_profile: author,
        target_characters: null,
        ready_for_planning: true,
      } as T;
    }
    if (method === "GET" && path === "/api/context/profiles") return [author] as T;
    if (method === "GET" && path === `/api/projects/${project.book_id}`) return project as T;
    throw new Error(`unexpected request: ${method} ${path}`);
  };
}

afterEach(() => {
  cleanup();
});

it("separates the new-book delivery profile from the existing-book audio workflow", async () => {
  render(
    <LaunchPlanningPanel
      project={project}
      chapter={null}
      onProject={() => undefined}
      api={fakeApi()}
    />,
  );

  await screen.findByText("СИСТЕМА ГОТОВА");
  expect(screen.getByRole("button", { name: "Создать книгу с нуля" })).toHaveAttribute(
    "aria-pressed",
    "true",
  );
  expect(screen.getByRole("button", { name: "Аудио — основной формат" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Текст + аудио" })).toBeInTheDocument();

  fireEvent.click(screen.getByRole("checkbox", { name: "Аудиоредакция для чтения DOCX" }));
  expect(screen.getByRole("checkbox", { name: "Текст для озвучки TXT" })).toBeChecked();

  fireEvent.click(
    screen.getByRole("button", { name: "Подготовить текст для аудиозаписи готовой книги" }),
  );
  expect(
    screen.getByRole("button", { name: "По оригиналу, с адаптацией для аудио" }),
  ).toBeInTheDocument();
  expect(
    screen.getByRole("button", { name: "Сохранить суть и концепцию, переписать для аудио" }),
  ).toBeInTheDocument();
  expect(screen.getByRole("checkbox", { name: "Текст для озвучки TXT — обязателен" })).toBeChecked();
  expect(screen.getByRole("checkbox", { name: "Текст для озвучки TXT — обязателен" })).toBeDisabled();
  expect(screen.getByRole("checkbox", { name: "Аудиоредакция для ЛитРес DOCX" })).not.toBeChecked();
  expect(screen.getByText("Изменить модель и лимиты — обычно не нужно")).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Аудио — основной формат" })).not.toBeInTheDocument();
});

it("keeps existing-book audio out of the new-book surface and exposes it at Release", async () => {
  const { unmount } = render(
    <LaunchPlanningPanel
      project={project}
      chapter={null}
      onProject={() => undefined}
      api={fakeApi()}
      surface="new-book"
    />,
  );

  await screen.findByText("СИСТЕМА ГОТОВА");
  expect(
    screen.queryByRole("button", { name: "Подготовить текст для аудиозаписи готовой книги" }),
  ).not.toBeInTheDocument();

  unmount();
  render(
    <LaunchPlanningPanel
      project={project}
      chapter={null}
      onProject={() => undefined}
      api={fakeApi()}
      surface="release"
    />,
  );

  expect(await screen.findByRole("button", { name: "Аудиоверсия готовой книги" })).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Аудиоверсия готовой книги" }));
  expect(screen.getByRole("heading", { name: "Подготовить AudioScript из готовой книги" })).toBeInTheDocument();
});

it("shows the exact proposed AudioScript checks and requires explicit human approval", async () => {
  const awaiting: RunningState = {
    run_id: "01JRUN00000000000000000000",
    status: "AWAITING_AUDIO_APPROVAL",
    phase: "EXPORT",
    requests_used: 8,
    max_requests: 40,
    authorized_cost_usd: 8,
    max_total_cost_usd: 25,
    current_chapter_ordinal: null,
    last_action: "AudioScript prepared",
    output_path: null,
    error: null,
    audio_script_id: "01JAUDIO00000000000000000",
  };
  const script = {
    audio_script_id: awaiting.audio_script_id,
    version: 1,
    status: "PROPOSED",
    source_identity: "master-1",
    source_hash: "a".repeat(64),
    content_hash: "b".repeat(64),
    adaptation_mode: "SOURCE_FAITHFUL",
    quality_checks: [
      { check_kind: "CLEAN_RECORDING_TEXT", state: "PASS", findings: [] },
      {
        check_kind: "LISTENABILITY",
        state: "ATTENTION",
        findings: [
          {
            code: "REAL_LISTENING_REVIEW_REQUIRED",
            location: "whole-script",
            detail: "Нужно прочитать вслух.",
            severity: "ATTENTION",
          },
        ],
      },
    ],
  };
  render(
    <LaunchPlanningPanel
      project={project}
      chapter={null}
      onProject={() => undefined}
      api={fakeApi(awaiting, script)}
    />,
  );

  expect(await screen.findByText("Проверьте AudioScript перед выпуском файлов")).toBeInTheDocument();
  const approve = screen.getByRole("button", {
    name: "Утвердить AudioScript и подготовить файлы",
  });
  expect(approve).toBeDisabled();
  fireEvent.click(
    screen.getByRole("checkbox", { name: /Я прочитала аудиоредакцию вслух/ }),
  );
  expect(approve).toBeEnabled();
});

it("offers a versioned human correction instead of leaving a blocking AudioScript stuck", async () => {
  const awaiting: RunningState = {
    run_id: "01JRUN00000000000000000000",
    status: "AWAITING_AUDIO_APPROVAL",
    phase: "EXPORT",
    requests_used: 8,
    max_requests: 40,
    authorized_cost_usd: 8,
    max_total_cost_usd: 25,
    current_chapter_ordinal: null,
    last_action: "AudioScript prepared",
    output_path: null,
    error: null,
    audio_script_id: "01JAUDIO00000000000000000",
  };
  const script = {
    audio_script_id: awaiting.audio_script_id,
    version: 1,
    status: "PROPOSED",
    source_identity: "master-1",
    source_hash: "a".repeat(64),
    content_hash: "b".repeat(64),
    adaptation_mode: "SOURCE_FAITHFUL",
    content: {
      title: "Книга",
      author: "Елена Дилон",
      language: "ru",
      sections: [
        {
          source_chapter_id: "chapter-1",
          title: "Глава 1",
          paragraphs: ["Смотрите выше: важный вывод."],
          visual_decisions: [],
        },
      ],
    },
    quality_checks: [
      {
        check_kind: "PAGE_DEPENDENT_LANGUAGE",
        state: "BLOCKING",
        findings: [
          {
            code: "PAGE_DEPENDENT_REFERENCE",
            location: "chapter-1:1",
            detail: "Фраза требует страницы.",
            severity: "BLOCKING",
          },
        ],
      },
    ],
  };
  render(
    <LaunchPlanningPanel
      project={project}
      chapter={null}
      onProject={() => undefined}
      api={fakeApi(awaiting, script)}
    />,
  );

  expect(
    await screen.findByText("Исправить отмеченные места в новой версии AudioScript"),
  ).toBeInTheDocument();
  const save = screen.getByRole("button", {
    name: "Сохранить исправленную версию и повторить проверки",
  });
  expect(save).toBeDisabled();
  fireEvent.change(screen.getByLabelText("Что исправлено"), {
    target: { value: "Убрана ссылка на страницу." },
  });
  expect(save).toBeEnabled();
});

it("keeps launch disabled until the required idea and authorization are present, then turns it ready", async () => {
  render(
    <LaunchPlanningPanel
      project={project}
      chapter={null}
      onProject={() => undefined}
      api={fakeApi()}
    />,
  );

  await screen.findByText("СИСТЕМА ГОТОВА");
  expect(screen.getByRole("button", { name: "Автоматически" })).toHaveAttribute(
    "aria-pressed",
    "true",
  );
  expect(screen.getByRole("checkbox", { name: "Полная рукопись DOCX" })).toBeChecked();
  expect(screen.getByRole("checkbox", { name: "Электронная книга EPUB" })).not.toBeChecked();
  expect(screen.getByRole("checkbox", { name: "Визуальные материалы — по необходимости" })).toBeChecked();
  expect(screen.getByText("Добавить материалы — необязательно")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "GPT-6 Astra Extra High" })).toBeInTheDocument();
  const launch = screen.getByRole("button", {
    name: "Запуск станет доступен после заполнения обязательных полей",
  });
  expect(launch).toBeDisabled();
  expect(launch).not.toHaveClass("ready");

  fireEvent.change(screen.getByLabelText(/Идея книги/), {
    target: { value: "Короткая пробная книга о понятном механизме." },
  });
  fireEvent.click(
    screen.getByRole("checkbox", {
      name: /Разрешаю этому запуску Auto Book автоматически проходить этапы/,
    }),
  );

  const readyLaunch = screen.getByRole("button", { name: "Запустить создание книги" });
  expect(readyLaunch).toBeEnabled();
  expect(readyLaunch).toHaveClass("ready");
});

it("shows the real 4000-character minimum and refuses 1800 characters", async () => {
  render(
    <LaunchPlanningPanel
      project={project}
      chapter={null}
      onProject={() => undefined}
      api={fakeApi()}
    />,
  );

  await screen.findByText("СИСТЕМА ГОТОВА");
  fireEvent.change(screen.getByLabelText(/Идея книги/), {
    target: { value: "Проверка минимального объёма." },
  });
  fireEvent.change(screen.getByLabelText(/Желаемый объём/), { target: { value: "1800" } });

  expect(screen.getByText("Минимум 4 000, максимум 2 000 000 знаков.")).toHaveClass(
    "field-error",
  );
  expect(
    screen.getByRole("button", {
      name: "Запуск станет доступен после заполнения обязательных полей",
    }),
  ).toBeDisabled();
  expect(within(screen.getByLabelText("Готовность к запуску")).getByText("○ Объём книги")).toBeInTheDocument();
});

it("shows visual progress and a resumable pause instead of a spinner after a provider disconnect", async () => {
  const state: RunningState = {
    run_id: "01JRUN00000000000000000000",
    status: "RUNNING",
    phase: "CHAPTER_DRAFT",
    requests_used: 5,
    max_requests: 40,
    authorized_cost_usd: 5,
    max_total_cost_usd: 25,
    current_chapter_ordinal: 2,
    last_action: "Temporary model connection interruption; progress saved",
    output_path: null,
    error: "Server disconnected without sending a response.",
  };

  render(
    <LaunchPlanningPanel
      project={project}
      chapter={null}
      onProject={() => undefined}
      api={fakeApi(state)}
    />,
  );

  expect(await screen.findByText("Создаю главу 2")).toBeInTheDocument();
  expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow");
  expect(screen.getByText("Связь прервалась, но прогресс сохранён.")).toBeInTheDocument();
  expect(screen.getByText("Server disconnected without sending a response.")).toBeInTheDocument();
  expect(
    screen.getByRole("button", { name: "Продолжить с сохранённого места" }),
  ).toBeInTheDocument();
});
