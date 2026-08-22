# BOOK OS — PRODUCT SPEC v0.1

**Status:** ACCEPTED FOR V0.1 IMPLEMENTATION  
**Version:** 0.1.0  
**Date:** 2026-08-22

## 1. Product promise

BOOK OS is an editorial-authoring operating system for high-quality nonfiction. It gives one strong author/editor the research, architecture, drafting, developmental-editing, evidence, cross-book, literary, voice-control, versioning, quality-gate and acceptance infrastructure of a professional editorial team.

It does **not** promise a bestseller and does **not** operate as a one-prompt AI book generator.

## 2. First user and first pilot

- First user: Owner of BOOK OS.
- First pilot: a real book created from zero.
- First profile: `Business Nonfiction`.
- User chooses one primary business subtype and optionally one secondary subtype.
- Architecture must support `Existing Manuscript / Materials`, but that mode is not the first pilot path.

## 3. Product-level independence requirements

BOOK OS must not depend on:

- a particular chat session;
- a particular LLM brand/model;
- a personal subscription to ChatGPT, Claude, Gemini or another vendor;
- a personal vendor API key as a product requirement;
- VPN use for a user in Russia;
- an external AI provider to keep the book itself accessible.

Any model/research service is a replaceable execution dependency behind a gateway. Book state and authority remain under BOOK OS control.

## 4. End-to-end Book-from-Zero flow

### Stage A — Idea

The user enters an idea, problem, observation, experience or working question. BOOK OS may challenge or broaden it but cannot silently establish thesis authority.

### Stage B — Reader & Market

BOOK OS helps define:

- intended reader;
- urgent reader problem/job-to-be-done;
- competing/adjacent books and ideas;
- differentiation opportunity;
- risks of banality or category saturation.

Output is structured project knowledge, not merely a chat answer.

### Stage C — Thesis

BOOK OS proposes testable thesis candidates, objections, counter-theses and unique angles. Human selects/edits the central thesis.

### Stage D — Research

Research questions are derived from the intended book, not performed as an unbounded web crawl. Sources and evidence enter the Research Engine / Claim Ledger.

### Stage E — Book Contract

A versioned `BookContract` is produced and must be human-approved before it is treated as settled authority.

### Stage F — Architecture

BOOK OS proposes parts/chapters and tests each chapter's unique structural function. Human approves the architecture before systematic drafting.

### Stage G — Chapter cycle

For each chapter:

`Chapter Contract → targeted research → bounded drafting → developmental review → evidence/fact review → revision → human acceptance`

The system may draft multiple sections, but every generation is tied to a BoundedTask and exact authority baseline.

### Stage H — Whole-book edit

After a complete manuscript exists, BOOK OS performs cross-book checks for idea duplication, examples, contradictions, promise coverage, transitions, rhythm, voice drift and AI-like prose.

### Stage I — Final review

BookBench runs against exact revisions. Material unresolved findings are visible; they are never hidden by a single aggregate score.

### Stage J — Literary Master

Only the human Owner can release `LiteraryMaster`. It is an immutable manifest of exact approved versions.

## 5. User experience surfaces for v0.1

The minimum user-facing product is not “a chat window”. It has explicit book-state surfaces:

1. **Projects** — create/open a book project.
2. **New Book** — choose Business + subtype(s), Book from Zero.
3. **Book Definition** — Reader, Market, Thesis, Book Contract.
4. **Architecture** — parts/chapters, purpose and dependencies.
5. **Chapter Workspace** — Chapter Contract, research, draft, revisions.
6. **Research & Claims** — sources, claims, evidence, verification state.
7. **Editorial Inbox** — findings and proposed changes with diff/decision.
8. **BookBench** — dimension-specific quality findings and gates.
9. **Release** — final checks and Literary Master creation/export.

An assistant/chat panel may exist as a convenience, but any durable result must be materialized as a first-class BOOK OS object. Chat transcript is not hidden product state.

## 6. User-facing Business taxonomy

Primary + optional secondary subtype:

1. Entrepreneurship
2. Strategy
3. Leadership
4. Management
5. Teams & Culture
6. Marketing & Brand
7. Sales & Negotiation
8. Finance & Investing
9. Product, Innovation & Technology
10. Career & Professional Development

Principle: **simple outside, smart inside**.

## 7. What v0.1 intentionally does not build

- own foundation model;
- fine-tuning as the starting strategy;
- agent swarm;
- publisher collaboration/enterprise permissions;
- marketing automation;
- cover generation pipeline;
- print production;
- translation production internals;
- audiobook production internals;
- automatic publication;
- support for every nonfiction or fiction genre;
- hidden automatic rewrite of a whole approved book.

## 8. MVP definition

BOOK OS v0.1 is an MVP only when the Owner can create one real Business Nonfiction book from zero to Literary Master using the system's structured workflow, while preserving evidence, authority, revision history and human control.

The MVP includes at least one operational region-compliant model path for a user in Russia before the “Russia-ready” product claim is accepted.

## 9. MVP success criteria

### Product success

A complete real project can move from Idea to Literary Master without using chat memory as required state.

### Editorial success

The system detects and exposes meaningful structural, repetition, evidence, style and coherence defects that materially improve the manuscript after human-reviewed revision.

### Writing success

BookBench + human review show that controlled BOOK OS drafting/editing is materially stronger than a simple one-shot/general AI drafting baseline on representative chapters.

### Authority success

No approved/locked object can be silently mutated; every material replacement has exact baseline, proposal, decision and approval history.

### Evidence success

Material factual claims are traceable to evidence/source relationships or remain visibly unresolved.

### Voice success

Author voice deviations and agreed AI-prose pathologies are detected with actionable evidence, not merely a generic style score.

### Recovery success

A new Central Brain can recover project-development state from GitHub. A user can recover a book project from its local project data/backup without needing the chat that created it.

### Regional access success

A user in Russia can use the core product without VPN and without personal subscriptions/API keys to foreign AI consumer services, using region-compliant routing.

## 10. “Done” does not mean “all scores are high”

BookBench does not decide that a book is “great”. It produces evidence and gates. Final creative acceptance remains human.
