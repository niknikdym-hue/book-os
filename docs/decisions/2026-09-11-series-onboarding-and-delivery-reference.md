# Owner Decision — Series Onboarding & Delivery Reference

**Date:** 2026-09-11  
**Status:** APPROVED / CURRENT  
**Owner:** product owner  
**Scope:** BOOK OS series creation and existing-series renewal workflow  

## Authority relationship

This decision **extends** and does not replace:

- `docs/decisions/2026-09-06-author-series-length-style-publishing-controls.md`;
- `docs/AUDIO_NATIVE_AND_SERIES_v0.1.md` (document body version 0.2.1).

All existing cross-book uniqueness, exclusion-corpus, Series Memory and SeriesBench rules remain binding and take precedence over any style/reference convenience introduced here.

## 1. Two first-class series onboarding paths

BOOK OS must support two distinct but equal series workflows.

### A. Create a new series from zero

The author may start a completely new series. BOOK OS may use the selected OpenAI executor (including GPT-6 Astra or GPT-5.6 Sol) to propose:

- series positioning / reader promise;
- planned book map and order;
- thematic territory owned by each planned book;
- shared editorial / literary invariants;
- future-book reservations;
- cross-book uniqueness requirements;
- series-level Style Profile refinement;
- pre-writing overlap / exclusion rules.

AI proposals remain proposals. Human authority rules remain unchanged.

### B. Renew / continue an existing series

The author may already have an existing series in which only one or some books have been brought to the new desired quality level.

BOOK OS must let the author upload a current accepted book as a **Series Delivery Reference** so later renewed/new books can preserve the intended level and manner of presenting material.

## 2. Meaning of Series Delivery Reference

A Series Delivery Reference is **not** a content source and **not** a template for cloning another volume.

It is evidence for **how the material should be presented**, including such dimensions as:

- explanatory depth;
- analytical density;
- rhythm of sentences and paragraphs;
- ratio of analysis, examples and practical value;
- transitions and intellectual pacing;
- tone and directness;
- chapter-level delivery rhythm;
- prose quality / density expectations.

The complete imported reference is retained locally with immutable content identity/hash and provenance. Model-facing use should prefer a bounded style/quality calibration and representative excerpts rather than unrestricted copying context.

## 3. Hard anti-clone invariant

Every book in a series is a unique book.

A Series Delivery Reference must never relax or replace the already-approved semantic uniqueness rules. In particular, the existing authority remains binding against reuse/overlap of:

- theses;
- mechanisms;
- scenes;
- arguments;
- research functions;
- examples and case studies;
- metaphors and analogies;
- practical tools;
- chapter/template/composition patterns;
- distinctive wording or recycled AI phrasing.

The reference answers **“what level / manner of delivery is expected?”**, never **“what content should be written again?”**.

If preserving the reference style would create prohibited semantic or structural overlap, uniqueness wins and the system must choose a different expression/structure or block the candidate.

## 4. Exclusion and SeriesBench remain mandatory

For later volumes or renewed books:

- earlier accepted Literary Masters remain the cumulative exclusion corpus;
- pre-writing overlap mapping remains required where the Series Profile requires it;
- chapter-level cross-book uniqueness gates remain required;
- Series Memory continues to detect reuse and contradiction;
- whole-book SeriesBench / cross-series audit remains required before Literary Master.

Series Delivery Reference is an additional calibration input, not a substitute for these gates.

## 5. Current real-series use case

For an existing series where the first book has already been updated to the target quality level but later books have not yet been renewed, BOOK OS must allow that first updated book to be loaded as the active Series Delivery Reference.

Later books should preserve its **quality and manner of presentation** while remaining substantively, structurally and rhetorically unique under the existing series authority.

## 6. Required product behavior

The series workspace must expose two understandable entry paths:

- **Создать серию с нуля**;
- **Обновляю существующую серию**.

For the existing-series path, the UI must support importing a reference manuscript at least from practical local text formats and clearly state that it is used only as a delivery/quality reference, not as reusable book content.

The selected Series Profile must preserve reference identity/hash/provenance and the active reference used by generation must be auditable.

## 7. Model routing

The reference mechanism is model-neutral. Astra and Sol may both consume the same resolved Series Profile + bounded Delivery Reference calibration. Model choice must not alter authority semantics, exclusion rules or uniqueness gates.
