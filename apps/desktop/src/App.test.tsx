import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { invoke } from "@tauri-apps/api/core";
import { App } from "./App";
import type { ProjectSummary, ProjectView } from "./types";

vi.mock("@tauri-apps/api/core", () => ({ invoke: vi.fn() }));

const invokeMock = vi.mocked(invoke);

const contractContent = {
  reader: "Руководители сервисного бизнеса",
  reader_problem: "Продажи зависят от случайных рекомендаций",
  central_promise: "Построить воспроизводимую систему продаж",
  central_thesis: "Доверие создаётся системой доказательств",
  unique_angle: "Продажа услуги как проектирование уверенности",
  reader_trajectory: "От хаотичных переговоров к управляемому процессу",
  explicit_exclusions: ["Не мотивационный сборник", "Не каталог скриптов"],
  evidence_policy: "Материальные утверждения связывать с проверяемым источником",
  voice_genre_constraints: "Ясный деловой нон-фикшн",
  readiness_criteria: ["Обещание книги выполнено"],
};

const architectureContent = {
  parts: [
    {
      title: "Часть I. Механизм",
      purpose: "Объяснить основу",
      chapters: [
        {
          chapter_id: "01JCHAPTER000000000000000",
          title: "Почему услугу трудно купить",
          purpose: "Показать природу риска",
          new_contribution: "Карта доверия",
          dependencies: [],
          transition: "От риска к доказательствам",
        },
      ],
    },
  ],
  intellectual_progression: "От проблемы к системе",
  concept_allocation: "Каждая глава добавляет отдельный механизм",
  promise_thesis_coverage: "Все элементы обещания покрыты",
  major_transitions: "Риск → доверие → решение",
};

function project(stage = "BOOK DEFINITION", contractStatus: string | null = null): ProjectView {
  const hasArchitecture = ["WRITING", "WHOLE-BOOK EDIT", "FINAL REVIEW", "LITERARY MASTER"].includes(stage);
  return {
    book_id: "01JTESTBOOK000000000000000",
    working_title: "Как продавать услуги",
    mode: "BOOK_FROM_ZERO",
    domain: "BUSINESS_NONFICTION",
    primary_subtype: "Strategy",
    secondary_subtype: null,
    profile_version: "business-nonfiction-v0.1",
    workflow_stage: stage,
    book_contract: contractStatus
      ? {
          entity_id: "01JCONTRACT00000000000000",
          revision_id: "01JREVISION00000000000000",
          status: contractStatus,
          authority_revision_id: "01JREVISION00000000000000",
          authority_status: contractStatus,
          content: contractContent,
        }
      : null,
    architecture: hasArchitecture
      ? {
          entity_id: "01JARCH00000000000000000",
          revision_id: "01JARCHREV000000000000000",
          status: "APPROVED",
          authority_revision_id: "01JARCHREV000000000000000",
          authority_status: "APPROVED",
          content: architectureContent,
        }
      : null,
    chapters: hasArchitecture
      ? [
          {
            chapter_id: "01JCHAPTER000000000000000",
            ordinal: 1,
            working_title: "Почему услугу трудно купить",
            architecture_role: "Объяснить природу риска",
            workflow_state: "CONTRACT_APPROVED",
            chapter_contract: {
              entity_id: "01JCHCONTRACT000000000000",
              revision_id: "01JCHREVISION000000000000",
              status: "APPROVED",
              authority_revision_id: "01JCHREVISION000000000000",
              authority_status: "APPROVED",
              content: {
                chapter_purpose: "Показать природу риска",
                new_contribution: "Карта доверия",
              },
            },
          },
        ]
      : [],
  };
}

const context = {
  author_profile: {
    profile_id: "01JAUTHOR0000000000000000",
    kind: "AUTHOR",
    name: "Елена Дым",
    status: "APPROVED",
  },
  series_profile: null,
  style_profile: null,
  target_characters: 180000,
  ready_for_planning: true,
};

type Fixture = {
  projects?: ProjectSummary[];
  library?: ProjectSummary[];
  series?: Array<{ series_profile_id: string; name: string; profile_status: string; books: [] }>;
  opened?: ProjectView;
  autoBook?: object | null;
};

function installFixture({ projects = [], library = [], series = [], opened, autoBook = null }: Fixture = {}) {
  invokeMock.mockImplementation(async (command, args) => {
    if (command === "core_health") return { status: "healthy", version: "0.1.0" };
    if (command !== "core_api") throw new Error(`unexpected invoke: ${command}`);
    const request = (args as { request: { method: string; path: string; body?: unknown } }).request;
    if (request.method === "GET" && request.path === "/api/projects") return projects;
    if (request.method === "GET" && request.path === "/api/library") return library;
    if (request.method === "GET" && request.path === "/api/series/workspaces") return series;
    if (request.method === "GET" && request.path.endsWith("/context")) return context;
    if (request.method === "GET" && request.path.endsWith("/auto-book")) return autoBook;
    if (request.method === "GET" && request.path.startsWith("/api/projects/") && opened) return opened;
    if (request.method === "GET" && request.path === "/api/context/profiles") return [];
    if (request.method === "GET" && request.path === "/api/launch/readiness") {
      return { openai_credential_state: "AVAILABLE", configured_model: "gpt-5.6-sol", anti_junk_entry_count: 60, external_calls: 0, paid_calls: 0 };
    }
    if (request.method === "GET" && request.path === "/api/anti-junk") return [];
    if (request.method === "POST" && request.path === "/api/projects") return project();
    if (request.method === "POST" && request.path.endsWith("/restore")) return null;
    throw new Error(`unexpected core request: ${request.method} ${request.path}`);
  });
}

beforeEach(() => {
  invokeMock.mockReset();
});
afterEach(() => cleanup());

it("keeps a healthy Home calm and free of technical system noise", async () => {
  installFixture();
  render(<App />);

  expect(await screen.findByText("Создавайте книги и серии — от замысла до готового выпуска.")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /Новая книга/ })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /Новая серия/ })).toBeInTheDocument();
  expect(screen.queryByText(/Local Core/)).not.toBeInTheDocument();
  expect(screen.queryByText(/provider/i)).not.toBeInTheDocument();
  expect(screen.queryByText(/max requests/i)).not.toBeInTheDocument();
});

it("opens one accessible Create flow for a Book or a Series", async () => {
  installFixture();
  render(<App />);
  await screen.findByText("Последние проекты");

  fireEvent.click(screen.getByRole("button", { name: "Создать" }));
  const dialog = screen.getByRole("dialog", { name: "Что создаём?" });
  expect(within(dialog).getByRole("button", { name: /Книгу/ })).toBeInTheDocument();
  expect(within(dialog).getByRole("button", { name: /Серию книг/ })).toBeInTheDocument();

  fireEvent.click(within(dialog).getByRole("button", { name: /Книгу/ }));
  expect(screen.getByRole("heading", { name: "Создайте проект книги" })).toBeInTheDocument();
  expect(screen.getByLabelText(/Рабочее название/)).toBeInTheDocument();
  expect(screen.getByLabelText(/Идея книги/)).toBeInTheDocument();
  expect(screen.getByLabelText(/Автор \/ псевдоним/)).toBeInTheDocument();
  expect(screen.getByLabelText("Серия")).toBeInTheDocument();
  expect(screen.getByRole("group", { name: "Объём книги" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Стандартная" })).toHaveAttribute("aria-pressed", "true");
  expect(screen.queryByLabelText(/Максимальная стоимость/)).not.toBeInTheDocument();
  expect(screen.queryByText(/Local Core/)).not.toBeInTheDocument();
});

it("makes Series a first-class navigation workspace instead of a floating drawer", async () => {
  installFixture();
  render(<App />);
  await screen.findByText("Последние проекты");

  const navigation = screen.getByRole("navigation", { name: "Главная навигация" });
  fireEvent.click(within(navigation).getByRole("button", { name: "Серии" }));

  expect(await screen.findByRole("heading", { name: "Книги, которые развивают одну большую идею" })).toBeInTheDocument();
  expect(screen.getByLabelText("Series Studio")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Создать серию с нуля" })).toBeInTheDocument();
  expect(document.querySelector(".series-studio-backdrop.embedded")).toBeInTheDocument();
});

it("projects backend authority into seven user stages and keeps locked stages closed", async () => {
  const opened = project("ARCHITECTURE", "APPROVED");
  const summary: ProjectSummary = opened;
  installFixture({ projects: [summary], opened });
  render(<App />);
  await screen.findByText("Последние проекты");

  fireEvent.click(screen.getByRole("button", { name: "Открыть книгу «Как продавать услуги»" }));
  const stages = await screen.findByRole("navigation", { name: "Этапы книги" });
  const labels = ["Замысел", "План", "Архитектура", "Написание", "Редактура", "Проверка", "Выпуск"];
  for (const label of labels) expect(within(stages).getByRole("button", { name: new RegExp(label) })).toBeInTheDocument();
  expect(within(stages).getByRole("button", { name: /Написание/ })).toBeDisabled();
  expect(within(stages).getByRole("button", { name: /Архитектура/ })).toHaveAttribute("aria-current", "step");
});

it("keeps a running Auto Book visible after navigation and exposes a resumable human status", async () => {
  const opened = project("WRITING", "APPROVED");
  installFixture({
    projects: [opened],
    opened,
    autoBook: {
      run_id: "01JRUN00000000000000000000",
      status: "RUNNING",
      phase: "CHAPTER_DRAFT",
      current_stage: "WRITING",
      current_chapter_ordinal: 1,
      progress_completed: 4,
      progress_total: 10,
      confirmed_cost_usd: 1.25,
      estimated_cost_usd: 5.5,
      max_total_cost_usd: 10,
    },
  });
  render(<App />);
  await screen.findByText("Последние проекты");
  fireEvent.click(screen.getByRole("button", { name: "Открыть книгу «Как продавать услуги»" }));

  const run = await screen.findByLabelText("BOOK OS создаёт книгу");
  expect(run).toHaveTextContent("Сейчас: создаю главу 1");
  fireEvent.click(screen.getByRole("button", { name: "Главная" }));
  expect(screen.getByLabelText("BOOK OS создаёт книгу")).toBeInTheDocument();
});

it("shows confirmed, estimated and unknown book cost without mixing them", async () => {
  const opened = project("WRITING", "APPROVED");
  installFixture({
    projects: [opened],
    opened,
    autoBook: {
      run_id: "01JRUN00000000000000000000",
      status: "STOPPED",
      phase: "CHAPTER_DRAFT",
      confirmed_cost_usd: 2.4,
      estimated_cost_usd: 8.75,
      reserved_cost_usd: 0.5,
      unknown_cost_usd: 0.75,
      max_total_cost_usd: 12,
    },
  });
  render(<App />);
  await screen.findByText("Последние проекты");
  fireEvent.click(screen.getByRole("button", { name: "Открыть книгу «Как продавать услуги»" }));

  const cost = await screen.findByText("Потрачено $2.40");
  fireEvent.click(cost.closest("summary")!);
  expect(screen.getByText("Оценка итоговой стоимости")).toBeInTheDocument();
  expect(screen.getByText("Ожидает подтверждения провайдера")).toBeInTheDocument();
  expect(screen.getByText("$0.75")).toBeInTheDocument();
});

it("keeps project cost controls and diagnostics in Settings rather than the book surface", async () => {
  installFixture();
  render(<App />);
  await screen.findByText("Последние проекты");
  expect(screen.queryByText("Система и диагностика")).not.toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: "Настройки" }));
  expect(await screen.findByRole("heading", { name: "BOOK OS под вашим контролем" })).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Расходы" }));
  expect(screen.getByText("Технические лимиты и safety controls")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Система и диагностика" }));
  expect(screen.getByText("Local Core")).toBeInTheDocument();
});

it("restores a book from the Library without exposing permanent delete as the primary action", async () => {
  const archived = project();
  installFixture({ library: [archived] });
  render(<App />);
  await screen.findByText("Последние проекты");
  fireEvent.click(screen.getByRole("button", { name: "Библиотека" }));

  const region = await screen.findByRole("region", { name: "Библиотека" });
  expect(within(region).getByRole("heading", { name: "Как продавать услуги" })).toBeInTheDocument();
  fireEvent.click(within(region).getByRole("button", { name: "Вернуть в работу" }));
  await waitFor(() => expect(invokeMock).toHaveBeenCalledWith(
    "core_api",
    expect.objectContaining({ request: expect.objectContaining({ method: "POST", path: `/api/library/${archived.book_id}/restore` }) }),
  ));
});
