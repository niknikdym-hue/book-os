import { useCallback, useEffect, useState } from "react";
import { coreApi } from "./api";

type SettingsApi = <T>(
  method: "GET" | "POST" | "PUT",
  path: string,
  body?: unknown,
) => Promise<T>;

type LaunchReadiness = {
  openai_credential_state: "AVAILABLE" | "NOT_AVAILABLE";
};

type Props = {
  api?: SettingsApi;
};

export function OpenAIWorkLevelPanel({ api = coreApi }: Props) {
  const [readiness, setReadiness] = useState<LaunchReadiness | null>(null);
  const [apiKey, setApiKey] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setReadiness(await api<LaunchReadiness>("GET", "/api/launch/readiness"));
  }, [api]);

  useEffect(() => {
    void reload().catch((reason: unknown) => setError(String(reason)));
  }, [reload]);

  async function saveOpenAIKey() {
    if (!apiKey.trim()) return;
    setBusy(true);
    setError(null);
    try {
      await api("POST", "/api/launch/openai-key", { api_key: apiKey.trim() });
      setApiKey("");
      await reload();
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  const available = readiness?.openai_credential_state === "AVAILABLE";

  return (
    <details className="utility-drawer global-advanced-settings" id="openai-settings">
      <summary>Настройки / Advanced</summary>
      <section className="panel" aria-label="Настройки OpenAI">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">СЛУЖЕБНЫЕ НАСТРОЙКИ</p>
            <h3>OpenAI API</h3>
          </div>
          <span className={`badge ${available ? "approved" : "draft"}`}>
            {available ? "ПОДКЛЮЧЁН" : "НЕ ПОДКЛЮЧЁН"}
          </span>
        </div>

        <p className="muted">
          Здесь находится техническое подключение OpenAI. В обычной авторской панели остаются только
          работа над книгой, три режима GPT-6 Astra и ограничение стоимости вызова.
        </p>

        {!available && (
          <div className="credential-setup">
            <label className="field">
              <span>API-ключ OpenAI</span>
              <small>Ключ сохраняется локально в macOS Keychain и не выводится обратно в интерфейс.</small>
              <input
                aria-label="API-ключ OpenAI"
                type="password"
                autoComplete="off"
                value={apiKey}
                onChange={(event) => setApiKey(event.target.value)}
                placeholder="sk-…"
              />
            </label>
            <button
              className="primary"
              type="button"
              disabled={busy || apiKey.trim().length < 10}
              onClick={() => void saveOpenAIKey()}
            >
              {busy ? "Сохраняю…" : "Сохранить OpenAI в Keychain"}
            </button>
          </div>
        )}

        {available && (
          <p className="selected-topic-summary" role="status">
            OpenAI подключён. Смена ключа не требуется для обычной работы над книгой.
          </p>
        )}

        {error && <div className="alert inline-alert">{error}</div>}
      </section>
    </details>
  );
}
