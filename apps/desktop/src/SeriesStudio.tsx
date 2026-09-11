import { useCallback, useEffect, useMemo, useState } from "react";
import { coreApi } from "./api";

type ProfileKind = "AUTHOR" | "SERIES" | "STYLE";
type ProfileView = {
  profile_id: string;
  kind: ProfileKind;
  name: string;
  status: "DRAFT" | "APPROVED";
  content: Record<string, unknown>;
};

type SeriesModelChoice = "ASTRA_MEDIUM" | "ASTRA_HIGH" | "ASTRA_XHIGH" | "SOL";

type SeriesCreateResult = {
  profile: ProfileView;
  provider: "openai";
  model: string;
  reasoning_effort: string | null;
};

type SeriesReference = {
  reference_id: string;
  series_profile_id: string;
  style_profile_id: string;
  title: string;
  filename: string;
  format: "TXT" | "MARKDOWN" | "DOCX";
  original_sha256: string;
  text_sha256: string;
  characters: number;
  paragraphs: number;
  usage_policy: string;
  created_at: string;
};

const MODEL_OPTIONS: readonly { value: SeriesModelChoice; label: string }[] = [
  { value: "ASTRA_MEDIUM", label: "GPT-6 Astra Medium" },
  { value: "ASTRA_HIGH", label: "GPT-6 Astra High" },
  { value: "ASTRA_XHIGH", label: "GPT-6 Astra Extra High" },
  { value: "SOL", label: "GPT-5.6 Sol" },
];

function stringList(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
}

function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  const chunkSize = 0x8000;
  let binary = "";
  for (let index = 0; index < bytes.length; index += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(index, index + chunkSize));
  }
  return btoa(binary);
}

export function SeriesStudio() {
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState<"NEW" | "EXISTING">("NEW");
  const [profiles, setProfiles] = useState<ProfileView[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [authorId, setAuthorId] = useState("");
  const [brief, setBrief] = useState("");
  const [modelChoice, setModelChoice] = useState<SeriesModelChoice>("ASTRA_HIGH");
  const [maxCostUsd, setMaxCostUsd] = useState("1.50");
  const [allowPaid, setAllowPaid] = useState(false);
  const [createdSeries, setCreatedSeries] = useState<ProfileView | null>(null);

  const [seriesId, setSeriesId] = useState("");
  const [referenceTitle, setReferenceTitle] = useState("");
  const [referenceFile, setReferenceFile] = useState<File | null>(null);
  const [referenceConfirmed, setReferenceConfirmed] = useState(false);
  const [currentReference, setCurrentReference] = useState<SeriesReference | null>(null);

  const reloadProfiles = useCallback(async () => {
    setProfiles(await coreApi<ProfileView[]>("GET", "/api/context/profiles"));
  }, []);

  useEffect(() => {
    if (!open) return;
    void reloadProfiles().catch((reason: unknown) => setError(String(reason)));
  }, [open, reloadProfiles]);

  const authors = useMemo(
    () => profiles.filter((item) => item.kind === "AUTHOR" && item.status === "APPROVED"),
    [profiles],
  );
  const series = useMemo(
    () => profiles.filter((item) => item.kind === "SERIES" && item.status === "APPROVED"),
    [profiles],
  );
  const styles = useMemo(
    () => profiles.filter((item) => item.kind === "STYLE" && item.status === "APPROVED"),
    [profiles],
  );

  const generatedRules = createdSeries
    ? stringList(createdSeries.content.cross_book_uniqueness_rules)
    : [];
  const generatedBooks = createdSeries ? stringList(createdSeries.content.planned_books) : [];
  const currentReferenceStyle = currentReference
    ? styles.find((item) => item.profile_id === currentReference.style_profile_id) ?? null
    : null;

  useEffect(() => {
    setCurrentReference(null);
    if (!seriesId || !open || mode !== "EXISTING") return;
    void coreApi<SeriesReference | null>(
      "GET",
      `/api/series/${seriesId}/delivery-reference`,
    )
      .then(setCurrentReference)
      .catch((reason: unknown) => setError(String(reason)));
  }, [mode, open, seriesId]);

  async function createSeries() {
    const cost = Number(maxCostUsd);
    if (!authorId || brief.trim().length < 20 || !allowPaid || !Number.isFinite(cost) || cost <= 0) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const result = await coreApi<SeriesCreateResult>("POST", "/api/series/create-with-ai", {
        author_profile_id: authorId,
        brief: brief.trim(),
        model_choice: modelChoice,
        max_cost_usd: cost,
        max_output_tokens: 5000,
        owner_authorizes_paid_call: true,
      });
      setCreatedSeries(result.profile);
      setAllowPaid(false);
      await reloadProfiles();
    } catch (reason) {
      setAllowPaid(false);
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  async function approveCreatedSeries() {
    if (!createdSeries) return;
    setBusy(true);
    setError(null);
    try {
      const approved = await coreApi<ProfileView>(
        "POST",
        `/api/context/profiles/${createdSeries.profile_id}/approve`,
      );
      setCreatedSeries(approved);
      setSeriesId(approved.profile_id);
      await reloadProfiles();
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  async function uploadReference() {
    if (!seriesId || !referenceFile || !referenceConfirmed) return;
    if (referenceFile.size > 8 * 1024 * 1024) {
      setError("Файл эталона больше локального лимита 8 МБ.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const contentBase64 = arrayBufferToBase64(await referenceFile.arrayBuffer());
      const reference = await coreApi<SeriesReference>(
        "POST",
        `/api/series/${seriesId}/delivery-reference`,
        {
          filename: referenceFile.name,
          content_base64: contentBase64,
          title: referenceTitle.trim(),
          role: "DELIVERY_STYLE_REFERENCE",
          actor: "OWNER",
          owner_approves_derived_style: true,
        },
      );
      setCurrentReference(reference);
      setReferenceConfirmed(false);
      await reloadProfiles();
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <button
        type="button"
        className="series-studio-launcher"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        Серии
      </button>

      {open && (
        <div className="series-studio-backdrop" role="presentation" onMouseDown={() => setOpen(false)}>
          <aside
            className="series-studio-drawer"
            aria-label="Series Studio"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <header className="series-studio-header">
              <div>
                <p className="eyebrow">SERIES STUDIO</p>
                <h2>Работа с серией</h2>
              </div>
              <button type="button" className="ghost" onClick={() => setOpen(false)}>Закрыть</button>
            </header>

            <p className="series-studio-rule">
              Книги одной серии не являются клонами. Общими могут быть уровень и узнаваемая манера
              подачи; темы, тезисы, механизмы, примеры, аналогии и композиция каждой книги уникальны.
            </p>

            <div className="series-studio-tabs" role="tablist" aria-label="Сценарий серии">
              <button
                type="button"
                className={mode === "NEW" ? "active" : ""}
                onClick={() => setMode("NEW")}
              >
                Создать серию с нуля
              </button>
              <button
                type="button"
                className={mode === "EXISTING" ? "active" : ""}
                onClick={() => setMode("EXISTING")}
              >
                Обновляю существующую серию
              </button>
            </div>

            {mode === "NEW" && (
              <section className="series-studio-section">
                <h3>Новая серия</h3>
                <p className="muted">
                  Astra или Sol предложат позиционирование, карту книг и границы между ними. BOOK OS
                  автоматически добавит обязательные cross-book uniqueness и SeriesBench требования.
                </p>

                <label className="field">
                  <span>Автор / псевдоним</span>
                  <select value={authorId} onChange={(event) => setAuthorId(event.target.value)}>
                    <option value="">Выберите утверждённого автора</option>
                    {authors.map((item) => (
                      <option key={item.profile_id} value={item.profile_id}>{item.name}</option>
                    ))}
                  </select>
                </label>

                <label className="field">
                  <span>Что это за серия?</span>
                  <textarea
                    rows={6}
                    value={brief}
                    onChange={(event) => setBrief(event.target.value)}
                    placeholder="Опишите аудиторию, задачу серии, какие книги уже задуманы и чем они должны отличаться друг от друга."
                  />
                </label>

                <div className="series-studio-grid">
                  <label className="field">
                    <span>Модель</span>
                    <select value={modelChoice} onChange={(event) => setModelChoice(event.target.value as SeriesModelChoice)}>
                      {MODEL_OPTIONS.map((item) => (
                        <option key={item.value} value={item.value}>{item.label}</option>
                      ))}
                    </select>
                  </label>
                  <label className="field">
                    <span>Лимит одного запроса, $</span>
                    <input
                      inputMode="decimal"
                      value={maxCostUsd}
                      onChange={(event) => {
                        setMaxCostUsd(event.target.value);
                        setAllowPaid(false);
                      }}
                    />
                  </label>
                </div>

                <label className="paid-approval">
                  <input
                    type="checkbox"
                    checked={allowPaid}
                    onChange={(event) => setAllowPaid(event.target.checked)}
                  />
                  <span>Разрешаю один платный вызов выбранной модели с указанным лимитом.</span>
                </label>

                <button
                  type="button"
                  className="primary"
                  disabled={busy || !authorId || brief.trim().length < 20 || !allowPaid}
                  onClick={() => void createSeries()}
                >
                  {busy ? "Модель работает…" : "Предложить архитектуру серии"}
                </button>

                {createdSeries && (
                  <article className="series-studio-result">
                    <div className="panel-heading">
                      <div>
                        <p className="eyebrow">ПРЕДЛОЖЕНИЕ</p>
                        <h3>{createdSeries.name}</h3>
                      </div>
                      <span className={`badge ${createdSeries.status === "APPROVED" ? "approved" : "draft"}`}>
                        {createdSeries.status === "APPROVED" ? "УТВЕРЖДЕНА" : "ЧЕРНОВИК"}
                      </span>
                    </div>
                    {typeof createdSeries.content.purpose_positioning === "string" && (
                      <p>{createdSeries.content.purpose_positioning}</p>
                    )}
                    {generatedBooks.length > 0 && (
                      <div>
                        <strong>Книги:</strong>
                        <ol>{generatedBooks.map((item) => <li key={item}>{item}</li>)}</ol>
                      </div>
                    )}
                    {generatedRules.length > 0 && (
                      <details>
                        <summary>Правила уникальности ({generatedRules.length})</summary>
                        <ul>{generatedRules.map((item) => <li key={item}>{item}</li>)}</ul>
                      </details>
                    )}
                    {createdSeries.status === "DRAFT" && (
                      <button type="button" className="primary" disabled={busy} onClick={() => void approveCreatedSeries()}>
                        Утвердить Series Profile
                      </button>
                    )}
                  </article>
                )}
              </section>
            )}

            {mode === "EXISTING" && (
              <section className="series-studio-section">
                <h3>Существующая серия</h3>
                <p className="muted">
                  Загрузите уже обновлённую книгу только как эталон манеры подачи и уровня качества.
                  BOOK OS не использует её как донор содержания для других книг.
                </p>

                <label className="field">
                  <span>Серия</span>
                  <select value={seriesId} onChange={(event) => setSeriesId(event.target.value)}>
                    <option value="">Выберите утверждённую серию</option>
                    {series.map((item) => (
                      <option key={item.profile_id} value={item.profile_id}>{item.name}</option>
                    ))}
                  </select>
                </label>

                {currentReference && (
                  <div className="series-reference-current">
                    <strong>Активный эталон: {currentReference.title}</strong>
                    <span>
                      {currentReference.characters.toLocaleString("ru-RU")} знаков · {currentReference.format}
                    </span>
                    <small>
                      Профиль манеры: {currentReferenceStyle?.name ?? currentReference.style_profile_id}
                    </small>
                  </div>
                )}

                <label className="field">
                  <span>Обновлённая книга-эталон</span>
                  <input
                    type="file"
                    accept=".txt,.md,.markdown,.docx,text/plain,text/markdown,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    onChange={(event) => setReferenceFile(event.target.files?.[0] ?? null)}
                  />
                  <small>TXT, Markdown или DOCX · до 8 МБ · файл хранится локально.</small>
                </label>

                <label className="field">
                  <span>Название эталонной книги — необязательно</span>
                  <input
                    value={referenceTitle}
                    onChange={(event) => setReferenceTitle(event.target.value)}
                    placeholder="Например: Как продавать услуги — обновлённая редакция"
                  />
                </label>

                <label className="paid-approval series-reference-confirm">
                  <input
                    type="checkbox"
                    checked={referenceConfirmed}
                    onChange={(event) => setReferenceConfirmed(event.target.checked)}
                  />
                  <span>
                    Подтверждаю: эта книга задаёт только манеру подачи и уровень. Другие книги серии
                    должны оставаться уникальными без повторов, пересечений, примеров и аналогий.
                  </span>
                </label>

                <button
                  type="button"
                  className="primary"
                  disabled={busy || !seriesId || !referenceFile || !referenceConfirmed}
                  onClick={() => void uploadReference()}
                >
                  {busy ? "Загружаю…" : "Закрепить как эталон манеры подачи"}
                </button>

                {currentReference && (
                  <p className="series-studio-success">
                    Эталон закреплён. Для следующей книги выберите созданный профиль манеры
                    «{currentReferenceStyle?.name ?? "эталон подачи серии"}»; content-уникальность
                    продолжает контролироваться отдельными правилами серии.
                  </p>
                )}
              </section>
            )}

            {error && <div className="alert inline-alert">{error}</div>}
          </aside>
        </div>
      )}
    </>
  );
}
