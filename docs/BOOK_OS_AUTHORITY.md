# BOOK OS — PROJECT AUTHORITY

**Status:** ACTIVE AUTHORITY  
**Version:** 0.1.0  
**Date:** 2026-08-22  
**Project:** BOOK OS  

## 0. Authority rule

This repository is the source of truth for BOOK OS.

Chats are working sessions and may contain hypotheses, drafts, rejected ideas, or incomplete reasoning. A decision becomes BOOK OS authority only when it is recorded here or in another authority file explicitly referenced from here.

Accepted decisions are not silently overwritten. If a decision changes, the prior decision remains in history and is marked `SUPERSEDED` by a new accepted decision.

---

## 1. Product identity — ACCEPTED

BOOK OS is a specialized editorial-authoring system for producing strong nonfiction at an international professional standard.

It is **not** a generic AI writer and **not** a one-prompt book generator.

Its purpose is to give one strong author/editor the intellectual and operational infrastructure of a professional editorial team across research, book architecture, drafting, developmental editing, evidence/fact checking, cross-book editing, literary editing, author-voice control, versioning, provenance, quality gates, human acceptance, and release of a literary master.

BOOK OS does not promise a bestseller. Its responsibility is to maximize manuscript quality; commercial success also depends on topic, author, market, publisher, marketing, timing, and other external factors.

---

## 2. Model principle — ACCEPTED

BOOK OS is model-agnostic.

A `Model Gateway` must allow different frontier models/providers to be assigned to roles according to BOOK OS internal evals.

Possible providers include OpenAI, Anthropic, Google Gemini, and future providers that pass internal quality tests.

A model brand or model version is never architectural authority. BOOK OS quality requirements and internal eval results are authority.

---

## 3. Two operating modes — ACCEPTED

BOOK OS supports two base modes.

### Mode A — Book from Zero

The system can take a book from an initial idea through research, contracts, architecture, bounded drafting, editorial stages, human acceptance, and Literary Master.

### Mode B — Existing Manuscript / Materials

The system can accept an existing manuscript, fragments, notes, interviews, research, or other source materials, formalize their state and authority, and take them through the same controlled editorial pipeline toward Literary Master.

BOOK OS must not collapse into either only a manuscript editor or only a book generator.

For **v0.1**, the first real end-to-end test scenario is **Book from Zero**.

---

## 4. First user — ACCEPTED

The first user of BOOK OS v0.1 is the project owner herself.

The first MVP is designed around one strong author/editor who remains the final human authority for major creative decisions.

The system should be validated on a real book rather than an abstract persona.

---

## 5. First book profile — ACCEPTED

The first v0.1 direction is **Business Nonfiction**.

The user-facing classification must remain simple: the user selects one primary subtype and, when useful, one additional subtype.

Initial business subtypes:

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

External market classifications and richer internal logic may be used by the system without burdening the user.

The subtype must be able to influence research/evidence standards, structural expectations, style risks, domain pathologies, and BookBench criteria.

---

## 6. Core production lifecycle — ACCEPTED BASELINE

The current baseline lifecycle for a book created from zero is:

`Idea`
→ `Market & Reader`
→ `Thesis`
→ `Research`
→ `Book Contract`
→ `Architecture`
→ `Chapter Contracts`
→ `Draft`
→ `Developmental Edit`
→ `Evidence / Fact Check`
→ `Cross-book Edit`
→ `Literary Edit`
→ `BookBench`
→ `Human Acceptance`
→ `Literary Master`

Derived production stages such as Audio, Translation, and Publishing come **after** Literary Master and do not redefine it.

The exact orchestration may be refined, but BOOK OS must never become uncontrolled whole-book generation.

---

## 7. Book Contract — ACCEPTED CONCEPT

Each book must have a formal `Book Contract` defining at minimum:

- intended reader;
- problem solved;
- central promise;
- central thesis;
- unique angle;
- intended intellectual trajectory of the reader;
- explicit exclusions / what the book does not do;
- evidence standards;
- voice and genre constraints;
- readiness criteria.

The Book Contract is a first-class authority object, not merely a prompt.

---

## 8. Chapter Contract — ACCEPTED CONCEPT

Before drafting a chapter, BOOK OS must know the chapter's function.

A Chapter Contract may include:

- chapter purpose;
- new idea introduced;
- what the reader already knows at this point;
- what the reader should understand after the chapter;
- required claims;
- permitted / required research;
- required scenes or examples;
- ideas already owned by other chapters and therefore not to be repeated;
- emotional and intellectual rhythm;
- opening requirements;
- ending requirements;
- transition to the next chapter.

A Chapter Contract is a gate before bounded drafting.

---

## 9. Authority Protocol v0.1 — ACCEPTED

### 9.1 Workflow stage and authority status are different

Book production stage describes **where work is in the lifecycle**.

Authority status describes **which version of an object is currently trusted and protected**.

Baseline workflow stages:

`IDEA`
→ `BOOK DEFINITION`
→ `ARCHITECTURE`
→ `WRITING`
→ `WHOLE-BOOK EDIT`
→ `FINAL REVIEW`
→ `LITERARY MASTER`

Baseline authority statuses:

`DRAFT`
→ `PROPOSED`
→ `REVIEWED`
→ `APPROVED`
→ `LOCKED`

Historical approved versions may become:

`SUPERSEDED`

### 9.2 Approved/locked content cannot be silently rewritten

AI must never mutate an `APPROVED` or `LOCKED` object in place.

The required pattern is:

`authority`
→ `bounded task`
→ `proposed patch / proposed version`
→ `review`
→ `human acceptance`
→ `new authority`

If a proposal is rejected, the prior authority remains unchanged.

### 9.3 Material vs minor changes

Material changes include changes to meaning, thesis, argument, claims, structure, examples, author voice, or conclusions and require human acceptance.

Minor/technical changes such as punctuation, obvious typos, or formatting may be accepted in batches, while preserving history.

### 9.4 Experiments

Experimental variants are isolated from current authority. They do not replace approved content unless promoted into a formal proposal and accepted.

---

## 10. Literary Master — ACCEPTED

`Literary Master` is an immutable release/snapshot of the book, not merely the latest DOCX file.

A Literary Master release must be reproducible from the exact authority versions it references, including at minimum:

- Book Contract version;
- Architecture version;
- approved chapter versions;
- relevant Style Profile version;
- Claim Ledger snapshot;
- BookBench final report;
- human approval;
- release timestamp/version.

Derived formats such as DOCX, PDF, EPUB, audio, translation, or publishing artifacts must not silently modify the Literary Master upstream.

---

## 11. Human authority — ACCEPTED

The human remains final authority for important creative decisions, especially:

- central thesis;
- book architecture;
- author voice;
- major deletions;
- major rearrangements;
- material changes to approved content;
- Literary Master release.

AI roles may research, draft, diagnose, critique, propose patches, and run checks. They do not grant themselves final approval.

---

## 12. Multi-model critical review — ACCEPTED PRINCIPLE

Critical decisions should not use a single self-validating loop in which one model writes, judges, and approves its own output.

Preferred pattern:

`model A proposes`
→ `model B critiques`
→ `deterministic / BookBench checks`
→ `human accepts`

Exact model assignments remain subject to internal evals.

---

## 13. Research / evidence direction — ACCEPTED CONCEPT

BOOK OS requires a serious research layer and must not allow fabricated studies, statistics, authors, or sources.

Research may use web search, scientific APIs and databases, primary research, official statistics, government/regulatory sources, and professional sources appropriate to the book domain.

Commodity research infrastructure should be integrated where practical rather than reinvented.

---

## 14. Claim Ledger — ACCEPTED CONCEPT

Verifiable claims should be representable as first-class objects with traceable evidence.

A claim record may include:

- claim text;
- location(s) of use;
- source;
- DOI / URL / bibliographic metadata;
- access date;
- source type;
- evidence strength;
- supporting excerpt/reference;
- study limitations;
- contradictory evidence;
- verification status;
- fact-check decision.

The purpose is traceable book-level fact checking.

---

## 15. Book Memory — ACCEPTED PRINCIPLE

BOOK OS must not rely only on a model's long context window.

Book Memory should combine:

`whole-book context`
+ `semantic retrieval`
+ `lexical / exact retrieval`
+ optional `reranking`

It must support detection of literal repetition, semantic repetition, contradictions, forgotten promises, and inadequately supported claims.

---

## 16. Style / author voice — ACCEPTED CONCEPT

BOOK OS requires a formal author-voice profile, not only a prompt such as "write vividly".

The system should eventually model and evaluate dimensions such as sentence/paragraph patterns, syntax, author presence, emotionality, irony, metaphor use, concrete detail density, scene vs abstraction, dialogue, transitions, openings/endings, prohibited constructions, and recurring AI-like patterns.

---

## 17. AI-prose pathology detection — ACCEPTED CONCEPT

BOOK OS should detect recurring machine-prose defects, including but not limited to:

- artificial oppositions;
- excessive "not X but Y" constructions;
- pseudo-aphorisms;
- artificial triads;
- repetitive paragraph structures;
- repetitive conclusions;
- over-explaining obvious ideas;
- empty therapeutic language;
- decorative rhetorical questions;
- false depth;
- banal generalizations;
- overly smooth/depersonalized prose;
- repeated chapter endings;
- synthetic syntactic symmetry.

---

## 18. BookBench — ACCEPTED CONCEPT

BookBench is a core proprietary quality-evaluation layer.

Over time it should evaluate at least:

- semantic novelty;
- idea repetition;
- example repetition;
- idea density;
- specificity;
- banality;
- evidence quality;
- unsupported claims;
- Book Contract fulfillment;
- Chapter Contract fulfillment;
- author-voice preservation;
- chapter structural function;
- transitions;
- opening strength;
- ending strength;
- rhythmic variation;
- AI-like prose;
- developmental defects;
- whole-book coherence.

Checks may be deterministic, lexical, semantic, statistical, LLM-as-judge, pairwise, multi-model, or human.

BookBench must not be reduced to a single magical quality score. Findings should be explainable and actionable.

---

## 19. Editorial decision data / moat — ACCEPTED

The main long-term moat is not a particular LLM.

A key proprietary asset is the accumulating editorial decision corpus:

`original`
→ `proposed edit`
→ `accepted / rejected`
→ `reason`
→ `final version`

Combined with BookBench, author-voice data, evidence history, and human acceptance, this becomes BOOK OS's proprietary editorial intelligence.

---

## 20. Repository separation — ACCEPTED

BOOK OS has its own repository.

Repositories of individual books are not the source of truth for BOOK OS itself.

BOOK OS architecture, authority documents, schemas, decisions, benchmarks, and future code belong in the BOOK OS repository.

---

## 21. v0.1 scope discipline — ACCEPTED

Do not begin v0.1 with:

- a proprietary foundational LLM;
- fine-tuning;
- uncontrolled agent swarms;
- automatic whole-book "make it better" rewriting;
- publishing/marketing automation as a core concern;
- translation/TTS as a core concern;
- optimization for every nonfiction genre at once;
- large multi-user SaaS complexity before editorial core quality is proven.

First prove a real, high-quality, end-to-end book creation workflow for one author/editor and one Business Nonfiction book from zero.

---

## 22. Next design step — CURRENT

The next design artifact to create is:

**Core Ontology v0.1**

It should formalize the main BOOK OS entities and relationships, including at minimum:

`BOOK`
→ `Book Contract`
→ `Architecture`
→ `Chapter`
→ `Chapter Contract`
→ `Claim`
→ `Source`
→ `Scene / Example`
→ `Style Profile`
→ `Editorial Finding`
→ `Patch / Proposal`
→ `Decision`
→ `Version`
→ `Approval`
→ `Literary Master`

No implementation work should precede enough design clarity to preserve the accepted authority and provenance rules.
