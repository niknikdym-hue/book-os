# BOOK OS — AUDIO-NATIVE AUTHORING, EXISTING-TEXT AUDIO ADAPTATION & SERIES v0.2

**Status:** ACCEPTED PRODUCT / EDITORIAL DESIGN
**Version:** 0.2.0
**Original decision date:** 2026-09-02
**Amended:** 2026-09-03

This version supersedes v0.1 inside the still-open authority PR #23. It preserves the accepted audio-native and series design and adds a strict separation between creating a book from zero and creating an audio edition from an existing text book.

## 1. Product topology: two different workflows, never one selector

BOOK OS has two fundamentally different audio-related workflows.

### Workflow A — create a book from zero

The user starts a new book project. The system plans, drafts, edits and evaluates the work from the beginning.

Only this workflow has the delivery-profile choice:

- `TEXT_FIRST` — written primarily for visual reading;
- `AUDIO_FIRST` — planned and written from the first stage for listening;
- `DUAL_TEXT_AUDIO` — created from the first stage so the same intellectual work is professionally usable in both text and audio editions.

### Workflow B — prepare an audio edition from an existing text book

The user already has an approved/imported text book. That text is the source authority. BOOK OS derives a separate audio script from an exact source revision.

Only this workflow has the audio-adaptation choice:

- `SOURCE_FAITHFUL` — по оригиналу, с необходимой адаптацией для аудио;
- `LISTENING_ADAPTATION` — сохранить суть и концепцию оригинала, но разрешить существенную переработку текста специально для прослушивания.

The two workflows must not share one combined mode selector, enum, prompt branch or release gate. A finished text book being adapted for audio does not become `AUDIO_FIRST` and does not silently change its original delivery profile.

Series membership is a separate first-class dimension and may apply to books from either workflow without merging the workflows.

The user-facing rule remains: **simple outside, smart inside**.

## 2. Workflow A — delivery profile for a book created from zero

Each newly created `BookProject` has one `delivery_profile`:

- `TEXT_FIRST`;
- `AUDIO_FIRST`;
- `DUAL_TEXT_AUDIO`.

This is selected in the new-book flow and persisted as book authority. It is not inferred later from export choice.

### 2.1 `TEXT_FIRST`

The book is planned and written primarily for visual reading. Normal BOOK OS literary/editorial gates apply.

A later decision to make an audio edition from this finished text enters Workflow B. It does not retroactively convert the source project to `AUDIO_FIRST`.

### 2.2 `AUDIO_FIRST`

`AUDIO_FIRST` does **not** mean “write ordinary prose and later run TTS over it”. BOOK OS must plan and write for a listener who normally receives the sentence once, cannot scan a page, and may be driving, walking, cooking or exercising.

Audio-first rules therefore influence:

- Book Contract;
- Architecture;
- Chapter Contracts;
- Writer prompts;
- Style Profile;
- Book Memory;
- BookBench diagnostics;
- Literary Master release readiness;
- immutable Audio Studio handoff metadata.

TTS, SSML, voice selection, pronunciation rendering, mastering and audio QC remain owned by Audio Studio. BOOK OS owns literary/editorial listenability.

### 2.3 `DUAL_TEXT_AUDIO`

`DUAL_TEXT_AUDIO` is not a compromise mode with weak text and weak audio. The manuscript must pass both reading and listening constraints.

When a concept genuinely needs a visual object such as a table, chart, formula, diagram or URL-heavy reference, BOOK OS must explicitly choose a representation strategy instead of silently assuming a page:

- rewrite the idea as self-sufficient spoken prose;
- retain the visual for the text edition and add an approved audio explanation/handoff note;
- move detail into a companion artifact while keeping the spoken argument complete;
- reject the visual dependency if it is unnecessary.

The core argument must remain understandable without forcing the listener to look at a page.

## 3. Workflow B — audio edition from an existing text book

### 3.1 Source authority and immutability

Workflow B starts only from an identified source manuscript/Literary Master revision. BOOK OS must bind the audio work to the exact source identity and content hash.

The source text is never silently rewritten. BOOK OS creates a separate versioned `AudioScript` / `AudioEditionScript` artifact.

Minimum derived-audio identity:

- source project/book identity;
- exact source Literary Master/revision identity and hash;
- adaptation mode;
- audio-script revision identity;
- transformation/coverage map;
- provenance/evidence bindings for material factual claims;
- authority status/revision history;
- human approval identity/time when approved.

AI-produced audio-script text remains `DRAFT/PROPOSED`. AI cannot approve it.

### 3.2 Mode A — `SOURCE_FAITHFUL`

User-facing label: **«По оригиналу, с адаптацией для аудио»**.

The audio script should follow the source book closely in content, order, wording and structure. It is not required to be mechanically word-for-word when literal transfer would damage listening quality.

Permitted bounded adaptations include:

- replacing page-dependent references such as “see below”;
- converting tables/charts/visual dependencies into spoken explanation or approved companion references;
- reshaping overloaded sentences for one-pass comprehension;
- restructuring long lists into audible groups;
- making quotation attribution clear before or during the quote;
- expanding necessary acronyms/terms on first audible use;
- removing raw URLs/reference strings from narration while preserving attribution elsewhere;
- adding minimal orientation where the page previously supplied it;
- adjusting punctuation and paragraph boundaries for natural narration.

This mode must have a source-fidelity gate. It should flag unjustified wording, structure, omission or content drift beyond what the audio adaptation requires.

### 3.3 Mode B — `LISTENING_ADAPTATION`

User-facing label: **«Сохранить суть и концепцию, переписать для аудио»**.

This is a genuine audio rewrite, not a light copy edit. The audio text may differ substantially from the printed text and may be written as a more vivid, natural, spoken work.

Allowed transformations include, subject to semantic-fidelity gates and human approval:

- substantially rewriting sentences and paragraphs;
- changing rhythm and sentence-length distribution;
- replacing written transitions with spoken transitions;
- rewriting chapter/section openings and endings for listening;
- moving explanatory material locally when that improves auditory comprehension;
- converting dense enumerations into interpreted spoken sequences;
- changing paragraph and local section boundaries;
- adding restrained reorientation where a listener genuinely needs it;
- removing page-specific scaffolding;
- using more conversational or vivid syntax while preserving the approved author identity;
- changing local presentation order when it improves comprehension and does not change the argument.

A materially restructured chapter or major change to argumentative order must be surfaced for explicit human approval.

The source book remains semantic authority. BOOK OS must preserve unless explicitly approved otherwise:

- core reader promise;
- thesis and concept;
- approved definitions and terminology;
- material factual claims;
- evidence and provenance relationships;
- argumentative logic;
- material conclusions;
- author identity/voice boundaries;
- legal/copyright/provenance constraints.

The model may not silently invent factual claims, replace evidence, reverse or weaken the thesis, omit a material claim, or reshape the book into a different concept.

New factual examples or claims require normal evidence/provenance. Purely rhetorical metaphors/analogies may be proposed, but they remain reviewable and must not smuggle in unsupported factual claims.

### 3.4 Transformation/coverage map

Every Workflow B audio script must make material transformation reviewable against the exact source.

At minimum, source units should be classified as applicable:

- `PRESERVED`;
- `REWRITTEN`;
- `MOVED`;
- `OMITTED`;
- `ADDED`.

`OMITTED` material claims and material `ADDED` content require explicit human acceptance before AudioScript approval.

The transformation map is not a requirement for one-to-one sentence mapping. In `LISTENING_ADAPTATION`, semantic coverage may be many-to-many, but the system must still prove where the source's material ideas, claims and evidence went.

## 4. Shared audio-native editorial rules

These rules apply to `AUDIO_FIRST`, the audio side of `DUAL_TEXT_AUDIO`, and Workflow B AudioScripts. They are quality constraints, not blind numeric bans.

### 4.1 One-pass comprehensibility

A listener should usually understand a sentence on first hearing.

BOOK OS should detect or avoid:

- overloaded nested syntax;
- ambiguous pronoun/reference chains;
- long parenthetical detours;
- sentences whose key subject arrives too late to remain easy to track;
- dense sequences of dates, percentages, names or qualifications without interpretation.

Complex thought is allowed. Unnecessary decoding cost is not.

### 4.2 Audible structure and orientation

The listener cannot visually scan headings or page position. Therefore:

- chapter and section openings should orient the listener naturally;
- transitions must express the intellectual move, not visual navigation;
- avoid page-dependent phrases such as “as shown above/below”, “see the table”, “in the diagram on the next page” unless an audio rendering strategy exists;
- structural signposting must not become repetitive presenter language.

### 4.3 Cognitive-load management

Long enumerations are difficult to hold in working memory.

BOOK OS should:

- group related items into meaningful chunks;
- prefer interpreted sequences over raw lists;
- flag multi-level enumerations and long item chains;
- allow deliberate repetition when it restores orientation, but distinguish it from redundant restatement.

### 4.4 Numbers, dates and measurements

Audio prose must be pronounceable and cognitively usable.

BOOK OS should flag:

- number strings that are easy to mishear;
- clusters of percentages without interpretation;
- tables read row-by-row;
- unexplained abbreviations and units;
- precision that adds visual density but no argumentative value.

Numbers should be integrated into the meaning of the sentence, not merely transferred from a spreadsheet.

### 4.5 Names, terms, acronyms and pronunciation

BOOK OS maintains literary identity; Audio Studio owns final pronunciation execution.

For audio-oriented work BOOK OS should maintain an exportable pronunciation/name ledger containing, where relevant:

- canonical spelling;
- first-use expansion for acronyms;
- language/origin note;
- optional pronunciation guidance supplied or approved by the human;
- consistency requirements across the book and series.

No pronunciation markup is inserted into source Literary Master text merely for TTS.

### 4.6 Quotations and attribution

Long quotations must not leave the listener unsure who is speaking. Attribution should be placed early enough for auditory comprehension. Source detail may live in notes/companion material, but the spoken argument must remain understandable.

### 4.7 Footnotes, citations, URLs and companion material

Audio prose must not depend on footnotes being visually available.

BOOK OS should:

- keep necessary attribution in fluent prose;
- move bibliographic detail to end matter/companion material when appropriate;
- flag raw URLs and reference strings in main narration;
- ensure removing/skipping the visual note does not break the central argument.

### 4.8 Tables, charts, formulas and figures

Every material visual dependency receives an explicit audio disposition:

- `SPOKEN_REWRITE`;
- `AUDIO_EXPLANATION`;
- `COMPANION_ARTIFACT`;
- `OMIT_FROM_AUDIO` only when omission does not damage the argument;
- `BLOCKED` when no honest audio representation exists yet.

An audio release candidate cannot contain unresolved `BLOCKED` material visual dependencies.

### 4.9 Rhythm, breath and narration

BOOK OS should optimize prose for spoken rhythm without flattening author voice:

- varied sentence length;
- natural breath groups;
- paragraph-level rhythmic contrast;
- controlled emphasis;
- avoidance of monotone same-shaped sentences;
- avoidance of fake rhetorical drama and AI-style stage language.

Punctuation remains literary punctuation. TTS-specific timing and SSML remain downstream in Audio Studio.

### 4.10 Chapter openings, endings and continuity

Audio-oriented architecture/scripts should favor chapters that can be entered without page scanning and exited with a clear intellectual landing.

BOOK OS may use brief reorientation when necessary, but must avoid mechanical “previously / now we will / in this chapter” boilerplate unless genuinely useful.

### 4.11 Estimated listening duration

BOOK OS may show a non-authoritative duration estimate from word count for planning. It must be labeled as an estimate because narrator, language, pacing, quotations and pauses change final duration.

## 5. BookBench / AudioScript quality gates

### 5.1 `LISTENABILITY`

Add/retain a first-class evaluation dimension: `LISTENABILITY`.

It should produce evidence with exact locations, never a single magic score.

Minimum finding families:

- `VISUAL_DEPENDENCY_UNRESOLVED`;
- `AUDITORY_REFERENCE_AMBIGUITY`;
- `DENSE_ENUMERATION`;
- `NUMBER_DENSITY_FOR_AUDIO`;
- `ACRONYM_OR_TERM_PRONUNCIATION_RISK`;
- `RAW_URL_IN_NARRATION`;
- `LONG_QUOTE_ATTRIBUTION_RISK`;
- `OVERLOADED_SENTENCE_FOR_LISTENING`;
- `AUDIO_ORIENTATION_GAP`;
- `AUDIO_REDUNDANCY`;
- `AUDIO_REORIENTATION_JUSTIFIED` as an allowed/positive classification where repetition is purposeful.

### 5.2 `SOURCE_FIDELITY` for `SOURCE_FAITHFUL`

This gate detects unjustified drift beyond necessary audio adaptation, including:

- omitted material source content;
- changed factual claims;
- changed evidence/attribution;
- unnecessary structural divergence;
- unsupported additions;
- conclusion/thesis drift.

### 5.3 `SEMANTIC_FIDELITY` for `LISTENING_ADAPTATION`

This gate allows large surface-form differences while protecting the book's intellectual identity.

Minimum finding families:

- `CORE_PROMISE_LOSS`;
- `THESIS_DRIFT`;
- `MATERIAL_CLAIM_OMITTED`;
- `UNSUPPORTED_CLAIM_ADDED`;
- `DEFINITION_OR_CONCEPT_DRIFT`;
- `EVIDENCE_ATTRIBUTION_DRIFT`;
- `ARGUMENT_LOGIC_DRIFT`;
- `CONCLUSION_DRIFT`;
- `AUTHOR_VOICE_DRIFT_FOR_AUDIO`;
- `UNAPPROVED_MATERIAL_RESTRUCTURE`.

A substantially rewritten audio script can be valid. Semantic drift cannot be silently accepted.

## 6. Literary Master, AudioScript and Audio Studio boundary

BOOK OS and Audio Studio remain separate products.

### 6.1 Workflow A handoff

For `AUDIO_FIRST` and the audio side of `DUAL_TEXT_AUDIO`:

`BOOK OS Literary Master → immutable Production Handoff → Audio Studio → Audio Edition Master`

The Literary Master has already passed required literary listenability gates before handoff.

### 6.2 Workflow B handoff

For an audio edition derived from an existing text book:

`BOOK OS Text Literary Master (immutable source) → BOOK OS AudioScript (derived + human-approved) → immutable Production Handoff → Audio Studio → Audio Edition Master`

Audio Studio still owns:

- narrator/TTS voice execution;
- SSML and provider-specific normalization;
- pronunciation rendering;
- segmenting and synthesis;
- mastering;
- audio QC;
- Audio Edition Master.

BOOK OS owns literary/editorial listenability and semantic/source fidelity of the AudioScript.

BOOK OS handoff should add, when available:

- workflow identity;
- `delivery_profile` for Workflow A or `adaptation_mode` for Workflow B;
- exact source revision identity for Workflow B;
- transformation/coverage map identity for Workflow B;
- series identity/order;
- ordered section/chapter identities;
- pronunciation/name ledger;
- approved audio dispositions for visual dependencies;
- intended spoken chapter/section titles;
- optional author-approved narration notes that do not mutate Literary Master or approved AudioScript.

## 7. Series — first-class object above books

A series is not a string copied into metadata. BOOK OS introduces a stable `SeriesProject` / `SeriesContract` that can own multiple `BookProject` objects.

Minimum series fields:

- `series_id`;
- working/published series name;
- `series_type`: `ORDERED | UNORDERED`;
- intended series audience;
- series-level promise / territory;
- shared exclusions and boundaries;
- shared author voice / Style Profile references;
- canonical terminology and recurring concepts;
- cross-volume progression or coverage map;
- volume membership/order;
- shared example/case-study registry;
- series-level evidence/provenance references where reusable;
- shared production metadata relevant to handoff;
- authority status and revision history.

### 7.1 Ordered series

Use when books form a progression and reading/listening order matters.

BOOK OS must know:

- what earlier volumes may be assumed;
- what each volume newly contributes;
- what concepts are introduced where;
- what cannot be prematurely repeated or spoiled;
- how each book closes its own promise while advancing the series.

### 7.2 Unordered series

Use when books share a recognizable territory, audience, voice or framework but can be consumed independently.

Each volume must still have a distinct promise and enough self-contained context. BOOK OS must prevent the series from becoming the same book with a new subtitle.

## 8. Series Book Contract extension

Each book in a series gains a series membership contract containing at minimum:

- `series_id`;
- `volume_number` or display order when ordered;
- role of this volume inside the series;
- unique promise / unique territory;
- inherited concepts/terms;
- concepts introduced here;
- permitted recap;
- forbidden duplication from previous volumes;
- cross-volume dependencies;
- bridge/continuity obligations;
- standalone-completeness requirement;
- metadata identity constraints.

The book-level Book Contract remains separately approvable and versioned.

## 9. Series Memory

BOOK OS extends Book Memory to cross-book memory for books in the same series.

Series Memory must support detection of:

- reused examples/case studies;
- repeated thesis or chapter function;
- contradictory definitions;
- changed terminology;
- duplicated openings/conclusions;
- recycled AI phrasing;
- promises made in one volume and forgotten later;
- unjustified re-explanation of concepts;
- missing necessary recap in an ordered series.

Cross-volume retrieval must use stable book/chapter/revision identities and must not depend on chat history.

An AudioScript derived under Workflow B belongs to its source book and does not become a new series volume merely because its wording differs substantially.

## 10. SeriesBench

Add series-level diagnostics. Minimum dimensions/findings:

- volume promise separation;
- cross-volume novelty;
- concept ownership and progression;
- example reuse;
- terminology consistency;
- contradiction across volumes;
- recap necessity vs redundancy;
- structural/template repetition;
- series voice continuity;
- ordered-series dependency integrity;
- standalone completeness where required.

No book receives series-level release readiness merely because its individual BookBench is green.

## 11. User interface

### 11.1 Top-level action

BOOK OS must not start with one mixed audio selector. The user first chooses what they are doing:

**Что вы хотите сделать?**

- `Создать книгу с нуля`;
- `Подготовить аудиоверсию готовой книги`.

These open different workflows and different state machines.

### 11.2 Workflow A — new-book panel

Only after `Создать книгу с нуля` show:

**Как будет использоваться книга?**

- `Текст` → `TEXT_FIRST`;
- `Аудио — основной формат` → `AUDIO_FIRST`;
- `Текст + аудио` → `DUAL_TEXT_AUDIO`.

Then show the independent series choice:

**Это отдельная книга или часть серии?**

- `Отдельная книга`;
- `Книга в серии`.

If `Книга в серии`:

- choose existing series or create new;
- series name;
- `По порядку` / `Можно читать независимо`;
- volume/order when applicable.

### 11.3 Workflow B — existing-text audio panel

Only after `Подготовить аудиоверсию готовой книги`:

1. select/import the source text book or exact approved source revision;
2. show source identity and confirm it will remain unchanged;
3. ask **«Как подготовить текст для аудиоверсии?»**;
4. show exactly two choices:

- `По оригиналу, с адаптацией для аудио` — текст остаётся близким к оригиналу, но BOOK OS делает необходимые изменения для хорошего прослушивания;
- `Сохранить суть и концепцию, переписать для аудио` — текст может заметно или сильно отличаться от печатной версии; BOOK OS пишет более живой аудиотекст, но сохраняет смысл, концепцию, факты, доказательства и выводы оригинала.

The UI must not expose `TEXT_FIRST`, `AUDIO_FIRST` or `DUAL_TEXT_AUDIO` inside Workflow B.

The UI must not expose `SOURCE_FAITHFUL` or `LISTENING_ADAPTATION` inside Workflow A.

Do not expose internal enum names to the user.

### 11.4 Project workspace

Show compact identity badges appropriate to the workflow, for example:

- `Книга с нуля · Текст`;
- `Книга с нуля · Аудио — основной формат`;
- `Книга с нуля · Текст + аудио`;
- `Аудиоверсия готовой книги · По оригиналу`;
- `Аудиоверсия готовой книги · Переписано для аудио`;
- `Серия · книга 2`.

For Workflow B show source revision identity and an explicit source-vs-audio transformation review before approval.

For series books, provide a series workspace showing volume map, series contract, shared memory and cross-volume diagnostics.

### 11.5 Migration safety

Existing books default to `TEXT_FIRST` and standalone status unless explicitly changed by the human.

Creating a Workflow B AudioScript from an existing book does not mutate the source book's delivery profile and does not convert it to `AUDIO_FIRST` or `DUAL_TEXT_AUDIO`.

BOOK OS must not silently infer a series or audio-first profile from title text.

## 12. Planning / generation propagation

Every generation task that can affect prose or structure must receive resolved workflow context through structured fields, not an untracked prompt fragment.

### Workflow A minimum context

- workflow = book from zero;
- delivery profile;
- applicable listenability rules;
- series contract/membership;
- cross-volume owned/reserved concepts;
- cross-volume duplication findings;
- approved Style Profile;
- anti-junk rules.

### Workflow B minimum context

- workflow = existing text to audio;
- exact source revision identity/hash;
- selected adaptation mode;
- source Book Contract/thesis/concept/definitions where available;
- source evidence/provenance bindings;
- transformation/coverage state;
- applicable listenability rules;
- semantic/source fidelity rules;
- approved Style Profile/author voice;
- anti-junk rules;
- series context when applicable.

Model output remains `DRAFT/PROPOSED` until human acceptance according to Authority Protocol.

## 13. Release gates

### Workflow A — `TEXT_FIRST`

Normal BOOK OS literary/editorial/BookBench release gates.

### Workflow A — `AUDIO_FIRST`

Normal gates + mandatory `LISTENABILITY` pass + zero unresolved blocked visual dependencies.

### Workflow A — `DUAL_TEXT_AUDIO`

Normal gates + mandatory `LISTENABILITY` pass + explicit audio disposition for every material visual dependency.

### Workflow B — `SOURCE_FAITHFUL`

Normal AudioScript literary/anti-junk gates + mandatory `LISTENABILITY` + mandatory `SOURCE_FIDELITY` + reviewed transformation map + zero unapproved material omissions/additions.

### Workflow B — `LISTENING_ADAPTATION`

Normal AudioScript literary/anti-junk gates + mandatory `LISTENABILITY` + mandatory `SEMANTIC_FIDELITY` + reviewed transformation map + zero unapproved material additions/omissions/major restructures.

### Series book

Individual book/audio-script gates + applicable `SeriesBench` gates.

## 14. Platform-facing metadata implications

BOOK OS should preserve exact stable series name and order as publishing metadata authority because retailers depend on consistent series metadata. Publishing adapters remain downstream and may vary by platform.

The internal model supports both ordered and unordered series; retailer-specific limitations do not redefine BOOK OS ontology.

A derived Workflow B AudioScript is an edition artifact of the source book unless the human explicitly creates a different publishing identity. Surface-level rewrite does not silently create a new book identity.

## 15. Non-goals

This capability does not:

- merge BOOK OS with Audio Studio;
- move TTS/mastering into BOOK OS;
- mix Workflow A and Workflow B into one mode selector;
- mutate a source Literary Master while preparing an audio edition;
- claim that every sentence must be short;
- ban all lists, numbers, tables or citations;
- force all books into a series;
- auto-approve series continuity or audio readiness;
- auto-approve semantic drift in a heavily rewritten audio script;
- treat a heavily rewritten AudioScript as a new book unless the human explicitly decides that.

## 16. Acceptance target for implementation

Implementation is complete only when all of the following exist:

1. product entry exposes two separate top-level actions: `Создать книгу с нуля` and `Подготовить аудиоверсию готовой книги`;
2. Workflow A alone exposes `Текст / Аудио — основной формат / Текст + аудио`;
3. Workflow B alone exposes `По оригиналу, с адаптацией для аудио / Сохранить суть и концепцию, переписать для аудио`;
4. canonical storage persists workflow identity separately from delivery profile/adaptation mode;
5. Workflow B stores immutable exact source revision identity/hash and never mutates source Literary Master;
6. Workflow B creates a separate versioned AudioScript with authority state;
7. Workflow B maintains a reviewable transformation/coverage map;
8. `SOURCE_FAITHFUL` has deterministic/source-assisted drift tests and source-fidelity gates;
9. `LISTENING_ADAPTATION` allows substantial prose differences but has semantic-fidelity gates for promise/thesis/claims/evidence/definitions/logic/conclusions/voice;
10. material omissions, additions and major restructures cannot be silently approved;
11. Planner/Writer/Editor receive structured workflow-specific context;
12. BookBench/AudioScript evaluation exposes `LISTENABILITY` plus the correct fidelity dimension with exact evidence;
13. existing books migrate safely and Workflow B does not mutate their delivery profile;
14. series objects and membership are first-class and versioned;
15. Series Memory can inspect prior volumes without chat history;
16. SeriesBench detects material cross-volume repetition/contradiction;
17. Literary Master/AudioScript release applies the correct workflow/profile/adaptation/series gates;
18. Audio handoff includes required workflow/profile-or-adaptation/source/pronunciation/visual-disposition metadata without moving TTS logic upstream;
19. automated tests cover TEXT_FIRST, AUDIO_FIRST, DUAL_TEXT_AUDIO, SOURCE_FAITHFUL, LISTENING_ADAPTATION, ordered series and unordered series;
20. tests prove a strongly rewritten `LISTENING_ADAPTATION` can pass when meaning/concept/evidence remain intact and fail when semantic drift is introduced;
21. no paid/provider calls are made by CI tests.
