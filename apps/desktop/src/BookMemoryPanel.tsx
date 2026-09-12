import { useEffect, useMemo, useState } from "react";
import { coreApi } from "./api";
import { uiLabel } from "./uiLabels";
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
  { value: "ALL", label: "Все объекты памяти" },
  { value: "MANUSCRIPT_UNIT", label: "Фрагменты рукописи" },
  { value: "BOOK_CONTRACT", label: "Контракт книги" },
  { value: "CHAPTER_CONTRACT", label: "Контракты глав" },
  { value: "CLAIM", label: "Утверждения" },
];

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
  const visibleConfig = useMemo(() => {
    if (!status?.provider || !status.model) return "Только лексический индекс";
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
      setError("Укажите embedding-модель перед перестроением семантической памяти.");
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
      setError("Введите запрос к памяти книги.");
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
          <p className="eyebrow">ПАМЯТЬ КНИГИ</p>
          <h3>Найти в книге</h3>
          <p>Введите фразу, идею или факт — BOOK OS выберет лучший доступный способ поиска.</p>
        </div>
      </div>

      <div className="form-grid">
        <label className="field">
          <span>Запрос</span>
          <input
            aria-label="Найти в книге"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Найти точную фразу, идею, утверждение или правило контракта"
          />
        </label>
        <label className="field">
          <span>Где искать</span>
          <span>
            <input
              aria-label="Current chapter only"
              type="checkbox"
              checked={currentChapterOnly}
              disabled={!chapter}
              onChange={(event) => setCurrentChapterOnly(event.target.checked)}
            />{" "}
            Только выбранная глава
          </span>
        </label>
      </div>

      <div className="actions">
        <button className="primary" disabled={busy} onClick={() => void search()}>
          {busy ? "Ищу…" : "Найти в книге"}
        </button>
      </div>

      <details className="utility-drawer">
        <summary>Расширенные настройки поиска</summary>
        <div className="form-grid">
          <label className="field"><span>Режим поиска</span><select aria-label="Book Memory mode" value={mode} onChange={(event) => setMode(event.target.value as MemorySearchMode)}><option value="LEXICAL">Лексический</option><option value="SEMANTIC">Семантический</option><option value="HYBRID">Автоматически лучший</option></select></label>
          <label className="field"><span>Область</span><select aria-label="Book Memory scope" value={scope} onChange={(event) => setScope(event.target.value as MemoryScope)}><option value="CURRENT">Текущая книга</option><option value="HISTORY">История версий</option></select></label>
          <label className="field"><span>Тип материала</span><select aria-label="Book Memory object kind" value={objectKind} onChange={(event) => setObjectKind(event.target.value as "ALL" | MemoryObjectKind)}>{objectKinds.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select></label>
          <label className="field"><span>Модель семантического поиска</span><input aria-label="Embedding model" value={embeddingModel} onChange={(event) => setEmbeddingModel(event.target.value)} /></label>
        </div>
        <p>Состояние индекса: {uiLabel(status?.status ?? "LOADING")} · {visibleConfig}</p>
        <div className="actions"><button className="secondary" disabled={busy} onClick={() => void sync()}>Синхронизировать</button><button className="secondary" disabled={busy} onClick={() => void rebuild()}>Перестроить семантический поиск</button></div>
      </details>
      {error && <p role="alert">{error}</p>}

      <div aria-label="Book Memory results">
        {results.length === 0 ? (
          <p>Результатов поиска пока нет.</p>
        ) : (
          results.map((result) => (
            <article className="chapter-plan" key={result.memory_id}>
              <div className="subheading"><strong>{uiLabel(result.object_kind)}</strong></div>
              <p>{result.text}</p>
            </article>
          ))
        )}
      </div>
    </section>
  );
}
