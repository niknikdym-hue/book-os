import { useCallback, useEffect, useMemo, useState } from "react";
import { coreApi } from "./api";
import { AutoBookClock } from "./AutoBookClock";
import type { ChapterView, ProjectView } from "./types";

type LaunchApi = <T>(
  method: "GET" | "POST" | "PUT",
  path: string,
  body?: unknown,
) => Promise<T>;

type LaunchReadiness = {
  openai_credential_state: "AVAILABLE" | "NOT_AVAILABLE";
};

type ContextProfile = {
  profile_id: string;
  kind: "AUTHOR" | "SERIES" | "STYLE";
  name: string;
  status: "DRAFT" | "APPROVED";
};

type BookContextView = {
  author_profile: ContextProfile | null;
  target_characters: number | null;
  ready_for_planning: boolean;
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
  started_at?: string | null;
  updated_at?: string | null;
};

type PlanningChoiceId = "AUTO" | "ASTRA_MEDIUM" | "ASTRA_HIGH" | "ASTRA_XHIGH" | "SOL";

type PlanningChoice = {
  id: PlanningChoiceId;
  label: string;
};

const PLANNING_CHOICES: readonly PlanningChoice[] = [
  { id: "AUTO", label: "Автоматически" },
  { id: "ASTRA_MEDIUM", label: "GPT-6 Astra Medium" },
  { id: "ASTRA_HIGH", label: "GPT-6 Astra High" },
  { id: "ASTRA_XHIGH", label: "GPT-6 Astra Extra High" },
  { id: "SOL", label: "GPT-5.6 Sol" },
];

const PROGRESS_STAGES = [
  { label: "Основа книги", threshold: 18 },
  { label: "Архитектура", threshold: 34 },
  { label: "Главы", threshold: 82 },
  { label: "Финальная проверка", threshold: 96 },
  { label: "Готово", threshold: 100 },
] as const;

type Props = {
  project: ProjectView;
  chapter: ChapterView | null;
  onProject: (project: ProjectView) => void;
  coreReady?: boolean;
  api?: LaunchApi;
};

function progressPercent(state: AutoBookState | null): number {
  if (!state) return 0;
  if (state.status === "DONE" || state.phase === "DONE") return 100;
  if (state.phase === "BOOK_CONTRACT") return 8;
  if (state.phase === "APPROVE_BOOK_CONTRACT") return 18;
  if (state.phase === "ARCHITECTURE") return 25;
  if (state.phase === "APPROVE_ARCHITECTURE") return 34;
  if (state.phase === "EXPORT") return 90;
  if (["CHAPTER_CONTRACT", "APPROVE_CHAPTER", "CHAPTER_DRAFT"].includes(state.phase)) {
    const ordinal = Math.max(1, state.current_chapter_ordinal ?? 1);
    const chapterProgress = Math.min(44, (ordinal - 1) * 7);
    const withinChapter =
      state.phase === "CHAPTER_CONTRACT" ? 2 : state.phase === "APPROVE_CHAPTER" ? 4 : 7;
    return Math.min(82, 34 + chapterProgress + withinChapter);
  }
  return state.status === "RUNNING" ? 5 : 0;
}

function progressMessage(state: AutoBookState | null): string {
  if (!state) return "Подготовка запуска";
  if (state.status === "DONE") return "Книга создана и финальная проверка завершена";
  if (state.phase === "BOOK_CONTRACT" || state.phase === "APPROVE_BOOK_CONTRACT") {
    return "Формирую основу и контракт книги";
  }
  if (state.phase === "ARCHITECTURE" || state.phase === "APPROVE_ARCHITECTURE") {
    return "Строю архитектуру книги";
  }
  if (["CHAPTER_CONTRACT", "APPROVE_CHAPTER", "CHAPTER_DRAFT"].includes(state.phase)) {
    return state.current_chapter_ordinal
      ? `Создаю главу ${state.current_chapter_ordinal}`
      : "Создаю главы";
  }
  if (state.phase === "EXPORT") {
    return "Финальная редактура → BookBench → Literary Master → файл";
  }
  return "BOOK OS продолжает создание книги";
}

export function LaunchPlanningPanel({
  project,
  onProject,
  coreReady = true,
  api = coreApi,
}: Props) {
  const [readiness, setReadiness] = useState<LaunchReadiness | null>(null);
  const [bookContext, setBookContext] = useState<BookContextView | null>(null);
  const [profiles, setProfiles] = useState<ContextProfile[]>([]);
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
  const [error, setError] = useState<string | null>(null);

  const credentialAvailable = readiness?.openai_credential_state === "AVAILABLE";
  const contractApproved =
    project.book_contract?.authority_status === "APPROVED" ||
    project.book_contract?.authority_status === "LOCKED";

  const reloadReadiness = useCallback(async () => {
    setReadiness(await api<LaunchReadiness>("GET", "/api/launch/readiness"));
  }, [api]);

  const reloadAutoState = useCallback(async () => {
    setAutoState(
      await api<AutoBookState | null>("GET", `/api/projects/${project.book_id}/auto-book`),
    );
  }, [api, project.book_id]);

  const reloadContext = useCallback(async () => {
    const [context, availableProfiles] = await Promise.all([
      api<BookContextView>("GET", `/api/projects/${project.book_id}/context`),
      api<ContextProfile[]>("GET", "/api/context/profiles"),
    ]);
    setBookContext(context);
    setProfiles(availableProfiles);
    setTargetCharacters((current) =>
      context.target_characters && current === "180000"
        ? String(context.target_characters)
        : current,
    );
  }, [api, project.book_id]);

  useEffect(() => {
    void Promise.all([reloadReadiness(), reloadAutoState(), reloadContext()]).catch(
      (reason: unknown) => setError(String(reason)),
    );
  }, [reloadAutoState, reloadContext, reloadReadiness]);

  async function refreshProject() {
    onProject(await api<ProjectView>("GET", `/api/projects/${project.book_id}`));
  }

  async function driveAutoBook(initial: AutoBookState) {
    setAutoBusy(true);
    setError(null);
    let current = initial;
    try {
      for (let step = 0; step < 250 && current.status === "RUNNING"; step += 1) {
        current = await api<AutoBookState>(
          "POST",
          `/api/projects/${project.book_id}/auto-book/advance`,
        );
        setAutoState(current);
      }
      if (current.status === "RUNNING") {
        throw new Error("Auto Book превысил внутренний безопасный лимит шагов");
      }
      await refreshProject();
    } catch (reason) {
      setError(String(reason));
      await Promise.all([reloadAutoState(), refreshProject()]).catch(() => undefined);
    } finally {
      setAutoBusy(false);
    }
  }

  const approvedAuthors = useMemo(
    () => profiles.filter((item) => item.kind === "AUTHOR" && item.status === "APPROVED"),
    [profiles],
  );
  const ideaReady = contractApproved || idea.trim().length >= 3;
  const authorReady =
    Boolean(bookContext?.author_profile) || authorName.trim().length > 0 || approvedAuthors.length === 1;
  const target = Number(targetCharacters);
  const targetReady = Number.isInteger(target) && target >= 4_000 && target <= 2_000_000;
  const totalBudget = Number(autoTotalBudget);
  const perRequestBudget = Number(autoPerRequestBudget);
  const maxRequests = Number(autoMaxRequests);
  const budgetReady =
    Number.isFinite(totalBudget) &&
    Number.isFinite(perRequestBudget) &&
    Number.isInteger(maxRequests) &&
    totalBudget > 0 &&
    perRequestBudget > 0 &&
    totalBudget >= perRequestBudget &&
    maxRequests > 0;
  const systemReady = coreReady && credentialAvailable;
  const formReady = ideaReady && authorReady && targetReady && budgetReady;
  const autoCanStart = systemReady && formReady && authorizeAuto && !autoBusy;
  const progress = progressPercent(autoState);

  async function startAutoBook() {
    if (!autoCanStart) return;
    const autoIdea =
      idea.trim() || (contractApproved ? `Продолжить книгу: ${project.working_title}` : "");

    setAutoBusy(true);
    setError(null);
    try {
      const started = await api<AutoBookState>(
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
      await reloadAutoState().catch(() => undefined);
      setAutoBusy(false);
    }
  }

  async function stopAutoBook() {
    try {
      setAutoState(
        await api<AutoBookState>("POST", `/api/projects/${project.book_id}/auto-book/stop`),
      );
    } catch (reason) {
      setError(String(reason));
    }
  }

  return (
    <section className="panel launch-planning-panel" aria-label="Запуск Auto Book">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">ОСНОВНОЙ МАРШРУТ</p>
          <h3>Создать книгу</h3>
          <p className="muted launch-intro">
            Заполните обязательные поля. Когда всё готово, кнопка запуска станет зелёной.
          </p>
        </div>
        <span className={`badge ${systemReady ? "approved" : "draft"}`}>
          {systemReady ? "СИСТЕМА ГОТОВА" : "ПОДГОТОВКА СИСТЕМЫ"}
        </span>
      </div>

      {autoState?.status !== "RUNNING" && !autoBusy && autoState?.status !== "DONE" && (
        <>
          <section className="planning-step primary-planning-step" aria-label="Модель для книги">
            <h4>1. Модель</h4>
            <div className="writer-levels writer-astra-modes" role="group" aria-label="Модель Auto Book">
              {PLANNING_CHOICES.map((choice) => (
                <button
                  key={choice.id}
                  type="button"
                  className={choiceId === choice.id ? "active" : ""}
                  aria-pressed={choiceId === choice.id}
                  onClick={() => {
                    setChoiceId(choice.id);
                    setAuthorizeAuto(false);
                  }}
                >
                  {choice.label}
                </button>
              ))}
            </div>
          </section>

          <section className="planning-step primary-planning-step" aria-label="Обязательные данные книги">
            <h4>2. Данные книги</h4>
            {!contractApproved && (
              <div className="form-grid">
                <label className="field required-field">
                  <span>
                    Идея книги <b className="required-mark">*</b>
                  </span>
                  <textarea
                    rows={5}
                    value={idea}
                    onChange={(event) => setIdea(event.target.value)}
                    placeholder="О чём книга и какой результат она должна дать читателю"
                  />
                  {!ideaReady && <small className="field-error">Нужно минимум 3 символа.</small>}
                </label>
                <label className="field">
                  <span>Кому книга — необязательно</span>
                  <textarea
                    rows={5}
                    value={readerHint}
                    onChange={(event) => setReaderHint(event.target.value)}
                    placeholder="Можно оставить пустым — BOOK OS предложит аудиторию сам"
                  />
                </label>
              </div>
            )}

            <div className="form-grid">
              <label className={`field ${authorReady ? "" : "required-field"}`}>
                <span>
                  Автор / псевдоним {!authorReady && <b className="required-mark">*</b>}
                </span>
                <input
                  value={authorName}
                  onChange={(event) => setAuthorName(event.target.value)}
                  placeholder={bookContext?.author_profile?.name ?? "Например: Елена Дилон"}
                />
                <small>
                  {bookContext?.author_profile
                    ? `Уже настроен: ${bookContext.author_profile.name}`
                    : approvedAuthors.length === 1
                      ? `Будет использован профиль: ${approvedAuthors[0].name}`
                      : "Обязательно, если автор ещё не настроен для этой книги."}
                </small>
              </label>
              <label className="field required-field">
                <span>
                  Желаемый объём, знаков с пробелами <b className="required-mark">*</b>
                </span>
                <input
                  inputMode="numeric"
                  value={targetCharacters}
                  onChange={(event) => setTargetCharacters(event.target.value)}
                  aria-invalid={!targetReady}
                />
                <small className={targetReady ? "" : "field-error"}>
                  Минимум 4 000, максимум 2 000 000 знаков.
                </small>
              </label>
            </div>
          </section>

          <details className="advanced-settings planning-settings">
            <summary>Расширенные настройки — обычно менять не нужно</summary>
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
            {!budgetReady && (
              <p className="field-error budget-error">
                Проверьте лимиты: общий бюджет должен быть не меньше лимита одного запроса.
              </p>
            )}
            <label className="paid-approval compact-option">
              <input
                type="checkbox"
                checked={prepareLitres}
                onChange={(event) => setPrepareLitres(event.target.checked)}
              />
              <span>Подготовить DOCX для ЛитРес после финальной проверки.</span>
            </label>
          </details>

          <section className="launch-readiness" aria-label="Готовность к запуску">
            <h4>3. Готовность к запуску</h4>
            <div className="readiness-grid">
              <span className={coreReady ? "ready" : "missing"}>
                {coreReady ? "✓" : "○"} Local Core {coreReady ? "готов" : "запускается"}
              </span>
              <span className={credentialAvailable ? "ready" : "missing"}>
                {credentialAvailable ? "✓" : "○"} OpenAI {credentialAvailable ? "подключён" : "не подключён"}
              </span>
              <span className={ideaReady ? "ready" : "missing"}>
                {ideaReady ? "✓" : "○"} Идея книги
              </span>
              <span className={authorReady ? "ready" : "missing"}>
                {authorReady ? "✓" : "○"} Автор
              </span>
              <span className={targetReady ? "ready" : "missing"}>
                {targetReady ? "✓" : "○"} Объём книги
              </span>
              <span className={budgetReady ? "ready" : "missing"}>
                {budgetReady ? "✓" : "○"} Лимиты Auto Book
              </span>
            </div>
          </section>

          {!credentialAvailable && coreReady && (
            <div className="alert inline-alert">
              OpenAI не подключён. Откройте «Настройки / Advanced» и добавьте API-ключ.
            </div>
          )}

          <label className="paid-approval required-approval">
            <input
              type="checkbox"
              checked={authorizeAuto}
              disabled={!systemReady || !formReady}
              onChange={(event) => setAuthorizeAuto(event.target.checked)}
            />
            <span>
              <b className="required-mark">*</b> Разрешаю этому запуску Auto Book автоматически
              проходить этапы и использовать OpenAI только в заданных лимитах.
            </span>
          </label>

          <button
            className={`primary auto-launch-button ${autoCanStart ? "ready" : ""}`}
            type="button"
            disabled={!autoCanStart}
            onClick={() => void startAutoBook()}
          >
            {autoCanStart ? "Запустить создание книги" : "Запуск станет доступен после заполнения обязательных полей"}
          </button>
        </>
      )}

      {(autoState?.status === "RUNNING" || autoBusy) && (
        <section className="auto-progress" role="status" aria-live="polite">
          <div className="auto-progress-heading">
            <div>
              <p className="eyebrow">AUTO BOOK РАБОТАЕТ</p>
              <h4>{progressMessage(autoState)}</h4>
            </div>
            <strong>{progress}%</strong>
          </div>
          <div
            className="auto-progress-track"
            role="progressbar"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={progress}
          >
            <span style={{ width: `${progress}%` }} />
          </div>
          <ol className="auto-progress-stages">
            {PROGRESS_STAGES.map((stage, index) => {
              const previous = index === 0 ? 0 : PROGRESS_STAGES[index - 1].threshold;
              const done = progress >= stage.threshold;
              const current = !done && progress >= previous;
              return (
                <li key={stage.label} className={done ? "done" : current ? "current" : "pending"}>
                  <span>{done ? "✓" : index + 1}</span>
                  <small>{stage.label}</small>
                </li>
              );
            })}
          </ol>
          <div className="auto-progress-meta">
            <span>
              AI-запросов: {autoState?.requests_used ?? 0}/{autoState?.max_requests ?? maxRequests}
            </span>
            {autoState?.current_chapter_ordinal && (
              <span>Сейчас: глава {autoState.current_chapter_ordinal}</span>
            )}
            <AutoBookClock
              startedAt={autoState?.started_at}
              updatedAt={autoState?.updated_at}
              running={autoState?.status === "RUNNING"}
            />
          </div>

          {autoState?.error && (
            <div className="auto-pause-message">
              <strong>Связь прервалась, но прогресс сохранён.</strong>
              <span>{autoState.error}</span>
            </div>
          )}
          {error && <div className="auto-pause-message">{error}</div>}

          {!autoBusy && autoState?.status === "RUNNING" && (
            <div className="actions planning-action">
              <button className="primary auto-launch-button ready" type="button" onClick={() => void driveAutoBook(autoState)}>
                Продолжить с сохранённого места
              </button>
              <button className="ghost" type="button" onClick={() => void stopAutoBook()}>
                Остановить
              </button>
            </div>
          )}
        </section>
      )}

      {autoState?.status === "DONE" && (
        <section className="auto-progress complete" role="status">
          <div className="auto-progress-heading">
            <div>
              <p className="eyebrow">ГОТОВО</p>
              <h4>Автоматический проход завершён</h4>
            </div>
            <strong>100%</strong>
          </div>
          <div className="auto-progress-track">
            <span style={{ width: "100%" }} />
          </div>
          <p>{autoState.last_action}</p>
          <AutoBookClock startedAt={autoState.started_at} updatedAt={autoState.updated_at} running={false} />
          {autoState.output_path && <small>Файл: {autoState.output_path}</small>}
        </section>
      )}

      {autoState?.status === "FAILED" && (
        <div className="alert inline-alert">
          Предыдущий запуск остановился: {autoState.error ?? autoState.last_action}. Исправьте причину
          и запустите Auto Book снова — уже созданные этапы книги будут использованы.
        </div>
      )}

      {error && autoState?.status !== "RUNNING" && !autoBusy && (
        <div className="alert inline-alert">{error}</div>
      )}
    </section>
  );
}
