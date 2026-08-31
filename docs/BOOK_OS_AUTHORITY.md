# BOOK OS — PROJECT AUTHORITY

**Status:** ACTIVE AUTHORITY  
**Version:** 0.4.0  
**Date:** 2026-08-31  
**Project:** BOOK OS  
**Canonical repository:** `https://github.com/niknikdym-hue/book-os`

## 0. Authority rule

GitHub `main` is the source of truth for BOOK OS product-development authority.

Chats are disposable working sessions and may contain drafts, hypotheses, rejected ideas or incomplete reasoning. A decision becomes project authority only when recorded in canonical repository authority/specification/decision files.

Accepted decisions are not silently overwritten. A changed decision is versioned and/or explicitly superseded; Git history and decision records preserve prior state.

This v0.4 consolidation preserves accepted product decisions while incorporating later explicit Owner decisions and accepted implementation state.

### Current supersession rule

The approved Owner decision `docs/decisions/2026-08-29-global-openai-first.md` explicitly SUPERSEDES all prior requirements that BOOK OS must prove a Russia/no-VPN runtime lane, Yandex/GigaChat production promotion, or Russia-specific provider availability before the current MVP/pilot GO/NO-GO.

Therefore any older authority/spec/task text that still describes that regional lane as a current gate is historical only and must not be used to restart former M8 / PR #12.

`docs/PROJECT_STATE.md` is the authority for the exact accepted checkpoint and next permitted action.

## 1. Product identity — ACCEPTED

BOOK OS is a specialized editorial-authoring operating system for producing strong nonfiction at an international professional standard.

It is **not** a generic AI writer and **not** a one-prompt book generator.

Its purpose is to give one strong author/editor the intellectual and operational infrastructure of a professional editorial team across research, book architecture, bounded drafting, developmental editing, evidence/fact checking, cross-book editing, literary editing, author-voice control, versioning, provenance, quality gates, human acceptance and release of a Literary Master.

BOOK OS does not promise a bestseller. Its responsibility is manuscript quality; commercial success also depends on topic, author, market, publisher, marketing, timing and external factors.

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

## 19. Local-first technical direction — ACCEPTED

BOOK OS v0.1 is a local-first desktop product.

Canonical book state/authority remains locally accessible and recoverable. External AI/research services are replaceable execution dependencies.

Accepted technical baseline is in `TECHNICAL_ARCHITECTURE_v0.1.md`:

- Tauri 2 + React/TypeScript desktop;
- Python 3.12 local editorial-core sidecar;
- FastAPI/Pydantic;
- SQLite canonical state + FTS5;
- local rebuildable semantic index;
- provider/research adapters;
- no heavy distributed infrastructure in v0.1 without measured need.

Current accepted runtime also includes macOS launch hardening from Task 012: Local Core startup may not block first window rendering; the Python child remains owned through startup/shutdown; readiness is emitted only after Uvicorn startup.

## 20. No-chat dependency — ACCEPTED

Project development: GitHub `main` + authority/spec/state/tasks/tests/evals is recoverable without chat history.

Product: durable book state, tasks, outputs, decisions and authority are first-class local objects. A conversational interface may exist, but conversation transcript is never required hidden state.

A successor must be able to recover from `README → PROJECT_STATE → DESIGN_INDEX → current decision/task/HEAD`.

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

Provider credentials/routing are product infrastructure concerns subject to provider terms/law. BYOK may exist later as optional capability, not a core requirement.

Before commercial provider brokerage, current vendor commercial/resale/regional/data-processing terms must be reviewed.

## 23. Repository / data boundary — ACCEPTED

`book-os` is a separate repository from concrete books and Audio Studio.

The public BOOK OS repository may contain project authority/specifications/source code, but must not contain:

- real private manuscripts;
- private source materials;
- API/signing secrets;
- proprietary human editorial-decision/eval corpus.

A user's book project has separate local/private storage authority.

## 24. BOOK OS ↔ Audio Studio boundary — ACCEPTED

BOOK OS and Audio Studio remain separate products/repositories.

`BOOK OS Literary Master → immutable Production Handoff → Audio Studio → Audio Edition Master`

Audio-only TTS/SSML/pronunciation/mastering transformations do not mutate Literary Master. A literary correction discovered in Audio Studio returns upstream as a correction request/proposal to BOOK OS.

Shared commodity infrastructure may be extracted later only after real duplication is observed and interface stability is demonstrated. Domain intelligence remains separate.

## 25. Build-vs-buy principle — ACCEPTED

Build BOOK OS-specific editorial IP ourselves: ontology, Authority Protocol, Contracts, Claim/Evidence semantics, editorial workflows, voice/pathology intelligence, cross-book editor, BookBench, human acceptance, Literary Master semantics and editorial-decision corpus.

Use proven commodity technology/APIs for LLMs, embeddings, research metadata/search, desktop/runtime, database, observability, CI and other infrastructure when it does not compromise authority/portability.

## 26. Project execution governance — ACCEPTED

`PROJECT_EXECUTION_PLAN.md` defines role split:

- Owner = final product/creative authority;
- Central Brain = architecture, sequencing, bounded task design, acceptance, authority/state maintenance;
- Codex = bounded implementation executor against explicit baseline/acceptance criteria.

Under `BOOKOS-DEC-0002`, Central Brain may finalize internal v0.1 technical/editorial design and issue bounded Codex tasks without pausing for Owner approval of every internal choice, unless a documented stop condition is triggered.

## 27. Implementation baseline — CURRENT AUTHORITY

The implementation baseline is no longer M0/Task 001.

Accepted and merged capability now includes:

- M0–M7 / Tasks 001–008;
- Task 010 Literary Master + exports;
- Task 011 real-book pilot instrumentation;
- Task 012 macOS launch hardening.

Canonical schema is Alembic `0010`.

Exact accepted SHAs, CI runs, transfer notes and the current `main` checkpoint are recorded in `docs/PROJECT_STATE.md`.

Codex or any other executor must not resume Task 001 or former M8 merely because older historical files exist.

## 28. Current pilot execution — CURRENT AUTHORITY

The current critical path is:

`real Business Nonfiction pilot → Literary Master → HUMAN GO | CONDITIONAL_GO | NO_GO`

Task 011 tooling acceptance is not product GO. BOOK OS product GO requires the actual private real-book pilot to reach a LOCKED Literary Master and the human Owner to make the final decision from the evidence.

No additional infrastructure milestone is required before starting the first complete book unless the pilot reveals a concrete regression/blocker.

The first current Owner gate is creative:

- select/confirm the real book idea;
- select/confirm the intended reader.

Before the first paid OpenAI call, explicit bounded budget approval remains mandatory. No task or UI action may infer that approval.
