# BOOK OS — PRE-IMPLEMENTATION HARDENING v0.1

**Status:** ACCEPTED TECHNICAL HARDENING BASELINE  
**Version:** 0.1.0  
**Date:** 2026-08-23  
**Authority:** Central Brain under `BOOKOS-DEC-0002`  
**Purpose:** close implementation-critical gaps found in the final pre-code architecture audit without changing product intent.

## 1. Audit conclusion

The accepted v0.1 architecture is sufficient to begin implementation. No redesign is required before `CODEX_TASK_001_BOOTSTRAP`.

The items below are mandatory hardening requirements to be scheduled into the existing milestones. They are not reasons to delay Milestone 0 unless explicitly marked `M0`.

## 2. Untrusted-content / prompt-injection boundary

External content must be treated as untrusted data, not instructions.

Applies to:
- web pages;
- PDFs and office documents;
- imported notes/files;
- retrieved academic/public sources;
- model-generated tool output;
- copied text from third parties.

Requirements:
- source content is clearly separated from system/developer/task instructions;
- retrieved text cannot grant itself tools, permissions, authority, or broaden task scope;
- model tools are allowlisted per `BoundedTask`;
- no arbitrary shell/file/network capability is exposed to model output;
- tool arguments are validated locally against typed schemas and policy;
- suspicious instruction-like content from sources is preserved as evidence but not executed;
- high-impact actions require deterministic policy checks and, where material, human acceptance;
- prompt-injection tests become part of Research/Model Gateway regression suites.

Milestone mapping: M3 Model Gateway + M4 Research Engine + M6 Editorial workflows.

## 3. Network fetch / SSRF / hostile-source controls

`DirectWebSourceFetcher` must not become a generic server-side URL execution primitive.

Requirements:
- only `http`/`https` schemes;
- block loopback, link-local, private/internal IP ranges and local file schemes by default;
- re-resolve and validate redirect targets;
- bounded redirects/timeouts/response sizes;
- content-type validation;
- no implicit credential forwarding;
- cache provenance includes final resolved URL and content hash;
- downloaded active content is never executed.

Milestone mapping: M4 Research Engine.

## 4. Imported-file safety

Imported files are untrusted.

Requirements:
- file type/size limits;
- parse in least-privilege process/library path where practical;
- no macros/scripts/executable content;
- preserve original hash and provenance;
- sanitize extracted text/metadata boundaries;
- malformed parser inputs must fail safely;
- add fixture tests for hostile/corrupt files before broad format support.

Milestone mapping: M4 and Existing-Manuscript mode.

## 5. Source rights / permissions ledger

The existing `Source` licensing/access fields are necessary but not sufficient for publication reuse.

Add a lightweight rights/permissions dimension for source-derived material:
- access basis;
- quotation/reuse status when known;
- license/terms reference;
- excerpt/image/table reuse permission status;
- attribution requirement;
- territorial/time restrictions when applicable;
- human waiver/decision for unresolved publication-rights issues.

Literary Master release must distinguish `evidence sufficient` from `publication rights cleared` where reuse exceeds ordinary citation/reference use.

Milestone mapping: M4 Research/Claims + M9 Release.

## 6. Software supply-chain security

The public repository and desktop distribution need a reproducible dependency/security baseline.

Requirements:
- lockfiles/pinned dependency ranges appropriate to each ecosystem;
- automated dependency vulnerability scanning;
- secret scanning;
- dependency provenance/license inventory;
- SBOM generation for release candidates;
- no unsigned arbitrary binary downloads in normal runtime;
- third-party sidecar/build artifacts verified by checksum/source;
- security-sensitive dependency updates run regression tests before release.

Milestone mapping: M0 CI baseline (minimum scanning/lockfiles), strengthened before packaged release.

## 7. Signed release / update trust chain

Before external distribution:
- macOS app signing + notarization;
- Tauri updater signatures if updater enabled;
- update manifests over authenticated transport;
- rollback/recovery path for failed application update;
- application update must never silently migrate/destroy manuscript authority without backup and migration checks.

Milestone mapping: post-M0 packaging, mandatory before external beta/public distribution.

## 8. Database migration / backup disaster tests

Current backup requirements are correct; implementation must test failure cases, not only happy path.

Required test cases before real-book pilot:
- interrupted migration;
- corrupted/incomplete backup;
- restore to fresh install;
- schema downgrade policy explicitly defined;
- disk-full/write-failure behavior;
- crash during authority transition;
- backup taken while WAL is active;
- checksum mismatch detection;
- export/import does not silently lose provenance/history.

Milestone mapping: M1 Authority & persistence.

## 9. Performance / scale envelope

v0.1 needs explicit measured envelopes so local-first architecture is validated rather than assumed.

Representative test corpus should include at least:
- a full nonfiction manuscript at target upper planning length;
- thousands of `ManuscriptUnit` objects;
- hundreds/thousands of Claims/Evidence links;
- revision history and editorial findings large enough to exercise realistic project growth.

Measure:
- project open time;
- autosave/transaction latency;
- FTS latency;
- semantic retrieval latency;
- BookBench batch runtime;
- backup/restore time;
- memory usage;
- database size growth.

Do not optimize prematurely; use measured thresholds to decide if NumPy exact search/SQLite remain adequate.

Milestone mapping: M1 baseline measurements, M5 Memory, M7 BookBench, M10 pilot.

## 10. UX durability requirements

Before real-book pilot, the authoring surface must include:
- autosave with visible durable-state semantics;
- undo/recovery for non-authority local editing where technically safe;
- explicit save/commit semantics for authority transitions;
- crash recovery without manuscript loss;
- visible current authority vs proposed text;
- clear offline/provider-unavailable states;
- long-running task cancellation/resume where supported.

Milestone mapping: M2–M6.

## 11. Accessibility / localization baseline

The first product may be Russian-first, but UI architecture must not hard-code prose into domain logic.

Requirements:
- Unicode-safe text handling end-to-end;
- locale-aware UI strings and dates/numbers;
- keyboard-accessible critical acceptance/diff flows;
- readable focus states and basic screen-reader semantics;
- manuscript language is independent from application UI language.

This is a professional-product requirement, not a blocker for M0 skeleton.

## 12. Commercial/legal launch gate

Before BOOK OS brokers paid third-party AI/research services to end users, a separate launch review is mandatory for:
- provider terms/resale/pass-through rights;
- regional availability;
- personal-data/data-processing obligations;
- payment/tax/consumer obligations for target market;
- data residency/transfer requirements where applicable;
- copyright/publication rights workflow;
- privacy policy/consent/retention/deletion behavior.

This gate is not required for Owner-only local development with existing permitted credentials.

Milestone mapping: before commercial beta / provider brokerage.

## 13. Data lifecycle / purge semantics

Before multi-user/commercial product:
- define retention classes;
- user-controlled project deletion/export;
- purge derived indexes/caches when source data is deleted;
- define whether rejected editorial decisions are retained, anonymized, or deleted;
- private editorial corpus use must be opt-in/contractually supported for future model training/evals.

Milestone mapping: after v0.1 pilot, mandatory before general external use.

## 14. Release reproducibility and environment capture

Every `LiteraryMaster` must be reconstructible independently of current model availability.

Release manifest should capture:
- exact authority revision hashes;
- schema/app version;
- BookBench rubric/check versions;
- evaluation result references;
- source/evidence snapshot IDs;
- export generator version;
- no requirement to re-run an obsolete model to reconstruct the approved text.

Milestone mapping: M9.

## 15. Explicit non-blockers for Milestone 0

Do not delay Task 001 for:
- cloud account/auth;
- billing;
- Yandex/GigaChat implementation;
- full file-import sandbox;
- SBOM publication;
- notarized release;
- accessibility polish;
- commercial legal review.

Task 001 must, however, keep dependency lockfiles, loopback/session security, no external calls, no secrets, minimal CI and fresh-clone reproducibility.

## 16. Pre-implementation verdict

`GO_FOR_IMPLEMENTATION`.

The project has a coherent product contract, authority model, ontology, editorial workflow, evidence model, local-first technical architecture, model abstraction, Book Memory, BookBench, security baseline, regional/no-VPN requirement, recovery protocol, Audio Studio boundary and milestone sequence.

The hardening items in this document close the principal implementation-risk gaps found in the final audit and are mapped to existing milestones so they cannot be forgotten without expanding Milestone 0 unnecessarily.
