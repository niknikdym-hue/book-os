import { useEffect, useState } from "react";
import { coreApi } from "./api";
import type { DraftRunView, DraftingPanelProps } from "./draftingTypes";

export function DraftingPanel({ project, chapter }: DraftingPanelProps) {
  const [objective, setObjective] = useState("");
  const [model, setModel] = useState("");
  const [context, setContext] = useState("");
  const [runs, setRuns] = useState<DraftRunView[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const approved =
    chapter?.chapter_contract?.authority_status === "APPROVED" ||
    chapter?.chapter_contract?.authority_status === "LOCKED";

  useEffect(() => {
    setRuns([]);
    setError(null);
    if (!chapter) return;
    void coreApi<DraftRunView[]>(
      "GET",
      `/api/projects/${project.book_id}/chapters/${chapter.chapter_id}/drafts`,
    )
      .then(setRuns)
      .catch((reason: unknown) => setError(String(reason)));
  }, [chapter?.chapter_id, project.book_id]);

  async function generate() {
    if (!chapter || !approved || !objective.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const run = await coreApi<DraftRunView>(
        "POST",
        `/api/projects/${project.book_id}/chapters/${chapter.chapter_id}/drafts`,
        {
          section_objective: objective.trim(),
          provider: "openai",
          model: model.trim() || null,
          untrusted_context: context.trim() ? [context] : [],
          max_output_tokens: 3500,
        },
      );
      setRuns((current) => [run, ...current]);
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  const latest = runs[0] ?? null;

  return (
    <section className="panel drafting-panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">M3 · BOUNDED WRITER</p>
          <h3>Controlled Section Draft</h3>
        </div>
        <span className="badge draft">DRAFT ONLY · HUMAN APPROVAL REQUIRED</span>
      </div>

      {!chapter && <p className="muted">Select an approved chapter contract first.</p>}
      {chapter && !approved && (
        <p className="muted">Approve this Chapter Contract before model drafting is allowed.</p>
      )}

      {chapter && approved && (
        <>
          <div className="form-grid">
            <label className="field">
              <span>Section objective</span>
              <textarea
                rows={4}
                value={objective}
                onChange={(event) => setObjective(event.target.value)}
                placeholder="What exactly must this one section accomplish?"
              />
            </label>
            <label className="field">
              <span>OpenAI model</span>
              <input
                value={model}
                onChange={(event) => setModel(event.target.value)}
                placeholder="Leave blank to use BOOK_OS_OPENAI_MODEL"
              />
            </label>
            <label className="field">
              <span>Optional untrusted context</span>
              <small>Stored as data only. It cannot grant tools, authority or broaden scope.</small>
              <textarea
                rows={5}
                value={context}
                onChange={(event) => setContext(event.target.value)}
                placeholder="Paste bounded source/manuscript context here if needed"
              />
            </label>
          </div>
          <div className="actions">
            <button
              className="primary"
              onClick={() => void generate()}
              disabled={busy || !objective.trim()}
            >
              {busy ? "Generating…" : "Generate Draft"}
            </button>
          </div>
        </>
      )}

      {error && <div className="alert inline-alert">{error}</div>}

      {latest && (
        <div className="draft-result">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">LATEST RUN</p>
              <h4>{latest.revision_status ?? latest.run_status}</h4>
            </div>
            <span className="badge draft">{latest.revision_status ?? latest.run_status}</span>
          </div>
          {latest.text && <article className="draft-copy">{latest.text}</article>}
          <dl className="provenance-grid">
            <div>
              <dt>Provider / model</dt>
              <dd>{latest.provider} · {latest.model}</dd>
            </div>
            <div>
              <dt>Prompt</dt>
              <dd>{latest.prompt_id} · {latest.prompt_version}</dd>
            </div>
            <div>
              <dt>Task</dt>
              <dd>{latest.task_id}</dd>
            </div>
            <div>
              <dt>Input revision</dt>
              <dd>{latest.input_revision_id}</dd>
            </div>
          </dl>
          {latest.notes.length > 0 && (
            <ul className="notes-list">
              {latest.notes.map((note) => <li key={note}>{note}</li>)}
            </ul>
          )}
        </div>
      )}
    </section>
  );
}
