import { useCallback, useEffect, useState } from "react";
import { coreApi } from "./api";
import type { OpenAIWorkLevel } from "./openaiWorkLevel";
import type { ChapterView, ProjectView } from "./types";

type LaunchReadiness = {
  openai_credential_state: "AVAILABLE" | "NOT_AVAILABLE";
};

type RoutingChoice = {
  provider: string;
  model: string;
  selection_mode: string;
  selection_scope: string | null;
  rationale: string;
};

type PlanningProposal = {
  run_id: string;
  provider: string;
  model: string;
  reasoning_effort?: string | null;
  project: ProjectView;
  routing?: RoutingChoice;
};

type AutoBookState = {
  run_id: string;
  status: "RUNNING" | "DONE" | "FAILED" | "STOPPED";
  phase: string;
  requests_used: number;
  max_requests: number;
  authorized_cost_usd: number;
  max_total_cost_usd: number;
  current_chapter_ordinal: number | null;
  last_action: string;
  output_path: string | null;
  error: string | null;
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
  {
    id: "ASTRA_MEDIUM",
    label: "GPT-6 Astra Medium",
    model: "gpt-6-astra",
    effort: "medium",
    selectionMode: "MANUAL",
  },
  {
    id: "ASTRA_HIGH",
    label: "GPT-6 Astra High",
    model: "gpt-6-astra",
    effort: "high",
    selectionMode: "MANUAL",
  },
  {
    id: "ASTRA_XHIGH",
    label: "GPT-6 Astra Extra High",
    model: "gpt-6-astra",
    effort: "xhigh",
    selectionMode: "MANUAL",
  },
  {
    id: "SOL",
    label: "GPT-5.6 Sol",
    model: "gpt-5.6-sol",
    effort: null,
    selectionMode: "MANUAL",
  },
];

type Props = {
  project: ProjectView;
  chapter: ChapterView | null;
  onProject: (project: ProjectView) => void;
};

function choiceById(id: PlanningChoiceId): PlanningChoice {
  return PLANNING_CHOICES.find((item) => item.id === id) ?? PLANNING_CHOICES[2];
}

export function LaunchPlanningPanel({ project, chapter, onProject }: Props) {
  const [readiness, setReadiness] = useState<LaunchReadiness | null>(null);
  const [choiceId, setChoiceId] = useState<PlanningChoiceId>("ASTRA_HIGH");
  const [idea, setIdea] = useState("");
  const [readerHint, setReaderHint] = useState("");
  const [authorName, setAuthorName] = useState("");
  const [targetCharacters, setTargetCharacters] = useState("180000");
  const [autoTotalBudget, setAutoTotalBudget] = useState("25.00");
  const [autoPerRequestBudget, setAutoPerRequestBudget] = useState("1.00");
  const [autoMaxRequests, setAutoMaxRequests] = useState("40");
  const [prepareLitres, setPrepareLitres] = useState(true);
  const [authorizeAuto, setAuthorizeAuto] = useState(false);
  const [autoState, setAutoState] = useState<AutoBookState | null>(null);
  const [autoBusy, setAutoBusy] = useState(false);

  const [planningNote, setPlanningNote] = useState("");
  const [maxCostUsd, setMaxCostUsd] = useState("0.50");
  const [allowPaid, setAllowPaid] = useState(false);
  const [latestRun, setLatestRun] = useState<PlanningProposal | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedChoice = choiceById(choiceId);
  const credentialAvailable = readiness?.openai_credential_state === "AVAILABLE";
  const contractApproved =
    project.book_contract?.authority_status === "APPROVED" ||
    project.book_contract?.authority_status === "LOCKED";
  const architectureApproved =
    project.architecture?.authority_status === "APPROVED" ||
    project.architecture?.authority_status === "LOCKED";

  const reloadReadiness = useCallback(async () => {
    setReadiness(await coreApi<LaunchReadiness>("GET", "/api/launch/readiness"));
  }, []);

  const reloadAutoState = useCallback(async () => {
    setAutoState(
      await coreApi<AutoBookState | null>("GET", `/api/projects/${project.book_id}/auto-book`),
    );
  }, [project.book_id]);

  useEffect(() => {
    void Promise.all([reloadReadiness(), reloadAutoState()]).catch((reason: unknown) =>
      setError(String(reason)),
    );
  }, [reloadAutoState, reloadReadiness]);

  async function refreshProject() {
    onProject(await coreApi<ProjectView>("GET", `/api/projects/${project.book_id}`));
  }

  async function driveAutoBook(initial: AutoBookState) {
    setAutoBusy(true);
    setError(null);
    let current = initial;
    try {
      for (let step = 0; step < 250 && current.status === "RUNNING"; step += 1) {
        current = await coreApi<AutoBookState>(
          "POST",
          `/api/projects/${project.book_id}/auto-book/advance`,
        );
        setAutoState(current);
        await refreshProject();
      }
      if (current.status === "RUNNING") {
        throw new Error("Auto Book exceeded the local step safety limit");
      }
    } catch (reason) {
      setError(String(reason));
      await reloadAutoState().catch(() => undefined);
    } finally {
      setAutoBusy(false);
    }
  }

  async function startAutoBook() {
    const autoIdea =
      idea.trim() || (contractApproved ? `Продолжить книгу: ${project.working_title}` : "");
    const totalBudget = Number(autoTotalBudget);
    const perRequestBudget = Number(autoPerRequestBudget);
    const maxRequests = Number(autoMaxRequests);
    const target = Number(targetCharacters);
    if (
      !authorizeAuto ||
      autoIdea.length < 3 ||
      !Number.isFinite(totalBudget) ||
      !Number.isFinite(perRequestBudget) ||
      !Number.isInteger(maxRequests) ||
      !Number.isInteger(target) ||
      totalBudget <= 0 ||
      perRequestBudget <= 0 ||
      maxRequests <= 0 ||
      target < 4000
    ) {
      return;
    }

    setAutoBusy(true);
    setError(null);
    try {
      const started = await coreApi<AutoBookState>(
        "POST",
        `/api/projects/${project.book_id}/auto-book/start`,
        {
          idea: autoIdea,
          reader_hint: readerHint.trim(),
          author_name: authorName.trim(),
          target_characters: target,
          model_choice: choiceId,
          max_cost_usd_per_request: perRequestBudget,
          max_total_cost_usd: totalBudget,
          max_requests: maxRequests,
          prepare_litres_docx: prepareLitres,
          owner_authorizes_auto_progress: true,
        },
      );
      setAutoState(started);
      setAuthorizeAuto(false);
      await driveAutoBook(started);
    } catch (reason) {
      setError(String(reason));
      setAutoBusy(false);
    }
  }

  async function stopAutoBook() {
    try {
      setAutoState(
        await coreApi<AutoBookState>(
          "POST",
          `/api/projects/${project.book_id}/auto-book/stop`,
        ),
      );
    } catch (reason) {
      setError(String(reason));
    }
  }

  async function runManual(path: string, body: Record<string, unknown>) {
    const cost = Number(maxCostUsd);
    if (!Number.isFinite(cost) || cost <= 0) return;
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

  const autoCanStart =
    credentialAvailable &&
    authorizeAuto &&
    (contractApproved || idea.trim().length >= 3) &&
    !autoBusy;

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
          Выберите Auto, Astra или Sol. Фактическая модель и параметры сохраняются с каждым
          результатом.
        </p>
        <div className="writer-levels writer-astra-modes" role="group" aria-label="Модель планирования">
          {PLANNING_CHOICES.map((choice) => (
            <button
              key={choice.id}
              type="button"
              className={choiceId === choice.id ? "active" : ""}
              aria-pressed={choiceId === choice.id}
              disabled={busy || autoBusy}
              onClick={() => {
                setChoiceId(choice.id);
                setAllowPaid(false);
                setAuthorizeAuto(false);
              }}
            >
              {choice.label}
            </button>
          ))}
        </div>
        {choiceId === "AUTO" && (
          <p className="selected-topic-summary" role="status">
            Auto использует реальную маршрутизацию BOOK OS. Основной контур создания книги сейчас
            Astra-first; выбранная модель всё равно записывается в историю каждого запуска.
          </p>
        )}
      </section>

      {!credentialAvailable && (
        <div className="alert inline-alert">
          OpenAI ещё не подключён на этом Mac. Ключ добавляется в «Настройки / Advanced».
        </div>
      )}

      <section className="planning-step primary-planning-step" aria-label="Авто-книга">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">ОСНОВНОЙ РЕЖИМ</p>
            <h4>Создать книгу автоматически</h4>
          </div>
          {autoState && (
            <span className={`badge ${autoState.status === "DONE" ? "approved" : "draft"}`}>
              {autoState.status}
            </span>
          )}
        </div>
        <p className="muted">
          BOOK OS проходит контракт, архитектуру, контракты глав и написание глав. Одно ваше
          разрешение относится только к этому запуску и ограничено общим бюджетом.
        </p>

        {!contractApproved && autoState?.status !== "RUNNING" && (
          <div className="form-grid">
            <label className="field">
              <span>Идея книги</span>
              <textarea
                rows={5}
                value={idea}
                onChange={(event) => setIdea(event.target.value)}
                placeholder="Опишите тему, проблему, механизм или результат для читателя."
              />
            </label>
            <label className="field">
              <span>Кому книга — необязательно</span>
              <textarea
                rows={5}
                value={readerHint}
                onChange={(event) => setReaderHint(event.target.value)}
                placeholder="Можно оставить пустым — модель предложит читателя сама."
              />
            </label>
          </div>
        )}

        {autoState?.status !== "RUNNING" && !autoBusy && autoState?.status !== "DONE" && (
          <>
            <div className="form-grid">
              <label className="field">
                <span>Автор / псевдоним</span>
                <input
                  value={authorName}
                  onChange={(event) => setAuthorName(event.target.value)}
                  placeholder="Например: Елена Дилон"
                />
                <small>Если профиль книги уже настроен, BOOK OS использует его.</small>
              </label>
              <label className="field">
                <span>Желаемый объём, знаков с пробелами</span>
                <input
                  inputMode="numeric"
                  value={targetCharacters}
                  onChange={(event) => setTargetCharacters(event.target.value)}
                />
              </label>
            </div>

            <details className="advanced-settings planning-settings">
              <summary>Бюджет Auto Book</summary>
              <div className="form-grid">
                <label className="field">
                  <span>Общий лимит, USD</span>
                  <input
                    inputMode="decimal"
                    value={autoTotalBudget}
                    onChange={(event) => setAutoTotalBudget(event.target.value)}
                  />
                </label>
                <label className="field">
                  <span>Максимум одного запроса, USD</span>
                  <input
                    inputMode="decimal"
                    value={autoPerRequestBudget}
                    onChange={(event) => setAutoPerRequestBudget(event.target.value)}
                  />
                </label>
                <label className="field">
                  <span>Максимум AI-запросов</span>
                  <input
                    inputMode="numeric"
                    value={autoMaxRequests}
                    onChange={(event) => setAutoMaxRequests(event.target.value)}
                  />
                </label>
              </div>
            </details>

            <label className="paid-approval">
              <input
                type="checkbox"
                checked={prepareLitres}
                onChange={(event) => setPrepareLitres(event.target.checked)}
              />
              <span>
                Подготовить <strong>DOCX для ЛитРес</strong> после написания.
              </span>
            </label>

            <label className="paid-approval">
              <input
                type="checkbox"
                checked={authorizeAuto}
                disabled={!credentialAvailable}
                onChange={(event) => setAuthorizeAuto(event.target.checked)}
              />
              <span>
                Разрешаю этому Auto Book run автоматически проходить этапы и использовать OpenAI
                только в пределах указанного бюджета.
              </span>
            </label>

            <button
              className="primary"
              type="button"
              disabled={!autoCanStart}
              onClick={() => void startAutoBook()}
            >
              Создать книгу автоматически
            </button>
          </>
        )}

        {(autoState?.status === "RUNNING" || autoBusy) && (
          <div className="selected-topic-summary" role="status">
            <strong>{autoBusy ? "Книга создаётся…" : "Auto Book готов продолжить"}</strong>
            <span>{autoState?.last_action ?? "Запуск подготовлен"}</span>
            <small>
              Запросов: {autoState?.requests_used ?? 0}/{autoState?.max_requests ?? 0}
              {autoState?.current_chapter_ordinal
                ? ` · сейчас глава ${autoState.current_chapter_ordinal}`
                : ""}
            </small>
            {!autoBusy && autoState?.status === "RUNNING" && (
              <div className="actions planning-action">
                <button className="primary" type="button" onClick={() => void driveAutoBook(autoState)}>
                  Продолжить
                </button>
                <button className="ghost" type="button" onClick={() => void stopAutoBook()}>
                  Остановить
                </button>
              </div>
            )}
          </div>
        )}

        {autoState?.status === "DONE" && (
          <div className="selected-topic-summary" role="status">
            <strong>Автоматический проход завершён</strong>
            <span>{autoState.last_action}</span>
            {autoState.output_path && <small>Файл для ЛитРес: {autoState.output_path}</small>}
          </div>
        )}

        {autoState?.status === "FAILED" && (
          <div className="alert inline-alert">
            Auto Book остановлен: {autoState.error ?? autoState.last_action}
          </div>
        )}
      </section>

      <details className="advanced-settings planning-settings">
        <summary>Ручной режим по шагам</summary>
        <div className="planning-step">
          {!contractApproved && (
            <p className="muted">Создать только Book Contract по введённой выше идее.</p>
          )}
          {contractApproved && !architectureApproved && (
            <label className="field">
              <span>Дополнительное указание к архитектуре — необязательно</span>
              <textarea
                rows={3}
                value={planningNote}
                onChange={(event) => setPlanningNote(event.target.value)}
              />
            </label>
          )}
          {architectureApproved && chapter && (
            <p className="selected-topic-summary">
              Глава {chapter.ordinal}: {chapter.working_title}
            </p>
          )}

          <label className="field">
            <span>Максимальная стоимость одного ручного запроса, USD</span>
            <input
              inputMode="decimal"
              value={maxCostUsd}
              onChange={(event) => {
                setMaxCostUsd(event.target.value);
                setAllowPaid(false);
              }}
            />
          </label>
          <label className="paid-approval">
            <input
              type="checkbox"
              checked={allowPaid}
              disabled={!credentialAvailable}
              onChange={(event) => setAllowPaid(event.target.checked)}
            />
            <span>Разрешаю только следующий ручной OpenAI-запрос.</span>
          </label>

          <div className="actions planning-action">
            {!contractApproved && (
              <button
                className="primary"
                disabled={busy || !allowPaid || idea.trim().length < 3}
                onClick={() =>
                  void runManual(`/api/projects/${project.book_id}/planning/book-contract`, {
                    idea: idea.trim(),
                    reader_hint: readerHint.trim(),
                    max_output_tokens: 2600,
                  })
                }
              >
                Сформировать Book Contract
              </button>
            )}
            {contractApproved && !architectureApproved && (
              <button
                className="primary"
                disabled={busy || !allowPaid}
                onClick={() =>
                  void runManual(`/api/projects/${project.book_id}/planning/architecture`, {
                    planning_note: planningNote.trim(),
                    max_output_tokens: 5000,
                  })
                }
              >
                Создать архитектуру
              </button>
            )}
            {architectureApproved && chapter && (
              <button
                className="primary"
                disabled={busy || !allowPaid}
                onClick={() =>
                  void runManual(
                    `/api/projects/${project.book_id}/chapters/${chapter.chapter_id}/planning/contract`,
                    { planning_note: planningNote.trim(), max_output_tokens: 3200 },
                  )
                }
              >
                Подготовить контракт главы
              </button>
            )}
          </div>

          {latestRun && (
            <details className="advanced-settings planning-settings">
              <summary>Данные последнего запуска</summary>
              <p className="muted">
                {latestRun.provider} · {latestRun.model}
                {latestRun.reasoning_effort ? ` · ${latestRun.reasoning_effort}` : ""} · run{" "}
                {latestRun.run_id}
              </p>
              {latestRun.routing && <p className="muted">{latestRun.routing.rationale}</p>}
            </details>
          )}
        </div>
      </details>

      {error && <div className="alert inline-alert">{error}</div>}
    </section>
  );
}
