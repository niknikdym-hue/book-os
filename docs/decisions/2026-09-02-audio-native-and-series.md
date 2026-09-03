# Owner decision — Audio-native authoring, existing-text audio adaptation and series are first-class BOOK OS capabilities

**Date:** 2026-09-02
**Amended:** 2026-09-03
**Status:** ACCEPTED

## Decision

BOOK OS must support independent product/editorial choices at the appropriate stage:

1. delivery profile for a book being created: `TEXT_FIRST | AUDIO_FIRST | DUAL_TEXT_AUDIO`;
2. publication structure: standalone book or book in a first-class series;
3. when an audio edition is prepared from an existing approved text, audio adaptation mode: `SOURCE_FAITHFUL | LISTENING_ADAPTATION`.

`AUDIO_FIRST` means the book is planned, drafted and evaluated for listening from the beginning. It is not an ordinary text manuscript later passed to TTS.

Existing-text audio adaptation is a different capability. A finished text book remains an immutable source Literary Master. BOOK OS creates a separate versioned `AudioScript` bound to the exact source revision and the human chooses one of two modes:

- `По тексту оригинала` → `SOURCE_FAITHFUL`: preserve wording and structure as closely as practical; make only bounded changes required for listenability, spoken rendering of visual/page-dependent material, attribution, pronunciation risk and similar audio blockers.
- `Адаптировать для прослушивания` → `LISTENING_ADAPTATION`: preserve the book's meaning, thesis, concept, factual claims, evidence/provenance, conclusions and approved author voice, while allowing sentences, paragraphs, transitions and local structure to be rewritten into more natural, vivid spoken prose.

The second mode is not permission to invent new facts, change the thesis, remove material claims, alter evidence, or silently reshape the book's concept. Material conceptual or structural change requires explicit human approval through the normal Authority Protocol.

Series are not title metadata only. BOOK OS must model series-level authority, continuity, cross-volume memory and cross-volume quality gates. Both ordered and independently consumable/unordered series are supported.

## Boundary preserved

The accepted BOOK OS ↔ Audio Studio boundary remains in force.

For an audio-native Literary Master:

`BOOK OS Literary Master → immutable Production Handoff → Audio Studio → Audio Edition Master`

For an audio edition derived from an existing text Literary Master:

`BOOK OS Text Literary Master (immutable source) → BOOK OS AudioScript (derived + human-approved) → immutable Production Handoff → Audio Studio → Audio Edition Master`

BOOK OS owns literary/editorial listenability and semantic fidelity of the audio script. Audio Studio owns narrator/TTS execution, SSML, pronunciation rendering, mastering and audio QC.

## Required product consequences

- New-book UI exposes simple Russian choices for delivery profile and series membership.
- Existing-text audio preparation exposes exactly two simple Russian choices: `По тексту оригинала` and `Адаптировать для прослушивания`.
- The original text Literary Master is never silently mutated by audio preparation.
- Every derived `AudioScript` stores exact source revision identity, adaptation mode, provenance and authority status.
- AI-produced audio-script text remains DRAFT/PROPOSED until human approval; AI cannot approve it.
- `SOURCE_FAITHFUL` must detect unjustified wording/structure drift beyond bounded audio necessities.
- `LISTENING_ADAPTATION` must pass both listenability and semantic-fidelity gates: no lost core claims, unsupported added claims, evidence/attribution drift or concept/definition drift.
- Delivery/adaptation/series context is persisted and propagated into Planner/Writer/Editor/BookBench as structured state.
- `AUDIO_FIRST` and `DUAL_TEXT_AUDIO` gain mandatory listenability gates.
- A first-class series object stores series contract, ordered/unordered type, volume membership, shared style/terminology, progression and cross-volume memory.
- Series books receive cross-volume novelty/consistency/repetition checks in addition to book-level BookBench.
- Existing books migrate safely to `TEXT_FIRST` + standalone unless a human explicitly changes them.
- TTS-specific transformations remain downstream and never silently mutate Literary Master or approved AudioScript.

Detailed design authority remains `docs/AUDIO_NATIVE_AND_SERIES_v0.1.md`; this 2026-09-03 amendment is binding where it adds the existing-text audio-adaptation capability and will be folded into implementation acceptance before merge.
