import { BookContextPanel } from "./BookContextPanel";
import { StylePreviewPanel } from "./StylePreviewPanel";
import type { ChapterView, ProjectView } from "./types";

type JourneyStatus = "done" | "current" | "locked";

type JourneyStep = {
  id: string;
  label: string;
  shortLabel: string;
  description: string;
  status: JourneyStatus;
  target?: string;
};

type Props = {
  project: ProjectView;
  chapter: ChapterView | null;
};

function approved(status?: string | null) {
  return status === "APPROVED" || status === "LOCKED";
}

const stageRank: Record<string, number> = {
  "BOOK DEFINITION": 0,
  ARCHITECTURE: 1,
  WRITING: 2,
  "WHOLE-BOOK EDIT": 3,
  "FINAL REVIEW": 4,
  "LITERARY MASTER": 5,
};

const workflowSummary: Record<string, string> = {
  research: "Проверка фактов и источников",
  editorial: "Редактура книги",
  bookbench: "BookBench",
  master: "Literary Master",
};

function openAndScroll(element: Element | null) {
  if (!element) return;
  if (element instanceof HTMLDetailsElement) element.open = true;
  element.scrollIntoView({ behavior: "smooth", block: "start" });
}

function moveTo(target?: string) {
  if (!target) return;

  if (target === "context") {
    openAndScroll(document.querySelector<HTMLDetailsElement>(".studio-context-drawer"));
    return;
  }

  if (target.startsWith("workflow:")) {
    const key = target.slice("workflow:".length);
    const expected = workflowSummary[key];
    if (!expected) return;
    const drawer = Array.from(
      document.querySelectorAll<HTMLDetailsElement>("details.workflow-drawer"),
    ).find((item) => item.querySelector(":scope > summary")?.textContent?.includes(expected));
    openAndScroll(drawer ?? null);
    return;
  }

  openAndScroll(document.querySelector(target));
}

export function BookJourney({ project, chapter }: Props) {
  const contractApproved = approved(project.book_contract?.authority_status);
  const architectureApproved = approved(project.architecture?.authority_status);
  const allChapterContractsApproved =
    project.chapters.length > 0 &&
    project.chapters.every((item) => approved(item.chapter_contract?.authority_status));
  const rank = stageRank[project.workflow_stage] ?? 0;

  const steps: JourneyStep[] = [
    {
      id: "direction",
      label: "Тема и направление",
      shortLabel: "Тема",
      description: "Проект книги создан.",
      status: "done",
    },
    {
      id: "contract",
      label: "Идея и контракт",
      shortLabel: "Контракт",
      description: "Обещание, тезис и границы книги.",
      status: contractApproved ? "done" : "current",
      target: project.book_contract ? "#book-contract" : ".launch-planning-panel",
    },
    {
      id: "architecture",
      label: "Архитектура",
      shortLabel: "Архитектура",
      description: "Части, главы и движение мысли.",
      status: !contractApproved ? "locked" : architectureApproved ? "done" : "current",
      target: "#architecture",
    },
    {
      id: "chapters",
      label: "Контракты глав",
      shortLabel: "Главы",
      description: "Функция и границы каждой главы.",
      status: !architectureApproved ? "locked" : allChapterContractsApproved ? "done" : "current",
      target: "#chapter-contract",
    },
    {
      id: "writing",
      label: "Исследование и написание",
      shortLabel: "Писать",
      description: "Astra/Writer, факты и управляемые черновики.",
      status: !allChapterContractsApproved ? "locked" : rank > 2 ? "done" : "current",
      target: ".drafting-panel",
    },
    {
      id: "edit",
      label: "Редактура",
      shortLabel: "Редактура",
      description: "Факты, повторы, аргумент и литературная правка.",
      status: rank < 3 ? "locked" : rank > 3 ? "done" : "current",
      target: "workflow:editorial",
    },
    {
      id: "bookbench",
      label: "BookBench / Final Review",
      shortLabel: "Проверить",
      description: "Независимый контроль качества перед выпуском.",
      status: rank < 4 ? "locked" : rank > 4 ? "done" : "current",
      target: "workflow:bookbench",
    },
    {
      id: "master",
      label: "Literary Master",
      shortLabel: "Выпустить",
      description: "Финальная воспроизводимая версия.",
      status: rank < 5 ? "locked" : "current",
      target: "workflow:master",
    },
  ];

  let actionTitle = "Настройте контекст книги";
  let actionText =
    "Автор, серия, стиль и объём должны быть зафиксированы до содержательного AI-планирования.";
  let actionTarget = "context";

  if (project.book_contract && !contractApproved) {
    actionTitle = "Проверьте контракт книги";
    actionText =
      "Уточните читателя, проблему, обещание, центральный тезис и ограничения. Утверждайте только тот контракт, по которому действительно хотите писать всю книгу.";
    actionTarget = "#book-contract";
  } else if (contractApproved && !project.architecture) {
    actionTitle = "Создайте архитектуру";
    actionText =
      "Утверждённый контракт уже является опорой. Теперь BOOK OS может разложить книгу на части и главы; предложение останется черновиком до вашего решения.";
    actionTarget = ".launch-planning-panel";
  } else if (project.architecture && !architectureApproved) {
    actionTitle = "Проверьте архитектуру целиком";
    actionText =
      "Проверьте функцию каждой главы, новый вклад и отсутствие повторов. Исправьте структуру и только затем утвердите её.";
    actionTarget = "#architecture";
  } else if (architectureApproved && !allChapterContractsApproved) {
    actionTitle = chapter ? `Подготовьте главу ${chapter.ordinal}` : "Подготовьте контракты глав";
    actionText =
      "Зафиксируйте функцию, обязательные мысли, примеры и границы очередной главы до систематического написания.";
    actionTarget = "#chapter-contract";
  } else if (allChapterContractsApproved && rank <= 2) {
    actionTitle = chapter ? `Начать работу над главой ${chapter.ordinal}` : "Начать написание";
    actionText =
      "Контуры книги утверждены. Выберите Astra и уровень работы, затем запускайте bounded Writer; после черновика идут факты, независимая критика и редактура.";
    actionTarget = ".drafting-panel";
  } else if (rank === 3) {
    actionTitle = "Довести книгу редактурой";
    actionText =
      "Свяжите существенные утверждения с источниками, устраните повторы и слабые места и проведите сквозную литературную редактуру.";
    actionTarget = "workflow:editorial";
  } else if (rank === 4) {
    actionTitle = "Пройти финальный BookBench";
    actionText =
      "Проверьте выполнение контракта, доказательность, голос, структуру и машинные патологии. Финальное решение остаётся человеческим.";
    actionTarget = "workflow:bookbench";
  } else if (rank >= 5) {
    actionTitle = "Собрать Literary Master";
    actionText =
      "Финальная версия должна ссылаться на точные утверждённые ревизии и проверки и быть готовой к воспроизводимому выпуску.";
    actionTarget = "workflow:master";
  }

  const doneCount = steps.filter((step) => step.status === "done").length;
  const progress = Math.round((doneCount / steps.length) * 100);

  return (
    <>
      <section className="panel journey-panel studio-command" aria-label="Маршрут книги">
        <div className="studio-command-head">
          <div>
            <p className="eyebrow">AUTHOR WORKSPACE</p>
            <h3>Производственный маршрут книги</h3>
            <p className="muted studio-command-copy">
              Один текущий шаг. Завершённое видно сразу. Закрытые этапы нельзя перескочить.
            </p>
          </div>
          <div className="studio-progress" aria-label={`${progress}% маршрута завершено`}>
            <strong>{doneCount}/{steps.length}</strong>
            <span>готово</span>
          </div>
        </div>

        <div className="progress-track" aria-hidden="true">
          <span style={{ width: `${progress}%` }} />
        </div>

        <nav className="journey-command-grid" aria-label="Этапы книги">
          {steps.map((step, index) => (
            <button
              key={step.id}
              type="button"
              className={`journey-command ${step.status}`}
              disabled={step.status === "locked" || !step.target}
              onClick={() => moveTo(step.target)}
              aria-current={step.status === "current" ? "step" : undefined}
              title={step.description}
            >
              <span className="journey-command-index" aria-hidden="true">
                {step.status === "done" ? "✓" : String(index + 1).padStart(2, "0")}
              </span>
              <span className="journey-command-label">{step.shortLabel}</span>
              <span className="journey-command-state">
                {step.status === "done" ? "Готово" : step.status === "current" ? "Сейчас" : "Позже"}
              </span>
            </button>
          ))}
        </nav>

        <div className="next-action studio-next-action" role="status">
          <div>
            <p className="eyebrow">СЕЙЧАС</p>
            <strong>{actionTitle}</strong>
            <p>{actionText}</p>
          </div>
          <button className="studio-next-button" type="button" onClick={() => moveTo(actionTarget)}>
            Перейти к шагу
            <span aria-hidden="true">→</span>
          </button>
        </div>

        <details className="help-drawer studio-context-drawer">
          <summary>Контекст книги, стиль и инструкция</summary>
          <div className="studio-context-stack">
            <BookContextPanel project={project} />
            <StylePreviewPanel bookId={project.book_id} />
            <div className="help-copy">
              <p>
                BOOK OS работает как редакционная система, а не как чат: AI создаёт предложения,
                ключевые решения утверждает автор, а финальной точкой является Literary Master.
              </p>
            </div>
          </div>
        </details>
      </section>
    </>
  );
}
