from pathlib import Path

bookbench = Path("services/local-core/src/book_os_core/bookbench.py")
text = bookbench.read_text(encoding="utf-8")
anchor = '''    def compare_voice(\n        self, book_id: str, fingerprint_id: str, target_snapshot_id: str\n    ) -> VoiceComparisonView:\n'''
method = '''    def list_voice_fingerprints(self, book_id: str) -> list[VoiceFingerprintView]:\n        engine = self._engine(book_id)\n        try:\n            with engine.connect() as connection:\n                fingerprint_ids = [\n                    cast(str, value)\n                    for value in connection.execute(\n                        text(\n                            "SELECT fingerprint_id FROM voice_fingerprints "\n                            "WHERE book_id=:book_id ORDER BY created_at,fingerprint_id"\n                        ),\n                        {"book_id": book_id},\n                    ).scalars()\n                ]\n        finally:\n            engine.dispose()\n        return [self.get_voice_fingerprint(book_id, item) for item in fingerprint_ids]\n\n'''
if method not in text:
    if anchor not in text:
        raise SystemExit("bookbench voice anchor missing")
    bookbench.write_text(text.replace(anchor, method + anchor, 1), encoding="utf-8")

app = Path("services/local-core/src/book_os_core/app.py")
text = app.read_text(encoding="utf-8")
anchor = '''    @app.post("/api/projects/{book_id}/bookbench/voice-fingerprints/{fingerprint_id}/compare")\n'''
route = '''    @app.get("/api/projects/{book_id}/bookbench/voice-fingerprints")\n    def list_voice_fingerprints(\n        book_id: str, service: BookBenchService = Depends(bookbench_service)\n    ) -> list[dict[str, object]]:\n        return [\n            item.model_dump(mode="json") for item in service.list_voice_fingerprints(book_id)\n        ]\n\n'''
if route not in text:
    if anchor not in text:
        raise SystemExit("app voice route anchor missing")
    app.write_text(text.replace(anchor, route + anchor, 1), encoding="utf-8")

backend_tests = Path("services/local-core/tests/test_bookbench.py")
text = backend_tests.read_text(encoding="utf-8")
anchor = '''    assert "rhetorical_question_rate" in fingerprint.features\n\n    comparison = service.compare_voice(\n'''
replacement = '''    assert "rhetorical_question_rate" in fingerprint.features\n    listed = service.list_voice_fingerprints(state["book_id"])\n    assert [item.fingerprint_id for item in listed] == [fingerprint.fingerprint_id]\n    assert listed[0].reference_revisions == fingerprint.reference_revisions\n\n    comparison = service.compare_voice(\n'''
if "listed = service.list_voice_fingerprints" not in text:
    if anchor not in text:
        raise SystemExit("bookbench test voice anchor missing")
    backend_tests.write_text(text.replace(anchor, replacement, 1), encoding="utf-8")

desktop_test = Path("apps/desktop/src/BookBenchPanel.test.tsx")
desktop_test.write_text(r'''import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
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
  fireEvent.click(screen.getByText("Build exact snapshot"));
  expect(await screen.findByText("Exact snapshot ready")).toBeInTheDocument();
  fireEvent.click(screen.getByText("Run deterministic"));
  expect(await screen.findByText("FALSE_CONTRAST_TEMPLATE")).toBeInTheDocument();
  expect(screen.getByText(/revision:x chars:1-12/)).toBeInTheDocument();
  fireEvent.click(screen.getByText("Send to Editorial Inbox"));
  expect(await screen.findByText(/Sent to Editorial Inbox/)).toBeInTheDocument();
});

test("scorecards remain per-dimension with dataset identity and no overall score", async () => {
  mockApi();
  render(<BookBenchPanel project={project} />);
  fireEvent.click(screen.getByText("Compare fake configs"));
  expect(await screen.findByLabelText("Dataset identity")).toHaveTextContent("Dataset v2");
  expect(await screen.findByLabelText("Configuration scorecards")).toBeInTheDocument();
  expect(screen.getAllByText(/no overall score/i).length).toBeGreaterThan(0);
});

test("chapter target, pairwise, voice fingerprint and independence controls are operational", async () => {
  mockApi();
  render(<BookBenchPanel project={project} />);

  fireEvent.change(screen.getByLabelText("Evaluation scope"), { target: { value: "CHAPTER" } });
  expect(screen.getByLabelText("Chapter target")).toHaveValue("C1");
  fireEvent.click(screen.getByText("Build exact snapshot"));
  await screen.findByText("Exact snapshot ready");
  await waitFor(() =>
    expect(vi.mocked(coreApi)).toHaveBeenCalledWith(
      "POST",
      "/api/projects/B/bookbench/snapshots",
      expect.objectContaining({ scope: "CHAPTER", chapter_id: "C1" }),
    ),
  );

  fireEvent.click(screen.getByText("Run semantic"));
  expect(await screen.findByLabelText("Semantic configuration")).toHaveTextContent("candidates only");

  fireEvent.click(screen.getByText("Run judge"));
  expect(await screen.findByLabelText("Judge independence")).toHaveTextContent("INDEPENDENT");

  fireEvent.click(screen.getByText("Run pairwise"));
  expect(await screen.findByLabelText("Pairwise result")).toHaveTextContent("Pairwise seed 42");

  fireEvent.click(screen.getByText("Create Voice Fingerprint"));
  expect(await screen.findByText(/Voice Fingerprint created/)).toBeInTheDocument();
  await waitFor(() => expect(screen.getByLabelText("Selected fingerprint")).toHaveValue("VF"));
  fireEvent.click(screen.getByText("Compare Voice Fingerprint"));
  expect(await screen.findByLabelText("Voice comparison")).toHaveTextContent("diagnostic only");
});
''', encoding="utf-8")
