import { useCallback, useEffect, useMemo, useState } from "react";
import { coreApi } from "./api";

type AntiJunkEntry = {
  entry_id: string;
  value: string;
  kind: "BANNED_TEMPLATE" | "CONTEXT_REVIEW";
  source: "SYSTEM" | "USER";
  created_at: string | null;
};

export function AntiJunkPanel() {
  const [entries, setEntries] = useState<AntiJunkEntry[]>([]);
  const [value, setValue] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setEntries(await coreApi<AntiJunkEntry[]>("GET", "/api/anti-junk"));
  }, []);

  useEffect(() => {
    void reload().catch((reason: unknown) => setError(String(reason)));
  }, [reload]);

  const systemCount = useMemo(
    () => entries.filter((entry) => entry.source === "SYSTEM").length,
    [entries],
  );
  const userCount = entries.length - systemCount;

  async function add() {
    if (!value.trim()) return;
    setBusy(true);
    setError(null);
    try {
      await coreApi("POST", "/api/anti-junk", {
        value: value.trim(),
        kind: "BANNED_TEMPLATE",
      });
      setValue("");
      await reload();
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  async function remove(entryId: string) {
    setBusy(true);
    setError(null);
    try {
      await coreApi("POST", `/api/anti-junk/${entryId}/remove`);
      await reload();
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel anti-junk-panel" aria-label="Словарь мусора">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">КОНТРОЛЬ ПРОЗЫ</p>
          <h3>Словарь мусора</h3>
        </div>
        <span className="badge">{entries.length} записей</span>
      </div>
      <p className="muted">
        Новая запись сразу становится ограничением для Writer и проверкой BookBench. Системные
        правила защищены; ваши записи можно удалить.
      </p>
      <div className="anti-junk-add">
        <label className="field">
          <span>Добавить мусорное слово, фразу или шаблон</span>
          <input
            value={value}
            onChange={(event) => setValue(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") void add();
            }}
            placeholder="Например: эта книга не о том"
          />
        </label>
        <button className="primary" onClick={() => void add()} disabled={busy || !value.trim()}>
          Добавить
        </button>
      </div>
      {error && <div className="alert inline-alert">{error}</div>}
      <details className="anti-junk-list">
        <summary>
          Показать словарь · системных {systemCount} · ваших {userCount}
        </summary>
        <div className="anti-junk-entries">
          {entries.map((entry) => (
            <div className="anti-junk-entry" key={entry.entry_id}>
              <div>
                <strong>{entry.value}</strong>
                <small>
                  {entry.kind === "BANNED_TEMPLATE" ? "запрещённый шаблон" : "проверять контекст"}
                  {entry.source === "SYSTEM" ? " · системный" : " · добавлено вами"}
                </small>
              </div>
              {entry.source === "USER" && (
                <button className="ghost small" disabled={busy} onClick={() => void remove(entry.entry_id)}>
                  Удалить
                </button>
              )}
            </div>
          ))}
        </div>
      </details>
    </section>
  );
}
