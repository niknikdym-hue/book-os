# Owner Decision — Series Production Discipline and Chapter Admission

**Date:** 2026-09-07  
**Status:** APPROVED / CURRENT  
**Owner:** product owner  
**Scope:** BOOK OS nonfiction workflow, series production, Book Definition, Architecture, chapter admission, whole-book review

## Decision

The production method developed in the canonical series project **«Секреты продвижения услуг»** contains stronger editorial controls than the current BOOK OS runtime in several areas. BOOK OS must absorb the stronger method as **generic product behavior**, not as hard-coded rules for that series and not as a runtime dependency on `books-for-litres`.

The governing production path becomes:

`Author Profile → optional Series Canon → Book Definition Pack → Architecture + reservations → Chapter Admission Gate → Writing → Chapter QA → Mid-book Audit → Whole-book Edit → Adversarial Review → Literary Master → Series Closure → Publishing Package`

A standalone book may skip Series Canon inheritance, but it still uses the book-level uniqueness, definition, chapter-admission, mid-book and adversarial controls that apply to its domain profile.

## 1. Series Canon is a living production object

A Series Profile is not sufficient as a static list of rules. When a book belongs to a series, BOOK OS must maintain a structured **Series Canon / Exclusion Registry** for intellectual assets and protected territories.

At minimum, series assets may include:

- book territory / promise;
- thesis or intellectual task;
- mechanism / causal chain;
- diagnostic distinction / classification;
- research function;
- scene/case function;
- analogy / metaphor function;
- framework / practical tool;
- practical artifact / reader action;
- composition pattern;
- signature rhetorical device when materially distinctive;
- future-book territory;
- legacy-protected territory.

The initial status model is:

- `PLANNED` — proposed but not human-approved;
- `RESERVED` — protected by an approved Book Definition or Architecture;
- `USED_DRAFT` — present in current working text;
- `USED_ACCEPTED` — present in accepted Literary Master and excluded from semantic reuse;
- `CROSS_REFERENCE_ONLY` — may be referenced briefly but not re-explained as new work;
- `LEGACY_PROTECTED` — belongs to an existing/legacy book territory pending its own rework;
- `RELEASED` — reservation removed after evidence proves the asset did not enter accepted master.

`USED_ACCEPTED` cannot be silently returned to free inventory. The full accepted Literary Master remains the final exclusion evidence; the registry is a navigational and planning layer, not a replacement for full-text semantic comparison.

## 2. Book Uniqueness Ledger

Every book must maintain a structured Book Uniqueness Ledger. After Architecture approval, each admitted chapter must have at least:

- one unique question;
- one unique mechanism or causal contribution;
- distinct reader-before / reader-after state;
- distinct decision/action/practical result where the domain requires practice;
- forbidden overlap with adjacent chapters;
- forbidden overlap with other books/legacy territories when in a series;
- research-function allocation;
- scene/case function allocation where used;
- analogy/metaphor reservation where used;
- practical-tool/artifact reservation where used;
- composition intent sufficiently differentiated from neighboring chapters.

Architecture approval creates `RESERVED` assets. Reservation protects territory but **does not grant permission to write**.

## 3. Book Definition Pack before Architecture

BOOK OS must treat Book Definition as a structured pack rather than only a compact Book Contract.

The generic pack must support the following gates/sections where relevant to the domain:

1. reader and real problem;
2. central promise / thesis / mechanism;
3. explicit boundaries and `NOT THIS BOOK`;
4. relationship to series and protected future-book territories;
5. category / competitor / substitute map;
6. world-class benchmark analysis;
7. original-contribution hypothesis;
8. research map and evidence functions;
9. practical-value map where the book is practical nonfiction;
10. target-market application map when local adaptation materially changes action;
11. freshness-risk map for time-sensitive facts/platforms/law/market data;
12. uniqueness / overlap proof;
13. AI-substitution test.

The UI does not need to expose these as separate markdown-like documents. They should be structured product sections and evidence-backed gates.

## 4. AI-substitution gate

For nonfiction produced in an AI-saturated market, BOOK OS must explicitly test whether the proposed book or chapter is materially more valuable than a strong current AI answer or high-quality free article.

A Book Definition requires REWORK if its central promise can be substantially delivered by a short generic AI answer without losing the book's claimed value.

A chapter requires REWORK / MERGE / DELETE when its independent value does not exceed a strong bounded AI answer, unless the chapter is structurally necessary for a larger argument and provides a distinct function that cannot be removed without loss.

This is an editorial-value gate, not a marketing slogan and not an anti-AI bias.

## 5. Four quality dimensions for major objects

For practical/business nonfiction, Book Definition, Architecture and Chapter Admission must evaluate at least:

1. `TOP_TIER_GLOBAL` — quality relative to strong international benchmark work for the same reader problem;
2. `ORIGINAL_CONTRIBUTION` — new synthesis, distinction, mechanism, causal model, framework or actionable clarity rather than compilation;
3. `PRACTICAL_VALUE` — concrete decision/action/output with observable utility when the domain is practical;
4. `TARGET_MARKET_APPLICATION` — adaptation to the actual reader market where local law, platforms, commercial practice or constraints materially change the advice.

For a Russian-targeted business book, `TARGET_MARKET_APPLICATION` is implemented as Russia application/freshness. Other domains/markets use an appropriate domain overlay.

Failure of a required quality dimension is `REWORK`, not permission to compensate with attractive prose.

## 6. Stronger Chapter Contract

BOOK OS Chapter Contract must be extended beyond purpose/contribution/claims/scenes.

The generic core should support:

- chapter problem / unique question;
- mechanism / causal chain;
- reader prior state / reader after state;
- contribution relative to adjacent chapters;
- evidence function and evidence limits;
- scene/case function if used;
- `NOT THIS CHAPTER` boundaries;
- opening / development / complication / ending intent;
- uniqueness proof;
- deletion / merge test.

Domain overlays may additionally require:

- decision enabled by the chapter;
- next action;
- practical artifact/output;
- observable check of output quality;
- economic significance;
- benchmark comparison;
- target-market application;
- freshness requirements;
- analogy/metaphor function;
- domain-specific safety or evidence gates.

A new example, profession, statistic or source does not make an old mechanism new.

## 7. Chapter Admission Gate and writing permission

**Architecture approval no longer opens WRITING globally.**

Each chapter starts with `WRITING_ALLOWED = NO`.

A chapter may move to `WRITING_ALLOWED = YES` only when its required admission checks pass. The initial generic admission set is:

- Book Definition and Architecture are human-approved/current;
- Chapter Contract is complete/current;
- uniqueness / overlap gate PASS;
- evidence/research readiness PASS for claims that require support;
- boundaries / reserved material PASS;
- domain quality gates PASS;
- no blocking anti-junk / policy / provenance defect;
- any explicit conditional merge/delete test is resolved or remains deliberately conditional with a defined checkpoint.

Writing services must fail closed if the chapter is not admitted. UI must show why writing is blocked and which checks remain open.

## 8. Deletion and merge discipline

A chapter must not survive merely because work has already been spent on it.

Before admission and during later audits, BOOK OS must ask whether:

- deleting the chapter removes a unique intellectual step;
- its core work could be merged into an adjacent chapter without material loss;
- it exists only because the category usually contains such a chapter;
- it repeats a mechanism under another example;
- it produces a distinct reader decision/action/output where applicable;
- its value exceeds a strong AI/free substitute.

Weak chapters are `REWORK / MERGE / DELETE` rather than padded or stylistically polished into existence.

## 9. Practical Value Map

For practical nonfiction, BOOK OS must maintain a book-level Practical Value Map tying each chapter to:

`problem → decision → action → artifact/output → observable check`

A practical output is not satisfied by generic advice such as “build trust”, “increase value” or “understand the customer better”. The reader must be able to identify what to create, change, measure, decide, stop doing or verify.

Where appropriate, add a next-business-day applicability check. Worksheets/checklists that merely restate the chapter do not count as unique practical value.

## 10. Mid-book audit

At approximately 40–60% of the planned manuscript, BOOK OS must create a mandatory mid-book audit checkpoint before the remaining writing proceeds without review.

The audit looks for at least:

- drift from Book Contract / Definition;
- repeated mechanisms or chapter functions;
- voice becoming formulaic;
- repetitive chapter rhythm/composition;
- future-book/neighboring-chapter leakage;
- repeated scene/case functions;
- repeated practical outputs;
- volume growth caused by padding rather than new substance;
- research/evidence gaps that have become structural.

A structural defect should trigger architecture/contract REWORK rather than be deferred to final copyediting.

## 11. Adversarial Review before Literary Master

Before Literary Master, BOOK OS must run an independent **Adversarial Review** whose goal is to find reasons the book is not ready, not to confirm prior work.

The review must challenge at least:

- banal or AI-replaceable chapters;
- hidden semantic repetition;
- unsupported or overconfident claims;
- pseudo-cases / manufactured documentary tone;
- weak practical value;
- unnecessary length;
- AI-prose pathology / formulaic rhetoric;
- internal editorial instructions leaking into reader text;
- mismatch with central promise;
- series/future-book leakage;
- stale market/platform/legal facts where relevant.

The Writer and Adversarial Reviewer should be independent executors where practical. The operation-level routing Owner Decision applies: the best executor for adversarial review may differ from the writer.

Adversarial Review never APPROVES the book; it produces evidence/findings for human review.

## 12. Series Closure

After human acceptance of Literary Master for a series book:

1. exact Literary Master joins the cumulative series exclusion corpus;
2. actually used assets are promoted to `USED_ACCEPTED`;
3. unused reservations may be released only with evidence they are absent from accepted master;
4. protected future-book territories remain protected;
5. the next book's Definition/Architecture may then use the updated canon.

This closure must be deterministic/provenance-aware and must not depend on chat memory.

## 13. Existing Manuscript / legacy inventory

When Existing Manuscript mode is used for an older published book, BOOK OS should classify legacy material before rebuilding it. Useful initial disposition classes are:

- `KEEP_AS_QUESTION`;
- `RESEARCH_ANEW`;
- `OBSOLETE`;
- `DUPLICATE`;
- `MOVE_TO_FUTURE`;
- `DISCARD`;
- `NEW_BOOK_CANDIDATE`.

Legacy text is evidence/source material, not automatic authority for the new Architecture or current factual claims.

## 14. Implementation consequence

Before the first real pilot is treated as representative, BOOK OS must implement at least the following executable slice:

1. Series Canon asset statuses/reservations for a series book;
2. Book Uniqueness Ledger bound to Architecture/chapter IDs;
3. stronger Chapter Contract fields required for uniqueness/admission;
4. per-chapter `WRITING_ALLOWED` admission state and fail-closed Writer gate;
5. Definition Pack data model sufficient for benchmark / contribution / practical / target-market / uniqueness / AI-substitution checks;
6. mid-book and adversarial review checkpoints before final pilot acceptance.

Publishing Package requirements from the 2026-09-06 decision remain mandatory and downstream of Literary Master.

## 15. Relationship to prior authority

This decision **extends** the 2026-09-06 Author/Series/Length/Style/Publishing Owner Decision. It does not remove Author Profile, Style Profile, target-length, Publishing Package, AI Pro/AI Ya or model-routing requirements.

Where the older runtime assumes that Architecture approval is sufficient to open global Writing, that assumption is **SUPERSEDED**. Writing permission is now chapter-specific and gate-driven.

The `books-for-litres/sekrety-prodvizheniya-uslug` files are evidence that informed this decision. The canonical runtime/product authority is this BOOK OS decision and subsequent BOOK OS schemas/code, not the external book repository.

## Change log

### v1.0 — 2026-09-07
- Owner accepted the proposal to absorb the stronger series/book production method developed in «Секреты продвижения услуг» into BOOK OS.
- Added living Series Canon / asset statuses, Book Uniqueness Ledger, Definition Pack, AI-substitution gate, stronger Chapter Contract, chapter-specific writing admission, Practical Value Map, mid-book audit, adversarial review, series closure and legacy inventory semantics.
