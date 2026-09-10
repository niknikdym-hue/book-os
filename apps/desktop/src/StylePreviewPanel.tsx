import { useCallback, useEffect, useMemo, useState } from "react";
import { coreApi } from "./api";
import { uniqueProfileNames } from "./profileOptions";

type ProfileView = {
  profile_id: string;
  kind: "AUTHOR" | "SERIES" | "STYLE";
  name: string;
  status: "DRAFT" | "APPROVED";
  content: Record<string, unknown>;
  updated_at: string;
};

type Readiness = {
  openai_credential_state: "AVAILABLE" | "NOT_AVAILABLE";
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

export function StylePreviewPanel({ bookId }: Props) {
  const [profiles, setProfiles] = useState<ProfileView[]>([]);
  const [readiness, setReadiness] = useState<Readiness | null>(null);
  const [authorId, setAuthorId] = useState("");
  const [styleIds, setStyleIds] = useState<string[]>([]);
  const [brief, setBrief] = useState("");
  const [costCap, setCostCap] = useState("0.30");
  const [allowPaid, setAllowPaid] = useState(false);
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

  const authors = useMemo(
    () =>
      uniqueProfileNames(
        profiles.filter((item) => item.kind === "AUTHOR" && item.status === "APPROVED"),
      ),
    [profiles],
  );
  const styles = profiles.filter(
    (item) =>
      item.kind === "STYLE" &&
      (!item.content.author_profile_id || item.content.author_profile_id === authorId),
  );
  const credentialAvailable = readiness?.openai_credential_state === "AVAILABLE";
  const cap = Number(costCap);
  const totalCap = Number.isFinite(cap) ? cap * styleIds.length : 0;
  const readyToRun =
    authorId.length > 0 &&
    styleIds.length >= 1 &&
    styleIds.length <= 3 &&
    brief.trim().length >= 20 &&
    credentialAvailable &&
    Number.isFinite(cap) &&
    cap > 0 &&
    allowPaid;

  function toggleStyle(styleId: string) {
    setResult(null);
    setStyleIds((current) => {
      if (current.includes(styleId)) return current.filter((item) => item !== styleId);
      if (current.length >= 3) return current;
      return [...current, styleId];
    });
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
          provider: "openai",
          selection_mode: "MANUAL",
          selection_scope: "OPERATION",
          model: "gpt-6-astra",
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
    <section className="panel" aria-label="Пробный вариант текста">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">ПРОБНЫЙ ВАРИАНТ</p>
          <h3>Примерить настройки до работы над книгой</h3>
        </div>
        <span className="badge draft">НЕ ВХОДИТ В РУКОПИСЬ</span>
      </div>
      <p className="muted">
        Astra создаст короткий отдельный пример по выбранным настройкам. Он не станет частью рукописи;
        его можно сохранить для сравнения или удалить с Mac.
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
          <span>Манера письма — выберите одну или несколько для сравнения</span>
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
        <h4>Модель для пробного варианта</h4>
        <p className="selected-topic-summary">GPT-6 Astra · настройки пробного текста не закрепляют модель для всей книги.</p>
      </div>

      {!credentialAvailable && <div className="alert inline-alert">OpenAI ещё не подключён на этом Mac.</div>}

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
          Разрешаю только этот пробный вариант: {styleIds.length} платных запросов через OpenAI,
          каждый не дороже ${costCap || "0"}. После попытки разрешение сбросится.
        </span>
      </label>
      <div className="actions">
        <button className="primary" disabled={busy || !readyToRun} onClick={() => void generate()}>
          {busy ? "Генерирую пробный вариант…" : "Создать тестовый вариант"}
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
                {item.provider_label} · {item.model}
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
