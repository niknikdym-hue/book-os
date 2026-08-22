# BOOK OS ↔ AUDIO STUDIO — PRODUCTION HANDOFF v0.1

**Status:** ACCEPTED ARCHITECTURAL BOUNDARY  
**Version:** 0.1.0  
**Date:** 2026-08-22

## 1. Decision

BOOK OS and Audio Studio remain separate products/repositories.

- BOOK OS owns literary/editorial authority and `LiteraryMaster`.
- Audio Studio owns audiobook production, TTS, pronunciation, mastering and audio QC.
- Neither product silently mutates the other's master.

## 2. Flow

`BOOK OS Literary Master → immutable Production Handoff → Audio Studio → Audio Edition Master`

## 3. Handoff manifest

Minimum future manifest:

- `handoff_version`;
- `book_id`;
- `literary_master_id/version`;
- Literary Master checksum;
- language;
- ordered chapter/section IDs and exact text revision hashes;
- approved display titles;
- author/book metadata needed by production;
- optional pronunciation/name notes that do not alter literary text;
- creation timestamp;
- source system/version.

The text payload may be transferred as a separate artifact referenced by checksum.

## 4. TTS-specific transformations

TTS punctuation, SSML, pronunciation markup, timing markers or audio-only textual normalization are derivatives owned by Audio Studio. They do not become Literary Master changes.

## 5. Correction discovered in Audio Studio

If audio production discovers a likely literary error:

`Audio finding → UpstreamCorrectionRequest → BOOK OS proposed patch → human acceptance → new Literary Master if accepted → new handoff`

Audio Studio never edits the BOOK OS master directly.

## 6. Shared infrastructure policy

Potential future shared commodity components:

- provider/API gateway primitives;
- secure secret storage;
- usage/cost accounting;
- durable local jobs;
- telemetry/logging;
- signed updater/release tooling;
- local runtime/process management.

Do **not** create a shared-core repository merely because two products exist. Extract a common component only after real duplicate implementation appears and its interface is stable.

Domain intelligence remains separate:

- BOOK OS: contracts, claims, editorial intelligence, BookBench, Literary Master.
- Audio Studio: voices, TTS, pronunciation, mastering, audio QC, Audio Master.
