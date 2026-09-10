import { useCallback, useEffect, useRef, useState } from "react";
import { coreApi } from "./api";
import type { DraftRunView, DraftingPanelProps } from "./draftingTypes";
import {
  openAIWorkLevelLabel,
  setPendingOpenAIWorkLevel,
  type OpenAIWorkLevel,
} from "./openaiWorkLevel";

type LaunchReadiness = {
  openai_credential_state: "AVAILABLE" | "NOT_AVAILABLE";
};

type AstraMode = {
  effort: OpenAIWorkLevel;
  label: string;
};

const ASTRA_MODES: readonly AstraMode[] = [
  { effort: "medium", label: "GPT-6 Astra Medium" },
  { effort: "high", label: "GPT-6 Astra High" },
  { effort: "xhigh", label: "GPT-6 Astra Extra High" },
];

function modeLabel(effort: OpenAIWorkLevel) {
  return ASTRA_MODES.find((item) => item.effort === effort)?.label ?? "GPT-6 Astra";
}

function optional(value: string | null | undefined) {
  return value && value.trim() ? value : "—";
}

export function DraftingPanel({ project, chapter, api = coreApi }: DraftingPanelProps) {
  const [objective, setObjective] = useState("");
  const [context, setContext] = useState("");
  const [workLevel, setWorkLevel] = useState<OpenAIWorkLevel>("high");
  const [maxCostUsd, setMaxCostUsd] = useState("0.50");
  const [allowPaid, setAllowPaid] = useState(false);
  const [runs, setRuns] = useState<DraftRunView[]>([]);
  const [readiness, setReadiness] = useState<LaunchReadiness | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const draftLoadSequence = useRef(0);

  const approved =
    chapter?.chapter_contract?.authority_status === "APPROVED" ||
    chapter?.chapter_contract?.authority_status === "LOCKED";
  const credentialAvailable = readiness?.openai_credential_state === "AVAILABLE";
  const cost = Number(maxCostUsd);
  const canRun =
    Boolean(chapter) &&
    approved &&
    credentialAvailable &&
    objective.trim().length > 0 &&
    allowPaid &&
    Number.isFinite(cost) &&
    cost > 0 &&
    !busy;
  const latest = runs[0] ?? null;
  const selectedModeLabel = modeLabel(workLevel);

  const reloadReadiness = useCallback(async () => {
    setReadiness(await api<LaunchReadiness>("GET", "/api/launch/readiness"));
  }, [api]);

  const reloadDrafts = useCallback(async () => {
    const loadId = ++draftLoadSequence.current;
    setRuns([]);
    setCopied(false);
    if (!chapter) return;
    const value = await api<DraftRunView[]>(
      "GET",
      `/api/projects/${project.book_id}/chapters/${chapter.chapter_id}/drafts`,
    );
    if (loadId === draftLoadSequence.current) setRuns(value);
  }, [api, chapter, project.book_id]);

  useEffect(() => {
    let active = true;
    setError(null);
    void Promise.all([reloadReadiness(), reloadDrafts()]).catch((reason: unknown) => {
      if (active) setError(String(reason));
    });
    return () => {
      active = false;
    };
  }, [reloadDrafts, reloadReadiness]);

  async function generate() {
    if (!chapter || !canRun) return;
    setBusy(true);
    setError(null);
    setCopied(false);
    try {
      setPendingOpenAIWorkLevel(workLevel);
      const run = await api<DraftRunView>(
        "POST",
        `/api/projects/${project.book_id}/chapters/${chapter.chapter_id}/drafts`,
        {
          section_objective: objective.trim(),
          provider: "openai",
          model: "gpt-6-astra",
          selection_mode: "MANUAL",
          selection_scope: "OPERATION",
          reasoning_effort: workLevel,
          untrusted_context: context.trim() ? [context.trim()] : [],
          max_output_tokens: 3500,
          max_cost_usd: cost,
        },
      );
      setRuns((current) => [run, ...current]);
      setAllowPaid(false);
    } catch (reason) {
      setAllowPaid(false);
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  async function copyLatest() {
    if (!latest?.text) return;
    try {
      await navigator.clipboard.writeText(latest.text);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1400);
    } catch {
      setCopied(false);
    }
  }

  return (
    <section className="writer-studio drafting-panel" aria-label="Writer Studio">
      <header className="writer-studio-head">
        <div>
          <p className="writer-kicker"><span aria-hidden="true" /> AUTHOR STUDIO</p>
          <h3>{selectedModeLabel}</h3>
          <p className="writer-chapter">
            {chapter ? `${chapter.ordinal}. ${chapter.working_title}` : "Выберите главу для работы"}
          </p>
        </div>
        <div className={`writer-status ${credentialAvailable ? "ready" : "missing"}`}>
          <span aria-hidden="true" />
          {credentialAvailable ? "OpenAI API подключён" : "OpenAI не подключён"}
        </div>
      </header>

      <div className="writer-layout">
        <section className="writer-canvas">
          {!chapter && (
            <div className="writer-empty">
              <strong>Сначала выберите главу</strong>
              <p>Рабочая область Writer откроется для конкретной главы.</p>
            </div>
          )}
          {chapter && !approved && (
            <div className="writer-empty">
              <strong>Нужен утверждённый контракт главы</strong>
              <p>Это защищает книгу от написания вне утверждённой архитектуры.</p>
            </div>
          )}

          {chapter && approved && (
            <>
              <div className="writer-section-head">
                <div>
                  <span className="writer-overline">ЗАДАЧА ДЛЯ МОДЕЛИ</span>
                  <h4>Что сделать с книгой сейчас?</h4>
                </div>
                <span className="writer-chip">{selectedModeLabel}</span>
              </div>

              <label className="writer-prompt-label">
                <span className="sr-only">Задача этого фрагмента</span>
                <textarea
                  aria-label="Задача этого фрагмента"
                  className="writer-prompt"
                  rows={7}
                  value={objective}
                  onChange={(event) => setObjective(event.target.value)}
                  placeholder="Например: напиши сильное открытие главы, объясни механизм без банальностей, сохрани голос автора и не повторяй предыдущие главы…"
                />
              </label>

              <details className="writer-context-drawer">
                <summary>Добавить исходный материал или уточнение</summary>
                <textarea
                  rows={5}
                  value={context}
                  onChange={(event) => setContext(event.target.value)}
                  placeholder="Заметки, факты, исходный фрагмент или дополнительное ограничение для этой операции"
                />
              </details>

              {latest?.text ? (
                <article className="writer-result">
                  <header>
                    <div>
                      <span className="writer-overline">ПОСЛЕДНИЙ РЕЗУЛЬТАТ</span>
                      <h4>Черновик готов</h4>
                    </div>
                    <button type="button" className="writer-copy" onClick={() => void copyLatest()}>
                      {copied ? "Скопировано" : "Копировать"}
                    </button>
                  </header>
                  <div className="writer-manuscript">{latest.text}</div>
                  <p className="writer-note">
                    {latest.model === "gpt-6-astra"
                      ? `GPT-6 Astra ${openAIWorkLevelLabel(latest.reasoning_effort)}`
                      : latest.model}
                    {latest.revision_status ? ` · ${latest.revision_status}` : ""}
                  </p>
                </article>
              ) : (
                <div className="writer-result-empty">
                  <span aria-hidden="true">A</span>
                  <div>
                    <strong>Результат Astra появится здесь</strong>
                    <p>Сразу в книге — без терминала, логов и отдельного окна.</p>
                  </div>
                </div>
              )}
            </>
          )}
        </section>

        <aside className="writer-inspector" aria-label="Настройки Writer">
          <section>
            <span className="writer-overline">РЕЖИМ ASTRA</span>
            <div className="writer-levels writer-astra-modes" role="group" aria-label="Режим Astra">
              {ASTRA_MODES.map((mode) => (
                <button
                  key={mode.effort}
                  type="button"
                  className={workLevel === mode.effort ? "active" : ""}
                  aria-pressed={workLevel === mode.effort}
                  disabled={busy}
                  onClick={() => {
                    setWorkLevel(mode.effort);
                    setAllowPaid(false);
                  }}
                >
                  {mode.label}
                </button>
              ))}
            </div>
          </section>

          {!credentialAvailable && (
            <section className="writer-key-section">
              <span className="writer-overline">OPENAI НЕ ПОДКЛЮЧЁН</span>
              <p className="writer-note">Подключение ключа вынесено в «Настройки / Advanced» вне рабочей панели.</p>
            </section>
          )}

          <section>
            <span className="writer-overline">ЛИМИТ ЗАПРОСА</span>
            <label className="writer-cost">
              <span>$</span>
              <input
                aria-label="Максимальная стоимость запроса, USD"
                inputMode="decimal"
                value={maxCostUsd}
                onChange={(event) => {
                  setMaxCostUsd(event.target.value);
                  setAllowPaid(false);
                }}
              />
              <small>максимум</small>
            </label>
          </section>

          <label className="writer-approval">
            <input
              type="checkbox"
              checked={allowPaid}
              disabled={!credentialAvailable || !approved}
              onChange={(event) => setAllowPaid(event.target.checked)}
            />
            <span>Разрешаю один следующий платный вызов с лимитом ${maxCostUsd || "0"}.</span>
          </label>

          <button type="button" className="writer-run" disabled={!canRun} onClick={() => void generate()}>
            <span>{busy ? "Astra работает…" : "Запустить Astra"}</span>
            <strong aria-hidden="true">→</strong>
          </button>

          {error && <div className="writer-error">{error}</div>}

          {runs.length > 0 && (
            <div className="writer-history">
              <span className="writer-overline">ИСТОРИЯ ГЛАВЫ</span>
              <strong>{runs.length} запусков</strong>
              <small>Последний результат показан в центре.</small>
            </div>
          )}
        </aside>
      </div>

      {latest && (
        <details className="utility-drawer writer-technical-provenance" aria-label="Технические данные запуска">
          <summary>Настройки / Advanced · технические данные запуска</summary>
          <div className="panel">
            <p className="muted">
              Эти данные нужны для аудита воспроизводимости и не являются частью обычной авторской панели.
            </p>
            <dl className="writer-provenance">
              <div><dt>Модель</dt><dd>{latest.model}</dd></div>
              <div><dt>Уровень</dt><dd>{openAIWorkLevelLabel(latest.reasoning_effort)}</dd></div>
              <div><dt>Provider</dt><dd>{latest.provider}</dd></div>
              <div><dt>Selection</dt><dd>{latest.selection_mode} · {optional(latest.selection_scope)}</dd></div>
              <div><dt>Routing</dt><dd>{optional(latest.routing_rationale)}</dd></div>
              <div><dt>Run ID</dt><dd>{latest.run_id}</dd></div>
              <div><dt>Task ID</dt><dd>{latest.task_id}</dd></div>
              <div><dt>Prompt</dt><dd>{latest.prompt_id} · v{latest.prompt_version}</dd></div>
              <div><dt>Prompt hash</dt><dd>{latest.prompt_hash}</dd></div>
              <div><dt>Input revision</dt><dd>{latest.input_revision_id}</dd></div>
              <div><dt>Input hash</dt><dd>{latest.input_revision_hash}</dd></div>
              <div><dt>Output revision</dt><dd>{optional(latest.revision_id)}</dd></div>
              <div><dt>Output hash</dt><dd>{optional(latest.revision_hash)}</dd></div>
              <div><dt>Provider run</dt><dd>{optional(latest.provider_run_id)}</dd></div>
              <div><dt>Статус</dt><dd>{latest.revision_status ?? latest.run_status}</dd></div>
              <div><dt>Notes</dt><dd>{latest.notes.length ? latest.notes.join(" · ") : "—"}</dd></div>
              <div><dt>Usage</dt><dd><code>{JSON.stringify(latest.usage)}</code></dd></div>
            </dl>
          </div>
        </details>
      )}
    </section>
  );
}
