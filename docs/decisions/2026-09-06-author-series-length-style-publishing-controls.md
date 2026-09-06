# Owner Decision — Author / Series / Length / Style / Publishing Controls

**Date:** 2026-09-06  
**Status:** APPROVED / CURRENT  
**Owner:** product owner  
**Scope:** BOOK OS nonfiction workflow  

## Decision

Before the first real quality pilot is treated as representative, BOOK OS must support the full context in which a professional nonfiction book is actually created and packaged for publication. A book is not an isolated text object.

The required hierarchy is:

`Author Profile → optional Series Profile → Book Contract → Architecture / Chapter Contracts → Literary Master`

A standalone book remains valid. A Series Profile is optional, but when a book belongs to a series its accepted series-level constraints are inherited and may not be silently ignored by planning, drafting, editing, BookBench or final review.

The existing series **«Право на себя»** and its current `AUTHOR-BRAIN-ELENA-DILON.md` / `SERIES-BRAIN.md` in `niknikdym-hue/books-for-litres` are the first real evidence corpus for this feature. They are input/reference data for the pilot, not hard-coded system rules and not a runtime dependency of BOOK OS. BOOK OS must model these concepts generically so another author or series can use the same capabilities.

## 1. Author Profile

BOOK OS must support a reusable author-level profile containing at least:

- author / pen name identity;
- author position and expertise constraints;
- voice and prose requirements;
- evidence and research discipline;
- storytelling expectations;
- rhythm / syntax preferences;
- irony, directness and emotional-temperature preferences;
- prose prohibitions and anti-junk extensions;
- approved benchmark excerpts or user-provided examples;
- provenance and human approval state.

Author-level authority is inherited by all books by that author unless an explicit, human-approved narrower override exists.

## 2. Series Profile

BOOK OS must understand a book series as a first-class editorial context, not merely a shared label.

A Series Profile must be able to store and enforce at least:

- series name and author;
- series purpose / reader promise / positioning;
- canonical or planned book list, order and statuses;
- thematic territory of each book;
- shared literary / editorial invariants;
- future-book reservations (material the current book must not consume);
- cross-book uniqueness requirements;
- exclusion corpus formed from earlier accepted Literary Masters;
- prohibited semantic overlap: theses, mechanisms, scenes, arguments, research functions, metaphors/analogies, practical tools and composition patterns;
- required pre-writing overlap map;
- chapter-level cross-book uniqueness gates;
- whole-book cross-series audit before Literary Master;
- change-control rules and provenance.

For **«Право на себя»**, the current hard requirement of semantic uniqueness and cumulative exclusion against all earlier accepted books must be preserved when the profile is imported into BOOK OS.

## 3. Target book length

The author must be able to set an approximate target length for the book.

The primary Russian publishing unit is **characters including spaces** (`characters_with_spaces`), with explicit display of the counting rule. BOOK OS may also show derived word counts, but must not silently convert a user-supplied character target into a word quota.

The book target must support:

- target characters;
- optional minimum / maximum range or tolerance;
- current actual character count;
- planned allocation by part/chapter after Architecture exists;
- variance against target at chapter and whole-book levels.

Length is a planning and audit constraint, **not permission to pad**. Density/quality rules remain superior: missing volume is created only by new substance (new argument, evidence, scene, distinction, counterargument, practical value or necessary development). Repetition or filler to hit a number is forbidden.

## 4. Style Profile and preview

BOOK OS must let the author choose and refine the intended manner of writing before long-form drafting.

A Style Profile must be explicit and inspectable rather than a vague label. It may contain dimensions such as:

- literary vs utilitarian register;
- degree of authorial presence;
- directness;
- sentence / paragraph rhythm;
- scene density;
- evidence density;
- analytical depth;
- irony / humor;
- emotional temperature;
- practical-instruction intensity;
- level of terminology;
- prohibited rhetorical patterns;
- approved benchmark excerpts.

The product must support:

1. reusable author-level style profiles;
2. optional series-level refinement;
3. optional book-level refinement;
4. user-created custom profiles;
5. human approval before the selected profile becomes operative for long-form generation.

Before choosing, the author must be able to generate **comparable preview samples**: the same bounded content brief is rendered in different candidate Style Profiles so the difference is visible in actual prose, not only in labels. The UI must show which profile produced each preview when the goal is style selection. A preview is disposable evidence and does not enter book authority or the manuscript automatically.

BOOK OS must not encode imitation of a named living writer as a built-in style preset. User-owned / user-supplied author examples may be analyzed into descriptive style attributes and benchmarked with provenance.

## 5. Annotation from the finished book

After a Literary Master exists (or after the user explicitly selects another eligible manuscript revision), BOOK OS must be able to generate publication annotations from the actual book.

The user must be able to specify a hard maximum character count, for example **no more than 1000 characters including spaces**.

Requirements:

- the source manuscript/revision is explicit;
- generated annotation must not invent claims, facts, outcomes or themes absent from the selected book;
- character count is calculated deterministically, including spaces;
- a candidate that exceeds the user limit fails validation and is not presented as compliant;
- UI shows actual count / limit;
- several candidate annotations may be generated and compared;
- the user may edit and approve a final variant;
- annotation is a downstream publishing artifact and never mutates Literary Master.

## 6. Platform taxonomy resolver: genres / subgenres / tags

BOOK OS must be able to recommend **real existing** genres, subgenres, categories and tags for a specified publishing platform.

The user may identify the platform by name and/or enter a platform/category URL. BOOK OS must inspect the current platform taxonomy or other authoritative platform pages rather than invent taxonomy values from model memory.

For every recommendation the system must preserve evidence:

- platform;
- source URL(s);
- retrieval/check date;
- exact taxonomy label as used by the platform;
- hierarchy when available (genre → subgenre/category);
- rationale tied to the finished book;
- confidence / ambiguity;
- rejected or unsuitable nearby categories when useful.

If the current taxonomy cannot be verified, BOOK OS must fail closed and say that verification is unavailable rather than fabricate genres or tags.

Platform taxonomy is time-varying. Saved recommendations must therefore keep their evidence snapshot/date and be refreshable before publication.

## 7. Publishing Package is downstream of Literary Master

Annotation and platform classification belong to a **Publishing Package**, derived from the accepted book. They do not become part of Literary Master and may vary by platform.

A Publishing Package may later be extended with other platform-specific metadata, but the first required slice is:

- annotation(s) with hard length constraints;
- verified genre/subgenre/category recommendations;
- verified platform tags/keywords where the platform exposes them;
- provenance and human selection/approval.

## 8. Pilot consequence

Do not treat the current first-book pilot flow as complete while it models only an isolated Business Nonfiction project.

Before the real pilot is accepted as representative, the product must provide a working path for:

1. selecting/creating an Author Profile;
2. standalone vs series membership and Series Profile inheritance;
3. target book length in characters including spaces;
4. Style Profile selection with generated comparable previews;
5. downstream annotation generation with a hard character limit;
6. verified platform taxonomy recommendations for the chosen publication platform.

These controls must be provenance-aware and human-approved where they affect book authority. AI may propose; it may not silently approve author, series, style, publishing classification or final annotation decisions.

## 9. Model routing

The 2026-09-06 Owner principle remains binding: **not “the best model”, but the best executor for the specific editorial operation**.

Style previews, annotation generation, taxonomy research/classification, series-overlap analysis and long-form writing are distinct operations and may be routed to different models/tools according to quality, risk, evidence needs and cost.

## 10. Initial provider scope and UI names

For the first working BOOK OS product contour, expose exactly **two AI providers** in the user interface:

- **AI Pro** = OpenAI;
- **AI Ya** = Yandex AI Studio / Yandex models.

Do not add Anthropic, Google, DeepSeek, Qwen or other provider switches to the initial user interface before the first real book workflow is validated. The internal Model Gateway must remain provider-neutral and extensible so additional providers can be added later without changing book authority semantics.

The provider switch is functional, not decorative. A provider that is not configured, has no valid credential, or has not passed its readiness/preflight gate must fail closed and must not silently fall back to the other provider.

Model identity and exact model selection may remain visible in advanced/diagnostic settings, while the primary author-facing control uses the stable product labels **AI Pro** and **AI Ya**.
