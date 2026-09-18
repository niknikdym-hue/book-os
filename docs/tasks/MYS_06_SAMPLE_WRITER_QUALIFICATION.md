# MYS-06 — REPRESENTATIVE FICTION SAMPLE / STYLEPROFILE / WRITER QUALIFICATION

**Status:** IMPLEMENTATION / STACKED DRAFT  
**Date:** 2026-09-18  
**Repository:** `niknikdym-hue/book-os`  
**Base:** `codex/mys-05-writing-admission-20260918` @ `ed15242a1f2c165744b67114ad20a57830852f3e`  
**Branch:** `codex/mys-06-sample-writer-qualification-20260918`

## Purpose

Prevent MYSTERY OS from scaling a weak or generic prose mode across a full manuscript.

MYS-06 separates two questions:

1. **Is the final representative fiction sample strong enough to become the prose reference for mass drafting?**
2. **Did the selected Writer actually demonstrate that quality under the accepted StyleProfile and scene contracts?**

A strong final sample after material human/editor rewriting may answer YES to question 1 and NO to question 2.

This distinction is mandatory for cost/quality routing. Otherwise a cheap Writer can appear “qualified” because an expensive editor silently repaired every sample.

## Reuse boundary

MYS-06 reuses:

- existing shared BOOK OS `StyleProfile` infrastructure;
- exact MYS-05 WritingAdmission provenance;
- future MysteryBench/anti-cliche/benchmark evaluation refs;
- existing routing/provider identities.

MYS-06 does **not** create:

- a second StyleProfile system;
- a new provider gateway;
- a new model router;
- a prose generator;
- a benchmark model call.

## Representative sample functions

The deterministic policy always requires coverage of:

- `OPENING`;
- `INVESTIGATION_DIALOGUE`.

Project policy may additionally require:

- `TENSION_MYSTIC`;
- `QUIET_CHARACTER`.

One artifact may cover more than one function, but the policy also defines a minimum number of **distinct sample scenes**, preventing one scene from pretending to represent an entire novel.

The project explicitly sets `min_characters_per_sample`; the runtime does not invent a hidden universal scene length.

## Exact StyleProfile binding

A sample pack stores:

- StyleProfile ID;
- exact StyleProfile content hash;
- StyleProfile status.

Qualification fails when:

- StyleProfile is not APPROVED;
- the hash is invalid;
- current StyleProfile differs from the sample snapshot.

This makes prose-mode qualification stale when style authority changes.

## Exact story-authority binding

The sample pack stores exact fiction authority revision refs relevant to the sample.

Qualification compares them with the current required authority snapshot.

A StoryDefinition/NarrativeContract/CaseSolution change therefore cannot silently keep an old sample qualified.

## MYS-05 admission provenance

Every sample artifact stores:

- exact scene revision ref;
- exact WritingAdmission ID;
- Writer output hash;
- final sample text hash;
- final character count;
- representative function codes;
- post-Writer revision class;
- post-Writer revision evidence ref when cleanup/rewrite occurred.

The caller supplies verified MYS-05 `admission_id -> scene_revision_ref` mappings.

Qualification fails when:

- admission is unknown;
- admission refers to another scene revision;
- scene/admission identifiers are absent.

MYS-06 does not trust a prose sample merely because somebody says it was “generated under the system”.

## Sample evaluation evidence

Each sample must have exactly one bounded evaluation record.

Every sample requires coverage of:

- `NARRATIVE_CONTRACT`;
- `POV_INTEGRITY`;
- `VOICE_STYLE`;
- `SCENE_CAUSALITY`;
- `ANTI_CLICHE`;
- `FACTUAL_REALISM`.

Function-specific coverage:

- `INVESTIGATION_DIALOGUE` -> `DIALOGUE`;
- `TENSION_MYSTIC` -> `SUSPENSE_INFORMATION_CONTROL`.

If audio is selected, every sample also requires:

- `AUDIO_LISTENABILITY`.

Any sample evaluation with:

- `MAJOR_GAP`;
- `BLOCKING_GAP`;
- `NOT_EVALUATED`

blocks representative-sample qualification.

This is intentional: the representative sample is the point where material prose defects should be fixed **before** mass drafting.

## Independent evaluation

The same executor identity that wrote the sample cannot be its sole quality evaluator.

Each sample evaluation records an `evaluator_identity`.

If it equals the Writer `executor_identity`, qualification blocks.

The Professional Fiction Benchmark evidence has the same independence requirement.

This is a deterministic provenance rule. It does not claim that different models automatically provide good judgment.

## Professional Fiction Benchmark evidence

The sample pack must include:

- PASS status;
- benchmark evidence ref;
- benchmark-set/version ref;
- independent evaluator identity.

MYS-06 does not run the benchmark itself. MYS-08 will become the canonical producer of benchmark evidence.

Until then the boundary is fail-closed.

## Writer qualification

The final representative sample can be qualified while the Writer remains unqualified.

Writer qualification additionally requires:

- every sample artifact is attributed to the candidate Writer;
- no artifact required `MATERIAL` post-Writer rewriting;
- if revision class is `NONE`, Writer-output hash must equal final-text hash.

Allowed revision classes:

- `NONE`;
- `MECHANICAL`;
- `MATERIAL`.

`MECHANICAL` allows bounded cleanup without automatically disqualifying the Writer, but it requires an explicit revision-evidence ref.

`MATERIAL` also requires revision evidence and means the final sample does not demonstrate the original Writer's quality.

## Qualification refs

Successful sample evaluation produces deterministic:

`representative-sample:<hash>`

Successful Writer evaluation additionally produces:

`writer-qualification:<hash>`

Refs bind exact:

- qualification policy (minimum sample count/length and required mystic/quiet/audio coverage);
- book;
- StyleProfile;
- Writer identity/route/prompt;
- authority revisions;
- sample hashes;
- evaluation refs/status;
- benchmark evidence.

Changing the sample or qualification context changes the ref.

`verify_writer_qualification()` recomputes qualification and rejects a stale prior ref.

## MYS-05 integration

MYS-06 provides:

`readiness_with_sample_qualification()`

This is the standard bridge into MYS-05 `ExternalWritingReadiness`.

It sets:

- `representative_sample_qualified`;
- `representative_sample_ref`;
- `writer_qualified`;
- `writer_qualification_ref`.

The values are derived from the MYS-06 result rather than manually toggled.

A materially rewritten sample therefore cannot accidentally set `writer_qualified=true`.

## Machine-readable contracts

MYS-06 adds:

- `contracts/mystery-os/representative_fiction_sample.schema.json`;
- `contracts/mystery-os/writer_qualification.schema.json`.

These are future publishing-system integration contracts, not DB/API/UI implementation.

## Model/cost boundary

This slice performs **zero model/provider calls**.

Future sample generation may use an explicitly authorized Writer through MYS-05/MYS-11.

Future evaluation may use:

- deterministic checks;
- MysteryBench;
- ColdReader;
- Professional Fiction Benchmark;
- independent premium reasoning where justified;
- human editorial judgment.

No paid sample generation or evaluation occurs merely because MYS-06 exists.

## Deliberately OUT

- no sample prose generation;
- no paid/model/provider calls;
- no DB/Alembic migration;
- no FastAPI/Desktop UI;
- no MysteryBench implementation;
- no Professional Benchmark implementation;
- no automatic anti-cliche scanner implementation;
- no real `Линия 112` sample;
- no merge authorization.

## Acceptance evidence

MYS-06 is technically GREEN only when:

- clean pack qualifies sample + Writer;
- missing representative functions block;
- exact StyleProfile drift blocks;
- invalid/mismatched MYS-05 admission blocks;
- required evaluation coverage is enforced;
- same-writer evaluator blocks;
- MAJOR/BLOCKING gaps block scaling;
- Professional Benchmark evidence is mandatory/independent;
- material rewrite can qualify final sample but not Writer;
- Writer-candidate inheritance is impossible;
- authority snapshot changes invalidate qualification;
- audio mode requires listenability coverage;
- Writer qualification ref is version-bound;
- MYS-06 result populates MYS-05 readiness without manual qualification flags;
- inherited MYS-01..MYS-05 tests remain green;
- Ruff format/check pass;
- strict mypy passes;
- full local-core pytest passes;
- Desktop/Tauri/native smoke show no regression;
- secret scan passes;
- provider/model/paid calls = 0.

Technical GREEN does not authorize sample generation, mass drafting, merge, or the `Линия 112` pilot.
