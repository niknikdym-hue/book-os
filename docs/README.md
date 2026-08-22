# BOOK OS

BOOK OS is a specialized editorial-authoring operating system for producing high-quality nonfiction.

It is **not** a generic AI writer and **not** a one-prompt book generator. Its purpose is to give one strong author/editor the research, architecture, drafting, editorial, evidence, voice-control, versioning, provenance, quality-gate, and human-acceptance infrastructure of a professional editorial team.

## Source of truth

**GitHub `main` is the project source of truth. Chats are working sessions, not authority.**

If a chat/session disappears, a successor must be able to recover the project from this repository without relying on remembered conversation context.

## Start here / recovery order

1. [`docs/BOOK_OS_AUTHORITY.md`](docs/BOOK_OS_AUTHORITY.md)
2. [`docs/PROJECT_EXECUTION_PLAN.md`](docs/PROJECT_EXECUTION_PLAN.md)
3. [`docs/PROJECT_STATE.md`](docs/PROJECT_STATE.md)
4. [`docs/DESIGN_INDEX.md`](docs/DESIGN_INDEX.md) — complete v0.1 design map and recovery order
5. current `main`, active task/PR, tests and eval evidence

Chat history is optional supplementary context and must never override repository authority.

## Current phase

**Design baseline complete → Implementation Milestone 0 ready.**

The first bounded Codex task is [`docs/tasks/CODEX_TASK_001_BOOTSTRAP.md`](docs/tasks/CODEX_TASK_001_BOOTSTRAP.md).

## Project-development rule

`accepted authority → bounded task → proposed implementation/patch → tests/evidence → review → acceptance → new authority`

## Core responsibility split

- **Owner:** final product/creative authority and major scope/cost/risk decisions.
- **Central Brain:** architecture/specifications, sequencing, bounded Codex tasks, acceptance review, authority/state maintenance.
- **Codex:** bounded implementation, tests/evidence, reproducible delivery; no silent product/architecture decisions.

## Privacy boundary

This public repository is the BOOK OS software/project-development authority. **Do not store real private manuscripts, API keys, user source materials or the proprietary accepted/rejected editorial-decision corpus here.**
