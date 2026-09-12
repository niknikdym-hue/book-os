import { useCallback, useEffect, useRef, useState } from "react";
import { coreApi } from "./api";
import type { DraftRunView, DraftingPanelProps } from "./draftingTypes";
import { openAIWorkLevelLabel, type OpenAIWorkLevel } from "./openaiWorkLevel";

type LaunchReadiness = {
  openai_credential_state: "AVAILABLE" | "NOT_AVAILABLE";
};

type WriterChoiceId = "AUTO" | "ASTRA_MEDIUM" | "ASTRA_HIGH" | "ASTRA_XHIGH" | "SOL";

type WriterChoice = {
  id: WriterChoiceId;
  label: string;
  model: string | null;
  effort: OpenAIWorkLevel | null;
  selectionMode: "AUTO" | "MANUAL";
};

const WRITER_CHOICES: readonly WriterChoice[] = [
  { id: "AUTO", label: "Автоматически", model: null, effort: null, selectionMode: "AUTO" },
  {
    id: "ASTRA_MEDIUM",
    label: "GPT-6 Astra Medium",
    model: "gpt-6-astra",
    effort: "medium",
    selectionMode: "MANUAL",
  },
  {
    id: "ASTRA_HIGH",
    label: "GPT-6 Astra High",
    model: "gpt-6-astra",
    effort: "high",
    selectionMode: "MANUAL",
  },
  {
    id: "ASTRA_XHIGH",
    label: "GPT-6 Astra Extra High",
    model: "gpt-6-astra",
    effort: "xhigh",
    selectionMode: "MANUAL",
  },
  {
    id: "SOL",
    label: "GPT-5.6 Sol",
    model: "gpt-5.6-sol",
    effort: null,
    selectionMode: "MANUAL",
  },
];

function choiceById(id: WriterChoiceId): WriterChoice {
  return WRITER_CHOICES.find((item) => item.id === id) ?? WRITER_CHOICES[2];
}

function resultModelLabel(run: DraftRunView) {
  if (run.model === "gpt-6-astra") {
    return `GPT-6 Astra ${openAIWorkLevelLabel(run.reasoning_effort)}`;
  }
  if (run.model === "gpt-5.6-sol") return "GPT-5.6 Sol";
  return run.model;
}

export function DraftingPanel({ project, chapter, api = coreApi }: DraftingPanelProps) {
  const [objective, setObjective] = useState("");
  const [context, setContext] = useState("");
  const [choiceId, setChoiceId] = useState<WriterChoiceId>("ASTRA_HIGH");
  const [maxCostUsd, setMaxCostUsd] = useState("0.50");
  const [allowPaid, setAllowPaid] = useState(false);
  const [runs, setRuns] = useState<DraftRunView[]>([]);
  const [readiness, setReadiness] = useState<LaunchReadiness | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const draftLoadSequence = useRef(0);

  const selectedChoice = choiceById(choiceId);
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
  const runNumber = runs.length || 1;
  const modelLabel = latest ? resultModelLabel(latest) : selectedChoice.label;

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
      const request: Record<string, unknown> = {
        section_objective: objective.trim(),
        provider: "openai",
        model: selectedChoice.model,
        selection_mode: selectedChoice.selectionMode,
        selection_scope: selectedChoice.selectionMode === "MANUAL" ? "OPERATION" : null,
        untrusted_context: context.trim() ? [context.trim()] : [],
        max_output_tokens: 3500,
        max_cost_usd: cost,
      };
      if (selectedChoice.effort) request.reasoning_effort = selectedChoice.effort;

      const run = await api<DraftRunView>(
        "POST",
        `/api/projects/${project.book_id}/chapters/${chapter.chapter_id}/drafts`,
        request,
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

  const runButton =
    selectedChoice.id === "SOL"
      ? "Запустить Sol"
      : selectedChoice.id === "AUTO"
        ? "Запустить автоматически"
        : "Запустить Astra";

  return (
    <section className="writer-studio drafting-panel" aria-label="Writer Studio">
      <header className="writer-studio-head">
        <div>
          <p className="writer-kicker"><span aria-hidden="true" /> AUTHOR STUDIO</p>
          <h3>{selectedChoice.label}</h3>
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
              <section
                className={`writer-work-state ${busy ? "working" : error ? "failed" : latest ? "complete" : "ready"}`}
                aria-live="polite"
                aria-label="Состояние работы модели"
              >
                <span className="writer-overline">СОСТОЯНИЕ РАБОТЫ МОДЕЛИ</span>
                {busy ? (
                  <><h4>{selectedChoice.id.startsWith("ASTRA") ? "Astra запущена · модель работает…" : "Модель работает…"}</h4><p>Сейчас выполняется: {objective.trim() || "задача готовится"}</p></>
                ) : error ? (
                  <><h4>Запуск не завершён</h4><p>{error}</p><small>Проверьте условия запуска и, если это безопасно, разрешите один новый запуск.</small></>
                ) : latest?.text ? (
                  <><h4>Готово ✓ · запуск №{runNumber}</h4><p>Модель: {modelLabel}</p><p className="writer-state-result">Что сделано: результат показан ниже и готов к копированию.</p></>
                ) : (
                  <><h4>Готово к запуску</h4><p>Выбрано: {modelLabel}. Опишите задачу, подтвердите один запуск — и кнопка станет зелёной.</p></>
                )}
              </section>
              <div className="writer-section-head">
                <div>
                  <span className="writer-overline">ЗАДАЧА ДЛЯ МОДЕЛИ</span>
                  <h4>Что сделать с книгой сейчас?</h4>
                </div>
                <span className="writer-chip">{selectedChoice.label}</span>
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
                      <h4>Что сделано</h4>
                    </div>
                    <button type="button" className="writer-copy" onClick={() => void copyLatest()}>
                      {copied ? "Скопировано" : "Копировать"}
                    </button>
                  </header>
                  <div className="writer-manuscript">{latest.text}</div>
                  <p className="writer-note">
                    {resultModelLabel(latest)}
                    {latest.revision_status ? ` · ${latest.revision_status}` : ""}
                  </p>
                </article>
              ) : (
                <div className="writer-result-empty">
                  <span aria-hidden="true">AI</span>
                  <div>
                    <strong>Результат появится здесь</strong>
                    <p>Сразу в книге — без терминала, логов и отдельного окна.</p>
                  </div>
                </div>
              )}
            </>
          )}
        </section>

        <aside className="writer-inspector" aria-label="Настройки Writer">
          <section>
            <span className="writer-overline">МОДЕЛЬ</span>
            <div className="writer-levels writer-astra-modes" role="group" aria-label="Модель Writer">
              {WRITER_CHOICES.map((choice) => (
                <button
                  key={choice.id}
                  type="button"
                  className={choiceId === choice.id ? "active" : ""}
                  aria-pressed={choiceId === choice.id}
                  disabled={busy}
                  onClick={() => {
                    setChoiceId(choice.id);
                    setAllowPaid(false);
                  }}
                >
                  {choice.label}
                </button>
              ))}
            </div>
            {selectedChoice.id === "AUTO" && (
              <p className="writer-note">
                BOOK OS выберет подходящую OpenAI-модель для операции. Фактическая модель сохранится с результатом.
              </p>
            )}
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
            <span>{busy ? "Модель работает…" : runButton}</span>
            <strong aria-hidden="true">→</strong>
          </button>

          {error && <div className="writer-error">{error}</div>}

          {runs.length > 0 && (
            <div className="writer-history">
              <span className="writer-overline">ПРЕДЫДУЩИЕ ЗАПУСКИ</span>
              <strong>{runs.length}</strong>
              <small>Последний результат — в центральном блоке.</small>
            </div>
          )}
        </aside>
      </div>
    </section>
  );
}
