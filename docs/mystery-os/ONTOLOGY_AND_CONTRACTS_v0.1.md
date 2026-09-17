# MYSTERY OS — ONTOLOGY AND CONTRACTS v0.1

**Status:** INCUBATION DRAFT  
**Date:** 2026-09-17

## 1. Design goal

MYSTERY OS extends BOOK OS with fiction-specific authority objects. It must not flatten a mystery novel into one mutable manuscript file or one giant prompt.

The core rule is:

`objective story truth != character knowledge != reader knowledge != prose presentation`

Every quality-critical object is versioned, traceable and subject to human authority where material.

## 2. Core entities

### `GenreProfile`
Defines subgenre expectations and optional constraints.

Minimum fields:
- `profile_id`;
- `name`;
- `primary_genre`;
- `secondary_genres[]`;
- `fair_play_mode: REQUIRED | EXPECTED | RELAXED`;
- `supernatural_mode: NONE | AMBIGUOUS | REAL`;
- `procedural_depth`;
- `violence_level`;
- `romance_weight`;
- `tone`;
- `reader_expectations[]`;
- `hard_exclusions[]`.

### `StoryDefinition`
Book-level fiction contract.

Minimum fields:
- reader/market;
- one-sentence premise;
- primary mystery question;
- secondary mystery questions;
- protagonist/narrative engine;
- stakes;
- tone/darkness;
- setting function;
- reality/supernatural contract;
- unique angle;
- target length;
- ending/satisfaction promise at non-prose abstraction;
- series role;
- explicit exclusions;
- anti-cliche risks;
- commercial hook statement.

### `CaseSolution`
Private objective case truth.

Minimum fields:
- incident/crime identity;
- actual sequence of events;
- responsible actors;
- motive(s);
- means;
- opportunity/access;
- preparation;
- intended outcome vs actual outcome;
- concealment/staging;
- mistakes/traces;
- witnesses/accomplices;
- knowledge map;
- lies and secrets;
- proof chain;
- unresolved ambiguity allowed by design.

`CaseSolution` is spoiler authority and MUST NOT be exposed wholesale to a reader-facing blurb/export.

### `MysteryQuestion`
Tracks one question the narrative asks.

Fields:
- text;
- scope: BOOK | SUBPLOT | SERIES;
- open/closed;
- evidence dependencies;
- intended reveal window;
- final answer;
- residual ambiguity;
- payoff location.

### `Character`
Persistent character identity.

Fields include:
- role;
- external goal;
- internal need;
- fear;
- contradiction;
- competencies;
- limitations;
- secrets;
- voice markers;
- relationships;
- case knowledge at each time;
- recurring-series continuity markers.

### `CharacterKnowledgeState`
Time-bound state of what a character knows/believes.

Fields:
- character;
- timestamp/scene boundary;
- facts known;
- false beliefs;
- hypotheses;
- secrets held;
- information intentionally withheld;
- source of each knowledge item.

This prevents characters from acting on information they never received.

### `Suspect`
A case-role overlay on a Character.

Fields:
- connection to victim/case;
- plausible motive;
- means;
- opportunity;
- alibi;
- alibi weaknesses;
- suspicious behavior;
- true explanation;
- secrets;
- evidence for suspicion;
- evidence against suspicion;
- status transitions.

### `Secret`
Truth deliberately concealed by one or more characters.

Fields:
- actual truth;
- holders;
- reason for concealment;
- disclosure risk;
- lies used;
- evidence leakage;
- reveal location;
- relevance: CORE_CASE | SIDE_SECRET | CHARACTER | SERIES.

### `Clue`
A real information-bearing object/event/detail.

Fields:
- origin/cause;
- type;
- objective meaning;
- who can discover it;
- discoverability constraints;
- first appearance;
- reader exposure location;
- interpretations[];
- dependency on other clues;
- necessity: DECISIVE | MATERIAL | CORROBORATING | OPTIONAL;
- reveal/recontextualization point;
- payoff status;
- fair-play status.

### `RedHerring`
A misdirection anchored in real causality.

Fields:
- underlying true fact;
- misleading interpretation;
- who promotes/accepts that interpretation;
- why it is plausible;
- collapse condition;
- cleanup/explanation;
- relation to culprit manipulation if any.

### `EvidenceChain`
Connects clues to hypotheses/solution.

Fields:
- proposition;
- supporting clues;
- contradicting clues;
- exclusions;
- confidence/strength;
- alternate explanations;
- final disposition.

This is separate from nonfiction Research Evidence. Fiction evidence proves in-world propositions; real-world research supports factual realism.

### `CaseTimeline`
Objective chronology independent from chapter order.

Fields:
- absolute or relative time;
- event;
- actors present;
- location;
- source/authority;
- uncertainty;
- linked clues;
- linked scene(s);
- travel/access feasibility.

### `NarrativeTimeline`
Order in which the reader experiences scenes/information.

Separating case vs narrative timelines is mandatory whenever flashbacks, non-linear structure, retrospective testimony or delayed revelation are used.

### `Location`
Fields:
- identity;
- geography/layout;
- access points;
- visibility/acoustics;
- security/cameras/locks;
- travel times;
- case relevance;
- continuity facts.

### `MysticRuleSet`
Private authority for supernatural causality.

Fields:
- phenomenon/entity;
- ontology (known/unknown bounds);
- capabilities;
- limitations;
- triggers;
- costs;
- reliability;
- deception capability;
- observability;
- physical consequences;
- perceivers/users;
- reader disclosure requirements;
- unknowns intentionally preserved;
- prohibited expansions after lock.

### `MysticEvent`
One supernatural event linked to the rule set.

Fields:
- event;
- timestamp;
- location;
- participants/perceivers;
- rule(s) invoked;
- physical trace;
- subjective perception;
- alternative mundane interpretation;
- narrative function;
- downstream consequence.

### `CharacterArc`
Tracks meaningful character change across one book.

Fields:
- starting state;
- pressure points;
- choices;
- reversals;
- ending state;
- relation to case;
- unresolved series continuation.

### `RelationshipArc`
Tracks dynamic between two or more recurring characters.

Fields:
- initial relationship state;
- tensions;
- trust/debt/conflict changes;
- key scenes;
- current boundary;
- prohibited repetition of prior beat;
- next-book reserved possibilities.

### `RevealPlan`
Controls when and how information changes meaning.

Fields:
- revelation;
- prerequisite clues;
- earliest permissible point;
- intended reveal location;
- viewpoint;
- immediate consequence;
- what remains unknown after reveal;
- anti-cliche risk;
- fairness check.

### `SceneContract`
Writing-admission unit.

Minimum fields:
- scene_id;
- viewpoint;
- time/location;
- purpose;
- entering state;
- exiting state;
- mystery question affected;
- clue/revelation operations;
- suspect/hypothesis movement;
- character/relationship movement;
- tension source;
- prohibited disclosure;
- continuity constraints;
- required factual research;
- anti-cliche warnings;
- audio/listenability notes if relevant.

### `AntiClicheFinding`
Fields:
- code;
- severity;
- location/object;
- matched pattern;
- why it is generic/cheap/repetitive;
- series collision reference if any;
- suggested action;
- human disposition.

### `AntiClicheException`
Human-gated exception for a BLOCKED-BY-DEFAULT device.

Fields:
- cliche/trope code;
- exact proposed use;
- reinvention rationale;
- expected reader familiarity;
- material transformation;
- alternatives considered;
- series collision check;
- human disposition.

### `MysteryBenchRun`
Version-bound quality evaluation.

Fields:
- evaluated authority/manuscript revisions;
- dimensions;
- findings;
- blockers;
- model/tool provenance;
- cold-reader outputs;
- human dispositions;
- rerun supersession links.

### `ColdReaderRun`
Blind-reader style evaluation where the evaluator is not given `CaseSolution`.

Fields:
- manuscript checkpoint;
- revealed text range;
- suspected culprit(s);
- working hypotheses;
- perceived clues;
- confusion points;
- predicted twists;
- engagement/tension diagnosis;
- confidence;
- whether final solution felt earned after reveal.

## 3. Graph relationships

Key edges include:

- `StoryDefinition -> CaseSolution`;
- `CaseSolution -> CaseTimeline`;
- `CaseSolution -> Suspect`;
- `CaseSolution -> EvidenceChain`;
- `MysticRuleSet -> MysticEvent`;
- `Clue -> CaseTimelineEvent`;
- `Clue -> EvidenceChain`;
- `Clue -> SceneContract`;
- `RedHerring -> Clue/Secret`;
- `RevealPlan -> Clue(s)`;
- `RevealPlan -> SceneContract`;
- `Character -> CharacterKnowledgeState`;
- `Character -> CharacterArc`;
- `Character -> RelationshipArc`;
- `SceneContract -> NarrativeTimeline`;
- `MysteryBenchRun -> exact authority/manuscript revisions`;
- `LiteraryMaster -> exact accepted MYSTERY OS authority pack`.

## 4. Staleness rules

Material authority changes must invalidate dependent objects.

Examples:

- changing culprit/motive/mechanism invalidates CaseSolution dependents, ClueLedger, EvidenceChains, Timeline, RevealPlan, affected SceneContracts and MysteryBench;
- changing MysticRuleSet invalidates MysticEvents and any clue/reveal/scene that depends on modified rules;
- moving a clue to a later scene may invalidate fair-play and ColdReader results;
- changing travel/location facts invalidates timeline feasibility;
- changing recurring-character history invalidates later Series Bible/continuity checks;
- changing prose alone does not invalidate case authority unless meaning/information exposure changes.

Staleness must be structural, not a vague “rerun everything just in case”.

## 5. Public vs private authority

Some objects are safe for author UI; others contain full spoilers.

Suggested visibility classes:

- `AUTHOR_NORMAL`: StoryDefinition, character cards, scene plan;
- `AUTHOR_SPOILER`: CaseSolution, culprit identity, clue meanings, reveal plan;
- `READER_DERIVED`: blurb, annotation, sample, metadata;
- `SYSTEM_PRIVATE`: evaluation traces, internal model reasoning artifacts where retained, cost/provenance;
- `PUBLIC_REPO_FORBIDDEN`: private manuscript text, unpublished proprietary series bible, private evaluation corpus.

The public software repository contains schemas/specs, not unpublished story content.

## 6. Human authority

The Owner/human author must approve at least:

- StoryDefinition;
- CaseSolution before systematic drafting;
- Series Bible/series engine;
- material recurring characters;
- any AntiClicheException for blocked devices;
- material post-lock solution changes;
- final Literary Master.

AI may generate candidates but cannot self-approve these objects.

## 7. Reuse principle

Where BOOK OS already has a compatible primitive, MYSTERY OS extends rather than duplicates it.

Examples:

- StyleProfile remains shared;
- Author/Series hierarchy remains shared;
- LiteraryMaster remains shared;
- general revision/provenance/cost primitives remain shared;
- Research Source/Evidence remains shared for real-world factual research;
- Book Memory remains shared and gains fiction-specific indexing;
- BookBench infrastructure remains shared while `MysteryBench` adds genre dimensions.