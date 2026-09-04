import { useEffect, useMemo, useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import { coreApi } from "./api";
import { AntiJunkPanel } from "./AntiJunkPanel";
import { ArchitectureEditor } from "./ArchitectureEditor";
import { BookBenchPanel } from "./BookBenchPanel";
import { BookJourney } from "./BookJourney";
import { BookMemoryPanel } from "./BookMemoryPanel";
import { BookStartPanel } from "./BookStartPanel";
import { DraftingPanel } from "./DraftingPanel";
import { EditorialPanel } from "./EditorialPanel";
import { LaunchPlanningPanel } from "./LaunchPlanningPanel";
import { LiteraryMasterPanel } from "./LiteraryMasterPanel";
import { PilotPanel } from "./PilotPanel";
import { ResearchPanel } from "./ResearchPanel";
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
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [project, setProject] = useState<ProjectView | null>(null);
  const [showNewBook, setShowNewBook] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [primarySubtype, setPrimarySubtype] = useState<BusinessSubtype | null>(null);
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

  function hydrate(next: ProjectView) {
    setProject(next);
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
    const items = await coreApi<ProjectSummary[]>("GET", "/api/projects");
    setProjects(items);
  }

  async function openProject(bookId: string) {
    setBusy(true);
    setError(null);
    try {
      hydrate(await coreApi<ProjectView>("GET", `/api/projects/${bookId}`));
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    void invoke<CoreHealth>("core_health")
      .then(async (value) => {
        setHealth(value);
        await refreshProjects();
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
    if (!newTitle.trim() || !primarySubtype) return;
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
      setPrimarySubtype(null);
      setSecondarySubtype("");
      setShowNewBook(false);
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

  async function approveChapterContract() {
    if (!project || !selectedChapterId) return;
    await runProjectMutation(
      "POST",
      `/api/projects/${project.book_id}/chapters/${selectedChapterId}/contract/approve`,
    );
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

  const healthLabel = health
    ? `Локальное ядро: ${health.status === "healthy" ? "работает" : health.status}`
    : error && !project
      ? "Локальное ядро недоступно"
      : "Проверка локального ядра…";

  const contractApproved = approved(project?.book_contract?.authority_status);
  const architectureApproved = approved(project?.architecture?.authority_status);
  const chapterReady = approved(selectedChapter?.chapter_contract?.authority_status);

  return (
    <main className="shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">ЛОКАЛЬНАЯ РЕДАКЦИОННО-АВТОРСКАЯ СИСТЕМА</p>
          <h1>BOOK OS</h1>
        </div>
        <div className="health-block">
          <span className={health ? "health" : "health error"}>{healthLabel}</span>
          {health && <small>Версия ядра {health.version}</small>}
        </div>
      </header>

      {error && <div className="alert">{error}</div>}

      <div className="workspace">
        <aside className="sidebar">
          <div className="sidebar-heading">
            <h2>Книги</h2>
            <button className="primary small" onClick={() => setShowNewBook(true)} disabled={busy}>
              + Новая
            </button>
          </div>
          {projects.length === 0 && <p className="muted">Проектов книг пока нет.</p>}
          <nav>
            {projects.map((item) => (
              <button
                key={item.book_id}
                className={`project-link ${project?.book_id === item.book_id ? "active" : ""}`}
                onClick={() => void openProject(item.book_id)}
                disabled={busy}
              >
                <strong>{item.working_title}</strong>
                <span>{subtypeLabel(item.primary_subtype)}</span>
                <small>{stageLabel(item.workflow_stage)}</small>
              </button>
            ))}
          </nav>
        </aside>

        <section className="content">
          {showNewBook && (
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

          {!project && !showNewBook && (
            <section className="hero panel">
              <p className="eyebrow">РАБОЧЕЕ ПРОСТРАНСТВО BOOK OS</p>
              <h2>Создайте первую реальную книгу</h2>
              <p>
                Выберите доступное направление, опишите идею, а дальше BOOK OS будет показывать один
                следующий шаг: контракт, архитектуру, главы, написание, редактуру и финальную проверку.
              </p>
              <ol className="hero-steps">
                <li>Выберите направление и тему.</li>
                <li>Дайте идею книги своими словами.</li>
                <li>Проверяйте и утверждайте ключевые предложения BOOK OS.</li>
                <li>Дойдите по маршруту до Literary Master.</li>
              </ol>
              <button className="primary" onClick={() => setShowNewBook(true)}>
                Создать новую книгу
              </button>
            </section>
          )}

          {project && (
            <>
              <section className="project-header panel">
                <div>
                  <p className="eyebrow">ДЕЛОВОЙ НОН-ФИКШЕН</p>
                  <h2>{project.working_title}</h2>
                  <p className="muted">
                    Бизнес → {subtypeLabel(project.primary_subtype)}
                    {project.secondary_subtype ? ` · ${subtypeLabel(project.secondary_subtype)}` : ""}
                  </p>
                </div>
                <div className="stage">
                  <small>Текущий этап</small>
                  <strong>{stageLabel(project.workflow_stage)}</strong>
                </div>
              </section>

              <BookJourney project={project} chapter={selectedChapter} />
              <LaunchPlanningPanel project={project} chapter={selectedChapter} onProject={hydrate} />

              {project.book_contract && (
                <section className="panel" id="book-contract">
                  <div className="panel-heading">
                    <div>
                      <p className="eyebrow">ЧЕЛОВЕЧЕСКОЕ РЕШЕНИЕ 1</p>
                      <h3>Контракт книги</h3>
                    </div>
                    <StatusBadge status={project.book_contract.status} />
                  </div>
                  <p className="muted">
                    Отредактируйте черновик до точного обещания книги. Утверждение — только ваше решение.
                  </p>
                  <div className="form-grid">
                    <Field
                      label="Читатель"
                      value={bookContract.reader}
                      onChange={(value) => setBookContract({ ...bookContract, reader: value })}
                    />
                    <Field
                      label="Проблема читателя"
                      value={bookContract.reader_problem}
                      onChange={(value) => setBookContract({ ...bookContract, reader_problem: value })}
                    />
                    <Field
                      label="Центральное обещание"
                      value={bookContract.central_promise}
                      onChange={(value) => setBookContract({ ...bookContract, central_promise: value })}
                    />
                    <Field
                      label="Центральный тезис"
                      value={bookContract.central_thesis}
                      onChange={(value) => setBookContract({ ...bookContract, central_thesis: value })}
                    />
                    <Field
                      label="Уникальный угол"
                      value={bookContract.unique_angle}
                      onChange={(value) => setBookContract({ ...bookContract, unique_angle: value })}
                    />
                    <Field
                      label="Траектория читателя"
                      value={bookContract.reader_trajectory}
                      onChange={(value) => setBookContract({ ...bookContract, reader_trajectory: value })}
                    />
                    <Field
                      label="Что книга сознательно не делает"
                      value={bookContract.explicit_exclusions.join("\n")}
                      onChange={(value) =>
                        setBookContract({ ...bookContract, explicit_exclusions: lines(value) })
                      }
                    />
                    <Field
                      label="Политика доказательности"
                      value={bookContract.evidence_policy}
                      onChange={(value) => setBookContract({ ...bookContract, evidence_policy: value })}
                    />
                    <Field
                      label="Жанр и голос"
                      value={bookContract.voice_genre_constraints}
                      onChange={(value) =>
                        setBookContract({ ...bookContract, voice_genre_constraints: value })
                      }
                    />
                    <Field
                      label="Критерии готовности"
                      value={bookContract.readiness_criteria.join("\n")}
                      onChange={(value) =>
                        setBookContract({ ...bookContract, readiness_criteria: lines(value) })
                      }
                    />
                  </div>
                  <div className="actions">
                    <button className="secondary" onClick={() => void saveBookContract()} disabled={busy}>
                      Сохранить черновик
                    </button>
                    {!contractApproved && (
                      <button className="primary" onClick={() => void approveBookContract()} disabled={busy}>
                        Утвердить контракт книги
                      </button>
                    )}
                  </div>
                </section>
              )}

              {project.architecture && (
                <section className="panel" id="architecture">
                  <div className="panel-heading">
                    <div>
                      <p className="eyebrow">ЧЕЛОВЕЧЕСКОЕ РЕШЕНИЕ 2</p>
                      <h3>Архитектура книги</h3>
                    </div>
                    <StatusBadge status={project.architecture.status} />
                  </div>
                  <p className="muted">
                    Перед утверждением видна вся система частей и глав. Меняйте порядок, назначение и
                    вклад каждой главы до фиксации архитектуры.
                  </p>
                  <ArchitectureEditor value={architecture} onChange={setArchitecture} />
                  <div className="actions">
                    <button className="secondary" onClick={() => void saveArchitecture()} disabled={busy}>
                      Сохранить архитектуру
                    </button>
                    {!architectureApproved && (
                      <button className="primary" onClick={() => void approveArchitecture()} disabled={busy}>
                        Утвердить архитектуру
                      </button>
                    )}
                  </div>
                </section>
              )}

              {project.chapters.length > 0 && (
                <section className="panel" id="chapter-contract">
                  <div className="panel-heading">
                    <div>
                      <p className="eyebrow">ЧЕЛОВЕЧЕСКОЕ РЕШЕНИЕ 3</p>
                      <h3>Контракт главы</h3>
                    </div>
                    <StatusBadge status={selectedChapter?.chapter_contract?.status} />
                  </div>
                  <label className="field compact">
                    <span>Глава</span>
                    <select
                      value={selectedChapterId ?? ""}
                      onChange={(event) => setSelectedChapterId(event.target.value)}
                    >
                      {project.chapters.map((chapter) => (
                        <option key={chapter.chapter_id} value={chapter.chapter_id}>
                          {chapter.ordinal}. {chapter.title}
                        </option>
                      ))}
                    </select>
                  </label>
                  <div className="form-grid">
                    <Field
                      label="Задача главы"
                      value={chapterContract.chapter_purpose}
                      onChange={(value) =>
                        setChapterContract({ ...chapterContract, chapter_purpose: value })
                      }
                    />
                    <Field
                      label="Новый вклад"
                      value={chapterContract.new_contribution}
                      onChange={(value) =>
                        setChapterContract({ ...chapterContract, new_contribution: value })
                      }
                    />
                    <Field
                      label="Состояние читателя до главы"
                      value={chapterContract.reader_prior_state}
                      onChange={(value) =>
                        setChapterContract({ ...chapterContract, reader_prior_state: value })
                      }
                    />
                    <Field
                      label="Состояние читателя после главы"
                      value={chapterContract.reader_after_state}
                      onChange={(value) =>
                        setChapterContract({ ...chapterContract, reader_after_state: value })
                      }
                    />
                    <Field
                      label="Обязательные утверждения"
                      value={chapterContract.required_claims.join("\n")}
                      onChange={(value) =>
                        setChapterContract({ ...chapterContract, required_claims: lines(value) })
                      }
                    />
                    <Field
                      label="Исследования: обязательные или допустимые"
                      value={chapterContract.required_or_permitted_research.join("\n")}
                      onChange={(value) =>
                        setChapterContract({
                          ...chapterContract,
                          required_or_permitted_research: lines(value),
                        })
                      }
                    />
                    <Field
                      label="Сцены и примеры"
                      value={chapterContract.required_scenes_examples.join("\n")}
                      onChange={(value) =>
                        setChapterContract({
                          ...chapterContract,
                          required_scenes_examples: lines(value),
                        })
                      }
                    />
                    <Field
                      label="Зарезервировано для других глав"
                      value={chapterContract.reserved_elsewhere.join("\n")}
                      onChange={(value) =>
                        setChapterContract({ ...chapterContract, reserved_elsewhere: lines(value) })
                      }
                    />
                    <Field
                      label="Требования к открытию"
                      value={chapterContract.opening_requirements}
                      onChange={(value) =>
                        setChapterContract({ ...chapterContract, opening_requirements: value })
                      }
                    />
                    <Field
                      label="Требования к окончанию"
                      value={chapterContract.ending_requirements}
                      onChange={(value) =>
                        setChapterContract({ ...chapterContract, ending_requirements: value })
                      }
                    />
                    <Field
                      label="Переход к следующей главе"
                      value={chapterContract.transition_requirements}
                      onChange={(value) =>
                        setChapterContract({ ...chapterContract, transition_requirements: value })
                      }
                    />
                  </div>
                  <div className="actions">
                    <button className="secondary" onClick={() => void saveChapterContract()} disabled={busy}>
                      Сохранить контракт главы
                    </button>
                    {!chapterReady && (
                      <button
                        className="primary"
                        onClick={() => void approveChapterContract()}
                        disabled={busy}
                      >
                        Утвердить контракт главы
                      </button>
                    )}
                  </div>
                </section>
              )}

              <DraftingPanel project={project} chapter={selectedChapter} onProject={hydrate} />
              <ResearchPanel project={project} chapter={selectedChapter} onProject={hydrate} />
              <EditorialPanel project={project} chapter={selectedChapter} onProject={hydrate} />
              <BookBenchPanel project={project} chapter={selectedChapter} />
              <BookMemoryPanel project={project} chapter={selectedChapter} />
              <LiteraryMasterPanel project={project} />
              <PilotPanel project={project} />
              <details className="utility-drawer">
                <summary>Словарь мусора и служебные настройки</summary>
                <AntiJunkPanel />
              </details>
            </>
          )}
        </section>
      </div>
    </main>
  );
}
