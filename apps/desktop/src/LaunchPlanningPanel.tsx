import { useCallback, useEffect, useState } from "react";
import { coreApi } from "./api";
import type { BookContractPayload, ChapterView, ProjectView } from "./types";

type LaunchReadiness = {
  openai_credential_state: "AVAILABLE" | "NOT_AVAILABLE";
  yandex_credential_state?: "AVAILABLE" | "NOT_AVAILABLE";
};

type BookModelPin = {
  provider: string;
  provider_label: string;
  model: string;
};

type RoutingState = {
  book_pin: BookModelPin | null;
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
  provider_run_id: string | null;
  prompt_id: string;
  prompt_version: string;
  prompt_hash: string;
  usage: Record<string, unknown>;
  status: string;
  project: ProjectView;
  routing?: RoutingChoice;
};

type BlindCandidate = {
  label: "A" | "B";
  run_id: string;
  contract: BookContractPayload;
};

type BlindComparison = {
  comparison_id: string;
  candidate_a: BlindCandidate;
  candidate_b: BlindCandidate;
  per_request_cap_usd: number;
  total_cap_usd: number;
  models_revealed: false;
};

type BlindSelection = {
  comparison_id: string;
  selected_label: "A" | "B";
  revealed_models: Record<string, string>;
  revealed_run_ids: Record<string, string>;
  project: ProjectView;
};

type Props = {
  project: ProjectView;
  chapter: ChapterView | null;
  onProject: (project: ProjectView) => void;
};

function ContractCandidateCard({
  candidate,
  busy,
  onSelect,
}: {
  candidate: BlindCandidate;
  busy: boolean;
  onSelect: (label: "A" | "B") => void;
}) {
  const contract = candidate.contract;
  return (
    <article className="panel" aria-label={`Вариант ${candidate.label}`}>
      <div className="panel-heading">
        <h4>Вариант {candidate.label}</h4>
        <span className="badge draft">Модель скрыта</span>
      </div>
      <p><strong>Для кого:</strong> {contract.reader}</p>
      <p><strong>Проблема:</strong> {contract.reader_problem}</p>
      <p><strong>Обещание:</strong> {contract.central_promise}</p>
      <p><strong>Центральный тезис:</strong> {contract.central_thesis}</p>
      <p><strong>Уникальный угол:</strong> {contract.unique_angle}</p>
      <p><strong>Траектория читателя:</strong> {contract.reader_trajectory}</p>
      <p><strong>Доказательность:</strong> {contract.evidence_policy}</p>
      <p><strong>Голос и жанр:</strong> {contract.voice_genre_constraints}</p>
      <div>
        <strong>Что исключено:</strong>
        <ul>{contract.explicit_exclusions.map((item) => <li key={item}>{item}</li>)}</ul>
      </div>
      <div>
        <strong>Критерии готовности:</strong>
        <ul>{contract.readiness_criteria.map((item) => <li key={item}>{item}</li>)}</ul>
      </div>
      <button className="primary" disabled={busy} onClick={() => onSelect(candidate.label)}>
        Выбираю вариант {candidate.label}
      </button>
    </article>
  );
}

export function LaunchPlanningPanel({ project, chapter, onProject }: Props) {
  const [readiness, setReadiness] = useState<LaunchReadiness | null>(null);
  const [routingState, setRoutingState] = useState<RoutingState | null>(null);
  const [yandexApiKey, setYandexApiKey] = useState("");
  const [yandexFolderId, setYandexFolderId] = useState("");
  const [idea, setIdea] = useState("");
  const [readerHint, setReaderHint] = useState("");
  const [planningNote, setPlanningNote] = useState("");
  const [maxCostUsd, setMaxCostUsd] = useState("0.50");
  const [allowPaid, setAllowPaid] = useState(false);
  const [blindCostUsd, setBlindCostUsd] = useState("0.50");
  const [allowBlindPaid, setAllowBlindPaid] = useState(false);
  const [blindComparison, setBlindComparison] = useState<BlindComparison | null>(null);
  const [blindSelection, setBlindSelection] = useState<BlindSelection | null>(null);
  const [latestRun, setLatestRun] = useState<PlanningProposal | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const bookPin = routingState?.book_pin ?? null;
  const cost = Number(maxCostUsd);
  const blindCost = Number(blindCostUsd);
  const credentialAvailable = readiness?.openai_credential_state === "AVAILABLE";
  const paidReady =
    credentialAvailable && allowPaid && Number.isFinite(cost) && cost > 0;
  const blindPaidReady =
    credentialAvailable &&
    allowBlindPaid &&
    Number.isFinite(blindCost) &&
    blindCost > 0 &&
    idea.trim().length >= 3;
  const contractApproved =
    project.book_contract?.authority_status === "APPROVED" ||
    project.book_contract?.authority_status === "LOCKED";
  const architectureApproved =
    project.architecture?.authority_status === "APPROVED" ||
    project.architecture?.authority_status === "LOCKED";

  const reloadReadiness = useCallback(async () => {
    setReadiness(await coreApi<LaunchReadiness>("GET", "/api/launch/readiness"));
  }, []);

  const reloadRouting = useCallback(async () => {
    setRoutingState(
      await coreApi<RoutingState>("GET", `/api/projects/${project.book_id}/model-routing`),
    );
  }, [project.book_id]);

  useEffect(() => {
    void Promise.all([reloadReadiness(), reloadRouting()]).catch((reason: unknown) =>
      setError(String(reason)),
    );
  }, [reloadReadiness, reloadRouting]);

  async function saveYandexCredentials() {
    if (!yandexApiKey.trim() || !yandexFolderId.trim()) return;
    setBusy(true);
    setError(null);
    try {
      await coreApi("POST", "/api/launch/yandex-credentials", {
        api_key: yandexApiKey.trim(),
        folder_id: yandexFolderId.trim(),
      });
      setYandexApiKey("");
      setYandexFolderId("");
      await reloadReadiness();
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  async function clearBookPin() {
    setBusy(true);
    setError(null);
    try {
      await coreApi("POST", `/api/projects/${project.book_id}/model-routing/clear-book-pin`);
      setRoutingState({ book_pin: null });
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  async function run(path: string, body: Record<string, unknown>) {
    setBusy(true);
    setError(null);
    try {
      const result = await coreApi<PlanningProposal>("POST", path, {
        ...body,
        provider: "openai",
        model: "gpt-6-astra",
        selection_mode: "MANUAL",
        selection_scope: "OPERATION",
        reasoning_effort: "high",
        max_cost_usd: cost,
      });
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

  async function runBlindComparison() {
    setBusy(true);
    setError(null);
    setBlindComparison(null);
    setBlindSelection(null);
    try {
      const result = await coreApi<BlindComparison>(
        "POST",
        `/api/projects/${project.book_id}/planning/book-contract/blind-compare`,
        {
          idea: idea.trim(),
          reader_hint: readerHint.trim(),
          max_output_tokens: 2600,
          max_cost_usd_per_request: blindCost,
        },
      );
      setBlindComparison(result);
    } catch (reason) {
      setError(String(reason));
    } finally {
      setAllowBlindPaid(false);
      setBusy(false);
    }
  }

  async function selectBlindCandidate(label: "A" | "B") {
    if (!blindComparison) return;
    setBusy(true);
    setError(null);
    try {
      const result = await coreApi<BlindSelection>(
        "POST",
        `/api/projects/${project.book_id}/planning/book-contract/blind-compare/${blindComparison.comparison_id}/select`,
        { selected_label: label },
      );
      setBlindSelection(result);
      onProject(result.project);
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel launch-planning-panel" aria-label="Идея и план книги">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">ТЕКУЩИЙ РАБОЧИЙ ШАГ</p>
          <h3>Идея и план книги</h3>
        </div>
        <span className={`badge ${credentialAvailable ? "approved" : "draft"}`}>
          {credentialAvailable ? "GPT-6 Astra High готов" : "OpenAI не подключён"}
        </span>
      </div>

      <p className="muted">
        Планирование работает в GPT-6 Astra High. BOOK OS создаёт только предложение: контракт книги,
        архитектура и контракты глав становятся авторитетными только после вашего отдельного утверждения.
      </p>

      {!credentialAvailable && (
        <div className="alert inline-alert">
          OpenAI ещё не подключён на этом Mac. Ключ добавляется в «Настройки / Advanced».
        </div>
      )}

      {!contractApproved && (
        <div className="planning-step primary-planning-step">
          <h4>Опишите идею книги</h4>
          <p className="muted">
            Не нужно писать промпт. Достаточно точно объяснить, какую проблему, механизм или вопрос
            должна раскрыть книга.
          </p>
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
                placeholder="Можно оставить пустым — BOOK OS предложит читателя сам."
              />
            </label>
          </div>
        </div>
      )}

      {contractApproved && !architectureApproved && (
        <div className="planning-step primary-planning-step">
          <h4>Подготовьте предложение архитектуры</h4>
          <p className="muted">
            Контракт уже утверждён. Можно дать BOOK OS дополнительное указание — или оставить поле
            пустым и получить структуру строго из контракта.
          </p>
          <label className="field">
            <span>Дополнительное указание — необязательно</span>
            <textarea
              rows={3}
              value={planningNote}
              onChange={(event) => setPlanningNote(event.target.value)}
              placeholder="Например: не делать главы одинакового размера ради симметрии."
            />
          </label>
        </div>
      )}

      {architectureApproved && chapter && (
        <div className="planning-step primary-planning-step">
          <h4>Подготовьте контракт выбранной главы</h4>
          <p className="muted">
            Глава {chapter.ordinal}: {chapter.working_title}. BOOK OS предложит функцию, обязательные
            мысли, исследования, сцены и ограничения этой главы.
          </p>
        </div>
      )}

      {!blindComparison && !blindSelection && (
        <>
          <details className="advanced-settings planning-settings">
            <summary>Изменить лимит расходов — необязательно</summary>
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
              <small>BOOK OS проверяет верхнюю границу стоимости до отправки платного запроса.</small>
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
              Разрешаю <strong>только следующий</strong> платный запрос GPT-6 Astra High.
              Текущий предел — ${maxCostUsd || "0"}. После любой попытки разрешение автоматически сбросится.
            </span>
          </label>
        </>
      )}

      <div className="actions planning-action">
        {!contractApproved && !blindComparison && !blindSelection && (
          <button
            className="ghost"
            disabled={busy || !paidReady || idea.trim().length < 3}
            onClick={() =>
              void run(`/api/projects/${project.book_id}/planning/book-contract`, {
                idea: idea.trim(),
                reader_hint: readerHint.trim(),
                max_output_tokens: 2600,
              })
            }
          >
            {busy ? "Astra работает…" : "Сформировать Book Contract"}
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
            {busy ? "Astra работает…" : "Предложить архитектуру"}
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
            {busy ? "Astra работает…" : "Предложить контракт главы"}
          </button>
        )}
      </div>

      {latestRun && (
        <>
          <div className="planning-run">
            <strong>Черновик создан — проверьте и утвердите, если он вам подходит</strong>
          </div>
          <details className="advanced-settings planning-settings">
            <summary>Настройки / Advanced · данные запуска</summary>
            <p className="muted">
              {latestRun.provider} · {latestRun.model} · run {latestRun.run_id}
            </p>
            {latestRun.routing && (
              <p className="muted">
                {latestRun.routing.selection_mode} · {latestRun.routing.selection_scope ?? "—"} · {latestRun.routing.rationale}
              </p>
            )}
          </details>
        </>
      )}

      <details className="advanced-settings planning-settings">
        <summary>Настройки / Advanced · маршрутизация и служебные инструменты</summary>
        <p className="muted">
          Обычный путь планирования закреплён на GPT-6 Astra High. Альтернативные провайдеры,
          старые book-pin настройки и сравнительные тесты находятся только здесь.
        </p>

        {bookPin && (
          <div className="selected-topic-summary" role="status">
            <small>Существующее ручное закрепление книги</small>
            <strong>{bookPin.provider_label} · {bookPin.model}</strong>
            <span>Обычный Astra-first запуск его не использует.</span>
            <button className="ghost" type="button" disabled={busy} onClick={() => void clearBookPin()}>
              Удалить старое закрепление
            </button>
          </div>
        )}

        {readiness?.yandex_credential_state !== "AVAILABLE" && (
          <div className="credential-setup">
            <label className="field">
              <span>API-ключ AI Ya (Yandex AI Studio)</span>
              <small>Служебный альтернативный провайдер. Ключ сохраняется только в macOS Keychain.</small>
              <input
                type="password"
                autoComplete="off"
                value={yandexApiKey}
                onChange={(event) => setYandexApiKey(event.target.value)}
                placeholder="API key"
              />
            </label>
            <label className="field">
              <span>Folder ID Yandex Cloud</span>
              <input
                value={yandexFolderId}
                onChange={(event) => setYandexFolderId(event.target.value)}
                placeholder="Идентификатор каталога"
              />
            </label>
            <button
              className="ghost"
              disabled={busy || yandexApiKey.trim().length < 10 || yandexFolderId.trim().length < 3}
              onClick={() => void saveYandexCredentials()}
            >
              Сохранить AI Ya в Keychain
            </button>
          </div>
        )}

        {!contractApproved && !blindSelection && (
          <section className="planning-step">
            <h4>Слепой тест OpenAI: Sol ↔ Astra</h4>
            <p className="muted">
              Это отдельный диагностический инструмент. Модели остаются скрыты до выбора варианта.
            </p>

            {!blindComparison && (
              <>
                <label className="field">
                  <span>Максимальная стоимость каждого из двух запросов, USD</span>
                  <input
                    inputMode="decimal"
                    value={blindCostUsd}
                    onChange={(event) => {
                      setBlindCostUsd(event.target.value);
                      setAllowBlindPaid(false);
                    }}
                  />
                  <small>
                    Общий жёсткий предел — до ${
                      Number.isFinite(blindCost) && blindCost > 0 ? (blindCost * 2).toFixed(2) : "0.00"
                    }.
                  </small>
                </label>
                <label className="paid-approval">
                  <input
                    type="checkbox"
                    checked={allowBlindPaid}
                    disabled={!credentialAvailable}
                    onChange={(event) => setAllowBlindPaid(event.target.checked)}
                  />
                  <span>
                    Разрешаю только этот слепой тест: два платных OpenAI-запроса,
                    каждый не дороже ${blindCostUsd || "0"}.
                  </span>
                </label>
                <button
                  className="ghost"
                  disabled={busy || !blindPaidReady}
                  onClick={() => void runBlindComparison()}
                >
                  {busy ? "BOOK OS работает…" : "Получить слепые варианты A и B"}
                </button>
              </>
            )}

            {blindComparison && (
              <>
                <p className="selected-topic-summary" role="status">
                  Модели скрыты. Сначала сравните содержание и выберите сильнейший Book Contract.
                </p>
                <div className="form-grid">
                  <ContractCandidateCard
                    candidate={blindComparison.candidate_a}
                    busy={busy}
                    onSelect={(label) => void selectBlindCandidate(label)}
                  />
                  <ContractCandidateCard
                    candidate={blindComparison.candidate_b}
                    busy={busy}
                    onSelect={(label) => void selectBlindCandidate(label)}
                  />
                </div>
              </>
            )}
          </section>
        )}
      </details>

      {blindSelection && (
        <div className="selected-topic-summary" role="status" aria-live="polite">
          <small>Слепой выбор зафиксирован до раскрытия моделей</small>
          <strong>Выбран вариант {blindSelection.selected_label}</strong>
          <span>A = {blindSelection.revealed_models.A} · B = {blindSelection.revealed_models.B}</span>
          <span>Выбранный вариант перенесён в черновик Book Contract для вашей проверки.</span>
        </div>
      )}

      {error && <div className="alert inline-alert">{error}</div>}
    </section>
  );
}
