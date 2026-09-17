# MYSTERY OS — CORE SPECIFICATION v0.1

**Status:** INCUBATION DRAFT — OWNER REVIEW REQUIRED  
**Date:** 2026-09-17  
**Scope:** mystery / crime fiction, including supernatural and crossover variants

## 1. Product identity

MYSTERY OS is an editorial-authoring operating system for creating professionally structured mystery/crime fiction. It is not a generic fiction generator, a beat-sheet template, a one-prompt novel writer, or a system that decides the culprit during drafting.

The system separates five kinds of truth that weak mystery workflows commonly mix together:

1. **case truth** — what actually happened in the fictional world;
2. **character belief** — what each character thinks happened;
3. **investigator hypothesis** — the currently considered explanation;
4. **reader evidence** — what has actually been made available to the reader;
5. **narrative presentation** — the order and form in which scenes reveal information.

A strong mystery can manipulate beliefs and presentation. It may not silently rewrite case truth to rescue the plot.

## 2. Quality responsibility

MYSTERY OS is responsible for helping produce fiction that is strong in all of the following dimensions:

- compelling premise and genre promise;
- coherent crime/case mechanics;
- fair and satisfying clue/reveal logic;
- plausible motive, means, opportunity and concealment;
- internally consistent supernatural mechanics when used;
- character causality rather than plot-puppet behavior;
- scene-level tension and progression;
- emotional involvement and memorable characters;
- distinctive voice and setting;
- structural pacing without dead investigative loops;
- earned twists rather than arbitrary reversals;
- whole-book continuity;
- series novelty and continuity;
- listenability for audio when selected;
- professional release readiness.

No single numeric “mystery score” may override a BLOCKING defect.

## 3. Supported profiles

The architecture must support a profile system rather than hard-code one subgenre.

Initial target profiles:

- classic / fair-play mystery;
- contemporary detective mystery;
- psychological crime mystery;
- police/procedural-adjacent mystery;
- cosy mystery;
- supernatural / mystical mystery;
- mystery-thriller crossover;
- romance/fantasy crossover where the mystery remains a material narrative engine.

A profile may tighten or relax individual expectations, but it may not silently permit broken causality, impossible timelines, retrospective invention of decisive rules, or an unearned solution.

## 4. Core lifecycle

Canonical MYSTERY OS workflow:

`IDEA -> MARKET / READER -> STORY DEFINITION -> CASE SOLUTION -> MYSTIC RULES (if applicable) -> CHARACTER / RELATIONSHIP AUTHORITY -> SUSPECT / CLUE / TIMELINE ARCHITECTURE -> SCENE ARCHITECTURE -> WRITING ADMISSION -> DRAFTING -> MID-BOOK MYSTERY AUDIT -> DEVELOPMENTAL EDIT -> FAIR-PLAY / CASE AUDIT -> WHOLE-BOOK EDIT -> COLD-READER / ADVERSARIAL REVIEW -> FINAL REVIEW -> LITERARY MASTER -> DERIVED OUTPUTS`

Each transition is versioned and auditable.

## 5. Authority statuses

Reuse BOOK OS authority semantics:

`DRAFT -> PROPOSED -> REVIEWED -> APPROVED -> LOCKED`

Historical accepted versions may become `SUPERSEDED`.

AI may propose, diagnose, compare and revise. AI may not self-grant final material approval.

### Locked-solution rule

Before systematic prose drafting, a complete `CaseSolution` must be at least HUMAN APPROVED. Any material change to the solution after writing begins must:

- create a new version rather than mutate the accepted solution;
- invalidate affected clue, timeline, scene and QA authority;
- identify downstream prose made stale;
- require human acceptance before the revised solution can govern further drafting.

This prevents “the killer changed in chapter 22, so the earlier clues were retrofitted”.

## 6. Minimum authority pack before writing

A chapter/scene may not be admitted to systematic writing merely because there is a premise.

Minimum project-level authority:

- `StoryDefinition`;
- accepted `CaseSolution`;
- `GenreProfile`;
- `CharacterBible` for material recurring/primary characters;
- `CaseTimeline` baseline;
- `ClueLedger` baseline;
- `MysticRuleSet` when supernatural causality is material;
- book-level `RevealPlan`;
- series constraints when the book belongs to a series.

Minimum scene-level authority:

- scene purpose;
- viewpoint;
- start state / end state;
- information available entering scene;
- clues/revelations introduced or recontextualized;
- suspect/hypothesis movement;
- character/emotional movement;
- prohibited premature disclosures;
- continuity/time/location constraints;
- exit pressure / consequence.

The Writer must fail closed when a required authority object is absent or stale.

## 7. StoryDefinition

The fiction equivalent of a high-level book contract must define at minimum:

- target reader and subgenre;
- commercial/reader promise;
- one-sentence premise;
- mystery question(s);
- protagonist and narrative engine;
- stakes;
- tone and darkness level;
- reality/supernatural contract with the reader;
- unique angle;
- setting function;
- target length;
- content boundaries;
- ending type / satisfaction promise at the appropriate abstraction level;
- series role, if any;
- explicit exclusions and anti-template risks.

A StoryDefinition is not a spoiler-free blurb. Internally it may contain the complete intended story promise.

## 8. CaseSolution

`CaseSolution` is private spoiler authority describing objective case truth.

It must answer, where applicable:

- what happened;
- who caused it;
- intended vs actual outcome;
- motive(s);
- means;
- opportunity/access;
- preparation;
- sequence of acts;
- concealment / staging / cleanup;
- mistakes and unavoidable traces;
- accomplices / witnesses;
- who knows which parts of the truth;
- what each relevant person lies about and why;
- evidence sufficient to distinguish the correct solution from alternatives;
- what remains unknowable or ambiguous by design.

The final solution must be demonstrable from accepted evidence and causality, not solely from a confession.

## 9. MysteryQuestion model

A novel may carry multiple questions, for example:

- Who killed X?
- Where is the missing person?
- Why are the events repeating?
- What is the apparently impossible mechanism?
- Is the supernatural interpretation true?
- What past act connects the suspects?

Each question has:

- open/closed state;
- evidence dependencies;
- intended reveal window;
- whether it is core, secondary or series-level;
- acceptable residual ambiguity.

The primary book-level mystery must resolve unless the declared subgenre/series contract explicitly promises otherwise.

## 10. Supernatural layer

Supernatural fiction does not suspend causal discipline.

When a material supernatural element exists, `MysticRuleSet` must record:

- ontology/source as far as the author knows;
- capabilities;
- limitations;
- triggers/conditions;
- costs/consequences;
- observability;
- reliability of perceptions/messages;
- whether entities can lie or misunderstand;
- interaction with physical evidence;
- who can perceive/use it;
- what the reader is entitled to know before any rule becomes decisive;
- unresolved uncertainty that is intentional rather than accidental.

A supernatural rule may remain mysterious to characters. It may not be undefined to the production system if it is used causally.

## 11. Clue system

Every material clue is a first-class object with:

- source/event that created it;
- objective meaning;
- discoverability;
- who observes it;
- when the reader receives it;
- current interpretation(s);
- alternate plausible interpretation(s);
- dependency on other clues;
- whether it is necessary, corroborating, exclusionary or atmospheric;
- reveal/recontextualization point;
- payoff status.

A clue cannot exist merely because the author needs it in the final explanation. It must have an in-world cause.

## 12. Red herrings

A red herring is not random misinformation inserted to delay the reader.

Every material red herring must be grounded in at least one real cause:

- a character is hiding something real but non-culpable;
- genuine evidence admits a plausible wrong interpretation;
- a culprit deliberately plants or manipulates evidence and has the means/opportunity to do so;
- an observer makes an understandable error;
- two causal chains overlap.

When the red herring collapses, its underlying reality still has to make sense.

## 13. Character causality

Characters may surprise the reader; they may not act stupidly only to preserve the plot.

For each material decision, the system should be able to answer:

- what the character knows;
- what the character wants;
- what the character fears;
- what constraints apply;
- what alternatives the character perceives;
- why this action is locally rational or emotionally credible for this person.

Repeated “failure to communicate” without a specific character reason is a quality defect.

## 14. Scene architecture

Each scene must perform meaningful work. Valid work includes:

- change the case state;
- change a hypothesis;
- reveal or recontextualize evidence;
- create a new danger/constraint;
- change a relationship in a way that affects future choices;
- force a decision;
- pay off or seed a narrative promise;
- materially deepen setting/atmosphere while advancing another function.

Pure transit, recap and duplicated interrogations are candidates for compression/deletion.

A scene should end with a changed state, not merely a lower word count remaining.

## 15. Mid-book audit

At a configured structural midpoint, drafting pauses for mandatory audit.

The audit asks:

- Is the primary mystery still active and legible?
- Has the investigation materially changed since the first quarter?
- Are too many clues unused or too few available?
- Is one suspect obviously over-signalled?
- Are alternate hypotheses genuinely viable?
- Has the supernatural layer gained undeclared powers?
- Are characters repeating conversations/actions?
- Has the reader learned enough to remain engaged without solving trivially?
- Are planned later reveals still supported by already written material?
- Has series continuity drifted?

A BLOCKING finding prevents further admitted drafting until disposition.

## 16. Final mystery audit

Before Literary Master, the system reconstructs the case independently from the manuscript and authority pack.

It must verify:

- chronology is feasible;
- access/opportunity is feasible;
- physical/digital/social evidence is causally possible;
- the accepted culprit/solution fits all mandatory evidence;
- material contradictory evidence is resolved;
- decisive clues were actually presented;
- decisive rules existed before use;
- final explanation does not introduce indispensable new facts;
- non-culprit suspicious behavior has credible explanations;
- the solution is stronger than major alternatives;
- the investigator's conclusion is supported, not merely intuited.

## 17. Reader fairness vs predictability

The goal is not to make the solution impossible to guess.

A strong result permits an attentive reader to form the correct hypothesis while still making the final reveal satisfying. “Nobody could possibly have known” is generally a defect, not a victory.

The system therefore tracks both:

- **fairness:** sufficient meaningful evidence existed;
- **reveal control:** evidence was distributed and framed so the answer was not trivially announced.

## 18. Model-role separation

Critical operations should not rely on one model writing and certifying itself.

Recommended independent roles:

- Premise/Market Analyst;
- Case Architect;
- Mystery Editor;
- Character/Scene Editor;
- Writer;
- Continuity/Timeline Auditor;
- Fair-Play Auditor;
- Supernatural-Rule Auditor;
- Cold Reader / Suspect Tracker;
- Series Editor;
- Literary Editor;
- Audio Editor.

Operation-level routing remains model/provider agnostic.

## 19. Research and factual reality

Fiction still makes real-world claims.

When the novel uses real police procedure, medicine, law, technology, geography, emergency services, weapons, communications, finance or other factual domains, BOOK OS research/evidence primitives should remain available.

Research truth must be separated from fictional case truth.

Invented procedural details may be intentionally fictionalized, but the decision must be explicit when a reasonable reader could mistake them for real practice.

## 20. Release

A `LiteraryMaster` for a mystery book should reference exact accepted versions/hashes of at least:

- StoryDefinition;
- CaseSolution;
- Character/relationship authority;
- ClueLedger;
- CaseTimeline;
- MysticRuleSet if used;
- final manuscript revisions;
- Style Profile;
- final MysteryBench runs;
- series closure/uniqueness evidence where applicable;
- human release approval.

Derived ebook, print, audio, translation and platform artifacts must not silently mutate upstream authority.