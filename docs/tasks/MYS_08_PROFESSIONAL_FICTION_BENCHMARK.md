# MYS-08 — PROFESSIONAL FICTION BENCHMARK

**Status:** IMPLEMENTATION / STACKED DRAFT  
**Date:** 2026-09-19  
**Repository:** `niknikdym-hue/book-os`  
**Base:** `codex/mys-07-mysterybench-coldreader-20260918` @ `cdf30088ff791661700c48e26b50d44b2af53ac6`  
**Branch:** `codex/mys-08-professional-fiction-benchmark-20260919`

## Purpose

Prevent MYSTERY OS from certifying itself only against criteria invented by MYSTERY OS.

MYS-08 validates whether the current fiction artifact has been compared, under a versioned and rights-safe protocol, with a relevant set of strong professional commercial fiction references.

The layer does **not** assign a universal artistic score.

It validates:

1. the benchmark corpus is fit for the target market/subgenre;
2. the comparison evidence is exact, current and independently evaluated;
3. findings are tied to current manuscript evidence and real benchmark observations;
4. readiness labels do not hide material defects;
5. the process does not request imitation or retain protected reference expression.

## Reuse boundary

MYS-08 reuses:

- MYS-07 `VerifiedEvaluationArtifact`;
- shared BOOK OS BookBench/evaluation persistence;
- MYS-06 ProfessionalBenchmarkEvidence bridge;
- future shared cost/routing provenance.

It does **not** create:

- another evaluation database;
- another judge runner;
- another model gateway;
- an opaque global score.

## BenchmarkSet as a first-class artifact

A `FictionBenchmarkSet` is versioned by:

- benchmark-set ID;
- integer version;
- deterministic content hash.

It records:

- subgenre;
- target market;
- language;
- audience;
- publication window;
- last review time;
- selected reference metadata.

The benchmark-set policy declares expected:

- subgenre;
- target market;
- language;
- minimum number of references;
- minimum distinct authors;
- minimum publication-year span;
- maximum share of one author;
- minimum lawful text-access references;
- required reference categories;
- minimum established-publisher representation;
- optional freshness limit.

These are policy values, not hidden universal literary constants.

Changing the corpus-quality policy changes the final Professional Benchmark ref.

## Reference diversity

Supported reference categories:

- `COMMERCIAL_SUCCESS`;
- `CRITICAL_RESPECT`;
- `DURABLE_BACKLIST`;
- `RECENT_EXPECTATION`;
- `AUDIO_REFERENCE`.

The purpose is not to make every set contain one rigid market recipe.

The policy for a target project decides which categories are required.

MYS-08 blocks:

- insufficient references;
- too few authors;
- single-author monoculture above policy threshold;
- too-narrow publication span;
- missing required categories;
- insufficient established-publisher coverage;
- insufficient lawful text-access coverage.

## Rights/access boundary

A public MYSTERY OS benchmark set stores metadata and non-reconstructive observations, not copyrighted benchmark manuscripts.

Access levels:

- `METADATA_ONLY`;
- `DERIVED_NON_RECONSTRUCTIVE`;
- `LAWFUL_BOUNDED_TEXT`;
- `LICENSED_FULL_ACCESS`;
- `PUBLIC_DOMAIN_FULL_ACCESS`.

Rights bases:

- `PUBLIC_METADATA`;
- `PUBLIC_DOMAIN`;
- `USER_OWNED`;
- `LICENSED`;
- `OTHER_DOCUMENTED`.

Every reference requires a rights ref and source-metadata ref.

The runtime blocks:

- raw protected benchmark text embedded in the set;
- text-access claims backed only by metadata rights;
- craft observations attached to metadata-only access;
- unknown access/rights/category codes.

MYS-08 does not itself decide copyright law. It requires explicit documented provenance before benchmark material can be used.

## No-mimicry rule

Benchmarking asks:

- is our dialogue more expository than the professional range?
- is our midpoint structurally weaker?
- is our setting less causally integrated?
- does our prose show less viewpoint specificity?

It does **not** ask:

- write like a named living author;
- copy this author's cadence;
- reproduce signature metaphors;
- copy another series' twist architecture.

Any run with:

- `mimicry_request_detected=true`; or
- `protected_expression_reproduction_detected=true`

is blocked.

## Checkpoints

### PRE_DRAFT

Required dimensions:

- PREMISE_IDENTITY;
- NARRATIVE_ENGINE;
- CHARACTERS;
- MYSTERY_CONSTRUCTION;
- ORIGINALITY.

### REPRESENTATIVE_SAMPLE

Required:

- SCENES;
- DIALOGUE;
- SUSPENSE;
- PROSE_VOICE;
- SETTING;
- EMOTIONAL_ARCHITECTURE;
- ORIGINALITY.

### MIDBOOK

Required:

- NARRATIVE_ENGINE;
- CHARACTERS;
- SCENES;
- MYSTERY_CONSTRUCTION;
- SUSPENSE;
- SETTING;
- EMOTIONAL_ARCHITECTURE;
- WHOLE_BOOK_STRUCTURE;
- ORIGINALITY.

### WHOLE_BOOK / FINAL

Required:

- all B1-B12 dimensions.

### Audio

When audio is selected, every checkpoint policy additionally requires:

- AUDIO_READINESS.

## Verified evaluation provenance

Each dimension evaluation must resolve to an exact immutable shared `VerifiedEvaluationArtifact`.

It must match:

- evaluation ref;
- manuscript snapshot;
- evaluator identity;
- evaluator class;
- rubric ref;
- exact purpose:
  `PROFESSIONAL_BENCHMARK:<checkpoint>:<dimension>`;
- SUCCEEDED;
- current=true.

An evaluation produced for another book, rubric or purpose cannot be relabeled as benchmark evidence.

Semantic/high-stakes evaluations cannot use the same Writer executor identity when independent evaluation is required.

## Finding evidence

A benchmark finding must bind:

- one dimension;
- one exact dimension-evaluation ref;
- manuscript evidence refs;
- benchmark observation refs;
- observation;
- recommended action;
- bounded non-infringing comparison;
- severity;
- optional human disposition.

Manuscript evidence must exist in the caller's verified current snapshot evidence set.

Benchmark observation refs must exist inside the exact qualified BenchmarkSet.

A free-form string cannot pretend to be comparative evidence.

## Severity

- `BLOCKING` — never waivable for qualification;
- `MAJOR` — may carry a verified human disposition at intermediate gates, but the readiness band must still admit that professional gaps remain;
- `MINOR`;
- `NOTE`.

A dimension marked PASS cannot simultaneously contain BLOCKING/MAJOR findings.

A BLOCKING_GAP dimension must have a corresponding BLOCKING finding.

A MAJOR_GAP dimension must have a corresponding MAJOR finding.

## Readiness bands

Internal diagnostic bands:

- `BELOW_PROFESSIONAL_FLOOR`;
- `PROFESSIONAL_GAPS_REMAIN`;
- `PROFESSIONAL_RANGE_CANDIDATE`;
- `STRONG_PROFESSIONAL_CANDIDATE`.

Rules:

- any BLOCKING -> BELOW_PROFESSIONAL_FLOOR;
- any MAJOR -> cannot be above PROFESSIONAL_GAPS_REMAIN;
- no material gaps -> at least PROFESSIONAL_RANGE_CANDIDATE;
- STRONG_PROFESSIONAL_CANDIDATE requires a verified human confirmation ref.

Each checkpoint policy also defines its minimum acceptable readiness band.

For representative sample and final publication workflows, policy can therefore require professional-range or strong-candidate status without hard-coding that threshold into the generic validator.

## Freshness

BenchmarkSet validation is recomputed on every Professional Benchmark gate.

A cached historical “qualified” set cannot stay green after:

- set review expires;
- rights/access metadata changes;
- corpus membership changes;
- corpus-quality policy changes.

The final benchmark ref binds both:

- benchmark set snapshot;
- benchmark-set quality policy.

## Version-bound output

Successful evaluation produces:

`professional-fiction-benchmark:<hash>`

It binds:

- book;
- exact checkpoint policy;
- exact BenchmarkSet policy;
- manuscript snapshot;
- evaluated revisions;
- exact BenchmarkSet version/hash;
- all dimension evaluations;
- findings;
- readiness band;
- rights/mimicry flags;
- strong-candidate human confirmation.

`verify_professional_benchmark()` recomputes the gate and rejects stale evidence.

## MYS-06 bridge

`sample_benchmark_evidence_from_result()` converts a qualified MYS-08 result into the MYS-06 benchmark boundary.

The bridge is PASS only if:

- MYS-08 is qualified; and
- readiness is at least `PROFESSIONAL_RANGE_CANDIDATE`.

A lower-policy intermediate result with `PROFESSIONAL_GAPS_REMAIN` cannot accidentally unlock representative-sample qualification.

The bridge uses fixed aggregator provenance:

`mystery-os/professional-benchmark-gate`

rather than accepting a caller-invented “independent evaluator” identity.

## Machine-readable contracts

MYS-08 adds/hardens:

- `contracts/mystery-os/fiction_benchmark_set.schema.json`;
- `contracts/mystery-os/professional_fiction_benchmark.schema.json`.

The runtime remains the authority for cross-field invariants that JSON Schema alone cannot express.

## Model/cost boundary

This slice runs **zero provider/model calls**.

Future benchmark execution may use:

- deterministic corpus diagnostics;
- shared BookBench;
- bounded pairwise comparison;
- independent premium reasoning when it changes an editorial decision materially;
- human editorial review.

The validator only consumes versioned evidence.

## Deliberately OUT

- no benchmark source acquisition;
- no model judge execution;
- no copyrighted corpus storage;
- no DB/Alembic migration;
- no FastAPI/Desktop UI;
- no real `Линия 112` benchmark corpus yet;
- no merge authorization.

## Acceptance evidence

MYS-08 is technically GREEN only when tests prove:

- clean relevant/diverse/rights-safe BenchmarkSet passes;
- wrong market/language/subgenre blocks;
- author monoculture/coverage defects block;
- rights/access violations block;
- stale BenchmarkSet blocks;
- required checkpoint dimensions enforced;
- audio dimension conditional;
- evaluation artifact provenance exact;
- Writer cannot self-judge semantic benchmark;
- mimicry/protected-expression flags block;
- manuscript evidence and benchmark observation refs are verified;
- BLOCKING cannot be waived/hidden;
- MAJOR may be human-disposed only in a compatible readiness band;
- STRONG candidate requires verified human confirmation;
- manuscript/BenchmarkSet snapshots are exact;
- benchmark ref changes with corpus-quality policy;
- live gate revalidates corpus freshness;
- MYS-06 bridge requires professional range;
- inherited MYS-01..07 tests remain green;
- Ruff, strict mypy and full pytest pass;
- Desktop/Tauri/native/secret-scan pass;
- provider/model/paid calls = 0.

Technical GREEN does not authorize merge, corpus acquisition spend, manuscript generation or release.
