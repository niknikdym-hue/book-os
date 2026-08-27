# BOOK OS — PROJECT STATE

**Status:** M8 ACTIVE — TASK 009 READY
**Version:** 1.5.1
**Date:** 2026-08-27
**Canonical repository:** `https://github.com/niknikdym-hue/book-os`

## Current phase

**IMPLEMENTATION MILESTONE 8 — RUSSIA / NO-VPN PROVIDER LANE**

Canonical accepted `main` at M8 activation:

`5115a20512437a68da7ee7eed44e55b8ebbf0d90`

Active contract:

`docs/tasks/CODEX_TASK_009_RUSSIA_PROVIDER_LANE.md`

Planned branch:

`brain/task-009-russia-provider-lane`

## Accepted milestones

- M0 / Task 001 — ACCEPTED AND MERGED.
- M1 / Task 002 — ACCEPTED AND MERGED.
- M2 / Task 003 — ACCEPTED AND MERGED.
- M3 / Task 004 — ACCEPTED AND MERGED.
- M4 / Task 005 — ACCEPTED AND MERGED.
- M5 / Task 006 — ACCEPTED AND MERGED.
- M6 / Task 007 — ACCEPTED AND MERGED.
- **M7 / Task 008 — ACCEPTED AND MERGED:** PR #11; accepted HEAD `8052ed9e1fe9f7902526a19ea8f6c9727946e4e4`; merge commit `5115a20512437a68da7ee7eed44e55b8ebbf0d90`; final exact-head CI `33101458190` SUCCESS with 74/74 pytest, 9/9 desktop tests, Rust test/check, dependency and secret scans.

Do not return to M0–M7 without a concrete regression.

## M8 objective

Prove a provider-neutral runtime lane for a user in Russia that:
- requires no VPN;
- requires no personal foreign AI subscription/key;
- does not circumvent provider geography/contracts;
- retains provider/model/config provenance and data-minimization rules;
- routes only through positively eligible provider/model/configs;
- does not lower BOOK OS role-quality gates;
- has structured unavailable/fallback behavior.

M8 uses two-stage acceptance:
1. implementation + mocked CI;
2. explicit live provider promotion evidence.

Passing Stage A alone is not Russia-ready acceptance.

## Current official facts verified 2026-08-27

- Yandex Cloud exposes a Russia region and AI Studio text/embeddings APIs; structured JSON/JSON-Schema output and scoped API-key/IAM authorization are documented.
- GigaChat uses `https://api.giga.chat`; access-token authorization, B2B/CORP scopes and strict JSON-Schema output are documented.
- GigaChat commercial use requires an appropriate paid/commercial path; `GigaChat-3-Ultra` is currently physical-person freemium only and is not a BOOK OS commercial-production candidate.
- Russia remains absent from OpenAI's official API-supported-country list, so OpenAI cannot be the mandatory Russian runtime route.

Canonical dated sources are embedded in Task 009.

## Non-negotiable M8 rules

- normal CI external/provider/model calls = 0; paid calls = 0;
- secrets remain behind SecretStore and never reach React/Git/logs;
- no `verify=False` production TLS path;
- live promotion is explicit-flag gated and never triggered by ordinary UI/tests;
- provider health does not imply provider quality;
- a route is production-eligible only after BookBench role promotion;
- no fallback below quality floor;
- no M9/M10 implementation inside M8.

## Execution state

Task 009 is READY. Create the M8 branch from the exact canonical `main` after this control-state commit, open one draft PR, and implement only Task 009.

Codex report text is not delivery authority. Required delivery evidence is:
`published GitHub HEAD + inspectable PR diff + authoritative GitHub CI`.

## Fixed critical path

`M8 Russia/no-VPN provider lane → M9 Literary Master + exports → M10 real Business Nonfiction pilot → GO/NO-GO`

## Next action

1. Commit Task 009 + this state/hash synchronization to canonical `main`.
2. Create `brain/task-009-russia-provider-lane`.
3. Open one draft M8 PR.
4. Execute Stage A implementation against exact baseline.
5. Central Brain reviews actual GitHub HEAD/diff/CI.
6. If Stage A passes but credentials/commercial access/live-eval budget are absent, record `BLOCKED_LIVE_PROMOTION`; do not lower quality.
7. After Stage B live promotion and final CI, ACCEPT + merge M8.
8. Only then start M9.

## Change log

### 1.5.1 — 2026-08-27
- Recorded M7 ACCEPT + merge and final exact-head CI.
- Activated M8 / Task 009.
- Added current provider-policy facts verified from official Yandex/GigaChat/OpenAI sources.
- Added two-stage M8 acceptance and the hard GitHub-delivery rule.
