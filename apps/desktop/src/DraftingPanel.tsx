import { useCallback, useEffect, useMemo, useState } from "react";
import { coreApi } from "./api";
import type { DraftRunView, DraftingPanelProps } from "./draftingTypes";

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
    label: "AI Pro",
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

export function DraftingPanel({ project, chapter, api = coreApi }: DraftingPanelProps) {
  const [objective, setObjective] = useState("");
  const [provider, setProvider] = useState<ProviderId>("openai");
  const [selectionMode, setSelectionMode] = useState<SelectionMode>("AUTO");
  const [selectionScope, setSelectionScope] = useState<SelectionScope>("OPERATION");
  const [model, setModel] = useState("gpt-6-astra");
  const [maxCostUsd, setMaxCostUsd] = useState("0.50");
  const [allowPaid, setAllowPaid] = useState(false);
  const [context, setContext] = useState("");
  const [runs, setRuns] = useState<DraftRunView[]>([]);
  const [readiness, setReadiness] = useState<LaunchReadiness | null>(null);
  const [routingState, setRoutingState] = useState<RoutingState | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const approved =
    chapter?.chapter_contract?.authority_status === "APPROVED" ||
    chapter?.chapter_contract?.authority_status === "LOCKED";
  const providers = readiness?.providers ?? routingState?.providers ?? FALLBACK_PROVIDERS;
  const selectedProvider = useMemo(
    () => providers.find((item) => item.id === provider) ?? FALLBACK_PROVIDERS[0],
    [provider, providers],
  );
  const bookPin = routingState?.book_pin ?? null;
  const cost = Number(maxCostUsd);
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

  useEffect(() => {
    let active = true;
    setRuns([]);
    setError(null);
    const tasks: Array<Promise<void>> = [
      api<LaunchReadiness>("GET", "/api/launch/readiness").then((value) => {
        if (active) setReadiness(value);
      }),
      reloadRouting(),
    ];
    if (chapter) {
      tasks.push(
        api<DraftRunView[]>(
          "GET",
          `/api/projects/${project.book_id}/chapters/${chapter.chapter_id}/drafts`,
        ).then((value) => {
          if (active) setRuns(value);
        }),
      );
    }
    void Promise.all(tasks).catch((reason: unknown) => {
      if (active) setError(String(reason));
    });
    return () => {
      active = false;
    };
  }, [api, chapter, project.book_id, reloadRouting]);

  useEffect(() => {
    if (selectionMode !== "MANUAL" || bookPin) return;
    if (!selectedProvider.models.some((item) => item.id === model)) {
      setModel(selectedProvider.models[0]?.id ?? "");
    }
  }, [bookPin, model, selectedProvider, selectionMode]);

  function chooseProvider(next: ProviderId) {
    if (bookPin || next === provider) return;
    setProvider(next);
    setAllowPaid(false);
    if (selectionMode === "MANUAL") {
      const nextProvider = providers.find((item) => item.id === next);
      setModel(nextProvider?.models[0]?.id ?? "");
    }
  }

  async function clearBookPin() {
    setBusy(true);
    setError(null);
    try {
      await api("POST", `/api/projects/${project.book_id}/model-routing/clear-book-pin`);
      setSelectionMode("AUTO");
      setSelectionScope("OPERATION");
      setAllowPaid(false);
      await reloadRouting();
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  async function generate() {
    if (!chapter || !approved || !objective.trim() || !paidReady) return;
    setBusy(true);
    setError(null);
    try {
      const run = await api<DraftRunView>(
        "POST",
        `/api/projects/${project.book_id}/chapters/${chapter.chapter_id}/drafts`,
        {
          section_objective: objective.trim(),
          provider,
          model: selectionMode === "MANUAL" ? model.trim() : null,
          selection_mode: selectionMode,
          selection_scope: selectionMode === "MANUAL" ? selectionScope : null,
          untrusted_context: context.trim() ? [context] : [],
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

  const latest = runs[0] ?? null;
  const latestProviderLabel =
    providers.find((item) => item.id === latest?.provider)?.label ?? latest?.provider;

  return (
    <section className="panel drafting-panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">WRITER · ОГРАНИЧЕННОЕ НАПИСАНИЕ</p>
          <h3>Черновик фрагмента</h3>
        </div>
        <span className="badge draft">ТОЛЬКО ЧЕРНОВИК · НУЖНО РЕШЕНИЕ ЧЕЛОВЕКА</span>
      </div>

      {!chapter && <p className="muted">Сначала выберите главу с утверждённым контрактом.</p>}
      {chapter && !approved && (
        <p className="muted">Перед написанием утвердите контракт этой главы.</p>
      )}

      {chapter && approved && (
        <>
          {bookPin && (
            <div className="selected-topic-summary" role="status">
              <small>На всю книгу закреплена модель</small>
              <strong>{bookPin.provider_label} · {bookPin.model}</strong>
              <span>Writer обязан использовать это закрепление, пока вы его не снимете.</span>
              <button className="ghost" disabled={busy} onClick={() => void clearBookPin()}>
                Снять закрепление на всю книгу
              </button>
            </div>
          )}

          <div className="form-grid">
            <label className="field">
              <span>Задача этого фрагмента</span>
              <textarea
                rows={4}
                value={objective}
                onChange={(event) => setObjective(event.target.value)}
                placeholder="Что именно должен сделать этот один фрагмент главы?"
              />
            </label>
            <div className="field">
              <span>AI-провайдер</span>
              <div className="actions planning-action">
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
              <small>
                {credentialAvailable
                  ? `${selectedProvider.label} готов к платному вызову.`
                  : `${selectedProvider.label} не настроен; запрос будет заблокирован.`}
              </small>
            </div>
            <div className="field">
              <span>Выбор модели</span>
              <div className="actions planning-action">
                <button
                  type="button"
                  className={selectionMode === "AUTO" ? "primary" : "ghost"}
                  disabled={busy || Boolean(bookPin)}
                  onClick={() => {
                    setSelectionMode("AUTO");
                    setSelectionScope("OPERATION");
                    setAllowPaid(false);
                  }}
                >
                  Авто
                </button>
                <button
                  type="button"
                  className={selectionMode === "MANUAL" ? "primary" : "ghost"}
                  disabled={busy || Boolean(bookPin)}
                  onClick={() => {
                    setSelectionMode("MANUAL");
                    setModel(selectedProvider.models[0]?.id ?? "");
                    setAllowPaid(false);
                  }}
                >
                  Ручной
                </button>
              </div>
              <small>
                Авто = BOOK OS выбирает исполнитель именно для операции написания фрагмента.
              </small>
            </div>
            {selectionMode === "MANUAL" && (
              <>
                <label className="field">
                  <span>Модель</span>
                  <select
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
                <div className="field">
                  <span>Где закрепить модель</span>
                  <div className="actions planning-action">
                    <button
                      type="button"
                      className={selectionScope === "OPERATION" ? "primary" : "ghost"}
                      disabled={busy || Boolean(bookPin)}
                      onClick={() => setSelectionScope("OPERATION")}
                    >
                      Только эта операция
                    </button>
                    <button
                      type="button"
                      className={selectionScope === "BOOK" ? "primary" : "ghost"}
                      disabled={busy || Boolean(bookPin)}
                      onClick={() => setSelectionScope("BOOK")}
                    >
                      На всю книгу
                    </button>
                  </div>
                </div>
              </>
            )}
            <label className="field">
              <span>Максимальная стоимость запроса, USD</span>
              <input
                inputMode="decimal"
                value={maxCostUsd}
                onChange={(event) => setMaxCostUsd(event.target.value)}
              />
            </label>
            <label className="field">
              <span>Дополнительный материал — необязательно</span>
              <small>Хранится как данные и не может изменить authority или расширить задачу.</small>
              <textarea
                rows={5}
                value={context}
                onChange={(event) => setContext(event.target.value)}
                placeholder="Можно вставить ограниченный исходный материал для этого фрагмента"
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
              Разрешаю только следующий платный запрос через {selectedProvider.label} с пределом ${maxCostUsd || "0"}.
              После попытки разрешение автоматически сбросится.
            </span>
          </label>
          <div className="actions">
            <button
              className="primary"
              onClick={() => void generate()}
              disabled={busy || !objective.trim() || !paidReady}
            >
              {busy ? "Writer пишет…" : "Создать черновик"}
            </button>
          </div>
        </>
      )}

      {error && <div className="alert inline-alert">{error}</div>}

      {latest && (
        <div className="draft-result">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">ПОСЛЕДНИЙ ЗАПУСК</p>
              <h4>{latest.revision_status ?? latest.run_status}</h4>
            </div>
            <span className="badge draft">{latest.revision_status ?? latest.run_status}</span>
          </div>
          {latest.text && <article className="draft-copy">{latest.text}</article>}
          <dl className="provenance-grid">
            <div>
              <dt>Провайдер / модель</dt>
              <dd>{latestProviderLabel} · {latest.model}</dd>
            </div>
            <div>
              <dt>Маршрутизация</dt>
              <dd>
                {latest.selection_mode}
                {latest.selection_scope ? ` · ${latest.selection_scope}` : ""}
              </dd>
            </div>
            <div>
              <dt>Prompt</dt>
              <dd>{latest.prompt_id} · {latest.prompt_version}</dd>
            </div>
            <div>
              <dt>Задача</dt>
              <dd>{latest.task_id}</dd>
            </div>
            <div>
              <dt>Входная revision</dt>
              <dd>{latest.input_revision_id}</dd>
            </div>
          </dl>
          {latest.routing_rationale && <small className="muted">{latest.routing_rationale}</small>}
          {latest.notes.length > 0 && (
            <ul className="notes-list">{latest.notes.map((note) => <li key={note}>{note}</li>)}</ul>
          )}
        </div>
      )}
    </section>
  );
}
