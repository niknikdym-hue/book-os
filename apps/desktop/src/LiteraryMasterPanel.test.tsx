import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import { LiteraryMasterPanel } from "./LiteraryMasterPanel";
import { coreApi } from "./api";
import type { ProjectView } from "./types";

vi.mock("./api", () => ({ coreApi: vi.fn() }));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

const project: ProjectView = {
  book_id: "B",
  working_title: "Literary Master Book",
  primary_subtype: "Strategy",
  secondary_subtype: null,
  workflow_stage: "FINAL REVIEW",
  mode: "BOOK_FROM_ZERO",
  domain: "BUSINESS_NONFICTION",
  profile_version: "business-nonfiction-v0.1",
  book_contract: null,
  architecture: null,
  chapters: [],
};

test("shows exact release blockers and cannot create early", async () => {
  vi.mocked(coreApi).mockImplementation(async (method, path) => {
    if (method === "GET" && path.endsWith("/literary-master/readiness")) {
      return {
        book_id: "B",
        ready: false,
        blockers: [{ code: "BOOKBENCH_BLOCKING", detail: "AUTHOR_VOICE is BLOCKING" }],
        snapshot_id: "S",
        snapshot_hash: "abcdef1234567890",
      } as never;
    }
    if (method === "GET" && path.endsWith("/literary-masters")) return [] as never;
    throw new Error(`unexpected API call ${method} ${path}`);
  });

  render(<LiteraryMasterPanel project={project} />);
  expect(await screen.findByText("BOOKBENCH_BLOCKING")).toBeInTheDocument();
  expect(screen.getByText(/AUTHOR_VOICE is BLOCKING/)).toBeInTheDocument();
  expect(screen.queryByText("Create Literary Master")).not.toBeInTheDocument();
  expect(screen.getByLabelText("Literary Master BookBench evidence")).toHaveTextContent("S");
});

test("requires human actor then creates master and exposes deterministic exports", async () => {
  let created = false;
  vi.mocked(coreApi).mockImplementation(async (method, path, body) => {
    if (method === "GET" && path.endsWith("/literary-master/readiness")) {
      return {
        book_id: "B",
        ready: true,
        blockers: [],
        snapshot_id: "S",
        snapshot_hash: "abcdef1234567890",
      } as never;
    }
    if (method === "GET" && path.endsWith("/literary-masters")) {
      return (created
        ? [
            {
              master_id: "MASTER1",
              book_id: "B",
              manifest_version: "literary-master.v1",
              manifest_hash: "11111111111111112222222222222222",
              canonical_content_hash: "33333333333333334444444444444444",
              book_title: "Literary Master Book",
              human_actor: "Elena",
              created_at: "2026-08-29T00:00:00Z",
              status: "LOCKED",
            },
          ]
        : []) as never;
    }
    if (method === "POST" && path.endsWith("/literary-masters")) {
      expect(body).toEqual({ human_actor: "Elena" });
      created = true;
      return { master_id: "MASTER1" } as never;
    }
    if (method === "POST" && path.endsWith("/exports/markdown")) {
      return {
        export_id: "E1",
        master_id: "MASTER1",
        format: "MARKDOWN",
        content_hash: "55555555555555556666666666666666",
        byte_length: 42,
        relative_path: "exports/MASTER1/manuscript.md",
      } as never;
    }
    if (method === "POST" && path.endsWith("/handoff/audiobook")) {
      return {
        export_id: "E2",
        master_id: "MASTER1",
        format: "AUDIOBOOK_HANDOFF_JSON",
        content_hash: "77777777777777778888888888888888",
        byte_length: 84,
        relative_path: "exports/MASTER1/audiobook-handoff.json",
      } as never;
    }
    throw new Error(`unexpected API call ${method} ${path}`);
  });

  render(<LiteraryMasterPanel project={project} />);
  const button = await screen.findByText("Create Literary Master");
  expect(button).toBeDisabled();
  fireEvent.change(screen.getByLabelText("Human release actor"), { target: { value: "Elena" } });
  expect(button).toBeEnabled();
  fireEvent.click(button);

  expect(await screen.findByText(/Master:/)).toHaveTextContent("MASTER1");
  await waitFor(() =>
    expect(vi.mocked(coreApi)).toHaveBeenCalledWith(
      "POST",
      "/api/projects/B/literary-masters",
      { human_actor: "Elena" },
    ),
  );

  fireEvent.click(screen.getByText("Export Markdown"));
  expect(await screen.findByLabelText("Markdown export evidence")).toHaveTextContent(
    "exports/MASTER1/manuscript.md",
  );

  fireEvent.click(screen.getByText("Create Audiobook handoff"));
  expect(await screen.findByLabelText("Audiobook handoff evidence")).toHaveTextContent(
    "exports/MASTER1/audiobook-handoff.json",
  );
});
