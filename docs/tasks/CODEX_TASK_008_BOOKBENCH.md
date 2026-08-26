# CODEX TASK 008 — BOOKBENCH v0.1

**Status:** READY  
**Milestone:** M7 — BookBench v0.1  
**Owner:** BOOK OS Central Brain

## WHY NOW

M0–M6 are accepted and merged. BOOK OS can create and draft a real Business Nonfiction book, verify factual Claims, retrieve current whole-book context, diagnose editorial problems, create exact-base proposals and preserve human decisions. The next critical-path capability is a reproducible internal evaluation system that can measure quality risks against exact revisions, compare model/configuration candidates and produce actionable evidence without pretending to predict commercial success.

## GOAL

Implement BookBench v0.1 as a versioned evaluation layer:

`exact revision snapshot → versioned checks/evaluators → EvaluationRun → actionable findings/metrics → optional M6 editorial handoff → human review`

BookBench is **diagnostic derived state, never authority**. It cannot edit manuscript/Contract authority, accept proposals, waive findings or hide a blocking dimension behind an average.

## BASELINE / AUTHORITY

Read current `main`, then:

- `BOOKBENCH_v0.1.md`;
- `CORE_ONTOLOGY.md`;
- `EDITORIAL_PROTOCOLS_v0.1.md`;
- `MODEL_GATEWAY_v0.1.md`;
- `BOOK_MEMORY_v0.1.md`;
- `RESEARCH_AND_CLAIMS_v0.1.md`;
- `TECHNICAL_ARCHITECTURE_v0.1.md`;
- `IMPLEMENTATION_ROADMAP_v0.1.md`;
- `TASK_EXECUTION_PROTOCOL_v0.1.md`;
- `PROJECT_STATE.md`;
- this contract.

Required prior milestone: Task 007 / M6 ACCEPTED AND MERGED.

Normal CI external/model/judge calls = 0. Paid calls = 0.

## NON-NEGOTIABLE PRODUCT RULES

1. No single magic overall book score (no “87/100”).
2. Every evaluation references exact target revision IDs/hashes and versioned check/rubric/evaluator configuration.
3. Evaluation output never mutates authority directly.
4. Findings must be actionable: dimension/category → exact location → measured evidence → severity → confidence → recommended action/status.
5. Deterministic signals are not semantic truth. Semantic similarity is not contradiction proof. LLM judge output is not human authority.
6. AI-prose pathology reports concrete measured patterns/locations; it must not claim probabilistic authorship detection.
7. Author Voice Fingerprint is diagnostic and versioned; it must not automatically homogenize prose.
8. Critical judge evidence is not release-grade if the same provider/model/config both produced and solely judged the output without independent review; independence state must be explicit.
9. Project evaluation datasets/decision corpus remain private in project SQLite. Synthetic fixtures only may live in the public repository.
10. No M8 regional/provider-launch implementation in M7.

## IN SCOPE

### A. Persistence / migration `0008`

Add only M7 derived evaluation persistence required for:

#### `evaluation_runs`

Minimum fields:
- stable `evaluation_id`;
- book ID;
- check/rubric ID + version;
- BookBench dimension;
- evaluator class `DETERMINISTIC | SEMANTIC | LLM_JUDGE | PAIRWISE | HUMAN_LABEL`;
- exact target snapshot/config references;
- provider/model/config identity when applicable;
- prompt/rubric ID/version/hash when applicable;
- dataset snapshot/version when applicable;
- independence state;
- status;
- measured latency/cost/usage metadata;
- created/completed timestamps.

#### `evaluation_findings`

Minimum fields:
- stable finding ID;
- evaluation ID;
- dimension/category;
- target object/unit/chapter and exact revision ID/hash;
- measured evidence/locations;
- severity `INFO | ATTENTION | BLOCKING`;
- confidence;
- recommended action;
- status/acknowledgement metadata when needed.

Evaluation finding diagnostic content is immutable; rerun/replacement creates a new EvaluationRun/finding rather than rewriting history.

#### metrics

Persist structured per-run/per-target metrics needed for distributions, counts and comparisons. Do not collapse them into one universal score.

#### versioned evaluation datasets

Add immutable project-private dataset snapshots/cases derived from M6 decision corpus and/or explicit synthetic/manual labels:
- snapshot ID/version/hash;
- exact input/base revision references;
- task/role/dimension;
- candidate/proposal refs/content hashes;
- human decision/label/reason when available;
- final accepted revision when available;
- provenance/timestamp.

#### role scorecards

Persist derived comparison runs/scorecards by role/config/dataset version with per-dimension metrics, severe-failure counts, latency/cost and pass/attention/blocking counts. No universal model leaderboard score.

### B. Versioned check registry

Implement a local code/data registry of BookBench checks/rubrics with stable IDs and versions.

At minimum the registry covers these dimensions:

1. `BOOK_CONTRACT_FULFILLMENT`;
2. `CHAPTER_CONTRACT_FULFILLMENT`;
3. `SEMANTIC_NOVELTY`;
4. `IDEA_REPETITION`;
5. `CONTRADICTION_INCONSISTENCY`;
6. `THOUGHT_DENSITY`;
7. `SPECIFICITY_GENERICNESS`;
8. `EVIDENCE_UNSUPPORTED_CLAIMS`;
9. `AUTHOR_VOICE`;
10. `AI_PROSE_PATHOLOGY`;
11. `OPENING_ENDING_TRANSITION`;
12. `CROSS_BOOK_COHERENCE`.

A dimension may have multiple checks/evaluator classes. Registry version/hash is stored with every run.

### C. Exact evaluation snapshots

BookBench evaluates exact canonical snapshots, not “whatever is current later”.

Implement deterministic snapshot construction for:
- selected current ManuscriptUnit;
- selected current chapter;
- current whole book.

Snapshot manifest includes exact current Book Contract, Chapter Contracts, ordered current ManuscriptUnit revisions/hashes, relevant current Claims/Evidence state, and Book Memory/index config refs when a semantic check depends on them.

If authority changes after snapshot creation, old EvaluationRun remains reproducible and visibly non-current; it is never silently retargeted.

### D. Deterministic / lexical / statistical checks

Implement conservative, measured checks with explicit locations/examples. At minimum:

#### Repetition / structural signals
- repeated exact/normalized phrases or n-grams across current manuscript units;
- repeated sentence starts/templates;
- repeated paragraph/conclusion transition templates;
- TODO/placeholder markers;
- excessive rhetorical-question count/rate relative to configured threshold;
- repeated artificial enumerations/three-part constructions as a measurable signal, not an automatic defect.

#### Length/density metrics
- sentence-length distribution;
- paragraph-length distribution;
- lexical diversity / repeated-term concentration or another documented deterministic thought-density proxy;
- concrete-number/proper-noun/example-like specificity signals vs empty abstraction markers under documented conservative heuristics.

#### Evidence checks
- count/list material Claims in `UNREVIEWED | DISPUTED | UNSUPPORTED`;
- stale Claim-to-manuscript revision binding;
- unresolved Claim/Evidence blockers.

#### Contract/transition structural checks
- approved Chapter Contract with no current manuscript content;
- required claims/requirements with no conservative lexical trace (clearly labeled lexical signal);
- opening/ending/transition presence/shape checks where deterministic.

Deterministic check output cannot claim semantic fulfillment merely from token overlap.

### E. AI-prose pathology detector v0.1

Implement a deterministic diagnostic detector that reports measured occurrences/locations, not an “AI probability”. Initial patterns include at least:

- false-contrast templates (`не X, а Y` / `это не про X ...` patterns where detectable);
- pseudo-aphoristic short declarative runs;
- artificial triads/list-of-three overuse;
- repeated paragraph architecture/conclusion templates;
- rhetorical-question excess;
- repeated generic AI-like transition phrases maintained in a versioned local pattern registry;
- over-symmetrical repeated sentence openings.

Every finding stores examples/locations and the detector version. Pattern occurrence is a review signal, not automatic rejection.

### F. Author Voice Fingerprint baseline

Implement a versioned, derived Author Voice Fingerprint from **explicitly selected exact reference manuscript revisions**.

Capture measurable features such as:
- sentence-length and paragraph-length distributions;
- punctuation tendencies;
- sentence-start/syntactic proxy patterns;
- first-person/author-presence rate;
- rhetorical-question rate;
- concrete-number density;
- transition-pattern frequencies;
- selected construction blacklist/allowed-tolerance metadata.

Fingerprint stores exact reference revision IDs/hashes + extractor version/hash.

Implement diagnostic comparison of a target exact revision/chapter against a selected fingerprint and return feature deltas/locations. Do not auto-rewrite text to match the fingerprint and do not turn fingerprint similarity into a magic quality score.

### G. Semantic checks using existing M5 infrastructure

Reuse M5 Book Memory/EmbeddingGateway/local exact cosine; do not add another vector database.

Implement bounded semantic checks including at minimum:

- paraphrased/semantic idea-duplication candidates across current ManuscriptUnits;
- chapter semantic novelty relative to other current chapters/units;
- Book Contract / Chapter Contract semantic coverage candidates;
- semantic drift candidate between a target chapter and its approved Chapter Contract.

Rules:
- semantic similarity produces candidates/signals only;
- it cannot alone assert contradiction, factual truth or Contract fulfillment;
- all results retain exact revision references and embedding config identity;
- incompatible/stale embedding config is a visible gate, not silently mixed.

Normal CI uses deterministic fake embeddings only.

### H. Bounded LLM judge / pairwise framework through existing Model Gateway

Do **not** create a second provider-specific gateway.

Boundedly generalize the accepted M3 Model Gateway structured-output path so it can support additional typed task/role values while preserving `SECTION_DRAFT/WRITER` behavior and tests.

Add BookBench task types/roles:
- `BOOKBENCH_JUDGE / EVALUATOR`;
- `BOOKBENCH_PAIRWISE / EVALUATOR`.

Add versioned prompt/rubric templates, at minimum:
- `bookbench_judge_v1`;
- `bookbench_pairwise_v1`.

Judge request must carry:
- exact target snapshot/revision refs;
- one bounded BookBench dimension/rubric;
- untrusted candidate/manuscript text as data;
- output JSON schema;
- provider/model/config identity;
- max-output/cost guard metadata.

Structured judge output contains bounded dimension verdict `PASS | ATTENTION | BLOCKING`, evidence-backed findings/locations, confidence, rationale and recommended action.

Pairwise output contains `A | B | TIE`, bounded dimension(s), evidence/rationale and confidence.

Pairwise rules:
- candidate labels are blind A/B;
- order is deterministically shuffled from a stored seed so runs are reproducible;
- raw candidate IDs are not exposed to the judge payload beyond opaque A/B;
- stored result maps A/B back to candidate/config IDs after evaluation.

Normal CI uses deterministic fake structured model outputs only. OpenAI development adapter remains mocked in CI; no live/paid calls.

### I. Judge independence gate

For critical/release-grade judge evidence, store and calculate:

- writer/candidate provider/model/config identity when known;
- judge provider/model/config identity;
- `INDEPENDENT | SAME_CONFIG | UNKNOWN`.

`SAME_CONFIG` or `UNKNOWN` may be diagnostic but cannot masquerade as independent release-grade evidence.

No brand/provider is exempt from this rule.

### J. Evaluation datasets from real editorial decisions

Implement explicit creation of immutable dataset snapshots from M6 Decision corpus.

At minimum, accepted/rejected/request-revision/waived editorial cases can become labelled cases containing exact base revision/proposal/final revision references + human reason.

Rules:
- dataset snapshot is immutable and hash-versioned;
- later decisions create a new snapshot/version;
- user manuscript text/data stay in project SQLite and are never committed to the public repo;
- synthetic repo fixtures prove behavior in CI.

### K. Model/config comparison + role scorecards

Implement a bounded comparison runner that evaluates at least two model/configuration candidates against the same immutable dataset snapshot.

For M7 CI, use two deterministic fake configurations that intentionally differ on representative outputs so regression logic is testable.

Scorecard reports by role/dimension:
- labelled-case agreement / preference outcome where meaningful;
- PASS/ATTENTION/BLOCKING counts;
- severe-failure count;
- latency/cost/usage;
- independence state;
- dataset version/hash;
- configuration identity.

Do not compute a single magic model quality number.

### L. BookBench report/read model

Expose a grouped report for one exact snapshot/run set:

`dimension → state PASS/ATTENTION/BLOCKING → findings → location → evidence → severity → confidence → recommended action`

Also show:
- check/evaluator version;
- exact target revisions;
- current/non-current status;
- judge independence state when relevant;
- run latency/cost/usage;
- unresolved blocking dimensions.

A report may summarize dimension status but must not average blockers away.

### M. Optional explicit handoff to M6 Editorial Finding

Allow an explicit HUMAN/SYSTEM action to copy a selected BookBench finding into the existing M6 typed EditorialFinding workflow, preserving source EvaluationRun/finding IDs in evidence/provenance.

Rules:
- not automatic;
- does not create a ChangeProposal automatically;
- does not accept/waive anything;
- exact current target baseline is revalidated at handoff time;
- stale eval finding cannot silently become a current editorial finding.

### N. Minimal authenticated API + desktop UI

Expose authenticated local operations to:
- build/inspect exact evaluation snapshot;
- run deterministic BookBench checks;
- run semantic checks with an explicitly ready embedding config;
- run fake/dev LLM judge/pairwise through the accepted Model Gateway;
- create/list/select Voice Fingerprints from exact refs;
- inspect AI-prose pathology findings;
- create immutable decision-dataset snapshot;
- compare at least two configurations / inspect scorecard;
- inspect grouped BookBench report;
- explicitly hand off a selected eval finding to M6 EditorialFinding.

Desktop adds one `BookBench` workspace:
- target/scope selection;
- run deterministic / semantic / judge / pairwise controls;
- no overall score;
- dimensions with `PASS | ATTENTION | BLOCKING`;
- actionable finding cards with exact locations/evidence;
- Voice Fingerprint creation/comparison;
- AI-prose pathology examples;
- dataset version and configuration comparison/scorecard;
- explicit “Send to Editorial Inbox” action;
- visible current/non-current and independence state.

### O. Backup/regression

Advance schema compatibility to `0008` while preserving supported older-backup restore/migrate-forward behavior.

M0–M6 regressions remain green.

## STRICT OUT OF SCOPE

- commercial bestseller prediction;
- single overall book/model quality score;
- automatic manuscript rewrite based on BookBench;
- automatic proposal acceptance/waive;
- hidden LLM judge authority;
- mandatory live/paid judge calls;
- M8 Yandex/GigaChat/Russia provider lane;
- provider promotion to production as part of M7;
- Literary Master/export/audio handoff;
- cloud/accounts/billing/sync;
- remote vector database/ANN infrastructure;
- publishing private user evaluation corpus to the software repository.

## REQUIRED ACCEPTANCE

1. Fresh DB migrates `0001→0008`; existing M6 DB upgrades to M7.
2. Evaluation snapshot records exact canonical target revision IDs/hashes and remains reproducible after later authority change.
3. EvaluationRun stores check/rubric/evaluator versions/config and never mutates authority.
4. Evaluation finding stores exact location/evidence/severity/confidence/recommended action and immutable diagnostic content.
5. Report has per-dimension PASS/ATTENTION/BLOCKING and **no overall magic score**.
6. Deterministic repetition check finds a known duplicate and exact locations.
7. Statistical checks produce reproducible sentence/paragraph/rhetorical-question metrics.
8. Evidence check flags known material `UNREVIEWED/DISPUTED/UNSUPPORTED` Claims without changing Claim state.
9. AI-prose pathology detector finds known versioned fixture patterns with concrete locations and makes no AI-authorship probability claim.
10. Voice Fingerprint created from explicit exact reference revisions is versioned/reproducible; target comparison returns measurable feature deltas without editing text.
11. Fake-embedding semantic duplication/novelty/contract-coverage checks retain exact revision/config identity and treat results as candidates only.
12. Stale/incompatible semantic config is rejected/visible.
13. Existing `SECTION_DRAFT/WRITER` Model Gateway regression remains green after bounded structured-output generalization.
14. BookBench judge request/response schema is deterministic, versioned and normal-CI fake-only.
15. OpenAI structured judge HTTP path is mocked only, `store=false`, secret-safe and no live call.
16. Pairwise A/B ordering is blind, reproducible from stored seed and correctly maps result back to candidates.
17. Same writer/judge config is marked `SAME_CONFIG` and cannot masquerade as independent release-grade evidence.
18. Immutable dataset snapshot can be built from known synthetic M6 decision cases and changing corpus creates a new version/hash.
19. Two deterministic fake model/configurations are compared on the same dataset and produce per-dimension role scorecards/regression evidence without one universal score.
20. Explicit BookBench → M6 finding handoff revalidates current exact baseline and never auto-creates/accepts a proposal.
21. Authenticated API boundary remains intact.
22. Desktop component test covers BookBench run → dimension finding/evidence → explicit send to Editorial Inbox; separate test covers scorecard/no-overall-score presentation.
23. Python Ruff/mypy/pytest green.
24. TypeScript lint/type/test/build green.
25. Rust cargo test/check green.
26. secret/dependency scans green.
27. normal CI external/model/judge calls = 0; paid calls = 0.
28. no M8+ scope.

## STOP CONDITIONS

Stop and surface a Central Brain/Owner decision rather than broadening scope if implementation would require:

- a single magic overall quality score;
- BookBench mutating manuscript/Contract authority;
- AI/system accepting editorial changes;
- mandatory paid/live judge API for normal operation/tests;
- treating semantic similarity as factual truth/contradiction proof;
- hiding same-config judge dependence;
- publishing private manuscript/eval datasets;
- implementing M8 provider-launch/regional routing to make M7 work.

## UNLOCKS NEXT

Central Brain ACCEPT of M7 unlocks M8 — Russia-ready/no-VPN provider lane.

Do not start M8 before M7 acceptance/merge.
