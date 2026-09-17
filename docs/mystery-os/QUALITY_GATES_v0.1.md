# MYSTERY OS — QUALITY GATES / MYSTERYBENCH v0.1

**Status:** INCUBATION DRAFT  
**Date:** 2026-09-17

## 1. Principle

Mystery quality is multi-dimensional. No aggregate score can average away a broken solution, impossible timeline, unfair decisive clue, unbounded supernatural rule, cliche-dependent architecture or contradictory character knowledge.

Quality decisions use findings by severity:

- `BLOCKING` — writing/release cannot continue;
- `MAJOR` — material rewrite required or explicit human disposition;
- `MINOR` — should be corrected unless intentionally retained;
- `NOTE` — non-blocking observation.

## 2. Pre-writing gates

### G0 — Commercial / reader promise

PASS requires:
- clear target reader/subgenre;
- premise understandable without a long explanation;
- specific hook beyond generic trope labels;
- recognizable genre promise;
- non-cosmetic differentiation from crowded comparables;
- plausible series position if applicable;
- no unresolved BLOCKED-BY-DEFAULT cliche.

FAIL examples:
- “mysterious murders happen in a small town” with no further identity;
- premise is a bundle of fashionable tropes;
- novelty exists only in profession/location naming;
- series sequel repeats prior book with a new victim.

### G1 — Story Definition

PASS requires approved StoryDefinition with scope, stakes, tone, reality contract, protagonist engine, target length, exclusions and primary mystery question.

### G2 — Case Solution integrity

BLOCKING checks:
- culprit/responsible actor known internally;
- motive/means/opportunity coherent;
- objective event chain complete;
- concealment feasible;
- clue-generating traces causally exist;
- final proof path exists independently of confession;
- no indispensable late invention.

### G3 — Supernatural rules

Required when supernatural causality is material.

BLOCKING checks:
- capabilities/limits declared;
- decisive rules exist before prose depends on them;
- supernatural event mapping does not contradict physical case truth;
- visions/messages have defined reliability constraints;
- no unlimited clue-delivery power.

### G4 — Suspect / clue / timeline architecture

PASS requires:
- plausible suspect field appropriate to profile;
- suspects differentiated;
- real secrets/lies have causes;
- enough evidence for eventual solution;
- meaningful alternate hypotheses;
- case timeline feasible;
- narrative disclosure plan supports fair play.

### G5 — Anti-cliche / series novelty

BLOCKING when:
- a blocked device has no approved exception;
- core architecture is a cosmetic reskin of a prior series book;
- culprit, motive, reveal and supernatural mechanism reproduce an earlier pattern closely enough to make outcome predictable;
- concept depends on multiple cheap cliches rather than one distinctive causal engine.

## 3. Writing admission

Every scene/chapter receives `WRITING_ALLOWED` only when its SceneContract is fresh relative to current authority.

Admission checks:
- time/location available;
- character knowledge states valid;
- clue/reveal operations valid;
- no premature disclosure;
- research dependencies either satisfied or explicitly bounded;
- anti-cliche warnings present;
- scene has a state-changing function.

Writer execution must fail closed before provider/model access if admission is missing or stale.

## 4. Draft-time deterministic audits

### Timeline audit
Checks:
- overlapping locations;
- impossible travel;
- alibi contradictions;
- time-of-death/window contradictions;
- device/camera/log timestamp consistency;
- day/date/week continuity;
- supernatural timing constraints.

### Knowledge audit
Checks:
- character refers to facts never learned;
- viewpoint withholds its own conscious decisive knowledge unfairly;
- investigator forgets known evidence for convenience;
- suspect changes story without the manuscript registering inconsistency.

### Clue lifecycle audit
Each material clue must be:
- caused;
- introduced;
- observed or intentionally missed;
- interpreted/reinterpreted;
- paid off, excluded or deliberately left unresolved.

Orphaned decisive clue = BLOCKING. Repeated nonfunctional clue = MAJOR.

### Rule audit
No case/supernatural rule may silently change to fit a later scene.

## 5. Mid-book gate

Mandatory around the structural midpoint, not necessarily 50.0% word count.

Audit dimensions:

### Mystery movement
Has the working model of the case changed materially, or have scenes merely accumulated interviews?

### Evidence balance
Are enough clues visible to sustain fair play? Is the true solution trivially over-signalled? Are alternate hypotheses alive for real reasons?

### Character pressure
Are choices becoming harder? Are recurring leads changing through action rather than exposition?

### Supernatural discipline
Has any phenomenon gained undeclared capabilities? Is mysticism replacing detection rather than complicating it?

### Pacing
Is there a dead zone of recap, travel, repeated questioning or atmosphere without change?

### Cliche drift
Did drafting fall back onto stock horror beats, stock dialogue, standard villain behavior or AI prose patterns not present in architecture?

Any BLOCKING finding pauses further admitted drafting.

## 6. Whole-book MysteryBench dimensions

### A. Case coherence
- objective event chain;
- motive/means/opportunity;
- concealment;
- evidence causality;
- proof sufficiency.

### B. Fair play
- decisive clues reader-visible;
- no hidden indispensable rule/fact;
- alternate hypotheses plausible;
- reveal reconstructable after the fact.

### C. Reveal quality
- surprise;
- inevitability after reveal;
- emotional consequence;
- no arbitrary reversal;
- denouement clarity without lecture dump.

### D. Suspect quality
- differentiation;
- credible motives/secrets;
- no cardboard suspects;
- suspicion evolves through evidence.

### E. Character causality
- knowledge/action consistency;
- believable choices;
- competence limits;
- emotional/relationship arcs.

### F. Supernatural integrity
- consistent rules;
- bounded powers;
- causal integration;
- no deus ex machina;
- retained mystery is intentional.

### G. Tension / pacing
- early genre promise;
- escalating cost;
- scene state change;
- information rhythm;
- absence of dead loops;
- earned climax.

### H. Originality / anti-cliche
- no unresolved blocked devices;
- trope transformation quality;
- distinctive characters/case/setting;
- absence of machine-template structures;
- series novelty.

### I. Prose / voice
- StyleProfile compliance;
- viewpoint integrity;
- dialogue distinctiveness;
- concrete/sensory specificity;
- AI-prose pathology detection;
- absence of fake profundity and melodramatic shorthand.

### J. Setting function
Setting must affect choices, access, danger, atmosphere or theme; decorative location swaps should not leave the book unchanged.

### K. Research realism
Material real-world procedures/facts are verified or intentionally fictionalized with recorded rationale.

### L. Audio readiness
When audio is selected:
- names/terms pronounceable;
- dialogue attribution intelligible;
- visual-only clues have an audible equivalent in prose;
- timelines/names are not impossibly confusing on first listen;
- tables/screens/messages are adapted appropriately.

## 7. Cold Reader protocol

A Cold Reader evaluator receives manuscript slices without CaseSolution.

Suggested checkpoints:
- early establishment;
- roughly first quarter;
- midpoint;
- roughly three quarters;
- immediately before final reveal;
- after reveal.

At each checkpoint record:
- current top suspects;
- confidence;
- perceived motive(s);
- noticed clues;
- unresolved questions;
- predicted twist(s);
- confusion vs productive uncertainty;
- tension/engagement drops.

After reveal record:
- whether solution was inferable;
- whether solution felt earned;
- which clue became satisfying in retrospect;
- which explanation felt invented late;
- whether any alternative remains stronger.

Cold Reader is evidence, not final authority.

## 8. Adversarial Case Reconstruction

An independent evaluator receives:
- final manuscript;
- no author explanation initially.

Task 1: reconstruct what happened solely from text.

Then compare reconstruction to accepted CaseSolution.

BLOCKING if:
- reconstruction requires facts absent from manuscript;
- timeline cannot be made feasible;
- more plausible alternate culprit fits accepted evidence better;
- final solution contradicts narrative facts;
- supernatural rule required by solution was never established.

## 9. Anti-cliche scan

Runs at concept, architecture, midpoint and final manuscript.

Checks at least:
- blocked trope registry;
- prior books in same series;
- repeated scene functions;
- repeated reveal mechanics;
- recurring dialogue/prose patterns;
- default supernatural shorthand;
- stock character packages;
- cosmetic reskin similarity.

A flag must show exact location/examples and rationale; no opaque “cliche score”.

## 10. Series closure gate

Before release of a series book, bind exact Literary Master to:
- Series Bible version;
- Book Passport;
- difference map vs prior books;
- used/reserved series assets;
- recurring-character continuity state;
- unresolved series questions;
- anti-collision findings/dispositions.

## 11. Release blockers

Literary Master cannot be approved with unresolved:
- impossible case/timeline;
- decisive unfair clue/fact;
- contradictory culprit/motive mechanism;
- undeclared decisive supernatural power;
- broken character knowledge causality;
- unapproved blocked cliche;
- material plagiarism/clone concern;
- series duplicate architecture;
- missing main mystery payoff promised by StoryDefinition.

## 12. No false certainty

Deterministic checks can prove some structural properties. LLM judges and Cold Reader tests provide diagnostic evidence. Human editorial judgment remains mandatory for literary quality, emotional power, originality and final release.