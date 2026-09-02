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
  const [apiKey, setApiKey] = useState("");
  const [idea, setIdea] = useState("");
  const [readerHint, setReaderHint] = useState("");
  const [planningNote, setPlanningNote] = useState("");
  const [model, setModel] = useState("gpt-5.6-sol");
  const [maxCostUsd, setMaxCostUsd] = useState("0.50");
  const [allowPaid, setAllowPaid] = useState(false);
  const [latestRun, setLatestRun] = useState<PlanningProposal | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function reloadReadiness() {
    const value = await coreApi<LaunchReadiness>("GET", "/api/launch/readiness");
    setReadiness(value);
    if (value.configured_model) setModel(value.configured_model);
  }

  useEffect(() => {
    void reloadReadiness().catch((reason: unknown) => setError(String(reason)));
  }, []);

  const cost = Number(maxCostUsd);
  const paidReady =
    readiness?.openai_credential_state === "AVAILABLE" &&
    allowPaid &&
    Number.isFinite(cost) &&
    cost > 0 &&
    model.trim().length > 0;
  const contractApproved =
    project.book_contract?.authority_status === "APPROVED" ||
    project.book_contract?.authority_status === "LOCKED";
  const architectureApproved =
    project.architecture?.authority_status === "APPROVED" ||
    project.architecture?.authority_status === "LOCKED";

  async function saveKey() {
    if (!apiKey.trim()) return;
    setBusy(true);
    setError(null);
    try {
      await coreApi("POST", "/api/launch/openai-key", { api_key: apiKey.trim() });
      setApiKey("");
      await reloadReadiness();
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

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
      setAllowPaid(false);
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel launch-planning-panel" aria-label="Идея и план книги">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">ТЕКУЩИЙ РАБОЧИЙ ШАГ</p>
          <h3>Идея и план книги</h3>
        </div>
        <span className={`badge ${readiness?.openai_credential_state === "AVAILABLE" ? "approved" : "draft"}`}>
          {readiness?.openai_credential_state === "AVAILABLE"
            ? "OpenAI готов"
            : "Нужен ключ OpenAI"}
        </span>
      </div>

      <p className="muted">
        BOOK OS создаёт только предложение. Контракт книги, архитектура и контракты глав становятся
        авторитетными только после вашего отдельного утверждения.
      </p>

      {readiness?.openai_credential_state === "NOT_AVAILABLE" && (
        <div className="credential-setup">
          <label className="field">
            <span>Ключ OpenAI API</span>
            <small>Сохраняется только в macOS Keychain и не показывается после сохранения.</small>
            <input
              type="password"
              autoComplete="off"
              value={apiKey}
              onChange={(event) => setApiKey(event.target.value)}
              placeholder="Вставьте API key"
            />
          </label>
          <button className="primary" disabled={busy || apiKey.trim().length < 10} onClick={() => void saveKey()}>
            Сохранить в Keychain
          </button>
        </div>
      )}

      {!contractApproved && (
        <div className="planning-step primary-planning-step">
          <h4>Опишите идею книги</h4>
          <p className="muted">
            Не нужно писать промпт. Достаточно точно объяснить, какую проблему, механизм или вопрос
            должна раскрыть книга.
          </p>
          <div className="form-grid">
            <label className="field">
              <span>Идея книги</span>
              <textarea
                rows={5}
                value={idea}
                onChange={(event) => setIdea(event.target.value)}
                placeholder="Например: почему растущая компания начинает зависеть от личного контроля основателя и как перенести качество решений из его головы в систему управления."
              />
            </label>
            <label className="field">
              <span>Кому эта книга — если уже понятно</span>
              <textarea
                rows={5}
                value={readerHint}
                onChange={(event) => setReaderHint(event.target.value)}
                placeholder="Можно оставить пустым — BOOK OS предложит читателя сам."
              />
            </label>
          </div>
        </div>
      )}

      {contractApproved && !architectureApproved && (
        <div className="planning-step primary-planning-step">
          <h4>Подготовьте предложение архитектуры</h4>
          <p className="muted">
            Контракт уже утверждён. Можно дать BOOK OS дополнительное указание — или оставить поле
            пустым и получить структуру строго из контракта.
          </p>
          <label className="field">
            <span>Дополнительное указание — необязательно</span>
            <textarea
              rows={3}
              value={planningNote}
              onChange={(event) => setPlanningNote(event.target.value)}
              placeholder="Например: не делать главы одинакового размера ради симметрии."
            />
          </label>
        </div>
      )}

      {architectureApproved && chapter && (
        <div className="planning-step primary-planning-step">
          <h4>Подготовьте контракт выбранной главы</h4>
          <p className="muted">
            Глава {chapter.ordinal}: {chapter.working_title}. BOOK OS предложит функцию, обязательные
            мысли, исследования, сцены и ограничения этой главы.
          </p>
        </div>
      )}

      <details className="advanced-settings planning-settings">
        <summary>Дополнительные настройки OpenAI</summary>
        <div className="form-grid planning-settings-grid">
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
      </details>

      <label className="paid-approval">
        <input
          type="checkbox"
          checked={allowPaid}
          onChange={(event) => setAllowPaid(event.target.checked)}
        />
        <span>
          Разрешаю <strong>только следующий</strong> платный OpenAI-запрос. Текущий предел — ${maxCostUsd || "0"}.
          После любой попытки разрешение автоматически сбросится.
        </span>
      </label>

      <div className="actions planning-action">
        {!contractApproved && (
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
            {busy ? "BOOK OS работает…" : "Предложить контракт книги"}
          </button>
        )}

        {contractApproved && !architectureApproved && (
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
            {busy ? "BOOK OS работает…" : "Предложить архитектуру"}
          </button>
        )}

        {architectureApproved && chapter && (
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
            {busy ? "BOOK OS работает…" : "Предложить контракт главы"}
          </button>
        )}
      </div>

      {latestRun && (
        <div className="planning-run">
          <strong>Черновик создан — теперь его нужно проверить</strong>
          <span>{latestRun.model}</span>
          <small>Технический Run ID: {latestRun.run_id}</small>
        </div>
      )}
      {readiness && (
        <small className="muted">
          Словарь мусора: {readiness.anti_junk_entry_count} записей · внешних вызовов при проверке готовности: {readiness.external_calls}
        </small>
      )}
      {error && <div className="alert inline-alert">{error}</div>}
    </section>
  );
}
