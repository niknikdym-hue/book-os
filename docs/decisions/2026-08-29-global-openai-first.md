# OWNER DECISION — GLOBAL / OPENAI-FIRST BOOK OS

**Date:** 2026-08-29  
**Status:** APPROVED OWNER AUTHORITY  
**Supersedes:** all prior requirements that BOOK OS must prove a Russia/no-VPN runtime lane, Yandex/GigaChat production promotion, or Russia-specific provider availability before M9/M10 or product GO/NO-GO.

## Decision

BOOK OS is a **global editorial-authoring system**.

The current product program does **not** contain a separate Russia deployment / no-VPN / regional-runtime task.

That task is removed, not deferred.

## Primary model strategy

For the current MVP and real-book pilot:

- OpenAI is the primary intelligence/provider lane for the quality path;
- the existing provider-neutral Model Gateway architecture remains mandatory;
- no backup provider is required before the real-book pilot;
- Yandex and GigaChat are not required WRITER/EDITOR candidates;
- no Yandex/GigaChat live promotion is required;
- no regional-provider milestone gates Literary Master or the real-book pilot.

## Provider-neutral invariant

OpenAI is the primary provider for the current quality path, but it is not permanent architecture authority.

Provider-specific behavior must remain behind adapters/gateways, with exact provider/model/config provenance and BookBench evaluation so stronger competitors can be benchmarked later without rewriting BOOK OS core.

## Disposition of former M8 / PR #12

The former Russia/no-VPN milestone and its live-promotion acceptance are **SUPERSEDED**.

PR #12 is historical/salvage evidence only. Its useful provider-neutral mechanisms may be reused later, but the PR must not be merged as a required BOOK OS milestone and no further Yandex/GigaChat live work is required.

## Current critical path

`OpenAI-first quality path → Literary Master + exports → real Business Nonfiction pilot → GO/NO-GO`

## Explicitly removed from current program

- Russia/no-VPN launch requirement;
- Russia-specific provider routing as an MVP gate;
- Yandex WRITER/EDITOR promotion;
- GigaChat WRITER/EDITOR promotion;
- regional availability as a blocker for BOOK OS product-quality acceptance.
