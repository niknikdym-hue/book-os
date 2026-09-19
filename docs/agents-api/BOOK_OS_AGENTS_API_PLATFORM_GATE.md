# BOOK OS — OpenAI Platform gate for Agents API development

Status: BOUNDED OWNER GATE for paid/model execution in the dedicated development project.

This gate applies only to the engineering Agents API lane. It must not alter the production BOOK OS project/key used by Astra/Sol for book work.

## Required project

Use a dedicated project:

`BOOK-OS-DEVELOPMENT`

Do not use `Default project` and do not reuse the production BOOK OS API project.

## Engineering model and reasoning policy

The controlled engineering lane uses:

- default model: `gpt-5.6-sol`;
- default reasoning mode: `auto`;
- Auto resolves locally to `medium | high | xhigh` without an extra model/API request;
- ordinary engineering work resolves to Medium;
- High is reserved for genuinely complex cross-module, architecture, migration, recovery, concurrency or comparable system work;
- Extra High is exceptional and requires a concrete severe/frontier signal, not merely caution or uncertainty;
- explicit Owner `medium | high | xhigh` overrides Auto;
- subagents: disabled.

Do not enable unrelated models merely for convenience. A later model change is a reviewed cost/quality decision.

## Application API key

Suggested key name:

`BOOK-OS-Development-Codex`

Key requirements:

- project-scoped to `BOOK-OS-DEVELOPMENT`;
- Restricted permissions;
- minimum endpoint permissions only:
  - `api.agents.read`
  - `api.agents.write`
  - `api.responses.write`;
- no Files permission for Phase 1;
- no fine-tuning, Assistants, Vault, admin or unrelated permissions;
- prefer an expiration date;
- never reuse/copy the production BOOK OS OpenAI key.

After creation, store the key only in the dedicated macOS Keychain item documented in `tools/agents_api/README.md`.

## Spend controls

Before any paid engineering run:

- keep a small project-level enforced spend limit when the Platform account exposes one;
- configure alerts and low practical rate limits for this one-user engineering lane;
- allow `gpt-5.6-sol` for the project;
- do not raise spend limits merely because an implementation task exists;
- review actual usage before materially increasing the development budget.

If the account UI exposes only a soft monthly budget, do not treat it as a hard safety boundary.

## Paid/model execution gate

A paid/model run is allowed only when all of the following are true:

1. `BOOK-OS-DEVELOPMENT` exists in the correct OpenAI Platform account;
2. the restricted development key is in that project;
3. `gpt-5.6-sol` is allowed for the project;
4. spend/rate controls are configured;
5. the key is stored in the dedicated macOS Keychain item;
6. `python3 tools/agents_api/preflight_snapshot.py --ref <approved-ref>` is PASS;
7. Agents API Safety CI is GREEN on the infrastructure PR exact head;
8. the destination/active feature branch boundary is explicitly respected;
9. no GitHub credential will be supplied to the sandbox;
10. the task contains no production manuscript or private BOOK OS data;
11. the task has an explicit bounded purpose and the chosen reasoning level follows the cost policy.

Updating runner code/docs or proving these guards does **not** itself authorize a paid smoke. API-free checks are sufficient for the current policy correction.

## First smoke task, when separately authorized

Use a read-only repository understanding task only:

`Inspect README.md and report the repository components. Make no code changes.`

Run it with `gpt-5.6-sol` and `--reasoning auto`; this ordinary task should resolve locally to Medium.

Expected proof:

- session starts in the OpenAI-hosted sandbox;
- network policy is disabled;
- source SHA is recorded;
- requested reasoning mode and resolved effort are recorded;
- no GitHub credential is present;
- no BOOK_OS_DATA_DIR/manuscript is present;
- required artifacts are returned;
- `book-os.patch` is empty;
- session is deleted after artifact retrieval;
- actual usage/cost is reviewed before any broader engineering task is authorized.

## Kill switch

If anything is unexpected:

1. revoke/expire the `BOOK-OS-Development-Codex` key in `BOOK-OS-DEVELOPMENT`;
2. delete the local Keychain copy with `keychain_runner.py delete`;
3. do not increase project spend limits;
4. keep Agents API direct GitHub write disabled.

Revoking this development credential must not affect the production BOOK OS book-writing credential.
