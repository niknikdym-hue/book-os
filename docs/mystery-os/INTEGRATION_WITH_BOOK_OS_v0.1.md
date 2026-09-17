# MYSTERY OS — INTEGRATION WITH BOOK OS v0.1

**Status:** INCUBATION DRAFT  
**Date:** 2026-09-17

## 1. Objective

MYSTERY OS is designed from day one to become a genre module inside a broader publishing system rather than a parallel monolith.

Current BOOK OS authority is nonfiction-focused. Therefore this document defines a **future integration boundary**, not an authorization to modify current production semantics.

## 2. Shared platform core

The following capabilities should remain genre-neutral and be reused:

- Author Profile;
- Series Profile / Series Studio;
- Style Profile / author voice;
- project/revision/authority graph;
- human approval statuses;
- Model Gateway and operation-level routing;
- cost authorization/accounting;
- provider/model provenance;
- Book Memory and retrieval infrastructure;
- file/material ingestion;
- research source/evidence infrastructure for real-world facts;
- whole-book editing framework;
- generic BookBench execution/reporting infrastructure;
- Editorial Decision Memory;
- Literary Master semantics;
- output/export registry;
- audio-script/adaptation workflow;
- publishing package/platform metadata;
- local-first desktop/security/backup/recovery;
- task/execution governance.

The rule is `share infrastructure, specialize editorial semantics`.

## 3. Fiction-specific modules

MYSTERY OS should add bounded modules/interfaces rather than overload nonfiction concepts.

Proposed logical modules:

### `fiction.story_definition`
Owns StoryDefinition and GenreProfile.

### `fiction.case_engine`
Owns CaseSolution, suspects, secrets, clue/evidence chains and objective CaseTimeline.

### `fiction.mystic_engine`
Owns MysticRuleSet and MysticEvent consistency.

### `fiction.character_engine`
Owns character knowledge states, CharacterArc and RelationshipArc.

### `fiction.scene_architecture`
Owns RevealPlan, NarrativeTimeline, SceneContract and writing admission.

### `fiction.mysterybench`
Owns case reconstruction, fair-play, timeline, clue lifecycle, cold-reader and anti-cliche evaluations.

### `fiction.series_brain`
Extends existing Series Studio with MysteryBookPassport, series engine and fiction-specific difference/collision maps.

## 4. Do not misuse nonfiction objects

Do NOT map fiction objects into nonfiction fields merely to avoid schema work.

Examples of prohibited shortcuts:

- putting culprit/motive into `central_thesis`;
- storing clues as nonfiction `Claim` records;
- using Research `Evidence` as a substitute for in-world EvidenceChain;
- treating scenes as chapters with fake “claims”;
- storing MysticRuleSet as unstructured notes;
- putting character knowledge into prompt text only.

These shortcuts would make future validation unreliable.

## 5. Shared vs distinct evidence semantics

### Real-world research evidence
Existing BOOK OS semantics:
`Source -> Evidence -> Claim`

Used for factual realism: medicine, law, police procedure, emergency services, technology, geography, history, etc.

### Fiction in-world evidence
MYSTERY OS semantics:
`CaseEvent -> Clue -> Interpretation/Hypothesis -> EvidenceChain -> CaseSolution`

These must remain separate in the data model, while UI can present them coherently.

## 6. Proposed top-level genre capability model

Future BOOK OS may expose a project `editorial_mode`, for example:

- `NONFICTION`;
- `MYSTERY_FICTION`;
- future fiction genres only after separate validated modules exist.

Do not generalize prematurely into a vague `FICTION` mode that promises all genres.

## 7. Lifecycle mapping

Shared high-level application journey may remain simple while internal gates differ.

### Nonfiction
`Idea -> Definition -> Research -> Architecture -> Writing -> Edit -> Check -> Release`

### Mystery fiction
`Idea -> Story Definition -> Case Solution -> Mystery Architecture -> Writing -> Edit -> MysteryBench -> Release`

The author-facing UI may still use common stage navigation, but stage internals and required authority objects must be genre-specific.

## 8. Book Memory extension

MYSTERY OS needs retrieval/indexing over:

- characters and aliases;
- character knowledge by scene/time;
- locations;
- clues;
- secrets;
- case timeline;
- narrative timeline;
- supernatural rules/events;
- series continuity;
- repeated scene/dialogue/twist patterns;
- consumed/reserved series assets.

Indexes remain derived/rebuildable from canonical structured state and manuscript revisions.

## 9. Model routing extension

New editorial operations should be independently routable, including:

- premise/commercial analyst;
- case architect;
- clue/fair-play auditor;
- timeline auditor;
- supernatural-rule auditor;
- scene architect;
- fiction writer;
- character editor;
- cold reader;
- adversarial case reconstructor;
- anti-cliche reviewer;
- series fiction editor.

Do not assume the best nonfiction Writer/Judge models are automatically best for fiction operations. Promotion should use operation-specific eval evidence.

## 10. MysteryBench as BookBench extension

Reuse generic evaluation run infrastructure, provenance, findings, severity and human dispositions.

Add fiction dimensions rather than a separate incompatible judge framework.

Blocking genre findings cannot be averaged into a general score.

## 11. Style system extension

Existing StyleProfile should remain shared but gain fiction-relevant inspectable features such as:

- POV and psychic distance;
- dialogue ratio and attribution style;
- scene/chapter rhythm;
- description density;
- interiority;
- suspense syntax/rhythm;
- humor/darkness;
- violence explicitness;
- romance explicitness;
- recurring prohibited phrases/constructions;
- reference passages where rights permit.

Anti-cliche policy remains a separate quality layer; style preference cannot authorize broken plot logic.

## 12. Literary Master extension

Future Mystery Literary Master manifest should add exact references to:

- StoryDefinition;
- CaseSolution;
- GenreProfile;
- Character authority;
- Clue/EvidenceChain snapshot;
- CaseTimeline;
- MysticRuleSet if applicable;
- RevealPlan;
- final MysteryBench/ColdReader evidence;
- Series Closure if applicable.

The final reader-facing export does not expose private spoiler authority, but release provenance retains it locally.

## 13. Data migration principle

No fiction database migration should be added until:

1. authority/spec pack is human-approved;
2. `Линия 112` pilot definition exercises the model on paper;
3. required fields/gates are shown to be necessary rather than speculative;
4. interaction with Task 021/Series Studio candidate is reconciled;
5. migration plan is forward-only and backup-tested.

This avoids building unused schema before the editorial process is proven.

## 14. UI integration principle

Do not add a “Mystery OS” engineering dashboard to the main author experience.

Future user-facing flow should remain author-centric:

- create project;
- choose `Мистический детектив` / relevant genre;
- enter a short idea or series direction;
- review concept;
- review/approve spoiler authority in a clearly separated author-only workspace;
- follow staged creation;
- review required decisions/findings;
- approve final manuscript and outputs.

Advanced clue/timeline/suspect graphs may be inspectable tools, not mandatory clutter on every screen.

## 15. Integration gates

MYSTERY OS may be promoted into production BOOK OS only after all are true:

- Owner approves genre authority pack;
- one complete real-book pilot is produced;
- case/fair-play/timeline audits demonstrate value;
- cold-reader/adversarial evaluation is run on the real manuscript;
- professional human editorial review finds the system useful rather than bureaucratic;
- anti-cliche/series uniqueness layer catches real defects;
- no current nonfiction workflow regresses;
- exact integration implementation passes software CI;
- human Owner explicitly approves integration/release.

## 16. Non-goals of Task 022

Task 022 does not authorize:

- database migrations;
- Desktop UI changes;
- paid model calls;
- manuscript generation;
- installation/deployment;
- merge to main;
- converting BOOK OS product identity from nonfiction to fiction;
- claiming MYSTERY OS is production-ready.

Task 022 creates the reusable editorial foundation and machine-readable contract for review.