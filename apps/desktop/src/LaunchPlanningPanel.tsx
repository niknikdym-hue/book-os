import { useCallback, useEffect, useMemo, useState } from "react";
import { coreApi } from "./api";
import type { BookContractPayload, ChapterView, ProjectView } from "./types";

type ProviderId = "openai" | "yandex";
type SelectionMode = "AUTO" | "MANUAL";
type SelectionScope = "OPERATION" | "BOOK";

type ProviderModel = { id: string; label: string };
type ProviderView = { id: ProviderId; label: string; models: ProviderModel[] };

type LaunchReadiness = {
  openai_credential_state: "AVAILABLE" | "NOT_AVAILABLE";
  yandex_credential_state?: "AVAILABLE" | "NOT_AVAILABLE";
  configured_model: string | null;
  providers?: ProviderView[];
  anti_junk_entry_count: number;
  external_calls: number;
  paid_calls: number;
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

type RoutingChoice = {
  provider: ProviderId;
  provider_label: string;
  model: string;
  selection_mode: SelectionMode;
  selection_scope: SelectionScope | null;
  operation: string;
  rationale: string;
};

type PlanningProposal = {
  run_id: string;
  run_kind: string;
  provider: string;
  model: string;
  project: ProjectView;
  routing?: RoutingChoice;
};

type BlindCandidate = {
  label: "A" | "B";
  run_id: string;
  contract: BookContractPayload;
};

type BlindComparison = {
  comparison_id: string;
  candidate_a: BlindCandidate;
  candidate_b: BlindCandidate;
  per_request_cap_usd: number;
  total_cap_usd: number;
  models_revealed: false;
};

type BlindSelection = {
  comparison_id: string;
  selected_label: "A" | "B";
  revealed_models: Record<string, string>;
  project: ProjectView;
};

type Props = {
  project: ProjectView;
  chapter: ChapterView | null;
  onProject: (project: ProjectView) => void;
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

function approved(status?: string | null) {
  return status === "APPROVED" || status === "LOCKED";
}

function Candidate({
  candidate,
  busy,
  onSelect,
}: {
  candidate: BlindCandidate;
  busy: boolean;
  onSelect: (label: "A" | "B") => void;
}) {
  return (
    <article className="panel compact-candidate">
      <div className="panel-heading">
        <h4>Вариант {candidate.label}</h4>
        <span className="badge draft">Модель скрыта</span>
      </div>
      <p><strong>Для кого:</strong> {candidate.contract.reader}</p>
      <p><strong>Проблема:</strong> {candidate.contract.reader_problem}</p>
      <p><strong>Обещание:</strong> {candidate.contract.central_promise}</p>
      <p><strong>Тезис:</strong> {candidate.contract.central_thesis}</p>
      <button className="primary" disabled={busy} onClick={() => onSelect(candidate.label)}>
        Выбрать вариант {candidate.label}
      </button>
    </article>
  );
}

export function LaunchPlanningPanel({ project, chapter, onProject }: Props) {
  const [readiness, setReadiness] = useState<LaunchReadiness | null>(null);
  const [routingState, setRoutingState] = useState<RoutingState | null>(null);
  const [provider, setProvider] = useState<ProviderId>("openai");
  const [selectionMode, setSelectionMode] = useState<SelectionMode>("AUTO");
  const [selectionScope, setSelectionScope] = useState<SelectionScope>("OPERATION");
  const [model, setModel] = useState("gpt-6-astra");
  const [apiKey, setApiKey] = useState("");
  const [yandexApiKey, setYandexApiKey] = useState("");
  const [yandexFolderId, setYandexFolderId] = useState("");
  const [idea, setIdea] = useState("");
  const [readerHint, setReaderHint] = useState("");
  const [planningNote, setPlanningNote] = useState("");
  const [maxCostUsd, setMaxCostUsd] = useState("0.50");
  const [allowPaid, setAllowPaid] = useState(false);
  const [blindCostUsd, setBlindCostUsd] = useState("0.50");
  const [allowBlindPaid, setAllowBlindPaid] = useState(false);
  const [blindComparison, setBlindComparison] = useState<BlindComparison | null>(null);
  const [blindSelection, setBlindSelection] = useState<BlindSelection | null>(null);
  const [latestRun, setLatestRun] = useState<PlanningProposal | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reloadReadiness = useCallback(async () => {
    setReadiness(await coreApi<LaunchReadiness>("GET", "/api/launch/readiness"));
  }, []);

  const reloadRouting = useCallback(async () => {
    const value = await coreApi<RoutingState>("GET", `/api/projects/${project.book_id}/model-routing`);
    setRoutingState(value);
    if (value.book_pin) {
      setProvider(value.book_pin.provider);
      setSelectionMode("MANUAL");
      setSelectionScope("BOOK");
      setModel(value.book_pin.model);
    }
  }, [project.book_id]);

  useEffect(() => {
    void Promise.all([reloadReadiness(), reloadRouting()]).catch((reason: unknown) =>
      setError(String(reason)),
    );
  }, [reloadReadiness, reloadRouting]);

  const providers = readiness?.providers ?? routingState?.providers ?? FALLBACK_PROVIDERS;
  const selectedProvider = useMemo(
    () => providers.find((item) => item.id === provider) ?? FALLBACK_PROVIDERS[0],
    [provider, providers],
  );
  const bookPin = routingState?.book_pin ?? null;
  const credentialAvailable =
    provider === "openai"
      ? readiness?.openai_credential_state === "AVAILABLE"
      : readiness?.yandex_credential_state === "AVAILABLE";
  const cost = Number(maxCostUsd);
  const blindCost = Number(blindCostUsd);
  const paidReady =
    credentialAvailable && allowPaid && Number.isFinite(cost) && cost > 0 &&
    (selectionMode === "AUTO" || model.trim().length > 0);
  const blindPaidReady =
    readiness?.openai_credential_state === "AVAILABLE" && allowBlindPaid &&
    Number.isFinite(blindCost) && blindCost > 0 && idea.trim().length >= 3;
  const contractApproved = approved(project.book_contract?.authority_status);
  const architectureApproved = approved(project.architecture?.authority_status);

  function chooseProvider(next: ProviderId) {
    if (bookPin) return;
    setProvider(next);
    setAllowPaid(false);
    const nextProvider = providers.find((item) => item.id === next);
    if (selectionMode === "MANUAL") setModel(nextProvider?.models[0]?.id ?? "");
  }

  async function saveOpenAIKey() {
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

  async function saveYandexCredentials() {
    if (!yandexApiKey.trim() || !yandexFolderId.trim()) return;
    setBusy(true);
    setError(null);
    try {
      await coreApi("POST", "/api/launch/yandex-credentials", {
        api_key: yandexApiKey.trim(),
        folder_id: yandexFolderId.trim(),
      });
      setYandexApiKey("");
      setYandexFolderId("");
      await reloadReadiness();
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  async function clearBookPin() {
    setBusy(true);
    setError(null);
    try {
      await coreApi("POST", `/api/projects/${project.book_id}/model-routing/clear-book-pin`);
      setSelectionMode("AUTO");
      setSelectionScope("OPERATION");
      await reloadRouting();
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
        provider,
        model: selectionMode === "MANUAL" ? model.trim() : null,
        selection_mode: selectionMode,
        selection_scope: selectionMode === "MANUAL" ? selectionScope : null,
        max_cost_usd: cost,
      });
      setLatestRun(result);
      onProject(result.project);
      setAllowPaid(false);
      if (selectionMode === "MANUAL" && selectionScope === "BOOK") await reloadRouting();
    } catch (reason) {
      setAllowPaid(false);
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  async function runBlindComparison() {
    setBusy(true);
    setError(null);
    setBlindComparison(null);
    setBlindSelection(null);
    try {
      setBlindComparison(
        await coreApi<BlindComparison>(
          "POST",
          `/api/projects/${project.book_id}/planning/book-contract/blind-compare`,
          {
            idea: idea.trim(),
            reader_hint: readerHint.trim(),
            max_output_tokens: 2600,
            max_cost_usd_per_request: blindCost,
          },
        ),
      );
    } catch (reason) {
      setError(String(reason));
    } finally {
      setAllowBlindPaid(false);
      setBusy(false);
    }
  }

  async function selectBlindCandidate(label: "A" | "B") {
    if (!blindComparison) return;
    setBusy(true);
    setError(null);
    try {
      const result = await coreApi<BlindSelection>(
        "POST",
        `/api/projects/${project.book_id}/planning/book-contract/blind-compare/${blindComparison.comparison_id}/select`,
        { selected_label: label },
      );
      setBlindSelection(result);
      onProject(result.project);
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel launch-planning-panel" aria-label="Текущая AI-задача">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">ТЕКУЩАЯ ЗАДАЧА</p>
          <h3>
            {!contractApproved
              ? "Идея и контракт книги"
              : !architectureApproved
                ? "Архитектура книги"
                : "Подготовка главы"}
          </h3>
        </div>
        <span className={`badge ${credentialAvailable ? "approved" : "draft"}`}>
          {credentialAvailable ? `${selectedProvider.label} подключён` : `${selectedProvider.label} не подключён`}
        </span>
      </div>

      {!contractApproved && (
        <div className="primary-planning-step">
          <label className="field">
            <span>О чём должна быть эта книга?</span>
            <textarea
              rows={6}
              value={idea}
              onChange={(event) => setIdea(event.target.value)}
              placeholder="Опишите задачу книги своими словами. Промпт писать не нужно."
            />
          </label>
          <label className="field">
            <span>Для кого книга — необязательно</span>
            <textarea
              rows={3}
              value={readerHint}
              onChange={(event) => setReaderHint(event.target.value)}
              placeholder="Если аудитория уже определена — укажите её."
            />
          </label>
        </div>
      )}

      {contractApproved && !architectureApproved && (
        <label className="field primary-planning-step">
          <span>Пожелание к структуре — необязательно</span>
          <textarea
            rows={4}
            value={planningNote}
            onChange={(event) => setPlanningNote(event.target.value)}
            placeholder="Например: не делать главы одинакового размера ради симметрии."
          />
        </label>
      )}

      {architectureApproved && chapter && (
        <div className="selected-topic-summary">
          <small>Следующая глава</small>
          <strong>{chapter.ordinal}. {chapter.working_title}</strong>
        </div>
      )}

      <details className="advanced-settings ai-settings">
        <summary>AI и модель</summary>
        <div className="planning-step">
          <div className="actions planning-action left-actions">
            {providers.map((item) => (
              <button
                key={item.id}
                type="button"
                className={provider === item.id ? "primary" : "ghost"}
                disabled={busy || Boolean(bookPin)}
                onClick={() => chooseProvider(item.id)}
              >
                {item.label}
              </button>
            ))}
          </div>

          {bookPin ? (
            <div className="selected-topic-summary">
              <small>Закреплено на всю книгу</small>
              <strong>{bookPin.provider_label} · {bookPin.model}</strong>
              <button className="ghost" type="button" disabled={busy} onClick={() => void clearBookPin()}>
                Вернуть автоматический выбор
              </button>
            </div>
          ) : (
            <>
              <div className="actions planning-action left-actions">
                <button
                  type="button"
                  className={selectionMode === "AUTO" ? "primary" : "ghost"}
                  onClick={() => { setSelectionMode("AUTO"); setAllowPaid(false); }}
                >
                  Автоматически
                </button>
                <button
                  type="button"
                  className={selectionMode === "MANUAL" ? "primary" : "ghost"}
                  onClick={() => {
                    setSelectionMode("MANUAL");
                    setModel(selectedProvider.models[0]?.id ?? "");
                    setAllowPaid(false);
                  }}
                >
                  Выбрать модель
                </button>
              </div>

              {selectionMode === "MANUAL" && (
                <div className="form-grid planning-settings-grid">
                  <label className="field">
                    <span>Модель</span>
                    <select value={model} onChange={(event) => setModel(event.target.value)}>
                      {selectedProvider.models.map((item) => (
                        <option key={item.id} value={item.id}>{item.label}</option>
                      ))}
                    </select>
                  </label>
                  <fieldset className="field">
                    <legend>Использовать</legend>
                    <label>
                      <input
                        type="radio"
                        name="model-scope"
                        checked={selectionScope === "OPERATION"}
                        onChange={() => setSelectionScope("OPERATION")}
                      />
                      Только для следующей операции
                    </label>
                    <label>
                      <input
                        type="radio"
                        name="model-scope"
                        checked={selectionScope === "BOOK"}
                        onChange={() => setSelectionScope("BOOK")}
                      />
                      Для всей книги
                    </label>
                  </fieldset>
                </div>
              )}
            </>
          )}
        </div>

        {!credentialAvailable && (
          <details className="credential-setup-drawer">
            <summary>Подключить {selectedProvider.label}</summary>
            {provider === "openai" ? (
              <div className="credential-setup">
                <label className="field">
                  <span>OpenAI API key</span>
                  <small>Сохраняется только в macOS Keychain.</small>
                  <input
                    type="password"
                    autoComplete="off"
                    value={apiKey}
                    onChange={(event) => setApiKey(event.target.value)}
                    placeholder="Вставьте API key"
                  />
                </label>
                <button className="primary" disabled={busy || apiKey.trim().length < 10} onClick={() => void saveOpenAIKey()}>
                  Подключить OpenAI
                </button>
              </div>
            ) : (
              <div className="credential-setup">
                <label className="field">
                  <span>Yandex AI Studio API key</span>
                  <input type="password" value={yandexApiKey} onChange={(event) => setYandexApiKey(event.target.value)} />
                </label>
                <label className="field">
                  <span>Folder ID</span>
                  <input value={yandexFolderId} onChange={(event) => setYandexFolderId(event.target.value)} />
                </label>
                <button
                  className="primary"
                  disabled={busy || yandexApiKey.trim().length < 10 || yandexFolderId.trim().length < 3}
                  onClick={() => void saveYandexCredentials()}
                >
                  Подключить Yandex AI
                </button>
              </div>
            )}
          </details>
        )}

        <details className="advanced-settings">
          <summary>Лимит стоимости запроса</summary>
          <label className="field">
            <span>Максимум, USD</span>
            <input inputMode="decimal" value={maxCostUsd} onChange={(event) => setMaxCostUsd(event.target.value)} />
          </label>
        </details>
      </details>

      {!contractApproved && provider === "openai" && (
        <details className="advanced-settings">
          <summary>Сравнить Sol и Astra вслепую — по желанию</summary>
          {!blindComparison && !blindSelection && (
            <>
              <label className="field">
                <span>Максимум на один из двух запросов, USD</span>
                <input inputMode="decimal" value={blindCostUsd} onChange={(event) => setBlindCostUsd(event.target.value)} />
              </label>
              <label className="paid-approval">
                <input type="checkbox" checked={allowBlindPaid} onChange={(event) => setAllowBlindPaid(event.target.checked)} />
                <span>Разрешаю два сравнительных OpenAI-запроса, каждый не дороже ${blindCostUsd || "0"}.</span>
              </label>
              <button className="ghost" disabled={busy || !blindPaidReady} onClick={() => void runBlindComparison()}>
                Получить варианты A и B
              </button>
            </>
          )}
          {blindComparison && (
            <div className="form-grid">
              <Candidate candidate={blindComparison.candidate_a} busy={busy} onSelect={(label) => void selectBlindCandidate(label)} />
              <Candidate candidate={blindComparison.candidate_b} busy={busy} onSelect={(label) => void selectBlindCandidate(label)} />
            </div>
          )}
          {blindSelection && (
            <div className="selected-topic-summary">
              <strong>Выбран вариант {blindSelection.selected_label}</strong>
              <span>A = {blindSelection.revealed_models.A} · B = {blindSelection.revealed_models.B}</span>
            </div>
          )}
        </details>
      )}

      {!blindComparison && !blindSelection && (
        <label className="paid-approval compact-approval">
          <input type="checkbox" checked={allowPaid} onChange={(event) => setAllowPaid(event.target.checked)} />
          <span>Разрешаю только следующий платный запрос. Лимит — ${maxCostUsd || "0"}.</span>
        </label>
      )}

      <div className="actions planning-action">
        {!contractApproved && !blindComparison && !blindSelection && (
          <button
            className="primary"
            disabled={busy || !paidReady || idea.trim().length < 3}
            onClick={() => void run(`/api/projects/${project.book_id}/planning/book-contract`, {
              idea: idea.trim(),
              reader_hint: readerHint.trim(),
              max_output_tokens: 2600,
            })}
          >
            {busy ? "BOOK OS работает…" : "Предложить контракт книги"}
          </button>
        )}

        {contractApproved && !architectureApproved && (
          <button
            className="primary"
            disabled={busy || !paidReady}
            onClick={() => void run(`/api/projects/${project.book_id}/planning/architecture`, {
              planning_note: planningNote.trim(),
              max_output_tokens: 5000,
            })}
          >
            {busy ? "BOOK OS работает…" : "Предложить архитектуру"}
          </button>
        )}

        {architectureApproved && chapter && (
          <button
            className="primary"
            disabled={busy || !paidReady}
            onClick={() => void run(
              `/api/projects/${project.book_id}/chapters/${chapter.chapter_id}/planning/contract`,
              { planning_note: planningNote.trim(), max_output_tokens: 3200 },
            )}
          >
            {busy ? "BOOK OS работает…" : "Предложить контракт главы"}
          </button>
        )}
      </div>

      {latestRun && (
        <details className="advanced-settings">
          <summary>Последний AI-запуск</summary>
          <div className="planning-run">
            <strong>Черновик создан — теперь его нужно проверить</strong>
            <span>{latestRun.routing?.provider_label ?? latestRun.provider} · {latestRun.model}</span>
          </div>
        </details>
      )}

      {error && <div className="alert inline-alert">{error}</div>}
    </section>
  );
}
