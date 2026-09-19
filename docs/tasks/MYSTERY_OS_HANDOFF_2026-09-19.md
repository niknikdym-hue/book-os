# MYSTERY OS — HANDOFF / BREAKPOINT 2026-09-19

**Status:** SAFE BREAKPOINT  
**Repository:** `niknikdym-hue/book-os`  
**Do not merge without Owner authorization.**  
**Provider/model/paid calls in MYS-05..07 work described here:** 0.

## 1. Exact completed GREEN slices

### MYS-05 — scene-scoped WRITING_ALLOWED

Draft PR: #47  
Branch: `codex/mys-05-writing-admission-20260918`  
Exact GREEN head:

`ed15242a1f2c165744b67114ad20a57830852f3e`

CI evidence recorded in PR #47.

PASS:
- Ruff format/check;
- strict mypy;
- full local-core pytest;
- Desktop lint/typecheck/tests/build/audit;
- Tauri cargo test/check;
- secret scan;
- native self-contained macOS build/launch.

Known external non-product blocker:
- Apple distribution signing preflight fails because distribution credentials are absent.

This is **not** a MYS-05 logic failure.

MYS-05 is Draft/unmerged.

### MYS-06 — Representative Fiction Sample / Writer Qualification

Draft PR: #48  
Branch: `codex/mys-06-sample-writer-qualification-20260918`  
Exact GREEN head:

`83e0a7760ea580ff0b38b0e7d70a66f58c49ae89`

CI run #1707 / run id `35361335900`.

PASS:
- Ruff format/check;
- strict mypy;
- full local-core pytest;
- Desktop lint/typecheck/tests/build/audit;
- Tauri cargo test/check;
- secret scan;
- native self-contained macOS build/launch.

Known external non-product blocker:
- Apple distribution signing preflight fails because distribution credentials are absent.

This is **not** a MYS-06 logic failure.

MYS-06 is Draft/unmerged.

## 2. MYS-06 rules now fixed

MYS-06 deliberately separates:

1. `representative_sample_qualified`
2. `writer_qualified`

A strong final sample after a MATERIAL editorial rewrite may qualify the final sample but **must not** qualify the original Writer.

Writer qualification is bound to exact:

- StyleProfile snapshot;
- current fiction authority refs;
- verified MYS-05 WritingAdmission provenance;
- Writer executor/route/prompt;
- sample hashes;
- evaluation refs;
- Professional Benchmark evidence;
- qualification policy.

Nontrivial post-Writer edits require revision-evidence refs.

MYS-06 populates MYS-05 readiness through a standard bridge rather than manual qualification flags.

## 3. Current MYS-07 provisional state

Branch:

`codex/mys-07-mysterybench-coldreader-20260918`

Current exact head at break:

`35d14ec640384a630537f8bdbc80beeeff9238f9`

Base:

MYS-06 exact GREEN head  
`83e0a7760ea580ff0b38b0e7d70a66f58c49ae89`

Current branch is 9 commits ahead of MYS-06.

Files added:

- `services/local-core/src/book_os_core/mystery_bench_validation.py`
- `services/local-core/tests/test_mystery_bench_validation.py`
- `contracts/mystery-os/mystery_bench_run.schema.json`
- `contracts/mystery-os/cold_reader_run.schema.json`
- `contracts/mystery-os/adversarial_case_reconstruction.schema.json`
- `docs/tasks/MYS_07_MYSTERYBENCH_COLDREADER.md`

MYS-07 has **no PR and no CI acceptance yet**.

Do not call MYS-07 GREEN.

## 4. MYS-07 architecture already implemented provisionally

MYS-07 is designed as a fiction-specific evidence/gate layer over shared BOOK OS BookBench.

Do **not** create a second:

- evaluation DB;
- snapshot store;
- model runner;
- cost ledger;
- evaluator registry.

Current provisional implementation includes:

- MIDBOOK vs FINAL policies;
- required mystery dimensions;
- conditional supernatural/audio dimensions;
- ColdReader checkpoints;
- prohibition on exposing private CaseSolution/spoiler authority to ColdReader;
- adversarial blind reconstruction before CaseSolution reveal;
- final evidence-consumption requirements;
- no averaging-away of BLOCKING gaps;
- MAJOR gap requires human disposition;
- exact manuscript/authority snapshot binding;
- deterministic MysteryBench ref;
- version-bound verification;
- zero model/provider calls.

## 5. Important MYS-07 correction that is NOT YET APPLIED

The next action must strengthen evaluation provenance before opening a PR.

Do not trust an arbitrary existing evaluation ref merely because it exists.

Introduce/read a verified evaluation artifact that proves the exact combination of at least:

- evaluation ref;
- manuscript/BookBench snapshot ref;
- evaluator identity;
- evaluator class;
- rubric/version or purpose/dimension;
- successful/current status.

Mystery dimension evidence must match that artifact exactly.

Also tighten adversarial comparison so the `accepted_case_solution_revision_ref` must equal the **current designated CaseSolution authority ref**, not merely any member of the authority snapshot.

This correction was planned immediately before the break but was **not committed**.

Start from current MYS-07 head and implement this first.

## 6. MYS-07 next acceptance sequence

After the provenance correction:

1. update/add adversarial tests;
2. run Central Brain review of exact diff;
3. apply Ruff formatting if CI requires it;
4. strict mypy;
5. full pytest including inherited MYS-01..06;
6. Desktop/Tauri/native/secret-scan regression checks;
7. only then open/retain a Draft PR and record exact GREEN head.

No model/provider/paid calls are required for this slice.

## 7. Later planned sequence

After MYS-07 is technically GREEN:

- MYS-08 — Professional Fiction Benchmark;
- MYS-09 — Series Brain / semantic collision control;
- MYS-10 — anti-cliche scanner / exception registry;
- MYS-11 — production routing integration;
- later bounded Agents API/editorial-prep and real `Линия 112` pilot only after the deterministic/editorial machine is ready.

Do not jump to writing the real series before the required gates are implemented.

## 8. Restart instruction

At restart, first verify:

- PR #47 still points to `ed15242a...`;
- PR #48 still points to `83e0a776...`;
- MYS-07 branch still points to `35d14ec...` or inspect any newer commits before continuing.

Then resume MYS-07 from section 5 of this handoff.

No merge. No release. No paid/model call without explicit bounded authorization.
