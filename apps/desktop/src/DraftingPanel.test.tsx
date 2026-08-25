import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, expect, it, vi } from "vitest";
import { invoke } from "@tauri-apps/api/core";
import { DraftingPanel } from "./DraftingPanel";
import type { ChapterView, ProjectView } from "./types";

vi.mock("@tauri-apps/api/core", () => ({ invoke: vi.fn() }));
const invokeMock = vi.mocked(invoke);

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
  chapters: [chapter],
};

beforeEach(() => invokeMock.mockReset());

it("generates a bounded DRAFT preview through the native bridge", async () => {
  invokeMock.mockImplementation(async (command, args) => {
    if (command !== "core_api") throw new Error(`unexpected command: ${command}`);
    const request = (args as { request: { method: string; path: string } }).request;
    if (request.method === "GET") return [];
    if (request.method === "POST") {
      return {
        task_id: "01JTASK0000000000000000000",
        run_id: "01JRUN00000000000000000000",
        task_status: "SUCCEEDED",
        run_status: "SUCCEEDED",
        provider: "openai",
        model: "test-writer",
        prompt_id: "section_draft_v1",
        prompt_version: "1.0.0",
        prompt_hash: "a".repeat(64),
        input_revision_id: chapter.chapter_contract?.authority_revision_id,
        input_revision_hash: "b".repeat(64),
        unit_id: "01JUNIT0000000000000000000",
        revision_id: "01JDRAFTREV00000000000000",
        revision_status: "DRAFT",
        text: "A bounded generated section.",
        notes: ["not approved"],
        provider_run_id: "resp_mock",
        usage: { output_tokens: 40 },
        error_code: null,
        error_message: null,
      };
    }
    throw new Error("unexpected request");
  });

  render(<DraftingPanel project={project} chapter={chapter} />);
  fireEvent.change(screen.getByLabelText("Section objective"), {
    target: { value: "Explain the bounded mechanism" },
  });
  fireEvent.change(screen.getByLabelText("OpenAI model"), {
    target: { value: "test-writer" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Generate Draft" }));

  expect(await screen.findByText("A bounded generated section.")).toBeInTheDocument();
  expect(screen.getAllByText("DRAFT").length).toBeGreaterThan(0);
  expect(screen.getByText(/openai · test-writer/)).toBeInTheDocument();
  expect(invokeMock).toHaveBeenCalledWith(
    "core_api",
    expect.objectContaining({
      request: expect.objectContaining({
        method: "POST",
        path: expect.stringContaining("/drafts"),
      }),
    }),
  );
});
