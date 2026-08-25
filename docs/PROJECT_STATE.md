# BOOK OS — PROJECT STATE

**Status:** ACTIVE CHECKPOINT  
**Version:** 1.1.0  
**Date:** 2026-08-25  
**Canonical repository:** `https://github.com/niknikdym-hue/book-os`

## Current phase

**IMPLEMENTATION MILESTONE 4 — TASK 005 READY**

Active contract:

`docs/tasks/CODEX_TASK_005_RESEARCH_CLAIM_LEDGER.md`

Planned implementation branch:

`brain/task-005-research-claim-ledger`

## Accepted authority

- Product/Authority baseline: `BOOK_OS_AUTHORITY.md`
- Product spec: `PRODUCT_SPEC_v0.1.md`
- Core Ontology: `CORE_ONTOLOGY.md` v0.2.0
- Editorial contracts/gates: `EDITORIAL_PROTOCOLS_v0.1.md`
- Model Gateway: `MODEL_GATEWAY_v0.1.md`
- Technical Architecture: `TECHNICAL_ARCHITECTURE_v0.1.md`
- Security/availability: `SECURITY_AVAILABILITY_v0.1.md`
- Implementation roadmap: `IMPLEMENTATION_ROADMAP_v0.1.md`
- Execution control: `TASK_EXECUTION_PROTOCOL_v0.1.md`
- Complete recovery map: `DESIGN_INDEX.md`

## Completed milestones

### M0 / Task 001 — ACCEPTED AND MERGED

- PR `#3`
- canonical merge: `b2bbe3dd208e15cbca0420e90c1b4adadab7acda`
- Owner-Mac `Local Core healthy`: PASS
- deterministic sidecar shutdown after normal close + Cmd-Q: PASS

### M1 / Task 002 — ACCEPTED AND MERGED

- PR `#5 — Authority & Persistence Engine`
- canonical merge: `c2cf2e88c81797ff3f67873b1d406ecc7f806e84`
- immutable revisions, Authority statuses, exact-base ChangeProposal, Decision/Approval/Provenance, transactional stale-baseline protection and WAL-safe backup/restore accepted.

### M2 / Task 003 — ACCEPTED AND MERGED

- PR `#6 — Book Creation, Contracts & Architecture`
- accepted source HEAD: `182b8e45ae7092fd2655ee61e42126af4cac1542`
- canonical merge: `5bd6c1af5dd1b502696e359c813f8e6544919cb8`
- final CI `32882543129`: SUCCESS
- accepted native product path:
  `Projects → New Business Book → Book Contract approval → Architecture approval → Chapter → Chapter Contract approval`
- per-book `project.sqlite`, restart discovery, stable chapters, authenticated local API and bounded Tauri proxy accepted.

### M3 / Task 004 — ACCEPTED AND MERGED

- PR `#7 — Model Gateway + Controlled Drafting`
- accepted source tree first reached at `16b724f056da5e2213b3e99dd003965573b41de0`
- canonical M3 merge: `1814ac7fffe9f9a6666ea59125439f32b0cff879`
- final full source-tree CI `32893389579`: SUCCESS
  - `local-core`: Ruff format/check + mypy + **30/30 pytest PASS**
  - `desktop`: lint + typecheck + Vitest + build + dependency audit PASS
  - `tauri-smoke`: `cargo test --locked` + `cargo check --locked` PASS
  - `secret-scan`: PASS
- provider-neutral gateway, versioned prompt registry, macOS Keychain SecretStore, mocked OpenAI Responses development adapter, deterministic fake adapter, BoundedTask/ModelRun persistence and DRAFT-only ManuscriptUnit generation accepted.
- exact Chapter Contract revision/hash provenance and stale-authority discard accepted.
- AI/system actor cannot approve generated text.
- CI external/model calls: `0`; paid calls: `0`.

## Active implementation task — M4

`Task 005 — Research Engine + Claim Ledger`

M4 implements the first factual-evidence vertical:

`ManuscriptUnit revision → Claim → research candidate → Source → Evidence → verification state`

Non-negotiable distinction:

`Source != Evidence != Claim`.

A material claim cannot become `SUPPORTED` merely because a search result/source exists. Support requires explicit Evidence with a real Source and concrete locator/pointer.

Initial metadata adapters are bounded to OpenAlex, Crossref and Semantic Scholar Academic Graph, with mocked HTTP in normal CI.

## Scope guard

Do not implement yet:

- embeddings / Book Memory;
- Developmental/Literary/Fact editorial workflows;
- BookBench;
- Yandex/GigaChat Russia provider lane;
- Literary Master/export/audio handoff;
- accounts/cloud/billing.

## Next permitted action

1. Synchronize design hash manifest for current control docs.
2. Create `brain/task-005-research-claim-ledger` from the resulting exact `main` HEAD.
3. Implement only Task 005 / M4.
4. Open one PR, fix objective CI/acceptance blockers, then Central Brain ACCEPT + merge.
5. Only then start M5 Book Memory.

## Known blockers

No Owner decision blocker for the bounded M4 metadata/evidence implementation. Paid research subscriptions, copyrighted full-text ingestion or paywall circumvention are stop conditions and are not authorized.

## Operational rule

`main` is accepted project-development authority. Implementation code uses bounded branches/PRs. Central Brain may make small project-control updates directly to `main` when a separate PR adds no review value.

## Recovery rule

If chat context disappears:

1. Open repository `main`.
2. Read README recovery order + `DESIGN_INDEX.md`.
3. Read this file and `TASK_EXECUTION_PROTOCOL_v0.1.md`.
4. Read `docs/tasks/CODEX_TASK_005_RESEARCH_CLAIM_LEDGER.md`.
5. Inspect `origin/main` and `brain/task-005-research-claim-ledger`.
6. Continue only M4 until Central Brain ACCEPT/merge; do not start M5 automatically.
