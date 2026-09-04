import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, expect, it, vi } from "vitest";
import { invoke } from "@tauri-apps/api/core";
import { App } from "./App";
import type { ProjectView } from "./types";

vi.mock("@tauri-apps/api/core", () => ({ invoke: vi.fn() }));

const invokeMock = vi.mocked(invoke);

const contractContent = {
  reader: "Leaders",
  reader_problem: "They need a better model",
  central_promise: "A usable model",
  central_thesis: "Systems beat isolated tactics",
  unique_angle: "Authority-first operating system",
  reader_trajectory: "From tactics to systems",
  explicit_exclusions: ["Not motivation"],
  evidence_policy: "Trace material claims",
  voice_genre_constraints: "Precise business nonfiction",
  readiness_criteria: ["Promise fulfilled"],
};

function project(contractStatus: string | null = null): ProjectView {
  return {
    book_id: "01JTESTBOOK000000000000000",
    working_title: "Operating Book",
    mode: "BOOK_FROM_ZERO",
    domain: "BUSINESS_NONFICTION",
    primary_subtype: "Strategy",
    secondary_subtype: null,
    profile_version: "business-nonfiction-v0.1",
    workflow_stage: contractStatus === "APPROVED" ? "ARCHITECTURE" : "BOOK DEFINITION",
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
    architecture: null,
    chapters: [],
  };
}

beforeEach(() => {
  invokeMock.mockReset();
});

function commonGet(request: { method: string; path: string }) {
  if (request.method === "GET" && request.path === "/api/anti-junk") return [];
  if (request.method === "GET" && request.path === "/api/launch/readiness") {
    return {
      openai_credential_state: "AVAILABLE",
      configured_model: "gpt-5.6-sol",
      anti_junk_entry_count: 0,
      external_calls: 0,
      paid_calls: 0,
    };
  }
  return undefined;
}

it("показывает реальный каталог тем, отражает выбор и создаёт проект книги", async () => {
  invokeMock.mockImplementation(async (command, args) => {
    if (command === "core_health") return { status: "healthy", version: "0.1.0" };
    if (command === "core_api") {
      const request = (args as { request: { method: string; path: string } }).request;
      const common = commonGet(request);
      if (common !== undefined) return common;
      if (request.method === "GET" && request.path === "/api/projects") return [];
      if (request.method === "POST" && request.path === "/api/projects") return project();
    }
    throw new Error(`unexpected invoke: ${command}`);
  });

  render(<App />);
  expect(await screen.findByText("Локальное ядро: работает")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Создать новую книгу" }));

  const businessButton = screen.getByRole("button", { name: "Бизнес, доступно" });
  const startupButton = screen.getByRole("button", {
    name: "Стартапы и создание бизнеса, доступно",
  });
  const strategyButton = screen.getByRole("button", { name: "Стратегия, доступно" });

  expect(businessButton).toBeEnabled();
  expect(startupButton).toBeEnabled();
  expect(strategyButton).toBeEnabled();
  expect(startupButton).toHaveAttribute("aria-pressed", "true");
  expect(
    screen.getByRole("button", { name: "Финансы и инвестиции, в разработке" }),
  ).toBeDisabled();
  expect(
    screen.getByRole("button", { name: "Психология и саморазвитие, в разработке" }),
  ).toBeDisabled();

  fireEvent.click(businessButton);
  fireEvent.click(strategyButton);

  expect(strategyButton).toHaveAttribute("aria-pressed", "true");
  expect(startupButton).toHaveAttribute("aria-pressed", "false");
  expect(screen.getByText("Бизнес → Стратегия")).toBeInTheDocument();
  expect(screen.getByText("Выбрано ✓")).toBeInTheDocument();

  fireEvent.change(screen.getByLabelText("Рабочее название"), {
    target: { value: "Operating Book" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Создать проект книги" }));

  expect(await screen.findByRole("heading", { name: "Operating Book" })).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "BOOK OS ведёт по шагам" })).toBeInTheDocument();
  expect(screen.getAllByText("Опишите идею книги").length).toBeGreaterThan(0);
  expect(invokeMock).toHaveBeenCalledWith(
    "core_api",
    expect.objectContaining({
      request: expect.objectContaining({
        method: "POST",
        path: "/api/projects",
        body: expect.objectContaining({ primary_subtype: "Strategy" }),
      }),
    }),
  );
});

it("показывает автору следующий шаг и сохраняет human gate контракта книги", async () => {
  const summary = {
    book_id: project().book_id,
    working_title: project().working_title,
    primary_subtype: "Strategy",
    secondary_subtype: null,
    workflow_stage: "BOOK DEFINITION",
  };
  invokeMock.mockImplementation(async (command, args) => {
    if (command === "core_health") return { status: "healthy", version: "0.1.0" };
    if (command === "core_api") {
      const request = (args as { request: { method: string; path: string } }).request;
      const common = commonGet(request);
      if (common !== undefined) return common;
      if (request.method === "GET" && request.path === "/api/projects") return [summary];
      if (request.method === "GET" && request.path === `/api/projects/${summary.book_id}`)
        return project("DRAFT");
      if (request.method === "PUT" && request.path.endsWith("/book-contract/draft"))
        return project("DRAFT");
      if (request.method === "POST" && request.path.endsWith("/book-contract/approve"))
        return project("APPROVED");
    }
    throw new Error(`unexpected invoke: ${command}`);
  });

  render(<App />);
  await screen.findByText("Локальное ядро: работает");
  fireEvent.click(await screen.findByRole("button", { name: /Operating Book/ }));
  expect(await screen.findByText("ЧЕРНОВИК")).toBeInTheDocument();
  expect(screen.getByText("Проверьте предложенный контракт книги")).toBeInTheDocument();

  fireEvent.click(screen.getAllByRole("button", { name: "Сохранить черновик" })[0]);
  await waitFor(() =>
    expect(invokeMock).toHaveBeenCalledWith(
      "core_api",
      expect.objectContaining({
        request: expect.objectContaining({
          method: "PUT",
          path: expect.stringContaining("book-contract/draft"),
        }),
      }),
    ),
  );

  fireEvent.click(screen.getAllByRole("button", { name: "Утвердить контракт книги" })[0]);
  expect(await screen.findByText("УТВЕРЖДЕНО")).toBeInTheDocument();
  expect(invokeMock).toHaveBeenCalledWith(
    "core_api",
    expect.objectContaining({
      request: expect.objectContaining({
        method: "POST",
        path: expect.stringContaining("book-contract/approve"),
      }),
    }),
  );
});
