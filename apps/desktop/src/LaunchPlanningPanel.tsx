import { useEffect, useState } from "react";
import { coreApi } from "./api";
import type { ChapterView, ProjectView } from "./types";

type LaunchReadiness = {
  openai_credential_state: "AVAILABLE" | "NOT_AVAILABLE";
  configured_model: string | null;
  anti_junk_entry_count: number;
  external_calls: number;
  paid_calls: number;
};

type PlanningProposal = {
  run_id: string;
  run_kind: string;
  provider: string;
  model: string;
  provider_run_id: string | null;
  prompt_id: string;
  prompt_version: string;
  prompt_hash: string;
  usage: Record<string, unknown>;
  status: string;
  project: ProjectView;
};

type Props = {
  project: ProjectView;
  chapter: ChapterView | null;
  onProject: (project: ProjectView) => void;
};

export function LaunchPlanningPanel({ project, chapter, onProject }: Props) {
  const [readiness, setReadiness] = useState<LaunchReadiness | null>(null);
  const [idea, setIdea] = useState("");
  const [readerHint, setReaderHint] = useState("");
  const [planningNote, setPlanningNote] = useState("");
  const [model, setModel] = useState("gpt-5.6-sol");
  const [maxCostUsd, setMaxCostUsd] = useState("0.50");
  const [allowPaid, setAllowPaid] = useState(false);
  const [latestRun, setLatestRun] = useState<PlanningProposal | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void coreApi<LaunchReadiness>("GET", "/api/launch/readiness")
      .then((value) => {
        setReadiness(value);
        if (value.configured_model) setModel(value.configured_model);
      })
      .catch((reason: unknown) => setError(String(reason)));
  }, []);

  const cost = Number(maxCostUsd);
  const paidReady =
    allowPaid && Number.isFinite(cost) && cost > 0 && model.trim().length > 0;
  const contractApproved =
    project.book_contract?.authority_status === "APPROVED" ||
    project.book_contract?.authority_status === "LOCKED";
  const architectureApproved =
    project.architecture?.authority_status === "APPROVED" ||
    project.architecture?.authority_status === "LOCKED";

  async function run(path: string, body: Record<string, unknown>) {
    setBusy(true);
    setError(null);
    try {
      const result = await coreApi<PlanningProposal>("POST", path, {
        ...body,
        provider: "openai",
        model: model.trim(),
        max_cost_usd: cost,
      });
      setLatestRun(result);
      onProject(result.project);
      setAllowPaid(false);
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel launch-planning-panel" aria-label="Старт книги">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">СТАРТ КНИГИ</p>
          <h3>BOOK OS Planner</h3>
        </div>
        <span className={`badge ${readiness?.openai_credential_state === "AVAILABLE" ? "approved" : "draft"}`}>
          {readiness?.openai_credential_state === "AVAILABLE"
            ? "OpenAI готов"
            : "OpenAI не настроен"}
        </span>
      </div>

      <p className="muted">
        Planner создаёт только черновые предложения. Book Contract, архитектура и контракты глав
        становятся authority только после вашего отдельного утверждения.
      </p>

      <div className="form-grid">
        <label className="field">
          <span>Модель</span>
          <input value={model} onChange={(event) => setModel(event.target.value)} />
          <small>Для первого качественного пилота: gpt-5.6-sol.</small>
        </label>
        <label className="field">
          <span>Максимальная стоимость одного запроса, USD</span>
          <input
            inputMode="decimal"
            value={maxCostUsd}
            onChange={(event) => setMaxCostUsd(event.target.value)}
          />
        </label>
      </div>
      <label className="paid-approval">
        <input
          type="checkbox"
          checked={allowPaid}
          onChange={(event) => setAllowPaid(event.target.checked)}
        />
        <span>
          Разрешаю следующий платный OpenAI-запрос с указанным пределом. После запроса разрешение
          автоматически сбросится.
        </span>
      </label>

      {!contractApproved && (
        <div className="planning-step">
          <h4>1. Определение книги и Book Contract</h4>
          <div className="form-grid">
            <label className="field">
              <span>Идея книги</span>
              <textarea
                rows={4}
                value={idea}
                onChange={(event) => setIdea(event.target.value)}
                placeholder="Коротко: какую проблему или механизм должна исследовать книга?"
              />
            </label>
            <label className="field">
              <span>Кому книга — если уже понятно</span>
              <textarea
                rows={4}
                value={readerHint}
                onChange={(event) => setReaderHint(event.target.value)}
                placeholder="Можно оставить пустым: Planner предложит читателя сам."
              />
            </label>
          </div>
          <div className="actions">
            <button
              className="primary"
              disabled={busy || !paidReady || idea.trim().length < 3}
              onClick={() =>
                void run(`/api/projects/${project.book_id}/planning/book-contract`, {
                  idea: idea.trim(),
                  reader_hint: readerHint.trim(),
                  max_output_tokens: 2600,
                })
              }
            >
              {busy ? "Planner работает…" : "Предложить Book Contract"}
            </button>
          </div>
        </div>
      )}

      {contractApproved && !architectureApproved && (
        <div className="planning-step">
          <h4>2. Архитектура книги</h4>
          <label className="field">
            <span>Дополнительное указание Planner — необязательно</span>
            <textarea
              rows={3}
              value={planningNote}
              onChange={(event) => setPlanningNote(event.target.value)}
              placeholder="Например: не делать главы одинакового размера ради симметрии."
            />
          </label>
          <div className="actions">
            <button
              className="primary"
              disabled={busy || !paidReady}
              onClick={() =>
                void run(`/api/projects/${project.book_id}/planning/architecture`, {
                  planning_note: planningNote.trim(),
                  max_output_tokens: 5000,
                })
              }
            >
              {busy ? "Planner работает…" : "Предложить архитектуру"}
            </button>
          </div>
        </div>
      )}

      {architectureApproved && chapter && (
        <div className="planning-step">
          <h4>3. Контракт выбранной главы</h4>
          <p className="muted">
            Глава {chapter.ordinal}: {chapter.working_title}
          </p>
          <div className="actions">
            <button
              className="primary"
              disabled={busy || !paidReady}
              onClick={() =>
                void run(
                  `/api/projects/${project.book_id}/chapters/${chapter.chapter_id}/planning/contract`,
                  { planning_note: planningNote.trim(), max_output_tokens: 3200 },
                )
              }
            >
              {busy ? "Planner работает…" : "Предложить контракт главы"}
            </button>
          </div>
        </div>
      )}

      {latestRun && (
        <div className="planning-run">
          <strong>Черновик создан</strong>
          <span>{latestRun.run_kind} · {latestRun.model}</span>
          <small>Run ID: {latestRun.run_id}</small>
        </div>
      )}
      {readiness && (
        <small className="muted">
          Словарь мусора: {readiness.anti_junk_entry_count} записей · preflight внешних вызовов: {readiness.external_calls}
        </small>
      )}
      {error && <div className="alert inline-alert">{error}</div>}
    </section>
  );
}
