# Owner decision — Audio-native authoring and series are first-class BOOK OS capabilities

**Date:** 2026-09-02
**Status:** ACCEPTED

## Decision

BOOK OS must support two independent project choices from the new-book panel:

1. delivery profile: `TEXT_FIRST | AUDIO_FIRST | DUAL_TEXT_AUDIO`;
2. publication structure: standalone book or book in a first-class series.

`AUDIO_FIRST` means the book is planned, drafted and evaluated for listening from the beginning. It is not an ordinary text manuscript later passed to TTS.

Series are not title metadata only. BOOK OS must model series-level authority, continuity, cross-volume memory and cross-volume quality gates. Both ordered and independently consumable/unordered series are supported.

## Boundary preserved

The accepted BOOK OS ↔ Audio Studio boundary remains in force:

`BOOK OS Literary Master → immutable Production Handoff → Audio Studio → Audio Edition Master`

BOOK OS owns literary/editorial listenability. Audio Studio owns narrator/TTS execution, SSML, pronunciation rendering, mastering and audio QC.

## Required product consequences

- New-book UI exposes simple Russian choices for delivery profile and series membership.
- Delivery/series context is persisted and propagated into Planner/Writer/Editor/BookBench as structured state.
- `AUDIO_FIRST` and `DUAL_TEXT_AUDIO` gain mandatory listenability gates.
- A first-class series object stores series contract, ordered/unordered type, volume membership, shared style/terminology, progression and cross-volume memory.
- Series books receive cross-volume novelty/consistency/repetition checks in addition to book-level BookBench.
- Existing books migrate safely to `TEXT_FIRST` + standalone unless a human explicitly changes them.
- TTS-specific transformations remain downstream and never silently mutate Literary Master.

Detailed design authority: `docs/AUDIO_NATIVE_AND_SERIES_v0.1.md`.
