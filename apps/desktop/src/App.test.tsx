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

it("shows authenticated Local Core health and creates a native book project", async () => {
  invokeMock.mockImplementation(async (command, args) => {
    if (command === "core_health") return { status: "healthy", version: "0.1.0" };
    if (command === "core_api") {
      const request = (args as { request: { method: string; path: string } }).request;
      if (request.method === "GET" && request.path === "/api/projects") return [];
      if (request.method === "POST" && request.path === "/api/projects") return project();
    }
    throw new Error(`unexpected invoke: ${command}`);
  });

  render(<App />);
  expect(await screen.findByText("Local Core healthy")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Create New Book" }));
  fireEvent.change(screen.getByLabelText("Working title"), {
    target: { value: "Operating Book" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Create project" }));

  expect(await screen.findByRole("heading", { name: "Operating Book" })).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "Book Contract" })).toBeInTheDocument();
  expect(invokeMock).toHaveBeenCalledWith(
    "core_api",
    expect.objectContaining({
      request: expect.objectContaining({ method: "POST", path: "/api/projects" }),
    }),
  );
});

it("routes Book Contract draft and approval through the token-safe native bridge", async () => {
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
  await screen.findByText("Local Core healthy");
  fireEvent.click(await screen.findByRole("button", { name: /Operating Book/ }));
  expect(await screen.findByText("DRAFT")).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: "Save Draft" }));
  await waitFor(() =>
    expect(invokeMock).toHaveBeenCalledWith(
      "core_api",
      expect.objectContaining({
        request: expect.objectContaining({ method: "PUT", path: expect.stringContaining("book-contract/draft") }),
      }),
    ),
  );

  fireEvent.click(screen.getByRole("button", { name: "Approve Book Contract" }));
  expect(await screen.findByText("APPROVED")).toBeInTheDocument();
  expect(invokeMock).toHaveBeenCalledWith(
    "core_api",
    expect.objectContaining({
      request: expect.objectContaining({ method: "POST", path: expect.stringContaining("book-contract/approve") }),
    }),
  );
});
