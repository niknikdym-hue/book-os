# Owner decision — BOOK OS has two separate audio-related workflows

**Date:** 2026-09-02
**Amended:** 2026-09-03
**Status:** ACCEPTED

## Decision

BOOK OS must keep two fundamentally different workflows separate in product UI, canonical state, prompts, quality gates and production handoff.

### Workflow A — create a book from zero

The user starts a new book project. Only here the user chooses the intended delivery profile:

- `TEXT_FIRST` — text is the primary format;
- `AUDIO_FIRST` — the book is planned and written from the beginning for listening;
- `DUAL_TEXT_AUDIO` — the book is created from the beginning to work professionally in both text and audio.

This workflow owns Book Contract, Architecture, Chapter Contracts, Writer, editorial gates and Literary Master creation from zero.

### Workflow B — prepare an audio edition from an existing text book

This is a separate entry point. It begins from an existing approved/imported text Literary Master or equivalent accepted source manuscript. The original text remains immutable.

BOOK OS creates a separate versioned `AudioScript` bound to the exact source revision. The user then chooses exactly one of two audio adaptation modes:

1. `По оригиналу, с адаптацией для аудио` → `SOURCE_FAITHFUL`.
   The audio script follows the original book closely in content, order, wording and structure, but may make the changes genuinely required for listening: remove page-dependent references, verbalize visual material, reshape overloaded sentences/lists, improve attribution/orientation, and make other bounded listenability adaptations.

2. `Сохранить суть и концепцию, переписать для аудио` → `LISTENING_ADAPTATION`.
   The source book remains semantic authority, but the audio script may differ substantially in wording, rhythm, transitions, paragraphing, chapter openings/endings and local structure. It may be written as a more vivid, natural, genuinely spoken work rather than as a text edition read aloud.

For `LISTENING_ADAPTATION`, BOOK OS must preserve the source book's core promise, thesis, concept, approved definitions, material factual claims, evidence/provenance, argumentative logic, conclusions and author identity unless the human explicitly approves a material change through the Authority Protocol.

The model may not silently invent factual claims, replace evidence, reverse or weaken the thesis, omit a material claim, or alter the book's concept. Material additions, omissions or conceptual/structural departures must be surfaced to the human before approval.

The two workflows must **never** be collapsed into one mode selector. `TEXT_FIRST | AUDIO_FIRST | DUAL_TEXT_AUDIO` belongs only to Workflow A. `SOURCE_FAITHFUL | LISTENING_ADAPTATION` belongs only to Workflow B.

Series membership is a separate book/series dimension and does not merge these workflows.

## Canonical derived-audio model

Every audio script produced from an existing text must store at minimum:

- exact source book/project identity;
- exact source Literary Master/revision identity and hash;
- selected adaptation mode;
- derived audio-script revision identity;
- transformation/coverage map from source to audio script;
- provenance/evidence bindings for material factual claims;
- authority status and revision history;
- human approval identity/time when approved.

The transformation map must make material `PRESERVED | REWRITTEN | MOVED | OMITTED | ADDED` changes reviewable. `OMITTED` and material `ADDED` content require explicit human acceptance.

AI-produced audio text remains `DRAFT/PROPOSED`; AI cannot approve it.

## Audio-version text output contract — NON-NEGOTIABLE

**UTF-8 TXT is the required output format of the text of an audio version.** It is not the required source/import format of an existing text book.

This rule applies to every BOOK OS path that produces text intended for recording or synthesis:

- a book created from zero as `AUDIO_FIRST`;
- the audio side of a book created from zero as `DUAL_TEXT_AUDIO`;
- a recording script derived from an existing text book in `SOURCE_FAITHFUL` mode;
- a recording script derived from an existing text book in `LISTENING_ADAPTATION` mode.

Before handoff to Audio Studio, the approved recording text must be exportable as a clean `.txt` file encoded in UTF-8 and intended to be read/recorded as the audio version.

The readable UTF-8 TXT must not be polluted with machine metadata. Hashes, provenance, adaptation mode, transformation/coverage map, authority data, pronunciation metadata and production-handoff manifest remain separate structured metadata/artifacts.

The source/import format of an existing text book is a separate concern and may be expanded independently; it does not change the required UTF-8 TXT output contract for the resulting audio-version text.

## Quality gates for Workflow B

Both modes must pass normal anti-junk/author-voice protections plus audio `LISTENABILITY` checks.

`SOURCE_FAITHFUL` additionally requires a source-fidelity gate that detects unjustified drift from the original.

`LISTENING_ADAPTATION` additionally requires a semantic-fidelity gate that detects at minimum:

- loss of core promise/thesis;
- omitted material claims;
- unsupported added claims;
- changed definitions/concepts;
- evidence or attribution drift;
- conclusion drift;
- materially changed argumentative logic;
- author-voice drift beyond the approved audio style.

A substantially rewritten audio script can be valid; semantic drift cannot be silently accepted.

## Boundary preserved

BOOK OS and Audio Studio remain separate products.

For a book authored for audio from zero:

`BOOK OS Literary Master → clean UTF-8 TXT recording text + immutable Production Handoff → Audio Studio → Audio Edition Master`

For an audio edition derived from an existing text book:

`BOOK OS Text Literary Master (immutable source) → BOOK OS AudioScript (derived + human-approved) → clean UTF-8 TXT recording text + immutable Production Handoff → Audio Studio → Audio Edition Master`

BOOK OS owns literary/editorial quality, listenability and semantic fidelity of the audio-version text. Audio Studio owns narrator/TTS execution, SSML, pronunciation rendering, synthesis, mastering and audio QC.

## Required UI consequence

The product must expose two separate top-level actions, not one combined audio selector:

- `Создать книгу с нуля`;
- `Подготовить текст для аудиозаписи готовой книги`.

Only `Создать книгу с нуля` exposes `Текст / Аудио — основной формат / Текст + аудио`.

Only `Подготовить текст для аудиозаписи готовой книги` exposes:

- `По оригиналу, с адаптацией для аудио`;
- `Сохранить суть и концепцию, переписать для аудио`.

The second option must explain in plain Russian that the audio text may differ substantially and be written specifically for listening while the meaning and concept of the original remain authoritative.

Whenever either workflow produces an audio-version text, the user-facing export must provide the clean UTF-8 TXT recording file.

## Series

Series remain first-class authority-bearing objects with ordered/unordered modes, cross-volume memory and diagnostics. Series are orthogonal to the two workflows above.

## Migration and safety

Existing book projects remain `TEXT_FIRST` + standalone unless the human explicitly changes their project metadata. Creating an audio edition from such a book does not mutate its delivery profile and does not convert the source Literary Master into `AUDIO_FIRST` or `DUAL_TEXT_AUDIO`.

No TTS-specific transformation may silently mutate a Literary Master or an approved AudioScript.

Detailed design authority: `docs/AUDIO_NATIVE_AND_SERIES_v0.1.md`; this decision amendment is binding where it defines the universal UTF-8 TXT audio-version text output contract.
