import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type Dispatch,
  type SetStateAction,
} from "react";
import { coreApi, coreHealth } from "./api";
import { AntiJunkPanel } from "./AntiJunkPanel";
import { ArchitectureEditor } from "./ArchitectureEditor";
import { BookBenchPanel } from "./BookBenchPanel";
import { BookMemoryPanel } from "./BookMemoryPanel";
import { BookSidebar } from "./BookSidebar";
import { BookStartPanel } from "./BookStartPanel";
import { DraftingPanel } from "./DraftingPanel";
import { EditorialPanel } from "./EditorialPanel";
import { LaunchPlanningPanel } from "./LaunchPlanningPanel";
import { LiteraryMasterPanel } from "./LiteraryMasterPanel";
import { OpenAIWorkLevelPanel } from "./OpenAIWorkLevelPanel";
import { ResearchPanel } from "./ResearchPanel";
import { SeriesStudio } from "./SeriesStudio";
import {
  BOOK_STAGES,
  bookProgress,
  bookStageStates,
  currentBookStage,
  humanAutoBookActivity,
  money,
  type AutoBookSummary,
  type BookStageId,
} from "./authorExperience";
import { BUSINESS_SUBTYPES, subtypeLabel, type BusinessSubtype } from "./bookCatalog";
import type {
  ArchitectureChapter,
  BookArchitecturePayload,
  BookContractPayload,
  ChapterContractPayload,
  CoreHealth,
  ProjectSummary,
  ProjectView,
} from "./types";

type TopLevelSection = "home" | "series" | "books" | "library" | "settings";
type SettingsTab = "ai" | "costs" | "text" | "release" | "diagnostics";
type EditFocus = "summary" | "facts" | "editorial";

type PendingBookSetup = {
  bookId: string;
  idea: string;
  readerHint: string;
  authorName: string;
  seriesName: string;
  targetCharacters: string;
};

type ContextProfile = {
  profile_id: string;
  kind: "AUTHOR" | "SERIES" | "STYLE";
  name: string;
  status: "DRAFT" | "APPROVED";
};

type BookContextSummary = {
  author_profile: ContextProfile | null;
  series_profile: ContextProfile | null;
  style_profile: ContextProfile | null;
  target_characters: number | null;
  include_bibliography?: boolean;
  plan_illustrations?: boolean;
  ready_for_planning: boolean;
};

type SeriesSummary = {
  series_profile_id: string;
  name: string;
  profile_status: string;
  books: Array<{ book_id: string; title: string; status: string }>;
};

const STATUS_LABELS: Record<string, string> = {
  DRAFT: "Черновик",
  PROPOSED: "На проверке",
  REVIEWED: "Проверено",
  APPROVED: "Утверждено",
  LOCKED: "Зафиксировано",
  SUPERSEDED: "Заменено",
};

const INTERNAL_STAGE_LABELS: Record<string, string> = {
  "BOOK DEFINITION": "Замысел",
  ARCHITECTURE: "Архитектура",
  WRITING: "Написание",
  "WHOLE-BOOK EDIT": "Редактура",
  "FINAL REVIEW": "Проверка",
  "LITERARY MASTER": "Выпуск",
};

const emptyBookContract: BookContractPayload = {
  reader: "",
  reader_problem: "",
  central_promise: "",
  central_thesis: "",
  unique_angle: "",
  reader_trajectory: "",
  explicit_exclusions: [],
  evidence_policy: "",
  voice_genre_constraints: "",
  readiness_criteria: [],
};

const newArchitectureChapter = (): ArchitectureChapter => ({
  chapter_id: null,
  title: "",
  purpose: "",
  new_contribution: "",
  dependencies: [],
  transition: "",
});

const emptyArchitecture: BookArchitecturePayload = {
  parts: [{ title: "Основная часть", purpose: "", chapters: [newArchitectureChapter()] }],
  intellectual_progression: "",
  concept_allocation: "",
  promise_thesis_coverage: "",
  major_transitions: "",
};

const emptyChapterContract: ChapterContractPayload = {
  chapter_purpose: "",
  new_contribution: "",
  reader_prior_state: "",
  reader_after_state: "",
  required_claims: [],
  required_or_permitted_research: [],
  required_scenes_examples: [],
  reserved_elsewhere: [],
  opening_requirements: "",
  ending_requirements: "",
  transition_requirements: "",
};

function approved(value?: string | null) {
  return value === "APPROVED" || value === "LOCKED";
}

function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

function lines(value: string) {
  return value.split("\n").map((item) => item.trim()).filter(Boolean);
}

function documentContent<T>(
  value: ProjectView["book_contract"] | ProjectView["architecture"],
): T | null {
  return value ? (value.content as T) : null;
}

function Field({
  label,
  value,
  onChange,
  rows = 3,
  hint,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  rows?: number;
  hint?: string;
}) {
  return (
    <label className="field">
      <span>{label}</span>
      {hint && <small>{hint}</small>}
      <textarea rows={rows} value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  );
}

function StatusBadge({ status }: { status?: string | null }) {
  return (
    <span className={`badge ${status?.toLowerCase() ?? "empty"}`}>
      {status ? STATUS_LABELS[status] ?? status.replaceAll("_", " ") : "Не начато"}
    </span>
  );
}

function NavIcon({ children }: { children: string }) {
  return <span className="nav-icon" aria-hidden="true">{children}</span>;
}

export function App() {
  const [health, setHealth] = useState<CoreHealth | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [topSection, setTopSection] = useState<TopLevelSection>("home");
  const [bookStage, setBookStage] = useState<BookStageId>("intent");
  const [settingsTab, setSettingsTab] = useState<SettingsTab>("ai");
  const [editFocus, setEditFocus] = useState<EditFocus>("summary");
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [libraryProjects, setLibraryProjects] = useState<ProjectSummary[]>([]);
  const [series, setSeries] = useState<SeriesSummary[]>([]);
  const [contextProfiles, setContextProfiles] = useState<ContextProfile[]>([]);
  const [project, setProject] = useState<ProjectView | null>(null);
  const [bookContext, setBookContext] = useState<BookContextSummary | null>(null);
  const [autoBook, setAutoBook] = useState<AutoBookSummary | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [createKind, setCreateKind] = useState<"book" | "series" | null>(null);
  const [newTitle, setNewTitle] = useState("");
  const [newIdea, setNewIdea] = useState("");
  const [newAuthorName, setNewAuthorName] = useState("");
  const [newSeriesName, setNewSeriesName] = useState("");
  const [newReaderHint, setNewReaderHint] = useState("");
  const [newTargetCharacters, setNewTargetCharacters] = useState("180000");
  const [pendingBookSetup, setPendingBookSetup] = useState<PendingBookSetup | null>(null);
  const [primarySubtype, setPrimarySubtype] = useState<BusinessSubtype>(BUSINESS_SUBTYPES[0]);
  const [secondarySubtype, setSecondarySubtype] = useState("");
  const [bookContract, setBookContract] = useState<BookContractPayload>(clone(emptyBookContract));
  const [architecture, setArchitecture] = useState<BookArchitecturePayload>(clone(emptyArchitecture));
  const [selectedChapterId, setSelectedChapterId] = useState<string | null>(null);
  const [chapterContract, setChapterContract] = useState<ChapterContractPayload>(clone(emptyChapterContract));

  const selectedChapter = useMemo(
    () => project?.chapters.find((chapter) => chapter.chapter_id === selectedChapterId) ?? null,
    [project, selectedChapterId],
  );

  const refreshProjects = useCallback(async () => {
    setProjects(await coreApi<ProjectSummary[]>("GET", "/api/projects"));
  }, []);
  const refreshLibraryProjects = useCallback(async () => {
    setLibraryProjects(await coreApi<ProjectSummary[]>("GET", "/api/library"));
  }, []);
  const refreshSeries = useCallback(async () => {
    setSeries(await coreApi<SeriesSummary[]>("GET", "/api/series/workspaces"));
  }, []);
  const refreshContextProfiles = useCallback(async () => {
    setContextProfiles(await coreApi<ContextProfile[]>("GET", "/api/context/profiles"));
  }, []);

  function hydrate(next: ProjectView) {
    setProject(next);
    setBookContract(documentContent<BookContractPayload>(next.book_contract) ?? clone(emptyBookContract));
    setArchitecture(documentContent<BookArchitecturePayload>(next.architecture) ?? clone(emptyArchitecture));
    const chapterId =
      next.chapters.find((chapter) => chapter.chapter_id === selectedChapterId)?.chapter_id ??
      next.chapters[0]?.chapter_id ??
      null;
    setSelectedChapterId(chapterId);
    const chapter = next.chapters.find((item) => item.chapter_id === chapterId);
    setChapterContract(
      chapter?.chapter_contract
        ? (chapter.chapter_contract.content as ChapterContractPayload)
        : clone(emptyChapterContract),
    );
  }

  useEffect(() => {
    void coreHealth<CoreHealth>()
      .then(async (value) => {
        setHealth(value);
        const results = await Promise.allSettled([
          refreshProjects(),
          refreshLibraryProjects(),
          refreshSeries(),
          refreshContextProfiles(),
        ]);
        const failed = results.find((result) => result.status === "rejected");
        if (failed?.status === "rejected") setError(String(failed.reason));
      })
      .catch((reason: unknown) => setError(String(reason)));
  }, [refreshContextProfiles, refreshLibraryProjects, refreshProjects, refreshSeries]);

  useEffect(() => {
    if (!selectedChapter) {
      setChapterContract(clone(emptyChapterContract));
      return;
    }
    setChapterContract(
      selectedChapter.chapter_contract
        ? (selectedChapter.chapter_contract.content as ChapterContractPayload)
        : clone(emptyChapterContract),
    );
  }, [selectedChapter]);

  useEffect(() => {
    if (!project || autoBook?.status !== "RUNNING") return;
    const timer = window.setInterval(() => {
      void coreApi<AutoBookSummary | null>("GET", `/api/projects/${project.book_id}/auto-book`)
        .then(setAutoBook)
        .catch(() => undefined);
    }, 1500);
    return () => window.clearInterval(timer);
  }, [autoBook?.status, project]);

  useEffect(() => {
    if (!project) return;
    const states = bookStageStates(project, autoBook);
    if (states[bookStage] === "locked") setBookStage(currentBookStage(project, autoBook));
  }, [autoBook, bookStage, project]);

  async function openProject(bookId: string) {
    setBusy(true);
    setError(null);
    try {
      const [next, context, state] = await Promise.all([
        coreApi<ProjectView>("GET", `/api/projects/${bookId}`),
        coreApi<BookContextSummary>("GET", `/api/projects/${bookId}/context`),
        coreApi<AutoBookSummary | null>("GET", `/api/projects/${bookId}/auto-book`),
      ]);
      setBookContext(context);
      setAutoBook(state);
      setPendingBookSetup((current) => current?.bookId === bookId ? current : null);
      hydrate(next);
      setBookStage(currentBookStage(next, state));
      setTopSection("books");
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  async function createProject() {
    if (!newTitle.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const created = await coreApi<ProjectView>("POST", "/api/projects", {
        working_title: newTitle.trim(),
        mode: "BOOK_FROM_ZERO",
        domain: "BUSINESS_NONFICTION",
        primary_subtype: primarySubtype,
        secondary_subtype: secondarySubtype || null,
        profile_version: "business-nonfiction-v0.1",
      });
      await refreshProjects();
      setPendingBookSetup({
        bookId: created.book_id,
        idea: newIdea,
        readerHint: newReaderHint,
        authorName: newAuthorName,
        seriesName: newSeriesName,
        targetCharacters: newTargetCharacters,
      });
      hydrate(created);
      setAutoBook(null);
      setBookContext(null);
      setTopSection("books");
      setBookStage("intent");
      setCreateOpen(false);
      setCreateKind(null);
      setNewTitle("");
      setSecondarySubtype("");
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  async function runProjectMutation(method: "POST" | "PUT", path: string, body?: unknown) {
    setBusy(true);
    setError(null);
    try {
      const next = await coreApi<ProjectView>(method, path, body);
      hydrate(next);
      await refreshProjects();
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  async function handleProjectListChanged(removedBookId?: string) {
    if (removedBookId && project?.book_id === removedBookId) {
      setProject(null);
      setBookContext(null);
      setAutoBook(null);
      setTopSection("home");
    }
    await Promise.all([refreshProjects(), refreshLibraryProjects()]);
  }

  async function restoreFromLibrary(bookId: string) {
    setBusy(true);
    setError(null);
    try {
      await coreApi("POST", `/api/library/${bookId}/restore`);
      await Promise.all([refreshLibraryProjects(), refreshProjects()]);
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  const contractApproved = approved(project?.book_contract?.authority_status);
  const architectureApproved = approved(project?.architecture?.authority_status);
  const stageStates = project ? bookStageStates(project, autoBook) : null;
  const systemStage = project ? currentBookStage(project, autoBook) : "intent";
  const progress = project ? bookProgress(project, autoBook) : 0;
  const currentStageLabel = BOOK_STAGES.find((stage) => stage.id === systemStage)?.label ?? "Замысел";
  const authorOptions = useMemo(
    () => Array.from(new Set(
      contextProfiles
        .filter((item) => item.kind === "AUTHOR" && item.status === "APPROVED")
        .map((item) => item.name.trim())
        .filter(Boolean),
    )),
    [contextProfiles],
  );
  const seriesOptions = useMemo(
    () => Array.from(new Set(series.map((item) => item.name.trim()).filter(Boolean))),
    [series],
  );

  function openCreate(kind: "book" | "series" | null = null) {
    setCreateKind(kind);
    setCreateOpen(true);
  }

  function nextStage() {
    if (!project || !stageStates) return;
    const currentIndex = BOOK_STAGES.findIndex((stage) => stage.id === bookStage);
    const next = BOOK_STAGES[currentIndex + 1];
    if (next && stageStates[next.id] !== "locked") setBookStage(next.id);
  }

  return (
    <main className="author-app-shell">
      <aside className="author-sidebar">
        <button className="brand-lockup" type="button" onClick={() => setTopSection("home")}>
          <span className="brand-mark" aria-hidden="true">B</span>
          <span><strong>BOOK OS</strong><small>Author Studio</small></span>
        </button>
        <button className="create-button" type="button" onClick={() => openCreate()}>
          <span aria-hidden="true">＋</span> Создать
        </button>
        <nav className="product-navigation" aria-label="Главная навигация">
          <button className={topSection === "home" ? "active" : ""} onClick={() => setTopSection("home")} type="button"><NavIcon>⌂</NavIcon> Главная</button>
          <button className={topSection === "series" ? "active" : ""} onClick={() => setTopSection("series")} type="button"><NavIcon>▦</NavIcon> Серии</button>
          <button className={topSection === "books" ? "active" : ""} onClick={() => setTopSection("books")} type="button"><NavIcon>▤</NavIcon> Книги</button>
          <button className={topSection === "library" ? "active" : ""} onClick={() => setTopSection("library")} type="button"><NavIcon>◇</NavIcon> Библиотека</button>
        </nav>
        <div className="sidebar-projects">
          <BookSidebar
            projects={projects}
            activeBookId={project?.book_id ?? null}
            busy={busy}
            onNew={() => openCreate("book")}
            onOpen={(bookId) => void openProject(bookId)}
            onProjectListChanged={(removedBookId) => void handleProjectListChanged(removedBookId)}
            stageLabel={(value) => INTERNAL_STAGE_LABELS[value] ?? value.replaceAll("_", " ")}
            showHeader={false}
            showLibrary={false}
          />
        </div>
        <button className={`settings-link ${topSection === "settings" ? "active" : ""}`} type="button" onClick={() => setTopSection("settings")}><NavIcon>⚙</NavIcon> Настройки</button>
      </aside>

      <section className="author-main">
        {error && <div className="system-problem" role="alert"><strong>Работа остановлена. Всё созданное сохранено.</strong><span>{error}</span></div>}
        {project && autoBook?.status === "RUNNING" && (
          <section className="persistent-run" aria-label="BOOK OS создаёт книгу" aria-live="polite">
            <div><span className="run-pulse" aria-hidden="true" /><strong>BOOK OS создаёт книгу</strong><span>Сейчас: {humanAutoBookActivity(autoBook)}</span></div>
            <div><strong>{progress}%</strong><button type="button" onClick={() => { setTopSection("books"); setBookStage(systemStage); }}>Открыть</button></div>
          </section>
        )}

        {topSection === "home" && (
          <section className="home-view">
            <header className="home-hero"><p className="eyebrow">ПРОФЕССИОНАЛЬНАЯ АВТОРСКАЯ СТУДИЯ</p><h1>BOOK OS</h1><p>Создавайте книги и серии — от замысла до готового выпуска.</p></header>
            {!health && !error && <p className="quiet-loading">Открываю вашу библиотеку…</p>}
            <div className="home-create-grid" aria-label="Создать проект">
              <button type="button" onClick={() => openCreate("book")}><span className="create-card-icon" aria-hidden="true">＋</span><span><strong>Новая книга</strong><small>От идеи до готовых файлов</small></span><b aria-hidden="true">→</b></button>
              <button type="button" onClick={() => openCreate("series")}><span className="create-card-icon series" aria-hidden="true">＋</span><span><strong>Новая серия</strong><small>Концепция, книги и единые правила</small></span><b aria-hidden="true">→</b></button>
            </div>
            <section className="continue-section">
              <div className="section-heading"><div><p className="eyebrow">ПРОДОЛЖИТЬ РАБОТУ</p><h2>Последние проекты</h2></div><button className="text-button" type="button" onClick={() => setTopSection("books")}>Все книги</button></div>
              {projects.length === 0 && series.length === 0 ? (
                <div className="empty-editorial-state"><span aria-hidden="true">✦</span><h3>Здесь появятся ваши книги и серии</h3><p>Создайте первый проект — BOOK OS покажет один понятный следующий шаг.</p></div>
              ) : (
                <div className="recent-projects">
                  {projects.slice(0, 4).map((item) => <article className="recent-card" key={item.book_id}><p className="eyebrow">КНИГА</p><h3>{item.working_title}</h3><p>{INTERNAL_STAGE_LABELS[item.workflow_stage] ?? item.workflow_stage}</p><button type="button" onClick={() => void openProject(item.book_id)}>Продолжить <span aria-hidden="true">→</span></button></article>)}
                  {series.slice(0, Math.max(0, 4 - projects.length)).map((item) => <article className="recent-card series-card" key={item.series_profile_id}><p className="eyebrow">СЕРИЯ · {item.books.length} КНИГ</p><h3>{item.name}</h3><p>{item.profile_status === "APPROVED" ? "Концепция утверждена" : "Концепция готовится"}</p><button type="button" onClick={() => setTopSection("series")}>Открыть серию <span aria-hidden="true">→</span></button></article>)}
                </div>
              )}
            </section>
          </section>
        )}

        {topSection === "series" && (
          <section className="section-view"><header className="section-title"><div><p className="eyebrow">СЕРИИ</p><h1>Книги, которые развивают одну большую идею</h1></div><button className="primary-action" type="button" onClick={() => openCreate("series")}>＋ Новая серия</button></header><SeriesStudio embedded initialMode={createKind === "series" ? "NEW" : "BOOK_OS"} /></section>
        )}

        {topSection === "library" && (
          <section className="section-view" aria-label="Библиотека"><header className="section-title"><div><p className="eyebrow">БИБЛИОТЕКА</p><h1>Завершённые и архивные книги</h1><p>Здесь книги хранятся целиком и не мешают текущей работе.</p></div></header>{libraryProjects.length === 0 ? <div className="empty-editorial-state"><span aria-hidden="true">◇</span><h3>Библиотека пока пуста</h3><p>Перенесите сюда книгу через меню «…» рядом с её названием.</p></div> : <div className="library-grid">{libraryProjects.map((item) => <article key={item.book_id} className="library-card"><p className="eyebrow">КНИГА В БИБЛИОТЕКЕ</p><h3>{item.working_title}</h3><p>{subtypeLabel(item.primary_subtype)} · {INTERNAL_STAGE_LABELS[item.workflow_stage] ?? item.workflow_stage}</p><button className="secondary" type="button" onClick={() => void restoreFromLibrary(item.book_id)}>Вернуть в работу</button></article>)}</div>}</section>
        )}

        {topSection === "settings" && (
          <section className="section-view settings-view"><header className="section-title"><div><p className="eyebrow">НАСТРОЙКИ</p><h1>BOOK OS под вашим контролем</h1><p>Обычная работа с книгой не требует этих параметров.</p></div></header><div className="settings-layout"><nav aria-label="Разделы настроек">{([["ai", "AI"], ["costs", "Расходы"], ["text", "Правила текста"], ["release", "Выпуск"], ["diagnostics", "Система и диагностика"]] as const).map(([id, label]) => <button type="button" className={settingsTab === id ? "active" : ""} key={id} onClick={() => setSettingsTab(id)}>{label}</button>)}</nav><div className="settings-content">{settingsTab === "ai" && <><h2>AI для книг</h2><p className="lead-copy">Автоматический режим рекомендован. Ручные модели остаются доступны для точной настройки.</p><OpenAIWorkLevelPanel /></>}{settingsTab === "costs" && <ProjectCostSettings state={autoBook} project={project} />}{settingsTab === "text" && <><h2>Правила текста</h2><p className="lead-copy">Стиль, голос и нежелательные конструкции применяются автоматически.</p><AntiJunkPanel /></>}{settingsTab === "release" && <><h2>Настройки выпуска</h2><p className="lead-copy">Форматы конкретной книги выбираются на этапе «Выпуск». Аудиоверсия всегда сохраняет человеческое утверждение.</p></>}{settingsTab === "diagnostics" && <><h2>Система и диагностика</h2><p className="lead-copy">Технические сведения нужны только при проблеме или аудите.</p><dl className="diagnostics-list"><div><dt>Local Core</dt><dd>{health?.status ?? "недоступен"}</dd></div><div><dt>Версия</dt><dd>{health?.version ?? "—"}</dd></div></dl>{project ? <BookMemoryPanel project={project} chapter={selectedChapter} /> : <p className="muted">Откройте книгу, чтобы увидеть её техническую память.</p>}</>}</div></div></section>
        )}

        {topSection === "books" && !project && (
          <section className="section-view"><header className="section-title"><div><p className="eyebrow">КНИГИ</p><h1>Ваши книги</h1><p>Откройте книгу слева или создайте новую.</p></div><button className="primary-action" type="button" onClick={() => openCreate("book")}>＋ Новая книга</button></header><div className="empty-editorial-state"><span aria-hidden="true">▤</span><h3>{projects.length ? "Выберите книгу" : "Книг пока нет"}</h3><p>{projects.length ? "Рабочий этап и следующий шаг откроются здесь." : "Начните с идеи — технические детали BOOK OS возьмёт на себя."}</p></div></section>
        )}

        {topSection === "books" && project && stageStates && (
          <section className="book-workspace">
            <header className="book-header">
              <div className="book-identity">
                <p className="eyebrow">
                  {bookContext?.series_profile ? bookContext.series_profile.name : "ОТДЕЛЬНАЯ КНИГА"}
                </p>
                <h1>{project.working_title}</h1>
                <p>
                  {bookContext?.author_profile?.name ?? "Автор будет выбран на этапе замысла"}
                  {" · "}{currentStageLabel} {progress}%
                </p>
              </div>
              <ProjectCost state={autoBook} />
              <button className="primary-action" type="button" onClick={() => setBookStage(systemStage)}>
                Продолжить
              </button>
            </header>

            <div className="book-progress" aria-label={`${progress}% книги готово`}>
              <span style={{ width: `${progress}%` }} />
            </div>

            <nav className="book-stage-nav" aria-label="Этапы книги">
              {BOOK_STAGES.map((stage, index) => {
                const state = stageStates[stage.id];
                return (
                  <button
                    key={stage.id}
                    type="button"
                    className={`${state} ${bookStage === stage.id ? "selected" : ""}`}
                    disabled={state === "locked"}
                    aria-current={stage.id === systemStage ? "step" : undefined}
                    onClick={() => setBookStage(stage.id)}
                    title={stage.description}
                  >
                    <span aria-hidden="true">{state === "done" ? "✓" : index + 1}</span>
                    <strong>{stage.label}</strong>
                  </button>
                );
              })}
            </nav>

            <div className="stage-canvas" data-stage={bookStage}>
              {bookStage === "intent" && (
                <IntentStage
                  project={project}
                  selectedChapter={selectedChapter}
                  contract={bookContract}
                  setContract={setBookContract}
                  contractApproved={contractApproved}
                  busy={busy}
                  coreReady={health?.status === "healthy"}
                  initialSetup={pendingBookSetup?.bookId === project.book_id ? pendingBookSetup : undefined}
                  onProject={hydrate}
                  onSave={() => void runProjectMutation(
                    "PUT",
                    `/api/projects/${project.book_id}/book-contract/draft`,
                    bookContract,
                  )}
                  onApprove={() => void runProjectMutation(
                    "POST",
                    `/api/projects/${project.book_id}/book-contract/approve`,
                  )}
                  onNext={nextStage}
                />
              )}
              {bookStage === "plan" && (
                <PlanStage
                  project={project}
                  context={bookContext}
                  contract={bookContract}
                  contractApproved={contractApproved}
                  busy={busy}
                  onApprove={() => void runProjectMutation(
                    "POST",
                    `/api/projects/${project.book_id}/book-contract/approve`,
                  )}
                  onNext={nextStage}
                />
              )}
              {bookStage === "architecture" && (
                <ArchitectureStage
                  project={project}
                  architecture={architecture}
                  setArchitecture={setArchitecture}
                  architectureApproved={architectureApproved}
                  selectedChapterId={selectedChapterId}
                  setSelectedChapterId={setSelectedChapterId}
                  selectedChapter={selectedChapter}
                  chapterContract={chapterContract}
                  setChapterContract={setChapterContract}
                  busy={busy}
                  onSave={() => void runProjectMutation(
                    "PUT",
                    `/api/projects/${project.book_id}/architecture/draft`,
                    architecture,
                  )}
                  onApprove={() => void runProjectMutation(
                    "POST",
                    `/api/projects/${project.book_id}/architecture/approve`,
                  )}
                  onSaveChapter={() => selectedChapterId && void runProjectMutation(
                    "PUT",
                    `/api/projects/${project.book_id}/chapters/${selectedChapterId}/contract/draft`,
                    chapterContract,
                  )}
                  onApproveChapter={() => selectedChapterId && void runProjectMutation(
                    "POST",
                    `/api/projects/${project.book_id}/chapters/${selectedChapterId}/contract/approve`,
                  )}
                />
              )}
              {bookStage === "writing" && (
                <WritingStage
                  project={project}
                  selectedChapterId={selectedChapterId}
                  setSelectedChapterId={setSelectedChapterId}
                  selectedChapter={selectedChapter}
                />
              )}
              {bookStage === "editing" && (
                <EditingStage
                  project={project}
                  selectedChapter={selectedChapter}
                  focus={editFocus}
                  setFocus={setEditFocus}
                />
              )}
              {bookStage === "check" && <CheckStage project={project} />}
              {bookStage === "release" && (
                <ReleaseStage
                  project={project}
                  selectedChapter={selectedChapter}
                  onProject={hydrate}
                  coreReady={health?.status === "healthy"}
                />
              )}
            </div>
          </section>
        )}
      </section>

      {createOpen && (
        <div className="modal-backdrop" role="presentation" onMouseDown={() => setCreateOpen(false)}>
          <section
            className="create-dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="create-title"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <header>
              <div><p className="eyebrow">НОВЫЙ ПРОЕКТ</p><h2 id="create-title">Что создаём?</h2></div>
              <button className="icon-button" aria-label="Закрыть" type="button" onClick={() => setCreateOpen(false)}>×</button>
            </header>
            {!createKind && (
              <div className="create-kind-grid">
                <button type="button" onClick={() => setCreateKind("book")}>
                  <span aria-hidden="true">▤</span><strong>Книгу</strong><small>Отдельную или внутри существующей серии</small>
                </button>
                <button type="button" onClick={() => setCreateKind("series")}>
                  <span aria-hidden="true">▦</span><strong>Серию книг</strong><small>Новую или продолжение существующей</small>
                </button>
              </div>
            )}
            {createKind === "book" && (
              <BookStartPanel
                newTitle={newTitle}
                setNewTitle={setNewTitle}
                idea={newIdea}
                setIdea={setNewIdea}
                authorName={newAuthorName}
                setAuthorName={setNewAuthorName}
                authorOptions={authorOptions}
                seriesName={newSeriesName}
                setSeriesName={setNewSeriesName}
                seriesOptions={seriesOptions}
                readerHint={newReaderHint}
                setReaderHint={setNewReaderHint}
                targetCharacters={newTargetCharacters}
                setTargetCharacters={setNewTargetCharacters}
                primarySubtype={primarySubtype}
                setPrimarySubtype={setPrimarySubtype}
                secondarySubtype={secondarySubtype}
                setSecondarySubtype={setSecondarySubtype}
                busy={busy}
                onCreate={() => void createProject()}
                onClose={() => setCreateKind(null)}
              />
            )}
            {createKind === "series" && (
              <div className="series-create-choice">
                <p>Серия откроется в отдельном рабочем пространстве: концепция, книги, правила и материалы.</p>
                <button className="primary-action" type="button" onClick={() => { setCreateOpen(false); setTopSection("series"); }}>
                  Открыть создание серии
                </button>
                <button className="text-button" type="button" onClick={() => setCreateKind(null)}>Назад</button>
              </div>
            )}
          </section>
        </div>
      )}
    </main>
  );
}

function ProjectCost({ state }: { state: AutoBookSummary | null }) {
  if (!state) {
    return <div className="project-cost empty"><span>Стоимость книги</span><strong>Пока без расходов</strong></div>;
  }
  const estimate = state.estimated_cost_usd ?? 0;
  return (
    <details className="project-cost">
      <summary>
        <span>Стоимость книги</span>
        <strong>Потрачено {money(state.confirmed_cost_usd)}</strong>
        {estimate > 0 && <small>Оценка итоговой {money(estimate)}</small>}
      </summary>
      <dl>
        <div><dt>Фактически потрачено</dt><dd>{money(state.confirmed_cost_usd)}</dd></div>
        {estimate > 0 && <div><dt>Оценка итоговой стоимости</dt><dd>{money(estimate)}</dd></div>}
        {(state.reserved_cost_usd ?? 0) > 0 && <div><dt>Зарезервировано</dt><dd>{money(state.reserved_cost_usd)}</dd></div>}
        {(state.unknown_cost_usd ?? 0) > 0 && (
          <div className="cost-warning"><dt>Ожидает подтверждения провайдера</dt><dd>{money(state.unknown_cost_usd)}</dd></div>
        )}
        {state.max_total_cost_usd !== undefined && <div><dt>Бюджет проекта</dt><dd>{money(state.max_total_cost_usd)}</dd></div>}
      </dl>
    </details>
  );
}

function ProjectCostSettings({ state, project }: { state: AutoBookSummary | null; project: ProjectView | null }) {
  return (
    <>
      <h2>Расходы</h2>
      <p className="lead-copy">Подтверждённые, оценочные и ожидающие суммы показаны отдельно и восстанавливаются из Local Core.</p>
      {project ? <ProjectCost state={state} /> : <p className="muted">Откройте книгу, чтобы увидеть её durable cost accounting.</p>}
      <details className="advanced-settings">
        <summary>Технические лимиты и safety controls</summary>
        <p className="settings-note">Общий бюджет, лимит одного запроса и число запросов задаются перед Auto Book запуском. BOOK OS не выполняет запрос вне этих границ.</p>
      </details>
    </>
  );
}

function IntentStage({
  project,
  selectedChapter,
  contract,
  setContract,
  contractApproved,
  busy,
  coreReady,
  initialSetup,
  onProject,
  onSave,
  onApprove,
  onNext,
}: {
  project: ProjectView;
  selectedChapter: ProjectView["chapters"][number] | null;
  contract: BookContractPayload;
  setContract: (
    value: BookContractPayload | ((current: BookContractPayload) => BookContractPayload),
  ) => void;
  contractApproved: boolean;
  busy: boolean;
  coreReady: boolean;
  initialSetup?: PendingBookSetup;
  onProject: (value: ProjectView) => void;
  onSave: () => void;
  onApprove: () => void;
  onNext: () => void;
}) {
  if (!project.book_contract) {
    return (
      <>
        <StageHeading
          eyebrow="ЭТАП 1 ИЗ 7"
          title="Расскажите о книге"
          copy="Опишите замысел обычными словами. BOOK OS предложит читателя, обещание, план исследования и дальнейший маршрут."
        />
        <LaunchPlanningPanel
          key={project.book_id}
          project={project}
          chapter={selectedChapter}
          onProject={onProject}
          coreReady={coreReady}
          surface="new-book"
          initialSetup={initialSetup}
        />
      </>
    );
  }

  const cards = [
    ["Для кого", contract.reader],
    ["Главная проблема", contract.reader_problem],
    ["Что изменится у читателя", contract.reader_trajectory],
    ["Главная идея", contract.central_thesis],
    ["Главное обещание", contract.central_promise],
    ["Чем книга отличается", contract.unique_angle],
  ];

  return (
    <>
      <StageHeading
        eyebrow="ЭТАП 1 ИЗ 7"
        title="BOOK OS понял книгу так"
        copy="Проверьте смысл, а не технический документ. Полная версия контракта сохраняется внутри authority."
      />
      <section className="summary-grid">
        {cards.map(([label, value]) => (
          <article key={label}><small>{label}</small><p>{value || "Нужно уточнить"}</p></article>
        ))}
      </section>
      <details className="editorial-details">
        <summary>Изменить замысел</summary>
        <div className="form-grid">
          {([
            ["reader", "Для кого"],
            ["reader_problem", "Главная проблема"],
            ["reader_trajectory", "Что изменится у читателя"],
            ["central_thesis", "Главная идея"],
            ["central_promise", "Главное обещание"],
            ["unique_angle", "Чем книга отличается"],
          ] as const).map(([key, label]) => (
            <Field
              key={key}
              label={label}
              value={contract[key]}
              onChange={(value) => setContract((current) => ({ ...current, [key]: value }))}
            />
          ))}
        </div>
        <div className="actions"><button className="secondary" type="button" disabled={busy} onClick={onSave}>Сохранить изменения</button></div>
      </details>
      <details className="editorial-details">
        <summary>Полный Book Contract · Advanced</summary>
        <div className="form-grid">
          <Field label="Правила доказательности" value={contract.evidence_policy} onChange={(value) => setContract((current) => ({ ...current, evidence_policy: value }))} />
          <Field label="Голос и жанровые рамки" value={contract.voice_genre_constraints} onChange={(value) => setContract((current) => ({ ...current, voice_genre_constraints: value }))} />
          <Field label="Что книга сознательно не делает" hint="Один пункт на строку" value={contract.explicit_exclusions.join("\n")} onChange={(value) => setContract((current) => ({ ...current, explicit_exclusions: lines(value) }))} />
          <Field label="Критерии готовности" hint="Один пункт на строку" value={contract.readiness_criteria.join("\n")} onChange={(value) => setContract((current) => ({ ...current, readiness_criteria: lines(value) }))} />
        </div>
      </details>
      <div className="stage-actions">
        <button className="primary-action" type="button" disabled={busy} onClick={contractApproved ? onNext : onApprove}>
          {contractApproved ? "Перейти к плану" : "Всё правильно"}
        </button>
        <StatusBadge status={project.book_contract.status} />
      </div>
    </>
  );
}

function PlanStage({
  project,
  context,
  contract,
  contractApproved,
  busy,
  onApprove,
  onNext,
}: {
  project: ProjectView;
  context: BookContextSummary | null;
  contract: BookContractPayload;
  contractApproved: boolean;
  busy: boolean;
  onApprove: () => void;
  onNext: () => void;
}) {
  return (
    <>
      <StageHeading
        eyebrow="ЭТАП 2 ИЗ 7"
        title="План и границы книги"
        copy="BOOK OS фиксирует, что войдёт в книгу, какие доказательства понадобятся и чем она отличается от соседних книг серии."
      />
      <section className="plan-map">
        <article><small>РЕЗУЛЬТАТ ДЛЯ ЧИТАТЕЛЯ</small><h3>{contract.central_promise || "Нужно уточнить обещание"}</h3><p>{contract.reader_trajectory}</p></article>
        {context?.series_profile && <article><small>МЕСТО В СЕРИИ</small><h3>{context.series_profile.name}</h3><p>Темы, механизмы и примеры сверяются с паспортами других книг серии.</p></article>}
        <article><small>ИССЛЕДОВАНИЕ</small><h3>Факты и источники</h3><p>{contract.evidence_policy || "Существенные утверждения должны иметь проверяемую опору."}</p></article>
        <article><small>СОЗНАТЕЛЬНО НЕ ВХОДИТ</small><ul>{contract.explicit_exclusions.length ? contract.explicit_exclusions.map((item) => <li key={item}>{item}</li>) : <li>Границы ещё не уточнены</li>}</ul></article>
      </section>
      <div className="quality-strip">
        <span>✓ Обещание книги зафиксировано</span>
        <span>✓ Границы доступны архитектуре</span>
        {context?.series_profile && <span>✓ Уникальность серии будет проверена</span>}
      </div>
      <div className="stage-actions">
        <button className="primary-action" disabled={busy} type="button" onClick={contractApproved ? onNext : onApprove}>
          {contractApproved ? "Перейти к архитектуре" : "Утвердить направление"}
        </button>
        <StatusBadge status={project.book_contract?.status} />
      </div>
    </>
  );
}

function ArchitectureStage({
  project,
  architecture,
  setArchitecture,
  architectureApproved,
  selectedChapterId,
  setSelectedChapterId,
  selectedChapter,
  chapterContract,
  setChapterContract,
  busy,
  onSave,
  onApprove,
  onSaveChapter,
  onApproveChapter,
}: {
  project: ProjectView;
  architecture: BookArchitecturePayload;
  setArchitecture: Dispatch<SetStateAction<BookArchitecturePayload>>;
  architectureApproved: boolean;
  selectedChapterId: string | null;
  setSelectedChapterId: (value: string) => void;
  selectedChapter: ProjectView["chapters"][number] | null;
  chapterContract: ChapterContractPayload;
  setChapterContract: (
    value: ChapterContractPayload | ((current: ChapterContractPayload) => ChapterContractPayload),
  ) => void;
  busy: boolean;
  onSave: () => void;
  onApprove: () => void;
  onSaveChapter: () => void;
  onApproveChapter: () => void;
}) {
  return (
    <>
      <StageHeading
        eyebrow="ЭТАП 3 ИЗ 7"
        title="Архитектура книги"
        copy="Карточки глав показывают функцию и новый вклад. Внутренние контракты остаются доступны только там, где они нужны."
      />
      <ArchitectureEditor
        architecture={architecture}
        setArchitecture={setArchitecture}
        statusBadge={<StatusBadge status={project.architecture?.status} />}
        busy={busy}
        onSave={onSave}
        onApprove={onApprove}
      />
      {architectureApproved && project.chapters.length > 0 && (
        <details className="editorial-details chapter-contract-details">
          <summary>Задачи и границы глав</summary>
          <label className="field">
            <span>Глава</span>
            <select value={selectedChapterId ?? ""} onChange={(event) => setSelectedChapterId(event.target.value)}>
              {project.chapters.map((chapter) => <option key={chapter.chapter_id} value={chapter.chapter_id}>{chapter.ordinal}. {chapter.working_title}</option>)}
            </select>
          </label>
          <div className="form-grid">
            {([
              ["chapter_purpose", "Задача главы"],
              ["new_contribution", "Новый вклад"],
              ["reader_prior_state", "Что читатель знает до"],
              ["reader_after_state", "Что читатель понимает после"],
              ["opening_requirements", "Начало"],
              ["ending_requirements", "Финал"],
              ["transition_requirements", "Переход"],
            ] as const).map(([key, label]) => (
              <Field key={key} label={label} value={chapterContract[key]} onChange={(value) => setChapterContract((current) => ({ ...current, [key]: value }))} />
            ))}
          </div>
          <div className="actions">
            <button className="secondary" disabled={busy || !selectedChapter} type="button" onClick={onSaveChapter}>Сохранить</button>
            <button className="primary-action" disabled={busy || !selectedChapter} type="button" onClick={onApproveChapter}>Утвердить задачу главы</button>
          </div>
        </details>
      )}
    </>
  );
}

function WritingStage({
  project,
  selectedChapterId,
  setSelectedChapterId,
  selectedChapter,
}: {
  project: ProjectView;
  selectedChapterId: string | null;
  setSelectedChapterId: (value: string) => void;
  selectedChapter: ProjectView["chapters"][number] | null;
}) {
  return (
    <>
      <StageHeading
        eyebrow="ЭТАП 4 ИЗ 7"
        title="Написание"
        copy="Работайте с одной главой. Задача, текст и редакционный контекст находятся рядом, технические сведения скрыты."
      />
      <div className="writing-workspace">
        <nav className="chapter-rail" aria-label="Главы книги">
          <p className="eyebrow">ГЛАВЫ</p>
          {project.chapters.map((chapter) => (
            <button
              key={chapter.chapter_id}
              className={chapter.chapter_id === selectedChapterId ? "active" : ""}
              type="button"
              onClick={() => setSelectedChapterId(chapter.chapter_id)}
            >
              <span>{chapter.ordinal}</span>
              <strong>{chapter.working_title}</strong>
              <small>{approved(chapter.chapter_contract?.authority_status) ? "Готова к работе" : "Нужна задача"}</small>
            </button>
          ))}
        </nav>
        <div className="manuscript-canvas">
          {selectedChapter ? (
            <DraftingPanel project={project} chapter={selectedChapter} calmMode />
          ) : (
            <div className="empty-editorial-state"><h3>Выберите главу</h3><p>Здесь откроется рукопись и действия редактора.</p></div>
          )}
        </div>
        <aside className="chapter-inspector">
          <p className="eyebrow">ИНСПЕКТОР</p>
          <h3>{selectedChapter?.working_title ?? "Глава не выбрана"}</h3>
          {selectedChapter?.chapter_contract ? (
            <>
              <p><strong>Задача</strong><br />{String(selectedChapter.chapter_contract.content.chapter_purpose ?? "—")}</p>
              <p><strong>Новый вклад</strong><br />{String(selectedChapter.chapter_contract.content.new_contribution ?? "—")}</p>
              <details><summary>Связи и provenance</summary><p className="muted">Точные authority/revision сведения сохранены Local Core и доступны в диагностике.</p></details>
            </>
          ) : (
            <p className="muted">Сначала утвердите задачу этой главы в архитектуре.</p>
          )}
        </aside>
      </div>
    </>
  );
}

function EditingStage({
  project,
  selectedChapter,
  focus,
  setFocus,
}: {
  project: ProjectView;
  selectedChapter: ProjectView["chapters"][number] | null;
  focus: EditFocus;
  setFocus: (value: EditFocus) => void;
}) {
  const categories = [
    "Содержание",
    "Логика",
    "Повторы",
    "Стиль и голос",
    "Факты и источники",
    "Связность глав",
    "Серия / уникальность",
    "Читаемость",
    "Шаблонные конструкции",
  ];
  return (
    <>
      <StageHeading
        eyebrow="ЭТАП 5 ИЗ 7"
        title="Редактура книги"
        copy="Все проверки собраны в одном месте. Откройте только тот вид работы, который нужен сейчас."
      />
      <div className="editing-categories">
        {categories.map((item) => (
          <button
            type="button"
            key={item}
            onClick={() => setFocus(
              item === "Факты и источники"
                ? "facts"
                : item === "Содержание" || item === "Логика" || item === "Стиль и голос"
                  ? "editorial"
                  : "summary",
            )}
          >
            <span className="state-dot" aria-hidden="true" />
            <strong>{item}</strong>
            <small>{selectedChapter ? "Открыть" : "После начала рукописи"}</small>
          </button>
        ))}
      </div>
      <nav className="subview-tabs" aria-label="Редакционные представления">
        <button className={focus === "summary" ? "active" : ""} type="button" onClick={() => setFocus("summary")}>Сводка</button>
        <button className={focus === "facts" ? "active" : ""} type="button" onClick={() => setFocus("facts")}>Факты и источники</button>
        <button className={focus === "editorial" ? "active" : ""} type="button" onClick={() => setFocus("editorial")}>Замечания редактора</button>
      </nav>
      {focus === "summary" && (
        <div className="editorial-summary">
          <h3>{selectedChapter ? "Выберите категорию проверки" : "Редактура начнётся после появления глав"}</h3>
          <p>Research, AntiJunk, cross-book и редакционные проверки остаются обязательными, но не занимают экран одновременно.</p>
        </div>
      )}
      {focus === "facts" && (selectedChapter ? <ResearchPanel project={project} chapter={selectedChapter} /> : <EmptyStage />)}
      {focus === "editorial" && (selectedChapter ? <EditorialPanel project={project} chapter={selectedChapter} /> : <EmptyStage />)}
    </>
  );
}

function CheckStage({ project }: { project: ProjectView }) {
  return (
    <>
      <StageHeading
        eyebrow="ЭТАП 6 ИЗ 7"
        title="Финальная проверка"
        copy="BOOK OS проверяет выполнение замысла, доказательность, голос, структуру и качество всей книги."
      />
      <section className="check-summary">
        <div>
          <span className="check-mark" aria-hidden="true">✓</span>
          <div><p className="eyebrow">BOOKBENCH</p><h3>Результат строится только из реальных проверок</h3><p>BOOK OS не показывает выдуманный общий балл. Блокирующие замечания должны быть исправлены до выпуска.</p></div>
        </div>
      </section>
      <BookBenchPanel project={project} />
    </>
  );
}

function ReleaseStage({
  project,
  selectedChapter,
  onProject,
  coreReady,
}: {
  project: ProjectView;
  selectedChapter: ProjectView["chapters"][number] | null;
  onProject: (project: ProjectView) => void;
  coreReady: boolean;
}) {
  return (
    <>
      <StageHeading
        eyebrow="ЭТАП 7 ИЗ 7"
        title="Выпуск"
        copy="Выберите нужные форматы из одного проверенного master. Аудиоверсия утверждается отдельно после проверки вслух."
      />
      <LiteraryMasterPanel project={project} />
      <details className="release-options" open>
        <summary>Файлы, аудиоверсия и дополнительные материалы</summary>
        <LaunchPlanningPanel
          key={`${project.book_id}:release`}
          project={project}
          chapter={selectedChapter}
          onProject={onProject}
          coreReady={coreReady}
          surface="release"
        />
      </details>
    </>
  );
}

function StageHeading({ eyebrow, title, copy }: { eyebrow: string; title: string; copy: string }) {
  return <header className="stage-heading"><p className="eyebrow">{eyebrow}</p><h2>{title}</h2><p>{copy}</p></header>;
}

function EmptyStage() {
  return <div className="empty-editorial-state"><h3>Сначала выберите главу</h3><p>Замечания и источники всегда привязаны к конкретному тексту.</p></div>;
}
