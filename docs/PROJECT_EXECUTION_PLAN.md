# BOOK OS — PROJECT EXECUTION PLAN

**Status:** ACCEPTED  
**Version:** 0.3.0  
**Date:** 2026-08-22  
**Canonical repository:** `https://github.com/niknikdym-hue/book-os`

## 1. конечная цель продукта

BOOK OS — специализированная редакционно-авторская операционная система для создания сильного нон-фикшена международного уровня.

Она должна дать одному сильному автору/редактору инфраструктуру полноценной профессиональной команды: исследование, архитектуру книги, написание, developmental editing, доказательность и fact checking, контроль повторов и противоречий, литературную редактуру, сохранение авторского голоса, versioning/provenance, quality gates, human acceptance и выпуск воспроизводимого Literary Master.

BOOK OS **не является** обычным AI writer и не работает по принципу «один prompt → вся книга». Коммерческий успех книги не обещается; ответственность BOOK OS — максимизировать качество рукописи.

Первый пользователь — Owner проекта. Первый реальный пилот — **Business Nonfiction / Book from Zero**.

## 2. Неприкосновенные продуктовые правила

1. **Human authority.** Человек остаётся финальным authority для центрального тезиса, архитектуры, авторского голоса, крупных редакционных изменений и Literary Master.
2. **Bounded change.** `authority → bounded task → proposed patch/version → review → acceptance → new authority`.
3. **No silent mutation.** `APPROVED` и `LOCKED` объекты не изменяются на месте.
4. **Model-agnostic.** Конкретная модель или провайдер не являются архитектурным authority; роли назначаются по BOOK OS evals.
5. **Independent review.** Критический текст не должен писать, оценивать и утверждать один и тот же исполнитель без независимой проверки.
6. **Traceability.** Claims, sources, edits, versions, decisions, approvals и происхождение текста должны быть восстанавливаемы.
7. **GitHub authority.** Чат — рабочая сессия; `main` репозитория — source of truth проекта.
8. **No VPN / no vendor subscription for the user.** Конечный пользователь BOOK OS не должен иметь личную подписку OpenAI/Anthropic/Google/другого модельного провайдера, предоставлять свой API key или пользоваться VPN ради основной функциональности BOOK OS.
9. **No circumvention.** BOOK OS не обходит географические или contractual ограничения модельных провайдеров. Model Gateway выбирает только разрешённые для соответствующего региона пути или собственную/self-hosted инфраструктуру.

## 3. Требование доступности для пользователя из России

BOOK OS должен предоставлять основной продукт пользователю из России **без VPN и без личных подписок на AI-сервисы**.

Следствие для архитектуры:

- пользователь авторизуется только в BOOK OS;
- vendor accounts/API keys принадлежат инфраструктуре BOOK OS, когда это разрешено условиями провайдера;
- личный `BYOK` может существовать позже как опция, но не как требование;
- Model Gateway хранит `provider capability matrix`: региональная доступность, модель, цена, latency, context, data-policy, eval score, разрешённые роли;
- если провайдер не поддерживает регион пользователя или запрещает предоставление доступа этому региону, BOOK OS его не использует для такого запроса;
- для российского контура должны существовать как минимум один разрешённый API/provider path и план self-hosted/open-weight fallback;
- качество регионального пути проверяется теми же BookBench/eval требованиями, а не считается достаточным только потому, что модель доступна.

### Текущий технологический факт, который влияет на проектирование

На 2026-08-22 Россия отсутствует в официальном списке поддерживаемых стран OpenAI API, а OpenAI прямо предупреждает, что доступ или предоставление доступа из неподдерживаемых стран может привести к блокировке. Поэтому **OpenAI API не может быть обязательным runtime-зависимым путём для пользователя из России**.

В качестве реальных кандидатов для российского provider lane уже существуют, например, Yandex Cloud AI Studio/YandexGPT и GigaChat API. Они должны проходить наши собственные литературные и редакционные evals до назначения на критические роли. Self-hosted/open-weight модели остаются резервным архитектурным путём.

References:
- OpenAI API supported countries: https://help.openai.com/en/articles/5347006-openai-api-supported-countries-and-territories
- Yandex Cloud AI Studio APIs: https://yandex.cloud/en/docs/overview/api
- GigaChat API documentation: https://developers.sber.ru/docs/ru/gigachat/api/main

## 3.1 Local-first product direction — ACCEPTED

Опыт локальной Аудиостудии используем как полезный архитектурный ориентир, но не копируем её механически.

Для BOOK OS v0.1 предпочтительно:

- основной пользовательский control plane и рабочее состояние книги находятся под контролем пользователя, а не внутри конкретного AI-чата;
- Book Project, authority, versions, provenance, contracts, decisions и локальные рабочие артефакты должны иметь локально доступное представление и синхронизируемый repository/state;
- внешние LLM, web search, scientific databases, embeddings/inference и другие облачные возможности подключаются через сменные API adapters;
- отказ одного AI-провайдера не должен делать книгу недоступной или разрушать её состояние;
- API keys и secrets не хранятся в Git и не являются частью book authority;
- приложение не обязано быть fully offline: local-first означает ownership/control of state и отсутствие обязательной зависимости от одного облачного интерфейса, а не запрет облачных вычислений;
- позднее можно добавить self-hosted/open-weight inference как resilience/fallback, если качество и стоимость это оправдают.

Это направление подтверждено в `TECHNICAL_ARCHITECTURE_v0.1.md`: принят local-first desktop + local editorial core, с будущим сервисным слоем только там, где он нужен для provider brokerage/sync/billing.

## 4. Два режима продукта

### Mode A — Book from Zero

`Idea → Market & Reader → Thesis → Research → Book Contract → Architecture → Chapter Contracts → bounded Drafting → Editing → Evidence / Fact Check → Cross-book Review → Literary Edit → BookBench → Human Acceptance → Literary Master`

Это первый v0.1 pilot path.

### Mode B — Existing Manuscript / Materials

Принимает существующую рукопись, фрагменты, заметки, интервью и research; формализует их состояние и authority и ведёт по контролируемому редакционному pipeline к Literary Master.

Архитектура обязана допускать оба режима, но первый MVP проверяется на Mode A.

## 5. Первый профиль книги

`Business Nonfiction`.

Пользовательский выбор остаётся простым: один основной подраздел и при необходимости один дополнительный.

Стартовые подразделы:

1. Предпринимательство
2. Стратегия
3. Лидерство
4. Управление
5. Команды и культура
6. Маркетинг и бренд
7. Продажи и переговоры
8. Финансы и инвестиции
9. Продукт, инновации и технологии
10. Карьера и профессиональное развитие

Принцип: **снаружи просто, внутри умно**.

## 6. Кто за что отвечает

### 6.1 Owner — конечный продуктовый и творческий authority

Owner:

- определяет конечную цель и бизнес-приоритеты;
- принимает/отклоняет owner decisions;
- выбирает тему и профиль пилотной книги;
- утверждает Book Contract и архитектуру книги;
- утверждает авторский голос и материальные изменения рукописи;
- принимает ключевые cost/quality trade-offs;
- проводит реальное пользовательское тестирование;
- единолично утверждает Literary Master.

Owner **не обязан** разбирать код и технические детали, если они не меняют продуктовый смысл, стоимость или риски.

### 6.2 Central Brain — управление проектом, архитектура и acceptance

Central Brain:

- начинает работу с чтения актуального `main` и authority;
- защищает продукт от превращения в generic AI writer;
- проектирует ontology, contracts, workflows, BookBench, Model Gateway, Book Memory, research/evidence и technical architecture;
- отделяет `ACCEPTED / PROPOSED / REJECTED / SUPERSEDED`;
- исследует внешние технологии перед build-vs-buy решениями;
- определяет последовательность разработки;
- превращает принятый дизайн в bounded tasks для Codex;
- заранее задаёт acceptance criteria;
- проверяет Codex diffs, tests, evals, scope и architecture drift;
- возвращает результат `ACCEPT / REWORK / OWNER_DECISION_NEEDED / BLOCKED`;
- обновляет authority и checkpoint после принятых этапов.

Central Brain **не является основным программистом** проекта.

### 6.3 Codex — bounded implementation executor

Codex:

- работает только против указанного baseline/HEAD;
- реализует ограниченное техническое задание;
- изменяет код, schema/migrations, tests, CI и implementation docs в пределах scope;
- выполняет требуемые tests/build/evals;
- возвращает точный HEAD/branch/PR, changed files и evidence;
- не придумывает product decisions и не расширяет scope сам;
- не меняет accepted architecture молча;
- при архитектурной неопределённости возвращает decision request;
- не объявляет собственную реализацию продуктово принятой только потому, что tests зелёные.

## 7. Handoff: Central Brain → Codex → Central Brain → Owner

Каждая техническая работа проходит один и тот же цикл.

### A. Central Brain выдаёт bounded task

Обязательные поля:

- `GOAL`
- `AUTHORITY / BASELINE`
- `IN SCOPE`
- `OUT OF SCOPE`
- `ALLOWED FILES / SYSTEMS`
- `REQUIRED BEHAVIOR`
- `ACCEPTANCE TESTS`
- `REGRESSION REQUIREMENTS`
- `DELIVERABLE / REPORT FORMAT`

### B. Codex выполняет

Возвращает реализацию и доказательства, а не только словесный отчёт.

### C. Central Brain делает acceptance

Проверяет соответствие authority, scope, tests, regressions, скрытые допущения, стоимость и сложность.

### D. Owner участвует только когда нужно

Owner decision требуется для изменения product intent, значительного scope, творческого authority, существенного cost/risk trade-off или Literary Master.

## 8. Что и где лежит в репозитории

Текущая минимальная структура:

```text
book-os/
├── README.md
└── docs/
    ├── BOOK_OS_AUTHORITY.md
    ├── PROJECT_EXECUTION_PLAN.md
    ├── PROJECT_STATE.md
    └── decisions/
```

Назначение:

- `README.md` — точка входа и recovery order.
- `BOOK_OS_AUTHORITY.md` — принятые продуктовые/архитектурные правила.
- `PROJECT_EXECUTION_PLAN.md` — конечная цель, роли, roadmap, handoff и критерии MVP.
- `PROJECT_STATE.md` — текущий checkpoint: где мы сейчас, что активно, что заблокировано, какой следующий шаг.
- `decisions/` — отдельные существенные решения, когда они становятся слишком большими для краткого authority summary.

По мере реализации структура расширяется только по принятой Technical Architecture. Milestone 0 создаёт `apps/desktop`, `services/local-core`, CI и минимальные tooling/config файлы; остальные каталоги добавляются по реальной необходимости.

## 9. Recovery Protocol — независимость от чата

Если текущий чат исчез, новый Central Brain должен:

1. открыть `README.md`;
2. прочитать `docs/BOOK_OS_AUTHORITY.md`;
3. прочитать `docs/PROJECT_EXECUTION_PLAN.md`;
4. прочитать `docs/PROJECT_STATE.md`;
5. прочитать относящиеся к текущей задаче файлы `docs/decisions/`;
6. проверить актуальный `main`, последние commits, открытые PR и tests/evals;
7. восстановить: текущую цель, phase, baseline, pending decisions, active task и next permitted step;
8. продолжить именно с checkpoint, а не пересобирать проект из памяти чата.

**Если информация из чата конфликтует с `main`, побеждает repository authority.**

После каждого принятого milestone `PROJECT_STATE.md` обновляется в том же repository change.

## 10. План реализации

### PHASE 0 — Governance / recovery foundation

Цель: убрать зависимость от чата.

Результат:
- canonical GitHub repository;
- authority;
- execution plan;
- checkpoint/recovery protocol;
- role split.

Gate: важные решения не существуют только в чате.

### PHASE 1 — Core Ontology v0.1

Цель: формально определить, что такое книга внутри BOOK OS.

Проектируем:
- `BOOK`;
- Book Contract;
- Architecture;
- Chapter / Chapter Contract;
- Claim / Source / Evidence;
- Scene / Example;
- Style Profile;
- Editorial Finding;
- Patch / Proposal;
- Decision / Approval;
- Version;
- Literary Master;
- Business Book Profile.

Gate: реальная книга описывается без неоднозначности и без привязки к одной LLM.

### PHASE 2 — Technical Architecture + Regional Model Gateway

Цель: выбрать минимальную профессиональную архитектуру.

Проектируем:
- backend/frontend boundaries;
- storage/data model;
- workflow/checkpoints;
- Model Gateway;
- provider capability/region matrix;
- fallback strategy;
- research-provider interface;
- Book Memory;
- provenance/versioning;
- security/secrets;
- observability/evals;
- build-vs-buy;
- stack.

Gate: существует законный/разрешённый no-VPN runtime path для российского пользователя и ни один критический продуктовый путь не зависит от OpenAI subscription/API availability в России.

### PHASE 3 — Core Foundation

Codex начинает production implementation только здесь.

Результат:
- reproducible repository/dev setup;
- schema/migrations;
- tests;
- CI;
- configuration/secrets;
- observability baseline.

### PHASE 4 — Authority & Version Engine

Результат:
- versioned objects;
- statuses/workflow stages;
- immutable approved/locked authority;
- proposals/diffs;
- accept/reject;
- snapshots/rollback;
- Literary Master primitive.

Gate: approved authority нельзя тихо перезаписать кодом или моделью.

### PHASE 5 — Book-from-Zero authoring path

Результат:
- create book;
- Business + subtype;
- Idea / Reader & Market / Thesis;
- Book Contract;
- Architecture;
- Chapter Contract;
- bounded Draft;
- first Model Gateway providers.

Gate: одна глава создаётся из accepted contracts без uncontrolled whole-book generation.

### PHASE 6 — Research Engine & Claim Ledger

Результат:
- source discovery/ingestion;
- bibliographic metadata;
- Claim Ledger;
- evidence links/strength;
- contradictory evidence;
- fact-check decisions;
- research provenance.

Gate: material factual claims имеют трассируемое evidence state.

### PHASE 7 — Book Memory & Cross-book Intelligence

Результат:
- exact retrieval;
- semantic retrieval;
- structured state retrieval;
- repetitions;
- contradictions;
- forgotten promises;
- cross-book findings.

### PHASE 8 — Editorial Roles + Style + BookBench v0.1

Результат:
- bounded agent roles;
- Author Voice Profile;
- AI-prose pathology detector;
- developmental/editorial checks;
- deterministic/semantic/model evals;
- multi-model review where useful;
- explainable findings, not a magical aggregate score.

### PHASE 9 — Human Acceptance Workspace

Результат:
- project status;
- authority view;
- pending decisions;
- proposed diff;
- evidence/findings;
- accept/reject;
- chapter/book progress;
- Literary Master release action.

Gate: Owner ощущает «я управляю созданием книги», а не «я переписываюсь с нейросетью».

### PHASE 10 — Real Business Book Pilot

Проводим настоящую книгу от Idea до Literary Master.

Сохраняем собственный moat corpus:

`original → proposed edit → accepted/rejected → reason → final`

### PHASE 11 — MVP acceptance and hardening

MVP принимается только если доказаны:

- end-to-end Book-from-Zero path;
- quality gain against simpler AI drafting baseline;
- traceable claims/evidence;
- no silent mutation of authority;
- useful whole-book/editorial findings;
- human-controllable author voice;
- reproducible Literary Master;
- recovery from repository without chat history;
- no-VPN/no-vendor-subscription user path for Russia;
- acceptable cost/latency on the real pilot.

## 11. Что строим сами / что покупаем через API

### Собственная IP BOOK OS

- ontology;
- Authority Protocol;
- Book/Chapter Contracts;
- Claim Ledger semantics;
- editorial workflows;
- Author Voice Fingerprint;
- AI-prose pathology rules;
- BookBench;
- cross-book editorial intelligence;
- human acceptance model;
- editorial decision corpus/evals.

### Commodity infrastructure / APIs

Берём готовыми, если проходят требования:

- LLM/model APIs;
- embeddings;
- search/scientific APIs;
- vector/search infrastructure;
- database/object storage;
- workflow runtime;
- observability;
- auth/billing;
- cloud compute;
- self-hosted open-weight inference platform when needed.

Не создаём свою foundation model на старте.

## 12. Что НЕ делаем до доказательства ядра

- fine-tuning;
- uncontrolled agent swarm;
- automatic publishing;
- cover pipeline;
- EPUB/print production as core MVP;
- audiobook/translation production;
- multi-tenant enterprise collaboration;
- поддержка всех жанров;
- generic “Make the whole book better” function.

## 13. Definition of MVP

BOOK OS v0.1 считается доказанным, когда Owner может начать новую Business Nonfiction книгу с идеи и пройти до воспроизводимого Literary Master через contracts, bounded drafting, evidence, editorial review, BookBench и human acceptance, а система сохраняет authority/provenance и может быть продолжена новым Central Brain только по состоянию GitHub.

## 14. Следующий разрешённый шаг

**Current design task: Core Ontology v0.1.**

Production coding Codex пока не начинается.

## 13. Accepted v0.1 design baseline

The implementation-ready design is indexed in `DESIGN_INDEX.md` and consists of:

- `CORE_ONTOLOGY.md`
- `PRODUCT_SPEC_v0.1.md`
- `EDITORIAL_PROTOCOLS_v0.1.md`
- `RESEARCH_AND_CLAIMS_v0.1.md`
- `MODEL_GATEWAY_v0.1.md`
- `BOOK_MEMORY_v0.1.md`
- `BOOKBENCH_v0.1.md`
- `TECHNICAL_ARCHITECTURE_v0.1.md`
- `SECURITY_AVAILABILITY_v0.1.md`
- `AUDIO_HANDOFF_v0.1.md`
- `IMPLEMENTATION_ROADMAP_v0.1.md`

Detailed internal technical decisions may be executed by Central Brain/Codex under `BOOKOS-DEC-0002` without pausing for Owner approval unless a documented stop condition is triggered.

