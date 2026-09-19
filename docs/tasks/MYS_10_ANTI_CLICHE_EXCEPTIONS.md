# MYS-10 — ANTI-CLICHE / EXCEPTION REGISTRY

**Status:** IMPLEMENTATION / STACKED DRAFT  
**Date:** 2026-09-19  
**Repository:** `niknikdym-hue/book-os`  
**Base:** MYS-09 exact GREEN head `2985ad3742a8aba0a28c5cd4b4bd29fcf06e36ea`  
**Branch:** `codex/mys-10-anti-cliche-exceptions-20260919`

## Purpose

Make the anti-cliche standard executable rather than advisory.

MYS-10 prevents a technically coherent mystery from entering Writing while it still depends on blocked stock devices, cheap supernatural shorthand, or unresolved high-risk/template findings.

It does not attempt to detect literary cliches using deterministic string matching alone. Contextual detection is semantic editorial evidence; deterministic code validates the rules, provenance, exceptions and gate semantics.

## Enforcement levels

- `BLOCKED_BY_DEFAULT`
- `HIGH_RISK_TROPE`
- `STYLE_PATHOLOGY`
- `SERIES_COLLISION`

### BLOCKED_BY_DEFAULT

The exact detected use is blocked unless:

- that rule explicitly permits exception;
- an `AntiClicheException` exists for the exact finding ref;
- exception points to the same exact snapshot and rule-pack revision;
- exact proposed use is unchanged;
- reinvention rationale, familiarity, transformation and alternatives are recorded;
- decision is `ACCEPT`;
- human decision ref is verified;
- for series books, exception cites the exact current Series Brain ref.

### HIGH_RISK_TROPE / STYLE_PATHOLOGY

A BLOCKING finding cannot be human-waived.

A MAJOR finding may proceed only with verified human disposition when policy permits.

MINOR/NOTE remain diagnostics.

### SERIES_COLLISION

AntiClicheException has no authority to clear Series Brain collisions.

A SERIES_COLLISION finding blocks and must be resolved through MYS-09.

## Exact exception scope

An exception is not a permission to use a trope forever.

It is bound to:

- exact rule code;
- exact finding hash;
- exact target snapshot;
- exact proposed use;
- exact rule-pack revision;
- exact current Series Brain ref when applicable.

Changing the story/use invalidates the old exception.

## Machine rule catalog

MYS-10 adds the default machine catalog:

`services/local-core/src/book_os_core/mystery_anti_cliche_catalog.py`

It contains 50+ coded rules from the approved policy, including explicit blocked rules for:

- inherited old mansion / house-as-evil-gateway;
- dusty archive, letters, diaries and old newspaper explanation;
- bookcase secret room;
- haunted antique defaults;
- generic ghost-presence signals;
- convenient cryptic ghost;
- generic occult symbols / Latin curse explanation;
- all-knowing keeper withholding information;
- undeclared ritual solution;
- chosen-by-bloodline;
- convenient psychic;
- repeated dead-person call/message as a fixed series formula without a materially original rule system;
- amnesia used to hide POV knowledge;
- psychiatric diagnosis as universal motive/explanation;
- confession replacing proof;
- late decisive forensic fact;
- convenient camera/network/phone failure;
- coincidence identifying culprit;
- villain explaining entire plan;
- supernatural entity replacing human motive/agency.

It also encodes high-risk investigator, culprit, plot and relationship devices plus AI/template prose pathologies.

The catalog is public generic editorial policy; it contains no unpublished story content.

## Scan provenance

Each AntiClicheRun binds:

- book;
- stage;
- exact target snapshot ref/hash;
- exact rule-pack ref/hash;
- Writer executor identity;
- independent semantic evaluator identity/class;
- exact rubric;
- scan evaluation ref;
- findings;
- exceptions;
- Series Brain ref when applicable.

The scan evaluation must resolve to a shared immutable `VerifiedEvaluationArtifact` with exact purpose:

`ANTI_CLICHE_SCAN:<stage>:<rule_pack_ref>`

It must be SUCCEEDED/current and bound to the exact target snapshot.

Deterministic-only evaluation cannot certify contextual anti-cliche review.

Writer cannot be the sole semantic anti-cliche judge.

## Findings

Each finding records:

- rule code;
- severity;
- observation;
- exact proposed use;
- exact target object refs;
- evidence refs;
- exact scan evaluation ref;
- optional human disposition.

The finding ref is content-hashed together with the target snapshot.

This prevents an old exception from being silently reused after material story changes.

## Human authority

Only a verified human decision can ACCEPT an exception.

AI/model output may:

- identify a cliche;
- propose reinvention;
- explain alternatives;
- recommend REWORK.

It cannot create human approval by writing a string that looks like a human decision ref.

## MYS-05 integration

MYS-05 no longer accepts “some anti-cliche evaluation ref” as sufficient.

`ExternalWritingReadiness` now requires:

- `anti_cliche_qualified=true`;
- exact `anti_cliche_evaluation_ref`;
- no unresolved blocked/major codes.

The standard bridge:

`readiness_with_anti_cliche()`

imports an exact MYS-10 result.

A failed result clears a previously supplied stale green ref.

The exact AntiCliche ref becomes part of WritingAdmissionToken evaluation provenance.

## Version-bound output

Successful run returns:

`anti-cliche:<hash>`

The ref binds:

- policy;
- target snapshot;
- rule pack;
- scan evaluator/rubric;
- findings;
- exact exceptions;
- series provenance.

`verify_anti_cliche()` recomputes and rejects stale evidence.

## Machine contracts

MYS-10 adds:

- `contracts/mystery-os/anti_cliche_rule_pack.schema.json`;
- `contracts/mystery-os/anti_cliche_run.schema.json`.

## Cost boundary

This validator and default catalog perform zero model/provider calls.

A future semantic anti-cliche scan may be produced by:

- a standard independent editor when adequate;
- a bounded premium/Astra/Agents review when the decision is high-impact or ambiguous.

Deterministic code remains responsible for versioning, exception authority, staleness and gate enforcement.

## Deliberately OUT

- no real semantic model scan;
- no real `Линия 112` exception;
- no automatic human approval;
- no DB/API/UI;
- no paid/provider call;
- no merge authorization.

## Acceptance

MYS-10 is technically GREEN only when tests prove:

- default rule catalog contains required prohibited shortcuts;
- clean exact scan passes;
- blocked-by-default finding blocks without exact exception;
- verified exact ACCEPT exception may clear only that finding;
- model-invented human ref cannot clear;
- REWORK/REJECT do not clear;
- use/snapshot/rule-pack changes invalidate exception;
- series exception must cite current Series Brain;
- SERIES_COLLISION cannot be waived here;
- high-risk BLOCKING cannot be waived;
- high-risk MAJOR requires verified disposition;
- scan provenance exact/current/independent;
- deterministic-only scan cannot certify contextual anti-cliche review;
- rule-pack/snapshot changes invalidate old run;
- unknown rule fails closed;
- invalid rule pack cannot make series collision waivable;
- MYS-05 blocks fake/manual unqualified anti-cliche refs;
- qualified MYS-10 bridge enters WritingAdmissionToken;
- inherited MYS-01..09 tests remain GREEN;
- Ruff, strict mypy, full pytest, Desktop/Tauri/native/secret scan pass;
- provider/model/paid calls = 0.

Technical GREEN does not authorize manuscript writing.
