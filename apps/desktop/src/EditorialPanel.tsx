import { useCallback, useEffect, useMemo, useState } from "react";
import { coreApi } from "./api";
import type {
  DecisionResult,
  EditorialApi,
  EditorialRole,
  EditorialRunResult,
  FindingSeverity,
  FindingStatus,
  InboxItem,
  ProposalView,
} from "./editorialTypes";
import type { ChapterView, ProjectView } from "./types";

type EditorialPanelProps = {
  project: ProjectView;
  chapter: ChapterView | null;
  api?: EditorialApi;
};

const roles: Array<{ value: "ALL" | EditorialRole; label: string }> = [
  { value: "ALL", label: "All roles" },
  { value: "DEVELOPMENTAL_EDITOR", label: "Developmental Editor" },
  { value: "CROSS_BOOK_AUDITOR", label: "Cross-book Auditor" },
  { value: "FACT_CHECKER", label: "Fact Checker" },
  { value: "LITERARY_EDITOR", label: "Literary Editor" },
  { value: "STYLE_GUARDIAN", label: "Style Guardian" },
];

const severities: Array<"ALL" | FindingSeverity> = [
  "ALL",
  "CRITICAL",
  "MAJOR",
  "MINOR",
  "INFO",
];
const statuses: Array<"ALL" | FindingStatus> = [
  "OPEN",
  "RESOLVED",
  "WAIVED",
  "SUPERSEDED",
  "ALL",
];

function short(value: string): string {
  return value.length <= 14 ? value : `${value.slice(0, 12)}…`;
}

export function EditorialPanel({ project, chapter, api = coreApi }: EditorialPanelProps) {
  const [role, setRole] = useState<"ALL" | EditorialRole>("ALL");
  const [severity, setSeverity] = useState<"ALL" | FindingSeverity>("ALL");
  const [status, setStatus] = useState<"ALL" | FindingStatus>("OPEN");
  const [items, setItems] = useState<InboxItem[]>([]);
  const [selectedFindingId, setSelectedFindingId] = useState<string | null>(null);
  const [proposedText, setProposedText] = useState("");
  const [rationale, setRationale] = useState("");
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastDecision, setLastDecision] = useState<DecisionResult | null>(null);
  const [lastRun, setLastRun] = useState<EditorialRunResult | null>(null);

  const basePath = `/api/projects/${project.book_id}/editorial`;
  const selected = useMemo(
    () => items.find((item) => item.finding.finding_id === selectedFindingId) ?? null,
    [items, selectedFindingId],
  );

  const loadInbox = useCallback(async () => {
    const params = new URLSearchParams();
    if (role !== "ALL") params.set("role", role);
    params.set("status", status === "ALL" ? "" : status);
    if (severity !== "ALL") params.set("severity", severity);
    const query = params.toString();
    const next = await api<InboxItem[]>("GET", `${basePath}/inbox${query ? `?${query}` : ""}`);
    setItems(next);
    setSelectedFindingId((current) =>
      current && next.some((item) => item.finding.finding_id === current)
        ? current
        : (next[0]?.finding.finding_id ?? null),
    );
  }, [api, basePath, role, severity, status]);

  useEffect(() => {
    setItems([]);
    setSelectedFindingId(null);
    setLastDecision(null);
    setError(null);
    void loadInbox().catch((cause: unknown) => setError(String(cause)));
  }, [loadInbox]);

  async function runAudit(kind: "developmental" | "cross-book" | "fact-check") {
    setBusy(true);
    setError(null);
    try {
      const path =
        kind === "developmental"
          ? `${basePath}/run/developmental/${chapter?.chapter_id ?? ""}`
          : `${basePath}/run/${kind}`;
      if (kind === "developmental" && !chapter) throw new Error("Select a chapter first.");
      const run = await api<EditorialRunResult>("POST", path);
      setLastRun(run);
      await loadInbox();
      if (run.findings[0]) setSelectedFindingId(run.findings[0].finding_id);
    } catch (cause: unknown) {
      setError(String(cause));
    } finally {
      setBusy(false);
    }
  }

  async function createProposal() {
    if (!selected) return;
    if (selected.finding.target_kind !== "MANUSCRIPT_UNIT") {
      setError("Text proposals in M6 are bounded to ManuscriptUnit findings.");
      return;
    }
    if (!proposedText.trim() || !rationale.trim()) {
      setError("Proposed replacement text and rationale are required.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const proposal = await api<ProposalView>(
        "POST",
        `${basePath}/findings/${selected.finding.finding_id}/proposals`,
        {
          proposed_text: proposedText.trim(),
          rationale: rationale.trim(),
          actor: "OWNER",
          actor_kind: "HUMAN",
        },
      );
      await loadInbox();
      setSelectedFindingId(proposal.finding_id);
    } catch (cause: unknown) {
      setError(String(cause));
    } finally {
      setBusy(false);
    }
  }

  async function decide(action: "accept" | "reject" | "request-revision" | "waive") {
    if (!selected) return;
    const normalizedReason = reason.trim();
    if (!normalizedReason) {
      setError("A human decision reason is required.");
      return;
    }
    const proposal = selected.latest_proposal;
    if (action !== "waive" && !proposal) {
      setError("Select a finding with an open proposal first.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const path =
        action === "waive"
          ? `${basePath}/findings/${selected.finding.finding_id}/waive${proposal ? `?proposal_id=${encodeURIComponent(proposal.proposal_id)}` : ""}`
          : `${basePath}/findings/${selected.finding.finding_id}/proposals/${proposal?.proposal_id}/${action}`;
      const decision = await api<DecisionResult>("POST", path, {
        actor: "OWNER",
        actor_kind: "HUMAN",
        reason: normalizedReason,
      });
      setLastDecision(decision);
      setReason("");
      setProposedText("");
      setRationale("");
      await loadInbox();
    } catch (cause: unknown) {
      setError(String(cause));
    } finally {
      setBusy(false);
    }
  }

  const proposal = selected?.latest_proposal ?? null;
  const baselineState = selected?.stale ? "STALE" : "CURRENT";

  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">M6 · HUMAN AUTHORITY</p>
          <h3>Editorial / Decision Inbox</h3>
          <p>
            Finding ≠ edit. Proposal ≠ authority. Material changes become current only after a human
            decision against an unchanged exact baseline.
          </p>
        </div>
        <strong>{items.length} inbox items</strong>
      </div>

      <div className="actions">
        <button disabled={busy || !chapter} onClick={() => void runAudit("developmental")}>
          Run Developmental audit
        </button>
        <button disabled={busy} onClick={() => void runAudit("cross-book")}>
          Run Cross-book audit
        </button>
        <button disabled={busy} onClick={() => void runAudit("fact-check")}>
          Run Fact Checker
        </button>
      </div>
      {lastRun && (
        <p>
          Last audit: <strong>{lastRun.role}</strong> · {lastRun.findings.length} findings · run{" "}
          <code>{short(lastRun.run_id)}</code>
        </p>
      )}

      <div className="form-grid">
        <label className="field">
          <span>Role</span>
          <select
            aria-label="Editorial role filter"
            value={role}
            onChange={(event) => setRole(event.target.value as "ALL" | EditorialRole)}
          >
            {roles.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>Status</span>
          <select
            aria-label="Editorial status filter"
            value={status}
            onChange={(event) => setStatus(event.target.value as "ALL" | FindingStatus)}
          >
            {statuses.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>Severity</span>
          <select
            aria-label="Editorial severity filter"
            value={severity}
            onChange={(event) => setSeverity(event.target.value as "ALL" | FindingSeverity)}
          >
            {severities.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="two-columns">
        <div>
          <h4>Findings</h4>
          {items.length === 0 ? (
            <p>No findings in this filter.</p>
          ) : (
            items.map((item) => (
              <button
                className={`project-link ${selectedFindingId === item.finding.finding_id ? "active" : ""}`}
                key={item.finding.finding_id}
                onClick={() => setSelectedFindingId(item.finding.finding_id)}
              >
                <strong>
                  {item.finding.severity} · {item.finding.role}
                </strong>
                <span>{item.finding.category}</span>
                <small>{item.stale ? "STALE" : item.finding.status}</small>
              </button>
            ))
          )}
        </div>

        <div>
          {selected ? (
            <>
              <div className="subheading">
                <strong>{selected.finding.category}</strong>
                <strong>{baselineState}</strong>
              </div>
              <p>{selected.finding.diagnosis}</p>
              <p>
                <strong>Why:</strong> {selected.finding.why}
              </p>
              <p>
                target {selected.finding.target_kind} · unit {selected.finding.unit_id ?? "—"} · chapter{" "}
                {selected.finding.chapter_id ?? "—"}
              </p>
              <p>
                base revision <code>{selected.finding.base_revision_id}</code>
              </p>
              <p>
                base hash <code>{selected.finding.base_revision_hash}</code>
              </p>
              <p>
                confidence {selected.finding.confidence.toFixed(2)} · severity {selected.finding.severity}
              </p>
              {selected.finding.expected_effect && (
                <p>
                  <strong>Expected effect:</strong> {selected.finding.expected_effect}
                </p>
              )}
              {selected.finding.risks && (
                <p>
                  <strong>Risks:</strong> {selected.finding.risks}
                </p>
              )}

              {proposal ? (
                <div>
                  <div className="subheading">
                    <strong>Proposal {proposal.status}</strong>
                    <strong>{proposal.stale ? "STALE" : "CURRENT BASE"}</strong>
                  </div>
                  <pre aria-label="Editorial proposal diff">{proposal.diff}</pre>
                </div>
              ) : selected.finding.target_kind === "MANUSCRIPT_UNIT" ? (
                <div className="form-grid">
                  <label className="field">
                    <span>Proposed replacement text</span>
                    <textarea
                      aria-label="Editorial proposed text"
                      rows={8}
                      value={proposedText}
                      onChange={(event) => setProposedText(event.target.value)}
                    />
                  </label>
                  <label className="field">
                    <span>Proposal rationale</span>
                    <textarea
                      aria-label="Editorial proposal rationale"
                      rows={4}
                      value={rationale}
                      onChange={(event) => setRationale(event.target.value)}
                    />
                  </label>
                  <button disabled={busy || selected.stale} onClick={() => void createProposal()}>
                    Create exact-base proposal
                  </button>
                </div>
              ) : (
                <p>This diagnostic finding is not a ManuscriptUnit text proposal target.</p>
              )}

              <label className="field">
                <span>Human decision reason</span>
                <textarea
                  aria-label="Editorial decision reason"
                  rows={3}
                  value={reason}
                  onChange={(event) => setReason(event.target.value)}
                />
              </label>
              <div className="actions">
                <button
                  className="primary"
                  disabled={busy || !proposal || proposal.status !== "OPEN" || proposal.stale}
                  onClick={() => void decide("accept")}
                >
                  Accept
                </button>
                <button
                  disabled={busy || !proposal || proposal.status !== "OPEN"}
                  onClick={() => void decide("reject")}
                >
                  Reject
                </button>
                <button
                  disabled={busy || !proposal || proposal.status !== "OPEN"}
                  onClick={() => void decide("request-revision")}
                >
                  Request revision
                </button>
                <button disabled={busy || selected.finding.status !== "OPEN"} onClick={() => void decide("waive")}>
                  Waive
                </button>
              </div>
            </>
          ) : (
            <p>Select an editorial finding.</p>
          )}
        </div>
      </div>

      {lastDecision && (
        <div className="alert" aria-label="Editorial decision result">
          <strong>
            {lastDecision.decision} · {lastDecision.finding.status}
          </strong>
          {lastDecision.accepted_revision_id && (
            <p>
              Current accepted revision <code>{lastDecision.accepted_revision_id}</code>
            </p>
          )}
        </div>
      )}
      {error && <p role="alert">{error}</p>}
    </section>
  );
}
