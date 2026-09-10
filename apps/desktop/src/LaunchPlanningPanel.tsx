import { useCallback, useEffect, useMemo, useState } from "react";
import { coreApi } from "./api";
import type { BookContractPayload, ChapterView, ProjectView } from "./types";

type ProviderId = "openai" | "yandex";
type SelectionMode = "AUTO" | "MANUAL";
type SelectionScope = "OPERATION" | "BOOK";

type ProviderModel = {
  id: string;
  label: string;
};

type ProviderView = {
  id: ProviderId;
  label: string;
  models: ProviderModel[];
};

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
  provider_run_id: string | null;
  prompt_id: string;
  prompt_version: string;
  prompt_hash: string;
  usage: Record<string, unknown>;
  status: string;
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
  revealed_run_ids: Record<string, string>;
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
    label: "AI Ya",
    models: [
      { id: "aliceai-llm", label: "Alice AI LLM" },
      { id: "aliceai-llm-flash", label: "Alice AI LLM Flash" },
      { id: "yandexgpt-5.1", label: "YandexGPT Pro 5.1" },
      { id: "yandexgpt-5-pro", label: "YandexGPT Pro 5" },
      { id: "yandexgpt-5-lite", label: "YandexGPT Lite 5" },
    ],
  },
];

function ContractCandidateCard({
  candidate,
  busy,
  onSelect,
}: {
  candidate: BlindCandidate;
  busy: boolean;
  onSelect: (label: "A" | "B") => void;
}) {
  const contract = candidate.contract;
  return (
    <article className="panel" aria-label={`Вариант ${candidate.label}`}>
      <div className="panel-heading">
        <h4>Вариант {candidate.label}</h4>
        <span className="badge draft">Модель скрыта</span>
      </div>
      <p><strong>Для кого:</strong> {contract.reader}</p>
      <p><strong>Проблема:</strong> {contract.reader_problem}</p>
      <p><strong>Обещание:</strong> {contract.central_promise}</p>
      <p><strong>Центральный тезис:</strong> {contract.central_thesis}</p>
      <p><strong>Уникальный угол:</strong> {contract.unique_angle}</p>
      <p><strong>Траектория читателя:</strong> {contract.reader_trajectory}</p>
      <p><strong>Доказательность:</strong> {contract.evidence_policy}</p>
      <p><strong>Голос и жанр:</strong> {contract.voice_genre_constraints}</p>
      <div>
        <strong>Что исключено:</strong>
        <ul>{contract.explicit_exclusions.map((item) => <li key={item}>{item}</li>)}</ul>
      </div>
      <div>
        <strong>Критерии готовности:</strong>
        <ul>{contract.readiness_criteria.map((item) => <li key={item}>{item}</li>)}</ul>
      </div>
      <button className="primary" disabled={busy} onClick={() => onSelect(candidate.label)}>
        Выбираю вариант {candidate.label}
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

  const providers = readiness?.providers ?? routingState?.providers ?? FALLBACK_PROVIDERS;
  const selectedProvider = useMemo(
    () => providers.find((item) => item.id === provider) ?? FALLBACK_PROVIDERS[0],
    [providers, provider],
  );
  const selectedProviderLabel = selectedProvider.label;
  const bookPin = routingState?.book_pin ?? null;

  const reloadReadiness = useCallback(async () => {
    const value = await coreApi<LaunchReadiness>("GET", "/api/launch/readiness");
    setReadiness(value);
  }, []);

  const reloadRouting = useCallback(async () => {
    const value = await coreApi<RoutingState>(
      "GET",
      `/api/projects/${project.book_id}/model-routing`,
    );
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

  useEffect(() => {
    if (selectionMode !== "MANUAL" || bookPin) return;
    if (!selectedProvider.models.some((item) => item.id === model)) {
      setModel(selectedProvider.models[0]?.id ?? "");
    }
  }, [bookPin, model, selectedProvider, selectionMode]);

  const cost = Number(maxCostUsd);
  const blindCost = Number(blindCostUsd);
  const credentialAvailable =
    provider === "openai"
      ? readiness?.openai_credential_state === "AVAILABLE"
      : readiness?.yandex_credential_state === "AVAILABLE";
  const paidReady =
    credentialAvailable &&
    allowPaid &&
    Number.isFinite(cost) &&
    cost > 0 &&
    (selectionMode === "AUTO" || model.trim().length > 0);
  const blindPaidReady =
    readiness?.openai_credential_state === "AVAILABLE" &&
    allowBlindPaid &&
    Number.isFinite(blindCost) &&
    blindCost > 0 &&
    idea.trim().length >= 3;
  const contractApproved =
    project.book_contract?.authority_status === "APPROVED" ||
    project.book_contract?.authority_status === "LOCKED";
  const architectureApproved =
    project.architecture?.authority_status === "APPROVED" ||
    project.architecture?.authority_status === "LOCKED";

  function chooseProvider(nextProvider: ProviderId) {
    if (bookPin || nextProvider === provider) return;
    setProvider(nextProvider);
    setAllowPaid(false);
    const next = providers.find((item) => item.id === nextProvider);
    if (selectionMode === "MANUAL") setModel(next?.models[0]?.id ?? "");
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
      await coreApi(
        "POST",
        `/api/projects/${project.book_id}/model-routing/clear-book-pin`,
      );
      setSelectionMode("AUTO");
      setSelectionScope("OPERATION");
      setRoutingState((current) => ({
        providers: current?.providers,
        book_pin: null,
      }));
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

  async function runBlindComparison() {
    setBusy(true);
    setError(null);
    setBlindComparison(null);
    setBlindSelection(null);
    try {
      const result = await coreApi<BlindComparison>(
        "POST",
        `/api/projects/${project.book_id}/planning/book-contract/blind-compare`,
        {
          idea: idea.trim(),
          reader_hint: readerHint.trim(),
          max_output_tokens: 2600,
          max_cost_usd_per_request: blindCost,
        },
      );
      setBlindComparison(result);
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
    <section className="panel launch-planning-panel" aria-label="Идея и план книги">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">ТЕКУЩИЙ РАБОЧИЙ ШАГ</p>
          <h3>Идея и план книги</h3>
        </div>
        <span className={`badge ${credentialAvailable ? "approved" : "draft"}`}>
          {credentialAvailable ? `${selectedProviderLabel} готов` : `${selectedProviderLabel} не настроен`}
        </span>
      </div>

      <p className="muted">
        BOOK OS создаёт только предложение. Контракт книги, архитектура и контракты глав становятся
        авторитетными только после вашего отдельного утверждения.
      </p>

      <section className="planning-step" aria-label="Выбор AI">
        <h4>AI для этой книги</h4>
        <div className="actions planning-action">
          {providers.map((item) => (
            <button
              key={item.id}
              type="button"
              className={provider === item.id ? "primary" : "ghost"}
              aria-pressed={provider === item.id}
              disabled={busy || Boolean(bookPin)}
              onClick={() => chooseProvider(item.id)}
            >
              {item.label}
            </button>
          ))}
        </div>

        {bookPin && (
          <div className="selected-topic-summary" role="status">
            <small>Ручное закрепление на всю книгу</small>
            <strong>{bookPin.provider_label} · {bookPin.model}</strong>
            <button className="ghost" type="button" disabled={busy} onClick={() => void clearBookPin()}>
              Снять закрепление и вернуть Авто
            </button>
          </div>
        )}

        {!bookPin && (
          <>
            <div className="actions planning-action">
              <button
                type="button"
                className={selectionMode === "AUTO" ? "primary" : "ghost"}
                aria-pressed={selectionMode === "AUTO"}
                disabled={busy}
                onClick={() => {
                  setSelectionMode("AUTO");
                  setAllowPaid(false);
                }}
              >
                Авто
              </button>
              <button
                type="button"
                className={selectionMode === "MANUAL" ? "primary" : "ghost"}
                aria-pressed={selectionMode === "MANUAL"}
                disabled={busy}
                onClick={() => {
                  setSelectionMode("MANUAL");
                  setModel(selectedProvider.models[0]?.id ?? "");
                  setAllowPaid(false);
                }}
              >
                Ручной выбор
              </button>
            </div>

            {selectionMode === "AUTO" ? (
              <p className="muted">
                BOOK OS сам выберет модель {selectedProviderLabel} для каждой редакционной операции.
                Точная модель сохранится в provenance каждого вызова.
              </p>
            ) : (
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
                  <legend>Где закрепить</legend>
                  <label>
                    <input
                      type="radio"
                      name="model-scope"
                      checked={selectionScope === "OPERATION"}
                      onChange={() => setSelectionScope("OPERATION")}
                    />
                    Только на конкретную операцию
                  </label>
                  <label>
                    <input
                      type="radio"
                      name="model-scope"
                      checked={selectionScope === "BOOK"}
                      onChange={() => setSelectionScope("BOOK")}
                    />
                    На всю книгу
                  </label>
                </fieldset>
              </div>
            )}
          </>
        )}
      </section>

      {provider === "openai" && readiness?.openai_credential_state === "NOT_AVAILABLE" && (
        <div className="alert inline-alert">OpenAI ещё не подключён на этом Mac.</div>
      )}

      {provider === "yandex" && readiness?.yandex_credential_state !== "AVAILABLE" && (
        <div className="credential-setup">
          <label className="field">
            <span>API-ключ AI Ya (Yandex AI Studio)</span>
            <small>Ключ сохраняется только в macOS Keychain.</small>
            <input
              type="password"
              autoComplete="off"
              value={yandexApiKey}
              onChange={(event) => setYandexApiKey(event.target.value)}
              placeholder="API key"
            />
          </label>
          <label className="field">
            <span>Folder ID Yandex Cloud</span>
            <input
              value={yandexFolderId}
              onChange={(event) => setYandexFolderId(event.target.value)}
              placeholder="Идентификатор каталога"
            />
          </label>
          <button
            className="primary"
            disabled={busy || yandexApiKey.trim().length < 10 || yandexFolderId.trim().length < 3}
            onClick={() => void saveYandexCredentials()}
          >
            Сохранить AI Ya в Keychain
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

      {provider === "openai" && !contractApproved && !blindSelection && (
        <section className="planning-step">
          <h4>Слепой тест OpenAI: Sol ↔ Astra</h4>
          <p className="muted">
            Это отдельный сравнительный инструмент. BOOK OS отправит одну и ту же идею двум моделям
            OpenAI с одинаковым контекстом. Вы увидите только варианты A и B до фиксации выбора.
          </p>

          {!blindComparison && (
            <>
              <label className="field">
                <span>Максимальная стоимость каждого из двух запросов, USD</span>
                <input
                  inputMode="decimal"
                  value={blindCostUsd}
                  onChange={(event) => setBlindCostUsd(event.target.value)}
                />
                <small>
                  При значении ${blindCostUsd || "0"} общий жёсткий предел двух запросов — до ${
                    Number.isFinite(blindCost) && blindCost > 0 ? (blindCost * 2).toFixed(2) : "0.00"
                  }.
                </small>
              </label>
              <label className="paid-approval">
                <input
                  type="checkbox"
                  checked={allowBlindPaid}
                  onChange={(event) => setAllowBlindPaid(event.target.checked)}
                />
                <span>
                  Разрешаю <strong>только этот слепой тест</strong>: два платных OpenAI-запроса,
                  каждый не дороже ${blindCostUsd || "0"}. После попытки разрешение автоматически сбросится.
                </span>
              </label>
              <div className="actions planning-action">
                <button
                  className="primary"
                  disabled={busy || !blindPaidReady}
                  onClick={() => void runBlindComparison()}
                >
                  {busy ? "BOOK OS работает…" : "Получить слепые варианты A и B"}
                </button>
              </div>
            </>
          )}

          {blindComparison && (
            <>
              <p className="selected-topic-summary" role="status">
                Модели скрыты. Сначала сравните содержание и выберите сильнейший Book Contract.
              </p>
              <div className="form-grid">
                <ContractCandidateCard
                  candidate={blindComparison.candidate_a}
                  busy={busy}
                  onSelect={(label) => void selectBlindCandidate(label)}
                />
                <ContractCandidateCard
                  candidate={blindComparison.candidate_b}
                  busy={busy}
                  onSelect={(label) => void selectBlindCandidate(label)}
                />
              </div>
            </>
          )}
        </section>
      )}

      {blindSelection && (
        <div className="selected-topic-summary" role="status" aria-live="polite">
          <small>Слепой выбор зафиксирован до раскрытия моделей</small>
          <strong>Выбран вариант {blindSelection.selected_label}</strong>
          <span>
            A = {blindSelection.revealed_models.A} · B = {blindSelection.revealed_models.B}
          </span>
          <span>Выбранный вариант перенесён в черновик Book Contract для вашей проверки.</span>
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
        <summary>Стоимость выбранного AI-вызова</summary>
        <label className="field">
          <span>Максимальная стоимость одного запроса, USD</span>
          <input
            inputMode="decimal"
            value={maxCostUsd}
            onChange={(event) => setMaxCostUsd(event.target.value)}
          />
          <small>BOOK OS проверяет верхнюю границу стоимости до отправки платного запроса.</small>
        </label>
      </details>

      {!blindComparison && !blindSelection && (
        <label className="paid-approval">
          <input
            type="checkbox"
            checked={allowPaid}
            onChange={(event) => setAllowPaid(event.target.checked)}
          />
          <span>
            Разрешаю <strong>только следующий</strong> платный запрос через {selectedProviderLabel}.
            Текущий предел — ${maxCostUsd || "0"}. После любой попытки разрешение автоматически сбросится.
          </span>
        </label>
      )}

      <div className="actions planning-action">
        {!contractApproved && !blindComparison && !blindSelection && (
          <button
            className="ghost"
            disabled={busy || !paidReady || idea.trim().length < 3}
            onClick={() =>
              void run(`/api/projects/${project.book_id}/planning/book-contract`, {
                idea: idea.trim(),
                reader_hint: readerHint.trim(),
                max_output_tokens: 2600,
              })
            }
          >
            {busy ? "BOOK OS работает…" : "Сформировать Book Contract"}
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
          <span>
            {latestRun.routing?.provider_label ?? latestRun.provider} · {latestRun.model}
          </span>
          {latestRun.routing && (
            <small>
              {latestRun.routing.selection_mode === "AUTO" ? "Авто" : "Ручной выбор"}
              {latestRun.routing.selection_scope === "BOOK" ? " · закреплено на книгу" : ""}
              {latestRun.routing.selection_scope === "OPERATION" ? " · только эта операция" : ""}
            </small>
          )}
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
