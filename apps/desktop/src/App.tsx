import { useEffect, useMemo, useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import { coreApi } from "./api";
import type {
  ArchitectureChapter,
  BookArchitecturePayload,
  BookContractPayload,
  ChapterContractPayload,
  CoreHealth,
  ProjectSummary,
  ProjectView,
} from "./types";

const BUSINESS_SUBTYPES = [
  "Entrepreneurship",
  "Strategy",
  "Leadership",
  "Management",
  "Teams & Culture",
  "Marketing & Brand",
  "Sales & Negotiation",
  "Finance & Investing",
  "Product, Innovation & Technology",
  "Career & Professional Development",
] as const;

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
  return <span className={`badge ${status?.toLowerCase() ?? "empty"}`}>{status ?? "NOT STARTED"}</span>;
}

export function App() {
  const [health, setHealth] = useState<CoreHealth | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [project, setProject] = useState<ProjectView | null>(null);
  const [showNewBook, setShowNewBook] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [primarySubtype, setPrimarySubtype] = useState<(typeof BUSINESS_SUBTYPES)[number]>(
    BUSINESS_SUBTYPES[0],
  );
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

  function updateArchitectureChapter(index: number, patch: Partial<ArchitectureChapter>) {
    setArchitecture((current) => {
      const next = clone(current);
      next.parts[0].chapters[index] = { ...next.parts[0].chapters[index], ...patch };
      return next;
    });
  }

  function moveChapter(index: number, delta: number) {
    setArchitecture((current) => {
      const next = clone(current);
      const target = index + delta;
      if (target < 0 || target >= next.parts[0].chapters.length) return current;
      const [item] = next.parts[0].chapters.splice(index, 1);
      next.parts[0].chapters.splice(target, 0, item);
      return next;
    });
  }

  const healthLabel = health
    ? `Local Core ${health.status}`
    : error && !project
      ? "Local Core unavailable"
      : "Checking Local Core…";

  return (
    <main className="shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">LOCAL-FIRST EDITORIAL SYSTEM</p>
          <h1>BOOK OS</h1>
        </div>
        <div className="health-block">
          <span className={health ? "health" : "health error"}>{healthLabel}</span>
          {health && <small>Core {health.version}</small>}
        </div>
      </header>

      {error && <div className="alert">{error}</div>}

      <div className="workspace">
        <aside className="sidebar">
          <div className="sidebar-heading">
            <h2>Projects</h2>
            <button className="primary small" onClick={() => setShowNewBook(true)} disabled={busy}>
              + New Book
            </button>
          </div>
          {projects.length === 0 && <p className="muted">No book projects yet.</p>}
          <nav>
            {projects.map((item) => (
              <button
                key={item.book_id}
                className={`project-link ${project?.book_id === item.book_id ? "active" : ""}`}
                onClick={() => void openProject(item.book_id)}
                disabled={busy}
              >
                <strong>{item.working_title}</strong>
                <span>{item.primary_subtype}</span>
                <small>{item.workflow_stage}</small>
              </button>
            ))}
          </nav>
        </aside>

        <section className="content">
          {showNewBook && (
            <section className="panel new-book">
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">BOOK FROM ZERO</p>
                  <h2>New Business Nonfiction Book</h2>
                </div>
                <button className="ghost" onClick={() => setShowNewBook(false)}>
                  Close
                </button>
              </div>
              <label className="field">
                <span>Working title</span>
                <input value={newTitle} onChange={(event) => setNewTitle(event.target.value)} />
              </label>
              <div className="two-columns">
                <label className="field">
                  <span>Primary subtype</span>
                  <select
                    value={primarySubtype}
                    onChange={(event) =>
                      setPrimarySubtype(event.target.value as (typeof BUSINESS_SUBTYPES)[number])
                    }
                  >
                    {BUSINESS_SUBTYPES.map((value) => (
                      <option key={value}>{value}</option>
                    ))}
                  </select>
                </label>
                <label className="field">
                  <span>Secondary subtype (optional)</span>
                  <select
                    value={secondarySubtype}
                    onChange={(event) => setSecondarySubtype(event.target.value)}
                  >
                    <option value="">None</option>
                    {BUSINESS_SUBTYPES.filter((value) => value !== primarySubtype).map((value) => (
                      <option key={value}>{value}</option>
                    ))}
                  </select>
                </label>
              </div>
              <button className="primary" onClick={() => void createProject()} disabled={busy}>
                Create project
              </button>
            </section>
          )}

          {!project && !showNewBook && (
            <section className="hero panel">
              <p className="eyebrow">M2 WORKSPACE</p>
              <h2>Create a real book project</h2>
              <p>
                BOOK OS now keeps contracts, architecture and approval history as durable local
                authority — not chat memory.
              </p>
              <button className="primary" onClick={() => setShowNewBook(true)}>
                Create New Book
              </button>
            </section>
          )}

          {project && (
            <>
              <section className="project-header panel">
                <div>
                  <p className="eyebrow">{project.domain.replaceAll("_", " ")}</p>
                  <h2>{project.working_title}</h2>
                  <p className="muted">
                    {project.primary_subtype}
                    {project.secondary_subtype ? ` · ${project.secondary_subtype}` : ""}
                  </p>
                </div>
                <div className="stage">
                  <small>Current stage</small>
                  <strong>{project.workflow_stage}</strong>
                </div>
              </section>

              <section className="panel">
                <div className="panel-heading">
                  <div>
                    <p className="eyebrow">HUMAN GATE 1</p>
                    <h3>Book Contract</h3>
                  </div>
                  <StatusBadge status={project.book_contract?.status} />
                </div>
                <div className="form-grid">
                  {(
                    [
                      ["reader", "Reader"],
                      ["reader_problem", "Reader problem"],
                      ["central_promise", "Central promise"],
                      ["central_thesis", "Central thesis"],
                      ["unique_angle", "Unique angle"],
                      ["reader_trajectory", "Reader trajectory"],
                      ["evidence_policy", "Evidence policy"],
                      ["voice_genre_constraints", "Voice / genre constraints"],
                    ] as const
                  ).map(([key, label]) => (
                    <Field
                      key={key}
                      label={label}
                      value={bookContract[key]}
                      onChange={(value) =>
                        setBookContract((current) => ({ ...current, [key]: value }))
                      }
                    />
                  ))}
                  <Field
                    label="Explicit exclusions"
                    hint="One item per line"
                    value={bookContract.explicit_exclusions.join("\n")}
                    onChange={(value) =>
                      setBookContract((current) => ({
                        ...current,
                        explicit_exclusions: lines(value),
                      }))
                    }
                  />
                  <Field
                    label="Readiness criteria"
                    hint="One item per line"
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
                    Save Draft
                  </button>
                  <button className="primary" onClick={() => void approveBookContract()} disabled={busy}>
                    Approve Book Contract
                  </button>
                </div>
              </section>

              <section className="panel">
                <div className="panel-heading">
                  <div>
                    <p className="eyebrow">HUMAN GATE 2</p>
                    <h3>Book Architecture</h3>
                  </div>
                  <StatusBadge status={project.architecture?.status} />
                </div>
                <div className="form-grid">
                  <Field
                    label="Intellectual progression"
                    value={architecture.intellectual_progression}
                    onChange={(value) =>
                      setArchitecture((current) => ({ ...current, intellectual_progression: value }))
                    }
                  />
                  <Field
                    label="Concept allocation"
                    value={architecture.concept_allocation}
                    onChange={(value) =>
                      setArchitecture((current) => ({ ...current, concept_allocation: value }))
                    }
                  />
                  <Field
                    label="Promise / thesis coverage"
                    value={architecture.promise_thesis_coverage}
                    onChange={(value) =>
                      setArchitecture((current) => ({ ...current, promise_thesis_coverage: value }))
                    }
                  />
                  <Field
                    label="Major transitions"
                    value={architecture.major_transitions}
                    onChange={(value) =>
                      setArchitecture((current) => ({ ...current, major_transitions: value }))
                    }
                  />
                  <Field
                    label="Part title"
                    value={architecture.parts[0].title}
                    onChange={(value) =>
                      setArchitecture((current) => {
                        const next = clone(current);
                        next.parts[0].title = value;
                        return next;
                      })
                    }
                  />
                  <Field
                    label="Part purpose"
                    value={architecture.parts[0].purpose}
                    onChange={(value) =>
                      setArchitecture((current) => {
                        const next = clone(current);
                        next.parts[0].purpose = value;
                        return next;
                      })
                    }
                  />
                </div>
                <div className="chapter-plans">
                  <div className="subheading">
                    <h4>Ordered chapters</h4>
                    <button
                      className="ghost"
                      onClick={() =>
                        setArchitecture((current) => {
                          const next = clone(current);
                          next.parts[0].chapters.push(newArchitectureChapter());
                          return next;
                        })
                      }
                    >
                      + Add chapter
                    </button>
                  </div>
                  {architecture.parts[0].chapters.map((chapter, index) => (
                    <div className="chapter-plan" key={chapter.chapter_id ?? `new-${index}`}>
                      <div className="chapter-order">
                        <strong>Chapter {index + 1}</strong>
                        <button className="icon" onClick={() => moveChapter(index, -1)} disabled={index === 0}>
                          ↑
                        </button>
                        <button
                          className="icon"
                          onClick={() => moveChapter(index, 1)}
                          disabled={index === architecture.parts[0].chapters.length - 1}
                        >
                          ↓
                        </button>
                      </div>
                      <label className="field">
                        <span>Title</span>
                        <input
                          value={chapter.title}
                          onChange={(event) =>
                            updateArchitectureChapter(index, { title: event.target.value })
                          }
                        />
                      </label>
                      <Field
                        label="Purpose"
                        value={chapter.purpose}
                        onChange={(value) => updateArchitectureChapter(index, { purpose: value })}
                      />
                      <Field
                        label="Distinct contribution"
                        value={chapter.new_contribution}
                        onChange={(value) =>
                          updateArchitectureChapter(index, { new_contribution: value })
                        }
                      />
                      <Field
                        label="Dependencies"
                        hint="One chapter ID/reference per line"
                        value={chapter.dependencies.join("\n")}
                        onChange={(value) =>
                          updateArchitectureChapter(index, { dependencies: lines(value) })
                        }
                      />
                      <Field
                        label="Transition"
                        value={chapter.transition}
                        onChange={(value) => updateArchitectureChapter(index, { transition: value })}
                      />
                    </div>
                  ))}
                </div>
                <div className="actions">
                  <button className="secondary" onClick={() => void saveArchitecture()} disabled={busy}>
                    Save Draft
                  </button>
                  <button className="primary" onClick={() => void approveArchitecture()} disabled={busy}>
                    Approve Architecture
                  </button>
                </div>
              </section>

              {project.chapters.length > 0 && (
                <section className="panel">
                  <div className="panel-heading">
                    <div>
                      <p className="eyebrow">HUMAN GATE 3</p>
                      <h3>Chapter Contract</h3>
                    </div>
                    <StatusBadge status={selectedChapter?.chapter_contract?.status} />
                  </div>
                  <label className="field">
                    <span>Chapter</span>
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
                        ["chapter_purpose", "Chapter purpose"],
                        ["new_contribution", "New contribution"],
                        ["reader_prior_state", "Reader prior state"],
                        ["reader_after_state", "Reader after state"],
                        ["opening_requirements", "Opening requirements"],
                        ["ending_requirements", "Ending requirements"],
                        ["transition_requirements", "Transition requirements"],
                      ] as const
                    ).map(([key, label]) => (
                      <Field
                        key={key}
                        label={label}
                        value={chapterContract[key]}
                        onChange={(value) =>
                          setChapterContract((current) => ({ ...current, [key]: value }))
                        }
                      />
                    ))}
                    {(
                      [
                        ["required_claims", "Required claims"],
                        ["required_or_permitted_research", "Required / permitted research"],
                        ["required_scenes_examples", "Required scenes / examples"],
                        ["reserved_elsewhere", "Reserved elsewhere"],
                      ] as const
                    ).map(([key, label]) => (
                      <Field
                        key={key}
                        label={label}
                        hint="One item per line"
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
                      Save Draft
                    </button>
                    <button
                      className="primary"
                      onClick={() => void approveChapterContract()}
                      disabled={busy || !selectedChapter}
                    >
                      Approve Chapter Contract
                    </button>
                  </div>
                </section>
              )}
            </>
          )}
        </section>
      </div>
    </main>
  );
}
