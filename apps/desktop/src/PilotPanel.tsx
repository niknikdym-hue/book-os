import { useCallback, useEffect, useMemo, useState } from "react";
import { coreApi } from "./api";
import type { ProjectView } from "./types";

type PilotRun = {
  pilot_id: string;
  book_id: string;
  profile_version: string;
  status: string;
  human_actor: string;
  started_at: string;
  completed_at: string | null;
  final_decision: string | null;
  final_reason: string | null;
  decision_actor: string | null;
};

type GoNoGoReadiness = { ready: boolean; blockers: string[] };

type PilotSummary = {
  pilot: PilotRun;
  stage_event_counts: Record<string, number>;
  elapsed_seconds_total: number;
  human_minutes_total: number;
  stage_recorded_cost_usd: number;
  ai_run_count: number;
  model_cost_usd: number | "UNKNOWN";
  model_identities: string[];
  claims_by_state: Record<string, number>;
  material_claims_without_evidence: number;
  editorial_by_status: Record<string, number>;
  latest_bookbench_snapshot_id: string | null;
  bookbench_blocking_count: number;
  latest_literary_master_id: string | null;
  latest_literary_master_hash: string | null;
  open_observations_by_severity: Record<string, number>;
  observations_by_category: Record<string, number>;
  human_literary_quality_judgment: boolean;
  bookbench_defect_reviewed_by_human: boolean;
  go_no_go: GoNoGoReadiness;
};

type OpenAIPreflight = {
  provider: string;
  credential_state: "AVAILABLE" | "NOT_AVAILABLE";
  writer_model: string;
  evaluator_model: string;
  editor_lane: string;
  external_calls: number;
  paid_calls: number;
};

const stages = [
  "IDEA",
  "BOOK_DEFINITION",
  "RESEARCH",
  "BOOK_CONTRACT",
  "ARCHITECTURE",
  "CHAPTER_CONTRACTS",
  "DRAFTING",
  "BOOK_MEMORY",
  "EDITORIAL",
  "BOOKBENCH",
  "FINAL_REVIEW",
  "LITERARY_MASTER",
] as const;

export function PilotPanel({ project }: { project: ProjectView }) {
  const [pilot, setPilot] = useState<PilotRun | null>(null);
  const [summary, setSummary] = useState<PilotSummary | null>(null);
  const [humanActor, setHumanActor] = useState("");
  const [stage, setStage] = useState<(typeof stages)[number]>("IDEA");
  const [stageHumanMinutes, setStageHumanMinutes] = useState("");
  const [observationText, setObservationText] = useState("");
  const [observationSeverity, setObservationSeverity] = useState("ATTENTION");
  const [writerModel, setWriterModel] = useState("");
  const [evaluatorModel, setEvaluatorModel] = useState("");
  const [preflight, setPreflight] = useState<OpenAIPreflight | null>(null);
  const [decision, setDecision] = useState("GO");
  const [decisionReason, setDecisionReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    const active = await coreApi<PilotRun | null>(
      "GET",
      `/api/projects/${project.book_id}/pilots/active`,
    );
    setPilot(active);
    if (active) {
      setSummary(
        await coreApi<PilotSummary>(
          "GET",
          `/api/projects/${project.book_id}/pilots/${active.pilot_id}/summary`,
        ),
      );
    } else {
      setSummary(null);
    }
  }, [project.book_id]);

  useEffect(() => {
    setError(null);
    setPreflight(null);
    void refresh().catch((reason: unknown) => setError(String(reason)));
  }, [refresh]);

  const completedStages = useMemo(
    () => stages.filter((item) => (summary?.stage_event_counts[item] ?? 0) > 0),
    [summary],
  );

  async function startPilot() {
    if (!humanActor.trim()) return;
    setBusy(true);
    setError(null);
    try {
      await coreApi<PilotRun>("POST", `/api/projects/${project.book_id}/pilots`, {
        human_actor: humanActor.trim(),
      });
      await refresh();
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  async function recordCheckpoint() {
    if (!pilot || !humanActor.trim()) return;
    const minutes = stageHumanMinutes.trim() ? Number(stageHumanMinutes) : null;
    setBusy(true);
    setError(null);
    try {
      await coreApi(
        "POST",
        `/api/projects/${project.book_id}/pilots/${pilot.pilot_id}/stage-events`,
        {
          stage,
          event_kind: "CHECKPOINT",
          actor: humanActor.trim(),
          actor_kind: "HUMAN",
          human_minutes: Number.isFinite(minutes) ? minutes : null,
          outcome: "SUCCESS",
          metadata: {},
        },
      );
      setStageHumanMinutes("");
      await refresh();
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  async function addObservation() {
    if (!pilot || !humanActor.trim() || !observationText.trim()) return;
    setBusy(true);
    setError(null);
    try {
      await coreApi(
        "POST",
        `/api/projects/${project.book_id}/pilots/${pilot.pilot_id}/observations`,
        {
          stage,
          category: "WORKFLOW_FRICTION",
          severity: observationSeverity,
          actor: humanActor.trim(),
          actor_kind: "HUMAN",
          description: observationText.trim(),
        },
      );
      setObservationText("");
      await refresh();
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  async function checkOpenAI() {
    if (!pilot || !writerModel.trim() || !evaluatorModel.trim()) return;
    setBusy(true);
    setError(null);
    try {
      setPreflight(
        await coreApi<OpenAIPreflight>(
          "POST",
          `/api/projects/${project.book_id}/pilots/${pilot.pilot_id}/openai-preflight`,
          {
            writer_model: writerModel.trim(),
            evaluator_model: evaluatorModel.trim(),
            editor_lane: "deterministic-m6-current",
          },
        ),
      );
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  async function recordFinalDecision() {
    if (!pilot || !summary?.go_no_go.ready || !humanActor.trim() || !decisionReason.trim()) return;
    setBusy(true);
    setError(null);
    try {
      await coreApi<PilotRun>(
        "POST",
        `/api/projects/${project.book_id}/pilots/${pilot.pilot_id}/final-decision`,
        {
          decision,
          actor: humanActor.trim(),
          actor_kind: "HUMAN",
          reason: decisionReason.trim(),
        },
      );
      await refresh();
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel" aria-label="Real-book Pilot">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">REAL BUSINESS NONFICTION PILOT</p>
          <h3>GO / NO-GO evidence</h3>
        </div>
        <span className={`badge ${summary?.go_no_go.ready ? "approved" : "draft"}`}>
          {pilot?.status === "COMPLETED"
            ? pilot.final_decision ?? "COMPLETED"
            : summary?.go_no_go.ready
              ? "HUMAN DECISION READY"
              : pilot
                ? "EVIDENCE INCOMPLETE"
                : "NOT STARTED"}
        </span>
      </div>

      <p className="muted">
        Pilot evidence is local to this book. Manuscript text is not copied into this workspace summary.
      </p>
      {error && <div className="alert">{error}</div>}

      {!pilot && (
        <div className="form-grid">
          <label className="field">
            <span>Human pilot owner</span>
            <input
              value={humanActor}
              onChange={(event) => setHumanActor(event.target.value)}
              placeholder="Owner / editor name"
            />
          </label>
          <div className="actions">
            <button
              className="primary"
              onClick={() => void startPilot()}
              disabled={busy || !humanActor.trim()}
            >
              Start real-book pilot
            </button>
          </div>
        </div>
      )}

      {pilot && summary && (
        <>
          <div className="summary-grid" aria-label="Pilot evidence summary">
            <div><strong>Stages</strong><span>{completedStages.length}/{stages.length}</span></div>
            <div><strong>Human time</strong><span>{summary.human_minutes_total} min</span></div>
            <div><strong>AI runs</strong><span>{summary.ai_run_count}</span></div>
            <div><strong>Model cost</strong><span>{String(summary.model_cost_usd)}</span></div>
            <div><strong>Open BLOCKING</strong><span>{summary.open_observations_by_severity.BLOCKING ?? 0}</span></div>
            <div><strong>Literary Master</strong><span>{summary.latest_literary_master_id ?? "not reached"}</span></div>
          </div>

          {!summary.go_no_go.ready && (
            <div aria-label="GO NO-GO blockers">
              <strong>Evidence blockers</strong>
              <ul>{summary.go_no_go.blockers.map((item) => <li key={item}>{item}</li>)}</ul>
            </div>
          )}

          {pilot.status === "ACTIVE" && (
            <>
              <div className="form-grid">
                <label className="field">
                  <span>Human actor</span>
                  <input value={humanActor} onChange={(event) => setHumanActor(event.target.value)} />
                </label>
                <label className="field">
                  <span>Pilot stage</span>
                  <select value={stage} onChange={(event) => setStage(event.target.value as typeof stage)}>
                    {stages.map((item) => <option key={item}>{item}</option>)}
                  </select>
                </label>
                <label className="field">
                  <span>Human minutes</span>
                  <input
                    inputMode="numeric"
                    value={stageHumanMinutes}
                    onChange={(event) => setStageHumanMinutes(event.target.value)}
                  />
                </label>
                <div className="actions">
                  <button
                    className="secondary"
                    onClick={() => void recordCheckpoint()}
                    disabled={busy || !humanActor.trim()}
                  >
                    Record stage checkpoint
                  </button>
                </div>
              </div>

              <div className="form-grid">
                <label className="field">
                  <span>Workflow observation</span>
                  <textarea
                    value={observationText}
                    onChange={(event) => setObservationText(event.target.value)}
                    placeholder="Local/private observation"
                  />
                </label>
                <label className="field">
                  <span>Severity</span>
                  <select
                    value={observationSeverity}
                    onChange={(event) => setObservationSeverity(event.target.value)}
                  >
                    <option>INFO</option>
                    <option>ATTENTION</option>
                    <option>BLOCKING</option>
                  </select>
                </label>
                <div className="actions">
                  <button
                    className="secondary"
                    onClick={() => void addObservation()}
                    disabled={busy || !humanActor.trim() || !observationText.trim()}
                  >
                    Record observation
                  </button>
                </div>
              </div>

              <div className="form-grid" aria-label="OpenAI zero-call preflight">
                <label className="field">
                  <span>Writer model</span>
                  <input value={writerModel} onChange={(event) => setWriterModel(event.target.value)} />
                </label>
                <label className="field">
                  <span>Evaluator model</span>
                  <input value={evaluatorModel} onChange={(event) => setEvaluatorModel(event.target.value)} />
                </label>
                <div className="actions">
                  <button
                    className="secondary"
                    onClick={() => void checkOpenAI()}
                    disabled={busy || !writerModel.trim() || !evaluatorModel.trim()}
                  >
                    Check OpenAI readiness — zero calls
                  </button>
                </div>
                {preflight && (
                  <p>
                    OpenAI credential: <strong>{preflight.credential_state}</strong> · external calls: {preflight.external_calls} · paid calls: {preflight.paid_calls}
                  </p>
                )}
              </div>

              {summary.go_no_go.ready && (
                <div className="form-grid" aria-label="Final human GO NO-GO decision">
                  <label className="field">
                    <span>Decision</span>
                    <select value={decision} onChange={(event) => setDecision(event.target.value)}>
                      <option>GO</option>
                      <option>CONDITIONAL_GO</option>
                      <option>NO_GO</option>
                    </select>
                  </label>
                  <label className="field">
                    <span>Human decision reason</span>
                    <textarea
                      value={decisionReason}
                      onChange={(event) => setDecisionReason(event.target.value)}
                    />
                  </label>
                  <div className="actions">
                    <button
                      className="primary"
                      onClick={() => void recordFinalDecision()}
                      disabled={busy || !humanActor.trim() || !decisionReason.trim()}
                    >
                      Record final human decision
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </>
      )}
    </section>
  );
}
