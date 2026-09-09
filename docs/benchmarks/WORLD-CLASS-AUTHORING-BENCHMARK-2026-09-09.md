# BOOK OS — WORLD-CLASS AUTHORING PRODUCT BENCHMARK

**Status:** ACTIVE PRODUCT BENCHMARK  
**Date:** 2026-09-09  
**Scope:** authoring UX, planning, research, AI assistance, revision, publishing, local-first product behavior  
**Rule:** do not reinvent solved commodity UX. Borrow the strongest proven interaction pattern, adapt it to BOOK OS authority/evidence rules, then improve it where BOOK OS has a genuine advantage.

## 1. Product north star

BOOK OS should feel as easy to enter as a mature writing app, as controllable as a professional editor, as research-aware as a serious knowledge tool, and as AI-capable as the strongest current AI-native authoring systems.

The product must expose **author work**, not implementation machinery.

Default experience:

`Books / structure → current working surface → optional inspector`

The center of the application belongs to the current author/editor task. Complexity appears progressively, not all at once.

## 2. Benchmark set and what BOOK OS should take

### Scrivener — long-form project control

Take:
- Binder-style persistent manuscript tree;
- Corkboard/Outliner bird's-eye structure;
- drag-and-drop structural rearrangement;
- split editor for manuscript + research or chapter + chapter;
- section snapshots + compare before major rewrites;
- seamless whole-manuscript / single-section views;
- research stored inside the project and always reachable;
- compile/export separated from writing format.

Improve in BOOK OS:
- structural moves must show their effect on Book Contract, chapter function, dependencies and reserved concepts;
- snapshots become authority-aware revisions, not only text backups;
- the outliner gets quality/evidence/overlap signals rather than only metadata.

### Ulysses — calm information architecture

Take:
- minimal three-pane mental model;
- hideable panels and distraction-free writing;
- revision mode separated from drafting mode;
- goals/stats present but not dominant;
- fast navigation without exposing implementation details.

Improve:
- revision mode becomes BOOK OS editorial mode with explicit finding → rationale → proposal → accept/reject;
- current stage/gate is visible but compact.

### iA Writer — focus and local deterministic style assistance

Take:
- Focus Mode at sentence/paragraph level;
- typewriter scrolling;
- syntax highlighting to reveal prose structure;
- local non-AI Style Check with custom patterns;
- no forced destructive edits.

Improve:
- Russian-first syntax/style diagnostics;
- integrate BOOK OS anti-junk lexicon, author style fingerprint and accepted exceptions;
- show local deterministic findings instantly, while expensive AI review stays optional.

### Atticus / Vellum — publishing should be easy

Take:
- clear separation of writing and final formatting;
- reusable professional themes;
- preview before export;
- one controlled path to print/ebook-ready output.

Improve:
- output profiles for LitRes and other channels;
- export must originate from exact Literary Master and record reproducible provenance.

### Dabble — progressive disclosure and focus

Take:
- clean manuscript-centered screen;
- Plot Grid / planning view available when needed and out of the way when not;
- drag-and-drop structure;
- goals, notes and supporting material surrounding the manuscript rather than replacing it;
- Focus Mode and hideable interface chrome.

Improve:
- BOOK OS planning view is nonfiction-first: promise, thesis, reader decision, chapter contribution, evidence needs and dependency lanes.

### Reedsy Studio — low-friction author workflow

Take:
- instantly understandable chapter sidebar + editor;
- Boards for flexible planning/research;
- comments/change tracking as collaboration primitives;
- professional export from the same project.

Improve:
- Boards become typed BOOK OS objects where useful: Claim, Evidence, Example, Reader Problem, Chapter Function, Source, Decision.

### Plottr / Final Draft — visual architecture

Take:
- timeline/board/outline views of the same underlying structure;
- zoom from whole work to a small section;
- cards linked to real manuscript units;
- custom lanes / plotlines / structure lines;
- visual reordering that changes the actual structure.

Improve:
- nonfiction lanes: thesis, promise coverage, concepts, examples, evidence, reader progression, archetype branches, freshness risk;
- heatmap for chapter overlap, evidence gaps and promise coverage.

### Campfire — modular knowledge graph

Take:
- modular supporting objects;
- cross-references between objects;
- project encyclopedia / research modules;
- configurable templates.

Improve:
- use a strict Book Graph ontology rather than unlimited worldbuilding objects;
- distinguish authority objects from derived indexes and notes.

### Novelcrafter — persistent project intelligence + model choice

Take:
- Codex-style persistent project knowledge linked across the work;
- shared knowledge across books/series;
- multiple planning views;
- AI that can brainstorm, draft or review with project context;
- model/provider flexibility rather than one-model lock-in;
- custom operations/shortcuts for expert users.

Improve:
- BOOK OS Book Graph must include evidence, authority, decisions, reservations, freshness and series overlap;
- model routing is operation-aware and quality-evaluated;
- AI output is always a proposal where authority requires human acceptance;
- default user experience hides provider plumbing.

### Sudowrite / LivingWriter — AI should act on the current object

Take:
- contextual actions such as write, guided write, rewrite, expand, brainstorm, analyze, chat with manuscript;
- AI commands live next to the text/task rather than in a giant global control panel;
- structured scene/unit generation from an approved plan.

Improve:
- nonfiction actions: strengthen argument, find missing evidence, challenge claim, propose example, reduce repetition, test reader comprehension, repair transition, compare alternatives;
- no blind "expand" path that incentivizes padding;
- every material AI edit can be reviewed as a diff.

### Grammarly — suggestion UX

Take:
- inline finding cards;
- Accept / Dismiss rather than silent mutation;
- explanation behind each suggestion;
- sentence/paragraph-level rewrite actions.

Improve:
- each BOOK OS suggestion identifies the governing authority/evidence/style rule;
- accepted/rejected decisions feed the private Editorial Decision Corpus;
- whole-book effects and cross-chapter conflicts are checked before material acceptance.

### Zotero — research integrity

Take:
- collect sources with high-quality metadata;
- built-in reading/annotation workflow;
- annotation → note with link back to exact source location;
- citation/bibliography generation;
- saved searches/collections.

Improve:
- explicit `Claim != Source != Evidence` relation;
- evidence strength, limitation and conflict status;
- click from manuscript claim to exact evidence and source location;
- freshness/reverification status for time-sensitive claims.

### Readwise Reader — research inbox and cited retrieval

Take:
- one inbox for heterogeneous research material;
- highlight/tag/note without breaking reading flow;
- keyboard-driven capture;
- chat/search over a whole research library with citations;
- filtered views.

Improve:
- retrieval must feed bounded BOOK OS tasks, not a free-floating chat;
- extracted ideas remain research/notes until promoted through Claim/Evidence/authority rules.

### Obsidian — local ownership and visual knowledge

Take:
- local-first data ownership;
- links/backlinks;
- graph and canvas views;
- open, durable data formats where appropriate;
- optional extensions without forcing cloud dependence.

Improve:
- graph semantics are typed and editorially meaningful;
- the user sees a useful Book Map, not an attractive but noisy generic graph.

## 3. BOOK OS target desktop layout

### Left: Navigator

Persistent, compact tree:
- Books;
- Parts;
- Chapters;
- Research;
- Sources;
- optional Series.

The user can collapse the sidebar completely.

### Center: Current Work

Only the current task occupies the main surface:
- define book;
- review contract;
- design architecture;
- write chapter/section;
- research claim;
- edit prose;
- review findings;
- prepare Literary Master.

No PilotPanel, provider diagnostics, memory index controls, raw provenance or API credentials in the default center surface.

### Right: Inspector

Hidden by default / opened on demand:
- current object metadata;
- status and authority;
- chapter purpose;
- evidence links;
- AI/model override;
- quality findings;
- word/character stats;
- provenance details.

### Top bar

Only:
- project/book name;
- current stage;
- one primary current action;
- search / command palette;
- view/focus toggle;
- settings.

## 4. Killer capabilities BOOK OS should make better than the benchmark set

### A. Living Book Map

One visual map of the complete nonfiction system, not merely chapters.

Layers can show:
- thesis/promise coverage;
- reader progression;
- concepts;
- examples;
- evidence;
- chapter dependencies;
- archetype branches;
- repetition/overlap;
- freshness risk;
- status/admission.

### B. Evidence-to-prose trace

Click a material sentence/claim and see:
`manuscript → Claim → Evidence → exact source/location → verification/freshness state`.

This should be materially stronger than ordinary bibliography management.

### C. Authority-aware AI review

AI never silently rewrites accepted material. Material change appears as:
`diagnosis → proposed diff → reason → affected authority/evidence → accept/reject`.

### D. Blind multi-model decision mode

For high-value creative/structural choices, compare candidate outputs without revealing model identity until the human preference is recorded.

This should be available selectively, not forced into ordinary writing.

### E. Editorial Decision Memory

BOOK OS learns from:
`original → finding → proposed change → accepted/rejected → reason → final`.

Use first for retrieval/routing/calibration; do not jump directly to fine-tuning.

### F. Series Brain

Across books in a series:
- reserve concepts/territory;
- detect overlap;
- track recurring terminology and author positions;
- protect each book's unique promise;
- surface useful cross-references without copy-paste reuse.

### G. Freshness Radar

Automatically identify claims likely to age:
- platforms;
- laws/regulations;
- prices/tariffs;
- statistics;
- product capabilities;
- market data.

Require reverification at the appropriate gate before final release.

### H. Zero-prompt author experience

The normal user should not have to engineer prompts.

They choose intent and provide content/context. BOOK OS constructs the bounded prompt/task internally from authority and the current object.

Expert users may inspect/extend advanced operations, but prompt plumbing is never the default UX.

### I. Local-fast / AI-when-needed split

Instant local operations:
- navigation;
- editing;
- search;
- version history;
- deterministic style checks;
- local Book Graph operations;
- offline reading and local diagnostics.

Network AI is invoked only for operations that materially benefit from it.

### J. Reproducible Literary Master

Publishing/export is not "whatever file is open".

A Literary Master points to exact accepted revisions, evidence snapshot, style profile, BookBench state and human release decision. Derived DOCX/PDF/EPUB/audio handoffs remain reproducible.

## 5. Explicit rejects

BOOK OS should not copy:
- giant dashboards that expose every subsystem simultaneously;
- provider/API configuration in the primary author workflow;
- forced chat as the main interface;
- one-button whole-book generation;
- automatic expansion for the sake of length;
- a single magic quality score;
- generic graph visualizations with no editorial meaning;
- platform lock-in as a substitute for durable local book state;
- AI changes that mutate approved text without review;
- prompt-engineering requirements for ordinary users.

## 6. Product acceptance tests derived from the benchmark

A new user should be able to:
1. launch BOOK OS like a normal Mac app;
2. create/open a book without understanding BOOK OS internals;
3. understand the current step in under 10 seconds;
4. reach the manuscript/architecture/research object they need in at most a few obvious interactions;
5. hide all nonessential panels;
6. perform local reading/editing without network access;
7. invoke AI in context without writing a technical prompt;
8. review any material AI change before it becomes authority;
9. trace important factual claims to evidence;
10. recover earlier accepted states;
11. export from an exact Literary Master.

If BOOK OS is more confusing than the mature benchmark products for a commodity task, that is a BOOK OS defect, not an "advanced feature".

## 7. Source set checked 2026-09-09

Official/current product material used for this benchmark includes:
- Literature & Latte / Scrivener — overview and feature documentation;
- Ulysses — help/revision/focused-writing documentation;
- iA Writer — Focus Mode, Syntax Highlight and Style Check documentation;
- Atticus — editor/formatting product documentation;
- Dabble — project organization, Plot Grid and Focus Mode documentation;
- Reedsy Studio — writing, Boards, collaboration and export documentation;
- Plottr — visual timelines, scene cards and series planning;
- Final Draft — Outline Editor / Beat Board documentation;
- Campfire — desktop/modules/research/relationship/timeline feature documentation;
- Novelcrafter — Codex, planning, AI/model-provider flexibility;
- Sudowrite — Write/Guided/Rewrite/Brainstorm/Scenes/Draft documentation;
- LivingWriter — AI manuscript chat/analysis and planning tooling;
- Grammarly — suggestion, explanation and paragraph-rewrite UX;
- Zotero — source capture, PDF annotations, notes, citations and syncing;
- Readwise Reader — research inbox, highlights, filtered views and cited document/library chat;
- Obsidian — local files, backlinks, graph, Canvas and optional sync/plugins.
