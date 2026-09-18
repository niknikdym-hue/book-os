# MYS-07 — MYSTERYBENCH / COLD READER / ADVERSARIAL RECONSTRUCTION

**Status:** IMPLEMENTATION / STACKED DRAFT  
**Date:** 2026-09-18  
**Repository:** `niknikdym-hue/book-os`  
**Base:** `codex/mys-06-sample-writer-qualification-20260918` @ `83e0a7760ea580ff0b38b0e7d70a66f58c49ae89`  
**Branch:** `codex/mys-07-mysterybench-coldreader-20260918`

## Purpose

Turn the mystery-specific quality standard into version-bound evaluation evidence **without creating a second BookBench database or runner**.

MYS-07 does not ask deterministic code to decide whether a novel is emotionally powerful or beautifully written.

It decides whether the required quality judgments:

- exist;
- evaluate the exact manuscript/authority snapshot;
- cover the required mystery dimensions;
- come from allowed/independent evaluator provenance;
- consume the required ColdReader/adversarial evidence;
- have no unresolved BLOCKING gap;
- have human authority for any retained MAJOR gap.

## Reuse boundary

BOOK OS BookBench remains the evaluation infrastructure.

MYS-07 consumes verified evaluation refs projected from BookBench or another explicitly registered evaluation artifact.

No second:

- evaluation DB;
- model runner;
- snapshot store;
- cost ledger;
- evaluator registry

is created in this slice.

The current BookBench database schema still uses its original nonfiction dimension enum. MYS-07 therefore acts as a fiction-specific orchestration/evidence layer over immutable BookBench evaluation refs rather than duplicating or prematurely rebuilding BookBench persistence. A future integration slice may widen generic persistence once the fiction rubric set is stable.

## Version binding

Every MysteryBench pack binds:

- book;
- exact manuscript snapshot ref;
- exact manuscript snapshot SHA-256;
- exact accepted fiction authority revision refs;
- private-spoiler subset of that authority;
- Writer executor identity;
- exact MysteryBench policy;
- exact dimension evaluation evidence;
- exact ColdReader protocol evidence where required;
- exact adversarial reconstruction evidence where required.

Any material change changes the deterministic:

`mystery-bench:<hash>`

## Required dimensions

### MIDBOOK

Required:

- CASE_COHERENCE;
- FAIR_PLAY;
- CHARACTER_CAUSALITY;
- NARRATIVE_INTEGRITY;
- TENSION_PACING;
- ORIGINALITY_ANTI_CLICHE;
- RESEARCH_REALISM;
- EMOTIONAL_ARCHITECTURE.

Conditional:

- SUPERNATURAL_INTEGRITY when supernatural causality is material;
- AUDIO_READINESS when audio is selected.

### FINAL

Required:

- CASE_COHERENCE;
- FAIR_PLAY;
- REVEAL_QUALITY;
- SUSPECT_QUALITY;
- CHARACTER_CAUSALITY;
- NARRATIVE_INTEGRITY;
- TENSION_PACING;
- ORIGINALITY_ANTI_CLICHE;
- PROSE_VOICE;
- SETTING_FUNCTION;
- RESEARCH_REALISM;
- EMOTIONAL_ARCHITECTURE.

Conditional:

- SUPERNATURAL_INTEGRITY;
- AUDIO_READINESS.

## Dimension evidence

Each dimension records:

- mystery dimension;
- status;
- immutable evaluation ref;
- exact BookBench/manuscript snapshot ref;
- versioned rubric ref;
- evaluator identity/class;
- independence state;
- supporting evidence refs;
- human disposition ref when applicable.

Runtime does not trust a random string as evidence.

Every evaluation ref must exist in the caller-supplied **verified evaluation catalog**.

This is the integration point to shared BookBench persistence.

## Severity rule

Dimension states:

- `PASS`;
- `MAJOR_GAP`;
- `BLOCKING_GAP`;
- `NOT_EVALUATED`.

Rules:

- BLOCKING is never waivable;
- NOT_EVALUATED blocks;
- MAJOR blocks unless it carries an explicit **verified human disposition ref**;
- a string invented by a model does not satisfy human disposition.

This follows the foundation rule that aggregate quality cannot average away broken case logic or unfairness.

## Independence

For semantic/LLM/pairwise/human evidence:

- independence state must be `INDEPENDENT`;
- evaluator identity must differ from Writer executor identity.

For deterministic checks:

- `NOT_APPLICABLE` or `INDEPENDENT` is permitted.

Different model names alone do not prove good judgment; this is only a provenance gate.

## ColdReader protocol

ColdReader does **not** receive private CaseSolution authority.

For every checkpoint MYS-07 records:

- exact manuscript snapshot;
- evaluation ref;
- evaluator identity;
- suspects;
- hypotheses;
- perceived clues;
- confusion;
- predicted twists;
- engagement state;
- post-reveal outcome fields when relevant.

Private CaseSolution exposure or private spoiler refs are protocol contamination and block the run.

### MIDBOOK required checkpoints

- EARLY;
- QUARTER;
- MIDPOINT.

### FINAL required checkpoints

- EARLY;
- QUARTER;
- MIDPOINT;
- THREE_QUARTER;
- PRE_REVEAL;
- POST_REVEAL.

At FINAL, POST_REVEAL must record:

- whether solution was inferable;
- whether it felt earned;
- whether late invention was detected;
- whether a stronger alternative remained.

ColdReader observations are evidence, not automatic literary authority. Final dimension evaluators must consume the protocol evidence.

At FINAL:

- FAIR_PLAY and REVEAL_QUALITY must cite exact ColdReader protocol ref.

## Adversarial Case Reconstruction

By default:

- optional at MIDBOOK;
- mandatory at FINAL.

Sequence:

1. evaluator receives manuscript snapshot without private spoiler authority;
2. evaluator fixes blind reconstruction;
3. only then receives accepted CaseSolution for comparison.

The contract therefore records:

`RECONSTRUCTION_THEN_CASE_SOLUTION`

Blind input may not include:

- CaseSolution;
- any authority marked private spoiler.

Adversarial blockers:

- required facts absent from manuscript;
- impossible timeline;
- materially stronger alternate solution;
- accepted solution contradicts manuscript;
- decisive supernatural rule never established;
- unfair decisive withholding.

At FINAL:

- CASE_COHERENCE;
- FAIR_PLAY;
- NARRATIVE_INTEGRITY

must cite exact adversarial protocol ref.

## Optional evidence

A policy may not require ColdReader/adversarial evidence at a stage, but if optional evidence is supplied it is still validated rather than rejected merely for being extra.

## Machine-readable contracts

MYS-07 adds:

- `contracts/mystery-os/mystery_bench_run.schema.json`;
- `contracts/mystery-os/cold_reader_run.schema.json`;
- `contracts/mystery-os/adversarial_case_reconstruction.schema.json`.

## Model/cost boundary

This slice performs zero model/provider calls.

Future evaluation execution may route through shared BookBench and selective premium/Astra/Agents operations, but MYS-07 itself only consumes immutable evaluation artifacts and validates them.

## Deliberately OUT

- no real judge/model calls;
- no ColdReader model execution;
- no BookBench DB migration;
- no new evaluation persistence;
- no Professional Fiction Benchmark implementation (MYS-08);
- no Series Brain/collision layer (MYS-09);
- no real `Линия 112` manuscript;
- no merge authorization.

## Acceptance evidence

MYS-07 is technically GREEN only when tests prove at least:

- clean FINAL pack passes;
- missing dimensions block;
- BLOCKING cannot be waived;
- MAJOR requires verified human disposition;
- unverified evaluation refs block;
- semantic evaluator must be independent from Writer;
- deterministic independence rule works;
- stale manuscript/authority snapshot blocks;
- ColdReader CaseSolution/spoiler contamination blocks;
- required checkpoint protocol enforced;
- adversarial blind-before-reveal boundary enforced;
- adversarial case defects block;
- final FAIR_PLAY/REVEAL/CASE evaluations consume protocol refs;
- supernatural/audio dimensions are conditional;
- MIDBOOK does not require FINAL-only dimensions/reconstruction by default;
- MysteryBench ref is version-bound to policy/evidence;
- inherited MYS-01..MYS-06 suite remains green;
- Ruff/mypy/full pytest pass;
- Desktop/Tauri/native smoke pass;
- secret scan passes;
- provider/model/paid calls = 0.

Technical GREEN does not authorize merge, final release, model spend or the real series pilot.
