# BOOK OS — PROSE ANTI-JUNK v0.1

**Status:** ACTIVE QUALITY RULESET  
**Purpose:** prevent recurrent generic AI/marketing prose from entering BOOK OS outputs and make violations visible in BookBench.

## Principle

This is not a ban on ordinary Russian words in legitimate context. The target is recurrent formulaic wording, especially when it substitutes for a concrete thought, argument, scene, mechanism or claim.

A single lexical item may be valid in context. A listed phrase/template is a quality violation when used as a stock rhetorical frame, title/subtitle formula, transition, conclusion, or generic promise.

## High-priority banned templates

### Decorative contrast / negative framing

- `это не про X, а про Y`
- `эта книга не про X, а про Y`
- `книга не про X, а про Y`
- `эта книга не о том, ...`
- `эта книга не о ...`
- `речь не о ...`
- `здесь речь не о ...`
- `дело не в X, а в Y`
- `не X, а Y` when used as a stock rhetorical contrast rather than a necessary factual distinction

Rule: state the actual thesis directly. Do not manufacture a false alternative merely to create rhetorical contrast.

### “Без …” marketing formulas

Avoid generic title/subtitle/promise constructions such as:

- `без ручного управления`
- `без хаоса`
- `без давления`
- `без лишней суеты`
- `без лишнего шума`
- `без стресса`
- `без выгорания`
- `без страха`
- `без усилий`
- `без перегруза`
- `без потери контроля`

The word `без` itself is not banned. The problem is the ready-made marketing promise formula.

### “Про / не про” framing

- `это про ...`
- `это не про ...`
- `книга про ...` when used as a rhetorical declaration instead of a precise subject statement
- `разговор про ...` as a generic framing move

The preposition `про` is not banned in normal Russian syntax.

### Noise / signal clichés

- `шум`
- `информационный шум`
- `лишний шум`
- `отделить шум от сигнала`

Use only when the literal/technical meaning is necessary and specific.

### Illusion clichés

- `иллюзия`
- `иллюзии контроля`
- `иллюзия выбора`
- `иллюзия безопасности`

Use only when the text identifies a precise mechanism and the word is semantically necessary; not as a generic dramatic label.

### Magic clichés

- `волшебство`
- `магия`
- `чудеса`
- `волшебная таблетка`
- `магическая кнопка`

Avoid as generic explanatory metaphors or marketing shorthand.

### Silence / fuss clichés

- `в тишине`
- `тихие смыслы`
- `без лишней суеты`
- `в суете`
- `суетиться`

Use only for literal description, not generic profundity or atmosphere.

### Change-speed clichés

- `мир меняется`
- `мир быстро меняется`
- `скорость изменений`
- `в быстро меняющемся мире`
- `в современном мире`

Replace with the concrete change, market, technology, rule, behavior or time period actually meant.

### Generic invitation / explainer openings

- `погрузимся`
- `давайте погрузимся`
- `давайте разберёмся`
- `разберёмся, почему`
- `попробуем разобраться`
- `давайте посмотрим`

Start with the actual observation, question, scene, evidence or mechanism instead.

## Existing BOOK OS pathology rules retained

This ruleset supplements existing BookBench signals including:

- artificial `не X, а Y` contrasts;
- `это не про ...`;
- artificial triads;
- generic transitions such as `важно понимать`, `стоит отметить`, `в конечном итоге`, `другими словами`, `на самом деле`, `важно помнить`, `следует понимать`, `в этом контексте`;
- repeated sentence openings;
- empty abstractions;
- repeated opening/ending templates;
- excessive rhetorical questions.

## Enforcement

1. Generation prompts must treat this file as a negative style constraint.
2. BookBench `AI_PROSE_PATHOLOGY` must surface direct matches with location/evidence.
3. Matches are quality findings, not claims of AI authorship.
4. Ordinary lexical use in a necessary literal/technical sense can be kept by explicit human judgment.
5. Titles, subtitles, chapter names, transitions and conclusions receive stricter review because stock formulas there are especially visible.

## Current owner examples

Initial owner-supplied anti-junk examples include:

- `без ручного управления`;
- `без хаоса`;
- `без давления`;
- `про / не про` rhetorical framing;
- `шум`, `информационный шум`;
- `иллюзия`, `иллюзии контроля`;
- `волшебство`, `магия`, `чудеса`;
- `в тишине`, `тихие смыслы`, `без лишней суеты`;
- `в суете`, `суетиться`;
- `мир меняется`, `скорость изменений`;
- `погрузимся`, `давайте разберёмся`;
- `эта книга не про X, а про Y`;
- `эта книга не о том, ...`.
