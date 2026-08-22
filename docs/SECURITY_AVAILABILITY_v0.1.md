# BOOK OS — SECURITY, PRIVACY & AVAILABILITY v0.1

**Status:** ACCEPTED FOR V0.1 IMPLEMENTATION  
**Version:** 0.1.0  
**Date:** 2026-08-22

## 1. Security goal

Protect manuscripts, source materials, credentials and authority history while keeping BOOK OS usable if a provider/chat/cloud is unavailable.

## 2. Data classes

- **Public project-development data:** BOOK OS public repository docs/code.
- **Private manuscript data:** book text, source materials, contracts tied to a real book.
- **Sensitive editorial data:** accepted/rejected edits, reasons, voice samples, BookBench datasets.
- **Secrets:** API keys, service credentials, signing keys.

Private manuscript/editorial data and secrets must never be committed to the public `book-os` repository.

## 3. Local-first privacy baseline

Canonical book state is local in v0.1. External providers receive only the bounded context required for a task, subject to provider policy.

Do not upload the whole book merely because a provider supports a huge context window.

## 4. Secret handling

- OS secure store through `SecretStore` abstraction;
- no secrets in Git, SQLite manuscript tables, prompt files or provenance records;
- no secret values in logs;
- frontend does not receive long-lived provider keys;
- developer live-test secrets are injected by environment/secure CI secret store;
- signing/private update keys stored separately from application repository.

## 5. Local sidecar security

- bind local service to loopback only;
- random port;
- per-launch unguessable session token;
- reject unauthenticated requests;
- parent-process lifecycle ownership;
- explicit CORS/origin restrictions if browser-origin semantics apply;
- no arbitrary shell execution endpoints.

## 6. Provider data minimization

Model/research request logs store metadata needed for provenance/cost/debugging. Raw manuscript prompt/response storage outside the local project is disabled by default unless explicitly required and approved.

Provider adapters expose data-retention/logging options when vendors support them.

## 7. Russia / no-VPN product policy

- no requirement for VPN;
- no circumvention of provider geography/contracts;
- route only to permitted provider/self-hosted paths;
- user should not need personal foreign AI subscriptions/API keys;
- unsupported providers are disabled for that lane;
- product displays structured provider-unavailable state instead of asking user to “turn on VPN”.

Current official OpenAI policy states that accessing/offering API services outside listed supported countries may lead to blocking/suspension; Russia is absent from the list as of 2026-08-22. Therefore OpenAI is development/international capability, not a mandatory Russian user dependency.

## 8. Commercial provider brokerage caveat

Before selling a hosted plan that uses BOOK OS-owned vendor credentials for end users, verify each provider's current commercial terms, regional rules, data processing requirements and resale/pass-through restrictions. Architecture allows brokerage; commercial launch must not assume permission without review.

## 9. Offline/degraded operation

Without network, user must still be able to:

- open/read projects;
- edit manuscript/contracts manually;
- inspect authority/version history;
- review existing findings/proposals;
- export existing approved content;
- create local backups.

External generation/research tasks become queued/unavailable with clear status, not data loss.

## 10. Backup and recovery

v0.1 must support a project backup/export bundle containing:

- canonical SQLite database;
- referenced local assets that user chooses/include;
- manifest/checksums;
- schema/app version;
- optional encrypted archive mode when implemented.

Backup restore must be tested.

The product-development repository recovery and a user's book-project recovery are separate concerns.

## 11. Integrity

- SHA-256 hashes for revisions/assets/release manifest;
- transactional authority transitions;
- stale proposal detection;
- database integrity checks on open/backup;
- Literary Master checksums.

## 12. Telemetry privacy

Telemetry is opt-in/controlled and must avoid manuscript text by default. Operational metrics can use IDs, duration, provider, token/cost and error categories without full content.

## 13. Public repo/IP boundary

The public repository improves continuity across chats/agents, but the strongest future moat is the private editorial decision/eval corpus. Keep real human decision datasets private/local or in a dedicated protected store. Public code/docs must never be mistaken for permission to publish user manuscripts or proprietary acceptance data.
