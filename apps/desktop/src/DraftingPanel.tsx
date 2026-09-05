import { useEffect, useState } from "react";
import { coreApi } from "./api";
import type { DraftRunView, DraftingPanelProps } from "./draftingTypes";

export function DraftingPanel({ project, chapter, api = coreApi }: DraftingPanelProps) {
  const [objective, setObjective] = useState("");
  const [model, setModel] = useState("gpt-5.6-sol");
  const [maxCostUsd, setMaxCostUsd] = useState("0.50");
  const [allowPaid, setAllowPaid] = useState(false);
  const [context, setContext] = useState("");
  const [runs, setRuns] = useState<DraftRunView[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const approved =
    chapter?.chapter_contract?.authority_status === "APPROVED" ||
    chapter?.chapter_contract?.authority_status === "LOCKED";
  const cost = Number(maxCostUsd);
  const paidReady = allowPaid && Number.isFinite(cost) && cost > 0 && model.trim().length > 0;

  useEffect(() => {
    setRuns([]);
    setError(null);
    if (!chapter) return;
    void api<DraftRunView[]>(
      "GET",
      `/api/projects/${project.book_id}/chapters/${chapter.chapter_id}/drafts`,
    )
      .then(setRuns)
      .catch((reason: unknown) => setError(String(reason)));
  }, [api, chapter, project.book_id]);

  async function generate() {
    if (!chapter || !approved || !objective.trim() || !paidReady) return;
    setBusy(true);
    setError(null);
    try {
      const run = await api<DraftRunView>(
        "POST",
        `/api/projects/${project.book_id}/chapters/${chapter.chapter_id}/drafts`,
        {
          section_objective: objective.trim(),
          provider: "openai",
          model: model.trim(),
          untrusted_context: context.trim() ? [context] : [],
          max_output_tokens: 3500,
          max_cost_usd: cost,
        },
      );
      setRuns((current) => [run, ...current]);
      setAllowPaid(false);
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
          <p className="eyebrow">WRITER · ОГРАНИЧЕННОЕ НАПИСАНИЕ</p>
          <h3>Черновик фрагмента</h3>
        </div>
        <span className="badge draft">ТОЛЬКО ЧЕРНОВИК · НУЖНО РЕШЕНИЕ ЧЕЛОВЕКА</span>
      </div>

      {!chapter && <p className="muted">Сначала выберите главу с утверждённым контрактом.</p>}
      {chapter && !approved && (
        <p className="muted">Перед написанием утвердите контракт этой главы.</p>
      )}

      {chapter && approved && (
        <>
          <div className="form-grid">
            <label className="field">
              <span>Задача этого фрагмента</span>
              <textarea
                rows={4}
                value={objective}
                onChange={(event) => setObjective(event.target.value)}
                placeholder="Что именно должен сделать этот один фрагмент главы?"
              />
            </label>
            <label className="field">
              <span>Модель OpenAI</span>
              <input value={model} onChange={(event) => setModel(event.target.value)} />
            </label>
            <label className="field">
              <span>Максимальная стоимость запроса, USD</span>
              <input
                inputMode="decimal"
                value={maxCostUsd}
                onChange={(event) => setMaxCostUsd(event.target.value)}
              />
            </label>
            <label className="field">
              <span>Дополнительный материал — необязательно</span>
              <small>Хранится как данные и не может изменить authority или расширить задачу.</small>
              <textarea
                rows={5}
                value={context}
                onChange={(event) => setContext(event.target.value)}
                placeholder="Можно вставить ограниченный исходный материал для этого фрагмента"
              />
            </label>
          </div>
          <label className="paid-approval">
            <input
              type="checkbox"
              checked={allowPaid}
              onChange={(event) => setAllowPaid(event.target.checked)}
            />
            <span>Разрешаю следующий платный запрос с указанным пределом стоимости.</span>
          </label>
          <div className="actions">
            <button
              className="primary"
              onClick={() => void generate()}
              disabled={busy || !objective.trim() || !paidReady}
            >
              {busy ? "Writer пишет…" : "Создать черновик"}
            </button>
          </div>
        </>
      )}

      {error && <div className="alert inline-alert">{error}</div>}

      {latest && (
        <div className="draft-result">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">ПОСЛЕДНИЙ ЗАПУСК</p>
              <h4>{latest.revision_status ?? latest.run_status}</h4>
            </div>
            <span className="badge draft">{latest.revision_status ?? latest.run_status}</span>
          </div>
          {latest.text && <article className="draft-copy">{latest.text}</article>}
          <dl className="provenance-grid">
            <div>
              <dt>Провайдер / модель</dt>
              <dd>{latest.provider} · {latest.model}</dd>
            </div>
            <div>
              <dt>Prompt</dt>
              <dd>{latest.prompt_id} · {latest.prompt_version}</dd>
            </div>
            <div>
              <dt>Задача</dt>
              <dd>{latest.task_id}</dd>
            </div>
            <div>
              <dt>Входная revision</dt>
              <dd>{latest.input_revision_id}</dd>
            </div>
          </dl>
          {latest.notes.length > 0 && (
            <ul className="notes-list">{latest.notes.map((note) => <li key={note}>{note}</li>)}</ul>
          )}
        </div>
      )}
    </section>
  );
}
