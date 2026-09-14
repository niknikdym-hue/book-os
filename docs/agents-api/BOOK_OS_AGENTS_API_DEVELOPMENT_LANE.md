# BOOK OS — Agents API development lane

Status: PROPOSED / isolated from production book-writing and from active Draft PR work.

## Purpose

Use OpenAI Agents API as an engineering execution lane for BOOK OS code changes without exposing production manuscripts, BOOK OS production model credentials, the installed desktop application, or merge/deploy authority.

This lane is not part of the book-writing ModelGateway. It is a separate developer tool.

## Required OpenAI Platform separation

- Use a dedicated OpenAI Platform project for development, recommended name: `BOOK-OS-DEVELOPMENT`.
- Never reuse the production BOOK OS OpenAI key used by Astra/Sol inside the application.
- Create a separate project-scoped application key for the development orchestrator.
- Minimum required application-key permissions for the initial lane:
  - `api.agents.read`
  - `api.agents.write`
  - `api.responses.write`
- Do not grant Files, Vaults, Assistants, fine-tuning, admin, or unrelated API permissions unless a later reviewed task proves they are required.
- Configure a project spend limit and model/rate limits before authorizing non-smoke development work.
- Prefer an expiring key and rotate/revoke it independently of production BOOK OS credentials.

## Phase 1 security architecture — mandatory default

### Code input

The engineering agent receives a deterministic Git snapshot created with `git archive` from an explicit commit/ref. It does not receive the user working tree.

Consequences:

- untracked files are excluded;
- local `.env` files are excluded;
- macOS Keychain is inaccessible;
- `BOOK_OS_DATA_DIR` and user manuscripts are not copied;
- installed `BOOK OS.app` is not copied;
- local Git credentials are not copied.

### Sandbox

Use `environment.type = openai_hosted`.

Default network policy:

```json
{"access": "disabled"}
```

No GitHub token, PAT, SSH key, OpenAI production key, Yandex key, Apple signing credential, manuscript credential, or other long-lived secret may be supplied to the sandbox.

The application API key remains outside the sandbox in the orchestrator process.

### GitHub boundary

Phase 1 has no GitHub write path from the agent.

The agent may produce only artifacts such as:

- `book-os.patch`
- `report.md`
- test logs
- proposed commit message

A separate trusted controller/Central Brain reviews the patch and decides whether to apply it to an approved development branch.

The agent cannot:

- push;
- merge;
- change PR state;
- deploy;
- create releases;
- modify repository secrets;
- replace the installed Desktop app.

## Active-work isolation

When another implementation PR is active, the Agents API lane must not write to that PR branch.

For the initial setup, the infrastructure branch is:

`brain/agents-api-development-lane-20260914`

It was created from the then-current `main`, not from the active feature PR. No integration commit should be pushed into another agent's branch while that work is in progress.

## Owner gates

The following actions always require explicit Owner/Central Brain authorization:

1. granting GitHub write credentials to an agent environment;
2. enabling unrestricted network access;
3. exposing any production or manuscript data;
4. exposing macOS Keychain or local user directories;
5. increasing project spend limits beyond the approved bounded development budget;
6. allowing automatic push;
7. allowing automatic merge;
8. deployment, notarization, signing, release, or replacement of the installed application;
9. production book/model runs as part of engineering work.

## Model policy

Use a coding-capable model selected for the engineering task. Model choice does not override cost gates, sandbox restrictions, branch restrictions, or authority rules.

A smoke test should use the minimum work necessary to prove the transport and sandbox. Do not use a production manuscript as smoke input.

## Cost policy

Before the first real engineering run:

- set a dedicated project spend limit;
- keep the first smoke test extremely small;
- log session id, model, usage and task identity;
- terminate/delete the sandbox after the test;
- do not infer that a completed turn means all shell/test actions succeeded — verify artifacts and reported tool outcomes.

## Artifact acceptance

An agent result is not accepted merely because the session completed.

A change is eligible for repository application only when:

1. the source snapshot SHA is recorded;
2. the produced patch is inspectable;
3. tests actually ran where required and their outputs are available;
4. no secret or manuscript material appears in the patch or logs;
5. the destination branch is explicitly allowed;
6. exact-head CI is checked after application;
7. merge remains a separate Owner/Central Brain decision.

## Later phases

A future write-enabled GitHub lane may be considered only after Phase 1 is proven. It must use a separate least-privilege GitHub credential restricted to one repository and, where technically possible, only approved development branches. Direct write to `main`, automatic merge, repository-secret administration and release/deploy rights remain prohibited.

## Kill switch

Revoking the dedicated `BOOK-OS-DEVELOPMENT` API key or disabling the development project must stop the Agents API engineering lane without affecting the production BOOK OS book-writing key.
