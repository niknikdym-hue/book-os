import { useCallback, useEffect, useMemo, useState } from "react";
import { coreApi } from "./api";
import { uiLabel } from "./uiLabels";
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
  { value: "ALL", label: "Все роли" },
  { value: "DEVELOPMENTAL_EDITOR", label: "Структурный редактор" },
  { value: "CROSS_BOOK_AUDITOR", label: "Редактор целой книги" },
  { value: "FACT_CHECKER", label: "Фактчекер" },
  { value: "LITERARY_EDITOR", label: "Литературный редактор" },
  { value: "STYLE_GUARDIAN", label: "Контроль авторского голоса" },
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

const statusLabels: Record<string, string> = {
  ALL: "Все", OPEN: "Открыто", RESOLVED: "Исправлено", WAIVED: "Оставлено как есть", SUPERSEDED: "Заменено",
};
const severityLabels: Record<string, string> = {
  ALL: "Любая", CRITICAL: "Критично", MAJOR: "Важно", MINOR: "Небольшое", INFO: "Справка",
};

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
      if (kind === "developmental" && !chapter) throw new Error("Сначала выберите главу.");
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
      setError("Текстовые предложения M6 разрешены только для конкретных фрагментов рукописи.");
      return;
    }
    if (!proposedText.trim() || !rationale.trim()) {
      setError("Нужны новый текст и обоснование правки.");
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
      setError("Укажите причину человеческого решения.");
      return;
    }
    const proposal = selected.latest_proposal;
    if (action !== "waive" && !proposal) {
      setError("Сначала выберите замечание с открытым предложением правки.");
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
          <p className="eyebrow">РЕДАКТУРА КНИГИ</p>
          <h3>Проверить книгу</h3>
          <p>Запустите проверку, затем посмотрите замечания и выберите, как с каждым поступить.</p>
        </div>
        <strong>{items.length} замечаний</strong>
      </div>

      <div className="actions">
        <button disabled={busy || !chapter} onClick={() => void runAudit("developmental")}>
          Проверить текущую главу
        </button>
        <button disabled={busy} onClick={() => void runAudit("cross-book")}>
          Проверить всю книгу
        </button>
        <button disabled={busy} onClick={() => void runAudit("fact-check")}>
          Проверить факты
        </button>
      </div>
      {busy && <p aria-live="polite"><strong>Проверяю…</strong></p>}
      {lastRun && <p aria-live="polite"><strong>Проверка завершена · {lastRun.findings.length ? `найдено ${lastRun.findings.length} замечаний` : "существенных замечаний нет"}</strong></p>}

      {items.length > 0 && <details className="editorial-filters">
        <summary>Фильтры</summary>
      <div className="form-grid">
        <label className="field">
          <span>Роль</span>
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
          <span>Статус</span>
          <select
            aria-label="Editorial status filter"
            value={status}
            onChange={(event) => setStatus(event.target.value as "ALL" | FindingStatus)}
          >
            {statuses.map((value) => (
              <option key={value} value={value}>
                {statusLabels[value]}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>Серьёзность</span>
          <select
            aria-label="Editorial severity filter"
            value={severity}
            onChange={(event) => setSeverity(event.target.value as "ALL" | FindingSeverity)}
          >
            {severities.map((value) => (
              <option key={value} value={value}>
                {severityLabels[value]}
              </option>
            ))}
          </select>
        </label>
      </div>
      </details>}

      <div className="two-columns">
        <div>
          <h4>Замечания</h4>
          {items.length === 0 ? (
            <p>По этому фильтру замечаний нет.</p>
          ) : (
            items.map((item) => (
              <button
                className={`project-link ${selectedFindingId === item.finding.finding_id ? "active" : ""}`}
                key={item.finding.finding_id}
                onClick={() => setSelectedFindingId(item.finding.finding_id)}
              >
                <strong>
                  {uiLabel(item.finding.severity)} · {uiLabel(item.finding.role)}
                </strong>
                <span>{item.finding.category}</span>
                <small>{item.stale ? "УСТАРЕЛО" : uiLabel(item.finding.status)}</small>
              </button>
            ))
          )}
        </div>

        <div>
          {selected ? (
            <>
              <div className="subheading">
                <strong>{selected.finding.category}</strong>
                <strong>{uiLabel(baselineState)}</strong>
              </div>
              <p>{selected.finding.diagnosis}</p>
              <p>
                <strong>Почему:</strong> {selected.finding.why}
              </p>
              <p><strong>Насколько это важно:</strong> {severityLabels[selected.finding.severity] ?? selected.finding.severity}</p>
              {selected.finding.expected_effect && (
                <p>
                  <strong>Что изменится после исправления:</strong> {selected.finding.expected_effect}
                </p>
              )}
              {selected.finding.risks && (
                <p>
                  <strong>Риск у правки:</strong> {selected.finding.risks}
                </p>
              )}

              {proposal ? (
                <div>
                  <div className="subheading">
                    <strong>Предложенный вариант текста</strong>
                  </div>
                  <pre aria-label="Editorial proposal diff">{proposal.diff}</pre>
                </div>
              ) : selected.finding.target_kind === "MANUSCRIPT_UNIT" ? (
                <div className="form-grid">
                  <label className="field">
                    <span>Предлагаемый вариант текста</span>
                    <textarea
                      aria-label="Editorial proposed text"
                      rows={8}
                      value={proposedText}
                      onChange={(event) => setProposedText(event.target.value)}
                    />
                  </label>
                  <label className="field">
                    <span>Почему эта правка поможет</span>
                    <textarea
                      aria-label="Editorial proposal rationale"
                      rows={4}
                      value={rationale}
                      onChange={(event) => setRationale(event.target.value)}
                    />
                  </label>
                  <button disabled={busy || selected.stale} onClick={() => void createProposal()}>
                    Подготовить вариант правки
                  </button>
                </div>
              ) : (
                <p>Это замечание относится к книге в целом и не требует замены конкретного фрагмента.</p>
              )}

              <label className="field">
                <span>Почему вы приняли это решение?</span>
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
                  Принять правку
                </button>
                <button
                  disabled={busy || !proposal || proposal.status !== "OPEN"}
                  onClick={() => void decide("reject")}
                >
                  Отклонить
                </button>
                <button
                  disabled={busy || !proposal || proposal.status !== "OPEN"}
                  onClick={() => void decide("request-revision")}
                >
                  Попросить доработать
                </button>
                <button disabled={busy || selected.finding.status !== "OPEN"} onClick={() => void decide("waive")}>
                  Оставить как есть
                </button>
              </div>
            </>
          ) : (
            <p>Выберите редакторское замечание.</p>
          )}
        </div>
      </div>

      {lastDecision && (
        <div className="alert" aria-label="Editorial decision result">
          <strong>
            Решение сохранено · {statusLabels[lastDecision.finding.status] ?? lastDecision.finding.status}
          </strong>
          {lastDecision.accepted_revision_id && (
            <p>
              Правка принята в рукопись.
            </p>
          )}
        </div>
      )}
      {error && <p role="alert">{error}</p>}
    </section>
  );
}
