# BOOK OS Decision — Frontier lane + independent local Brain

**Date:** 2026-09-09  
**Status:** OWNER ACCEPTED  
**Scope:** model execution strategy, local intelligence, quality target, build-vs-reuse

## Decision

BOOK OS will use a dual execution strategy:

1. **Frontier external lane now** for the highest-quality work while the local lane matures.
2. **Independent local BOOK OS Brain** developed in parallel, using local/open-weight models and BOOK OS-owned editorial intelligence.

The long-term objective is that normal high-quality nonfiction production can run locally without requiring an external frontier model, while external providers remain optional benchmark/fallback/expert execution resources.

The local Brain is judged by editorial outcome — depth, correctness, evidence fidelity, originality, structure, voice, usefulness, density, coherence and absence of machine-prose pathologies — not by imitating the wording or hidden behavior of any proprietary model.

## Build-vs-reuse rule

BOOK OS must not reinvent mature commodity modules without a demonstrated product reason.

Prefer strong maintained components for commodity layers, including where appropriate:

- OpenAI Responses API / hosted tools / Agents SDK / Evals for the external lane;
- Apple MLX / MLX-LM or an equivalent mature Apple-Silicon runtime for local inference;
- Tiptap/ProseMirror for the future professional manuscript editor;
- established research metadata/search sources such as OpenAlex/Crossref/Semantic Scholar;
- proven OS/platform mechanisms for packaging, signing, updates and local secure storage.

BOOK OS-specific editorial IP remains owned and controlled by BOOK OS: Authority, Contracts, Book Graph/Memory, Claim/Evidence, Series Brain, chapter admission, Editorial Decision Memory, BookBench, quality routing, adversarial review and Literary Master.

## Provider-state boundary

External vendor state is never canonical BOOK OS authority. Remote conversations, traces, vector stores, agent state or hosted tool state are derived/execution state only. Canonical project authority and durable book state remain locally reconstructable.

## Training/data boundary

OpenAI output must not be used to train, distill, fine-tune or create training targets for a competing local model. Local model development must use rights-clean independent data and a separately governed training/evaluation corpus.

External frontier output may be used for the user's book-production workflow and bounded human comparison, but benchmark results and external outputs must remain isolated from any prohibited local-model training pipeline.

## Quality promotion rule

Local execution is promoted **per editorial operation**, never by one global claim that “the local model is good enough.”

Promotion requires reproducible evaluation against BOOK OS quality dimensions and human review, with no blocking quality regression hidden by average scores.

If a local executor is weaker for a difficult operation, that operation remains routed to the stronger external lane until evidence supports promotion.

## Implementation

Task authority: `docs/tasks/TASK_020_FRONTIER_QUALITY_LOOP_LOCAL_BRAIN.md`.

Task 017 series-production/chapter-admission gates remain a required dependency and must not be duplicated or bypassed.
