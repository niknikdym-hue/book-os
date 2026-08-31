import { useCallback, useEffect, useMemo, useState } from "react";
import { coreApi } from "./api";
import { uiLabel } from "./uiLabels";
import type { DraftRunView } from "./draftingTypes";
import type {
  CitationCheckView,
  ClaimView,
  EvidenceView,
  ResearchApi,
  ResearchCandidate,
  SourceView,
} from "./researchTypes";
import type { ChapterView, ProjectView } from "./types";

type ResearchPanelProps = {
  project: ProjectView;
  chapter: ChapterView | null;
  api?: ResearchApi;
};

const claimTypes = [
  "QUANTITATIVE",
  "EMPIRICAL",
  "CAUSAL",
  "HISTORICAL",
  "ATTRIBUTION",
  "CASE_ASSERTION",
  "LEGAL_REGULATORY",
  "CONSENSUS",
  "INTERPRETIVE",
  "AUTHORIAL",
] as const;

export function ResearchPanel({ project, chapter, api = coreApi }: ResearchPanelProps) {
  const [drafts, setDrafts] = useState<DraftRunView[]>([]);
  const [claims, setClaims] = useState<ClaimView[]>([]);
  const [claimText, setClaimText] = useState("");
  const [claimType, setClaimType] = useState<(typeof claimTypes)[number]>("EMPIRICAL");
  const [selectedClaimId, setSelectedClaimId] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [candidates, setCandidates] = useState<ResearchCandidate[]>([]);
  const [source, setSource] = useState<SourceView | null>(null);
  const [inspectionNote, setInspectionNote] = useState("");
  const [relationship, setRelationship] = useState<
    "SUPPORTS" | "PARTIALLY_SUPPORTS" | "CONTRADICTS" | "CONTEXT_ONLY"
  >("PARTIALLY_SUPPORTS");
  const [pointer, setPointer] = useState("");
  const [limitations, setОграничения доказательства] = useState("");
  const [evidence, setEvidence] = useState<EvidenceView[]>([]);
  const [citationIdentifier, setCitationIdentifier] = useState("");
  const [citationCheck, setCitationCheck] = useState<CitationCheckView | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const currentDraft = useMemo(
    () =>
      drafts.find(
        (item) => item.unit_id && item.revision_id && item.revision_hash && item.revision_status === "DRAFT",
      ) ?? null,
    [drafts],
  );
  const selectedClaim = useMemo(
    () => claims.find((item) => item.claim_id === selectedClaimId) ?? claims[0] ?? null,
    [claims, selectedClaimId],
  );

  const reloadClaims = useCallback(
    async (draft: DraftRunView) => {
      if (!chapter || !draft.unit_id) return;
      const items = await api<ClaimView[]>(
        "GET",
        `/api/projects/${project.book_id}/claims?chapter_id=${encodeURIComponent(chapter.chapter_id)}&unit_id=${encodeURIComponent(draft.unit_id)}`,
      );
      setClaims(items);
      setSelectedClaimId((current) =>
        current && items.some((item) => item.claim_id === current)
          ? current
          : (items[0]?.claim_id ?? null),
      );
    },
    [api, chapter, project.book_id],
  );

  useEffect(() => {
    setDrafts([]);
    setClaims([]);
    setSelectedClaimId(null);
    setCandidates([]);
    setSource(null);
    setEvidence([]);
    setCitationCheck(null);
    setError(null);
    if (!chapter) return;
    void api<DraftRunView[]>(
      "GET",
      `/api/projects/${project.book_id}/chapters/${chapter.chapter_id}/drafts`,
    )
      .then(async (items) => {
        setDrafts(items);
        const draft =
          items.find(
            (item) =>
              item.unit_id &&
              item.revision_id &&
              item.revision_hash &&
              item.revision_status === "DRAFT",
          ) ?? null;
        if (draft) await reloadClaims(draft);
      })
      .catch((reason: unknown) => setError(String(reason)));
  }, [api, chapter, project.book_id, reloadClaims]);

  useEffect(() => {
    setEvidence([]);
    setCitationCheck(null);
    if (!selectedClaim) return;
    void api<EvidenceView[]>(
      "GET",
      `/api/projects/${project.book_id}/claims/${selectedClaim.claim_id}/evidence`,
    )
      .then(setEvidence)
      .catch((reason: unknown) => setError(String(reason)));
  }, [api, project.book_id, selectedClaim]);

  async function createClaim() {
    if (
      !chapter ||
      !currentDraft?.unit_id ||
      !currentDraft.revision_id ||
      !currentDraft.revision_hash ||
      !claimText.trim()
    ) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const created = await api<ClaimView>("POST", `/api/projects/${project.book_id}/claims`, {
        chapter_id: chapter.chapter_id,
        unit_id: currentDraft.unit_id,
        manuscript_revision_id: currentDraft.revision_id,
        manuscript_revision_hash: currentDraft.revision_hash,
        normalized_text: claimText.trim(),
        claim_type: claimType,
        materiality: "HIGH",
        required_evidence_level: "INSPECTED_SOURCE",
      });
      setClaimText("");
      await reloadClaims(currentDraft);
      setSelectedClaimId(created.claim_id);
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  async function searchResearch() {
    if (!query.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const result = await api<ResearchCandidate[]>(
        "POST",
        `/api/projects/${project.book_id}/research/search`,
        {
          query: query.trim(),
          providers: ["openalex", "crossref", "semantic_scholar"],
          limit_per_provider: 5,
        },
      );
      setCandidates(result);
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  async function importCandidate(candidate: ResearchCandidate) {
    setBusy(true);
    setError(null);
    try {
      const imported = await api<SourceView>(
        "POST",
        `/api/projects/${project.book_id}/sources/import`,
        { candidate, primary_secondary: "UNCLASSIFIED" },
      );
      setSource(imported);
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  async function markInspected() {
    if (!source || !inspectionNote.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const inspected = await api<SourceView>(
        "POST",
        `/api/projects/${project.book_id}/sources/${source.source_id}/access`,
        {
          access_status: "FULL_SOURCE_INSPECTED",
          actor: "OWNER",
          note: inspectionNote.trim(),
        },
      );
      setSource(inspected);
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  async function addEvidence() {
    if (!selectedClaim || !source || !pointer.trim()) return;
    setBusy(true);
    setError(null);
    try {
      await api<EvidenceView>(
        "POST",
        `/api/projects/${project.book_id}/claims/${selectedClaim.claim_id}/evidence`,
        {
          source_id: source.source_id,
          relationship,
          pointer: pointer.trim(),
          note: "Добавлено из панели исследования BOOK OS.",
          strength: "MODERATE",
          limitations: limitations.trim(),
          actor: "OWNER",
        },
      );
      if (currentDraft) await reloadClaims(currentDraft);
      const rows = await api<EvidenceView[]>(
        "GET",
        `/api/projects/${project.book_id}/claims/${selectedClaim.claim_id}/evidence`,
      );
      setEvidence(rows);
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  async function checkCitation() {
    if (!selectedClaim || !citationIdentifier.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const result = await api<CitationCheckView>(
        "POST",
        `/api/projects/${project.book_id}/claims/${selectedClaim.claim_id}/citation-check`,
        { identifier: citationIdentifier.trim() },
      );
      setCitationCheck(result);
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel research-panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">M4 · РЕЕСТР УТВЕРЖДЕНИЙ</p>
          <h3>Исследование и доказательства</h3>
        </div>
        <span className="badge">Источник ≠ доказательство ≠ утверждение</span>
      </div>

      {!chapter && <p className="muted">Сначала выберите главу.</p>}
      {chapter && !currentDraft && (
        <p className="muted">Сначала создайте черновик текста, затем регистрируйте проверяемые утверждения.</p>
      )}

      {currentDraft && (
        <>
          <div className="research-boundary">
            <strong>Точная версия рукописи</strong>
            <code>{currentDraft.revision_id}</code>
            <small>Доказательства привязаны к этой версии и её хэшу; после изменения текста привязка становится устаревшей.</small>
          </div>

          <div className="form-grid">
            <label className="field">
              <span>Проверяемое утверждение</span>
              <textarea
                rows={3}
                value={claimText}
                onChange={(event) => setClaimText(event.target.value)}
                placeholder="Запишите одно фактическое утверждение в формулировке, которую нужно проверить"
              />
            </label>
            <label className="field">
              <span>Тип утверждения</span>
              <select value={claimType} onChange={(event) => setClaimType(event.target.value as typeof claimType)}>
                {claimTypes.map((item) => <option key={item} value={item}>{uiLabel(item)}</option>)}
              </select>
            </label>
          </div>
          <div className="actions">
            <button className="secondary" disabled={busy || !claimText.trim()} onClick={() => void createClaim()}>
              Добавить утверждение
            </button>
          </div>

          {claims.length > 0 && (
            <>
              <label className="field">
                <span>Утверждение на проверке</span>
                <select
                  value={selectedClaim?.claim_id ?? ""}
                  onChange={(event) => setSelectedClaimId(event.target.value)}
                >
                  {claims.map((item) => (
                    <option key={item.claim_id} value={item.claim_id}>
                      {uiLabel(item.verification_state)} · {item.normalized_text}
                    </option>
                  ))}
                </select>
              </label>
              {selectedClaim && (
                <div className="claim-status">
                  <span className={`badge ${selectedClaim.verification_state.toLowerCase()}`}>
                    {uiLabel(selectedClaim.verification_state)}
                  </span>
                  <span>{selectedClaim.evidence_count} доказательств</span>
                </div>
              )}

              <div className="form-grid">
                <label className="field">
                  <span>Поисковый запрос</span>
                  <input value={query} onChange={(event) => setQuery(event.target.value)} />
                </label>
              </div>
              <div className="actions">
                <button className="secondary" disabled={busy || !query.trim()} onClick={() => void searchResearch()}>
                  Найти источники
                </button>
              </div>

              {candidates.length > 0 && (
                <div className="research-results">
                  {candidates.map((item) => (
                    <article className="candidate" key={`${item.provider}:${item.external_id}`}>
                      <strong>{item.title}</strong>
                      <small>{item.provider} · {item.publication_year ?? "n.d."} · {item.doi ?? item.external_id}</small>
                      <button className="ghost" disabled={busy} onClick={() => void importCandidate(item)}>
                        Добавить источник
                      </button>
                    </article>
                  ))}
                </div>
              )}

              {source && (
                <div className="source-card">
                  <h4>{source.title}</h4>
                  <p><strong>Статус источника:</strong> {uiLabel(source.access_status)}</p>
                  <p className="muted">
                    Метаданные и место в поиске ничего не доказывают. Для подтверждения нужно изучить сам источник и создать Evidence.
                  </p>
                  {source.access_status !== "FULL_SOURCE_INSPECTED" && (
                    <>
                      <label className="field">
                        <span>Что именно проверено в источнике</span>
                        <textarea
                          rows={2}
                          value={inspectionNote}
                          onChange={(event) => setInspectionNote(event.target.value)}
                          placeholder="Укажите страницу, раздел или другой проверенный фрагмент"
                        />
                      </label>
                      <button className="secondary" disabled={busy || !inspectionNote.trim()} onClick={() => void markInspected()}>
                        Отметить источник изученным
                      </button>
                    </>
                  )}

                  <div className="form-grid">
                    <label className="field">
                      <span>Отношение доказательства к утверждению</span>
                      <select
                        value={relationship}
                        onChange={(event) => setRelationship(event.target.value as typeof relationship)}
                      >
                        <option value="SUPPORTS">{uiLabel("SUPPORTS")}</option>
                        <option value="PARTIALLY_SUPPORTS">{uiLabel("PARTIALLY_SUPPORTS")}</option>
                        <option value="CONTRADICTS">{uiLabel("CONTRADICTS")}</option>
                        <option value="CONTEXT_ONLY">{uiLabel("CONTEXT_ONLY")}</option>
                      </select>
                    </label>
                    <label className="field">
                      <span>Точное место в источнике</span>
                      <input
                        value={pointer}
                        onChange={(event) => setPointer(event.target.value)}
                        placeholder="Страница, раздел, абзац, фрагмент URL или другой точный указатель"
                      />
                    </label>
                    <label className="field">
                      <span>Ограничения доказательства</span>
                      <textarea
                        rows={2}
                        value={limitations}
                        onChange={(event) => setОграничения доказательства(event.target.value)}
                        placeholder="Обязательно для частичного подтверждения"
                      />
                    </label>
                  </div>
                  <button className="primary" disabled={busy || !pointer.trim()} onClick={() => void addEvidence()}>
                    Добавить доказательство
                  </button>
                </div>
              )}

              {evidence.length > 0 && (
                <div className="evidence-list">
                  {evidence.map((item) => (
                    <div key={item.evidence_id}>
                      <strong>{uiLabel(item.relationship)}</strong> · {item.pointer} · {uiLabel(item.status)}
                    </div>
                  ))}
                </div>
              )}

              <div className="citation-check">
                <label className="field">
                  <span>Проверка DOI / идентификатора источника</span>
                  <input
                    value={citationIdentifier}
                    onChange={(event) => setCitationIdentifier(event.target.value)}
                    placeholder="DOI или сохранённый идентификатор источника"
                  />
                </label>
                <button className="ghost" disabled={busy || !citationIdentifier.trim()} onClick={() => void checkCitation()}>
                  Проверить ссылку
                </button>
                {citationCheck && (
                  <p className={citationCheck.resolved ? "healthy" : "alert inline-alert"}>
                    {citationCheck.resolved ? "НАЙДЕНО" : "НЕ НАЙДЕНО"}: {citationCheck.reason}
                  </p>
                )}
              </div>
            </>
          )}
        </>
      )}

      {error && <div className="alert inline-alert">{error}</div>}
    </section>
  );
}
