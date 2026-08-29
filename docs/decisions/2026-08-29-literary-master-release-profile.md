# Literary Master release evidence profile — 2026-08-29

**Status:** ACCEPTED IMPLEMENTATION CLARIFICATION

Task 010 Literary Master uses a fail-closed release evidence profile.

Before a Literary Master can be created for an exact BOOK BookBench snapshot:

- all seven M7 deterministic checks must have a successful run for that exact snapshot:
  - `deterministic.repetition`;
  - `deterministic.statistics`;
  - `deterministic.specificity`;
  - `deterministic.evidence`;
  - `deterministic.contract_structure`;
  - `deterministic.ai_prose_pathology`;
  - `deterministic.opening_ending_transition`;
- no finding on the exact snapshot may be `BLOCKING`;
- the snapshot must match the exact current Book Contract, Chapter Contracts and manuscript revisions selected for release;
- the current Claim set/state must not have outgrown the release snapshot;
- any material editorial finding in `WAIVED` state must have HUMAN waiver-state evidence;
- any open MAJOR/CRITICAL editorial finding blocks release.

This is the minimum deterministic release baseline. The real-book pilot may apply additional semantic, judge, pairwise, author-voice and human review gates without weakening this baseline.
