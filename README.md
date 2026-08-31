# BOOK OS

BOOK OS is a separate editorial-authoring system for producing high-quality nonfiction.

This repository is the project source of truth. Chats are working sessions, not authority.

## Current phase

**Real Business Nonfiction pilot — ready to execute on the accepted local-first desktop.**

Accepted implementation milestones now include M0–M7, Literary Master + exports, real-book pilot instrumentation, and macOS launch hardening. The actual first private book pilot is the remaining product-validation path before HUMAN `GO | CONDITIONAL_GO | NO_GO`.

Current exact checkpoint and next permitted action are always in [`docs/PROJECT_STATE.md`](docs/PROJECT_STATE.md).

The current program is global/OpenAI-first for the MVP/pilot while keeping provider-neutral gateways. The former Russia/no-VPN/Yandex/GigaChat promotion milestone is explicitly SUPERSEDED by [`docs/decisions/2026-08-29-global-openai-first.md`](docs/decisions/2026-08-29-global-openai-first.md).

## Development setup

Prerequisites: Python 3.12, Node.js 20+ with pnpm, and Rust stable.

```sh
cd services/local-core
python3.12 -m venv .venv
.venv/bin/pip install -r requirements-dev.lock
.venv/bin/pytest

cd ../../apps/desktop
pnpm install --frozen-lockfile --prod=false
BOOK_OS_PYTHON="../../services/local-core/.venv/bin/python" pnpm tauri dev
```

Relative `BOOK_OS_PYTHON` values are resolved from `apps/desktop`, so the command is independent of the native process's working directory. Absolute overrides are also supported unchanged.

The desktop starts the Python Local Core on an OS-assigned `127.0.0.1` port. Its random per-launch bearer token remains in the native process; the React UI asks Tauri to perform authenticated local API calls. macOS startup is hardened so Local Core initialization does not block first window rendering and the Python child remains owned through startup/shutdown.

Canonical schema is Alembic `0010`.

## Authority

Canonical project decisions live in [`docs/BOOK_OS_AUTHORITY.md`](docs/BOOK_OS_AUTHORITY.md).

Recovery order and the current design map live in [`docs/DESIGN_INDEX.md`](docs/DESIGN_INDEX.md).

Decision history and bounded architecture records live in [`docs/decisions/`](docs/decisions/).

The real private manuscript, source corpus and private evaluation content never belong in the public software repository.

## Current critical path

`real Business Nonfiction book → Literary Master → HUMAN GO/CONDITIONAL_GO/NO_GO`

## Core rule

`authority -> bounded task -> proposed patch -> review -> acceptance -> new authority`
