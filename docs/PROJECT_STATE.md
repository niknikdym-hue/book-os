# BOOK OS — PROJECT STATE

**Status:** M7 FINAL ACCEPTANCE SYNC — PENDING EXACT-HEAD CI  
**Version:** 1.5.0  
**Date:** 2026-08-27  
**Canonical repository:** `https://github.com/niknikdym-hue/book-os`

## Current phase

**IMPLEMENTATION MILESTONE 7 — TASK 008 / BOOKBENCH v0.1**

Active contract: `docs/tasks/CODEX_TASK_008_BOOKBENCH.md`  
Implementation branch: `brain/task-008-bookbench`  
Active pull request: `PR #11 — Task 008 — BookBench v0.1`

Canonical `main` synchronized into this acceptance line:

`12e994dab4119eb94f861485ea5674bb003c4d23`

Last fully validated M7 source tree before main synchronization:

`279cb2e3460ed787a997919cc5bf1ea11f07113c`

Authoritative functional CI:

`33100945557` — SUCCESS

- local-core: Ruff format/check PASS; mypy PASS; **74/74 pytest PASS**;
- desktop: lint PASS; typecheck PASS; **9/9 Vitest PASS**; build PASS; production dependency audit PASS;
- tauri-smoke: `cargo test --locked` PASS; `cargo check --locked` PASS;
- secret-scan: PASS.

Normal CI external/model/judge live calls = `0`; paid calls = `0`.

## Accepted milestones

- **M0 / Task 001 — ACCEPTED AND MERGED**
- **M1 / Task 002 — ACCEPTED AND MERGED**
- **M2 / Task 003 — ACCEPTED AND MERGED**
- **M3 / Task 004 — ACCEPTED AND MERGED**
- **M4 / Task 005 — ACCEPTED AND MERGED**
- **M5 / Task 006 — ACCEPTED AND MERGED**
- **M6 / Task 007 — ACCEPTED AND MERGED:** PR `#10`, accepted implementation HEAD `8fcdd725b5c6ece2d7b9500ae87c55478e008bd4`, canonical merge `9cfa9b9e8966715c243410e44dbe011e363974c1`, final CI `32961531865` SUCCESS.

Do not return to M0–M6 without a new concrete defect.

## M7 acceptance evidence

Task 008 implementation now covers the required BookBench v0.1 scope:

- schema migration `0008`, exact reproducible snapshots and immutable EvaluationRun/EvaluationFinding history;
- versioned deterministic/statistical/evidence checks and grouped per-dimension `PASS | ATTENTION | BLOCKING` report with **no overall magic score**;
- deterministic AI-prose pathology signals with concrete examples/locations and no authorship-probability claim;
- versioned Author Voice Fingerprints from explicit exact revisions, persistent list/select operations and diagnostic target comparison;
- M5 EmbeddingGateway semantic duplication/novelty/contract-coverage signals with exact embedding identity and stale/incompatible-config gates;
- typed BookBench judge and blind pairwise execution through the accepted Model Gateway, mocked OpenAI structured path with `store=false`, deterministic fake CI path, stored pairwise seed and candidate remapping;
- judge independence `INDEPENDENT | SAME_CONFIG | UNKNOWN`, with same/unknown configuration prevented from masquerading as release-grade independent evidence;
- immutable M6 decision-dataset snapshots/version/hash and deterministic two-configuration per-role/per-dimension scorecards without a universal score;
- explicit current-safe BookBench → M6 EditorialFinding handoff with provenance and no automatic ChangeProposal, acceptance or waiver;
- authenticated BookBench API;
- native BookBench desktop workspace with BOOK/CHAPTER/MANUSCRIPT_UNIT target selection, deterministic/semantic/judge/pairwise controls, exact finding evidence, currentness, independence, Voice Fingerprint create/list/select/compare, AI-prose examples, dataset/config scorecards and explicit Editorial Inbox handoff;
- backup/restore compatibility through `0008` and M0–M6 regression coverage.

Task 008 REQUIRED ACCEPTANCE items 1–28 are objectively evidenced by implementation/tests and CI `33100945557`. Final M7 acceptance is withheld only until the post-`main` synchronization exact-head CI is green.

## Codex environment

The existing Codex environment `niknikdym-hue/book-os` is present and was used for M7. Earlier intermittent environment-resolution messages are **not an active Owner blocker** and are superseded by the successfully published GitHub implementation.

Codex task/report text is never implementation authority. A task is considered delivered only when its code is present in GitHub and validated by the required CI gates.

## Repository hygiene

Only PR #11 is the active M7 implementation PR. PRs #1–#10 are closed/merged.

Historical milestone branches and Codex task history are not project authority. No temporary M7 recovery/transport workflow or helper file remains in the final M7 source tree.

## Scope guard

M7 contains no M8 Russia-provider implementation, provider production promotion, Literary Master/export/audio implementation, cloud/accounts/billing/sync or private manuscript/evaluation corpus.

Human authority, no-silent-mutation, no-universal-score and zero-normal-CI-live/paid-call invariants remain mandatory.

## Fixed critical path to launch

`M7 BookBench → M8 Russia/no-VPN provider lane → M9 Literary Master + exports → M10 real Business Nonfiction pilot → GO/NO-GO`

## Next permitted action

1. Run full CI on the exact post-`main` synchronized PR #11 HEAD.
2. If all four canonical jobs pass, Central Brain issues `ACCEPT Task 008 / M7`.
3. Merge PR #11 to `main`.
4. Verify canonical merged `main`.
5. Immediately synchronize project state to M8 and issue the bounded M8 Russia/no-VPN provider-lane contract.
6. Do not start M9 until M8 is accepted/merged.

## Change log

### 1.5.0 — 2026-08-27
- Replaced stale Codex-environment blocker state with actual published M7 evidence.
- Recorded final functional CI `33100945557`: 74/74 Python, 9/9 desktop, Rust test/check and scans PASS.
- Recorded completion of the previously missing desktop target/pairwise/Voice Fingerprint/independence gates and Voice Fingerprint list API.
- Established GitHub publication + CI, not Codex task text, as the delivery rule.
- Entered final M7 main-sync acceptance gate; M8 remains locked until M7 merge.
