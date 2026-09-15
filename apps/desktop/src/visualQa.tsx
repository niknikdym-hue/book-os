import { mockIPC } from "@tauri-apps/api/mocks";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import type { ProjectView } from "./types";
import "./styles.css";
import "./launchUx.css";
import "./studio.css";
import "./authorStudio.css";
import "./authorStudioCorrections.css";
import "./bookSidebar.css";
import "./seriesStudio.css";
import "./authorExperience.css";

const scenario = new URLSearchParams(window.location.search).get("scenario") ?? "home-populated";
const contentScenario = scenario.startsWith("narrow-") ? scenario.slice("narrow-".length) : scenario;
const bookId = "01JQAEXPERIENCE000000000000";
const chapterId = "01JQACHAPTER00000000000000";
const seriesId = "01JQASERIES000000000000000";

const contract = {
  reader: "Владельцы и руководители сервисного бизнеса",
  reader_problem: "Продажи зависят от случайных рекомендаций и личной убедительности",
  central_promise: "Построить воспроизводимую систему продажи сложной услуги",
  central_thesis: "Доверие до покупки создаётся системой проверяемых доказательств",
  unique_angle: "Продажа услуги как проектирование уверенности клиента",
  reader_trajectory: "От хаотичных переговоров к управляемому процессу",
  explicit_exclusions: ["Не сборник скриптов", "Не мотивационная книга"],
  evidence_policy: "Материальные утверждения связывать с проверяемым источником",
  voice_genre_constraints: "Ясный, точный деловой нон-фикшн",
  readiness_criteria: ["Обещание книги выполнено", "Главы не дублируют друг друга"],
};

const architecture = {
  parts: [
    {
      title: "Часть I. Почему услугу трудно купить",
      purpose: "Показать природу риска и доверия",
      chapters: [
        {
          chapter_id: chapterId,
          title: "Невидимый результат",
          purpose: "Объяснить, почему клиент не может оценить услугу заранее",
          new_contribution: "Карта рисков до покупки",
          dependencies: [],
          transition: "От риска к системе доказательств",
        },
      ],
    },
  ],
  intellectual_progression: "Риск → доверие → доказательства → решение",
  concept_allocation: "Каждая глава добавляет отдельный механизм",
  promise_thesis_coverage: "Все элементы обещания покрыты",
  major_transitions: "От объяснения проблемы к рабочей системе",
};

function workflowStage(): string {
  if (["editing"].includes(contentScenario)) return "WHOLE-BOOK EDIT";
  if (["check"].includes(contentScenario)) return "FINAL REVIEW";
  if (["release", "audio-approval"].includes(contentScenario)) return "LITERARY MASTER";
  if (["writing", "running"].includes(contentScenario)) return "WRITING";
  if (contentScenario === "architecture") return "ARCHITECTURE";
  return "BOOK DEFINITION";
}

function project(): ProjectView {
  const stage = workflowStage();
  const hasContract = !["intent", "running"].includes(scenario);
  const hasArchitecture = ["WRITING", "WHOLE-BOOK EDIT", "FINAL REVIEW", "LITERARY MASTER"].includes(stage);
  return {
    book_id: bookId,
    working_title: "Как продавать услуги",
    primary_subtype: "Strategy",
    secondary_subtype: null,
    workflow_stage: stage,
    mode: "BOOK_FROM_ZERO",
    domain: "BUSINESS_NONFICTION",
    profile_version: "business-nonfiction-v0.1",
    book_contract: hasContract
      ? {
          entity_id: "01JQACONTRACT0000000000000",
          revision_id: "01JQACONTRACTREV000000000",
          status: "APPROVED",
          authority_revision_id: "01JQACONTRACTREV000000000",
          authority_status: "APPROVED",
          content: contract,
        }
      : null,
    architecture: hasArchitecture
      ? {
          entity_id: "01JQAARCH0000000000000000",
          revision_id: "01JQAARCHREV000000000000",
          status: "APPROVED",
          authority_revision_id: "01JQAARCHREV000000000000",
          authority_status: "APPROVED",
          content: architecture,
        }
      : null,
    chapters: hasArchitecture
      ? [
          {
            chapter_id: chapterId,
            ordinal: 1,
            working_title: "Невидимый результат",
            architecture_role: "Объяснить природу риска",
            workflow_state: "DRAFTED",
            chapter_contract: {
              entity_id: "01JQACHCONTRACT0000000000",
              revision_id: "01JQACHREVISION0000000000",
              status: "APPROVED",
              authority_revision_id: "01JQACHREVISION0000000000",
              authority_status: "APPROVED",
              content: {
                chapter_purpose: "Объяснить, почему клиент не видит результат заранее",
                new_contribution: "Карта рисков до покупки",
                reader_prior_state: "Считает, что всё решает цена",
                reader_after_state: "Видит систему рисков и доказательств",
                required_claims: ["Нематериальность повышает воспринимаемый риск"],
                required_or_permitted_research: ["Исследования доверия"],
                required_scenes_examples: ["Выбор консультанта"],
                reserved_elsewhere: [],
                opening_requirements: "Начать с узнаваемой ситуации выбора",
                ending_requirements: "Дать карту следующего решения",
                transition_requirements: "Перейти к доказательствам",
              },
            },
          },
        ]
      : [],
  };
}

const autoBook = scenario === "running"
  ? {
      run_id: "01JQARUN00000000000000000",
      status: "RUNNING",
      phase: "CHAPTER_DRAFT",
      current_stage: "WRITING",
      current_chapter_ordinal: 4,
      progress_completed: 8,
      progress_total: 18,
      requests_used: 9,
      max_requests: 40,
      authorized_cost_usd: 5.8,
      estimated_cost_usd: 15.8,
      reserved_cost_usd: 0.9,
      confirmed_cost_usd: 6.42,
      unknown_cost_usd: 0,
      max_total_cost_usd: 25,
      last_action: "Создаю главу 4",
      output_path: null,
      error: null,
    }
  : scenario === "audio-approval"
    ? {
        run_id: "01JQARUN00000000000000000",
        status: "AWAITING_AUDIO_APPROVAL",
        phase: "EXPORT",
        current_stage: "MASTER_AND_EXPORTS",
        progress_completed: 17,
        progress_total: 18,
        requests_used: 24,
        max_requests: 40,
        authorized_cost_usd: 14.6,
        estimated_cost_usd: 18.2,
        reserved_cost_usd: 0.6,
        confirmed_cost_usd: 13.84,
        unknown_cost_usd: 0,
        max_total_cost_usd: 25,
        current_chapter_ordinal: null,
        last_action: "Аудиоредакция ждёт проверки",
        output_path: null,
        audio_script_id: "01JQAAUDIO000000000000000",
        error: null,
      }
    : {
        run_id: "01JQARUN00000000000000000",
        status: scenario === "release" ? "DONE" : "STOPPED",
        phase: scenario === "release" ? "DONE" : "CHAPTER_DRAFT",
        current_stage: scenario === "release" ? "MASTER_AND_EXPORTS" : workflowStage(),
        progress_completed: scenario === "release" ? 18 : 8,
        progress_total: 18,
        requests_used: 18,
        max_requests: 40,
        authorized_cost_usd: 11,
        estimated_cost_usd: 17.8,
        reserved_cost_usd: 0,
        confirmed_cost_usd: 12.4,
        unknown_cost_usd: 0.35,
        max_total_cost_usd: 25,
        current_chapter_ordinal: null,
        last_action: "Работа сохранена",
        output_path: scenario === "release" ? "outputs/Как продавать услуги" : null,
        error: null,
      };

const author = {
  profile_id: "01JQAAUTHOR00000000000000",
  kind: "AUTHOR",
  name: "Елена Дым",
  status: "APPROVED",
  content: { author_name: "Елена Дым" },
  updated_at: "2026-09-13T12:00:00Z",
};

const audioScript = {
  audio_script_id: "01JQAAUDIO000000000000000",
  version: 2,
  status: "PROPOSED",
  source_identity: "literary-master:01JQA",
  source_hash: "a".repeat(64),
  content_hash: "b".repeat(64),
  adaptation_mode: "SOURCE_FAITHFUL",
  content: {
    title: "Как продавать услуги",
    author: "Елена Дым",
    language: "ru",
    sections: [
      {
        source_chapter_id: chapterId,
        title: "Невидимый результат",
        paragraphs: ["Покупатель услуги принимает решение до того, как может увидеть результат."],
        visual_decisions: [],
      },
    ],
  },
  quality_checks: [
    { check_kind: "SOURCE_FIDELITY", state: "PASS", findings: [] },
    {
      check_kind: "LISTENABILITY",
      state: "ATTENTION",
      findings: [{ code: "LONG_SENTENCE", location: "Глава 1", detail: "Проверить ритм вслух", severity: "ATTENTION" }],
    },
  ],
};

const promotionSeriesBooks = [
  ["Как продавать услуги", "Задача клиента, предложение, цена, доказательства и путь до оплаты", "CURRENT_REWRITTEN", "COMPLETED"],
  ["Секреты продвижения услуг психолога в Яндекс Директ", "Поисковый спрос, деликатные обещания и путь до первой встречи", "LEGACY_TITLE_ONLY", "PLANNED"],
  ["Как продвигать юридические услуги в Яндекс Директ: Практическое руководство", "Квалификация юридического обращения и путь до договора", "LEGACY_TITLE_ONLY", "PLANNED"],
  ["Как продать онлайн-курсы", "Проверка спроса, программа, сопровождение и набор", "LEGACY_TITLE_ONLY", "PLANNED"],
  ["Как продавать услуги компаниям: от первого контакта до договора", "Решение о покупке внутри компании", "NEW", "PLANNED"],
  ["Как продвигать местные услуги: клиенты в вашем городе и районе", "Территориальная доступность исполнителя", "NEW", "PLANNED"],
  ["Как продавать дорогие услуги: доверие, доказательства и выбор исполнителя", "Обоснование серьёзного решения о покупке", "NEW", "PLANNED"],
  ["Как возвращать клиентов: повторные продажи и рекомендации в услугах", "Отношения после первой продажи", "NEW", "PLANNED"],
] as const;

mockIPC((command, payload) => {
  if (command === "core_health") return { status: "healthy", version: "0.1.0" };
  if (command !== "core_api") return null;
  const request = (payload as { request: { method: string; path: string } }).request;
  const path = request.path;
  if (path === "/api/projects") return scenario === "home-empty" ? [] : [project()];
  if (path === "/api/library") return [];
  if (path === "/api/context/profiles") return [author];
  if (path === "/api/series/workspaces") {
    return scenario === "home-empty"
      ? []
      : [
          {
            series_profile_id: seriesId,
            name: "Секреты продвижения услуг",
            profile_status: "APPROVED",
            profile_revision: 3,
            territory: "Самостоятельные книги о разных задачах продвижения и продажи услуг",
            books: promotionSeriesBooks.map(([title, uniqueIdea, originKind, lifecycle], index) => ({
              book_id: index === 0 ? bookId : `01JQASERIESBOOK${String(index + 1).padStart(10, "0")}`,
              ordinal: index + 1,
              title,
              unique_idea: uniqueIdea,
              status: lifecycle === "COMPLETED" ? "READY" : "IDEA",
              source_kind: originKind === "CURRENT_REWRITTEN" ? "BOOK_OS" : "PLANNED",
              origin_kind: originKind,
              lifecycle,
              legacy_content_allowed: false,
              current_corpus_eligible: originKind === "CURRENT_REWRITTEN" && lifecycle === "COMPLETED",
              definition_ready: lifecycle === "COMPLETED",
              passport_hash: `qa-passport-${index + 1}`,
              passport_approved: lifecycle === "COMPLETED",
              imported_sources: [],
            })),
            map: { map_hash: "qa-map", status: "PASS", approved: true, current: true, findings: [] },
          },
        ];
  }
  if (path === `/api/series/${seriesId}/costs`) {
    return {
      series_profile_id: seriesId,
      series_confirmed_cost_usd: 1.2,
      books_confirmed_cost_usd: 12.4,
      total_confirmed_cost_usd: 13.6,
      total_estimated_cost_usd: 19.3,
      total_reserved_cost_usd: 0.9,
      total_unknown_cost_usd: 0.35,
      current_books_forecast_low_usd: 15,
      current_books_forecast_high_usd: 17,
      production_forecast_low_usd: 88,
      production_forecast_high_usd: 104,
      production_forecast_status: "COMPARABLE_COMPLETED_BOOKS",
      books: [{ book_id: bookId, title: "Как продавать услуги", confirmed_cost_usd: 12.4, estimated_cost_usd: 5.4, reserved_cost_usd: 0.9, unknown_cost_usd: 0.35, runtime_status: "RUNNING", forecast_total_low_usd: 15, forecast_total_high_usd: 17 }],
      future_books: [{ title: "Как продвигать услуги", forecast_total_low_usd: 13, forecast_total_high_usd: 16 }],
      operations: [],
    };
  }
  if (path === `/api/projects/${bookId}`) return project();
  if (path === `/api/projects/${bookId}/context`) {
    return {
      author_profile: author,
      series_profile: { ...author, profile_id: seriesId, kind: "SERIES", name: "Секреты продвижения услуг" },
      style_profile: null,
      target_characters: 180000,
      ready_for_planning: true,
    };
  }
  if (path === `/api/projects/${bookId}/auto-book/costs`) {
    return {
      book_id: bookId,
      run_id: autoBook?.run_id ?? "qa-run",
      confirmed_cost_usd: autoBook?.confirmed_cost_usd ?? 0,
      estimated_operations_cost_usd: 5.4,
      reserved_cost_usd: autoBook?.reserved_cost_usd ?? 0,
      unknown_cost_usd: autoBook?.unknown_cost_usd ?? 0,
      max_budget_usd: autoBook?.max_total_cost_usd ?? 25,
      forecast_remaining_low_usd: null,
      forecast_remaining_high_usd: null,
      forecast_total_low_usd: null,
      forecast_total_high_usd: null,
      forecast_status: "INSUFFICIENT_DATA",
      categories: [],
      operations: [],
    };
  }
  if (path === `/api/projects/${bookId}/auto-book`) return autoBook;
  if (path.endsWith("/auto-book/audio-script")) return audioScript;
  if (path === "/api/launch/readiness") return { openai_credential_state: "AVAILABLE" };
  if (path.endsWith("/drafts")) {
    return [
      {
        task_id: "qa-task",
        run_id: "qa-run",
        task_status: "COMPLETED",
        run_status: "SUCCEEDED",
        provider: "openai",
        model: "gpt-6-astra",
        selection_mode: "AUTO",
        selection_scope: null,
        routing_rationale: "Выбрано по сложности главы",
        reasoning_effort: "high",
        prompt_id: "section-draft",
        prompt_version: "1",
        prompt_hash: "qa",
        input_revision_id: "qa-input",
        input_revision_hash: "qa-hash",
        unit_id: "qa-unit",
        revision_id: "qa-revision",
        revision_hash: "qa-revision-hash",
        revision_status: "PROPOSED",
        text: "Покупатель услуги принимает решение в условиях двойной неопределённости: он ещё не видит результат и не может отделить обещание от доказательства. Поэтому продажа начинается не со скрипта, а с архитектуры доверия.",
        notes: [],
        provider_run_id: "qa-provider-run",
        usage: {},
        error_code: null,
        error_message: null,
      },
    ];
  }
  if (path.endsWith("/literary-master/readiness")) {
    return { book_id: bookId, ready: true, blockers: [], snapshot_id: "qa-snapshot", snapshot_hash: "qa-hash" };
  }
  if (path.endsWith("/literary-masters")) return [];
  if (path === "/api/anti-junk") return [];
  return [];
});

const root = document.getElementById("root");
if (!root) throw new Error("visual QA root is missing");
createRoot(root).render(<App />);

function clickButton(name: string): boolean {
  const button = Array.from(document.querySelectorAll("button")).find(
    (item) => item.textContent?.replace(/\s+/g, " ").trim().includes(name),
  );
  button?.click();
  return Boolean(button);
}

function wait(milliseconds: number) {
  return new Promise((resolve) => window.setTimeout(resolve, milliseconds));
}

async function prepareScenario() {
  await wait(350);
  if (scenario === "create-book" || scenario === "create-series") {
    clickButton("Создать");
    await wait(80);
    clickButton(scenario === "create-book" ? "Книгу" : "Серию книг");
  } else if (scenario === "series") {
    clickButton("Серии");
  } else if (scenario.startsWith("settings")) {
    clickButton("Настройки");
    await wait(80);
    if (scenario === "settings-costs") clickButton("Расходы");
  } else if (!["home-empty", "home-populated"].includes(scenario)) {
    const open = document.querySelector<HTMLButtonElement>(`[aria-label="Открыть книгу «Как продавать услуги»"]`);
    open?.click();
    await wait(450);
    const stageLabels: Record<string, string> = {
      intent: "Замысел",
      architecture: "Архитектура",
      writing: "Написание",
      editing: "Редактура",
      check: "Проверка",
      release: "Выпуск",
      "audio-approval": "Выпуск",
    };
    const stage = stageLabels[contentScenario];
    if (stage) clickButton(stage);
  }
  await wait(700);
  document.documentElement.dataset.visualQa = "ready";
}

void prepareScenario();
