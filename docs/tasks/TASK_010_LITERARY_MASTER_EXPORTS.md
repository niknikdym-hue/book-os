# TASK 010 — LITERARY MASTER + EXPORTS

**Status:** ACTIVE
**Milestone:** Literary Master + exports
**Owner:** BOOK OS Central Brain
**Baseline:** `18338f94ee51e6f7149f5a3616408fb902f18895`
**Branch:** `brain/task-010-literary-master`

## WHY NOW

M0–M7 are accepted and merged. The former Russia/no-VPN provider milestone is SUPERSEDED and removed from the current program. The next launch-critical capability is a reproducible Literary Master that freezes exact human-approved authority state and produces derivative exports without mutating the master.

## GOAL

Implement:

`release gate -> immutable Literary Master manifest -> deterministic ordered rebuild -> reproducible export -> Audiobook Studio handoff manifest`

The Literary Master is authority-bearing release metadata, not an AI output and not an export file.

## NON-NEGOTIABLES

1. GitHub is source of truth for system authority; project SQLite authority remains source of truth for each book.
2. AI cannot approve or lock the Literary Master.
3. Only exact current authority revisions may enter a Literary Master.
4. No required unresolved BookBench BLOCKING dimension may remain at release.
5. No unresolved material editorial finding may be silently ignored; explicit human WAIVE remains visible provenance.
6. Rebuilding the same Literary Master must produce byte-identical canonical manuscript content and identical hashes.
7. Derivative exports never mutate authority or the master manifest.
8. Provider/model identity may appear in provenance but never becomes book authority.
9. Private manuscript text is never committed to this public repository.
10. Normal CI has zero paid/model/provider calls.

## SCHEMA — MIGRATION 0009

Because former PR #12 was closed without merge, accepted `main` ends at Alembic `0008`. Task 010 therefore uses revision `0009`, down_revision `0008`.

Persist:

### literary_masters
- `master_id`
- `book_id`
- `manifest_version`
- `manifest_hash`
- `book_title`
- `book_contract_revision_id/hash`
- `architecture_revision_id/hash`
- exact ordered chapter/unit manifest JSON
- canonical_content_hash
- release_gate_json
- human_actor
- created_at
- status (`LOCKED` only for accepted master rows)

Rows are append-only. Creating a new master never overwrites a prior one.

### literary_master_exports
- `export_id`
- `master_id`
- `format`
- `content_hash`
- `byte_length`
- `relative_path`
- `created_at`

Export evidence is append-only and non-authoritative.

## RELEASE GATE

Before master creation, fail closed unless:

- Book Contract current authority status is APPROVED or LOCKED;
- Architecture current authority status is APPROVED or LOCKED;
- every active chapter has an APPROVED/LOCKED Chapter Contract;
- every manuscript unit selected for release has a current authority head whose status is APPROVED or LOCKED;
- at least one manuscript unit exists;
- latest/current BookBench report for the exact release snapshot has no required BLOCKING dimensions;
- no stale mismatch exists between release revisions and the evaluated snapshot;
- unresolved editorial BLOCKING findings are absent unless explicitly human-waived under existing M6 authority;
- human actor is supplied explicitly for master creation.

Do not auto-approve manuscript units as part of release.

## ORDERING + CANONICAL CONTENT

Order deterministically by:
1. active chapter ordinal;
2. manuscript unit ordinal;
3. stable ID only as deterministic tie-breaker.

Canonical manuscript serialization v1:
- UTF-8;
- LF newlines;
- deterministic title/chapter headings;
- exact approved manuscript text, no model rewriting;
- exactly one trailing newline;
- no timestamps inside canonical manuscript bytes.

Hash with SHA-256.

## MANIFEST

Manifest must bind:
- book identity/title;
- Book Contract revision ID/hash;
- Architecture revision ID/hash;
- each chapter ID/ordinal/title/contract revision ID/hash;
- each manuscript unit ID/ordinal/revision ID/hash/content hash;
- BookBench snapshot/report evidence identity;
- editorial release-gate evidence summary;
- canonical manuscript SHA-256;
- schema/manifest version.

Canonical manifest hash excludes mutable export evidence and timestamps where they would break deterministic identity.

## EXPORTS

Implement at minimum Markdown export from exact Literary Master canonical bytes.

Store under the project directory, e.g. `exports/<master_id>/manuscript.md`, with traversal-safe paths.

Repeated export for the same master/format must reproduce identical bytes/hash.

No export operation may modify any authority/revision/master row.

## AUDIOBOOK STUDIO HANDOFF

Create a deterministic JSON handoff manifest from the Literary Master containing only the production identity needed by the separate Audiobook Studio domain:
- BOOK OS book/master IDs;
- working/final title;
- canonical manuscript hash;
- ordered chapter/unit identities and revision hashes;
- export path/hash;
- handoff schema version.

Do not merge Audiobook Studio state or QA authority into BOOK OS.

## API

Authenticated Local Core endpoints:
- release readiness/gate for a book;
- create Literary Master (explicit human actor);
- list/get Literary Masters;
- export Markdown for exact master;
- get handoff manifest.

No endpoint auto-approves manuscript authority.

## DESKTOP

Add a minimal Literary Master panel/workspace:
- readiness state and exact blockers;
- current/latest master identity/hash;
- explicit Create Literary Master control requiring human actor/name;
- Markdown export action after master exists;
- no misleading RELEASED state before gate passes.

## BACKUP

Advance backup compatibility through `0009` and preserve restore compatibility for supported older schemas.

## ACCEPTANCE

1. fresh DB migrates 0008 -> 0009;
2. incomplete/unapproved book fails release gate with structured reasons;
3. unresolved BookBench BLOCKING fails release;
4. stale/non-current evaluated revisions fail release;
5. unresolved editorial BLOCKING fails unless existing explicit human waiver applies;
6. master creation requires explicit human actor;
7. master uses only exact current APPROVED/LOCKED revisions;
8. master manifest is append-only/immutable;
9. identical authority/evidence state yields identical canonical content hash and deterministic manifest identity;
10. changed revision produces a different master identity/hash; prior master remains unchanged;
11. Markdown export bytes are deterministic and hash-verified;
12. export cannot mutate authority or master;
13. handoff manifest deterministic and domain-separated;
14. authenticated API tests pass;
15. desktop tests cover readiness/master/export states;
16. backup/restore through 0009 passes;
17. Ruff format/check, mypy, full pytest green;
18. desktop lint/typecheck/Vitest/build/audit green;
19. Rust cargo test/check green;
20. secret scan green;
21. normal CI provider/model/paid calls = 0;
22. no M10 real-book private content enters public Git.

## UNLOCKS NEXT

Acceptance + merge unlocks the real Business Nonfiction pilot from Idea to Literary Master.