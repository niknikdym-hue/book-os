import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import { BookBenchPanel } from "./BookBenchPanel";
import { coreApi } from "./api";
import type { ProjectView } from "./types";

vi.mock("./api", () => ({ coreApi: vi.fn() }));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

const project: ProjectView = {
  book_id: "B",
  working_title: "BookBench Book",
  primary_subtype: "Strategy",
  secondary_subtype: null,
  workflow_stage: "WRITING",
  mode: "BOOK_FROM_ZERO",
  domain: "BUSINESS_NONFICTION",
  profile_version: "business-nonfiction-v0.1",
  book_contract: null,
  architecture: null,
  chapters: [
    {
      chapter_id: "C1",
      ordinal: 1,
      working_title: "Quality Signals",
      architecture_role: "Measure quality",
      workflow_state: "CONTRACT_APPROVED",
      chapter_contract: null,
    },
  ],
};

const snapshot = {
  snapshot_id: "S",
  snapshot_hash: "abcdef1234567890",
  current: true,
  scope: "BOOK",
  chapter_id: null,
  unit_id: null,
};

const report = {
  snapshot_id: "S",
  snapshot_hash: "abcdef1234567890",
  current: true,
  blocking_dimensions: [],
  dimensions: [
    {
      dimension: "AI_PROSE_PATHOLOGY",
      state: "ATTENTION",
      run_ids: ["R"],
      metrics: {},
      findings: [
        {
          finding_id: "F",
          dimension: "AI_PROSE_PATHOLOGY",
          category: "FALSE_CONTRAST_TEMPLATE",
          location: "revision:x chars:1-12",
          evidence: { pattern: "не X, а Y" },
          severity: "ATTENTION",
          confidence: 0.9,
          recommended_action: "Human review",
        },
      ],
    },
  ],
};

function mockApi() {
  vi.mocked(coreApi).mockImplementation(async (method, path, body) => {
    if (method === "POST" && path.endsWith("/snapshots")) {
      return { ...snapshot, ...(body as object) } as never;
    }
    if (method === "POST" && path.endsWith("/deterministic")) return [] as never;
    if (method === "GET" && path.endsWith("/report")) return report as never;
    if (method === "POST" && path.endsWith("/handoff")) return { finding_id: "E" } as never;
    if (method === "POST" && path.endsWith("/semantic")) {
      return {
        evaluation_ids: ["SEM"],
        embedding_config: { provider: "fake" },
        config_hash: "1234567890abcdef",
      } as never;
    }
    if (method === "POST" && path.endsWith("/judge")) {
      return {
        evaluation_id: "J",
        independence_state: "INDEPENDENT",
        latency_ms: 3,
        cost_usd: 0,
        output: { release_grade: true },
      } as never;
    }
    if (method === "POST" && path.endsWith("/pairwise")) {
      return {
        evaluation_id: "P",
        seed: 42,
        labels: { A: "candidate-one", B: "candidate-two" },
        winner_candidate_id: "candidate-one",
        output: { preference: "A" },
      } as never;
    }
    if (method === "POST" && path.endsWith("/voice-fingerprints")) {
      return {
        fingerprint_id: "VF",
        name: "Owner reference voice",
        extractor_version: "1.0.0",
        fingerprint_hash: "fedcba0987654321",
        reference_snapshot_id: "S",
        reference_revisions: [{ revision_id: "R", revision_hash: "H" }],
        features: {},
      } as never;
    }
    if (method === "GET" && path.endsWith("/voice-fingerprints")) {
      return [
        {
          fingerprint_id: "VF",
          name: "Owner reference voice",
          extractor_version: "1.0.0",
          fingerprint_hash: "fedcba0987654321",
          reference_snapshot_id: "S",
          reference_revisions: [{ revision_id: "R", revision_hash: "H" }],
          features: {},
        },
      ] as never;
    }
    if (method === "POST" && path.endsWith("/voice-fingerprints/VF/compare")) {
      return {
        fingerprint_id: "VF",
        target_snapshot_id: "S",
        feature_deltas: { sentence_length_mean: 1.2 },
        target_features: {},
        diagnostic_only: true,
      } as never;
    }
    if (method === "POST" && path.endsWith("/datasets")) {
      return {
        dataset_snapshot_id: "D",
        name: "Editorial decisions",
        version: 2,
        dataset_hash: "1122334455667788",
        case_count: 3,
      } as never;
    }
    if (method === "POST" && path.endsWith("/datasets/D/compare")) {
      return [
        {
          scorecard_id: "SC",
          dataset_snapshot_id: "D",
          config_id: "fake-a",
          config_hash: "CA",
          role: "WRITER",
          dimensions: { AUTHOR_VOICE: { pass: 1 } },
          severe_failure_count: 0,
          pass_count: 1,
          attention_count: 0,
          blocking_count: 0,
          latency_ms: 1,
          cost_usd: 0,
          usage: { external_calls: 0, paid_calls: 0 },
        },
      ] as never;
    }
    throw new Error(`unexpected API call: ${method} ${path}`);
  });
}

test("run shows exact finding evidence and explicit editorial handoff", async () => {
  mockApi();
  render(<BookBenchPanel project={project} />);
  fireEvent.click(screen.getByText("Создать точный снимок"));
  expect(await screen.findByText("Точный снимок готов")).toBeInTheDocument();
  fireEvent.click(screen.getByText("Запустить детерминированные проверки"));
  expect(await screen.findByText("FALSE_CONTRAST_TEMPLATE")).toBeInTheDocument();
  expect(screen.getAllByText(/revision:x chars:1-12/)).toHaveLength(2);
  fireEvent.click(screen.getByText("Передать в редактуру"));
  expect(await screen.findByText(/Передано в редактуру/)).toBeInTheDocument();
});

test("scorecards remain per-dimension with dataset identity and Без магического общего балла", async () => {
  mockApi();
  render(<BookBenchPanel project={project} />);
  fireEvent.click(screen.getByText("Сравнить тестовые конфигурации"));
  expect(await screen.findByLabelText("Dataset identity")).toHaveTextContent("Dataset v2");
  expect(await screen.findByLabelText("Configuration scorecards")).toBeInTheDocument();
  expect(screen.getAllByText(/Без магического общего балла/i).length).toBeGreaterThan(0);
});

test("chapter target, pairwise, voice fingerprint and independence controls are operational", async () => {
  mockApi();
  render(<BookBenchPanel project={project} />);

  fireEvent.change(screen.getByLabelText("Область проверки"), { target: { value: "CHAPTER" } });
  expect(screen.getByLabelText("Глава")).toHaveValue("C1");
  fireEvent.click(screen.getByText("Создать точный снимок"));
  await screen.findByText("Точный снимок готов");
  await waitFor(() =>
    expect(vi.mocked(coreApi)).toHaveBeenCalledWith(
      "POST",
      "/api/projects/B/bookbench/snapshots",
      expect.objectContaining({ scope: "CHAPTER", chapter_id: "C1" }),
    ),
  );

  fireEvent.click(screen.getByText("Запустить семантические проверки"));
  expect(await screen.findByLabelText("Semantic configuration")).toHaveTextContent("только кандидаты");

  fireEvent.click(screen.getByText("Запустить модельную оценку"));
  expect(await screen.findByLabelText("Judge independence")).toHaveTextContent("INDEPENDENT");

  fireEvent.click(screen.getByText("Сравнить два варианта"));
  expect(await screen.findByLabelText("Pairwise result")).toHaveTextContent("Seed сравнения 42");

  fireEvent.click(screen.getByText("Create Профиль авторского голоса"));
  expect(await screen.findByText(/Профиль авторского голоса создан/)).toBeInTheDocument();
  await waitFor(() => expect(screen.getByLabelText("Выбранный профиль")).toHaveValue("VF"));
  fireEvent.click(screen.getByText("Compare Профиль авторского голоса"));
  expect(await screen.findByLabelText("Voice comparison")).toHaveTextContent("только диагностика");
});
