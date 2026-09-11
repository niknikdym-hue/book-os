import { useCallback, useEffect, useState } from "react";
import { coreApi } from "./api";
import type { ChapterView, ProjectView } from "./types";
import type { OpenAIWorkLevel } from "./openaiWorkLevel";

type LaunchReadiness = {
  openai_credential_state: "AVAILABLE" | "NOT_AVAILABLE";
};

type RoutingChoice = {
  provider: string;
  provider_label: string;
  model: string;
  selection_mode: string;
  selection_scope: string | null;
  operation: string;
  rationale: string;
};

type PlanningProposal = {
  run_id: string;
  run_kind: string;
  provider: string;
  model: string;
  reasoning_effort?: string | null;
  provider_run_id: string | null;
  prompt_id: string;
  prompt_version: string;
  prompt_hash: string;
  usage: Record<string, unknown>;
  status: string;
  project: ProjectView;
  routing?: RoutingChoice;
};

type PlanningChoiceId = "AUTO" | "ASTRA_MEDIUM" | "ASTRA_HIGH" | "ASTRA_XHIGH" | "SOL";

type PlanningChoice = {
  id: PlanningChoiceId;
  label: string;
  model: string | null;
  effort: OpenAIWorkLevel | null;
  selectionMode: "AUTO" | "MANUAL";
};

const PLANNING_CHOICES: readonly PlanningChoice[] = [
  { id: "AUTO", label: "Автоматически", model: null, effort: null, selectionMode: "AUTO" },
  { id: "ASTRA_MEDIUM", label: "GPT-6 Astra Medium", model: "gpt-6-astra", effort: "medium", selectionMode: "MANUAL" },
  { id: "ASTRA_HIGH", label: "GPT-6 Astra High", model: "gpt-6-astra", effort: "high", selectionMode: "MANUAL" },
  { id: "ASTRA_XHIGH", label: "GPT-6 Astra Extra High", model: "gpt-6-astra", effort: "xhigh", selectionMode: "MANUAL" },
  { id: "SOL", label: "GPT-5.6 Sol", model: "gpt-5.6-sol", effort: null, selectionMode: "MANUAL" },
];

type Props = {
  project: ProjectView;
  chapter: ChapterView | null;
  onProject: (project: ProjectView) => void;
};

function choiceById(id: PlanningChoiceId) {
  return PLANNING_CHOICES.find((item) => item.id === id) ?? PLANNING_CHOICES[2];
}

export function LaunchPlanningPanel({ project, chapter, onProject }: Props) {
  const [readiness, setReadiness] = useState<LaunchReadiness | null>(null);
  const [choiceId, setChoiceId] = useState<PlanningChoiceId>("ASTRA_HIGH");
  const [idea, setIdea] = useState("");
  const [readerHint, setReaderHint] = useState("");
  const [planningNote, setPlanningNote] = useState("");
  const [maxCostUsd, setMaxCostUsd] = useState("0.50");
  const [allowPaid, setAllowPaid] = useState(false);
  const [latestRun, setLatestRun] = useState<PlanningProposal | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedChoice = choiceById(choiceId);
  const cost = Number(maxCostUsd);
  const credentialAvailable = readiness?.openai_credential_state === "AVAILABLE";
  const paidReady = credentialAvailable && allowPaid && Number.isFinite(cost) && cost > 0;
  const contractApproved =
    project.book_contract?.authority_status === "APPROVED" ||
    project.book_contract?.authority_status === "LOCKED";
  const architectureApproved =
    project.architecture?.authority_status === "APPROVED" ||
    project.architecture?.authority_status === "LOCKED";

  const reloadReadiness = useCallback(async () => {
    setReadiness(await coreApi<LaunchReadiness>("GET", "/api/launch/readiness"));
  }, []);

  useEffect(() => {
    void reloadReadiness().catch((reason: unknown) => setError(String(reason)));
  }, [reloadReadiness]);

  async function run(path: string, body: Record<string, unknown>) {
    setBusy(true);
    setError(null);
    try {
      const request: Record<string, unknown> = {
        ...body,
        provider: "openai",
        model: selectedChoice.model,
        selection_mode: selectedChoice.selectionMode,
        selection_scope: selectedChoice.selectionMode === "MANUAL" ? "OPERATION" : null,
        max_cost_usd: cost,
      };
      if (selectedChoice.effort) request.reasoning_effort = selectedChoice.effort;

      const result = await coreApi<PlanningProposal>("POST", path, request);
      setLatestRun(result);
      onProject(result.project);
      setAllowPaid(false);
    } catch (reason) {
      setAllowPaid(false);
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  let stepTitle = "Опишите идею книги";
  let stepText =
    "Достаточно своими словами описать, какую проблему, механизм или вопрос должна раскрыть книга.";
  if (contractApproved && !architectureApproved) {
    stepTitle = "Создать архитектуру книги";
    stepText = "BOOK OS разложит утверждённый замысел на части и главы.";
  } else if (architectureApproved && chapter) {
    stepTitle = `Подготовить главу ${chapter.ordinal}`;
    stepText = `Сначала BOOK OS создаст контракт главы «${chapter.working_title}», затем по нему можно писать текст.`;
  }

  return (
    <section className="panel launch-planning-panel" aria-label="Идея и план книги">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">ТЕКУЩИЙ РАБОЧИЙ ШАГ</p>
          <h3>Идея и план книги</h3>
        </div>
        <span className={`badge ${credentialAvailable ? "approved" : "draft"}`}>
          {credentialAvailable ? "OpenAI готов" : "OpenAI не подключён"}
        </span>
      </div>

      <section className="planning-step primary-planning-step" aria-label="AI для этой книги">
        <h4>AI для этой книги</h4>
        <p className="muted">
          Выберите модель сами или оставьте автоматический режим. BOOK OS сохраняет фактическую модель и параметры каждого результата.
        </p>
        <div className="writer-levels writer-astra-modes" role="group" aria-label="Модель планирования">
          {PLANNING_CHOICES.map((choice) => (
            <button
              key={choice.id}
              type="button"
              className={choiceId === choice.id ? "active" : ""}
              aria-pressed={choiceId === choice.id}
              disabled={busy}
              onClick={() => {
                setChoiceId(choice.id);
                setAllowPaid(false);
              }}
            >
              {choice.label}
            </button>
          ))}
        </div>
        {selectedChoice.id === "AUTO" && (
          <p className="selected-topic-summary" role="status">
            Авто — реальная маршрутизация BOOK OS, а не подпись в интерфейсе. Для каждой операции будет сохранена фактически выбранная модель.
          </p>
        )}
      </section>

      {!credentialAvailable && (
        <div className="alert inline-alert">
          OpenAI ещё не подключён на этом Mac. Ключ добавляется в «Настройки / Advanced».
        </div>
      )}

      <section className="planning-step primary-planning-step">
        <h4>{stepTitle}</h4>
        <p className="muted">{stepText}</p>

        {!contractApproved && (
          <div className="form-grid">
            <label className="field">
              <span>Идея книги</span>
              <textarea
                rows={5}
                value={idea}
                onChange={(event) => setIdea(event.target.value)}
                placeholder="Например: почему растущая компания начинает зависеть от личного контроля основателя и как перенести качество решений из его головы в систему управления."
              />
            </label>
            <label className="field">
              <span>Кому эта книга — если уже понятно</span>
              <textarea
                rows={5}
                value={readerHint}
                onChange={(event) => setReaderHint(event.target.value)}
                placeholder="Можно оставить пустым — модель предложит читателя сама."
              />
            </label>
          </div>
        )}

        {contractApproved && !architectureApproved && (
          <label className="field">
            <span>Дополнительное указание — необязательно</span>
            <textarea
              rows={3}
              value={planningNote}
              onChange={(event) => setPlanningNote(event.target.value)}
              placeholder="Например: не делать главы одинакового размера ради симметрии."
            />
          </label>
        )}

        {architectureApproved && chapter && (
          <p className="selected-topic-summary">
            Глава {chapter.ordinal}: {chapter.working_title}
          </p>
        )}
      </section>

      <details className="advanced-settings planning-settings">
        <summary>Лимит расходов — необязательно</summary>
        <label className="field">
          <span>Максимальная стоимость одного запроса, USD</span>
          <input
            inputMode="decimal"
            value={maxCostUsd}
            onChange={(event) => {
              setMaxCostUsd(event.target.value);
              setAllowPaid(false);
            }}
          />
          <small>BOOK OS проверяет верхнюю границу стоимости до отправки запроса.</small>
        </label>
      </details>

      <label className="paid-approval">
        <input
          type="checkbox"
          checked={allowPaid}
          disabled={!credentialAvailable}
          onChange={(event) => setAllowPaid(event.target.checked)}
        />
        <span>
          Разрешаю <strong>только следующий</strong> платный OpenAI-запрос. Текущий предел — ${maxCostUsd || "0"}.
        </span>
      </label>

      <div className="actions planning-action">
        {!contractApproved && (
          <button
            className="primary"
            disabled={busy || !paidReady || idea.trim().length < 3}
            onClick={() =>
              void run(`/api/projects/${project.book_id}/planning/book-contract`, {
                idea: idea.trim(),
                reader_hint: readerHint.trim(),
                max_output_tokens: 2600,
              })
            }
          >
            {busy ? "Модель работает…" : "Сформировать идею и контракт"}
          </button>
        )}

        {contractApproved && !architectureApproved && (
          <button
            className="primary"
            disabled={busy || !paidReady}
            onClick={() =>
              void run(`/api/projects/${project.book_id}/planning/architecture`, {
                planning_note: planningNote.trim(),
                max_output_tokens: 5000,
              })
            }
          >
            {busy ? "Модель работает…" : "Создать архитектуру"}
          </button>
        )}

        {architectureApproved && chapter && (
          <button
            className="primary"
            disabled={busy || !paidReady}
            onClick={() =>
              void run(
                `/api/projects/${project.book_id}/chapters/${chapter.chapter_id}/planning/contract`,
                { planning_note: planningNote.trim(), max_output_tokens: 3200 },
              )
            }
          >
            {busy ? "Модель работает…" : "Подготовить контракт главы"}
          </button>
        )}
      </div>

      {latestRun && (
        <>
          <div className="planning-run">
            <strong>Предложение создано. Фактическая модель: {latestRun.model}</strong>
          </div>
          <details className="advanced-settings planning-settings">
            <summary>Настройки / Advanced · данные запуска</summary>
            <p className="muted">
              {latestRun.provider} · {latestRun.model}
              {latestRun.reasoning_effort ? ` · ${latestRun.reasoning_effort}` : ""} · run {latestRun.run_id}
            </p>
            {latestRun.routing && (
              <p className="muted">
                {latestRun.routing.selection_mode} · {latestRun.routing.selection_scope ?? "—"} · {latestRun.routing.rationale}
              </p>
            )}
          </details>
        </>
      )}

      {error && <div className="alert inline-alert">{error}</div>}
    </section>
  );
}
