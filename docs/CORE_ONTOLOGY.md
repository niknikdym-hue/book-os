# BOOK OS — CORE ONTOLOGY v0.1

**Status:** ACCEPTED FOR V0.1 IMPLEMENTATION  
**Version:** 0.2.0  
**Date:** 2026-08-22  
**Project phase:** PHASE 1 — Core Ontology  
**Canonical repository:** `https://github.com/niknikdym-hue/book-os`

## 1. Purpose

This ontology defines the minimum set of first-class objects that BOOK OS must understand in order to create, edit, verify, version, approve, recover, and release a nonfiction book without relying on chat memory or a single AI model.

The ontology is intentionally small enough for v0.1, but it must preserve the accepted Authority Protocol and leave room for professional expansion.

Core rule:

> A book is not a text file. It is a versioned graph of intent, content, evidence, editorial decisions, provenance, and approvals.

## 2. Six layers

BOOK OS v0.1 is organized into six conceptual layers.

### Layer A — Book definition

1. `BookProject`
2. `BookProfile`
3. `BookContract`
4. `BookArchitecture`
5. `Chapter`
6. `ChapterContract`

### Layer B — Manuscript and book memory

7. `ManuscriptUnit`
8. `Concept`
9. `SceneExample`
10. `StyleProfile`

### Layer C — Evidence

11. `Claim`
12. `Source`
13. `Evidence`

### Layer D — Editorial work

14. `EditorialFinding`
15. `BoundedTask`
16. `ChangeProposal`

### Layer E — Authority and provenance

17. `Revision`
18. `Decision`
19. `Approval`
20. `ProvenanceRecord`

### Layer F — Quality and release

21. `EvaluationRun`
22. `LiteraryMaster`

These are logical entities. They do not imply 22 database tables. Technical storage is decided later in Technical Architecture v0.1.

## 3. Root object: BookProject

`BookProject` is the stable root identity of one book.

Minimum fields:

- `book_id`
- working title
- operating mode: `BOOK_FROM_ZERO | EXISTING_MATERIALS`
- `book_profile_id`
- current workflow stage
- current authority references
- current Literary Master release, if any
- created/updated timestamps

`BookProject` owns or references every book-specific object below.

It is not itself the manuscript text.

## 4. BookProfile

`BookProfile` tells BOOK OS what kind of book it is producing.

For v0.1:

- domain: `BUSINESS_NONFICTION`
- one primary subtype
- optional one secondary subtype
- profile/ruleset version

Initial subtypes are the already accepted Business Nonfiction taxonomy.

The profile may influence research standards, structural expectations, domain pathologies, Style rules, and BookBench criteria, while keeping the user-facing choice simple.

## 5. BookContract

`BookContract` is the accepted definition of the book's promise and boundaries.

Minimum fields:

- intended reader
- reader problem
- central promise
- central thesis
- unique angle
- intended intellectual trajectory
- explicit exclusions
- evidence standard
- voice/genre constraints
- readiness criteria

`BookContract` is versioned and authority-bearing.

Drafting cannot treat an unapproved Book Contract as settled authority.

## 6. BookArchitecture

`BookArchitecture` describes how the Book Contract becomes a whole book.

Minimum fields:

- ordered parts/chapters
- purpose of each chapter
- intellectual progression
- concept allocation
- promise/thesis coverage
- dependencies between chapters
- major transitions

It is versioned and authority-bearing.

A chapter move, merge, deletion, or large functional change is a material architectural change.

## 7. Chapter

`Chapter` is a stable identity, not a mutable text blob.

Minimum fields:

- `chapter_id`
- ordinal / position
- working/current title
- architecture role
- current `ChapterContract` revision
- current manuscript revision/reference
- chapter workflow state

The stable `chapter_id` survives title changes and revisions.

## 8. ChapterContract

`ChapterContract` defines what a chapter must accomplish before drafting or major rewriting.

Minimum fields:

- purpose
- new idea / contribution
- assumed prior reader knowledge
- intended reader outcome
- required claims
- required/permitted research
- required scenes/examples
- ideas owned elsewhere and not to repeat
- rhythm expectations
- opening requirements
- ending requirements
- transition requirements

It is versioned and authority-bearing.

## 9. ManuscriptUnit

`ManuscriptUnit` gives BOOK OS stable locations inside manuscript text.

v0.1 hierarchy may use:

`Chapter -> Section -> Text Block`

A text block can correspond to a paragraph or another bounded editable unit.

Minimum fields:

- stable `unit_id`
- parent unit/chapter
- unit type
- order
- current revision
- text/content

Why this exists: patches, claims, findings, comments, and provenance must point to stable objects, not only fragile character offsets such as "characters 18420-18930".

A proposal must identify a target unit and the exact base revision it was created against.

## 10. Concept

`Concept` represents a meaningful idea the book intentionally introduces or uses.

Minimum fields:

- `concept_id`
- canonical name
- definition
- owning/introduction location
- related concepts
- intended reuse rules
- current status

This supports architecture, semantic repetition checks, contradiction detection, glossary-like consistency, and Book Memory.

## 11. SceneExample

`SceneExample` is a reusable narrative or explanatory asset.

Examples include a business case, founder story, anecdote, experiment description, hypothetical example, or personal scene.

Minimum fields:

- `example_id`
- type
- summary/content reference
- source/provenance
- intended editorial function
- allowed/actual usage locations
- factual verification requirement

This allows BOOK OS to detect accidental reuse of the same example across chapters.

## 12. StyleProfile

`StyleProfile` is the formal versioned definition of author voice and prose constraints.

It can contain:

- explicit rules
- prohibited constructions
- preferred tendencies
- reference samples
- measurable fingerprint features
- tolerances
- AI-prose pathology rules

It is authority-bearing when approved.

## 13. Claim

`Claim` is a separately traceable, externally checkable assertion.

Minimum fields:

- `claim_id`
- normalized claim text
- manuscript location(s)
- claim type
- importance/materiality
- required evidence level
- current verification state
- linked evidence

Suggested verification states for v0.1:

`UNREVIEWED | SUPPORTED | PARTIALLY_SUPPORTED | DISPUTED | UNSUPPORTED | REJECTED`

These are evidence states, not Authority Protocol statuses.

## 14. Source

`Source` represents one external source.

Minimum fields when applicable:

- `source_id`
- source type
- title
- author/organization
- publication/date
- DOI / URL / bibliographic identifiers
- access date
- primary vs secondary classification
- reliability metadata
- stored citation metadata

A source existing in the ledger does not by itself prove a claim.

## 15. Evidence

`Evidence` is the explicit relationship between a `Claim` and a `Source`.

Minimum fields:

- `evidence_id`
- `claim_id`
- `source_id`
- supporting location/excerpt pointer
- relationship: `SUPPORTS | PARTIALLY_SUPPORTS | CONTRADICTS | CONTEXT_ONLY`
- strength
- limitations
- analyst/reviewer decision

This distinction is fundamental:

`Source != Evidence != Claim`.

## 16. EditorialFinding

`EditorialFinding` records a diagnosed problem or opportunity without silently changing text.

Minimum fields:

- `finding_id`
- category
- target entity/unit and base revision
- diagnosis
- why it matters
- supporting evidence
- severity
- confidence
- status: `OPEN | RESOLVED | WAIVED | SUPERSEDED`

Examples: semantic repetition, weak opening, unsupported claim, architecture drift, author-voice deviation.

## 17. BoundedTask

`BoundedTask` is a first-class record of permission to perform a limited operation.

Minimum fields:

- `task_id`
- task type / role
- target object(s)
- exact authority baseline/revision(s)
- reason
- `IN SCOPE`
- `OUT OF SCOPE`
- constraints
- expected output type
- assigned actor/model role
- resulting findings/proposals

This object operationalizes the accepted rule:

`authority -> bounded task -> proposal -> review -> acceptance -> new authority`.

No generic "make the whole book better" task is valid.

## 18. ChangeProposal

`ChangeProposal` represents a proposed change that has not yet replaced authority.

Minimum fields:

- `proposal_id`
- originating finding/task
- target object/unit
- exact base revision
- proposed operation/patch
- rationale
- expected effect
- risks
- confidence
- provenance
- status: `OPEN | ACCEPTED | REJECTED | SUPERSEDED`

Material proposals require human decision.

For manuscript text, proposals should be reviewable as a human-readable diff.

## 19. Revision

`Revision` is an immutable snapshot/version of an authority-bearing object.

Minimum fields:

- `revision_id`
- entity id/type
- parent revision(s)
- content or content reference
- checksum/hash
- created timestamp
- provenance reference
- Authority Protocol status

Accepted statuses remain:

`DRAFT | PROPOSED | REVIEWED | APPROVED | LOCKED | SUPERSEDED`

Once a revision is `APPROVED` or `LOCKED`, its content is immutable.

A new edit creates a new revision.

## 20. Decision

`Decision` records a human or formally permitted decision about a proposal or project choice.

Minimum fields:

- `decision_id`
- decision type
- subject/proposal
- actor
- decision: `ACCEPT | REJECT | REQUEST_REVISION | WAIVE`
- reason
- timestamp

Important creative/material acceptance belongs to the human Owner.

Decision history is never silently rewritten.

## 21. Approval

`Approval` is the formal authority-transition record created when the required decision and gates permit a revision to become current authority.

Minimum fields:

- `approval_id`
- approved revision
- prior authority revision, if any
- approving actor
- gates/checks satisfied
- timestamp

If a new revision becomes authority, the prior approved authority may become `SUPERSEDED` but remains recoverable.

`Decision` answers "what did we decide and why?"  
`Approval` answers "which exact revision became authority?"

## 22. ProvenanceRecord

`ProvenanceRecord` records where content or a change came from.

Minimum fields as applicable:

- origin: `HUMAN_WRITTEN | AI_ASSISTED | AI_GENERATED | IMPORTED | SYSTEM_DERIVED`
- actor
- provider/model
- model/version
- task id
- input authority revisions
- prompt/task-template version or hash
- timestamp
- transformation metadata

Secrets/API keys are never part of provenance.

## 23. EvaluationRun

`EvaluationRun` records a BookBench or other quality check against exact revisions.

Minimum fields:

- `evaluation_id`
- evaluator/check type and version
- target revision(s)
- inputs/configuration
- findings
- metrics when applicable
- model/provider when applicable
- timestamp

Evaluation results do not themselves change authority.

They can satisfy review gates or generate Editorial Findings.

## 24. LiteraryMaster

`LiteraryMaster` is an immutable release manifest, not "the latest Word file".

Minimum fields:

- `master_id` / release version
- exact Book Contract revision
- exact Book Architecture revision
- exact Style Profile revision
- ordered exact chapter/manuscript revisions
- Claim Ledger / evidence snapshot reference
- final EvaluationRun / BookBench references
- human final approval
- checksums
- release timestamp

A Literary Master may only reference revisions that satisfy the release gate.

Audio, Translation, Publishing, EPUB, PDF, and other production outputs are derivatives of a Literary Master and must not mutate it backward.

## 25. Relationship map

```text
BookProject
├── BookProfile
├── BookContract
├── BookArchitecture
├── StyleProfile
├── Chapters[]
│   ├── ChapterContract
│   └── ManuscriptUnits[]
│       ├── Claims[]
│       ├── Concepts[]
│       └── SceneExamples[]
├── Sources[]
│   └── Evidence[] <-> Claims[]
├── EditorialFindings[]
│   └── BoundedTasks[]
│       └── ChangeProposals[]
├── Revisions[]
│   ├── ProvenanceRecords[]
│   ├── Decisions[]
│   └── Approvals[]
├── EvaluationRuns[]
└── LiteraryMasters[]
```

This is a conceptual graph, not a storage schema.

## 26. Non-negotiable invariants

### I1 — Stable identity, immutable revisions

Entity identity survives editing. Approved/locked revision content does not.

### I2 — No authority mutation in place

Changing an approved/locked object always creates a new proposal/revision.

### I3 — Exact baseline for every proposal

Every material proposal identifies the exact revision it was created against.

### I4 — Stable manuscript addressing

Claims/findings/proposals attach to stable manuscript units and revisions, not only raw character offsets.

### I5 — Claim traceability

A material factual claim can be traced to evidence and sources, or is visibly marked unsupported/unresolved.

### I6 — Source is not proof by itself

Support is expressed through an Evidence object connecting source and claim.

### I7 — AI cannot self-approve material authority

A model may draft, diagnose, evaluate, or propose. It cannot give itself final human approval.

### I8 — Provenance is append-only history

Relevant origin/model/task/input information remains recoverable after acceptance.

### I9 — Evaluations do not silently edit

BookBench/evals produce findings or gate evidence; they do not mutate manuscript authority.

### I10 — Literary Master is reproducible

Given the release manifest, BOOK OS can reconstruct the exact approved manuscript and supporting release state.

## 27. Intentionally deferred from v0.1 ontology

Do not add first-class complexity yet for:

- multi-author permissions and publisher organizations;
- billing/subscriptions;
- marketing campaigns;
- cover design;
- print/EPUB layout;
- audiobook production internals;
- translation workflow internals;
- fine-tuning datasets as a separate product subsystem;
- autonomous agent social structures;
- every possible publishing metadata standard.

These may integrate later without changing the core book/authority model.

## 28. Acceptance questions

Core Ontology v0.1 is acceptable if the Owner and Central Brain can answer yes to all of these:

1. Can one real Business Nonfiction book from zero be represented without using chat memory as hidden state?
2. Can BOOK OS distinguish book intent, manuscript text, claims, sources, evidence, findings, proposals, and accepted authority?
3. Can every material edit be attached to an exact baseline and human decision?
4. Can claims and factual support be traced separately?
5. Can author voice and BookBench be attached to exact revisions?
6. Can a Literary Master be reconstructed exactly later?
7. Can Audio/Translation/Publishing consume the master without acquiring authority to rewrite it?
8. Is the model independent of any one AI provider?
9. Is the ontology small enough to implement in v0.1?

This document is the accepted ontology authority for v0.1 implementation. Technical Architecture v0.1 is defined in `TECHNICAL_ARCHITECTURE_v0.1.md`.
