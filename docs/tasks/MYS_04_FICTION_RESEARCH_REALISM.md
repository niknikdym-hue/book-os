# MYS-04 — FICTION RESEARCH LEDGER / REALISM / RESEARCH STALENESS

**Status:** IMPLEMENTATION / STACKED DRAFT  
**Date:** 2026-09-18  
**Repository:** `niknikdym-hue/book-os`  
**Base:** `codex/mys-03-narrative-fairness-20260918` @ `59768477c7634612cd4d2b757a0d82877e51b2de`  
**Branch:** `codex/mys-04-fiction-research-20260918`

## Purpose

Turn Fiction Research & Realism from documentation into a fail-closed, versioned fiction-authority layer **without creating a second research/source system**.

BOOK OS remains the owner of generic Source/Evidence primitives.

MYS-04 owns only:

- fiction-specific research conclusion;
- risk class;
- jurisdiction/time applicability;
- exact shared source/evidence refs;
- intentional fictionalization decision;
- freshness;
- expert/risk review state;
- exact dependencies from story authority to the accepted research conclusion;
- propagation of external research invalidation to dependent story authority.

## Core architecture

### Shared research stays shared

MYS-04 does **not** create:

- a second source table;
- a second evidence table;
- a separate search provider stack;
- a second citation system;
- web/provider calls inside deterministic validators.

`SharedResearchEvidence` is only a read-only projection of existing BOOK OS research metadata needed for deterministic checks.

### Research conclusion becomes versioned authority

A `FictionResearchItem` is material editorial authority when story logic consumes it.

Its authority kind is:

`FICTION_RESEARCH_ITEM`

Story authority binds to its exact accepted revision. Runtime ledger projections are also keyed by exact `revision_id`, never only by research entity ID, so an unaccepted working draft cannot displace the governing conclusion:

`CaseSolution -> FictionResearchItem@revision`

`CaseTimeline -> FictionResearchItem@revision`

`ClueLedger -> FictionResearchItem@revision`

`SceneContract -> FictionResearchItem@revision`

A new accepted research conclusion therefore triggers the existing MYS-01 structural staleness graph instead of inventing a second invalidation engine.

## Risk classes

- `R0` — invented/self-contained;
- `R1` — low-risk texture;
- `R2` — material realism;
- `R3` — plot-critical factual dependency;
- `R4` — safety/legal/reputationally sensitive.

## Deterministic gates

### Context

When the item declares jurisdiction/time dependence, the relevant values are mandatory.

The validator does not guess whether a fact is jurisdictional. Research decomposition must make the scope explicit.

### Disposition

`RESEARCH_NEEDED`:
- R0 -> NOTE;
- R1 -> MAJOR;
- R2/R3/R4 -> BLOCKING.

`REJECTED` is BLOCKING.

`QUALIFIED`:
- R2 may proceed only when uncertainty is explicitly marked safe for scene/case logic;
- R3/R4 cannot govern plot-critical writing while only QUALIFIED.

### Evidence

R2/R3/R4 accepted conclusions require exact shared evidence refs.

Material evidence must include at least one `FULL_SOURCE_INSPECTED` source. Evidence catalog key, evidence identity and declared source relationship must all agree.

A VERIFIED R2/R3/R4 conclusion must have active `SUPPORTS` evidence.

For VERIFIED R3/R4 — and for the real-world baseline of FICTIONALIZED R3/R4 — the deterministic minimum is:

- one strong inspected PRIMARY supporting evidence; **or**
- two independent inspected material sources of MODERATE/STRONG strength.

This is a minimum admission rule, not a claim that all research questions can be judged mechanically.

Active contradicting evidence requires an explicit contradiction resolution before VERIFIED use.

### Confidence

VERIFIED R2/R3/R4 cannot use UNKNOWN/LOW confidence.

VERIFIED R3/R4 require HIGH confidence.

### Intentional fictionalization

`FICTIONALIZED` requires:

- explicit intentional-fictionalization flag;
- rationale;
- prior fictionalization decision ref;
- for R2/R3/R4, documented real-world baseline.

An error cannot be relabeled fictionalization after the fact without changing authority.

### Freshness

Runtime normalized freshness modes:

- `STABLE`;
- `VALID_UNTIL`;
- `RECHECK_REQUIRED`.

Expired/recheck-required research is externally stale even when story text and the research authority hash have not changed.

### R4

R4 requires:

- explicit risk-review ref;
- completed expert review.

This does not replace safety/legal policy; it is an editorial readiness gate.

## External research staleness

Two staleness mechanisms intentionally coexist:

1. **structural revision staleness** — a new accepted `FICTION_RESEARCH_ITEM` revision is handled by MYS-01 exact-revision dependency logic;
2. **external-state staleness** — expiry, superseded evidence or other current validation failure is propagated by MYS-04 over effective authority dependencies.

This distinction matters: evidence may become invalid without changing a manuscript or research payload.

## Authority transition rule

A research DRAFT/PROPOSED/REVIEWED item may be incomplete.

Before `APPROVED` or `LOCKED`:

- item identity/hash must match the exact authority revision;
- all blocking MYS-04 validation findings must be clear;
- MYS-01 still requires HUMAN authority for acceptance.

AI cannot turn weak research into accepted authority.

## Deliberately OUT

- no DB/Alembic migration;
- no new source/evidence persistence;
- no FastAPI/Desktop UI;
- no web search/provider calls;
- no LLM/Astra/Agents API calls;
- no automatic source-quality interpretation from prose;
- no real `Линия 112` research yet;
- no merge authorization.

Future research discovery/synthesis may use standard BOOK OS research or bounded Astra/Agents EDITORIAL_PREP, but model output itself is never evidence.

## Acceptance evidence

MYS-04 is technically GREEN only when:

- targeted research validation tests pass;
- inherited MYS-01/MYS-02/MYS-03 tests remain green;
- Ruff format/check pass;
- strict mypy passes;
- full local-core pytest passes;
- Desktop/Tauri/native smoke show no regression;
- secret scan passes;
- zero provider/model/paid calls;
- Central Brain reviews the exact diff.

Technical GREEN does not approve Task 022, merge, real research, or manuscript Writing.
