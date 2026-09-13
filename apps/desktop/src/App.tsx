import { useEffect, useMemo, useState } from "react";
import { coreApi, coreHealth } from "./api";
import { AntiJunkPanel } from "./AntiJunkPanel";
import { ArchitectureEditor } from "./ArchitectureEditor";
import { BookBenchPanel } from "./BookBenchPanel";
import { BookContextPanel } from "./BookContextPanel";
import { BookJourney } from "./BookJourney";
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
  BUSINESS_SUBTYPES,
  subtypeLabel,
  type BusinessSubtype,
} from "./bookCatalog";
import type {
  ArchitectureChapter,
  BookArchitecturePayload,
  BookContractPayload,
  ChapterContractPayload,
  CoreHealth,
  ProjectSummary,
  ProjectView,
} from "./types";

const STATUS_LABELS: Record<string, string> = {
  DRAFT: "ЧЕРНОВИК",
  PROPOSED: "ПРЕДЛОЖЕНО",
  REVIEWED: "ПРОВЕРЕНО",
  APPROVED: "УТВЕРЖДЕНО",
  LOCKED: "ЗАФИКСИРОВАНО",
  SUPERSEDED: "ЗАМЕНЕНО",
};

const STAGE_LABELS: Record<string, string> = {
  "BOOK DEFINITION": "ОПРЕДЕЛЕНИЕ КНИГИ",
  ARCHITECTURE: "АРХИТЕКТУРА",
  WRITING: "НАПИСАНИЕ",
  "WHOLE-BOOK EDIT": "СКВОЗНАЯ РЕДАКТУРА",
  "FINAL REVIEW": "ФИНАЛЬНАЯ ПРОВЕРКА",
  "LITERARY MASTER": "ЛИТЕРАТУРНЫЙ МАСТЕР",
};

function statusLabel(value?: string | null) {
  if (!value) return "НЕ НАЧАТО";
  return STATUS_LABELS[value] ?? value.replaceAll("_", " ");
}

function stageLabel(value: string) {
  return STAGE_LABELS[value] ?? value.replaceAll("_", " ");
}

function approved(value?: string | null) {
  return value === "APPROVED" || value === "LOCKED";
}

type TopLevelSection = "books" | "series" | "library" | "settings";

type WorkspaceTab =
  | "overview"
  | "research"
  | "structure"
  | "manuscript"
  | "editorial"
  | "audio"
  | "publish";

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

function lines(value: string): string[] {
  return value
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);
}

function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

function documentContent<T>(value: ProjectView["book_contract"] | ProjectView["architecture"]): T | null {
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
  return <span className={`badge ${status?.toLowerCase() ?? "empty"}`}>{statusLabel(status)}</span>;
}

export function App() {
  const [health, setHealth] = useState<CoreHealth | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [topSection, setTopSection] = useState<TopLevelSection>("books");
  const [workspaceTab, setWorkspaceTab] = useState<WorkspaceTab>("overview");
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [libraryProjects, setLibraryProjects] = useState<ProjectSummary[]>([]);
  const [project, setProject] = useState<ProjectView | null>(null);
  const [showNewBook, setShowNewBook] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [primarySubtype, setPrimarySubtype] = useState<BusinessSubtype>(BUSINESS_SUBTYPES[0]);
  const [secondarySubtype, setSecondarySubtype] = useState("");
  const [bookContract, setBookContract] = useState<BookContractPayload>(clone(emptyBookContract));
  const [architecture, setArchitecture] = useState<BookArchitecturePayload>(clone(emptyArchitecture));
  const [selectedChapterId, setSelectedChapterId] = useState<string | null>(null);
  const [chapterContract, setChapterContract] = useState<ChapterContractPayload>(
    clone(emptyChapterContract),
  );

  const selectedChapter = useMemo(
    () => project?.chapters.find((chapter) => chapter.chapter_id === selectedChapterId) ?? null,
    [project, selectedChapterId],
  );
  const chapterChoices = project?.chapters ?? [];
  const hasChapters = chapterChoices.length > 0;

  const workspaceTabs: ReadonlyArray<{ id: WorkspaceTab; title: string; hint: string }> = [
    { id: "overview", title: "Обзор", hint: "Что сделано и какой следующий шаг" },
    { id: "research", title: "Исследование", hint: "Источники и утверждения" },
    { id: "structure", title: "Структура", hint: "Контекст, архитектура, главы" },
    { id: "manuscript", title: "Рукопись", hint: "Текст и редактируемые правки" },
    { id: "editorial", title: "Редактура", hint: "Замечания и доработка" },
    { id: "audio", title: "Аудио", hint: "Подготовка и утверждение аудиоверсии" },
    { id: "publish", title: "Выпуск", hint: "Готовые файлы и публикационный статус" },
  ];

  function hydrate(next: ProjectView) {
    setProject(next);
    setTopSection("books");
    setWorkspaceTab("overview");
    setShowNewBook(false);
    setBookContract(documentContent<BookContractPayload>(next.book_contract) ?? clone(emptyBookContract));
    setArchitecture(
      documentContent<BookArchitecturePayload>(next.architecture) ?? clone(emptyArchitecture),
    );
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

  async function refreshProjects() {
    setProjects(await coreApi<ProjectSummary[]>("GET", "/api/projects"));
  }

  async function refreshLibraryProjects() {
    try {
      setLibraryProjects(await coreApi<ProjectSummary[]>("GET", "/api/library"));
    } catch (reason) {
      setError(String(reason));
    }
  }

  async function handleProjectListChanged(removedBookId?: string) {
    if (removedBookId && project?.book_id === removedBookId) {
      setProject(null);
      setSelectedChapterId(null);
      setBookContract(clone(emptyBookContract));
      setArchitecture(clone(emptyArchitecture));
      setChapterContract(clone(emptyChapterContract));
    }
    await refreshProjects();
    await refreshLibraryProjects();
  }

  async function openProject(bookId: string) {
    setBusy(true);
    setError(null);
    try {
      setTopSection("books");
      setWorkspaceTab("overview");
      hydrate(await coreApi<ProjectView>("GET", `/api/projects/${bookId}`));
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    void coreHealth<CoreHealth>()
      .then(async (value) => {
        setHealth(value);
        await refreshProjects();
        await refreshLibraryProjects();
      })
      .catch((reason: unknown) => setError(String(reason)));
  }, []);

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
      hydrate(created);
      setNewTitle("");
      setSecondarySubtype("");
      setShowNewBook(false);
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

  async function saveBookContract() {
    if (!project) return;
    await runProjectMutation("PUT", `/api/projects/${project.book_id}/book-contract/draft`, bookContract);
  }

  async function approveBookContract() {
    if (!project) return;
    await runProjectMutation("POST", `/api/projects/${project.book_id}/book-contract/approve`);
  }

  async function saveArchitecture() {
    if (!project) return;
    await runProjectMutation("PUT", `/api/projects/${project.book_id}/architecture/draft`, architecture);
  }

  async function approveArchitecture() {
    if (!project) return;
    await runProjectMutation("POST", `/api/projects/${project.book_id}/architecture/approve`);
  }

  async function saveChapterContract() {
    if (!project || !selectedChapterId) return;
    await runProjectMutation(
      "PUT",
      `/api/projects/${project.book_id}/chapters/${selectedChapterId}/contract/draft`,
      chapterContract,
    );
  }

  async function restoreFromLibrary(bookId: string) {
    setBusy(true);
    setError(null);
    try {
      await coreApi("POST", `/api/library/${bookId}/restore`);
      await refreshLibraryProjects();
      await refreshProjects();
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  async function approveChapterContract() {
    if (!project || !selectedChapterId) return;
    await runProjectMutation(
      "POST",
      `/api/projects/${project.book_id}/chapters/${selectedChapterId}/contract/approve`,
    );
  }

  const healthLabel = health
    ? `Локальное ядро: ${health.status === "healthy" ? "работает" : health.status}`
    : error && !project
      ? "Локальное ядро недоступно"
      : "Локальное ядро запускается…";

  const contractApproved = approved(project?.book_contract?.authority_status);
  const architectureApproved = approved(project?.architecture?.authority_status);

  const chapterHint = hasChapters ? `Выберите главу из ${chapterChoices.length} доступных` : "";

  const workspaceHeaderLabel = project
    ? `${subtypeLabel(project.primary_subtype)}${project.secondary_subtype ? ` · ${subtypeLabel(project.secondary_subtype)}` : ""}`
    : "";

  return (
    <main className="shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">ИЗДАТЕЛЬСКАЯ ПЛАТФОРМА</p>
          <h1>BOOK OS</h1>
          <small>Публикация нон-фикшн в одном редакционном контуре</small>
        </div>
        <div className="health-block">
          <span className={health ? "health" : "health error"}>{healthLabel}</span>
          {health && <small>Версия ядра {health.version}</small>}
        </div>
      </header>

      <nav className="top-level-nav" aria-label="Главная навигация">
        <button
          className={topSection === "books" ? "top-level-nav-item active" : "top-level-nav-item"}
          onClick={() => setTopSection("books")}
          type="button"
        >
          Книги
        </button>
        <button
          className={topSection === "series" ? "top-level-nav-item active" : "top-level-nav-item"}
          onClick={() => setTopSection("series")}
          type="button"
        >
          Серии
        </button>
        <button
          className={topSection === "library" ? "top-level-nav-item active" : "top-level-nav-item"}
          onClick={() => setTopSection("library")}
          type="button"
        >
          Библиотека
        </button>
        <button
          className={topSection === "settings" ? "top-level-nav-item active" : "top-level-nav-item"}
          onClick={() => setTopSection("settings")}
          type="button"
        >
          Настройки
        </button>
      </nav>

      {error && <div className="alert">{error}</div>}

      <div className="workspace">
        <BookSidebar
          projects={projects}
          activeBookId={project?.book_id ?? null}
          busy={busy}
          onNew={() => {
            setTopSection("books");
            setWorkspaceTab("overview");
            setShowNewBook(true);
          }}
          onOpen={(bookId) => {
            setTopSection("books");
            setWorkspaceTab("overview");
            void openProject(bookId);
          }}
          onProjectListChanged={(removedBookId) => void handleProjectListChanged(removedBookId)}
          stageLabel={stageLabel}
        />

        <section className="content">
          {topSection === "series" && (
            <>
              <section className="project-header panel" aria-label="Серия">
                <div>
                  <p className="eyebrow">СЕРИИ</p>
                  <h2>Серийная работа</h2>
                  <p className="muted">Управляйте авторскими сериями и производите связанный выпуск.</p>
                </div>
              </section>
              <SeriesStudio />
            </>
          )}

          {topSection === "library" && (
            <>
              <section className="project-header panel" aria-label="Библиотека">
                <div>
                  <p className="eyebrow">БИБЛИОТЕКА</p>
                  <h2>Завершённые и архивные книги</h2>
                  <p className="muted">
                    Книги в библиотеке не участвуют в текущей работе, но остаются доступными для возврата.
                  </p>
                </div>
              </section>

              <section className="panel">
                {libraryProjects.length === 0 ? (
                  <p className="muted">
                    Библиотека пока пуста. Перенесите книгу со вкладки «Книги» через меню книги.
                  </p>
                ) : (
                  <div className="library-grid">
                    {libraryProjects.map((item) => (
                      <article key={item.book_id} className="library-card">
                        <p className="eyebrow">АРХИВ</p>
                        <h3>{item.working_title}</h3>
                        <small>{subtypeLabel(item.primary_subtype)}</small>
                        <p className="muted">{stageLabel(item.workflow_stage)}</p>
                        <div className="actions">
                          <button className="secondary" type="button" onClick={() => void restoreFromLibrary(item.book_id)}>
                            Вернуть в книги
                          </button>
                        </div>
                      </article>
                    ))}
                  </div>
                )}
              </section>
            </>
          )}

          {topSection === "settings" && (
            <>
              <section className="project-header panel" aria-label="Настройки приложения">
                <div>
                  <p className="eyebrow">НАСТРОЙКИ</p>
                  <h2>Параметры среды</h2>
                  <p className="muted">Техническая конфигурация скрыта за экраном Advanced.</p>
                </div>
              </section>
              <OpenAIWorkLevelPanel />
              <details className="utility-drawer" open>
                <summary>Настройки текста и словарь мусора</summary>
                <AntiJunkPanel />
              </details>
              <details className="utility-drawer">
                <summary>Диагностика и внутренние артефакты</summary>
                <BookMemoryPanel project={project} chapter={selectedChapter} />
              </details>
            </>
          )}

          {topSection === "books" && showNewBook && (
            <BookStartPanel
              newTitle={newTitle}
              setNewTitle={setNewTitle}
              primarySubtype={primarySubtype}
              setPrimarySubtype={setPrimarySubtype}
              secondarySubtype={secondarySubtype}
              setSecondarySubtype={setSecondarySubtype}
              busy={busy}
              onCreate={() => void createProject()}
              onClose={() => setShowNewBook(false)}
            />
          )}

          {topSection === "books" && !project && !showNewBook && (
            <section className="hero panel">
              <p className="eyebrow">НОН-ФИКШН ИЗДАТЕЛЬСКИЙ РАБОЧЕЙ ПЛОЩАДКЕ</p>
              <h2>Создайте первую книгу</h2>
              <p>
                Откройте проект, опишите замысел и в пару шагов получите понятную редакторскую
                конвейерную работу до готового выпуска.
              </p>
              <button className="primary" onClick={() => setShowNewBook(true)}>
                Новая книга
              </button>
            </section>
          )}

          {topSection === "books" && project && (
            <>
              <section className="project-header panel">
                <div>
                  <p className="eyebrow">КНИГА</p>
                  <h2>{project.working_title}</h2>
                  <p className="muted">{workspaceHeaderLabel}</p>
                </div>
                <div className="stage" aria-live="polite">
                  <small>Текущий этап</small>
                  <strong>{stageLabel(project.workflow_stage)}</strong>
                </div>
              </section>
              <nav className="project-tabs" aria-label="Рабочие вкладки книги">
                {workspaceTabs.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    className={workspaceTab === item.id ? "active" : ""}
                    onClick={() => setWorkspaceTab(item.id)}
                    disabled={!project}
                    title={item.hint}
                  >
                    {item.title}
                  </button>
                ))}
              </nav>

              {workspaceTab === "overview" && (
                <>
                  <BookJourney project={project} chapter={selectedChapter} />
                  <section className="panel">
                    <LaunchPlanningPanel
                      project={project}
                      chapter={selectedChapter}
                      onProject={hydrate}
                      coreReady={health?.status === "healthy"}
                    />
                  </section>
                </>
              )}

              {workspaceTab === "structure" && (
                <>
                  <BookContextPanel project={project} />
                  {project.book_contract && (
                    <section className="panel" id="book-contract">
                      <div className="panel-heading">
                        <div>
                          <p className="eyebrow">РУЧНОЙ КОНТРОЛЬ</p>
                          <h3>Контракт книги</h3>
                        </div>
                        <StatusBadge status={project.book_contract.status} />
                      </div>
                      <p className="muted">Этот раздел нужен, если нужно вручную зафиксировать намерение книги.</p>
                      <div className="form-grid">
                        {(
                          [
                            ["reader", "Читатель"],
                            ["reader_problem", "Проблема читателя"],
                            ["central_promise", "Главное обещание книги"],
                            ["central_thesis", "Центральный тезис"],
                            ["unique_angle", "Уникальный угол"],
                            ["reader_trajectory", "Траектория читателя"],
                            ["evidence_policy", "Правила доказательности"],
                            ["voice_genre_constraints", "Голос и жанровые ограничения"],
                          ] as const
                        ).map(([key, label]) => (
                          <Field
                            key={key}
                            label={label}
                            value={bookContract[key]}
                            onChange={(value) => setBookContract((current) => ({ ...current, [key]: value }))}
                          />
                        ))}
                        <Field
                          label="Что книга сознательно не делает"
                          hint="Один пункт на строку"
                          value={bookContract.explicit_exclusions.join("\n")}
                          onChange={(value) =>
                            setBookContract((current) => ({
                              ...current,
                              explicit_exclusions: lines(value),
                            }))
                          }
                        />
                        <Field
                          label="Критерии готовности"
                          hint="Один пункт на строку"
                          value={bookContract.readiness_criteria.join("\n")}
                          onChange={(value) =>
                            setBookContract((current) => ({
                              ...current,
                              readiness_criteria: lines(value),
                            }))
                          }
                        />
                      </div>
                      <div className="actions">
                        <button className="secondary" onClick={() => void saveBookContract()} disabled={busy}>
                          Сохранить черновик
                        </button>
                        <button
                          className={`primary ${contractApproved ? "ready" : ""}`}
                          onClick={() => void approveBookContract()}
                          disabled={busy || contractApproved}
                        >
                          {contractApproved ? "Утверждено ✓" : "Утвердить контракт книги"}
                        </button>
                      </div>
                    </section>
                  )}

                  {(contractApproved || project.architecture) && (
                    <div id="architecture">
                      <ArchitectureEditor
                        architecture={architecture}
                        setArchitecture={setArchitecture}
                        statusBadge={<StatusBadge status={project.architecture?.status} />}
                        busy={busy}
                        onSave={() => void saveArchitecture()}
                        onApprove={() => void approveArchitecture()}
                      />
                    </div>
                  )}

                  {architectureApproved && project.chapters.length > 0 && (
                    <section className="panel" id="chapter-contract">
                      <div className="panel-heading">
                        <div>
                          <p className="eyebrow">РУЧНОЙ КОНТРОЛЬ</p>
                          <h3>Контракт главы</h3>
                        </div>
                        <StatusBadge status={selectedChapter?.chapter_contract?.status} />
                      </div>
                      <label className="field">
                        <span>Глава</span>
                        <select
                          value={selectedChapterId ?? ""}
                          onChange={(event) => setSelectedChapterId(event.target.value)}
                        >
                          {project.chapters.map((chapter) => (
                            <option key={chapter.chapter_id} value={chapter.chapter_id}>
                              {chapter.ordinal}. {chapter.working_title}
                            </option>
                          ))}
                        </select>
                      </label>
                      <div className="form-grid">
                        {(
                          [
                            ["chapter_purpose", "Функция главы"],
                            ["new_contribution", "Новый вклад"],
                            ["reader_prior_state", "Что читатель понимает до главы"],
                            ["reader_after_state", "Что читатель понимает после главы"],
                            ["opening_requirements", "Требования к началу"],
                            ["ending_requirements", "Требования к финалу"],
                            ["transition_requirements", "Требования к переходу"],
                          ] as const
                        ).map(([key, label]) => (
                          <Field
                            key={key}
                            label={label}
                            value={chapterContract[key]}
                            onChange={(value) => setChapterContract((current) => ({ ...current, [key]: value }))}
                          />
                        ))}
                        {(
                          [
                            ["required_claims", "Обязательные утверждения"],
                            ["required_or_permitted_research", "Нужное/разрешённое исследование"],
                            ["required_scenes_examples", "Нужные сцены и примеры"],
                            ["reserved_elsewhere", "Что должно остаться в других главах"],
                          ] as const
                        ).map(([key, label]) => (
                          <Field
                            key={key}
                            label={label}
                            hint="Один пункт на строку"
                            value={chapterContract[key].join("\n")}
                            onChange={(value) =>
                              setChapterContract((current) => ({ ...current, [key]: lines(value) }))
                            }
                          />
                        ))}
                      </div>
                      <div className="actions">
                        <button
                          className="secondary"
                          onClick={() => void saveChapterContract()}
                          disabled={busy || !selectedChapter}
                        >
                          Сохранить черновик
                        </button>
                        <button
                          className="primary"
                          onClick={() => void approveChapterContract()}
                          disabled={busy || !selectedChapter}
                        >
                          Утвердить контракт главы
                        </button>
                      </div>
                    </section>
                  )}
                </>
              )}

              {workspaceTab === "manuscript" && (
                <>
                  <p className="eyebrow muted">Раздел «Рукопись» для текущей главы</p>
                  {selectedChapter ? (
                    <DraftingPanel project={project} chapter={selectedChapter} />
                  ) : (
                    <div className="panel help-copy" role="status">
                      <p>
                        Для работы с рукописью сначала откройте любую из глав книги. У вас уже есть список
                        глав во вкладке структуры или выше.
                      </p>
                    </div>
                  )}
                </>
              )}

              {workspaceTab === "research" && (
                <>
                  <p className="eyebrow muted">Раздел «Исследование» работает только с выбранной главой</p>
                  {selectedChapter ? (
                    <ResearchPanel project={project} chapter={selectedChapter} />
                  ) : (
                    <div className="panel help-copy" role="status">
                      <p>Выберите главу для запуска поиска источников и фиксации доказательности.</p>
                    </div>
                  )}
                </>
              )}

              {workspaceTab === "editorial" && (
                <>
                  {selectedChapter ? (
                    <>
                      <EditorialPanel project={project} chapter={selectedChapter} />
                      <BookBenchPanel project={project} />
                    </>
                  ) : (
                    <div className="panel help-copy" role="status">
                      <p>Сначала выберите главу, чтобы видеть редакционные замечания по тексту.</p>
                    </div>
                  )}
                </>
              )}

              {workspaceTab === "audio" && (
                <>
                  <p className="eyebrow muted">Раздел «Аудио» — подготовка аудиоредакции и подтверждение результатов</p>
                  <LaunchPlanningPanel
                    project={project}
                    chapter={selectedChapter}
                    onProject={hydrate}
                    coreReady={health?.status === "healthy"}
                  />
                </>
              )}

              {workspaceTab === "publish" && (
                <>
                  <p className="eyebrow muted">Раздел «Выпуск»</p>
                  <LiteraryMasterPanel project={project} />
                  <details className="utility-drawer">
                    <summary>Критерии готовности и технические артефакты</summary>
                    <BookBenchPanel project={project} />
                  </details>
                </>
              )}

              {hasChapters && (
                <section className="panel panel-small muted" aria-label="Справка по главам">
                  <p>{chapterHint}</p>
                  <label className="field">
                    <span>Текущая глава</span>
                    <select
                      value={selectedChapterId ?? ""}
                      onChange={(event) => setSelectedChapterId(event.target.value)}
                      disabled={busy}
                    >
                      {project.chapters.map((chapter) => (
                        <option key={chapter.chapter_id} value={chapter.chapter_id}>
                          {chapter.ordinal}. {chapter.working_title}
                        </option>
                      ))}
                    </select>
                  </label>
                </section>
              )}
            </>
          )}
        </section>
      </div>
    </main>
  );
}
