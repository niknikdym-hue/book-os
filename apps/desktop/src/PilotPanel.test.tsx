import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import { PilotPanel } from "./PilotPanel";
import { coreApi } from "./api";
import type { ProjectView } from "./types";

vi.mock("./api", () => ({ coreApi: vi.fn() }));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

const project: ProjectView = {
  book_id: "B",
  working_title: "Private Pilot Book",
  primary_subtype: "Strategy",
  secondary_subtype: null,
  workflow_stage: "IDEA",
  mode: "BOOK_FROM_ZERO",
  domain: "BUSINESS_NONFICTION",
  profile_version: "business-nonfiction-v0.1",
  book_contract: null,
  architecture: null,
  chapters: [],
};

const pilot = {
  pilot_id: "P1",
  book_id: "B",
  profile_version: "real-business-nonfiction-pilot.v1",
  status: "ACTIVE",
  human_actor: "Elena",
  started_at: "2026-08-29T00:00:00Z",
  completed_at: null,
  final_decision: null,
  final_reason: null,
  decision_actor: null,
};

function summary(ready = false) {
  return {
    pilot,
    stage_event_counts: { IDEA: 1 },
    elapsed_seconds_total: 120,
    human_minutes_total: 15,
    stage_recorded_cost_usd: 0,
    ai_run_count: ready ? 3 : 0,
    model_cost_usd: ready ? "UNKNOWN" : 0,
    model_identities: ready ? ["openai:writer-model"] : [],
    claims_by_state: {},
    material_claims_without_evidence: 0,
    editorial_by_status: {},
    latest_bookbench_snapshot_id: ready ? "S1" : null,
    bookbench_blocking_count: 0,
    latest_literary_master_id: ready ? "M1" : null,
    latest_literary_master_hash: ready ? "abcdef" : null,
    open_observations_by_severity: {},
    observations_by_category: {},
    human_literary_quality_judgment: ready,
    bookbench_defect_reviewed_by_human: ready,
    go_no_go: {
      ready,
      blockers: ready ? [] : ["LITERARY_MASTER_MISSING", "AI_RUN_EVIDENCE_MISSING"],
    },
  };
}

test("starts a pilot only with an explicit human owner", async () => {
  let started = false;
  vi.mocked(coreApi).mockImplementation(async (method, path, body) => {
    if (method === "GET" && path.endsWith("/pilots/active")) return (started ? pilot : null) as never;
    if (method === "POST" && path.endsWith("/pilots")) {
      expect(body).toEqual({ human_actor: "Elena" });
      started = true;
      return pilot as never;
    }
    if (method === "GET" && path.endsWith("/summary")) return summary(false) as never;
    throw new Error(`unexpected API call ${method} ${path}`);
  });

  render(<PilotPanel project={project} />);
  const button = await screen.findByText("Start real-book pilot");
  expect(button).toBeDisabled();
  fireEvent.change(screen.getByLabelText("Human pilot owner"), { target: { value: "Elena" } });
  expect(button).toBeEnabled();
  fireEvent.click(button);
  expect(await screen.findByLabelText("Pilot evidence summary")).toHaveTextContent("1/12");
});

test("shows fail-closed blockers and zero-call OpenAI preflight", async () => {
  vi.mocked(coreApi).mockImplementation(async (method, path) => {
    if (method === "GET" && path.endsWith("/pilots/active")) return pilot as never;
    if (method === "GET" && path.endsWith("/summary")) return summary(false) as never;
    if (method === "POST" && path.endsWith("/openai-preflight")) {
      return {
        provider: "openai",
        book_id: "B",
        pilot_id: "P1",
        credential_state: "AVAILABLE",
        writer_model: "writer-model",
        evaluator_model: "evaluator-model",
        editor_lane: "deterministic-m6-current",
        max_requests: 3,
        max_input_tokens: 1000,
        max_output_tokens: 500,
        max_cost_usd: 1.25,
        plan_hash: "a".repeat(64),
        external_calls: 0,
        paid_calls: 0,
      } as never;
    }
    throw new Error(`unexpected API call ${method} ${path}`);
  });

  render(<PilotPanel project={project} />);
  expect(await screen.findByText("LITERARY_MASTER_MISSING")).toBeInTheDocument();
  expect(screen.queryByLabelText("Final human GO NO-GO decision")).not.toBeInTheDocument();

  fireEvent.change(screen.getByLabelText("Writer model"), { target: { value: "writer-model" } });
  fireEvent.change(screen.getByLabelText("Evaluator model"), {
    target: { value: "evaluator-model" },
  });
  fireEvent.change(screen.getByLabelText("Max requests"), { target: { value: "3" } });
  fireEvent.change(screen.getByLabelText("Max input tokens"), { target: { value: "1000" } });
  fireEvent.change(screen.getByLabelText("Max output tokens"), { target: { value: "500" } });
  fireEvent.change(screen.getByLabelText("Max cost USD"), { target: { value: "1.25" } });
  fireEvent.click(screen.getByText("Check OpenAI readiness — zero calls"));
  expect(await screen.findByText(/OpenAI credential:/)).toHaveTextContent("AVAILABLE");
  expect(screen.getByText(/OpenAI credential:/)).toHaveTextContent("external calls: 0");
  expect(screen.getByText(/OpenAI credential:/)).toHaveTextContent("paid calls: 0");
});

test("shows final decision only when evidence is ready and records a HUMAN decision", async () => {
  vi.mocked(coreApi).mockImplementation(async (method, path, body) => {
    if (method === "GET" && path.endsWith("/pilots/active")) return pilot as never;
    if (method === "GET" && path.endsWith("/summary")) return summary(true) as never;
    if (method === "POST" && path.endsWith("/final-decision")) {
      expect(body).toEqual({
        decision: "GO",
        actor: "Elena",
        actor_kind: "HUMAN",
        reason: "Quality threshold passed.",
      });
      return { ...pilot, status: "COMPLETED", final_decision: "GO" } as never;
    }
    throw new Error(`unexpected API call ${method} ${path}`);
  });

  render(<PilotPanel project={project} />);
  expect(await screen.findByLabelText("Final human GO NO-GO decision")).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText("Human actor"), { target: { value: "Elena" } });
  fireEvent.change(screen.getByLabelText("Human decision reason"), {
    target: { value: "Quality threshold passed." },
  });
  fireEvent.click(screen.getByText("Record final human decision"));
  await waitFor(() =>
    expect(vi.mocked(coreApi)).toHaveBeenCalledWith(
      "POST",
      "/api/projects/B/pilots/P1/final-decision",
      {
        decision: "GO",
        actor: "Elena",
        actor_kind: "HUMAN",
        reason: "Quality threshold passed.",
      },
    ),
  );
});
