import { useCallback, useEffect, useMemo, useState } from "react";
import { coreApi } from "./api";
import type { DraftRunView } from "./draftingTypes";
import {
  OPENAI_WORK_LEVEL_OPTIONS,
  openAIWorkLevelLabel,
  setPendingOpenAIWorkLevel,
  type OpenAIWorkLevel,
} from "./openaiWorkLevel";
import type { ChapterView, ProjectView } from "./types";

type LaunchReadiness = {
  openai_credential_state: "AVAILABLE" | "NOT_AVAILABLE";
};

type Props = {
  project: ProjectView;
  chapter: ChapterView | null;
};

export function AstraStudio({ project, chapter }: Props) {
  const [readiness, setReadiness] = useState<LaunchReadiness | null>(null);
  const [apiKey, setApiKey] = useState("");
  const [objective, setObjective] = useState("");
  const [context, setContext] = useState("");
  const [workLevel, setWorkLevel] = useState<OpenAIWorkLevel>("high");
  const [maxCostUsd, setMaxCostUsd] = useState("0.50");
  const [allowPaid, setAllowPaid] = useState(false);
  const [runs, setRuns] = useState<DraftRunView[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const approved =
    chapter?.chapter_contract?.authority_status === "APPROVED" ||
    chapter?.chapter_contract?.authority_status === "LOCKED";
  const keyReady = readiness?.openai_credential_state === "AVAILABLE";
  const cost = Number(maxCostUsd);
  const canRun =
    Boolean(chapter) &&
    approved &&
    keyReady &&
    objective.trim().length > 0 &&
    allowPaid &&
    Number.isFinite(cost) &&
    cost > 0 &&
    !busy;
  const latest = runs[0] ?? null;

  const chapterLabel = useMemo(
    () => (chapter ? `${chapter.ordinal}. ${chapter.working_title}` : "Глава не выбрана"),
    [chapter],
  );

  const reloadReadiness = useCallback(async () => {
    setReadiness(await coreApi<LaunchReadiness>("GET", "/api/launch/readiness"));
  }, []);

  const reloadDrafts = useCallback(async () => {
    if (!chapter) {
      setRuns([]);
      return;
    }
    setRuns(
      await coreApi<DraftRunView[]>(
        "GET",
        `/api/projects/${project.book_id}/chapters/${chapter.chapter_id}/drafts`,
      ),
    );
  }, [chapter, project.book_id]);

  useEffect(() => {
    setError(null);
    void Promise.all([reloadReadiness(), reloadDrafts()]).catch((reason: unknown) =>
      setError(String(reason)),
    );
  }, [reloadDrafts, reloadReadiness]);

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

  async function generate() {
    if (!chapter || !canRun) return;
    setBusy(true);
    setError(null);
    setCopied(false);
    try {
      setPendingOpenAIWorkLevel(workLevel);
      const run = await coreApi<DraftRunView>(
        "POST",
        `/api/projects/${project.book_id}/chapters/${chapter.chapter_id}/drafts`,
        {
          section_objective: objective.trim(),
          provider: "openai",
          model: "gpt-6-astra",
          selection_mode: "MANUAL",
          selection_scope: "OPERATION",
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
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      setCopied(false);
    }
  }

  return (
    <section className="astra-studio" aria-label="Astra Author Studio">
      <header className="astra-studio-header">
        <div>
          <div className="astra-kicker">
            <span className="astra-orb" aria-hidden="true" />
            OPENAI · AUTHOR STUDIO
          </div>
          <h3>Пишите книгу с GPT-6 Astra</h3>
          <p>{chapterLabel}</p>
        </div>
        <div className={`astra-connection ${keyReady ? "ready" : "missing"}`}>
          <span aria-hidden="true" />
          {keyReady ? "OpenAI API подключён" : "Нужен OpenAI API key"}
        </div>
      </header>

      <div className="astra-studio-grid">
        <section className="astra-canvas">
          <div className="astra-canvas-heading">
            <div>
              <span className="astra-overline">ЗАДАЧА</span>
              <h4>Что Astra должна сделать сейчас?</h4>
            </div>
            <span className="astra-model-chip">GPT-6 Astra</span>
          </div>

          {!chapter && (
            <div className="astra-empty-state">
              <strong>Выберите главу</strong>
              <span>Для работы Writer нужна конкретная глава.</span>
            </div>
          )}
          {chapter && !approved && (
            <div className="astra-empty-state">
              <strong>Сначала утвердите контракт главы</strong>
              <span>BOOK OS не позволяет Astra писать вне утверждённых границ главы.</span>
            </div>
          )}

          {chapter && approved && (
            <>
              <textarea
                className="astra-prompt"
                rows={7}
                value={objective}
                onChange={(event) => setObjective(event.target.value)}
                placeholder="Например: напиши сильное открытие главы, объясни механизм без банальностей и не повторяй предыдущие главы…"
              />

              <details className="astra-context">
                <summary>Добавить материал или уточнение</summary>
                <textarea
                  rows={5}
                  value={context}
                  onChange={(event) => setContext(event.target.value)}
                  placeholder="Факты, заметки, исходный фрагмент или дополнительное ограничение для этой операции"
                />
              </details>

              {latest?.text ? (
                <article className="astra-output">
                  <div className="astra-output-head">
                    <div>
                      <span className="astra-overline">РЕЗУЛЬТАТ ASTRA</span>
                      <h4>Черновик готов к вашей работе</h4>
                    </div>
                    <button type="button" className="astra-text-action" onClick={() => void copyLatest()}>
                      {copied ? "Скопировано" : "Копировать"}
                    </button>
                  </div>
                  <div className="astra-manuscript">{latest.text}</div>
                  <details className="astra-provenance">
                    <summary>Технические данные запуска</summary>
                    <dl>
                      <div><dt>Модель</dt><dd>{latest.model}</dd></div>
                      <div><dt>Уровень</dt><dd>{openAIWorkLevelLabel(latest.reasoning_effort)}</dd></div>
                      <div><dt>Статус</dt><dd>{latest.revision_status ?? latest.run_status}</dd></div>
                      <div><dt>Revision</dt><dd>{latest.revision_id ?? "—"}</dd></div>
                    </dl>
                  </details>
                </article>
              ) : (
                <div className="astra-output-placeholder">
                  <span className="astra-output-mark" aria-hidden="true">A</span>
                  <div>
                    <strong>Результат появится здесь</strong>
                    <p>Не в логах и не в отдельном окне — прямо в рабочем пространстве книги.</p>
                  </div>
                </div>
              )}
            </>
          )}
        </section>

        <aside className="astra-inspector" aria-label="Настройки Astra">
          <div className="astra-inspector-block">
            <span className="astra-overline">МОДЕЛЬ</span>
            <div className="astra-model-card">
              <span className="astra-orb large" aria-hidden="true" />
              <div>
                <strong>GPT-6 Astra</strong>
                <small>OpenAI API · Writer</small>
              </div>
            </div>
          </div>

          <div className="astra-inspector-block">
            <span className="astra-overline">ГЛУБИНА РАБОТЫ</span>
            <div className="astra-level-switch" role="group" aria-label="Уровень работы Astra">
              {OPENAI_WORK_LEVEL_OPTIONS.map((option) => (
                <button
                  type="button"
                  key={option.value}
                  aria-pressed={workLevel === option.value}
                  className={workLevel === option.value ? "active" : ""}
                  onClick={() => {
                    setWorkLevel(option.value);
                    setAllowPaid(false);
                  }}
                >
                  {option.label}
                </button>
              ))}
            </div>
            <p className="astra-help">
              Для основной работы над книгой — High. Extra High оставляйте для самых сложных редакторских задач.
            </p>
          </div>

          {!keyReady && (
            <div className="astra-inspector-block astra-key-block">
              <span className="astra-overline">OPENAI API</span>
              <label>
                <span>API key</span>
                <input
                  type="password"
                  value={apiKey}
                  onChange={(event) => setApiKey(event.target.value)}
                  placeholder="sk-…"
                  autoComplete="off"
                />
              </label>
              <button type="button" className="astra-secondary" disabled={busy || !apiKey.trim()} onClick={() => void saveKey()}>
                Сохранить в macOS Keychain
              </button>
              <small>Ключ хранится локально в Keychain и не записывается в проект книги.</small>
            </div>
          )}

          <div className="astra-inspector-block">
            <span className="astra-overline">ЛИМИТ ЗАПРОСА</span>
            <label className="astra-cost-field">
              <span>$</span>
              <input
                inputMode="decimal"
                value={maxCostUsd}
                onChange={(event) => {
                  setMaxCostUsd(event.target.value);
                  setAllowPaid(false);
                }}
              />
              <small>максимум</small>
            </label>
          </div>

          <label className="astra-paid-approval">
            <input
              type="checkbox"
              checked={allowPaid}
              disabled={!keyReady || !approved}
              onChange={(event) => setAllowPaid(event.target.checked)}
            />
            <span>Разрешаю один следующий платный вызов Astra с указанным лимитом.</span>
          </label>

          <button
            type="button"
            className="astra-run"
            disabled={!canRun}
            onClick={() => void generate()}
          >
            <span>{busy ? "Astra работает…" : "Запустить Astra"}</span>
            <strong aria-hidden="true">→</strong>
          </button>

          {error && <div className="astra-error">{error}</div>}

          {runs.length > 0 && (
            <div className="astra-history">
              <span className="astra-overline">ИСТОРИЯ ГЛАВЫ</span>
              <strong>{runs.length} запусков</strong>
              <small>Последний результат всегда показан в центре.</small>
            </div>
          )}
        </aside>
      </div>
    </section>
  );
}
