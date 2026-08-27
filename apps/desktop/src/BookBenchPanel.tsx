import { useMemo, useState } from "react";
import { coreApi } from "./api";
import type {
  DatasetSnapshot,
  EvaluationRun,
  PairwiseResult,
  Report,
  Scorecard,
  SemanticResult,
  Snapshot,
  VoiceComparison,
  VoiceFingerprint,
} from "./bookbenchTypes";
import type { ProjectView } from "./types";

type Scope = "BOOK" | "CHAPTER" | "MANUSCRIPT_UNIT";

export function BookBenchPanel({ project }: { project: ProjectView }) {
  const [scope, setScope] = useState<Scope>("BOOK");
  const [chapterId, setChapterId] = useState(project.chapters[0]?.chapter_id ?? "");
  const [unitId, setUnitId] = useState("");
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [report, setReport] = useState<Report | null>(null);
  const [semantic, setSemantic] = useState<SemanticResult | null>(null);
  const [judge, setJudge] = useState<EvaluationRun | null>(null);
  const [pairwise, setPairwise] = useState<PairwiseResult | null>(null);
  const [candidateA, setCandidateA] = useState("Candidate A text");
  const [candidateB, setCandidateB] = useState("Candidate B text");
  const [pairwiseSeed, setPairwiseSeed] = useState(42);
  const [fingerprints, setFingerprints] = useState<VoiceFingerprint[]>([]);
  const [selectedFingerprintId, setSelectedFingerprintId] = useState("");
  const [voiceName, setVoiceName] = useState("Owner reference voice");
  const [voiceComparison, setVoiceComparison] = useState<VoiceComparison | null>(null);
  const [dataset, setDataset] = useState<DatasetSnapshot | null>(null);
  const [scorecards, setScorecards] = useState<Scorecard[]>([]);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const basePath = `/api/projects/${project.book_id}/bookbench`;
  const pathologyFindings = useMemo(
    () => report?.dimensions.find((dimension) => dimension.dimension === "AI_PROSE_PATHOLOGY")?.findings ?? [],
    [report],
  );

  async function refreshReport(snapshotId: string) {
    setReport(await coreApi<Report>("GET", `${basePath}/snapshots/${snapshotId}/report`));
  }

  async function buildSnapshot() {
    setError("");
    if (scope === "CHAPTER" && !chapterId) {
      setError("Select a chapter before building a chapter snapshot.");
      return;
    }
    if (scope === "MANUSCRIPT_UNIT" && !unitId.trim()) {
      setError("Enter a ManuscriptUnit id before building a unit snapshot.");
      return;
    }
    const body = {
      scope,
      chapter_id: scope === "CHAPTER" ? chapterId : null,
      unit_id: scope === "MANUSCRIPT_UNIT" ? unitId.trim() : null,
    };
    const next = await coreApi<Snapshot>("POST", `${basePath}/snapshots`, body);
    setSnapshot(next);
    setReport(null);
    setSemantic(null);
    setJudge(null);
    setPairwise(null);
    setVoiceComparison(null);
    setMessage("Exact snapshot ready");
  }

  async function runDeterministic() {
    if (!snapshot) return;
    await coreApi("POST", `${basePath}/snapshots/${snapshot.snapshot_id}/deterministic`);
    await refreshReport(snapshot.snapshot_id);
  }

  async function runSemantic() {
    if (!snapshot) return;
    const result = await coreApi<SemanticResult>(
      "POST",
      `${basePath}/snapshots/${snapshot.snapshot_id}/semantic`,
      { provider: "fake", model: "fake-embedding" },
    );
    setSemantic(result);
    await refreshReport(snapshot.snapshot_id);
  }

  async function runJudge() {
    if (!snapshot) return;
    const result = await coreApi<EvaluationRun>(
      "POST",
      `${basePath}/snapshots/${snapshot.snapshot_id}/judge`,
      {
        dimension: "AUTHOR_VOICE",
        provider: "fake",
        model: "fake-judge",
        config_id: "judge-v1",
        writer_identity: {
          provider: "fake",
          model: "fake-writer",
          config_id: "writer-v1",
        },
      },
    );
    setJudge(result);
    await refreshReport(snapshot.snapshot_id);
  }

  async function runPairwise() {
    if (!snapshot) return;
    const result = await coreApi<PairwiseResult>(
      "POST",
      `${basePath}/snapshots/${snapshot.snapshot_id}/pairwise`,
      {
        dimension: "AUTHOR_VOICE",
        candidates: {
          "candidate-one": candidateA,
          "candidate-two": candidateB,
        },
        seed: pairwiseSeed,
        provider: "fake",
        model: "fake-pairwise",
        config_id: "pairwise-v1",
      },
    );
    setPairwise(result);
  }

  async function loadFingerprints() {
    const items = await coreApi<VoiceFingerprint[]>("GET", `${basePath}/voice-fingerprints`);
    setFingerprints(items);
    setSelectedFingerprintId((current) => current || items[0]?.fingerprint_id || "");
  }

  async function createFingerprint() {
    if (!snapshot) return;
    const created = await coreApi<VoiceFingerprint>("POST", `${basePath}/voice-fingerprints`, {
      snapshot_id: snapshot.snapshot_id,
      name: voiceName.trim() || "Owner reference voice",
    });
    await loadFingerprints();
    setSelectedFingerprintId(created.fingerprint_id);
    setMessage("Voice Fingerprint created from exact references");
  }

  async function compareVoice() {
    if (!snapshot || !selectedFingerprintId) return;
    const comparison = await coreApi<VoiceComparison>(
      "POST",
      `${basePath}/voice-fingerprints/${selectedFingerprintId}/compare`,
      { target_snapshot_id: snapshot.snapshot_id },
    );
    setVoiceComparison(comparison);
  }

  async function compareConfigs() {
    const created = await coreApi<DatasetSnapshot>("POST", `${basePath}/datasets`, {
      name: "Editorial decisions",
    });
    setDataset(created);
    setScorecards(
      await coreApi<Scorecard[]>("POST", `${basePath}/datasets/${created.dataset_snapshot_id}/compare`, {
        configs: [
          { config_id: "fake-a", provider: "fake", model: "fake-a", role: "WRITER" },
          { config_id: "fake-b", provider: "fake", model: "fake-b", role: "WRITER" },
        ],
      }),
    );
  }

  async function sendToEditorialInbox(findingId: string) {
    await coreApi("POST", `${basePath}/findings/${findingId}/handoff`, { actor: "OWNER" });
    setMessage("Sent to Editorial Inbox for human review");
  }

  return (
    <section className="panel bookbench">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">M7 · DIAGNOSTIC DERIVED STATE</p>
          <h3>BookBench</h3>
        </div>
        <strong>No overall score</strong>
      </div>

      <p>Exact revision evidence only. Results never rewrite, approve, accept, or waive authority.</p>

      <div className="toolbar">
        <label>
          Evaluation scope
          <select
            aria-label="Evaluation scope"
            value={scope}
            onChange={(event) => setScope(event.target.value as Scope)}
          >
            <option value="BOOK">BOOK</option>
            <option value="CHAPTER">CHAPTER</option>
            <option value="MANUSCRIPT_UNIT">MANUSCRIPT_UNIT</option>
          </select>
        </label>
        {scope === "CHAPTER" && (
          <label>
            Chapter target
            <select
              aria-label="Chapter target"
              value={chapterId}
              onChange={(event) => setChapterId(event.target.value)}
            >
              {project.chapters.map((chapter) => (
                <option key={chapter.chapter_id} value={chapter.chapter_id}>
                  {chapter.ordinal}. {chapter.working_title}
                </option>
              ))}
            </select>
          </label>
        )}
        {scope === "MANUSCRIPT_UNIT" && (
          <label>
            ManuscriptUnit target
            <input
              aria-label="ManuscriptUnit target"
              value={unitId}
              onChange={(event) => setUnitId(event.target.value)}
              placeholder="unit id"
            />
          </label>
        )}
        <button onClick={() => void buildSnapshot()}>Build exact snapshot</button>
      </div>

      <div className="toolbar">
        <button disabled={!snapshot} onClick={() => void runDeterministic()}>
          Run deterministic
        </button>
        <button disabled={!snapshot} onClick={() => void runSemantic()}>
          Run semantic
        </button>
        <button disabled={!snapshot} onClick={() => void runJudge()}>
          Run judge
        </button>
        <button disabled={!snapshot} onClick={() => void runPairwise()}>
          Run pairwise
        </button>
      </div>

      <div className="toolbar">
        <label>
          Candidate one
          <input
            aria-label="Candidate one"
            value={candidateA}
            onChange={(event) => setCandidateA(event.target.value)}
          />
        </label>
        <label>
          Candidate two
          <input
            aria-label="Candidate two"
            value={candidateB}
            onChange={(event) => setCandidateB(event.target.value)}
          />
        </label>
        <label>
          Pairwise seed
          <input
            aria-label="Pairwise seed"
            type="number"
            value={pairwiseSeed}
            onChange={(event) => setPairwiseSeed(Number(event.target.value))}
          />
        </label>
      </div>

      <section>
        <h4>Voice Fingerprint</h4>
        <div className="toolbar">
          <label>
            Fingerprint name
            <input
              aria-label="Fingerprint name"
              value={voiceName}
              onChange={(event) => setVoiceName(event.target.value)}
            />
          </label>
          <button disabled={!snapshot} onClick={() => void createFingerprint()}>
            Create Voice Fingerprint
          </button>
          <button onClick={() => void loadFingerprints()}>Load Voice Fingerprints</button>
          <label>
            Selected fingerprint
            <select
              aria-label="Selected fingerprint"
              value={selectedFingerprintId}
              onChange={(event) => setSelectedFingerprintId(event.target.value)}
            >
              <option value="">Select fingerprint</option>
              {fingerprints.map((fingerprint) => (
                <option key={fingerprint.fingerprint_id} value={fingerprint.fingerprint_id}>
                  {fingerprint.name} · v{fingerprint.extractor_version}
                </option>
              ))}
            </select>
          </label>
          <button
            disabled={!snapshot || !selectedFingerprintId}
            onClick={() => void compareVoice()}
          >
            Compare Voice Fingerprint
          </button>
        </div>
      </section>

      <button onClick={() => void compareConfigs()}>Compare fake configs</button>

      {error && <p role="alert">{error}</p>}
      {message && <p role="status">{message}</p>}

      {snapshot && (
        <p aria-label="BookBench snapshot identity">
          <strong>{snapshot.current ? "CURRENT" : "NON-CURRENT / STALE"}</strong> · {snapshot.scope} ·
          snapshot {snapshot.snapshot_hash.slice(0, 12)}
        </p>
      )}

      {semantic && (
        <p aria-label="Semantic configuration">
          Semantic config {semantic.config_hash.slice(0, 12)} · candidates only
        </p>
      )}

      {judge && (
        <p aria-label="Judge independence">
          Judge independence: <strong>{judge.independence_state}</strong> · latency {judge.latency_ms}ms ·
          cost ${judge.cost_usd ?? 0}
        </p>
      )}

      {pairwise && (
        <p aria-label="Pairwise result">
          Pairwise seed {pairwise.seed} · A={pairwise.labels.A} · B={pairwise.labels.B} · winner {pairwise.winner_candidate_id ?? "TIE"}
        </p>
      )}

      {voiceComparison && (
        <section aria-label="Voice comparison">
          <h4>Voice comparison · diagnostic only</h4>
          <pre>{JSON.stringify(voiceComparison.feature_deltas, null, 2)}</pre>
        </section>
      )}

      {report?.dimensions.map((dimension) => (
        <article key={dimension.dimension} className="finding-card">
          <h4>
            {dimension.dimension} <span className="badge">{dimension.state}</span>
          </h4>
          {dimension.findings.map((finding) => (
            <div key={finding.finding_id}>
              <strong>{finding.category}</strong>
              <p>
                {finding.location} · confidence {finding.confidence}
              </p>
              <pre>{JSON.stringify(finding.evidence, null, 2)}</pre>
              <p>{finding.recommended_action}</p>
              <button onClick={() => void sendToEditorialInbox(finding.finding_id)}>
                Send to Editorial Inbox
              </button>
            </div>
          ))}
        </article>
      ))}

      <section aria-label="AI prose pathology examples">
        <h4>AI-prose pathology examples</h4>
        {pathologyFindings.length === 0 ? (
          <p>No measured pathology examples in the current report.</p>
        ) : (
          pathologyFindings.map((finding) => (
            <p key={finding.finding_id}>
              {finding.category} · {finding.location} · {JSON.stringify(finding.evidence)}
            </p>
          ))
        )}
      </section>

      {dataset && (
        <p aria-label="Dataset identity">
          Dataset v{dataset.version} · {dataset.dataset_hash.slice(0, 12)} · {dataset.case_count} cases
        </p>
      )}

      {scorecards.length > 0 && (
        <section aria-label="Configuration scorecards">
          <h4>Dataset/config scorecards — no overall score</h4>
          {scorecards.map((scorecard) => (
            <article key={scorecard.scorecard_id}>
              <strong>
                {scorecard.role} · {scorecard.config_id}
              </strong>
              <p>
                PASS {scorecard.pass_count} · ATTENTION {scorecard.attention_count} · BLOCKING {scorecard.blocking_count} · severe {scorecard.severe_failure_count}
              </p>
              <pre>{JSON.stringify(scorecard.dimensions, null, 2)}</pre>
              <small>
                latency {scorecard.latency_ms}ms · cost ${scorecard.cost_usd} · usage {JSON.stringify(scorecard.usage)}
              </small>
            </article>
          ))}
        </section>
      )}
    </section>
  );
}
