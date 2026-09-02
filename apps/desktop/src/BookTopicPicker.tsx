export const BUSINESS_SUBTYPES = [
  "Entrepreneurship",
  "Strategy",
  "Leadership",
  "Management",
  "Teams & Culture",
  "Marketing & Brand",
  "Sales & Negotiation",
  "Finance & Investing",
  "Product, Innovation & Technology",
  "Career & Professional Development",
] as const;

export type BusinessSubtype = (typeof BUSINESS_SUBTYPES)[number];

export const SUBTYPE_LABELS: Record<BusinessSubtype, string> = {
  Entrepreneurship: "Стартапы и создание бизнеса",
  Strategy: "Стратегия",
  Leadership: "Лидерство",
  Management: "Менеджмент",
  "Teams & Culture": "Команды и корпоративная культура",
  "Marketing & Brand": "Маркетинг, PR и бренд",
  "Sales & Negotiation": "Продажи и переговоры",
  "Finance & Investing": "Финансы и инвестиции",
  "Product, Innovation & Technology": "Продукт, инновации и технологии",
  "Career & Professional Development": "Карьера и профессиональное развитие",
};

const AVAILABLE_TOPICS: Array<{ value: BusinessSubtype; description: string }> = [
  {
    value: "Entrepreneurship",
    description: "Запуск, проверка идеи, бизнес-модель, рост стартапа и роль основателя.",
  },
  {
    value: "Strategy",
    description: "Выбор направления, конкурентное преимущество, рынок и стратегические решения.",
  },
  {
    value: "Leadership",
    description: "Роль руководителя, лидерские решения, влияние и ответственность.",
  },
  {
    value: "Management",
    description: "Управленческие системы, процессы, контроль, делегирование и масштабирование.",
  },
  {
    value: "Teams & Culture",
    description: "Команды, культура, ответственность, найм и взаимодействие людей.",
  },
  {
    value: "Marketing & Brand",
    description: "Позиционирование, бренд, маркетинговая стратегия, коммуникации и спрос.",
  },
  {
    value: "Sales & Negotiation",
    description: "Продажи, переговоры, клиентские решения и коммерческие процессы.",
  },
  {
    value: "Finance & Investing",
    description: "Финансовые решения бизнеса, инвестиционная логика и управление капиталом.",
  },
  {
    value: "Product, Innovation & Technology",
    description: "Продукт, инновации, технологии, продуктовые решения и развитие продукта.",
  },
  {
    value: "Career & Professional Development",
    description: "Карьера, профессиональный рост, переход в управление и развитие компетенций.",
  },
];

const FUTURE_BUSINESS_TOPICS = [
  "Работа с клиентами",
  "Тайм-менеджмент",
  "Личная эффективность",
  "Интернет-бизнес",
  "Малый и средний бизнес",
  "Недвижимость",
  "Личные финансы",
  "Экономика",
  "Бухучёт, налогообложение и аудит",
  "Банковское дело",
  "Логистика",
] as const;

const FUTURE_SECTIONS = [
  {
    title: "Психология и саморазвитие",
    description: "Отдельный production-profile ещё не принят.",
  },
  {
    title: "Научно-популярная литература",
    description: "Потребуется отдельный evidence/profile gate.",
  },
  {
    title: "Биографии и мемуары",
    description: "Потребуется отдельный narrative/source profile.",
  },
  {
    title: "История",
    description: "Потребуется отдельный исторический evidence profile.",
  },
  {
    title: "Медицина и здоровье",
    description: "Недоступно до отдельного high-stakes evidence profile.",
  },
] as const;

type Props = {
  primarySubtype: BusinessSubtype;
  secondarySubtype: string;
  onPrimarySubtype: (value: BusinessSubtype) => void;
  onSecondarySubtype: (value: string) => void;
};

export function BookTopicPicker({
  primarySubtype,
  secondarySubtype,
  onPrimarySubtype,
  onSecondarySubtype,
}: Props) {
  return (
    <div className="topic-picker" aria-label="Выбор раздела и темы книги">
      <div className="topic-picker-section">
        <div className="subheading">
          <div>
            <span className="step-kicker">1</span>
            <strong>Выберите раздел</strong>
          </div>
          <small>Доступность соответствует реальным production-профилям BOOK OS.</small>
        </div>
        <div className="section-card-grid">
          <button type="button" className="section-card available selected">
            <span className="availability available">Доступно сейчас</span>
            <strong>Бизнес</strong>
            <small>Business Nonfiction · профиль v0.1</small>
          </button>
          {FUTURE_SECTIONS.map((section) => (
            <button
              type="button"
              className="section-card unavailable"
              key={section.title}
              disabled
              title="Направление появится после отдельной проверки качества BOOK OS"
            >
              <span className="availability unavailable">В разработке</span>
              <strong>{section.title}</strong>
              <small>{section.description}</small>
            </button>
          ))}
        </div>
      </div>

      <div className="topic-picker-section">
        <div className="subheading">
          <div>
            <span className="step-kicker">2</span>
            <strong>Выберите тему книги</strong>
          </div>
          <small>Активны только темы, которые поддерживает текущий Business Nonfiction profile.</small>
        </div>
        <div className="topic-card-grid">
          {AVAILABLE_TOPICS.map((topic) => {
            const selected = primarySubtype === topic.value;
            return (
              <button
                type="button"
                key={topic.value}
                className={`topic-card available ${selected ? "selected" : ""}`}
                aria-pressed={selected}
                onClick={() => onPrimarySubtype(topic.value)}
              >
                <span className="availability available">Доступно</span>
                <strong>{SUBTYPE_LABELS[topic.value]}</strong>
                <small>{topic.description}</small>
              </button>
            );
          })}
          {FUTURE_BUSINESS_TOPICS.map((topic) => (
            <button
              type="button"
              key={topic}
              className="topic-card unavailable"
              disabled
              title="Тема видна в каталоге, но пока не имеет отдельного production-profile"
            >
              <span className="availability unavailable">Пока недоступно</span>
              <strong>{topic}</strong>
              <small>Отдельный профиль качества ещё не принят.</small>
            </button>
          ))}
        </div>
      </div>

      <label className="field secondary-topic-field">
        <span>Вторая тема — необязательно</span>
        <small>Используйте только если книга действительно находится на пересечении двух направлений.</small>
        <select value={secondarySubtype} onChange={(event) => onSecondarySubtype(event.target.value)}>
          <option value="">Нет</option>
          {BUSINESS_SUBTYPES.filter((value) => value !== primarySubtype).map((value) => (
            <option key={value} value={value}>
              {SUBTYPE_LABELS[value]}
            </option>
          ))}
        </select>
      </label>
    </div>
  );
}
