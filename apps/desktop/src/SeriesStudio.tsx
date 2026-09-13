import { useCallback, useEffect, useMemo, useState } from "react";
import { coreApi } from "./api";
import { uniqueProfileNames } from "./profileOptions";

type ProfileKind = "AUTHOR" | "SERIES" | "STYLE";
type ProfileView = {
  profile_id: string;
  kind: ProfileKind;
  name: string;
  status: "DRAFT" | "APPROVED";
  content: Record<string, unknown>;
  updated_at: string;
};

type SeriesModelChoice = "AUTO" | "ASTRA_MEDIUM" | "ASTRA_HIGH" | "ASTRA_XHIGH" | "SOL";

type SeriesCreateResult = {
  profile: ProfileView;
  concepts: ProfileView[];
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
  { value: "AUTO", label: "Автоматически" },
  { value: "ASTRA_MEDIUM", label: "GPT-6 Astra Medium" },
  { value: "ASTRA_HIGH", label: "GPT-6 Astra High" },
  { value: "ASTRA_XHIGH", label: "GPT-6 Astra Extra High" },
  { value: "SOL", label: "GPT-5.6 Sol" },
];

type SeriesWorkspace = {
  series_profile_id: string;
  name: string;
  profile_status: string;
  profile_revision: number;
  territory: string;
  books: Array<{
    book_id: string;
    ordinal: number;
    title: string;
    unique_idea: string;
    status: string;
    source_kind: string;
    passport_hash: string;
    passport_approved: boolean;
    imported_sources?: Array<{
      source_id: string;
      filename: string;
      format: string;
      analysis_status: string;
      analysis: { characters?: number; headings?: string[]; tables?: number; visuals?: number; warnings?: string[] };
    }>;
  }>;
  map: null | {
    map_hash: string;
    status: "PASS" | "ATTENTION" | "BLOCKING";
    approved: boolean;
    current: boolean;
    findings: Array<Record<string, unknown>>;
  };
};

type SeriesOutputs = {
  complete_manuscripts: boolean;
  editorial_and_litres: boolean;
  audio_editions: boolean;
  descriptions: boolean;
  series_and_book_passports: boolean;
  difference_map: boolean;
  visual_materials: boolean;
  sources_and_freshness: boolean;
  next_books_plan: boolean;
};

const DEFAULT_SERIES_OUTPUTS: SeriesOutputs = {
  complete_manuscripts: false,
  editorial_and_litres: false,
  audio_editions: false,
  descriptions: true,
  series_and_book_passports: true,
  difference_map: true,
  visual_materials: false,
  sources_and_freshness: true,
  next_books_plan: true,
};

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

type Props = {
  embedded?: boolean;
  initialMode?: "NEW" | "IMPORT" | "BOOK_OS";
};

export function SeriesStudio({ embedded = false, initialMode = "NEW" }: Props = {}) {
  const [open, setOpen] = useState(embedded);
  const [mode, setMode] = useState<"NEW" | "IMPORT" | "BOOK_OS">(initialMode);
  const [profiles, setProfiles] = useState<ProfileView[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [authorId, setAuthorId] = useState("");
  const [brief, setBrief] = useState("");
  const [modelChoice, setModelChoice] = useState<SeriesModelChoice>("AUTO");
  const [maxCostUsd, setMaxCostUsd] = useState("1.50");
  const [allowPaid, setAllowPaid] = useState(false);
  const [createdSeries, setCreatedSeries] = useState<ProfileView | null>(null);
  const [createdConcepts, setCreatedConcepts] = useState<ProfileView[]>([]);

  const [seriesId, setSeriesId] = useState("");
  const [referenceTitle, setReferenceTitle] = useState("");
  const [referenceFile, setReferenceFile] = useState<File | null>(null);
  const [referenceConfirmed, setReferenceConfirmed] = useState(false);
  const [currentReference, setCurrentReference] = useState<SeriesReference | null>(null);
  const [workspaces, setWorkspaces] = useState<SeriesWorkspace[]>([]);
  const [externalSeriesName, setExternalSeriesName] = useState("");
  const [externalAudience, setExternalAudience] = useState("");
  const [externalPromise, setExternalPromise] = useState("");
  const [externalTerritory, setExternalTerritory] = useState("");
  const [externalBookTitle, setExternalBookTitle] = useState("");
  const [externalBookIdea, setExternalBookIdea] = useState("");
  const [externalBookFile, setExternalBookFile] = useState<File | null>(null);
  const [additionalExternalBooks, setAdditionalExternalBooks] = useState<Array<{
    title: string;
    idea: string;
    file: File | null;
  }>>([]);
  const [rightsStatus, setRightsStatus] = useState("AUTHOR_MANUSCRIPT");
  const [seriesOutputs, setSeriesOutputs] = useState<SeriesOutputs>(DEFAULT_SERIES_OUTPUTS);
  const [seriesExportPath, setSeriesExportPath] = useState<string | null>(null);

  const reloadProfiles = useCallback(async () => {
    const [availableProfiles, availableWorkspaces] = await Promise.all([
      coreApi<ProfileView[]>("GET", "/api/context/profiles"),
      coreApi<SeriesWorkspace[]>("GET", "/api/series/workspaces"),
    ]);
    setProfiles(availableProfiles);
    setWorkspaces(availableWorkspaces);
  }, []);

  useEffect(() => {
    if (!open) return;
    void reloadProfiles().catch((reason: unknown) => setError(String(reason)));
  }, [open, reloadProfiles]);

  useEffect(() => {
    if (!embedded) return;
    setOpen(true);
    setMode(initialMode);
  }, [embedded, initialMode]);

  const authors = useMemo(
    () =>
      uniqueProfileNames(
        profiles.filter((item) => item.kind === "AUTHOR" && item.status === "APPROVED"),
      ),
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
    if (!seriesId || !open || mode !== "IMPORT") return;
    void coreApi<SeriesReference | null>(
      "GET",
      `/api/series/${seriesId}/delivery-reference`,
    )
      .then(setCurrentReference)
      .catch((reason: unknown) => setError(String(reason)));
  }, [mode, open, seriesId]);

  async function importExternalSeries() {
    if (
      !authorId ||
      !externalSeriesName.trim() ||
      !externalBookTitle.trim() ||
      !externalBookIdea.trim() ||
      !externalBookFile
    ) return;
    setBusy(true);
    setError(null);
    try {
      const draft = await coreApi<ProfileView>("POST", "/api/series/workspaces", {
        series_name: externalSeriesName.trim(),
        author_profile_id: authorId,
        audience: externalAudience.trim(),
        promise: externalPromise.trim(),
        territory: externalTerritory.trim(),
        prohibited_territories: [],
      });
      const approved = await coreApi<ProfileView>(
        "POST",
        `/api/context/profiles/${draft.profile_id}/approve`,
      );
      const importedBooks = [
        { title: externalBookTitle, idea: externalBookIdea, file: externalBookFile },
        ...additionalExternalBooks,
      ];
      for (const [index, item] of importedBooks.entries()) {
        if (!item.file || !item.title.trim() || !item.idea.trim()) continue;
        const book = await coreApi<{ book_id: string }>(
          "POST",
          `/api/series/${approved.profile_id}/books`,
          {
            title: item.title.trim(),
            ordinal: index + 1,
            unique_idea: item.idea.trim(),
            reader_problem: item.idea.trim(),
            reader_result: externalPromise.trim() || item.idea.trim(),
            unique_mechanism: item.idea.trim(),
            excluded_topics: [],
            source_kind: "IMPORTED",
          },
        );
        await coreApi(
          "POST",
          `/api/series/${approved.profile_id}/books/${book.book_id}/imports`,
          {
            filename: item.file.name,
            content_base64: arrayBufferToBase64(await item.file.arrayBuffer()),
            rights_status: rightsStatus,
          },
        );
      }
      setSeriesId(approved.profile_id);
      await reloadProfiles();
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

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
      setCreatedConcepts(result.concepts);
      setAllowPaid(false);
      await reloadProfiles();
    } catch (reason) {
      setAllowPaid(false);
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  async function loadServicesPromotionPreset() {
    if (!authorId) return;
    setBusy(true);
    setError(null);
    try {
      await coreApi("POST", "/api/series/presets/services-promotion", {
        author_profile_id: authorId,
      });
      await reloadProfiles();
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  async function exportSeries(seriesProfileId: string) {
    setBusy(true);
    setError(null);
    try {
      const result = await coreApi<{ output_directory: string }>(
        "POST",
        `/api/series/${seriesProfileId}/exports`,
        seriesOutputs,
      );
      setSeriesExportPath(result.output_directory);
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  async function analyzeSeries(seriesProfileId: string) {
    setBusy(true);
    setError(null);
    try {
      await coreApi("POST", `/api/series/${seriesProfileId}/analyze`);
      await reloadProfiles();
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  async function approveSeriesMap(seriesProfileId: string, mapHash: string) {
    setBusy(true);
    setError(null);
    try {
      await coreApi("POST", `/api/series/${seriesProfileId}/maps/${mapHash}/approve`, {
        reason: "Автор проверил актуальную карту различий в Series Studio",
      });
      await reloadProfiles();
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  async function approveBookPassport(
    seriesProfileId: string,
    bookId: string,
    passportHash: string,
  ) {
    setBusy(true);
    setError(null);
    try {
      await coreApi(
        "POST",
        `/api/series/${seriesProfileId}/books/${bookId}/passport/approve`,
        {
          passport_hash: passportHash,
          reason: "Автор утвердил текущую уникальную идею, границы и механизм книги",
        },
      );
      await reloadProfiles();
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  async function archiveSeriesBook(seriesProfileId: string, bookId: string) {
    setBusy(true);
    setError(null);
    try {
      await coreApi("POST", `/api/series/${seriesProfileId}/books/${bookId}/archive`);
      await reloadProfiles();
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  async function deleteImportedSource(
    seriesProfileId: string,
    bookId: string,
    sourceId: string,
    filename: string,
  ) {
    const confirmed = window.confirm(
      `Удалить локально сохранённый оригинал «${filename}»? Это действие нельзя отменить.`,
    );
    if (!confirmed) return;
    setBusy(true);
    setError(null);
    try {
      await coreApi(
        "DELETE",
        `/api/series/${seriesProfileId}/books/${bookId}/imports/${sourceId}`,
      );
      await reloadProfiles();
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  async function approveWorkspaceSeries(seriesProfileId: string) {
    setBusy(true);
    setError(null);
    try {
      await coreApi("POST", `/api/context/profiles/${seriesProfileId}/approve`);
      await reloadProfiles();
    } catch (reason) {
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
      {!embedded && <button
        type="button"
        className="series-studio-launcher"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        Серии
      </button>}

      {open && (
        <div
          className={`series-studio-backdrop ${embedded ? "embedded" : ""}`}
          role={embedded ? undefined : "presentation"}
          onMouseDown={() => { if (!embedded) setOpen(false); }}
        >
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
              {!embedded && <button type="button" className="ghost" onClick={() => setOpen(false)}>Закрыть</button>}
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
                className={mode === "IMPORT" ? "active" : ""}
                onClick={() => setMode("IMPORT")}
              >
                Добавить внешнюю серию
              </button>
              <button
                type="button"
                className={mode === "BOOK_OS" ? "active" : ""}
                onClick={() => setMode("BOOK_OS")}
              >
                Продолжить в BOOK OS
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
                {createdConcepts.length > 1 && (
                  <div className="series-studio-result" aria-label="Концепции серии">
                    <strong>Выберите одну из {createdConcepts.length} концепций</strong>
                    <div className="series-studio-tabs">
                      {createdConcepts.map((concept, index) => (
                        <button
                          key={concept.profile_id}
                          type="button"
                          className={concept.profile_id === createdSeries?.profile_id ? "active" : ""}
                          onClick={() => setCreatedSeries(concept)}
                        >
                          {index + 1}. {concept.name}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </section>
            )}

            {mode === "IMPORT" && (
              <section className="series-studio-section">
                <h3>Серия, начатая вне BOOK OS</h3>
                <p className="muted">
                  Оригинал сохраняется неизменяемым. Сначала BOOK OS покажет аналитический профиль
                  и карту различий; импорт не разрешает переписывать или публиковать текст.
                </p>

                <label className="field">
                  <span>Автор / псевдоним</span>
                  <select value={authorId} onChange={(event) => setAuthorId(event.target.value)}>
                    <option value="">Выберите утверждённого автора</option>
                    {authors.map((item) => <option key={item.profile_id} value={item.profile_id}>{item.name}</option>)}
                  </select>
                </label>
                <div className="series-studio-grid">
                  <label className="field"><span>Название серии</span><input value={externalSeriesName} onChange={(event) => setExternalSeriesName(event.target.value)} /></label>
                  <label className="field"><span>Аудитория</span><input value={externalAudience} onChange={(event) => setExternalAudience(event.target.value)} /></label>
                  <label className="field"><span>Обещание серии</span><input value={externalPromise} onChange={(event) => setExternalPromise(event.target.value)} /></label>
                  <label className="field"><span>Территория серии</span><input value={externalTerritory} onChange={(event) => setExternalTerritory(event.target.value)} /></label>
                  <label className="field"><span>Название первой книги</span><input value={externalBookTitle} onChange={(event) => setExternalBookTitle(event.target.value)} /></label>
                  <label className="field"><span>Уникальная идея этой книги</span><textarea rows={3} value={externalBookIdea} onChange={(event) => setExternalBookIdea(event.target.value)} /></label>
                </div>
                <label className="field">
                  <span>Файл первой книги</span>
                  <input type="file" accept=".docx,.txt,.pdf,.epub,.md,.markdown" onChange={(event) => setExternalBookFile(event.target.files?.[0] ?? null)} />
                  <small>DOCX, TXT, PDF, EPUB или Markdown · до 25 МБ.</small>
                </label>
                {additionalExternalBooks.map((item, index) => (
                  <div className="series-studio-result" key={`external-${index + 2}`}>
                    <strong>Книга {index + 2}</strong>
                    <label className="field"><span>Подтверждённое название</span><input value={item.title} onChange={(event) => setAdditionalExternalBooks((current) => current.map((value, itemIndex) => itemIndex === index ? { ...value, title: event.target.value } : value))} /></label>
                    <label className="field"><span>Уникальная идея книги</span><textarea rows={3} value={item.idea} onChange={(event) => setAdditionalExternalBooks((current) => current.map((value, itemIndex) => itemIndex === index ? { ...value, idea: event.target.value } : value))} /></label>
                    <label className="field"><span>Файл этой книги</span><input type="file" accept=".docx,.txt,.pdf,.epub,.md,.markdown" onChange={(event) => setAdditionalExternalBooks((current) => current.map((value, itemIndex) => itemIndex === index ? { ...value, file: event.target.files?.[0] ?? null } : value))} /></label>
                    <button type="button" className="ghost" onClick={() => setAdditionalExternalBooks((current) => current.filter((_, itemIndex) => itemIndex !== index))}>Убрать книгу из импорта</button>
                  </div>
                ))}
                <button type="button" className="ghost" onClick={() => setAdditionalExternalBooks((current) => [...current, { title: "", idea: "", file: null }])}>
                  + Добавить ещё книгу и файл
                </button>
                <label className="field">
                  <span>Права на файл</span>
                  <select value={rightsStatus} onChange={(event) => setRightsStatus(event.target.value)}>
                    <option value="AUTHOR_MANUSCRIPT">Авторская рукопись</option>
                    <option value="PUBLISHED_OWN_BOOK">Опубликованная книга автора</option>
                    <option value="LICENSED_MATERIAL">Лицензированный материал</option>
                    <option value="REFERENCE_ONLY">Только справочный материал</option>
                  </select>
                </label>
                <button type="button" className="primary" disabled={busy || !authorId || !externalSeriesName.trim() || !externalBookTitle.trim() || !externalBookIdea.trim() || !externalBookFile || additionalExternalBooks.some((item) => !item.title.trim() || !item.idea.trim() || !item.file)} onClick={() => void importExternalSeries()}>
                  {busy ? "Сохраняю и анализирую…" : "Создать паспорт и сохранить оригинал"}
                </button>

                <label className="field">
                  <span>Закрепить эталон подачи для серии — необязательно</span>
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

            {mode === "BOOK_OS" && (
              <section className="series-studio-section">
                <h3>Серии в BOOK OS</h3>
                <p className="muted">Выберите серию, чтобы увидеть книги, порядок, статус паспорта и актуальность карты различий.</p>
                <div className="series-studio-result">
                  <strong>Согласованный каркас автора</strong>
                  <p className="muted">
                    Создаёт черновик «Секреты продвижения услуг» с четырьмя закреплёнными и
                    четырьмя планируемыми книгами. Тексты не генерируются и файлы не меняются.
                  </p>
                  <label className="field">
                    <span>Автор / псевдоним</span>
                    <select value={authorId} onChange={(event) => setAuthorId(event.target.value)}>
                      <option value="">Выберите утверждённого автора</option>
                      {authors.map((item) => <option key={item.profile_id} value={item.profile_id}>{item.name}</option>)}
                    </select>
                  </label>
                  <button type="button" className="primary" disabled={busy || !authorId} onClick={() => void loadServicesPromotionPreset()}>
                    Загрузить «Секреты продвижения услуг»
                  </button>
                </div>
                {workspaces.length === 0 ? (
                  <p className="muted">Сохранённых серий пока нет.</p>
                ) : workspaces.map((workspace) => (
                  <article className="series-studio-result" key={workspace.series_profile_id}>
                    <div className="panel-heading">
                      <div><p className="eyebrow">SERIES BIBLE v{workspace.profile_revision}</p><h3>{workspace.name}</h3></div>
                      <span className={`badge ${workspace.profile_status === "APPROVED" ? "approved" : "draft"}`}>{workspace.profile_status === "APPROVED" ? "УТВЕРЖДЁН" : "ЧЕРНОВИК"}</span>
                    </div>
                    {workspace.territory && <p>{workspace.territory}</p>}
                    {workspace.profile_status !== "APPROVED" && (
                      <button type="button" className="primary" disabled={busy} onClick={() => void approveWorkspaceSeries(workspace.series_profile_id)}>
                        Утвердить паспорт серии
                      </button>
                    )}
                    <ol>
                      {workspace.books.map((book) => (
                        <li key={book.book_id}>
                          <strong>{book.title}</strong> — {book.unique_idea} · {book.status} · {book.source_kind}
                          {!book.passport_approved && (
                            <button type="button" className="ghost" disabled={busy} onClick={() => void approveBookPassport(workspace.series_profile_id, book.book_id, book.passport_hash)}>
                              Утвердить паспорт этой книги
                            </button>
                          )}
                          {book.imported_sources?.map((source) => (
                            <span key={source.source_id} className="series-import-source">
                              <small className="muted">
                                {source.filename} · {source.format} · {source.analysis_status} · {source.analysis.characters ?? 0} знаков · {source.analysis.headings?.length ?? 0} глав · {source.analysis.tables ?? 0} таблиц · {source.analysis.visuals ?? 0} визуалов
                                {(source.analysis.warnings?.length ?? 0) > 0 ? ` · предупреждения: ${source.analysis.warnings!.join("; ")}` : ""}
                              </small>
                              <button
                                type="button"
                                className="ghost danger"
                                disabled={busy}
                                onClick={() => void deleteImportedSource(
                                  workspace.series_profile_id,
                                  book.book_id,
                                  source.source_id,
                                  source.filename,
                                )}
                              >
                                Удалить сохранённый оригинал
                              </button>
                            </span>
                          ))}
                          {book.status !== "ARCHIVED" && (
                            <button
                              type="button"
                              className="ghost"
                              disabled={busy}
                              onClick={() => void archiveSeriesBook(
                                workspace.series_profile_id,
                                book.book_id,
                              )}
                            >
                              Архивировать книгу
                            </button>
                          )}
                        </li>
                      ))}
                    </ol>
                    <p className="muted">
                      Карта различий: {workspace.map === null ? "не построена" : !workspace.map.current ? "устарела" : `${workspace.map.status}${workspace.map.approved ? " · утверждена" : " · ждёт решения автора"}`}
                    </p>
                    {(workspace.map === null || !workspace.map.current) && (
                      <button type="button" className="primary" disabled={busy} onClick={() => void analyzeSeries(workspace.series_profile_id)}>
                        Построить актуальную карту различий
                      </button>
                    )}
                    {workspace.map?.current && !workspace.map.approved && workspace.map.status !== "BLOCKING" && (
                      <button type="button" className="primary" disabled={busy} onClick={() => void approveSeriesMap(workspace.series_profile_id, workspace.map!.map_hash)}>
                        Утвердить различия книг
                      </button>
                    )}
                    {workspace.map?.status === "BLOCKING" && (
                      <p className="alert inline-alert">Есть существенные дубли или неразобранные источники. Утверждение и написание заблокированы до исправления.</p>
                    )}
                    <details>
                      <summary>Что выгрузить по серии</summary>
                      {([
                        ["complete_manuscripts", "Полные рукописи выбранных книг"],
                        ["editorial_and_litres", "Редакционные версии и версии для ЛитРес"],
                        ["audio_editions", "Аудиоредакции"],
                        ["descriptions", "Оглавления и описания"],
                        ["series_and_book_passports", "Паспорт серии и паспорта книг"],
                        ["difference_map", "Карта различий и отчёт о повторах"],
                        ["visual_materials", "Пакет визуальных материалов"],
                        ["sources_and_freshness", "Источники и отчёт об актуальности"],
                        ["next_books_plan", "План следующих книг без запуска написания"],
                      ] as Array<[keyof SeriesOutputs, string]>).map(([key, label]) => (
                        <label className="output-choice" key={key}>
                          <input type="checkbox" checked={seriesOutputs[key]} onChange={(event) => setSeriesOutputs((current) => ({ ...current, [key]: event.target.checked }))} />
                          <span>{label}</span>
                        </label>
                      ))}
                      <button type="button" className="primary" disabled={busy || !Object.values(seriesOutputs).some(Boolean)} onClick={() => void exportSeries(workspace.series_profile_id)}>
                        Подготовить выбранные материалы серии
                      </button>
                    </details>
                  </article>
                ))}
                {seriesExportPath && <p className="series-studio-success">Материалы готовы: {seriesExportPath}</p>}
              </section>
            )}

            {error && <div className="alert inline-alert">{error}</div>}
          </aside>
        </div>
      )}
    </>
  );
}
