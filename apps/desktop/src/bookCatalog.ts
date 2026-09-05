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
export type CatalogAvailability = "AVAILABLE" | "COMING_SOON";

export type CatalogTopic = {
  id: string;
  label: string;
  description: string;
  availability: CatalogAvailability;
  subtype?: BusinessSubtype;
  note?: string;
};

export type BookCategory = {
  id: string;
  label: string;
  description: string;
  availability: CatalogAvailability;
  topics: readonly CatalogTopic[];
};

export const SUBTYPE_LABELS: Record<BusinessSubtype, string> = {
  Entrepreneurship: "Стартапы и создание бизнеса",
  Strategy: "Стратегия",
  Leadership: "Лидерство",
  Management: "Менеджмент и управление",
  "Teams & Culture": "Команды и корпоративная культура",
  "Marketing & Brand": "Маркетинг, бренд и PR",
  "Sales & Negotiation": "Продажи и переговоры",
  "Finance & Investing": "Финансы и инвестиции",
  "Product, Innovation & Technology": "Продукт, инновации и технологии",
  "Career & Professional Development": "Карьера и профессиональное развитие",
};

// User-facing labels are normalized against familiar Russian bookstore taxonomy while
// internal subtype keys remain stable BOOK OS authority identifiers.
export const BUSINESS_TOPICS: readonly CatalogTopic[] = [
  {
    id: "startups",
    label: "Стартапы и создание бизнеса",
    description: "Идея, проверка спроса, запуск, бизнес-модель, рост и масштабирование.",
    availability: "AVAILABLE",
    subtype: "Entrepreneurship",
  },
  {
    id: "strategy",
    label: "Стратегия",
    description: "Выбор рынка, позиционирование, конкурентные преимущества и стратегические решения.",
    availability: "AVAILABLE",
    subtype: "Strategy",
  },
  {
    id: "leadership",
    label: "Лидерство",
    description: "Роль руководителя, решения, ответственность и развитие лидерской практики.",
    availability: "AVAILABLE",
    subtype: "Leadership",
  },
  {
    id: "management",
    label: "Менеджмент и управление",
    description: "Процессы, делегирование, операционная система компании и управленческие решения.",
    availability: "AVAILABLE",
    subtype: "Management",
  },
  {
    id: "teams",
    label: "Команды и корпоративная культура",
    description: "Командная работа, ответственность, культура, найм и взаимодействие.",
    availability: "AVAILABLE",
    subtype: "Teams & Culture",
  },
  {
    id: "marketing",
    label: "Маркетинг, бренд и PR",
    description: "Ценность для клиента, позиционирование, бренд, коммуникации и маркетинговые системы.",
    availability: "AVAILABLE",
    subtype: "Marketing & Brand",
  },
  {
    id: "sales",
    label: "Продажи и переговоры",
    description: "Продажи, переговоры, работа с клиентом и коммерческие процессы.",
    availability: "AVAILABLE",
    subtype: "Sales & Negotiation",
  },
  {
    id: "product",
    label: "Продукт, инновации и технологии",
    description: "Продуктовое мышление, инновации, технологии и вывод решений на рынок.",
    availability: "AVAILABLE",
    subtype: "Product, Innovation & Technology",
  },
  {
    id: "career",
    label: "Карьера и профессиональное развитие",
    description: "Профессиональный рост, переход к управлению и развитие деловой роли.",
    availability: "AVAILABLE",
    subtype: "Career & Professional Development",
  },
  {
    id: "finance",
    label: "Финансы и инвестиции",
    description: "Финансовые решения, капитал и инвестиционные темы.",
    availability: "COMING_SOON",
    subtype: "Finance & Investing",
    note: "Будет открыто после отдельного усиленного профиля доказательности для финансовых утверждений.",
  },
  {
    id: "personal-effectiveness",
    label: "Личная эффективность",
    description: "Рабочие привычки, продуктивность и организация профессиональной деятельности.",
    availability: "COMING_SOON",
    note: "Отдельный production profile ещё не принят.",
  },
  {
    id: "internet-business",
    label: "Интернет-бизнес",
    description: "Цифровые бизнес-модели, платформы и онлайн-коммерция.",
    availability: "COMING_SOON",
    note: "Тема видима в каталоге, но пока не имеет отдельного проверенного профиля BOOK OS.",
  },
];

export const BOOK_CATEGORIES: readonly BookCategory[] = [
  {
    id: "business",
    label: "Бизнес",
    description: "Деловой нон-фикшен — первый проверяемый production-профиль BOOK OS.",
    availability: "AVAILABLE",
    topics: BUSINESS_TOPICS,
  },
  {
    id: "psychology",
    label: "Психология и саморазвитие",
    description: "Будущий профиль с отдельными требованиями к доказательности и языку.",
    availability: "COMING_SOON",
    topics: [],
  },
  {
    id: "popular-science",
    label: "Научно-популярная литература",
    description: "Потребует отдельного научного evidence-профиля и предметных проверок.",
    availability: "COMING_SOON",
    topics: [],
  },
  {
    id: "history-society",
    label: "История и общество",
    description: "Будущий профиль для исторического и общественного нон-фикшена.",
    availability: "COMING_SOON",
    topics: [],
  },
  {
    id: "memoir",
    label: "Биографии и мемуары",
    description: "Будущий профиль для документального авторского материала.",
    availability: "COMING_SOON",
    topics: [],
  },
  {
    id: "health",
    label: "Здоровье",
    description: "Не будет доступно без отдельного медицинского evidence и safety-профиля.",
    availability: "COMING_SOON",
    topics: [],
  },
];

export const AVAILABLE_BUSINESS_SUBTYPES = BUSINESS_TOPICS.flatMap((topic) =>
  topic.availability === "AVAILABLE" && topic.subtype ? [topic.subtype] : [],
);

export function subtypeLabel(value: string): string {
  return (SUBTYPE_LABELS as Record<string, string>)[value] ?? value;
}
