import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { coreApi } from "./api";
import type { DraftRunView, DraftingPanelProps } from "./draftingTypes";
import {
  OPENAI_WORK_LEVEL_OPTIONS,
  openAIWorkLevelLabel,
  setPendingOpenAIWorkLevel,
  type OpenAIWorkLevel,
} from "./openaiWorkLevel";

type ProviderId = "openai" | "yandex";
type SelectionMode = "AUTO" | "MANUAL";
type SelectionScope = "OPERATION" | "BOOK";

type ProviderView = {
  id: ProviderId;
  label: string;
  models: Array<{ id: string; label: string }>;
};

type LaunchReadiness = {
  openai_credential_state: "AVAILABLE" | "NOT_AVAILABLE";
  yandex_credential_state?: "AVAILABLE" | "NOT_AVAILABLE";
  providers?: ProviderView[];
};

type BookModelPin = {
  provider: ProviderId;
  provider_label: string;
  model: string;
};

type RoutingState = {
  book_pin: BookModelPin | null;
  providers?: ProviderView[];
};

const FALLBACK_PROVIDERS: ProviderView[] = [
  {
    id: "openai",
    label: "OpenAI",
    models: [
      { id: "gpt-6-astra", label: "GPT-6 Astra" },
      { id: "gpt-5.6-sol", label: "GPT-5.6 Sol" },
      { id: "gpt-5.6-terra", label: "GPT-5.6 Terra" },
      { id: "gpt-5.6-luna", label: "GPT-5.6 Luna" },
    ],
  },
  {
    id: "yandex",
    label: "Yandex AI",
    models: [
      { id: "aliceai-llm", label: "Alice AI LLM" },
      { id: "aliceai-llm-flash", label: "Alice AI LLM Flash" },
      { id: "yandexgpt-5.1", label: "YandexGPT Pro 5.1" },
      { id: "yandexgpt-5-pro", label: "YandexGPT Pro 5" },
      { id: "yandexgpt-5-lite", label: "YandexGPT Lite 5" },
    ],
  },
];

function providerTitle(provider: ProviderId) {
  return provider === "openai" ? "OpenAI" : "Yandex AI";
}

export function DraftingPanel({ project, chapter, api = coreApi }: DraftingPanelProps) {
  const [objective, setObjective] = useState("");
  const [context, setContext] = useState("");
  const [provider, setProvider] = useState<ProviderId>("openai");
  const [selectionMode, setSelectionMode] = useState<SelectionMode>("MANUAL");
  const [selectionScope, setSelectionScope] = useState<SelectionScope>("OPERATION");
  const [model, setModel] = useState("gpt-6-astra");
  const [workLevel, setWorkLevel] = useState<OpenAIWorkLevel>("high");
  const [maxCostUsd, setMaxCostUsd] = useState("0.50");
  const [allowPaid, setAllowPaid] = useState(false);
  const [apiKey, setApiKey] = useState("");
  const [runs, setRuns] = useState<DraftRunView[]>([]);
  const [readiness, setReadiness] = useState<LaunchReadiness | null>(null);
  const [routingState, setRoutingState] = useState<RoutingState | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const draftLoadSequence = useRef(0);

  const approved =
    chapter?.chapter_contract?.authority_status === "APPROVED" ||
    chapter?.chapter_contract?.authority_status === "LOCKED";
  const providers = readiness?.providers ?? routingState?.providers ?? FALLBACK_PROVIDERS;
  const selectedProvider = useMemo(
    () => providers.find((item) => item.id === provider) ?? FALLBACK_PROVIDERS[0],
    [provider, providers],
  );
  const selectedModel =
    selectedProvider.models.find((item) => item.id === model) ?? selectedProvider.models[0] ?? null;
  const bookPin = routingState?.book_pin ?? null;
  const cost = Number(maxCostUsd);
  const credentialAvailable =
    provider === "openai"
      ? readiness?.openai_credential_state === "AVAILABLE"
      : readiness?.yandex_credential_state === "AVAILABLE";
  const canRun =
    Boolean(chapter) &&
    approved &&
    Boolean(credentialAvailable) &&
    objective.trim().length > 0 &&
    allowPaid &&
    Number.isFinite(cost) &&
    cost > 0 &&
    (selectionMode === "AUTO" || model.trim().length > 0) &&
    !busy;
  const latest = runs[0] ?? null;

  const reloadReadiness = useCallback(async () => {
    setReadiness(await api<LaunchReadiness>("GET", "/api/launch/readiness"));
  }, [api]);

  const reloadRouting = useCallback(async () => {
    const state = await api<RoutingState>(
      "GET",
      `/api/projects/${project.book_id}/model-routing`,
    );
    setRoutingState(state);
    if (state.book_pin) {
      setProvider(state.book_pin.provider);
      setSelectionMode("MANUAL");
      setSelectionScope("BOOK");
      setModel(state.book_pin.model);
    }
  }, [api, project.book_id]);

  const reloadDrafts = useCallback(async () => {
    const loadId = ++draftLoadSequence.current;
    setRuns([]);
    setCopied(false);
    if (!chapter) return;
    const value = await api<DraftRunView[]>(
      "GET",
      `/api/projects/${project.book_id}/chapters/${chapter.chapter_id}/drafts`,
    );
    if (loadId === draftLoadSequence.current) {
      setRuns(value);
    }
  }, [api, chapter, project.book_id]);

  useEffect(() => {
    let active = true;
    setError(null);
    void Promise.all([reloadReadiness(), reloadRouting(), reloadDrafts()]).catch(
      (reason: unknown) => {
        if (active) setError(String(reason));
      },
    );
    return () => {
      active = false;
    };
  }, [reloadDrafts, reloadReadiness, reloadRouting]);

  useEffect(() => {
    if (selectionMode !== "MANUAL" || bookPin) return;
    if (!selectedProvider.models.some((item) => item.id === model)) {
      setModel(selectedProvider.models[0]?.id ?? "");
      setAllowPaid(false);
    }
  }, [bookPin, model, selectedProvider, selectionMode]);

  async function saveOpenAIKey() {
    if (!apiKey.trim()) return;
    setBusy(true);
    setError(null);
    try {
      await api("POST", "/api/launch/openai-key", { api_key: apiKey.trim() });
      setApiKey("");
      await reloadReadiness();
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  function chooseProvider(next: ProviderId) {
    if (bookPin || next === provider) return;
    setProvider(next);
    setSelectionMode("MANUAL");
    const nextProvider = providers.find((item) => item.id === next);
    setModel(nextProvider?.models[0]?.id ?? "");
    setAllowPaid(false);
  }

  async function clearBookPin() {
    setBusy(true);
    setError(null);
    try {
      await api("POST", `/api/projects/${project.book_id}/model-routing/clear-book-pin`);
      setProvider("openai");
      setSelectionMode("MANUAL");
      setSelectionScope("OPERATION");
      setModel("gpt-6-astra");
      setAllowPaid(false);
      await reloadRouting();
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
      if (provider === "openai") setPendingOpenAIWorkLevel(workLevel);
      const run = await api<DraftRunView>(
        "POST",
        `/api/projects/${project.book_id}/chapters/${chapter.chapter_id}/drafts`,
        {
          section_objective: objective.trim(),
          provider,
          model: selectionMode === "MANUAL" ? model.trim() : null,
          selection_mode: selectionMode,
          selection_scope: selectionMode === "MANUAL" ? selectionScope : null,
          reasoning_effort: provider === "openai" ? workLevel : null,
          untrusted_context: context.trim() ? [context.trim()] : [],
          max_output_tokens: 3500,
          max_cost_usd: cost,
        },
      );
      setRuns((current) => [run, ...current]);
      setAllowPaid(false);
      if (selectionMode === "MANUAL" && selectionScope === "BOOK") {
        await reloadRouting();
      }
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
          <h3>{provider === "openai" && model === "gpt-6-astra" ? "GPT-6 Astra" : selectedModel?.label ?? model}</h3>
          <p className="writer-chapter">
            {chapter ? `${chapter.ordinal}. ${chapter.working_title}` : "Выберите главу для работы"}
          </p>
        </div>
        <div className={`writer-status ${credentialAvailable ? "ready" : "missing"}`}>
          <span aria-hidden="true" />
          {credentialAvailable ? `${providerTitle(provider)} API подключён` : `${providerTitle(provider)} не подключён`}
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
                <span className="writer-chip">
                  {selectionMode === "AUTO" ? "Автовыбор" : selectedModel?.label ?? model}
                </span>
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
                  <details className="writer-provenance">
                    <summary>Данные запуска</summary>
                    <dl>
                      <div><dt>Модель</dt><dd>{latest.model}</dd></div>
                      <div><dt>Уровень</dt><dd>{openAIWorkLevelLabel(latest.reasoning_effort)}</dd></div>
                      <div><dt>Статус</dt><dd>{latest.revision_status ?? latest.run_status}</dd></div>
                      <div><dt>Revision</dt><dd>{latest.revision_id ?? "—"}</dd></div>
                    </dl>
                  </details>
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
            <span className="writer-overline">МОДЕЛЬ</span>
            <div className="writer-model-card">
              <span className="writer-model-orb" aria-hidden="true" />
              <div>
                <strong>{selectionMode === "AUTO" ? "BOOK OS Auto" : selectedModel?.label ?? model}</strong>
                <small>{providerTitle(provider)} · Writer</small>
              </div>
            </div>
          </section>

          {provider === "openai" && (
            <section>
              <span className="writer-overline">ГЛУБИНА РАБОТЫ</span>
              <div className="writer-levels" role="group" aria-label="Уровень работы OpenAI">
                {OPENAI_WORK_LEVEL_OPTIONS.map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    className={workLevel === option.value ? "active" : ""}
                    aria-pressed={workLevel === option.value}
                    onClick={() => {
                      setWorkLevel(option.value);
                      setAllowPaid(false);
                    }}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
              <p className="writer-note">High — основной режим для работы над книгой.</p>
            </section>
          )}

          {!credentialAvailable && provider === "openai" && (
            <section className="writer-key-section">
              <span className="writer-overline">ПОДКЛЮЧИТЬ OPENAI</span>
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
              <button
                type="button"
                className="writer-secondary"
                disabled={busy || !apiKey.trim()}
                onClick={() => void saveOpenAIKey()}
              >
                Сохранить в Keychain
              </button>
              <small>Ключ хранится локально в macOS Keychain.</small>
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

          {bookPin && (
            <section className="writer-pin">
              <span className="writer-overline">НА ВСЮ КНИГУ</span>
              <strong>{bookPin.provider_label} · {bookPin.model}</strong>
              <button type="button" className="writer-link" disabled={busy} onClick={() => void clearBookPin()}>
                Снять закрепление
              </button>
            </section>
          )}

          <details className="writer-advanced">
            <summary>Другие модели и маршрутизация</summary>
            <div className="writer-advanced-content">
              <div className="writer-provider-switch" role="group" aria-label="AI-провайдер">
                {providers.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    className={provider === item.id ? "active" : ""}
                    disabled={busy || Boolean(bookPin)}
                    onClick={() => chooseProvider(item.id)}
                  >
                    {providerTitle(item.id)}
                  </button>
                ))}
              </div>
              <div className="writer-routing-switch" role="group" aria-label="Выбор модели">
                <button
                  type="button"
                  className={selectionMode === "MANUAL" ? "active" : ""}
                  disabled={busy || Boolean(bookPin)}
                  onClick={() => {
                    setSelectionMode("MANUAL");
                    setModel(selectedProvider.models[0]?.id ?? "");
                    setAllowPaid(false);
                  }}
                >
                  Ручной
                </button>
                <button
                  type="button"
                  className={selectionMode === "AUTO" ? "active" : ""}
                  disabled={busy || Boolean(bookPin)}
                  onClick={() => {
                    setSelectionMode("AUTO");
                    setSelectionScope("OPERATION");
                    setAllowPaid(false);
                  }}
                >
                  Авто
                </button>
              </div>
              {selectionMode === "MANUAL" && (
                <>
                  <label>
                    <span>Модель</span>
                    <select
                      aria-label="Модель"
                      value={model}
                      disabled={busy || Boolean(bookPin)}
                      onChange={(event) => {
                        setModel(event.target.value);
                        setAllowPaid(false);
                      }}
                    >
                      {selectedProvider.models.map((item) => (
                        <option key={item.id} value={item.id}>{item.label}</option>
                      ))}
                    </select>
                  </label>
                  <div className="writer-routing-switch" role="group" aria-label="Где закрепить модель">
                    <button
                      type="button"
                      className={selectionScope === "OPERATION" ? "active" : ""}
                      disabled={busy || Boolean(bookPin)}
                      onClick={() => setSelectionScope("OPERATION")}
                    >
                      Эта операция
                    </button>
                    <button
                      type="button"
                      className={selectionScope === "BOOK" ? "active" : ""}
                      disabled={busy || Boolean(bookPin)}
                      onClick={() => setSelectionScope("BOOK")}
                    >
                      Вся книга
                    </button>
                  </div>
                </>
              )}
            </div>
          </details>

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
            <span>{busy ? "Astra работает…" : provider === "openai" && model === "gpt-6-astra" ? "Запустить Astra" : "Запустить Writer"}</span>
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
    </section>
  );
}
