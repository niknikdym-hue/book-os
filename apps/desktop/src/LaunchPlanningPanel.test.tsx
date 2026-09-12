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
  status: "RUNNING" | "DONE" | "FAILED" | "STOPPED";
  phase: string;
  requests_used: number;
  max_requests: number;
  authorized_cost_usd: number;
  max_total_cost_usd: number;
  current_chapter_ordinal: number | null;
  last_action: string;
  output_path: string | null;
  error: string | null;
};

function fakeApi(autoState: RunningState | null = null) {
  return async function api<T>(method: "GET" | "POST" | "PUT", path: string): Promise<T> {
    if (method === "GET" && path === "/api/launch/readiness") {
      return { openai_credential_state: "AVAILABLE" } as T;
    }
    if (method === "GET" && path.endsWith("/auto-book")) return autoState as T;
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
