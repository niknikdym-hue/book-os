import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, expect, it } from "vitest";
import { DraftingPanel } from "./DraftingPanel";
import type { DraftApi, DraftRunView } from "./draftingTypes";
import type { ChapterView, ProjectView } from "./types";

const chapter: ChapterView = {
  chapter_id: "01JCHAPTER000000000000000",
  ordinal: 1,
  working_title: "The mechanism",
  architecture_role: "Explain the mechanism",
  workflow_state: "CONTRACT_APPROVED",
  chapter_contract: {
    entity_id: "01JCONTRACT00000000000000",
    revision_id: "01JCONTRACTREV00000000000",
    status: "APPROVED",
    authority_revision_id: "01JCONTRACTREV00000000000",
    authority_status: "APPROVED",
    content: { chapter_purpose: "Teach the mechanism" },
  },
};

const secondChapter: ChapterView = {
  ...chapter,
  chapter_id: "01JCHAPTER200000000000000",
  ordinal: 2,
  working_title: "The next mechanism",
  chapter_contract: {
    ...chapter.chapter_contract!,
    entity_id: "01JCONTRACT20000000000000",
    revision_id: "01JCONTRACTREV20000000000",
    authority_revision_id: "01JCONTRACTREV20000000000",
  },
};

const project: ProjectView = {
  book_id: "01JBOOK000000000000000000",
  working_title: "Drafting Book",
  mode: "BOOK_FROM_ZERO",
  domain: "BUSINESS_NONFICTION",
  primary_subtype: "Strategy",
  secondary_subtype: null,
  profile_version: "business-nonfiction-v0.1",
  workflow_stage: "WRITING",
  book_contract: null,
  architecture: null,
  chapters: [chapter, secondChapter],
};

const providers = [
  {
    id: "openai",
    label: "AI Pro",
    models: [
      { id: "gpt-6-astra", label: "GPT-6 Astra" },
      { id: "gpt-5.6-sol", label: "GPT-5.6 Sol" },
    ],
  },
  {
    id: "yandex",
    label: "AI Ya",
    models: [{ id: "aliceai-llm", label: "Alice AI LLM" }],
  },
];

const calls: Array<{ method: string; path: string; body?: unknown }> = [];

function success(model = "gpt-6-astra", reasoning = "high"): DraftRunView {
  return {
    task_id: "01JTASK0000000000000000000",
    run_id: "01JRUN00000000000000000000",
    task_status: "SUCCEEDED",
    run_status: "SUCCEEDED",
    provider: "openai",
    model,
    selection_mode: "MANUAL",
    selection_scope: "OPERATION",
    routing_rationale: "Human manual model pin for operation SECTION_DRAFT",
    reasoning_effort: reasoning as DraftRunView["reasoning_effort"],
    prompt_id: "section_draft_v1",
    prompt_version: "1.1.0",
    prompt_hash: "a".repeat(64),
    input_revision_id: chapter.chapter_contract?.authority_revision_id ?? "",
    input_revision_hash: "b".repeat(64),
    unit_id: "01JUNIT0000000000000000000",
    revision_id: "01JDRAFTREV00000000000000",
    revision_hash: "c".repeat(64),
    revision_status: "DRAFT",
    text: "A bounded generated section.",
    notes: ["not approved"],
    provider_run_id: "resp_mock",
    usage: { output_tokens: 40 },
    error_code: null,
    error_message: null,
  };
}

const fakeApi: DraftApi = async function fakeApi<T>(
  method: "GET" | "POST" | "PUT",
  path: string,
  body?: unknown,
): Promise<T> {
  calls.push({ method, path, body });
  if (method === "GET" && path === "/api/launch/readiness") {
    return {
      openai_credential_state: "AVAILABLE",
      yandex_credential_state: "AVAILABLE",
      providers,
    } as T;
  }
  if (method === "GET" && path.endsWith("/model-routing")) {
    return { book_pin: null, providers } as T;
  }
  if (method === "GET" && path.endsWith("/drafts")) return [] as T;
  if (method === "POST" && path.endsWith("/drafts")) {
    const request = body as { model?: string | null; reasoning_effort?: string | null };
    return success(request.model ?? "gpt-6-astra", request.reasoning_effort ?? "high") as T;
  }
  throw new Error(`unexpected request: ${method} ${path}`);
};

beforeEach(() => {
  calls.length = 0;
});

it("starts in Astra High and returns the book text in the author workspace", async () => {
  render(<DraftingPanel project={project} chapter={chapter} api={fakeApi} />);

  expect(await screen.findByRole("heading", { name: "GPT-6 Astra" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "High" })).toHaveAttribute("aria-pressed", "true");

  fireEvent.change(screen.getByLabelText("Задача этого фрагмента"), {
    target: { value: "Explain the bounded mechanism" },
  });
  fireEvent.click(screen.getByRole("checkbox"));
  fireEvent.click(screen.getByRole("button", { name: "Запустить Astra" }));

  expect(await screen.findByText("A bounded generated section.")).toBeInTheDocument();
  expect(screen.getByText("Черновик готов")).toBeInTheDocument();
  expect(screen.getAllByText("High").length).toBeGreaterThan(0);
  expect(calls).toContainEqual({
    method: "POST",
    path: expect.stringContaining("/drafts"),
    body: expect.objectContaining({
      section_objective: "Explain the bounded mechanism",
      provider: "openai",
      model: "gpt-6-astra",
      selection_mode: "MANUAL",
      selection_scope: "OPERATION",
      reasoning_effort: "high",
    }),
  });
});

it("keeps other approved models available behind the advanced routing control", async () => {
  render(<DraftingPanel project={project} chapter={chapter} api={fakeApi} />);
  await screen.findByText("OpenAI API подключён");

  fireEvent.click(screen.getAllByText("Другие модели и маршрутизация")[0]);
  fireEvent.change(screen.getAllByLabelText("Модель")[0], {
    target: { value: "gpt-5.6-sol" },
  });

  expect(screen.getByRole("heading", { name: "GPT-5.6 Sol" })).toBeInTheDocument();
});

it("never renders a late draft response from the previously selected chapter", async () => {
  let resolveFirstChapter: (value: DraftRunView[]) => void = () => undefined;
  const firstChapterDrafts = new Promise<DraftRunView[]>((resolve) => {
    resolveFirstChapter = resolve;
  });
  const raceApi: DraftApi = async function raceApi<T>(
    method: "GET" | "POST" | "PUT",
    path: string,
  ): Promise<T> {
    if (method === "GET" && path === "/api/launch/readiness") {
      return {
        openai_credential_state: "AVAILABLE",
        yandex_credential_state: "AVAILABLE",
        providers,
      } as T;
    }
    if (method === "GET" && path.endsWith("/model-routing")) {
      return { book_pin: null, providers } as T;
    }
    if (method === "GET" && path.includes(chapter.chapter_id) && path.endsWith("/drafts")) {
      return firstChapterDrafts as Promise<T>;
    }
    if (method === "GET" && path.includes(secondChapter.chapter_id) && path.endsWith("/drafts")) {
      return [] as T;
    }
    throw new Error(`unexpected request: ${method} ${path}`);
  };

  const view = render(<DraftingPanel project={project} chapter={chapter} api={raceApi} />);
  const writer = within(view.container);
  expect(await writer.findByText("1. The mechanism")).toBeInTheDocument();

  view.rerender(<DraftingPanel project={project} chapter={secondChapter} api={raceApi} />);
  expect(await writer.findByText("2. The next mechanism")).toBeInTheDocument();
  expect(writer.queryByText("A bounded generated section.")).not.toBeInTheDocument();

  resolveFirstChapter([success()]);
  await waitFor(() =>
    expect(writer.queryByText("A bounded generated section.")).not.toBeInTheDocument(),
  );
});
