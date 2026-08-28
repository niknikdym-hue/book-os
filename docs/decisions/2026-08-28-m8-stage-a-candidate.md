# M8 Stage A acceptance — 2026-08-28

**Status:** ACCEPTED — Stage A implementation only

Task 009 / M8 Stage A is accepted on PR #12.

Accepted exact implementation/evidence HEAD before this authority record:
`1219fa07df3185b9aaf365ef2dff59c524251a8c`

Authoritative GitHub Actions run:
`33180705731`

Evidence:
- migration: `0009`, revises accepted M7 `0008`;
- Ruff format/check: PASS;
- mypy: PASS, 22 source files;
- pytest: PASS, 82/82;
- desktop lint/typecheck: PASS;
- desktop Vitest: PASS, 7 files / 11 tests;
- desktop production build: PASS;
- desktop production dependency audit: PASS, no known vulnerabilities;
- Rust/Tauri `cargo test --locked`: PASS;
- Rust/Tauri `cargo check --locked`: PASS;
- secret scan: PASS;
- normal CI external/provider/model calls: `0`;
- normal CI paid calls: `0`;
- `verify=False` production path: absent;
- M9/M10 scope: not started.

Stage A acceptance covers Task 009 acceptance items 1–20: M8 schema/backup compatibility, persisted capability/policy/probe/promotion evidence, fail-closed RU routing, OpenAI exclusion from mandatory RU runtime, current mocked Yandex and GigaChat generation/embedding protocol adapters, role-specific promotion gates, deterministic eligible fallback with provenance, explicit live-run guard, authenticated secret-safe API, and Provider Lane desktop unavailable/availability presentation.

This decision DOES NOT accept M8 as a whole and DOES NOT authorize a Russia-ready product claim.

Stage B live promotion acceptance items 21–30 remain mandatory. No live/paid Stage B execution has occurred. PR #12 remains draft and must not be merged before final M8 acceptance.
