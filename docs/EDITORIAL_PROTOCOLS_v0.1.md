# BOOK OS — EDITORIAL PROTOCOLS v0.1

**Status:** ACCEPTED FOR V0.1 IMPLEMENTATION  
**Version:** 0.1.0  
**Date:** 2026-08-22

## 1. Purpose

This document specifies the structured editorial contracts, bounded roles and human-acceptance workflow used by BOOK OS v0.1.

## 2. Book Contract v0.1

`BookContract` is a versioned authority-bearing object.

### Required fields

- `reader`: who the book is for;
- `reader_problem`: what meaningful problem/tension the reader brings;
- `central_promise`: what the book promises to deliver;
- `central_thesis`: the central claim/idea the book argues;
- `unique_angle`: why this book is not merely a restatement of the category;
- `reader_trajectory`: intended intellectual/behavioral shift across the book;
- `explicit_exclusions`: what the book deliberately does not attempt;
- `evidence_policy`: standards appropriate to the profile/subtype;
- `voice_genre_constraints`: high-level voice and genre boundaries;
- `readiness_criteria`: what must be true before the manuscript can be released.

### Recommended fields

- working title/subtitle candidates;
- key objections/counter-theses to answer;
- claims that would destroy the thesis if disproven;
- expected use of case studies, data, personal experience and frameworks;
- target complexity/reader knowledge level;
- target length range as a planning constraint, not a quality target.

### Gate

A draft Book Contract may be researched and challenged. Systematic book architecture/drafting cannot treat it as settled authority until human approval.

## 3. Chapter Contract v0.1

Each chapter must have a versioned contract before bounded drafting.

### Required fields

- `chapter_purpose`;
- `new_contribution`: the distinct idea/function contributed by this chapter;
- `reader_prior_state`;
- `reader_after_state`;
- `required_claims`;
- `required_or_permitted_research`;
- `required_scenes_examples`;
- `reserved_elsewhere`: ideas/examples explicitly owned by other chapters;
- `opening_requirements`;
- `ending_requirements`;
- `transition_requirements`.

### Recommended fields

- likely objections;
- emotional/intellectual rhythm;
- key concepts introduced/reused;
- forbidden shortcuts/clichés;
- soft length budget;
- evidence risk areas.

## 4. Editorial finding schema

Every diagnosis that may trigger change should be structured as:

- `DIAGNOSIS`
- `LOCATION`
- `BASE_REVISION`
- `WHY`
- `EVIDENCE`
- `SEVERITY`
- `CONFIDENCE`
- optional `PROPOSED_CHANGE`
- `EXPECTED_EFFECT`
- `RISKS`

A finding is not an edit.

## 5. Change proposal schema

A material proposal must include:

- exact target stable ID(s);
- exact base revision(s);
- human-readable diff or replacement preview;
- rationale linked to finding/task;
- expected effect;
- evidence/claim implications;
- architecture/contract implications;
- voice/style implications;
- risk/confidence;
- provenance: actor, provider/model, task/prompt version.

If the baseline changed after the proposal was created, it becomes `STALE` and cannot be accepted without rebase/review.

## 6. Editorial roles and permissions

Roles are bounded workflows/configurations, not autonomous personalities with unlimited access.

| Role | May do | May not do |
|---|---|---|
| Researcher | Form research queries, discover sources, normalize metadata | Invent citations, approve claims |
| Evidence Analyst | Link claims to supporting/contradicting evidence, assess limitations | Turn a source into “proof” without analysis |
| Book Architect | Propose thesis/architecture options, test chapter functions | Lock architecture without human approval |
| Drafting Writer | Draft bounded manuscript units against contracts | Rewrite approved whole book, self-approve |
| Developmental Editor | Diagnose structure, clarity, argument, chapter function | Mutate authority silently |
| Cross-book Auditor | Find repetition, contradiction, forgotten promises, duplicated examples | Delete/merge content directly |
| Fact Checker | Verify material claims against retrieved evidence | Approve unsupported claims as factual |
| Literary Editor | Improve prose/rhythm/clarity through proposals | Override Book/Chapter Contracts silently |
| Style Guardian | Detect voice drift and AI-prose pathologies | Enforce style by blind global rewrite |
| Skeptical Reader | Attack assumptions, weak logic, reader confusion | Establish facts without evidence |
| BookBench Judge | Evaluate exact revisions using versioned rubrics/checks | Change manuscript authority |
| Acceptance Controller | Verify required gates/evidence are present | Substitute for Owner on material creative acceptance |

## 7. Multi-model rule

For high-value text/architecture decisions:

`model/actor A proposes → independent model/actor B critiques → deterministic/semantic checks → human decision`

The same model may be reused when no alternative exists, but the run must be independently prompted/configured and must never be treated as equivalent to independent multi-model evidence. High-stakes BookBench can require different providers when available.

## 8. Human acceptance workflow

### Decision Inbox

The user sees material pending decisions in one place.

For each item:

- what is wrong / opportunity;
- exact location and baseline;
- why it matters;
- proposed patch/diff;
- evidence/BookBench support;
- risks/confidence;
- buttons: `ACCEPT`, `REJECT`, `REQUEST REVISION`, `WAIVE`.

### Material changes

Require explicit human decision when changing:

- thesis/promise;
- architecture;
- chapter function;
- meaning/argument;
- material factual claim;
- major example/scene;
- author voice;
- major deletions/moves;
- release master.

### Minor changes

Typographic, punctuation, formatting and clearly mechanical corrections may be proposed and accepted in batches, with preserved audit history.

## 9. Human gates for Book from Zero

1. Book Contract acceptance.
2. Book Architecture acceptance.
3. Chapter Contract acceptance before systematic drafting.
4. Material editorial-change acceptance.
5. Final Literary Master release.

The UI may allow efficient batch review, but gates cannot be hidden.

## 10. Version/provenance rules

- stable entity ID survives edits;
- content change creates a new immutable revision;
- approved/locked revisions are immutable;
- every material proposal identifies exact baseline;
- accepted proposal creates a new authority revision;
- prior authority becomes `SUPERSEDED`, never deleted;
- provenance records model/provider/version, task, prompt-template version/hash and input authority revisions;
- secrets are never stored in provenance;
- rejected proposals remain available as training/eval signals unless the user explicitly purges them.

## 11. Editorial decision corpus — moat

The system must persist, in structured form:

`original → diagnosis → proposed edit → accepted/rejected → reason → final`

This corpus is the primary future source for BookBench calibration, model routing and later fine-tuning/reward modeling. It is private user/project data, not something to publish in the public software repository.
