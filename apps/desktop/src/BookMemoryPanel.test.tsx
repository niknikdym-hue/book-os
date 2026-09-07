import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import { BookMemoryPanel } from "./BookMemoryPanel";
import type { MemoryApi, MemoryIndexStatus, MemorySearchResult } from "./memoryTypes";
import type { ChapterView, ProjectView } from "./types";

const chapter: ChapterView = {
  chapter_id: "01JCHAPTER000000000000000",
  ordinal: 1,
  working_title: "Memory chapter",
  architecture_role: "Test whole-book memory",
  workflow_state: "CONTRACT_APPROVED",
  chapter_contract: null,
};

const project: ProjectView = {
  book_id: "01JBOOK000000000000000000",
  working_title: "Memory Book",
  mode: "BOOK_FROM_ZERO",
  domain: "BUSINESS_NONFICTION",
  primary_subtype: "Strategy",
  secondary_subtype: null,
  profile_version: "business-nonfiction-v0.1",
  workflow_stage: "WRITING",
  book_contract: null,
  architecture: null,
  chapters: [chapter],
};

const lexicalStatus: MemoryIndexStatus = {
  book_id: project.book_id,
  status: "LEXICAL_READY",
  document_count: 6,
  embedding_count: 0,
  provider: null,
  model: null,
  model_version: null,
  config_hash: null,
  dimension: null,
  updated_at: "2026-08-26T10:00:00Z",
};

const semanticStatus: MemoryIndexStatus = {
  ...lexicalStatus,
  status: "SEMANTIC_READY",
  embedding_count: 6,
  provider: "fake",
  model: "memory-test",
  model_version: "fake-v1",
  config_hash: "a".repeat(64),
  dimension: 8,
};

const result: MemorySearchResult = {
  memory_id: "01JMEMORY0000000000000000",
  object_kind: "MANUSCRIPT_UNIT",
  object_id: "01JUNIT0000000000000000000",
  chapter_id: chapter.chapter_id,
  revision_id: "01JREVISION000000000000000",
  revision_hash: "b".repeat(64),
  content_hash: "c".repeat(64),
  source_status: "DRAFT",
  currentness: "CURRENT",
  text: "Whole-book memory keeps the current revision visible.",
  lexical_score: 0.91,
  semantic_score: 0.95,
  fused_score: 0.032,
  lexical_rank: 1,
  semantic_rank: 1,
  fused_rank: 1,
};

it("rebuilds semantic memory then returns a stable CURRENT hybrid result", async () => {
  const calls: Array<{ method: string; path: string; body?: unknown }> = [];
  const api: MemoryApi = async function api<T>(
    method: "GET" | "POST" | "PUT",
    path: string,
    body?: unknown,
  ): Promise<T> {
    calls.push({ method, path, body });
    if (method === "GET" && path.endsWith("/memory/status")) return lexicalStatus as T;
    if (method === "POST" && path.endsWith("/memory/rebuild")) return semanticStatus as T;
    if (method === "POST" && path.endsWith("/memory/search")) return [result] as T;
    if (method === "POST" && path.endsWith("/memory/sync")) return lexicalStatus as T;
    throw new Error(`unexpected API call: ${method} ${path}`);
  };

  render(<BookMemoryPanel project={project} chapter={chapter} api={api} />);

  expect(await screen.findByText("Лексический индекс готов")).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText("Embedding model"), {
    target: { value: "memory-test" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Перестроить семантическую память" }));
  expect(await screen.findByText("Семантический индекс готов")).toBeInTheDocument();

  fireEvent.change(screen.getByLabelText("Book Memory query"), {
    target: { value: "whole book current revision" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Искать в памяти книги" }));

  expect(
    await screen.findByText("Whole-book memory keeps the current revision visible."),
  ).toBeInTheDocument();
  expect(screen.getByText("Текущая версия")).toBeInTheDocument();
  expect(screen.getByText(result.revision_id, { selector: "code" })).toBeInTheDocument();
  expect(screen.getByText(result.revision_hash, { selector: "code" })).toBeInTheDocument();

  expect(calls).toContainEqual({
    method: "POST",
    path: expect.stringContaining("/memory/rebuild"),
    body: { provider: "openai", model: "memory-test" },
  });
  expect(calls).toContainEqual({
    method: "POST",
    path: expect.stringContaining("/memory/search"),
    body: expect.objectContaining({
      query: "whole book current revision",
      mode: "HYBRID",
      scope: "CURRENT",
    }),
  });
});
