import { useCallback, useEffect, useMemo, useState } from "react";
import { coreApi } from "./api";
import type { ProjectView } from "./types";

type ReleaseBlocker = {
  code: string;
  detail: string;
};

type ReleaseReadiness = {
  book_id: string;
  ready: boolean;
  blockers: ReleaseBlocker[];
  snapshot_id: string | null;
  snapshot_hash: string | null;
};

type LiteraryMaster = {
  master_id: string;
  book_id: string;
  manifest_version: string;
  manifest_hash: string;
  canonical_content_hash: string;
  book_title: string;
  human_actor: string;
  created_at: string;
  status: string;
};

type ExportEvidence = {
  export_id: string;
  master_id: string;
  format: string;
  content_hash: string;
  byte_length: number;
  relative_path: string;
};

function blockerLabel(blocker: ReleaseBlocker): string {
  const chapter = blocker.detail.match(/chapter\s+(\d+)/i)?.[1];
  if (blocker.code.includes("MANUSCRIPT_UNIT_NOT_APPROVED")) return "Есть текст, который ещё не утверждён.";
  if (blocker.code.includes("CHAPTER_MANUSCRIPT_EMPTY")) return chapter ? `Глава ${chapter} — текст ещё не создан.` : "В одной из глав ещё нет текста.";
  if (blocker.code.includes("CHAPTER_CONTRACT_MISSING")) return chapter ? `Глава ${chapter} — контракт главы ещё не создан.` : "У одной из глав ещё нет контракта.";
  if (blocker.code.includes("CHAPTER_CONTRACT") && blocker.code.includes("APPROV")) return chapter ? `Глава ${chapter} — контракт ещё не утверждён.` : "Есть контракт главы, который ещё не утверждён.";
  if (blocker.code.includes("BOOKBENCH")) return "Финальная проверка BookBench ещё не выполнена.";
  return "Есть шаг, который ещё нужно завершить перед выпуском книги.";
}

export function LiteraryMasterPanel({ project }: { project: ProjectView }) {
  const [readiness, setReadiness] = useState<ReleaseReadiness | null>(null);
  const [masters, setMasters] = useState<LiteraryMaster[]>([]);
  const [humanActor, setHumanActor] = useState("");
  const [exportEvidence, setExportEvidence] = useState<ExportEvidence | null>(null);
  const [handoffEvidence, setHandoffEvidence] = useState<ExportEvidence | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const latestMaster = useMemo(() => masters.at(-1) ?? null, [masters]);

  const refresh = useCallback(async () => {
    const [nextReadiness, nextMasters] = await Promise.all([
      coreApi<ReleaseReadiness>(
        "GET",
        `/api/projects/${project.book_id}/literary-master/readiness`,
      ),
      coreApi<LiteraryMaster[]>("GET", `/api/projects/${project.book_id}/literary-masters`),
    ]);
    setReadiness(nextReadiness);
    setMasters(nextMasters);
  }, [project.book_id]);

  useEffect(() => {
    setError(null);
    setExportEvidence(null);
    setHandoffEvidence(null);
    void refresh().catch((reason: unknown) => setError(String(reason)));
  }, [refresh]);

  async function createMaster() {
    if (!readiness?.ready || !humanActor.trim()) return;
    setBusy(true);
    setError(null);
    try {
      await coreApi<LiteraryMaster>(
        "POST",
        `/api/projects/${project.book_id}/literary-masters`,
        { human_actor: humanActor.trim() },
      );
      await refresh();
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  async function exportMarkdown() {
    if (!latestMaster) return;
    setBusy(true);
    setError(null);
    try {
      setExportEvidence(
        await coreApi<ExportEvidence>(
          "POST",
          `/api/projects/${project.book_id}/literary-masters/${latestMaster.master_id}/exports/markdown`,
        ),
      );
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  async function createHandoff() {
    if (!latestMaster) return;
    setBusy(true);
    setError(null);
    try {
      setHandoffEvidence(
        await coreApi<ExportEvidence>(
          "POST",
          `/api/projects/${project.book_id}/literary-masters/${latestMaster.master_id}/handoff/audiobook`,
        ),
      );
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel" aria-label="Literary Master">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">ФИНАЛЬНЫЙ ЭТАП</p>
          <h3>Что осталось до готовой книги</h3>
        </div>
        <span className={`badge ${readiness?.ready ? "approved" : "draft"}`}>
          {latestMaster ? "КНИГА ГОТОВА ✓" : readiness?.ready ? "ГОТОВО К ВЫПУСКУ" : "ЕЩЁ ЕСТЬ ШАГИ"}
        </span>
      </div>

      <p className="muted">BOOK OS показывает только реальные оставшиеся шаги и не меняет текст при выпуске.</p>

      {error && <div className="alert">{error}</div>}

      {!readiness && !error && <p>Проверяем готовность к выпуску…</p>}

      {readiness && !readiness.ready && (
        <div aria-label="Literary Master blockers">
          <strong>Что осталось до готовой книги</strong>
          <ul>
            {readiness.blockers.map((blocker) => (
              <li key={`${blocker.code}:${blocker.detail}`}>
                {blockerLabel(blocker)}
              </li>
            ))}
          </ul>
        </div>
      )}


      {!latestMaster && readiness?.ready && (
        <div className="form-grid">
          <label className="field">
            <span>Кто выпускает мастер</span>
            <input
              value={humanActor}
              onChange={(event) => setHumanActor(event.target.value)}
              placeholder="Имя владельца / редактора"
            />
          </label>
          <div className="actions">
            <button
              className="primary"
              onClick={() => void createMaster()}
              disabled={busy || !humanActor.trim()}
            >
              Создать литературный мастер
            </button>
          </div>
        </div>
      )}

      {latestMaster && (
        <div aria-label="Current Literary Master">
          <p>
            <strong>Мастер:</strong> {latestMaster.master_id}
          </p>
          <p className="muted">
            Manifest {latestMaster.manifest_hash.slice(0, 16)}… · рукопись {latestMaster.canonical_content_hash.slice(0, 16)}… · решение: {latestMaster.human_actor}
          </p>
          <div className="actions">
            <button className="secondary" onClick={() => void exportMarkdown()} disabled={busy}>
              Экспортировать Markdown
            </button>
            <button className="secondary" onClick={() => void createHandoff()} disabled={busy}>
              Создать передачу в Audiobook Studio
            </button>
          </div>
        </div>
      )}

      {exportEvidence && (
        <p aria-label="Markdown export evidence">
          Markdown: {exportEvidence.relative_path} · {exportEvidence.content_hash.slice(0, 16)}…
        </p>
      )}
      {handoffEvidence && (
        <p aria-label="Audiobook handoff evidence">
          Передача: {handoffEvidence.relative_path} · {handoffEvidence.content_hash.slice(0, 16)}…
        </p>
      )}
    </section>
  );
}
