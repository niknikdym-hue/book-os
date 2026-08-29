# Literary Master migration numbering — 2026-08-29

**Status:** ACCEPTED IMPLEMENTATION CLARIFICATION

Canonical `main` at Task 010 activation ends at Alembic revision `0008` (M7 / BookBench).

The former Russia/no-VPN M8 work existed only in closed, unmerged PR #12. Its branch-local `0009` migration never entered canonical `main` and is historical/superseded implementation only.

Therefore Task 010 / Literary Master correctly uses:

- `revision = "0009"`
- `down_revision = "0008"`

Do not reserve or skip schema revision numbers for migrations that never entered canonical `main`.
