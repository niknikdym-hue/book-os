# BOOK OS — Agents API GitHub write gate

Status: BLOCKING for any direct agent-to-GitHub write integration.

Observed on 2026-09-14:

- repository: `niknikdym-hue/book-os`;
- default branch: `main`;
- `main` branch protection: disabled at the time of inspection;
- active implementation work must remain isolated from the Agents API infrastructure lane.

## Phase 1 decision

Phase 1 remains safe because the Agents API sandbox receives **no GitHub token, PAT, SSH key or Git credential**. The agent can only return proposal artifacts for separate trusted review/application.

## Mandatory prerequisites before any future write-enabled lane

Direct agent-to-GitHub write capability is forbidden until all of the following are independently verified:

1. `main` is protected by branch protection or an equivalent repository ruleset;
2. direct pushes to `main` are disallowed for the agent credential;
3. force pushes and branch deletion are disallowed;
4. merge requires a pull request;
5. required exact-head CI checks are enforced before merge;
6. the agent credential is least-privilege and restricted to `niknikdym-hue/book-os`;
7. the agent cannot administer repository secrets, Actions secrets, rulesets, collaborators, releases or deployments;
8. automatic merge remains disabled unless a later Owner decision explicitly changes that rule;
9. production deploy/sign/notarize/release rights remain outside the agent credential;
10. an emergency credential-revocation procedure is tested.

Until these conditions are satisfied, the only permitted Agents API integration is the artifact-only Phase 1 lane documented in `BOOK_OS_AGENTS_API_DEVELOPMENT_LANE.md`.
