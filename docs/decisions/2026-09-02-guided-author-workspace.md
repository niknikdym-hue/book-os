# Owner Decision — Guided Author Workspace and Capability-Aware Topic Catalog

**Date:** 2026-09-02  
**Status:** ACCEPTED OWNER DECISION  
**Scope:** BOOK OS native desktop UX for creating and progressing a book

## Decision

The BOOK OS author interface must be self-explanatory and guide the user through the correct order of actions. The user must not need to understand internal architecture, remember a separate workflow, or guess which panel to open next.

The visible author journey is:

`Topic & Idea → Book Contract → Architecture → Chapter Contracts → Research & Writing → Editorial → BookBench / Final Review → Literary Master`

The interface must always show:

1. completed steps;
2. the single current step;
3. later locked steps;
4. a plain-language "what to do now" instruction;
5. built-in "How to use BOOK OS" guidance.

AI output remains proposal-only. Existing human authority gates are not weakened by this UX simplification.

## Topic catalog

New-book creation uses a hierarchical market-facing catalog:

`section → topic → optional secondary topic`

The catalog may use familiar market language validated against major book-store taxonomies, but a visible option is clickable only when BOOK OS has an accepted production profile that can support it at the required quality level.

### Available now

Top-level section:

- Business

Current Business Nonfiction profile values remain the stable internal identifiers. User-facing labels are:

- `Entrepreneurship` → `Стартапы и создание бизнеса`
- `Strategy` → `Стратегия`
- `Leadership` → `Лидерство`
- `Management` → `Менеджмент`
- `Teams & Culture` → `Команды и корпоративная культура`
- `Marketing & Brand` → `Маркетинг, PR и бренд`
- `Sales & Negotiation` → `Продажи и переговоры`
- `Finance & Investing` → `Финансы и инвестиции`
- `Product, Innovation & Technology` → `Продукт, инновации и технологии`
- `Career & Professional Development` → `Карьера и профессиональное развитие`

The label change does not change stored internal subtype identifiers or the accepted Business Nonfiction v0.1 profile.

### Visible but unavailable

The UI should expose plausible future nonfiction sections and business topics for orientation, but they must be visually distinct and non-clickable until a dedicated profile is accepted.

Examples include:

- Psychology and self-development;
- popular science;
- biographies and memoirs;
- history;
- medicine and health;
- customer service;
- time management;
- personal effectiveness;
- internet business;
- small and medium business;
- real estate;
- personal finance;
- economics;
- accounting/tax/audit;
- banking;
- logistics.

No unavailable category may silently route into the Business Nonfiction profile.

## UX principles

- "Simple outside, smart inside" remains authoritative.
- The workflow guide appears before technical working panels.
- Disabled means genuinely unavailable, not merely visually muted.
- Future categories are informative only and cannot create a project.
- Internal codes/statuses remain stable; Russian market-facing labels are presentation-layer concerns.
- The built-in help is part of the application, not dependent on chat or an external manual.
- Paid model calls retain explicit per-call human authorization and cost cap.
- The Anti-Junk lexicon remains a persistent author tool and is explained in the built-in guide.

## Market-language reference

The first market-language pass was checked against the current LitRes genre taxonomy, including `Бизнес-книги`, `Стартапы и создание бизнеса`, `Менеджмент`, `Продажи`, `Маркетинг, PR, реклама`, `Корпоративная культура`, `Финансы`, `Ценные бумаги / инвестиции`, `Поиск работы / карьера`, as well as broader nonfiction groups such as psychology/self-development, popular science, biographies/memoirs, history, and medicine/health.

Store taxonomies are reference vocabulary only. They do not define BOOK OS capability or authority.
