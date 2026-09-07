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
          <p className="eyebrow">ФИНАЛЬНОЕ РЕШЕНИЕ ЧЕЛОВЕКА</p>
          <h3>Literary Master</h3>
        </div>
        <span className={`badge ${readiness?.ready ? "approved" : "draft"}`}>
          {latestMaster ? "МАСТЕР ЗАФИКСИРОВАН" : readiness?.ready ? "ГОТОВО К ВЫПУСКУ" : "ЕЩЁ НЕ ГОТОВО"}
        </span>
      </div>

      <p className="muted">
        Литературный мастер фиксирует точные утверждённые версии. Экспорт никогда не меняет authority книги.
      </p>

      {error && <div className="alert">{error}</div>}

      {!readiness && !error && <p>Проверяем готовность к выпуску…</p>}

      {readiness && !readiness.ready && (
        <div aria-label="Literary Master blockers">
          <strong>Что блокирует выпуск</strong>
          <ul>
            {readiness.blockers.map((blocker) => (
              <li key={`${blocker.code}:${blocker.detail}`}>
                <code>{blocker.code}</code> — {blocker.detail}
              </li>
            ))}
          </ul>
        </div>
      )}

      {readiness?.snapshot_id && (
        <p className="muted" aria-label="Literary Master BookBench evidence">
          Снимок BookBench: {readiness.snapshot_id} · {readiness.snapshot_hash?.slice(0, 16)}…
        </p>
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
