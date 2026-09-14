# BOOK OS Agents API engineering runner

This directory contains an isolated development helper for running engineering tasks through OpenAI Agents API without giving the agent GitHub credentials, production BOOK OS credentials, local manuscripts, or the user's working tree.

Read first:

`docs/agents-api/BOOK_OS_AGENTS_API_DEVELOPMENT_LANE.md`

## Required Platform configuration

Create a dedicated OpenAI Platform project for this lane, recommended name:

`BOOK-OS-DEVELOPMENT`

Create a dedicated restricted application API key with only:

- `api.agents.read`
- `api.agents.write`
- `api.responses.write`

Do not use the BOOK OS production OpenAI key.

Configure the development project's spend limit, model permissions and rate limits before any non-smoke task.

## API-free preflight

Before creating or using an Agents API session, validate the exact committed snapshot. This command uses only local Git and the Python standard library: it makes **zero network calls and zero model calls**.

```bash
python3 tools/agents_api/preflight_snapshot.py --ref <approved-sha-or-branch>
```

It fails closed when the selected ref contains a tracked credential-bearing path, a high-risk credential pattern, or a compressed Git snapshot above the initial 5 MiB inline-file limit.

A PASS from this preflight is required before the first smoke or any later engineering run.

## Local environment

Use a separate virtual environment for the orchestration helper:

```bash
cd /path/to/book-os
python3 -m venv .venv-agents-api
.venv-agents-api/bin/pip install -r tools/agents_api/requirements.txt
```

The runner deliberately uses `BOOK_OS_AGENTS_API_KEY`, not the standard `OPENAI_API_KEY`, to reduce the chance of accidentally reusing the production application credential.

Load the dedicated development key into the local process through a secure secret mechanism. Never commit it to the repository and never include it in a prompt.

## Smoke test

The first authorized task should be read-only and tiny, for example:

```bash
BOOK_OS_AGENTS_API_KEY='***' \
.venv-agents-api/bin/python tools/agents_api/safe_development_agent.py \
  --ref main \
  --model gpt-5.6-sol \
  --task 'Inspect README.md and report the repository components. Make no code changes.' \
  --out-dir /tmp/book-os-agents-smoke
```

The agent sandbox has network access disabled and receives only a compressed `git archive` of the explicit ref.

Expected local outputs:

- `events.jsonl`
- `metadata.json`
- `report.md`
- `book-os.patch`
- `result.zip`

For a no-change smoke test, `book-os.patch` should be empty.

## Engineering task

Use a task file for substantial work:

```bash
BOOK_OS_AGENTS_API_KEY='***' \
.venv-agents-api/bin/python tools/agents_api/safe_development_agent.py \
  --ref <approved-sha-or-branch> \
  --task-file /path/to/task.md \
  --out-dir /tmp/book-os-agent-result
```

The returned patch is a proposal only. Inspect it and run local/CI verification before applying it to any development branch.

## Why there is no GitHub token

The initial lane intentionally has no direct repository write capability. The sandbox cannot push, merge, change PR state, deploy, create releases, or access repository secrets. A trusted controller applies an accepted patch separately.

This separation is a safety feature, not a missing integration.

## Snapshot limits

The hosted sandbox accepts inline input files up to 5 MiB each. The runner fails closed if the compressed Git snapshot exceeds that limit. Do not solve this by silently broadening API-key permissions. A larger-input lane using the Files API must be reviewed separately.

## Current active-work rule

Do not use the runner to apply changes directly to a branch that another agent/Codex session is actively modifying. Snapshotting such a branch for read-only analysis is allowed; repository writes remain external and separately controlled.
