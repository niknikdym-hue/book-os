import type { ProjectView } from "./types";

type JourneyState = "done" | "current" | "locked";

type JourneyStep = {
  number: number;
  title: string;
  description: string;
};

const JOURNEY_STEPS: JourneyStep[] = [
  {
    number: 1,
    title: "Тема и идея",
    description: "Выберите доступный раздел и тему, создайте проект книги и сформулируйте исходную идею.",
  },
  {
    number: 2,
    title: "Контракт книги",
    description: "Planner предлагает читателя, проблему, обещание, тезис, угол и границы. Утверждает только автор.",
  },
  {
    number: 3,
    title: "Архитектура",
    description: "BOOK OS предлагает интеллектуальную логику книги, части, главы и переходы. Автор проверяет и утверждает.",
  },
  {
    number: 4,
    title: "Контракты глав",
    description: "Для каждой главы фиксируются функция, новый вклад, доказательства, примеры, начало, финал и переход.",
  },
  {
    number: 5,
    title: "Исследование и написание",
    description: "Research и Writer работают в границах утверждённых контрактов, источников и Словаря мусора.",
  },
  {
    number: 6,
    title: "Редактура",
    description: "Developmental, evidence/fact, cross-book и literary проверки устраняют слабые места рукописи.",
  },
  {
    number: 7,
    title: "BookBench и финальная проверка",
    description: "Система показывает конкретные дефекты качества. Финальные содержательные решения принимает человек.",
  },
  {
    number: 8,
    title: "Literary Master",
    description: "После человеческого принятия создаётся воспроизводимая финальная версия книги.",
  },
];

function authorityApproved(status?: string | null) {
  return status === "APPROVED" || status === "LOCKED";
}

function currentStep(project: ProjectView | null): number {
  if (!project) return 1;

  if (!authorityApproved(project.book_contract?.authority_status)) return 2;
  if (!authorityApproved(project.architecture?.authority_status)) return 3;

  const chapterContractsReady =
    project.chapters.length > 0 &&
    project.chapters.every((chapter) => authorityApproved(chapter.chapter_contract?.authority_status));
  if (!chapterContractsReady) return 4;

  switch (project.workflow_stage) {
    case "WHOLE-BOOK EDIT":
      return 6;
    case "FINAL REVIEW":
      return 7;
    case "LITERARY MASTER":
      return 8;
    default:
      return 5;
  }
}

function stateFor(step: number, current: number, project: ProjectView | null): JourneyState {
  if (!project && step > 1) return "locked";
  if (step < current) return "done";
  if (step === current) return "current";
  return "locked";
}

function nextAction(project: ProjectView | null, current: number): string {
  if (!project) {
    return "Нажмите «Новая книга», выберите доступный раздел и тему. Серые направления видны для ориентира, но не открываются до отдельной проверки качества.";
  }
  switch (current) {
    case 2:
      return "В блоке «Старт книги» введите идею книги. Planner подготовит только черновик контракта; проверьте его и утвердите сами.";
    case 3:
      return "После утверждения контракта попросите Planner предложить архитектуру. Проверьте все части и главы перед утверждением.";
    case 4:
      return "По очереди выберите главы и создайте для каждой контракт. Написание не должно начинаться без ясной функции главы.";
    case 5:
      return "Переходите к исследованию и написанию. Writer обязан соблюдать утверждённые контракты, источники и Словарь мусора.";
    case 6:
      return "Запустите редакционные проверки всей книги и исправляйте только подтверждённые проблемы, сохраняя историю решений.";
    case 7:
      return "Проведите BookBench и финальную человеческую проверку. Оценка системы не заменяет ваше решение.";
    case 8:
      return "Проверьте финальные authority-версии и выпускайте Literary Master только после собственного подтверждения.";
    default:
      return "Продолжайте по текущему этапу книги.";
  }
}

type Props = {
  project: ProjectView | null;
  onStartBook: () => void;
};

export function AuthorJourney({ project, onStartBook }: Props) {
  const current = currentStep(project);

  return (
    <section className="panel author-journey" aria-label="Маршрут создания книги">
      <div className="panel-heading journey-heading">
        <div>
          <p className="eyebrow">МАРШРУТ КНИГИ</p>
          <h2>{project ? "Что делать дальше" : "Создание книги шаг за шагом"}</h2>
        </div>
        {!project && (
          <button type="button" className="primary" onClick={onStartBook}>
            Начать новую книгу
          </button>
        )}
      </div>

      <div className="next-action" role="status">
        <strong>Сейчас</strong>
        <span>{nextAction(project, current)}</span>
      </div>

      <ol className="journey-steps">
        {JOURNEY_STEPS.map((step) => {
          const state = stateFor(step.number, current, project);
          return (
            <li className={`journey-step ${state}`} key={step.number}>
              <span className="journey-number" aria-hidden="true">
                {state === "done" ? "✓" : step.number}
              </span>
              <div>
                <div className="journey-step-title">
                  <strong>{step.title}</strong>
                  <span className={`journey-state ${state}`}>
                    {state === "done" ? "Готово" : state === "current" ? "Текущий шаг" : "Откроется позже"}
                  </span>
                </div>
                <small>{step.description}</small>
              </div>
            </li>
          );
        })}
      </ol>

      <details className="how-to-use" open={!project}>
        <summary>Как пользоваться BOOK OS</summary>
        <div className="how-to-grid">
          <div>
            <strong>1. Не ищите нужную панель сами</strong>
            <p>Смотрите на блок «Сейчас». Он показывает единственное основное действие, которое требуется на текущем этапе.</p>
          </div>
          <div>
            <strong>2. Серое — пока недоступно</strong>
            <p>Разделы, темы и будущие этапы отображаются заранее, но BOOK OS не даст использовать их до готовности соответствующего профиля или предыдущего gate.</p>
          </div>
          <div>
            <strong>3. AI всегда предлагает черновик</strong>
            <p>Planner, Writer и редакторы могут предлагать материал. Контракт книги, архитектуру, важные изменения и Literary Master утверждаете вы.</p>
          </div>
          <div>
            <strong>4. Перед платным запросом есть отдельное разрешение</strong>
            <p>Поставьте галочку и задайте предел стоимости. После попытки разрешение сбрасывается автоматически.</p>
          </div>
          <div>
            <strong>5. Добавляйте мусор сразу</strong>
            <p>Если заметили нежелательный оборот, внесите его в «Словарь мусора». Writer и BookBench будут учитывать пользовательское правило дальше.</p>
          </div>
          <div>
            <strong>6. Не утверждайте то, что не устраивает</strong>
            <p>Сохраните вариант как черновик, исправьте или запросите новое предложение. APPROVED — это ваше содержательное решение, а не формальность.</p>
          </div>
        </div>
      </details>
    </section>
  );
}
