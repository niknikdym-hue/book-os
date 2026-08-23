# BOOK OS

BOOK OS is a separate editorial-authoring system for producing high-quality nonfiction.

This repository is the project source of truth. Chats are working sessions, not authority.

## Current phase

**Implementation Milestone 0 — Task 001 rework in progress.**

The active bounded task is [`docs/tasks/CODEX_TASK_001_BOOTSTRAP.md`](docs/tasks/CODEX_TASK_001_BOOTSTRAP.md). Current exact checkpoint and next permitted action are always in [`docs/PROJECT_STATE.md`](docs/PROJECT_STATE.md).

## M0 development setup

Prerequisites: Python 3.12, Node.js 20+ with pnpm, and Rust stable. No cloud account or API key is required.

```sh
cd services/local-core
python3.12 -m venv .venv
.venv/bin/pip install -r requirements-dev.lock
.venv/bin/pytest

cd ../../apps/desktop
pnpm install --frozen-lockfile --prod=false
BOOK_OS_PYTHON="../../services/local-core/.venv/bin/python" pnpm tauri dev
```

The desktop starts the Python core, which binds an OS-assigned `127.0.0.1` port. Its random per-launch bearer token remains in the native process; the React UI asks Tauri to perform the authenticated health check.

## Authority

Canonical project decisions live in [`docs/BOOK_OS_AUTHORITY.md`](docs/BOOK_OS_AUTHORITY.md).

Decision history and future bounded architecture records live in [`docs/decisions/`](docs/decisions/).

## Core rule

`authority -> bounded task -> proposed patch -> review -> acceptance -> new authority`
