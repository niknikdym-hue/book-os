import { useEffect, useMemo, useState } from "react";
import { coreApi } from "./api";
import type {
  MemoryApi,
  MemoryIndexStatus,
  MemoryObjectKind,
  MemoryScope,
  MemorySearchMode,
  MemorySearchResult,
} from "./memoryTypes";
import type { ChapterView, ProjectView } from "./types";

type BookMemoryPanelProps = {
  project: ProjectView;
  chapter: ChapterView | null;
  api?: MemoryApi;
};

const objectKinds: Array<{ value: "ALL" | MemoryObjectKind; label: string }> = [
  { value: "ALL", label: "All memory objects" },
  { value: "MANUSCRIPT_UNIT", label: "Manuscript units" },
  { value: "BOOK_CONTRACT", label: "Book Contract" },
  { value: "CHAPTER_CONTRACT", label: "Chapter Contracts" },
  { value: "CLAIM", label: "Claims" },
];

function score(value: number | null): string {
  return value == null ? "—" : value.toFixed(4);
}

export function BookMemoryPanel({ project, chapter, api = coreApi }: BookMemoryPanelProps) {
  const [status, setStatus] = useState<MemoryIndexStatus | null>(null);
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState<MemorySearchMode>("HYBRID");
  const [scope, setScope] = useState<MemoryScope>("CURRENT");
  const [objectKind, setObjectKind] = useState<"ALL" | MemoryObjectKind>("ALL");
  const [currentChapterOnly, setCurrentChapterOnly] = useState(false);
  const [embeddingModel, setEmbeddingModel] = useState("");
  const [results, setResults] = useState<MemorySearchResult[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const memoryPath = `/api/projects/${project.book_id}/memory`;
  const semanticReady = status?.status === "SEMANTIC_READY";
  const visibleConfig = useMemo(() => {
    if (!status?.provider || !status.model) return "Lexical index only";
    const suffix = status.config_hash ? ` · ${status.config_hash.slice(0, 10)}…` : "";
    return `${status.provider} · ${status.model}${suffix}`;
  }, [status]);

  async function loadStatus() {
    const next = await api<MemoryIndexStatus>("GET", `${memoryPath}/status`);
    setStatus(next);
  }

  useEffect(() => {
    setStatus(null);
    setResults([]);
    setError(null);
    void loadStatus().catch((reason: unknown) => setError(String(reason)));
    // memoryPath changes whenever the selected project changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [api, memoryPath]);

  async function sync() {
    setBusy(true);
    setError(null);
    try {
      const next = await api<MemoryIndexStatus>("POST", `${memoryPath}/sync`);
      setStatus(next);
      setResults([]);
    } catch (reason: unknown) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  async function rebuild() {
    const model = embeddingModel.trim();
    if (!model) {
      setError("Enter an embedding model before semantic rebuild.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const next = await api<MemoryIndexStatus>("POST", `${memoryPath}/rebuild`, {
        provider: "openai",
        model,
      });
      setStatus(next);
      setResults([]);
    } catch (reason: unknown) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  async function search() {
    const normalizedQuery = query.trim();
    if (!normalizedQuery) {
      setError("Enter a Book Memory query.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const payload = {
        query: normalizedQuery,
        mode,
        scope,
        chapter_id: currentChapterOnly && chapter ? chapter.chapter_id : null,
        object_kinds: objectKind === "ALL" ? [] : [objectKind],
        limit: 12,
        exact_phrase: false,
      };
      const items = await api<MemorySearchResult[]>("POST", `${memoryPath}/search`, payload);
      setResults(items);
    } catch (reason: unknown) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">M5 · DERIVED STATE</p>
          <h3>Book Memory</h3>
          <p>
            Whole-book retrieval only. Results point to exact revisions; memory indexes never become
            authority.
          </p>
        </div>
        <div>
          <strong>{status?.status ?? "LOADING"}</strong>
          <p>
            {status?.document_count ?? 0} docs · {status?.embedding_count ?? 0} vectors
          </p>
        </div>
      </div>

      <div className="form-grid">
        <label className="field">
          <span>Query</span>
          <input
            aria-label="Book Memory query"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Find an exact phrase, idea, claim, or contract rule"
          />
        </label>
        <label className="field">
          <span>Mode</span>
          <select
            aria-label="Book Memory mode"
            value={mode}
            onChange={(event) => setMode(event.target.value as MemorySearchMode)}
          >
            <option value="LEXICAL">Lexical</option>
            <option value="SEMANTIC">Semantic</option>
            <option value="HYBRID">Hybrid</option>
          </select>
        </label>
        <label className="field">
          <span>Scope</span>
          <select
            aria-label="Book Memory scope"
            value={scope}
            onChange={(event) => setScope(event.target.value as MemoryScope)}
          >
            <option value="CURRENT">Current only</option>
            <option value="HISTORY">History diagnostics</option>
          </select>
        </label>
        <label className="field">
          <span>Object kind</span>
          <select
            aria-label="Book Memory object kind"
            value={objectKind}
            onChange={(event) =>
              setObjectKind(event.target.value as "ALL" | MemoryObjectKind)
            }
          >
            {objectKinds.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>Semantic rebuild model</span>
          <input
            aria-label="Embedding model"
            value={embeddingModel}
            onChange={(event) => setEmbeddingModel(event.target.value)}
            placeholder="Explicit OpenAI development model"
          />
        </label>
        <label className="field">
          <span>Chapter filter</span>
          <span>
            <input
              aria-label="Current chapter only"
              type="checkbox"
              checked={currentChapterOnly}
              disabled={!chapter}
              onChange={(event) => setCurrentChapterOnly(event.target.checked)}
            />{" "}
            Current selected chapter only
          </span>
        </label>
      </div>

      <div className="actions">
        <button className="secondary" disabled={busy} onClick={() => void sync()}>
          Sync lexical memory
        </button>
        <button className="secondary" disabled={busy} onClick={() => void rebuild()}>
          Rebuild semantic memory
        </button>
        <button className="primary" disabled={busy} onClick={() => void search()}>
          Search Book Memory
        </button>
      </div>

      <p>
        Index configuration: <strong>{visibleConfig}</strong>
        {semanticReady ? " · semantic ready" : " · semantic rebuild required for Semantic/Hybrid"}
      </p>
      {scope === "HISTORY" && (
        <p role="alert">History mode is diagnostic: every returned row is explicitly non-current.</p>
      )}
      {error && <p role="alert">{error}</p>}

      <div aria-label="Book Memory results">
        {results.length === 0 ? (
          <p>No memory results loaded.</p>
        ) : (
          results.map((result) => (
            <article className="chapter-plan" key={result.memory_id}>
              <div className="subheading">
                <strong>
                  #{result.fused_rank ?? result.semantic_rank ?? result.lexical_rank ?? "—"} ·{" "}
                  {result.object_kind}
                </strong>
                <strong>{result.currentness}</strong>
              </div>
              <p>{result.text}</p>
              <p>
                object <code>{result.object_id}</code> · revision <code>{result.revision_id}</code>
              </p>
              <p>
                revision hash <code>{result.revision_hash}</code>
              </p>
              <p>
                lexical {score(result.lexical_score)} · semantic {score(result.semantic_score)} ·
                fused {score(result.fused_score)}
              </p>
            </article>
          ))
        )}
      </div>
    </section>
  );
}
