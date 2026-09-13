# BOOK OS — TASK 021 AUDIO EDITORIAL ADDENDUM

**Status:** IMPLEMENTED_AWAITING_CENTRAL_BRAIN_ACCEPTANCE

**Date:** 2026-09-13

**Parent task:** `TASK_021_AUTO_BOOK_COMPLETE_CYCLE.md`

## Purpose

Audio DOCX/TXT files are not evidence that an audio edition is ready. A text-first manuscript may
produce audio outputs only through a separate, versioned AudioScript workflow. BOOK OS owns the
literary/editorial recording text; Audiobook Studio continues to own voice/TTS, SSML, pronunciation
rendering, synthesis, mastering and audio QC.

This addendum is governed by:

- `docs/AUDIO_NATIVE_AND_SERIES_v0.1.md`;
- `docs/decisions/2026-09-02-audio-native-and-series.md`;
- `docs/AUDIO_HANDOFF_v0.1.md`;
- `docs/BOOK_OS_AUTHORITY.md`.

## Required workflows

The product keeps two actions separate:

1. **Create a book from zero** with `TEXT_FIRST | AUDIO_FIRST | DUAL_TEXT_AUDIO`.
2. **Prepare recording text from an existing book** with
   `SOURCE_FAITHFUL | LISTENING_ADAPTATION`.

`AUDIO_FIRST` and `DUAL_TEXT_AUDIO` propagate listenability constraints into the Book Contract,
architecture, chapter contracts, Writer and final edit. An approved audio-native Literary Master is
not redundantly rewritten merely to create another object. A text-first or imported book remains an
immutable source and receives a separate derived AudioScript.

Choosing only the pronunciation dictionary must not trigger a paid full-book rewrite.

## AudioScript authority

Every derived AudioScript stores:

- its own stable ID, version, status and content hash;
- exact source kind, identity and hash;
- adaptation mode;
- ordered recording sections and visual dispositions;
- `PRESERVED | REWRITTEN | MOVED | OMITTED | ADDED` transformation/coverage entries;
- model/prompt/run/usage provenance;
- exact source/script-bound quality checks;
- a separate pronunciation ledger;
- explicit HUMAN approval evidence.

AI output remains `PROPOSED`. It cannot write final `APPROVED`. Any blocking check prevents
approval. Every ATTENTION finding must be explicitly dispositioned by the human. A changed source
makes a prior script stale without deleting its approved historical bytes or files.

## Recording-text rules

The audio editor must make the work understandable to a listener who cannot see the page and
usually hears a sentence once. It must preserve author voice, thesis, facts, evidence, qualifications
and conclusions while:

- reshaping overloaded written syntax and long lists;
- adding useful, non-mechanical audible orientation and transitions;
- removing page-dependent phrases;
- making attribution and foreign fragments clear;
- preparing numbers, dates, percentages, formulas, money and units for unambiguous speech;
- transforming footnotes, URLs and bibliographic notes without losing material attribution;
- placing audio explanations of tables/figures at the logically correct point;
- avoiding bureaucratic, template-like or artificial announcer prose.

The system must not add unsupported facts, silently omit material claims or call a mechanically
copied manuscript an audio adaptation.

## Visual material

Every material table, chart, diagram, infographic or illustration requires one existing-compatible
disposition:

- `SPOKEN_REWRITE` / `AUDIO_EXPLANATION`;
- `COMPANION_ARTIFACT` / `SUPPLEMENT_REFERENCE`;
- `OMIT_FROM_AUDIO` only when meaning is not lost;
- `BLOCKED` when an honest audio representation is not ready.

At least one material `BLOCKED` item prevents release. A non-empty `audio_equivalent` is not enough:
the check must compare it with the visual title/source facts and material numeric data.

## Outputs and handoff

The selectable existing outputs remain:

- `Аудиоредакция-для-чтения.docx`;
- `Аудиоредакция-для-Литрес.docx`;
- `Текст-для-озвучки.txt`;
- `Словарь-произношения.txt`.

Any audio-version release always includes clean UTF-8 `Текст-для-озвучки.txt`, even if the user
selected only an audio DOCX. DOCX and TXT are generated from the same exact approved AudioScript.
The release also creates an immutable Audiobook Studio production-handoff manifest.

The clean TXT contains no Markdown, SSML, hashes, internal IDs, model instructions, editor comments,
empty placeholders or technical metadata. It does not make unsupported claims about the
availability of another edition.

Audio LitRes output uses a separately versioned, checkable profile and never promises platform
acceptance.

## Pronunciation ledger

Discovery covers the whole AudioScript, including headings and visual explanations, and considers:

- people and geographic names;
- companies/products;
- abbreviations;
- foreign and professional terms;
- ambiguous stress;
- author-created or unique words.

Automatically discovered entries default to `NEEDS_REVIEW`. Empty pronunciation guidance is never
presented as verified. Recommendation origin and verification status remain in the separate ledger,
not in Literary Master or clean recording prose.

## Mandatory checks

Every exact source/script pair records:

- `LISTENABILITY`;
- `SOURCE_FIDELITY` or `SEMANTIC_FIDELITY`, as applicable;
- `AUTHOR_VOICE_FOR_AUDIO`;
- `VISUAL_DEPENDENCY_RESOLVED`;
- `NUMBER_AND_SYMBOL_PRONUNCIATION`;
- `ACRONYM_AND_TERM_PRONUNCIATION`;
- `PAGE_DEPENDENT_LANGUAGE`;
- `AUDIO_ORIENTATION`;
- `AUDIO_REDUNDANCY`;
- `CLEAN_RECORDING_TEXT`;
- `AUDIO_COMPLETENESS`.

Missing, stale or unexecuted checks do not become PASS. Deterministic checks prove technical
properties, not literary quality. Real listening, semantic/source fidelity and author voice retain
explicit human-review findings until a human reviews them.

## Execution and safety

Audio editing reuses Model Gateway, operation-aware routing, durable operations, request/cost
reservations and unknown-outcome protection. Provider calls are recorded before execution and a
transport interruption is not blindly retried. The strongest mode is not used unconditionally;
manual selections and exact provenance remain supported.

Normal CI uses deterministic adapters only. Provider/model calls in CI are zero and paid calls are
zero. This task does not authorize TTS, voice generation, deployment, app replacement, merge or a
real paid literary-quality trial.

## Technical acceptance

Tests must prove that:

1. AudioScript is separate from and cannot mutate Literary Master.
2. Audio exports cannot bypass the audio-editorial/human-approval gate.
3. AUDIO_FIRST avoids a redundant rewrite and delivery context reaches planning/writing/editing.
4. Exact source identity/hash and prior versions survive source/script changes.
5. Visual explanations are ordered and content-checked; a material BLOCKED item blocks release.
6. Clean UTF-8 TXT and both DOCX variants bind to one approved script hash.
7. The pronunciation dictionary is separate and honest about unverified entries.
8. SOURCE_FAITHFUL and LISTENING_ADAPTATION remain distinct.
9. Existing-source imports fail closed on incomplete extraction.
10. Pause/recovery, budget exhaustion and unknown paid outcomes remain safe.
11. No deterministic check fabricates human listening or literary-quality acceptance.
12. Regression fixtures cover a long list, numbers/percent/date, table, graph, footnote, foreign
    term, page-dependent reference, ambiguous stress and a material qualification.

Technical GREEN and human-confirmed real audio-text quality are reported separately.
