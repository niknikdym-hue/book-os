# BOOK OS Auto Book — gap map

**Status:** IMPLEMENTATION BASELINE  
**Verified repository baseline:** `19ab44ba30036936f843e9b13f2a0f7c8f7b1204`  
**Verified:** 2026-09-13  
**Purpose:** bound the implementation of the complete author-facing Auto Book cycle without
replacing existing books, manual workflows, authority, research, Book Memory, BookBench, or
Literary Master.

## Repository and open work

| Surface | Verified state | Reuse decision |
| --- | --- | --- |
| GitHub `main` | PR #37 merged at `19ab44ba30036936f843e9b13f2a0f7c8f7b1204` | Implementation baseline |
| PR #32 | Draft, head `eb5ed8415619a3eadbf0d26cc1b3ff23aafbc53f`; bounded quality loop and Local Brain | Reuse the quality-loop domain/orchestrator; Local Brain is optional, never a prerequisite for OpenAI Auto |
| PR #34 | Open, head `c448a44756a023f9561db5b03bf9f4ec9da2eab6`; source-only OpenAI web discovery and prompt-cache accounting | Reuse the fail-soft research and cache primitives; do not merge the PR wholesale |

## Current gap map

| Capability | Current `main` | Required implementation |
| --- | --- | --- |
| Author entry | Simple project creation plus a separate Auto form | One clear intent form: idea, reader, author, series/standalone, length, attachment roles, selected outputs and visual policy |
| Auto lifecycle | UI repeatedly calls `/advance`; contract → architecture → chapter contracts → drafts → export | Durable Local Core queue with an exclusive lease, checkpoints, pause/resume, restart recovery and idempotent operation keys |
| Authority | Run-level owner pre-authorization exists, but automatic applications are recorded as fresh `HUMAN` actions | Persist launch authorization separately and distinguish human acceptance from system use of delegated scope |
| Model routing | Four operation defaults and manual modes; Auto choice lacks reasoning effort and measured complexity | Versioned operation/complexity/risk policy returning exact model, effort, rationale, quality floor, estimate and escalation condition |
| Budget | `authorized_cost_usd` is displayed and accumulated as if it were spend | Separate estimated, reserved, confirmed and unknown cost; atomic reservation; reserve release/final-edit budget |
| Research | Research Engine, Source → Evidence → Claim and Book Memory exist | Add question map, factual-claim coverage, evidence freshness and exact manuscript-revision links |
| Chapter quality | Drafting plus deterministic diagnostics | Addressable writer → critic → revision loop; failed/exhausted work never becomes PASS |
| Whole-book quality | Per-unit final edit, deterministic cross-book/fact checks and BookBench | Mid-book audit, full-book coverage, substantive independent review on an exact snapshot and bounded corrective pass |
| Master | Literary Master stores canonical text and current exports | Structured content model for paragraphs, native tables, figures, captions, links, sources and appendices |
| Visuals | Book-level visual preference and planning language | Visual Plan and asset registry with provenance, data source, rights/origin, alt text and audio equivalent |
| Outputs | Markdown, audiobook handoff JSON, and a simple LitRes DOCX | Selected-output registry; full DOCX, LitRes DOCX, PDF, EPUB, two audio DOCX profiles, voice TXT, pronunciation dictionary, reader extras and publisher pack; independent QA/staleness |
| UX | Auto form shows one optional LitRes checkbox and technical limits | Russian output checkboxes, preflight summary/range/hard cap, honest progress/costs, ready files, pause/resume, and natural-language change request |
| Recovery | JSON state is atomically replaced, but no durable worker/lease or unknown paid outcome | SQLite-backed operation ledger; no blind retry after an unknown provider outcome; recover by provider ID where supported |

## External quality and series sources

The series authority was verified from `niknikdym-hue/books-for-litres` `origin/main` at
`7a841a37d382dca9ace7f4d9b26110dea3dd959f`. Universal executable rules are carried into the
Auto policy: full-text and functional zero-overlap, protected future-book territory, explicit
`NOT THIS BOOK`, practical outputs, factual integrity, anti-junk gates, whole-book review, and
Russia-specific freshness as a profile layer. Series-specific content remains in its series
profile and is not made a universal BOOK OS rule. No authority from the unrelated «Право на
себя» series is imported.

The owner-provided «Как продавать услуги» files are private evaluation references, not repository
content and not model-training material:

| Role | SHA-256 | Structural evidence |
| --- | --- | --- |
| Full manuscript DOCX | `ed764455ae077a41cd6a056fe791ff900dd4c68c2b479423697b731dde4a67b9` | 16 native Word tables |
| Reader audio adaptation DOCX | `0bd18e2c744b1231647f8d0e5b4b1cdf0ee8eaafcbffba6dd2df7379995fae81` | separate adaptation; 0 tables |
| LitRes audio adaptation DOCX | `1ae08073296d677dbd72916a54b44767befd93b147cc32a8b339d2e308af1ed3` | separate adaptation; 0 tables |
| Voice text TXT | `0b39b40f0d75da657bd5a022bc0dda9759389edbe818434c77ae5fd11fb0d6d3` | 353,723 characters; spoken-text result |

Only hashes, roles, structural counts and quality requirements may be used by repository tests.
The manuscript itself must not be committed.

## Completion boundary

Green deterministic tests establish technical correctness only. Real writing quality remains
`NOT_CONFIRMED` until a separately authorized, budget-capped comparative editorial trial on new
prompts is blind-reviewed for depth, clarity, practical completeness, evidence, voice and total
cost of accepted text. No paid call is authorized by this implementation task.
