# MYSTERY OS — PROFESSIONAL FICTION BENCHMARK v0.1

**Status:** INCUBATION DRAFT  
**Date:** 2026-09-18

## 1. Purpose

MYSTERY OS must not certify itself against criteria it invented and then declare success.

The `Professional Fiction Benchmark` provides an external reference protocol for evaluating whether a manuscript approaches the craft level of professionally acquired, edited and published commercial fiction in the target genre.

This benchmark does **not** copy prose, imitate a living author's voice, reproduce protected text or claim objective artistic ranking.

It compares observable craft properties and reader experience.

## 2. Core principle

Internal correctness asks:

> Did the system build the book consistently?

Professional benchmarking asks:

> Does the resulting novel hold up when compared with strong real books readers already choose?

Both are required.

## 3. Benchmark corpus

For each target subgenre maintain a curated `FictionBenchmarkSet` containing metadata and editorial observations about strong reference works.

The corpus should include a balanced mix where lawful/access-appropriate:

- established-publisher commercial successes;
- critically respected genre works;
- durable backlist titles;
- recent successful titles reflecting current reader expectations;
- text and audio when audio is strategically important;
- different authors to avoid mistaking one author's mannerisms for universal quality.

Do not use only bestsellers. Sales can reflect brand and marketing as well as craft.

Do not use only award winners. Literary prestige can optimize for a different reader promise.

## 4. Rights boundary

The benchmark system stores only what is lawful and necessary.

Public repository must never contain copyrighted benchmark manuscripts.

Permitted internal benchmark artifacts may include:

- bibliographic metadata;
- public descriptions;
- high-level editorial observations;
- user-owned/licensed extracts when legally usable;
- derived non-reconstructive metrics;
- human notes;
- model evaluation outputs that do not reproduce substantial protected expression.

Do not train or prompt the system to "write like [living author]".

Use references to measure qualities, not imitate signature language.

## 5. Benchmark dimensions

### B1 — Premise identity

Evaluate:
- immediate specificity;
- genre legibility;
- freshness beyond trope labels;
- capacity to sustain a novel;
- promise/actual-delivery alignment.

### B2 — Narrative engine

Evaluate:
- why the reader continues;
- how pressure renews;
- whether the middle evolves rather than repeats;
- whether story movement depends on character decisions.

### B3 — Character distinctiveness

Evaluate:
- agency;
- contradiction;
- voice recognition;
- believable error;
- relational specificity;
- change under pressure;
- desire to follow recurring leads into another book.

### B4 — Scene quality

Evaluate:
- clear but non-mechanical scene purpose;
- conflict/pressure;
- state change;
- subtext;
- consequence;
- economy;
- scene-to-scene propulsion.

### B5 — Dialogue

Evaluate:
- voice distinction;
- subtext;
- power movement;
- exposition control;
- rhythm;
- avoidance of generic banter and info-dumps.

### B6 — Mystery construction

Evaluate:
- CaseSolution credibility;
- clue lifecycle;
- alternate hypotheses;
- fair-play quality;
- reveal surprise/inevitability balance;
- proof sufficiency;
- emotional consequence of solution.

### B7 — Suspense / information control

Evaluate:
- pressure curve;
- uncertainty management;
- knowledge asymmetry;
- variation in intensity;
- chapter propulsion without cheap bait.

### B8 — Prose / voice

Evaluate:
- precision;
- rhythm;
- viewpoint embodiment;
- specificity;
- restraint;
- image freshness;
- authorial identity;
- absence of machine-default smoothness.

### B9 — Setting

Evaluate:
- functional integration;
- authenticity;
- social/geographic specificity;
- causal effect on plot;
- atmosphere without generic shorthand.

### B10 — Emotional architecture

Evaluate:
- attachment to characters;
- emotional consequence of plot turns;
- relationship movement;
- earned vulnerability;
- avoidance of melodramatic shortcuts.

### B11 — Whole-book structure

Evaluate:
- opening strength;
- first-quarter establishment;
- midpoint transformation;
- third-quarter escalation;
- climax preparation;
- ending resonance;
- removable/dead stretches.

### B12 — Originality / anti-template

Evaluate:
- dependence on stock devices;
- transformation of familiar tropes;
- predictability to experienced genre readers;
- identity after removing names/setting labels;
- series differentiation.

### B13 — Audio performance readiness

Where relevant:
- first-listen comprehensibility;
- name/character differentiation;
- auditory clue clarity;
- dialogue readability aloud;
- sentence rhythm;
- visual-only dependency.

## 6. Comparative protocol

Benchmarking should use three forms of comparison.

### A. Criterion-referenced

Compare manuscript to explicit professional standards.

### B. Pairwise/blind

Where lawful and practical, evaluators compare bounded de-identified samples/derived descriptions without knowing which text came from which system/model.

The purpose is not to crown a universal winner but to detect material quality gaps.

### C. Distributional / corpus-level

Compare derived metrics across a benchmark set, for example:

- scene-length distribution;
- dialogue proportion;
- POV-switch frequency;
- repeated phrase density;
- chapter-end pattern repetition;
- character speaking-turn concentration;
- lexical/syntactic repetition;
- clue spacing;
- exposition density proxies.

Metrics are diagnostics, not style targets.

## 7. No mimicry rule

A benchmark result must never say:

- make the prose more like a named living author;
- copy this author's sentence rhythm;
- reproduce this series' twist architecture;
- imitate signature metaphors, diction or voice.

Allowed form:

- our dialogue is more expository than the professional benchmark range;
- our midpoint does not materially change the case model;
- our recurring leads show lower agency density than strong comparables;
- our chapter endings rely on repeated teaser syntax;
- our setting has less causal function than selected references.

## 8. Benchmark-set construction

Each set should record:

- subgenre;
- target market/language;
- publication period;
- format;
- publisher/imprint where relevant;
- audience/content rating;
- series/standalone status;
- why each reference was selected;
- what it should **not** be used to infer;
- source/access rights status;
- date last reviewed.

Avoid one-book or one-author monoculture.

## 9. Sample selection

Whole-book evaluation is preferred for structure when lawful/available.

For bounded craft comparison, sample functions rather than arbitrary pages:

- opening;
- first major investigation scene;
- dialogue-heavy scene;
- midpoint;
- high-tension scene;
- reveal/climax;
- quiet aftermath/ending.

This prevents cherry-picking only polished openings.

## 10. Evaluator independence

The model that drafted a scene should not be the sole benchmark judge.

Use, where justified:

- deterministic diagnostics;
- independent model judge;
- alternate provider/model judge when available;
- ColdReader evidence;
- human editorial judgment.

Evaluator identity and prompt/version must be recorded.

## 11. Benchmark finding structure

A `FictionBenchmarkFinding` should contain:

- dimension;
- manuscript location/scope;
- benchmark set/version;
- observation;
- evidence/examples from our manuscript;
- non-infringing high-level comparison;
- severity: `BLOCKING | MAJOR | MINOR | NOTE`;
- recommended editorial action;
- human disposition;
- rerun status.

No opaque global score.

## 12. Quality bands

MYSTERY OS may use descriptive readiness bands only if they cannot hide blockers.

Suggested internal bands:

- `BELOW_PROFESSIONAL_FLOOR`;
- `PROFESSIONAL_GAPS_REMAIN`;
- `PROFESSIONAL_RANGE_CANDIDATE`;
- `STRONG_PROFESSIONAL_CANDIDATE`.

These are diagnostic labels, not marketing claims.

No book may enter a higher band while a dimension-critical BLOCKING defect remains unresolved.

## 13. Gate points

Professional benchmarking should occur selectively.

### Before full drafting

Benchmark premise/series engine/character package at high level.

### After representative sample

Benchmark 2–4 strong representative scenes before investing in an entire weak prose mode.

### Mid-book

Benchmark structural and character trajectory, not line polish only.

### Whole-book candidate

Run comprehensive benchmark before final Literary Master approval.

This prevents expensive late discovery that the prose or dramatic execution was never competitive.

## 14. Representative Sample Gate

Before mass drafting, MYSTERY OS should produce a small approved `RepresentativeFictionSample` after core authority is locked.

Suggested contents:

- opening scene/chapter;
- one investigation/dialogue scene;
- one tension/supernatural scene if applicable;
- optionally one quiet character scene.

The sample is evaluated for:

- voice;
- POV integrity;
- dialogue;
- scene causality;
- suspense;
- anti-cliche drift;
- listenability;
- benchmark gap.

If the sample fails materially, fix StyleProfile/NarrativeContract/Writer routing before drafting 250k+ characters.

## 15. Model-routing implication

Premium/Astra-class execution is especially justified for:

- benchmark-set interpretation;
- comparative premise architecture;
- whole-book developmental comparison;
- final gap diagnosis;
- hard scenes where ordinary Writer repeatedly fails benchmark.

Routine benchmark metrics and repetition checks should remain deterministic/local where possible.

Do not pay frontier cost to count what software can count.

## 16. Cost discipline

Benchmarking does not mean comparing every paragraph against dozens of books.

Use staged sampling:

1. cheap deterministic diagnostics;
2. representative bounded samples;
3. escalate only material uncertainties;
4. whole-book premium review at major gates.

The cost question is:

> Where does stronger evaluation change an editorial decision enough to justify its cost?

## 17. Human benchmark review

Before final release, human review should answer:

- Does this feel authored rather than assembled?
- Are the characters memorable outside their plot functions?
- Does the middle sustain interest without formula repetition?
- Would an experienced genre reader see the twist machinery too early?
- Is the prose merely competent or does it have identity?
- Does the novel compare credibly with books a professional reader can buy from established publishers today?
- Would we still approve it if no one knew AI was involved?

## 18. Release rule

Passing MysteryBench is necessary but not sufficient.

A manuscript intended for the MYSTERY OS premium target cannot be released as quality-complete while a Professional Fiction Benchmark run still reports unresolved material gaps in core dimensions unless the human Owner explicitly accepts that trade-off.

## 19. Principle

The benchmark exists to protect MYSTERY OS from grading its own homework.