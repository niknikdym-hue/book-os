# BOOK OS — AUDIO-NATIVE AUTHORING & SERIES v0.1

**Status:** ACCEPTED PRODUCT / EDITORIAL DESIGN
**Version:** 0.1.0
**Date:** 2026-09-02

## 1. Purpose

BOOK OS must support two independent choices at book creation time:

1. how the book is primarily consumed;
2. whether the book is standalone or belongs to a series.

These are not publishing metadata decorations. They change planning, drafting, editorial diagnostics, BookBench, release readiness and production handoff.

The user-facing rule remains: **simple outside, smart inside**.

## 2. Delivery profile — first-class book property

Each `BookProject` has one `delivery_profile`:

- `TEXT_FIRST` — written primarily for visual reading;
- `AUDIO_FIRST` — written from the first planning stage for listening;
- `DUAL_TEXT_AUDIO` — written so that the same intellectual work is professionally usable in both text and audio editions.

This is selected in the new-book panel and is persisted as book authority. It is not inferred later from export choice.

### 2.1 What `AUDIO_FIRST` means

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

### 2.2 `DUAL_TEXT_AUDIO`

`DUAL_TEXT_AUDIO` is not a compromise mode with weak text and weak audio. The manuscript must pass both reading and listening constraints.

When a concept genuinely needs a visual object (table, chart, formula, diagram, URL-heavy reference), BOOK OS must explicitly choose a representation strategy instead of silently assuming a page:

- rewrite the idea as self-sufficient spoken prose;
- retain the visual for the text edition and add an approved audio explanation/handoff note;
- move detail into a companion artifact while keeping the spoken argument complete;
- reject the visual dependency if it is unnecessary.

The core argument must remain understandable without forcing the listener to look at a page.

## 3. Audio-native editorial rules

These rules guide generation and evaluation. They are quality constraints, not blind numeric bans.

### 3.1 One-pass comprehensibility

A listener should usually understand a sentence on first hearing.

BOOK OS should detect or avoid:

- overloaded nested syntax;
- ambiguous pronoun/reference chains;
- long parenthetical detours;
- sentences whose key subject arrives too late to remain easy to track;
- dense sequences of dates, percentages, names or qualifications without interpretation.

Complex thought is allowed. Unnecessary decoding cost is not.

### 3.2 Audible structure and orientation

The listener cannot visually scan headings or page position. Therefore:

- chapter and section openings should orient the listener naturally;
- transitions must express the intellectual move, not visual navigation;
- avoid page-dependent phrases such as “as shown above/below”, “see the table”, “in the diagram on the next page” unless an audio rendering strategy exists;
- structural signposting must not become repetitive presenter language.

### 3.3 Cognitive-load management

Long enumerations are difficult to hold in working memory.

BOOK OS should:

- group related items into meaningful chunks;
- prefer interpreted sequences over raw lists;
- flag multi-level enumerations and long item chains;
- allow deliberate repetition when it restores orientation, but distinguish it from redundant restatement.

### 3.4 Numbers, dates and measurements

Audio prose must be pronounceable and cognitively usable.

BOOK OS should flag:

- number strings that are easy to mishear;
- clusters of percentages without interpretation;
- tables read row-by-row;
- unexplained abbreviations and units;
- precision that adds visual density but no argumentative value.

Numbers should be integrated into the meaning of the sentence, not merely transferred from a spreadsheet.

### 3.5 Names, terms, acronyms and pronunciation

BOOK OS maintains literary identity; Audio Studio owns final pronunciation execution.

For audio-oriented books BOOK OS should maintain an exportable pronunciation/name ledger containing, where relevant:

- canonical spelling;
- first-use expansion for acronyms;
- language/origin note;
- optional pronunciation guidance supplied or approved by the human;
- consistency requirements across the book and series.

No pronunciation markup is inserted into Literary Master text merely for TTS.

### 3.6 Quotations and attribution

Long quotations must not leave the listener unsure who is speaking. Attribution should be placed early enough for auditory comprehension. Source detail may live in notes/companion material, but the spoken argument must remain understandable.

### 3.7 Footnotes, citations, URLs and companion material

Audio-first text must not depend on footnotes being visually available.

BOOK OS should:

- keep necessary attribution in fluent prose;
- move bibliographic detail to end matter/companion material when appropriate;
- flag raw URLs and reference strings in main narration;
- ensure removing/skipping the visual note does not break the central argument.

### 3.8 Tables, charts, formulas and figures

Every visual dependency receives an explicit audio disposition:

- `SPOKEN_REWRITE`;
- `AUDIO_EXPLANATION`;
- `COMPANION_ARTIFACT`;
- `OMIT_FROM_AUDIO` only when omission does not damage the argument;
- `BLOCKED` when no honest audio representation exists yet.

An `AUDIO_FIRST` Literary Master cannot contain unresolved `BLOCKED` visual dependencies.

### 3.9 Rhythm, breath and narration

BOOK OS should optimize prose for spoken rhythm without flattening author voice:

- varied sentence length;
- natural breath groups;
- paragraph-level rhythmic contrast;
- controlled emphasis;
- avoidance of monotone same-shaped sentences;
- avoidance of fake rhetorical drama and AI-style stage language.

Punctuation remains literary punctuation. TTS-specific timing and SSML remain downstream in Audio Studio.

### 3.10 Chapter openings, endings and continuity

Audio-first architecture should favor chapters that can be entered without page scanning and exited with a clear intellectual landing.

BOOK OS may use brief reorientation when necessary, but must avoid mechanical “previously / now we will / in this chapter” boilerplate unless genuinely useful.

### 3.11 Estimated listening duration

BOOK OS may show a non-authoritative duration estimate from word count for planning. It must be labeled as an estimate because narrator, language, pacing, quotations and pauses change final duration.

## 4. Audio readiness in BookBench

Add a first-class evaluation dimension: `LISTENABILITY`.

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

For `AUDIO_FIRST`, unresolved high-severity listenability findings block Literary Master release.

For `DUAL_TEXT_AUDIO`, both normal literary/editorial gates and listenability gates apply.

## 5. Literary Master and Audio Studio boundary

Existing boundary remains valid:

`BOOK OS Literary Master → immutable Production Handoff → Audio Studio → Audio Edition Master`

The new rule is that an `AUDIO_FIRST` or `DUAL_TEXT_AUDIO` Literary Master has already passed literary listenability requirements before handoff.

Audio Studio still owns:

- narrator / TTS voice execution;
- SSML and provider-specific normalization;
- pronunciation rendering;
- segmenting and synthesis;
- mastering;
- audio QC;
- Audio Edition Master.

BOOK OS handoff should add, when available:

- `delivery_profile`;
- series identity/order;
- ordered section/chapter identities;
- pronunciation/name ledger;
- approved audio dispositions for visual dependencies;
- intended spoken chapter/section titles;
- optional author-approved narration notes that do not mutate Literary Master.

## 6. Series — first-class object above books

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

### 6.1 Ordered series

Use when books form a progression and reading/listening order matters.

BOOK OS must know:

- what earlier volumes may be assumed;
- what each volume newly contributes;
- what concepts are introduced where;
- what cannot be prematurely repeated or spoiled;
- how each book closes its own promise while advancing the series.

### 6.2 Unordered series

Use when books share a recognizable territory, audience, voice or framework but can be consumed independently.

Each volume must still have a distinct promise and enough self-contained context. BOOK OS must prevent the series from becoming the same book with a new subtitle.

## 7. Series Book Contract extension

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

## 8. Series Memory

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

## 9. SeriesBench

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

## 10. User interface

### 10.1 New-book panel

Add two simple choices.

**Как будет использоваться книга?**

- `Текст` → `TEXT_FIRST`
- `Аудио — основной формат` → `AUDIO_FIRST`
- `Текст + аудио` → `DUAL_TEXT_AUDIO`

**Это отдельная книга или часть серии?**

- `Отдельная книга`
- `Книга в серии`

If `Книга в серии`:

- choose existing series or create new;
- series name;
- `По порядку` / `Можно читать независимо`;
- volume/order when applicable.

Do not expose internal enum names to the user.

### 10.2 Project workspace

Show compact identity badges such as:

- `Аудио — основной формат`;
- `Текст + аудио`;
- `Серия · книга 2`.

For series books, provide a series workspace showing volume map, series contract, shared memory and cross-volume diagnostics.

### 10.3 Migration safety

Existing books default to `TEXT_FIRST` and standalone status unless explicitly changed by the human. BOOK OS must not silently infer a series or audio-first profile from title text.

## 11. Planning / generation propagation

Every generation task that can affect prose or structure must receive resolved delivery and series context through structured fields, not an untracked prompt fragment.

Minimum context passed to Planner/Writer/Editor where relevant:

- delivery profile;
- applicable listenability rules;
- series contract/membership;
- cross-volume owned/reserved concepts;
- cross-volume duplication findings;
- approved Style Profile;
- anti-junk rules.

Model output remains DRAFT/PROPOSED until human acceptance according to Authority Protocol.

## 12. Release gates

### `TEXT_FIRST`
Normal BOOK OS literary/editorial/BookBench release gates.

### `AUDIO_FIRST`
Normal gates + mandatory `LISTENABILITY` pass + zero unresolved blocked visual dependencies.

### `DUAL_TEXT_AUDIO`
Normal gates + mandatory `LISTENABILITY` pass + explicit audio disposition for every material visual dependency.

### Series book
Individual book gates + applicable `SeriesBench` gates.

## 13. Platform-facing metadata implications

BOOK OS should preserve exact stable series name and order as publishing metadata authority because retailers depend on consistent series metadata. Publishing adapters remain downstream and may vary by platform.

The internal model supports both ordered and unordered series; retailer-specific limitations do not redefine BOOK OS ontology.

## 14. Non-goals

This capability does not:

- merge BOOK OS with Audio Studio;
- move TTS/mastering into BOOK OS;
- claim that every sentence must be short;
- ban all lists, numbers, tables or citations;
- force all books into a series;
- auto-approve series continuity or audio readiness;
- silently rewrite an approved Literary Master.

## 15. Acceptance target for implementation

Implementation is complete only when all of the following exist:

1. new-book panel exposes delivery profile and standalone/series choice;
2. canonical storage persists these choices;
3. existing books migrate safely;
4. Planner/Writer receive structured delivery and series context;
5. BookBench exposes listenability findings with exact evidence;
6. series objects and membership are first-class and versioned;
7. Series Memory can inspect prior volumes without chat history;
8. SeriesBench detects material cross-volume repetition/contradiction;
9. Literary Master release applies the correct profile/series gates;
10. Audio handoff includes required profile/series/pronunciation/visual-disposition metadata without moving TTS logic upstream;
11. automated tests cover TEXT_FIRST, AUDIO_FIRST, DUAL_TEXT_AUDIO, ordered series and unordered series;
12. no paid/provider calls are made by CI tests.
