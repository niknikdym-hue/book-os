# MYS-03 — NARRATIVE CONTRACT / READER KNOWLEDGE / FAIRNESS

**Status:** IMPLEMENTATION / STACKED DRAFT  
**Date:** 2026-09-18  
**Repository:** `niknikdym-hue/book-os`  
**Base:** `codex/mys-02-case-integrity-20260918` @ `8b2dc41d925eac8a9afb098c1115c03606f0be53`  
**Branch:** `codex/mys-03-narrative-fairness-20260918`

## Purpose

Turn the accepted NarrativeContract design into deterministic pre-writing/fairness checks without pretending software can judge prose semantics by itself.

MYS-03 validates the **declared information architecture of scenes**:

- authorized POV ownership;
- person/tense contract adherence;
- limited-POV interior-access boundaries;
- reader exposure vs POV knowledge/observable facts;
- explicit withholding mechanisms;
- prohibited suppression;
- conscious decisive facts hidden without contractual reason;
- approved narrative devices;
- reader knowledge accumulation by narrative order;
- bounded unreliable-narrator source/domain/signal completeness;
- narrative-mode vs grammatical-person consistency;
- explicit culprit-POV policy and deterministic culprit-identity fairness guards.

## OUT

- no natural-language prose interpretation;
- no claim that software can detect every lie/subtext/head-hop in final prose;
- no DB/API/Desktop changes;
- no model/Agents API call;
- no private `Линия 112` content;
- no merge authorization.

## Core distinction

`known by POV != consciously material in this scene != exposed to reader`

A fair mystery does **not** require a narrator to verbalize every known fact in every scene. Therefore deterministic hidden-fact blocking applies only where the fact is declared both:

1. consciously/materially active for the POV in the scene; and
2. decisive/protected under the NarrativeContract.

Other fairness questions remain for MysteryBench / adversarial literary review.

## Deterministic contract rules

- scene IDs and narrative `reader_order` values are unique;
- limited modes require an authorized POV unless contract explicitly allows viewpointless scenes;
- scene person/tense must fit contract (`MIXED` / `MIXED_CONTROLLED` are explicit exceptions);
- limited POV cannot directly access another character's interior state unless contract explicitly permits it;
- reader-exposed non-observable facts in limited POV must be known to that POV;
- conscious facts must be a subset of POV-known facts;
- a withheld fact must actually be known/conscious to the POV;
- each intentional withholding requires an allowed mechanism code;
- prohibited mechanism codes always block;
- viewpoint-specific protected facts cannot be intentionally suppressed;
- a decisive conscious fact cannot be silently hidden without a contractual withholding decision;
- a fact cannot be simultaneously declared exposed and withheld in one scene;
- narrative-device refs must be accepted by the contract;
- bounded/explicit unreliable narration requires declared source, bounded domains and reader signals;
- FIRST modes require FIRST grammatical person and THIRD_LIMITED modes require THIRD;
- culprit POV requires an explicit policy; identity-focused policies require explicit identity facts, while PRE_ACT_CONSCIOUSNESS requires explicit relevant-act awareness facts;
- reader knowledge checkpoints are derived in narrative order and never “forget” a fact deterministically.

## Planned finding families

### Contract
- `NARRATIVE.CONTRACT.DUPLICATE_VIEWPOINT`
- `NARRATIVE.CONTRACT.WITHHOLDING_POLICY_CONFLICT`
- `NARRATIVE.CONTRACT.UNRELIABLE_WITHOUT_SIGNAL`
- `NARRATIVE.CONTRACT.UNRELIABLE_SOURCE_MISSING`
- `NARRATIVE.CONTRACT.UNRELIABLE_DOMAINS_MISSING`
- `NARRATIVE.CONTRACT.MODE_PERSON_CONFLICT`
- `NARRATIVE.CONTRACT.CULPRIT_POV_POLICY_MISSING`
- `NARRATIVE.CONTRACT.CULPRIT_IDENTITY_FACT_MISSING`
- `NARRATIVE.CONTRACT.CULPRIT_ACT_AWARENESS_FACT_MISSING`

### Scene/POV
- `NARRATIVE.SCENE.DUPLICATE_ID`
- `NARRATIVE.SCENE.DUPLICATE_ORDER`
- `NARRATIVE.POV.MISSING`
- `NARRATIVE.POV.UNAUTHORIZED`
- `NARRATIVE.POV.PERSON_DRIFT`
- `NARRATIVE.POV.TENSE_DRIFT`
- `NARRATIVE.POV.HEAD_HOPPING`
- `NARRATIVE.POV.CONSCIOUS_FACT_NOT_KNOWN`

### Withholding/fairness
- `NARRATIVE.WITHHOLDING.DUPLICATE_FACT`
- `NARRATIVE.WITHHOLDING.UNKNOWN_FACT`
- `NARRATIVE.WITHHOLDING.UNKNOWN_MECHANISM`
- `NARRATIVE.WITHHOLDING.PROHIBITED_MECHANISM`
- `NARRATIVE.WITHHOLDING.PROTECTED_FACT`
- `NARRATIVE.WITHHOLDING.EXPOSED_CONFLICT`
- `NARRATIVE.FAIRNESS.HIDDEN_DECISIVE_FACT`
- `NARRATIVE.READER.KNOWLEDGE_LEAK`
- `NARRATIVE.DEVICE.UNAPPROVED`
- `NARRATIVE.CULPRIT_POV.IDENTITY_NOT_EXPOSED`
- `NARRATIVE.CULPRIT_POV.IDENTITY_HIDDEN_WITHOUT_DECISION`
- `NARRATIVE.CULPRIT_POV.PRE_ACT_AWARENESS_ACTIVE`
- `NARRATIVE.CULPRIT_POV.FORMAL_FRAME_DEVICE_MISSING`

## Acceptance evidence

- targeted MYS-03 tests green;
- inherited MYS-01/MYS-02 tests green;
- full local-core suite green;
- Ruff format/check green;
- strict mypy green;
- zero provider/model calls;
- Central Brain diff review.

Technical GREEN does not authorize manuscript Writing or merge.
