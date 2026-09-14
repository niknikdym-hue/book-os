# BOOK OS — OpenAI Platform gate for Agents API development

Status: BLOCKING until completed by the Owner in the dedicated OpenAI Platform account.

This gate applies only to the engineering Agents API lane. It must not alter the production BOOK OS project/key used by Astra/Sol for book work.

## Required project

Create a dedicated project:

`BOOK-OS-DEVELOPMENT`

Do not use `Default project` and do not reuse the production BOOK OS API project.

## Initial model policy

For the first controlled smoke:

- allow `gpt-5.3-codex`;
- do not enable unrelated models merely for convenience;
- runner must pass the model explicitly;
- initial reasoning effort: `low`;
- subagents: disabled.

Additional models may be enabled only after a reviewed need/cost decision.

## Application API key

Suggested key name:

`BOOK-OS-Development-Codex`

Key requirements:

- project-scoped to `BOOK-OS-DEVELOPMENT`;
- Restricted permissions;
- minimum initial endpoint permissions only:
  - `api.agents.read`
  - `api.agents.write`
  - `api.responses.write`;
- no Files permission for Phase 1;
- no fine-tuning, Assistants, Vault, admin or unrelated permissions;
- prefer an expiration date;
- never reuse/copy the production BOOK OS OpenAI key.

After creation, store the key only in the dedicated macOS Keychain item documented in `tools/agents_api/README.md`.

## Spend controls

Initial safety target before the first smoke:

- set a project-level **enforced hard spend limit of USD 1.00** if the Platform UI offers enforced mode for this project;
- set an alert at 50% and 100%;
- keep `gpt-5.3-codex` as the only model needed for the smoke;
- use the lowest practical project rate limits for this one-user engineering lane.

If the account UI exposes only a soft monthly budget, do not treat it as a hard safety boundary. Confirm the enforced spend-control setting separately before authorizing ongoing autonomous engineering.

The USD 1.00 limit is intentionally a commissioning limit, not the final development budget. Raising it is a separate Owner/Central Brain decision after the smoke report and usage are reviewed.

## Smoke authorization gate

The first paid/model call is allowed only after all of the following are true:

1. `BOOK-OS-DEVELOPMENT` exists in the correct OpenAI Platform account;
2. the restricted key is created in that project;
3. `gpt-5.3-codex` is allowed for the project;
4. initial spend/rate controls are configured;
5. the key is stored in the dedicated macOS Keychain item;
6. `python3 tools/agents_api/preflight_snapshot.py --ref <approved-ref>` is PASS;
7. Agents API Safety CI is GREEN on the infrastructure PR exact head;
8. the active BOOK OS implementation PR/branch is not used as a write target;
9. no GitHub credential will be supplied to the sandbox;
10. the smoke task contains no manuscript or production data.

## First smoke task

Use a read-only repository understanding task only:

`Inspect README.md and report the repository components. Make no code changes.`

Expected proof:

- session starts in the OpenAI-hosted sandbox;
- network policy is disabled;
- source SHA is recorded;
- no GitHub credential is present;
- no BOOK_OS_DATA_DIR/manuscript is present;
- required artifacts are returned;
- `book-os.patch` is empty;
- session is deleted after artifact retrieval;
- actual usage/cost is reviewed before any engineering task is authorized.

## Kill switch

If anything is unexpected:

1. revoke/expire the `BOOK-OS-Development-Codex` key in `BOOK-OS-DEVELOPMENT`;
2. delete the local Keychain copy with `keychain_runner.py delete`;
3. do not increase project spend limits;
4. keep Agents API direct GitHub write disabled.

Revoking this development credential must not affect the production BOOK OS book-writing credential.
