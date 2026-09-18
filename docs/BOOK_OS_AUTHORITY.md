# BOOK OS — PROJECT AUTHORITY

**Status:** ACTIVE AUTHORITY  
**Version:** 0.7.5  
**Date:** 2026-09-18  
**Project:** BOOK OS  
**Canonical repository:** `https://github.com/niknikdym-hue/book-os`

## 0. Authority rule

GitHub `main` is the source of truth for BOOK OS product-development authority.

Chats are disposable working sessions and may contain drafts, hypotheses, rejected ideas or incomplete reasoning. A decision becomes project authority only when recorded in canonical repository authority/specification/decision files.

Accepted decisions are not silently overwritten. A changed decision is versioned and/or explicitly superseded; Git history and decision records preserve prior state.

This v0.7 consolidation preserves all accepted v0.6 product decisions and adds the Owner's explicit world-class module-reuse and dual-execution invariant: BOOK OS must reuse strong mature commodity components where appropriate, concentrate custom engineering on BOOK OS-specific editorial intelligence, use the strongest external execution lane for current frontier-quality work, and build an independent local BOOK OS Brain in parallel without claiming parity until reproducible evaluation proves it per editorial operation.

### Current supersession rule

The approved Owner decision `docs/decisions/2026-08-29-global-openai-first.md` explicitly SUPERSEDES all prior requirements that BOOK OS must prove a Russia/no-VPN runtime lane, Yandex/GigaChat production promotion, or Russia-specific provider availability before the current MVP/pilot GO/NO-GO.

Therefore any older authority/spec/task text that still describes that regional lane as a current gate is historical only and must not be used to restart former M8 / PR #12.

`docs/PROJECT_STATE.md` is the authority for the exact accepted checkpoint and next permitted action.

## 1. Product identity — ACCEPTED

BOOK OS is a specialized editorial-authoring operating system for producing strong nonfiction at an international professional standard.

It is **not** a generic AI writer and **not** a one-prompt book generator.

Its purpose is to give one strong author/editor the intellectual and operational infrastructure of a professional editorial team across research, book architecture, bounded drafting, developmental editing, evidence/fact checking, cross-book editing, literary editing, author-voice control, versioning, provenance, quality gates, human acceptance and release of a Literary Master.

BOOK OS does not promise a bestseller. Its responsibility is manuscript quality; commercial success also depends on topic, author, market, publisher, marketing, timing and external factors.

## 1A. Highest professional quality and current-best methods — ACCEPTED / NON-NEGOTIABLE

This is a permanent project invariant and applies to product design, implementation, evaluation, acceptance and the real-book workflow.

### Book-quality rule

BOOK OS must be built and operated to produce nonfiction at the **highest professional standard realistically achievable**, comparable to work created by a strong professional author, researcher, developmental editor, fact checker, literary editor and production editor working as one disciplined team.

“Technically works”, “tests pass”, “the model returned text”, “the UI is complete” or “the pipeline finished” are **never sufficient acceptance criteria** for a book-producing capability.

A capability that is technically GREEN but predictably produces mediocre, generic, weakly researched, structurally shallow, stylistically synthetic or otherwise sub-professional books is **NOT ACCEPTED**.

Quality includes, where applicable:

- intellectual originality and clarity;
- depth and correctness of research;
- claim/evidence integrity and provenance;
- strong reader promise and thesis;
- professional architecture and chapter function;
- thought density without unnecessary difficulty;
- specificity and useful examples;
- factual accuracy and honest uncertainty;
- coherent whole-book logic and progression;
- genuine author voice and stylistic distinction;
- absence of machine-prose pathologies and editorial junk;
- developmental, line and literary editing quality;
- professional text readability and, when applicable, professional listenability;
- preservation of meaning/concept/evidence when adapting an existing work;
- whole-book consistency, novelty and release readiness.

## 1B. Owner junk-lexicon invariant — ACCEPTED / NON-NEGOTIABLE

This rule applies to **all BOOK OS nonfiction books and series**, including manuscript prose, headings/subheadings, examples, cases, tables, callouts, conclusions, annotations and other book-facing text generated or revised by BOOK OS.

Any word or phrase that the Owner has explicitly designated as a **junk word / junk phrase** in the active BOOK OS anti-junk lexicon is prohibited in BOOK PROSE. It must not be used as a stylistic shortcut, rhetorical filler, marketing formula or decorative abstraction.

### Wordform rule

A prohibited junk item **cannot be made acceptable by changing its grammatical form**.

For Russian lexical items, the prohibition includes ordinary inflectional wordforms that preserve the same lexical meaning, including where applicable:

- case;
- number;
- gender;
- person;
- tense.

Examples: if `опора` is prohibited, `опоры`, `опорой`, `опорах` are also prohibited; if `откликнулась` is prohibited, ordinary forms such as `откликнулся` and `откликнулись` are also prohibited; if `больше не обязан` is prohibited, gender/number variants such as `больше не обязана` and `больше не обязаны` are also prohibited.

Derivational relatives are **not** automatically prohibited merely because they share a root. BOOK OS must distinguish an inflectional wordform from a different lexical item.

### Enforcement consequence

- Writer/Planner generation constraints must include the current Owner-designated junk lexicon.
- Deterministic post-generation checks must reject prohibited junk items and their covered wordforms before the text can be accepted as book prose.
- A model, editor or downstream formatter may not bypass the rule by replacing a banned item with another grammatical form of the same item.
- Exceptions require an explicit new Owner decision that changes the lexicon authority; they are not inferred from context by the model.

The detailed lexicon contract and machine-readable rules remain in `docs/CONTENT_QUALITY_LEXICON_CONTRACT_v1.md`, `docs/PROSE_ANTI_JUNK_v0.1.md` and `contracts/content-quality-core-ru-v1.json`. This Authority section governs the book-level invariant.

## 1C. Nonfiction anti-template invariant — ACCEPTED / NON-NEGOTIABLE

This rule applies to **all nonfiction books and nonfiction series produced by BOOK OS**.

BOOK OS must not generate or preserve a manuscript by repeatedly filling the same prose, chapter or book template with different topics, examples, platforms, professions or nouns.

### Prohibited template reuse

The following are prohibited when they recur as a production pattern rather than arise from the material itself:

- repeated chapter openings built from the same rhetorical move;
- repeated chapter endings built from the same summary / exhortation formula;
- identical chapter skeletons such as `problem → N mistakes → what to do → checklist` used across the manuscript;
- repeated listicle, case, dialogue, diagnostic or worksheet structures used merely to fill volume;
- recycled transitions, rhetorical frames, hooks, conclusions or call-to-action formulas;
- reuse of the same example, case function, metaphor, analogy, practical artifact or mechanism with only the surface domain changed;
- cloning a chapter/template/composition pattern from another book in the same series;
- padding required length by repeating an argument in a different wording or by manufacturing structurally equivalent sections.

### Required nonfiction behavior

Each admitted chapter must have its own intellectual function, unique question, contribution, reader-before / reader-after change, and composition justified by the material.

The structure of a chapter must follow its actual task. Similar structures are allowed only when the subject matter independently requires them; BOOK OS must not impose a reusable house template merely for consistency or production speed.

Across a series, books may share quality standards, voice constraints and delivery level, but must remain substantively, structurally and rhetorically distinct.

### Enforcement consequence

- Chapter Admission must reject a chapter whose function or composition merely duplicates another chapter under a different topic.
- Mid-book Audit must detect repetitive chapter rhythm/composition, repeated mechanisms, examples and practical outputs.
- Whole-book / SeriesBench review must detect template reuse across the manuscript and across accepted books in the series.
- Adversarial Review must challenge formulaic rhetoric, structurally cloned chapters and length created by repetition rather than new substance.
- A technically correct manuscript that reads as template-filled nonfiction is not release-ready.

This invariant strengthens the existing Series Production Discipline and Hard Anti-Clone rules; it does not replace them.

## 1D. Pre-author whole-book QA invariant — ACCEPTED / NON-NEGOTIABLE

This rule applies to **all nonfiction manuscripts produced or revised under BOOK OS rules**, including temporary manual/chat-assisted production while the BOOK OS application is not yet the execution environment.

A completed manuscript must **not be presented to the human Author as author-ready, finished, checked or publication-ready immediately after drafting**. Before such presentation, BOOK OS must run a whole-manuscript **Pre-Author QA** against the exact candidate revision.

Intermediate drafts may be shown only when the Author explicitly requests them or when they are clearly labeled as a working draft / diagnostic artifact rather than a completed manuscript.

### Mandatory Pre-Author QA coverage

The default whole-book check must cover, where applicable:

- conformity with the human-approved Book Definition / Book Contract and Architecture;
- target length and density, with no padding used to reach volume;
- semantic repetition within chapters and across the whole manuscript;
- repeated examples, mechanisms, conclusions, practical outputs and argument functions;
- template reuse, repetitive composition, repeated openings/endings/transitions and other AI-prose pathologies;
- the active Owner anti-junk lexicon, including covered Russian inflectional wordforms;
- material factual claims, evidence quality, source coverage and provenance;
- freshness of time-sensitive law, platform rules, interfaces, algorithms, market data and statistics;
- target-market applicability where local law, platforms or commercial practice materially change the advice;
- practical value and AI-substitution risk of chapters/sections;
- for practical nonfiction, **worked-example teaching coverage**: major methods and decisions must be demonstrated through enough concrete worked material for the reader to distinguish weak execution from strong execution and understand why; acceptable forms include before/after fragments, strong/weak variants, diagnostic breakdowns, worked cases, counterexamples, decision walkthroughs and annotated samples; a manuscript made mostly of abstract advice plus brief “for example” mentions does not satisfy this requirement;
- cross-book overlap, protected series territories and cumulative exclusion requirements;
- **zero-tolerance service/editorial-note leakage check**: reader-facing prose must contain no internal editorial instructions, author/editor reminders, production notes, QA notes, revision instructions, TODO/FIXME markers, placeholders, status labels, future-edition reminders, source-verification reminders, BOOK OS process language or other text addressed to the production team rather than the reader;
- whole-book coherence, progression, transitions, unresolved contradictions and forgotten promises;
- literary/style quality and consistency with the active Author / Series / Book Style Profile;
- an adversarial whole-book pass whose purpose is to find reasons the manuscript is not yet ready.

### Worked-example teaching rule for practical nonfiction

Practical nonfiction must teach through **demonstration and analysis**, not explanation alone.

For each major method, decision or recurring reader error, the whole-book QA must ask whether the reader has enough concrete material to see:

- what a weak / mistaken version looks like;
- what a stronger version looks like or how the situation should be rebuilt;
- which specific differences matter;
- why those differences change the result;
- how the reader can transfer the reasoning to a new situation.

The form must follow the material. BOOK OS must **not** impose one repeated “bad example → good example → checklist” template across chapters. Different sections may use a worked case, annotated fragment, before/after rewrite, diagnostic comparison, counterexample, scenario, metric interpretation, dialogue analysis or another form justified by the subject.

A passing manuscript may not rely on abstract instruction with occasional one-line examples where the reader still cannot observe the method in action.

### Service/editorial-note zero-tolerance rule

Any service/editorial note found in reader-facing manuscript text is a **BLOCKING Pre-Author QA defect**.

Examples include, but are not limited to:

- instructions to the author, editor, fact checker, designer, formatter or future reviser;
- reminders such as “verify before publication / before a new edition”, “add source”, “update statistic”, “check law/platform rule”, “insert example”, “rewrite later”;
- internal labels such as draft/review/QA/BookBench/Chapter Contract/WRITING_ALLOWED status;
- placeholders, TODO/FIXME text, unresolved brackets or production comments;
- explanations of series territory, future-book allocation or internal BOOK OS workflow that are not intentionally written for the reader;
- comments about why a passage exists, what should be checked later, or how the manuscript should be produced.

The required result before author presentation is **zero unresolved service/editorial notes in book-facing text**. If a note contains a useful fact for the reader, it must be rewritten as normal reader-facing prose; otherwise it must be removed.

### Default repair loop

If Pre-Author QA finds a blocking defect, the system must repair or rework the candidate and rerun the affected checks before presenting it as author-ready.

Passing deterministic checks alone is insufficient. A manuscript with unresolved structural, evidentiary, stylistic, originality, series-overlap or practical-value defects is not author-ready.

The human Author remains the final authority. Pre-Author QA does not approve the manuscript on the Author's behalf; it prevents avoidable draft-quality defects from being handed to the Author as if the manuscript were already ready for review.

### Current-best-methods rule

BOOK OS implementation must actively use the **strongest current world methods and technologies that materially improve quality, reliability, evidence, evaluation or author control**.

This includes evaluating and adopting, when justified, advances in model capabilities, structured generation, retrieval, reranking, long-context use, research tooling, provenance, semantic analysis, model routing, multi-model evaluation, LLM-as-judge, pairwise evaluation, deterministic diagnostics, author-voice fingerprinting, editorial decision learning, human-in-the-loop authority and other relevant methods.

This does **not** mean chasing novelty or replacing proven components merely because something newer exists. “Latest” is subordinate to measured usefulness. A new method should be adopted when evidence or bounded evaluation shows that it improves BOOK OS quality/reliability or removes a material limitation without violating authority, privacy or safety constraints.

The system remains architecture-level model/provider agnostic. No provider or model brand is protected from replacement when a materially better option is demonstrated for a BOOK OS role.

### Acceptance consequence

For every quality-critical module, Central Brain must ask two separate questions:

1. **Does it work correctly as software?**
2. **Is it strong enough to help produce a genuinely excellent professional book?**

Both must be YES before the module may be treated as quality-complete.

CI, unit/integration tests and deterministic gates prove software properties. Real-book pilots, BookBench evidence, comparative evaluations and human editorial judgment prove book-quality properties. One cannot substitute for the other.

If a better current method could materially improve a critical quality dimension, Central Brain must not hide that fact merely to preserve schedule or previous implementation. The gap must be surfaced and either closed or explicitly accepted by the human Owner as a bounded trade-off.

### No silent quality downgrade

Speed, implementation convenience, token cost, provider convenience or backward compatibility must not silently lower the professional quality target.

Any material quality/cost/speed trade-off requires explicit human Owner acceptance. Default behavior is to protect book quality.

Codex and other implementation executors may optimize implementation, but they may not redefine this quality target, weaken it to make tests pass, or declare product GO from technical completion alone.

## 2. First user / pilot — ACCEPTED

- First user of v0.1: Owner.
- First real pilot: one new book created from zero.
- First direction: `Business Nonfiction`.
- Product is validated on a real book, not an abstract demo persona.

## 3. Two operating modes — ACCEPTED

### Mode A — Book from Zero

`Idea → Reader/Market → Thesis → Research → Book Contract → Architecture → Chapter Contracts → bounded drafting/editing → evidence/fact check → whole-book edit → BookBench → Human Acceptance → Literary Master`

This is the first v0.1 pilot path.

### Mode B — Existing Manuscript / Materials

BOOK OS can accept an existing manuscript, fragments, notes, interviews, research or other source materials, formalize state/authority, and move them through the controlled editorial pipeline toward Literary Master.

Architecture must support both modes; v0.1 implementation prioritizes Mode A.

## 4. Business Nonfiction taxonomy — ACCEPTED

User-facing selection stays simple: one primary subtype and optionally one secondary subtype.

1. Entrepreneurship
2. Strategy
3. Leadership
4. Management
5. Teams & Culture
6. Marketing & Brand
7. Sales & Negotiation
8. Finance & Investing
9. Product, Innovation & Technology
10. Career & Professional Development

Principle: **simple outside, smart inside**.

Subtype may influence research/evidence standards, structural expectations, style risks, domain pathologies and BookBench criteria.

## 5. Core production lifecycle — ACCEPTED

Baseline lifecycle:

`Idea → Market & Reader → Thesis → Research → Book Contract → Architecture → Chapter Contracts → Draft → Developmental Edit → Evidence / Fact Check → Cross-book Edit → Literary Edit → BookBench → Human Acceptance → Literary Master`

Exact orchestration may be refined without weakening authority/human gates.

Derived production stages such as Audio, Translation and Publishing come after Literary Master and do not redefine it.

## 6. Authority Protocol v0.1 — ACCEPTED

Workflow stage and authority status are separate.

### Workflow stages

`IDEA → BOOK DEFINITION → ARCHITECTURE → WRITING → WHOLE-BOOK EDIT → FINAL REVIEW → LITERARY MASTER`

### Authority statuses

`DRAFT → PROPOSED → REVIEWED → APPROVED → LOCKED`

Historical approved versions may become `SUPERSEDED`.

### Non-negotiable rule

AI/system code must never mutate an `APPROVED` or `LOCKED` object in place.

Required pattern:

`authority → bounded task → proposed patch/revision → review → human acceptance → new authority`

Rejected proposal leaves prior authority unchanged.

Material changes require human acceptance; minor mechanical changes may be batch-accepted with preserved history.

Experiments remain isolated until promoted into a formal proposal.

## 7. Literary Master — ACCEPTED

`LiteraryMaster` is an immutable reproducible release manifest, not merely the latest DOCX/file.

It references exact versions/hashes of at least:

- Book Contract;
- Book Architecture;
- approved manuscript/chapter revisions;
- Style Profile;
- Claim/Evidence snapshot;
- final BookBench/Evaluation runs;
- human release approval.

Derived DOCX/PDF/EPUB/Audio/Translation/Publishing artifacts cannot silently mutate Literary Master upstream.

## 8. Human authority — ACCEPTED

Human Owner remains final authority for important creative/product decisions, including:

- central thesis/promise;
- book architecture;
- author voice;
- material approved-content changes;
- major deletions/rearrangements;
- significant quality/cost/risk trade-offs;
- Literary Master release.

AI roles may research, draft, diagnose, critique, evaluate and propose. They do not grant themselves final material approval.

## 9. Model principle — ACCEPTED

BOOK OS is model-agnostic at the architecture level.

`Model Gateway` assigns providers/models to roles according to internal BOOK OS evals plus privacy, capability, cost, latency, availability and any applicable contractual constraints.

OpenAI, Anthropic, Google, Yandex, GigaChat, open-weight/self-hosted or future providers are replaceable execution resources. Model brand/version is never architectural authority.

For the **current MVP and first real-book pilot**, OpenAI is the primary intelligence lane under the approved 2026-08-29 Owner decision. No backup provider and no Yandex/GigaChat promotion are required before that pilot.

Critical workflows should avoid a single self-validating loop in which one model writes, judges and approves its own work. Human authority remains mandatory regardless of provider.

## 10. Book Contract — ACCEPTED

Each book has a formal versioned `BookContract` defining at minimum:

- reader;
- reader problem;
- central promise;
- central thesis;
- unique angle;
- reader intellectual trajectory;
- explicit exclusions;
- evidence standards;
- voice/genre constraints;
- readiness criteria.

It is first-class authority, not merely a prompt.

## 11. Chapter Contract — ACCEPTED

Before systematic chapter drafting, BOOK OS must know the chapter's function through a versioned `ChapterContract` covering at minimum:

- purpose/new contribution;
- reader prior/after state;
- required claims/research;
- required scenes/examples;
- ideas/examples reserved elsewhere;
- opening/ending/transition requirements;
- rhythm/constraints as appropriate.

## 12. Research / Claim Ledger — ACCEPTED

BOOK OS has a serious Research Engine and traceable Claim Ledger.

Core evidence distinction:

`Claim != Source != Evidence`

A source existing in the ledger does not by itself prove a claim. `Evidence` records the explicit relationship, supporting location, strength, limitations and conflicts.

No model-generated citation is considered verified merely because it looks plausible.

Primary initial research adapters include web search, OpenAlex, Crossref, Semantic Scholar, direct official/public sources and user-provided files.

## 13. Book Memory — ACCEPTED

BOOK OS does not rely only on model context.

Memory combines:

- structured Book Graph;
- lexical/exact retrieval;
- semantic retrieval;
- whole-book context when justified;
- optional reranking.

It must support detection of literal repetition, semantic idea repetition, contradictions, forgotten promises, duplicated examples and unsupported claims.

Indexes are derived/rebuildable and must reference stable manuscript/revision IDs.

## 14. Style / author voice — ACCEPTED

BOOK OS uses a versioned `StyleProfile` / Author Voice Fingerprint, not only a “write beautifully” prompt.

It may model sentence/paragraph distributions, syntax, author presence, emotionality, irony, metaphors, concrete detail, dialogue, transitions, opening/ending patterns, prohibited constructions and accepted reference passages.

System must check voice compliance, not merely state voice rules in prompts.

## 15. AI-prose pathology detection — ACCEPTED

BookBench/Style Guardian must detect measured versions of machine-prose defects including artificial contrasts, excessive `не X, а Y`, pseudo-aphorisms, artificial threes, repeated paragraph structures, repeated conclusions, unnecessary rhetorical questions, empty therapeutic/corporate abstractions, false profundity, banal generalization, excessive syntactic symmetry and overly smooth depersonalized prose.

Findings show examples/locations and respect the author Style Profile; they are not blind bans.

## 16. BookBench — ACCEPTED

BookBench is BOOK OS's internal evaluation system and a key moat.

It combines deterministic, lexical, statistical, semantic, LLM-as-judge, pairwise, multi-model and human evaluation where appropriate.

It measures/finds dimensions such as contract fulfillment, chapter novelty/function, idea/example repetition, contradictions, thought density, specificity/banality, evidence quality/unsupported claims, voice, AI-prose pathology, beginnings/endings/transitions and whole-book coherence.

BookBench does **not** hide findings behind one magic “book score”.

Model/prompt/provider role assignment is driven by BOOK OS eval data, not brand reputation.

## 17. Editorial decision corpus / moat — ACCEPTED

The most valuable accumulating dataset is:

`original → diagnosis → proposed edit → accepted/rejected → reason → final`

This corpus drives future BookBench calibration, routing and only later potential fine-tuning/training.

It is private/sensitive project data, not something to publish in the public software repository.

Fine-tuning is explicitly not the starting strategy.

## 18. Core Ontology — ACCEPTED

`CORE_ONTOLOGY.md` v0.2.0 is the v0.1 ontology authority.

A book is modeled as a versioned graph of intent, content, evidence, editorial work, authority/provenance, evaluations and release — not as one mutable text file.

## 19. Native macOS application and runtime independence — ACCEPTED / NON-NEGOTIABLE

BOOK OS is a **normal self-contained macOS desktop application**, not a developer checkout, repository launcher or browser-dependent product.

Owner-approved product requirements:

1. BOOK OS installs as `BOOK OS.app` in **Applications** (`/Applications`).
2. BOOK OS launches by ordinary double-click like a normal Mac application.
3. Everything required for normal local operation ships inside the application bundle or its signed installer payload.
4. After installation, normal use must **not require GitHub, any repository checkout, Python, Node.js, Rust, Codex, Terminal, shell scripts or a development environment**.
5. Production distributions must be signed with an appropriate **Developer ID** identity and **notarized by Apple**; ad-hoc signing is not sufficient for the intended end-user distribution path.
6. BOOK OS may support secure in-app updates. The update channel must use signed artifacts and must not make GitHub a runtime dependency; a developer-controlled endpoint/object storage/CDN may be used.
7. Books, canonical book state, author/series/style settings and other durable working data are stored **locally on the user's Mac** by default and remain accessible without a repository or cloud service.
8. Internet access is required only for explicitly invoked external capabilities such as AI/model APIs, research/network APIs and, if enabled by the user, software updates or backup/synchronization. Loss of internet must not prevent the application itself from launching or prevent normal local reading/editing/local checks that do not inherently require a network service.

### Packaging consequence

The current development-time design in which the desktop binary locates a Python venv and source tree outside the application bundle is **not an acceptable production runtime architecture** and must be replaced.

The production Local Core must be bundled as a self-contained sidecar/runtime payload inside the application distribution. The chosen implementation may use a packaged Python executable/server or another equivalent self-contained mechanism, provided the end user is not required to install or manage Python or any other development runtime.

The standard direct-distribution target is a signed/notarized macOS app delivered through a conventional installer experience such as a DMG. App Store distribution may be evaluated separately later, but is not required for this invariant.

### Cloud and hosting boundary

Yandex Cloud or another controlled storage/CDN may be used for distribution, update metadata/artifacts or optional backup/synchronization **only when useful**. No such cloud is allowed to become mandatory for launching BOOK OS or accessing the user's local books.

External model/provider services remain replaceable execution dependencies behind provider-neutral gateways. Current production code may expose specific providers, but no provider brand becomes architectural authority merely because it is currently integrated.

## 20. No-chat / no-repository runtime dependency — ACCEPTED

Project development authority remains recoverable from GitHub `main` + authority/spec/state/tasks/tests/evals without chat history.

That development rule must **not** leak into the installed product. GitHub and repository checkouts are development/source-control infrastructure only; the installed BOOK OS application must not contact or require them for launch, local book access or normal local operation.

Product: durable book state, tasks, outputs, decisions and authority are first-class local objects. A conversational interface may exist, but conversation transcript is never required hidden state.

A successor developer must be able to recover the project from `README → PROJECT_STATE → DESIGN_INDEX → current decision/task/HEAD`; an end user must not need any of those development artifacts to use the installed application.

## 21. Regional access / Russia — SUPERSEDED HISTORICAL REQUIREMENT

Earlier BOOK OS authority required a Russia/no-VPN runtime path and prohibited mandatory dependence on providers unavailable for Russian production use. That requirement led to former M8 / Task 009 and PR #12.

**This requirement is no longer current product authority.**

The Owner decision dated 2026-08-29 (`docs/decisions/2026-08-29-global-openai-first.md`) explicitly SUPERSEDES the Russia/no-VPN runtime milestone and removes it from the current product program rather than deferring it.

Current consequences:

- BOOK OS is a global system;
- OpenAI is the primary provider lane for the current MVP/real-book pilot;
- provider-neutral ModelGateway/EmbeddingGateway remain mandatory;
- no Yandex/GigaChat live promotion is required;
- no regional provider lane blocks Literary Master, the real-book pilot, or product-quality GO/NO-GO;
- PR #12 is CLOSED, NOT MERGED and retained only as historical/salvage evidence;
- older text describing Russia-ready provider proof as a current acceptance gate must not be followed.

The superseded requirement remains recoverable through Git history and the explicit decision record; it is not silently erased.

## 22. End-user API/subscription model — ACCEPTED DIRECTION

End users should buy/use BOOK OS, not assemble personal subscriptions across AI vendors.

Provider credentials/routing are product infrastructure concerns subject to provider terms/law. BYOK may exist as an optional capability and is acceptable for the Owner/internal pilot, but it is not a required dependency of the installed application itself.

Before commercial provider brokerage, current vendor commercial/resale/regional/data-processing terms must be reviewed.

## 23. Repository / data boundary — ACCEPTED

`book-os` is a separate repository from concrete books and Audio Studio.

The public BOOK OS repository may contain project authority/specifications/source code, but must not contain:

- real private manuscripts;
- private source materials;
- API/signing secrets;
- proprietary human editorial-decision/eval corpus.

A user's book project has separate local/private storage authority.

The installed production application must not use the source repository as runtime storage, application data storage, update state, book state or executable dependency.

## 24. BOOK OS ↔ Audio Studio boundary — ACCEPTED

BOOK OS and Audio Studio remain separate products/repositories.

`BOOK OS Literary Master → immutable Production Handoff → Audio Studio → Audio Edition Master`

Audio-only TTS/SSML/pronunciation/mastering transformations do not mutate Literary Master. A literary correction discovered in Audio Studio returns upstream as a correction request/proposal to BOOK OS.

Shared commodity infrastructure may be extracted later only after real duplication is observed and interface stability is demonstrated. Domain intelligence remains separate.

## 25. Build-vs-buy principle — ACCEPTED

Build BOOK OS-specific editorial IP ourselves: ontology, Authority Protocol, Contracts, Claim/Evidence semantics, editorial workflows, voice/pathology intelligence, cross-book editor, BookBench, human acceptance, Literary Master semantics and editorial-decision corpus.

Use proven commodity technology/APIs for LLMs, embeddings, research metadata/search, desktop/runtime, database, observability, CI and other infrastructure when it does not compromise authority/portability.

Commodity infrastructure used during development must not create an unnecessary end-user runtime dependency when the same capability can be packaged locally or made optional.

## 25A. World-class module reuse + independent local Brain — ACCEPTED / NON-NEGOTIABLE

BOOK OS must **not reinvent mature commodity modules without a demonstrated product reason**. The default engineering choice is to evaluate and reuse strong maintained world-class components, then invest custom engineering in BOOK OS-specific editorial intelligence and integration quality.

Examples of preferred reusable layers, when they satisfy current licensing/security/product requirements, include:

- OpenAI Responses API, hosted tools, Agents SDK, tracing and Evals/Graders for the external execution/evaluation lane;
- Apple MLX / MLX-LM or an equivalent mature Apple-Silicon inference runtime for local open-weight execution;
- Tiptap/ProseMirror or an equivalent mature document engine for the professional manuscript editor;
- established research/search/metadata sources and libraries rather than home-grown commodity crawlers/parsers where a stronger maintained option exists;
- proven OS/platform mechanisms for packaging, signing, updates, local secure storage and observability.

These components are **additions to, not replacements for, BOOK OS editorial IP**. BOOK OS retains canonical control over Authority, Book/Chapter Contracts, Book Graph/Memory, Claim/Evidence, Series Brain, chapter admission, Editorial Decision Memory, BookBench, quality routing, adversarial review and Literary Master.

### Dual execution strategy

BOOK OS uses two coordinated execution lanes:

1. **Frontier external lane now** for editorial operations where it currently delivers the strongest demonstrable nonfiction quality.
2. **Independent local BOOK OS Brain in parallel**, built from local/open-weight models plus BOOK OS-owned editorial intelligence, memory, evidence, quality loops and evaluation.

The long-term objective is that normal high-quality nonfiction production can execute locally without requiring an external frontier model, while external providers remain optional benchmark, fallback or expert resources.

The local Brain is not defined by copying or imitating the wording, hidden reasoning or proprietary implementation of any external model. It is judged by editorial outcome: intellectual depth, correctness, evidence fidelity, originality, structure, voice, usefulness, thought density, whole-book coherence and absence of machine-prose pathologies.

### Quality promotion rule

Local execution is promoted **per editorial operation**, never by one global declaration that “the local model is as good.” Promotion requires reproducible BOOK OS evaluation plus human review. Averages may not hide BLOCKING regressions.

If the local lane remains weaker for a difficult operation, that operation remains on the stronger external lane until evidence supports promotion. No cost, latency or independence goal may silently lower the Section 1A quality target.

### Provider/data boundary

External vendor state — conversations, traces, hosted vector stores, agent state or tool state — is execution/derived state only and never canonical BOOK OS authority. Durable book state remains locally reconstructable.

Provider outputs may be used only in ways permitted by applicable provider terms and law. In particular, OpenAI output must not be used to train, distill, fine-tune or create training targets for a competing local model. Local Brain development must use rights-clean independent data and a separately governed training/evaluation corpus.

Task 020 (`docs/tasks/TASK_020_FRONTIER_QUALITY_LOOP_LOCAL_BRAIN.md`) is the first implementation authority for this strategy. Task 017 remains a required production dependency and must not be bypassed or duplicated.

## 26. Project execution governance — ACCEPTED

`PROJECT_EXECUTION_PLAN.md` defines role split:

- Owner = final product/creative authority;
- Central Brain = architecture, sequencing, bounded task design, acceptance, authority/state maintenance;
- Codex = bounded implementation executor against explicit baseline/acceptance criteria.

Under `BOOKOS-DEC-0002`, Central Brain may finalize internal v0.1 technical/editorial design and issue bounded Codex tasks without pausing for Owner approval of every internal choice, unless a documented stop condition is triggered.

## 27. Implementation baseline — CURRENT AUTHORITY

The implementation baseline is no longer M0/Task 001.

Accepted and merged capability on current `main` includes the previously accepted M0–M7 chain and later accepted desktop/editorial milestones, including:

- Literary Master + exports;
- real-book pilot instrumentation;
- macOS launch hardening and visible desktop app work;
- Russian first-book launch workspace and guided author workflow work already accepted into the current baseline;
- GPT-6 Astra production lane;
- explicit OpenAI `Medium / High / Extra High` work-level selection.

The exact accepted SHAs, CI runs, transfer notes and current `main` checkpoint are recorded in `docs/PROJECT_STATE.md` and Git history. When those sources disagree with an older implementation summary in this authority file, the exact current `main` implementation wins for implementation facts, while this document remains authority for product invariants.

The existing source-tree/venv-based native launch mechanism is now explicitly classified as a **development/pilot implementation to be superseded** by the self-contained native macOS application requirement in Section 19. It must not be treated as the final distribution architecture merely because it previously passed launch CI.

Codex or any other executor must not resume Task 001 or former M8 merely because older historical files exist.

## 28. Current pilot execution — CURRENT AUTHORITY

The current critical path is:

`real Business Nonfiction pilot → Literary Master → HUMAN GO | CONDITIONAL_GO | NO_GO`

Tooling acceptance is not product GO. BOOK OS product GO requires the actual private real-book pilot to reach a LOCKED Literary Master and the human Owner to make the final decision from the evidence.

No additional infrastructure milestone is permitted merely for architectural neatness. However a **concrete product defect discovered in the real Owner workflow** — including unusable UX, incorrect project classification, non-standard macOS installation/launch, or a runtime dependency that violates Section 19 — is a legitimate blocker and must be corrected on the critical path.

Before the first paid provider call, explicit bounded budget approval remains mandatory. No task or UI action may infer that approval.

## Change log

### 0.7.0 — 2026-09-09

Owner accepted the world-class module-reuse and independent local Brain strategy:

- reuse mature commodity modules instead of rebuilding them without a product reason;
- keep BOOK OS-specific editorial intelligence canonical and custom;
- use the strongest external execution lane for current frontier-quality work;
- build an independent local BOOK OS Brain in parallel using local/open-weight models and BOOK OS-owned systems;
- promote local execution per editorial operation only after reproducible quality evidence and human review;
- keep external vendor state non-canonical;
- keep local-model training/evaluation rights-clean and compliant with provider terms;
- Task 020 becomes the implementation authority for the quality-loop/local-Brain foundation, with Task 017 retained as a required dependency.

### 0.6.0 — 2026-09-09

Owner accepted the native macOS application/runtime-independence contract:

- install as `BOOK OS.app` in Applications;
- launch by double-click;
- ship required local runtime inside the application distribution;
- no normal-use dependency on GitHub/repositories/Python/Node/Rust/Terminal/development tooling;
- Developer ID signing + Apple notarization for production distribution;
- secure self-update capability allowed without making GitHub a runtime dependency;
- books/settings remain local by default;
- internet is limited to explicitly invoked external AI/research APIs and optional updates/backup/synchronization.

This version explicitly supersedes the source-tree/venv-dependent launch mechanism as the intended production distribution architecture. It preserves GitHub `main` as the source of truth for **development authority**, not as an end-user runtime dependency.