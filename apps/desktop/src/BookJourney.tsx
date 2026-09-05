import type { ChapterView, ProjectView } from "./types";

type JourneyStatus = "done" | "current" | "locked";

type JourneyStep = {
  id: string;
  label: string;
  description: string;
  status: JourneyStatus;
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
      label: "Тема",
      description: "Направление и рабочий проект выбраны.",
      status: "done",
    },
    {
      id: "contract",
      label: "Идея и контракт",
      description: "BOOK OS формирует предложение; автор проверяет и утверждает.",
      status: contractApproved ? "done" : "current",
    },
    {
      id: "architecture",
      label: "Архитектура",
      description: "Части, главы, функция каждой главы и движение мысли.",
      status: !contractApproved ? "locked" : architectureApproved ? "done" : "current",
    },
    {
      id: "chapters",
      label: "Подготовка глав",
      description: "Контракт каждой главы до систематического написания.",
      status: !architectureApproved ? "locked" : allChapterContractsApproved ? "done" : "current",
    },
    {
      id: "writing",
      label: "Написание",
      description: "Управляемые черновики по утверждённым контрактам глав.",
      status: !allChapterContractsApproved ? "locked" : rank > 2 ? "done" : "current",
    },
    {
      id: "edit",
      label: "Факты и редактура",
      description: "Claim/Evidence, сквозная и литературная редактура.",
      status: rank < 3 ? "locked" : rank > 3 ? "done" : "current",
    },
    {
      id: "bookbench",
      label: "BookBench",
      description: "Проверка качества книги перед финальным решением.",
      status: rank < 4 ? "locked" : rank > 4 ? "done" : "current",
    },
    {
      id: "master",
      label: "Literary Master",
      description: "Финальная воспроизводимая версия после человеческого утверждения.",
      status: rank < 5 ? "locked" : "current",
    },
  ];

  let actionTitle = "Опишите идею книги";
  let actionText =
    "В блоке «Идея и план книги» дайте несколько точных предложений о том, какую проблему или механизм должна исследовать книга. BOOK OS предложит контракт, но не утвердит его за вас.";

  if (project.book_contract && !contractApproved) {
    actionTitle = "Проверьте предложенный контракт книги";
    actionText =
      "Уточните читателя, проблему, обещание, центральный тезис и ограничения. Когда формулировки действительно задают нужную книгу, нажмите «Утвердить контракт книги».";
  } else if (contractApproved && !project.architecture) {
    actionTitle = "Попросите BOOK OS предложить архитектуру";
    actionText =
      "Утверждённый контракт уже является опорой. Теперь BOOK OS может разложить книгу на части и главы; предложение останется черновиком до вашего решения.";
  } else if (project.architecture && !architectureApproved) {
    actionTitle = "Проверьте архитектуру целиком";
    actionText =
      "Просмотрите все части и главы: зачем нужна каждая глава, что нового она добавляет и нет ли повторов. Исправьте структуру и только затем утвердите её.";
  } else if (architectureApproved && !allChapterContractsApproved) {
    actionTitle = chapter ? `Подготовьте контракт главы ${chapter.ordinal}` : "Подготовьте контракты глав";
    actionText =
      "Выберите очередную главу, получите предложение BOOK OS, проверьте её функцию, обязательные мысли, примеры и ограничения, затем утвердите контракт главы.";
  } else if (allChapterContractsApproved && rank <= 2) {
    actionTitle = chapter ? `Пишите главу ${chapter.ordinal}` : "Переходите к написанию";
    actionText =
      "Контуры книги утверждены. Работайте по одной главе: Writer создаёт bounded draft, после чего текст проходит проверку фактов, редактуру и BookBench.";
  } else if (rank === 3) {
    actionTitle = "Проверьте факты и отредактируйте книгу";
    actionText =
      "Свяжите существенные утверждения с проверенными источниками, устраните повторения и слабые места, затем завершите сквозную и литературную редактуру.";
  } else if (rank === 4) {
    actionTitle = "Пройдите финальный BookBench";
    actionText =
      "Проверьте выполнение контракта, доказательность, голос, повторы, структуру и машинные патологии. Оценка не заменяет человеческого решения.";
  } else if (rank >= 5) {
    actionTitle = "Проверьте и выпустите Literary Master";
    actionText =
      "Финальная версия должна ссылаться на точные утверждённые ревизии и проверки. Выпуск остаётся вашим человеческим решением.";
  }

  return (
    <section className="panel journey-panel" aria-label="Маршрут книги">
      <div className="panel-heading journey-heading">
        <div>
          <p className="eyebrow">МАРШРУТ КНИГИ</p>
          <h3>BOOK OS ведёт по шагам</h3>
        </div>
        <span className="journey-progress">
          {steps.filter((step) => step.status === "done").length}/{steps.length} завершено
        </span>
      </div>

      <ol className="journey-steps">
        {steps.map((step, index) => (
          <li key={step.id} className={`journey-step ${step.status}`}>
            <span className="journey-number" aria-hidden="true">
              {step.status === "done" ? "✓" : index + 1}
            </span>
            <div>
              <strong>{step.label}</strong>
              <small>{step.description}</small>
            </div>
            <span className="journey-state">
              {step.status === "done" ? "Готово" : step.status === "current" ? "Сейчас" : "Позже"}
            </span>
          </li>
        ))}
      </ol>

      <div className="next-action" role="status">
        <p className="eyebrow">ЧТО ДЕЛАТЬ СЕЙЧАС</p>
        <strong>{actionTitle}</strong>
        <p>{actionText}</p>
      </div>

      <details className="help-drawer">
        <summary>? Как пользоваться BOOK OS</summary>
        <div className="help-copy">
          <p>
            BOOK OS работает как редакционная система, а не как чат: программа предлагает следующий
            материал, а автор принимает ключевые решения в самом проекте книги.
          </p>
          <ol className="help-steps">
            <li><strong>Смотрите на «Что делать сейчас».</strong> Это главное действие текущего этапа.</li>
            <li><strong>AI создаёт предложения, не решения.</strong> Контракт, архитектуру и значимые изменения утверждает человек.</li>
            <li><strong>Не перескакивайте закрытые шаги.</strong> Следующие этапы становятся доступны после обязательных ворот.</li>
            <li><strong>Словарь мусора находится в «Настройках текста».</strong> Добавленные фразы начинают участвовать в контроле прозы.</li>
            <li><strong>Платный OpenAI-вызов всегда отдельный.</strong> Перед каждым таким запросом нужен явный лимит и разрешение.</li>
            <li><strong>Финальная цель — Literary Master.</strong> Это зафиксированная версия книги, а не просто последний открытый текст.</li>
          </ol>
        </div>
      </details>
    </section>
  );
}
