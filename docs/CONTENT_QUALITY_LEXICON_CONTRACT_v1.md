# Content Quality Lexicon Contract v1

Status: PROPOSED
Owner approval required before merge.

## Purpose

Provide one professional anti-junk vocabulary for BOOK OS and Audiobook Studio without creating a runtime dependency between the two applications.

The same user-added editorial rules must be visible to both applications on the same Mac. Each application keeps its own application-specific rules and its own enforcement semantics.

## Non-negotiable principle

A shared lexicon is not a global word ban.

Rules have an explicit match type, action and profile. Ordinary words such as `шум`, `опора`, `звучать`, `иллюзия`, `магия` may be legitimate in literal context and therefore default to `WARN`, not unconditional `BLOCK`.

The top-level prohibited AI pattern is:

> first artificially declare what a text, book, idea or phenomenon is NOT, instead of stating the precise thought directly.

Examples include `Эта книга не о том...`, `Эта книга не про X, а про Y`, `Это не про X. Это про Y`, and decorative `не X, а Y` framing.

## Profiles

### BOOK_PROSE

Used by BOOK OS generation and BookBench.

- `BLOCK`: generated prose must fail closed and be regenerated/revised before acceptance.
- `WARN`: surface to BookBench/human review; do not mechanically delete or replace the text.
- BOOK OS may use rules as generation constraints before a model call and deterministic checks after generation.

### AUDIOBOOK_PRE_SYNTHESIS

Used by Audiobook Studio before PREPARE/EXECUTE.

- Reuses the shared editorial vocabulary to catch prose-quality junk before money is spent on synthesis.
- Audiobook Studio MUST NOT silently rewrite the literary source to satisfy a rule.
- `BLOCK`: synthesis preparation is stopped and the user is shown the exact finding; the source/working copy must be deliberately corrected upstream or explicitly resolved by a human workflow.
- `WARN`: visible review item; does not mutate text.

### AUDIOBOOK_TTS_TECHNICAL

Audiobook Studio only.

Contains technical speech-preparation rules such as unexpected URLs, Markdown residue, prompt residue, placeholders, malformed control markers, unsupported pronunciation markup or other artifacts that should not reach TTS.

These rules MUST NOT be loaded into BOOK OS prose generation.

## System core and application overlays

There are three logical layers:

1. **Shared system core** — versioned Russian editorial rules in `contracts/content-quality-core-ru-v1.json`.
2. **Shared user rules** — private mutable local file, never committed to Git.
3. **Application overlay** — system rules specific to BOOK OS or Audiobook Studio.

Runtime must never download rules from GitHub or from the other application. Each application vendors the accepted shared system pack and records its contract version. This preserves offline operation and failure isolation.

## Shared private user store

Canonical macOS path:

`~/Library/Application Support/ContentQualityLexicon/user-rules-v1.json`

Optional override for tests/development:

`CONTENT_QUALITY_LEXICON_PATH=/absolute/path/user-rules-v1.json`

Requirements:

- JSON must validate against `contracts/content-quality-lexicon-v1.schema.json`.
- Only `origin=USER` entries may be written to the shared mutable file.
- Writes are atomic (`temp file -> fsync -> replace`).
- Cross-process writes use an advisory lock file next to the store (`user-rules-v1.json.lock`) so BOOK OS and Audiobook Studio cannot overwrite one another.
- Every successful mutation increments `revision` and updates `updated_at`.
- Duplicate detection is Unicode/case/whitespace normalized.
- A corrupt or schema-invalid file fails closed for mutation and produces a visible diagnostic; applications must not overwrite it with an empty file.
- No manuscript text, API key, project identity or private book data is stored in this file.

## User rule defaults

A rule entered through the BOOK OS `Словарь мусора` panel defaults to:

- `match_type=PHRASE`
- `action=BLOCK`
- `profiles=[BOOK_PROSE, AUDIOBOOK_PRE_SYNTHESIS]`
- `origin=USER`

The UI must allow the owner to change the action to `WARN` and scope a rule to book prose only or to both editorial profiles. TTS-technical rules are managed by Audiobook Studio and are never the default for a prose entry.

## Matching semantics

- `PHRASE`: normalized literal phrase match, case-insensitive; must not interpret the value as regex.
- `TERM`: token/word-boundary-aware match where possible for the language; do not match arbitrary substrings inside longer words.
- `REGEX`: system-authored only in v1. User-entered regex is forbidden in v1 to avoid accidental catastrophic or overbroad rules.

Findings must include at minimum:

- `rule_id`
- matched text
- start/end offsets
- action
- profile
- origin
- rationale when present

## Enforcement and provenance

BOOK OS:

- Planner/Writer receive applicable `BLOCK` rules as generation constraints.
- Generated text is deterministically rescanned before persistence/acceptance.
- BookBench surfaces both BLOCK and WARN findings with rule IDs.
- AI never self-approves a violation or an exception.

Audiobook Studio:

- The shared editorial scan runs before provider execution and before any paid request.
- The TTS technical scan runs on the exact prepared working text identity.
- Findings are bound to the source/prepared SHA so an approval cannot be reused after text changes.
- No rule may silently alter the canonical manuscript.
- A human exception, if supported, must record rule ID, exact text identity, actor, reason and timestamp; changing the text invalidates that exception.

## Synchronization behavior

Because both applications read the same shared private user file, a rule added in BOOK OS becomes visible to Audiobook Studio on its next lexicon reload. No copy/paste of individual words is required.

System rule changes remain versioned code changes. A system-pack bump requires updating both applications to the same accepted contract version; user rules remain intact.

## Security and privacy

- Shared user lexicon is local-only.
- It is excluded from repository commits, diagnostics bundles and model prompts except for the minimum rule text needed as a generation constraint.
- No cloud sync is introduced by this contract.
- No provider/model request is required to scan or manage the lexicon.

## Required tests

Both applications must have offline tests for:

1. schema validation;
2. atomic add/update/remove;
3. cross-process lock discipline;
4. duplicate normalization;
5. corrupt-file fail-closed behavior;
6. profile filtering;
7. BLOCK vs WARN behavior;
8. negative-first pattern detection;
9. no provider/model calls during lexicon tests;
10. exact text-identity invalidation for any Audiobook Studio resolution/approval.

## Compatibility rule

`schema_version=1` is the interoperability boundary. New fields may only be added compatibly or through a new schema version. An application that encounters a higher unsupported schema version must refuse mutation and show a clear upgrade-required message rather than downgrading or truncating the file.
