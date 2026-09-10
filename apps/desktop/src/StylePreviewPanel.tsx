import { useCallback, useEffect, useMemo, useState } from "react";
import { coreApi } from "./api";

type ProviderId = "openai" | "yandex";
type SelectionMode = "AUTO" | "MANUAL";
type SelectionScope = "OPERATION" | "BOOK";

type ProfileView = {
  profile_id: string;
  kind: "AUTHOR" | "SERIES" | "STYLE";
  name: string;
  status: "DRAFT" | "APPROVED";
  content: Record<string, unknown>;
};

type ProviderModel = { id: string; label: string };
type ProviderView = { id: ProviderId; label: string; models: ProviderModel[] };

type Readiness = {
  openai_credential_state: "AVAILABLE" | "NOT_AVAILABLE";
  yandex_credential_state?: "AVAILABLE" | "NOT_AVAILABLE";
  providers?: ProviderView[];
};

type PreviewItem = {
  preview_id: string;
  style_profile_id: string;
  style_name: string;
  provider: string;
  provider_label: string;
  model: string;
  selection_mode: string;
  selection_scope: string | null;
  text: string;
};

type PreviewBatch = {
  batch_id: string;
  brief_hash: string;
  per_request_cap_usd: number;
  total_cap_usd: number;
  previews: PreviewItem[];
};

type Props = { bookId: string };

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

export function StylePreviewPanel({ bookId }: Props) {
  const [profiles, setProfiles] = useState<ProfileView[]>([]);
  const [readiness, setReadiness] = useState<Readiness | null>(null);
  const [authorId, setAuthorId] = useState("");
  const [styleIds, setStyleIds] = useState<string[]>([]);
  const [brief, setBrief] = useState("");
  const [provider, setProvider] = useState<ProviderId>("openai");
  const [selectionMode, setSelectionMode] = useState<SelectionMode>("AUTO");
  const [selectionScope, setSelectionScope] = useState<SelectionScope>("OPERATION");
  const [model, setModel] = useState("gpt-6-astra");
  const [costCap, setCostCap] = useState("0.30");
  const [allowPaid, setAllowPaid] = useState(false);
  const [openaiKey, setOpenaiKey] = useState("");
  const [yandexKey, setYandexKey] = useState("");
  const [yandexFolderId, setYandexFolderId] = useState("");
  const [result, setResult] = useState<PreviewBatch | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    const [profileItems, readinessValue] = await Promise.all([
      coreApi<ProfileView[]>("GET", "/api/context/profiles"),
      coreApi<Readiness>("GET", "/api/launch/readiness"),
    ]);
    setProfiles(profileItems);
    setReadiness(readinessValue);
  }, []);

  useEffect(() => {
    void reload().catch((reason: unknown) => setError(String(reason)));
  }, [reload]);

  const authors = profiles.filter(
    (item) => item.kind === "AUTHOR" && item.status === "APPROVED",
  );
  const styles = profiles.filter(
    (item) =>
      item.kind === "STYLE" &&
      (!item.content.author_profile_id || item.content.author_profile_id === authorId),
  );
  const providers = readiness?.providers ?? FALLBACK_PROVIDERS;
  const selectedProvider = useMemo(
    () => providers.find((item) => item.id === provider) ?? FALLBACK_PROVIDERS[0],
    [provider, providers],
  );
  const credentialAvailable =
    provider === "openai"
      ? readiness?.openai_credential_state === "AVAILABLE"
      : readiness?.yandex_credential_state === "AVAILABLE";
  const cap = Number(costCap);
  const totalCap = Number.isFinite(cap) ? cap * styleIds.length : 0;
  const readyToRun =
    authorId.length > 0 &&
    styleIds.length >= 2 &&
    styleIds.length <= 3 &&
    brief.trim().length >= 20 &&
    credentialAvailable &&
    Number.isFinite(cap) &&
    cap > 0 &&
    allowPaid &&
    (selectionMode === "AUTO" || model.length > 0);

  function toggleStyle(styleId: string) {
    setResult(null);
    setStyleIds((current) => {
      if (current.includes(styleId)) return current.filter((item) => item !== styleId);
      if (current.length >= 3) return current;
      return [...current, styleId];
    });
  }

  function selectProvider(next: ProviderId) {
    setProvider(next);
    setAllowPaid(false);
    setResult(null);
    const nextProvider = providers.find((item) => item.id === next);
    if (selectionMode === "MANUAL") setModel(nextProvider?.models[0]?.id ?? "");
  }

  async function saveProviderCredential() {
    setBusy(true);
    setError(null);
    try {
      if (provider === "openai") {
        await coreApi("POST", "/api/launch/openai-key", { api_key: openaiKey.trim() });
        setOpenaiKey("");
      } else {
        await coreApi("POST", "/api/launch/yandex-credentials", {
          api_key: yandexKey.trim(),
          folder_id: yandexFolderId.trim(),
        });
        setYandexKey("");
        setYandexFolderId("");
      }
      await reload();
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  async function generate() {
    if (!readyToRun) return;
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const value = await coreApi<PreviewBatch>(
        "POST",
        `/api/projects/${bookId}/style-previews`,
        {
          author_profile_id: authorId,
          style_profile_ids: styleIds,
          content_brief: brief.trim(),
          provider,
          selection_mode: selectionMode,
          selection_scope: selectionMode === "MANUAL" ? selectionScope : null,
          model: selectionMode === "MANUAL" ? model : null,
          max_output_tokens: 900,
          max_cost_usd_per_request: cap,
        },
      );
      setResult(value);
    } catch (reason) {
      setError(String(reason));
    } finally {
      setAllowPaid(false);
      setBusy(false);
    }
  }

  async function deletePreview(previewId: string) {
    if (!window.confirm("Удалить этот тестовый вариант с этого Mac? Книга и её настройки не изменятся.")) return;
    setBusy(true);
    try {
      await coreApi("DELETE", `/api/projects/${bookId}/style-previews/${previewId}`);
      setResult((current) => current ? { ...current, previews: current.previews.filter((item) => item.preview_id !== previewId) } : current);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel" aria-label="Сравнение манер письма">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">STYLE PREVIEW</p>
          <h3>Сравнить манеры письма на одном тексте</h3>
        </div>
        <span className="badge draft">НЕ ВХОДИТ В РУКОПИСЬ</span>
      </div>
      <p className="muted">
        Один и тот же содержательный brief будет написан в 2–3 выбранных Style Profiles. Это только
        материал для вашего выбора; ни один пример не становится текстом книги автоматически.
      </p>

      <div className="form-grid">
        <label className="field">
          <span>Автор</span>
          <select
            value={authorId}
            onChange={(event) => {
              setAuthorId(event.target.value);
              setStyleIds([]);
              setResult(null);
            }}
          >
            <option value="">Выберите утверждённого автора</option>
            {authors.map((item) => (
              <option key={item.profile_id} value={item.profile_id}>{item.name}</option>
            ))}
          </select>
        </label>
        <div className="field">
          <span>Манеры для сравнения — выберите 2 или 3</span>
          {styles.length === 0 ? (
            <small>Сначала создайте Style Profiles в блоке выше.</small>
          ) : (
            styles.map((item) => (
              <label key={item.profile_id}>
                <input
                  type="checkbox"
                  checked={styleIds.includes(item.profile_id)}
                  onChange={() => toggleStyle(item.profile_id)}
                />
                {item.name} {item.status === "DRAFT" ? "· черновик" : "· утверждён"}
              </label>
            ))
          )}
          <button className="ghost" type="button" disabled={busy} onClick={() => void reload()}>
            Обновить список профилей
          </button>
        </div>
      </div>

      <label className="field">
        <span>Одинаковый содержательный brief</span>
        <textarea
          rows={5}
          value={brief}
          onChange={(event) => setBrief(event.target.value)}
          placeholder="Например: показать сцену, в которой руководитель обнаруживает, что все важные решения команды незаметно вернулись к нему на согласование, и вывести из неё управленческий механизм."
        />
      </label>

      <div className="planning-step">
        <h4>Какой AI пишет примеры</h4>
        <div className="actions planning-action">
          {providers.map((item) => (
            <button
              key={item.id}
              type="button"
              className={provider === item.id ? "primary" : "ghost"}
              aria-pressed={provider === item.id}
              onClick={() => selectProvider(item.id)}
            >
              {item.label}
            </button>
          ))}
        </div>
        <div className="actions planning-action">
          <button
            type="button"
            className={selectionMode === "AUTO" ? "primary" : "ghost"}
            aria-pressed={selectionMode === "AUTO"}
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
            onClick={() => {
              setSelectionMode("MANUAL");
              setModel(selectedProvider.models[0]?.id ?? "");
              setAllowPaid(false);
            }}
          >
            Ручной выбор
          </button>
        </div>

        {selectionMode === "MANUAL" && (
          <div className="form-grid">
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
                  name="preview-model-scope"
                  checked={selectionScope === "OPERATION"}
                  onChange={() => setSelectionScope("OPERATION")}
                />
                Только на Style Preview
              </label>
              <label>
                <input
                  type="radio"
                  name="preview-model-scope"
                  checked={selectionScope === "BOOK"}
                  onChange={() => setSelectionScope("BOOK")}
                />
                На всю книгу
              </label>
            </fieldset>
          </div>
        )}
      </div>

      {!credentialAvailable && (
        <div className="credential-setup">
          {provider === "openai" ? (
            <label className="field">
              <span>Ключ AI Pro</span>
              <input
                type="password"
                autoComplete="off"
                value={openaiKey}
                onChange={(event) => setOpenaiKey(event.target.value)}
              />
            </label>
          ) : (
            <>
              <label className="field">
                <span>API-ключ AI Ya</span>
                <input
                  type="password"
                  autoComplete="off"
                  value={yandexKey}
                  onChange={(event) => setYandexKey(event.target.value)}
                />
              </label>
              <label className="field">
                <span>Folder ID Yandex Cloud</span>
                <input
                  value={yandexFolderId}
                  onChange={(event) => setYandexFolderId(event.target.value)}
                />
              </label>
            </>
          )}
          <button
            className="primary"
            disabled={
              busy ||
              (provider === "openai"
                ? openaiKey.trim().length < 10
                : yandexKey.trim().length < 10 || yandexFolderId.trim().length < 3)
            }
            onClick={() => void saveProviderCredential()}
          >
            Сохранить {selectedProvider.label} в Keychain
          </button>
        </div>
      )}

      <label className="field">
        <span>Максимальная стоимость одного примера, USD</span>
        <input inputMode="decimal" value={costCap} onChange={(event) => setCostCap(event.target.value)} />
        <small>
          Сейчас выбрано {styleIds.length} манер. Общий жёсткий предел — до ${totalCap.toFixed(2)}.
        </small>
      </label>
      <label className="paid-approval">
        <input
          type="checkbox"
          checked={allowPaid}
          onChange={(event) => setAllowPaid(event.target.checked)}
        />
        <span>
          Разрешаю только этот Style Preview: {styleIds.length} платных запросов через {selectedProvider.label},
          каждый не дороже ${costCap || "0"}. После попытки разрешение сбросится.
        </span>
      </label>
      <div className="actions">
        <button className="primary" disabled={busy || !readyToRun} onClick={() => void generate()}>
          {busy ? "Генерирую примеры…" : "Показать варианты текста"}
        </button>
      </div>

      {result && (
        <div className="form-grid">
          {result.previews.map((item) => (
            <article className="panel" key={item.preview_id}>
              <div className="panel-heading">
                <h4>{item.style_name}</h4>
                <span className="badge draft">ПРИМЕР</span>
              </div>
              <p className="manuscript-text">{item.text}</p>
              <small className="muted">
                {item.provider_label} · {item.model} · {item.selection_mode === "AUTO" ? "Авто" : "Ручной"}
              </small>
              <button className="ghost small" type="button" disabled={busy} onClick={() => void deletePreview(item.preview_id)}>
                Удалить тест
              </button>
            </article>
          ))}
        </div>
      )}
      {error && <div className="alert inline-alert">{error}</div>}
    </section>
  );
}
