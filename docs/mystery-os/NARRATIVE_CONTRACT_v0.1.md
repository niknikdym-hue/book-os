# MYSTERY OS — NARRATIVE CONTRACT v0.1

**Status:** INCUBATION DRAFT  
**Date:** 2026-09-18

## 1. Purpose

Mystery fiction can be logically fair at the case level and still cheat the reader through narration.

MYSTERY OS therefore treats narrative design as explicit authority rather than an implicit Writer choice.

The `NarrativeContract` defines what the reader may know, when, through whose consciousness, with what degree of reliability, and what forms of withholding are legitimate.

## 2. Core rule

`case truth != character knowledge != narrator knowledge != reader knowledge != prose presentation`

A Writer may control presentation.

A Writer may not hide decisive information merely because revealing it would make the solution easier when the selected viewpoint would naturally and consciously contain that information.

## 3. NarrativeContract minimum fields

- `narrative_mode`;
- grammatical person;
- tense;
- viewpoint roster;
- POV allocation policy;
- psychic distance range;
- narrator reliability model;
- narrator/character knowledge boundary;
- allowed withholding mechanisms;
- prohibited withholding mechanisms;
- direct-thought policy;
- flashback/memory policy;
- dream/vision policy;
- document/message/media presentation policy;
- head-hopping prohibition/exception rules;
- scene-entry and scene-exit viewpoint rules;
- reader-fairness constraints;
- voice markers;
- audio/listenability constraints when applicable.

## 4. Supported narrative modes

MYSTERY OS should support at least:

- first-person single POV;
- first-person multiple POV;
- third-person limited single POV;
- third-person limited multiple POV;
- controlled omniscient;
- epistolary/documentary hybrid;
- mixed mode only with explicit rules.

A mode is not chosen because it is fashionable. It must improve mystery control, character intimacy or dramatic effect.

## 5. POV allocation

For multiple-POV books, the system must record:

- which characters may own scenes;
- what narrative function each POV serves;
- minimum/maximum switching frequency if needed;
- whether culprit POV is permitted;
- whether victim POV is permitted;
- whether antagonist scenes occur before reveal;
- what information each POV may expose;
- what information is forbidden from artificial suppression.

A new POV introduced late solely to deliver a clue or create suspense is a quality risk.

## 6. Fair withholding

Legitimate withholding may arise from:

- the POV character genuinely does not know;
- the character has not consciously formed a conclusion yet;
- attention is plausibly elsewhere;
- a memory is incomplete for established, credible reasons;
- a character chooses not to speak, while the narration still remains honest about their internal state;
- the narrator is explicitly unreliable under a contract the reader can fairly detect;
- information is naturally absent because the scene is outside that viewpoint.

## 7. Unfair withholding

BLOCKING or MAJOR depending on impact:

- the POV character clearly knows the culprit identity but narration avoids their thoughts solely to preserve the twist;
- internal monologue uses unnatural pronouns/euphemisms to conceal familiar identity (`тот человек`, `он`) when the character would think a name;
- a memory disappears until the exact chapter where plot requires it without established cause;
- the narrator describes every relevant thought except the one decisive fact;
- culprit POV lies directly to the reader in an otherwise reliable internal narration without contract support;
- a chapter ends immediately before a character would naturally complete a sentence, repeatedly, only to delay information;
- consciousness is selectively censored by author convenience.

Mystery difficulty cannot be purchased with narrative dishonesty.

## 8. Unreliable narrator protocol

Unreliability must itself obey rules.

Record:

- source of unreliability;
- what domains are unreliable;
- whether distortion is intentional, perceptual, mnemonic, ideological or interpretive;
- stable signals available to the reader;
- what remains objectively true;
- what evidence can contradict the narrator;
- final resolution level.

Unreliable narration is not permission for arbitrary contradiction.

A diagnosis introduced only at the end to explain unreliability is blocked by the anti-cliche policy unless explicitly reinvented and human-approved.

## 9. Culprit POV

Culprit POV is high risk.

If used, it must specify one of:

- identity is known to reader;
- identity is concealed but internal narration remains semantically honest;
- scenes occur before culprit consciously commits/understands the relevant act;
- narration uses a formally justified limited frame.

The system should run a `CULPRIT_POV_FAIRNESS` audit before approval.

## 10. Psychic distance

For each POV voice define allowed distance:

- external/observational;
- close limited;
- deep limited;
- variable with rules.

Abrupt unmotivated movement from deep interiority to camera-like withholding is a fairness risk.

Distance should change for dramatic reasons, not to hide clues.

## 11. Thought representation

The Style/Narrative contract should specify preferred methods:

- free indirect discourse;
- direct thought;
- narrated thought;
- minimal explicit thought.

Avoid machine-like over-explanation of emotion after effective action/dialogue.

Do not require every inference to be verbalized merely to prove fairness; reader-visible evidence may remain implicit if it was genuinely available.

## 12. Flashback and memory

Every material flashback/memory must have:

- trigger or structural reason;
- knowledge-status effect;
- relation to CaseTimeline;
- reader-new information;
- fairness status;
- consequence after return to present.

Blocked/high risk:

- flashback inserted only to reveal a fact needed by the next chapter;
- conveniently partial memory that becomes complete at climax without causal reason;
- repeated childhood trauma fragments used as generic mystery bait;
- memory presented as objective video when it is actually subjective.

## 13. Dreams and visions

Dream/vision material must declare:

- whether supernatural, psychological or ambiguous;
- reliability;
- what it can and cannot communicate;
- whether it counts as reader evidence;
- whether it may contain literal clues;
- how often it may occur without becoming a shortcut.

A dream/vision cannot solve the case by delivering otherwise unavailable decisive truth.

## 14. Documents, messages and recordings

When narrative uses texts, chats, transcripts, audio, CCTV summaries, emails or documents, define:

- authenticity status;
- completeness;
- who created it;
- who can access it;
- whether it can be manipulated;
- how the reader experiences it;
- audio adaptation rule.

A document is not automatically objective truth.

## 15. Head-hopping

Within limited POV, unmarked head-hopping is prohibited by default.

Exceptions require explicit formal design.

The system should detect:

- knowledge unavailable to current viewpoint;
- interior states of non-POV characters asserted as fact;
- sudden perspective jumps inside a scene;
- narrator omniscience appearing only when convenient.

## 16. Narrative information ledger

For each scene the system should be able to derive:

- current POV;
- facts POV knows entering;
- facts POV learns;
- false beliefs;
- hypotheses;
- secrets consciously held;
- facts reader receives;
- facts reader may infer;
- facts intentionally withheld and contractual reason;
- reveals caused by the scene.

This ledger connects `CharacterKnowledgeState`, `SceneContract`, `RevealPlan` and `ColdReaderRun`.

## 17. Reader knowledge state

MYSTERY OS should model not only what was technically printed but what an attentive reader could reasonably know.

A `ReaderKnowledgeState` may include:

- exposed clues;
- unresolved questions;
- viable hypotheses;
- known contradictions;
- established supernatural rules;
- deliberately ambiguous facts;
- information likely forgotten due to distance/repetition.

This enables better fair-play and reveal calibration.

## 18. Narrative fairness gate before Writing

A SceneContract cannot receive `WRITING_ALLOWED` when:

- viewpoint is undefined;
- required knowledge state is stale;
- planned withholding violates NarrativeContract;
- a reveal depends on head-hopping or hidden conscious knowledge;
- scene introduces an unapproved narrative device that changes reader access to truth.

## 19. Narrative fairness gate at midpoint

Audit:

- has POV distribution drifted;
- is one narrator being used only as a clue delivery system;
- is culprit/victim interiority unfairly censored;
- are flashbacks multiplying to repair architecture;
- is psychic distance changing conveniently around clues;
- does reader evidence match planned fair-play exposure;
- are multiple voices genuinely distinct.

## 20. Final Narrative Integrity audit

Before Literary Master verify:

- every scene has valid POV ownership;
- character knowledge never exceeds acquisition;
- narrator knowledge is contract-consistent;
- decisive facts are not unfairly suppressed;
- all intentional withholding has a valid mechanism;
- unreliable narration remains reconstructable;
- POV voices remain distinguishable;
- tense/person do not drift unintentionally;
- documentary inserts remain plausible and traceable;
- audio adaptation does not destroy required information hierarchy.

## 21. Narrative voice vs StyleProfile

`NarrativeContract` defines epistemic and structural rules.

`StyleProfile` defines expressive tendencies.

They are related but not interchangeable.

Example:
- NarrativeContract: third-person limited, Elena-only in Book 1, close distance, past tense.
- StyleProfile: restrained syntax, concrete perception, low metaphor density, dry humor, no therapeutic abstraction.

## 22. Series continuity

For recurring narrators, Series Bible should track:

- stable voice traits;
- information already learned;
- secrets already disclosed;
- relationship knowledge;
- shifts in worldview;
- whether later books may add POV characters;
- devices already consumed (e.g., one unreliable-narrator book).

Repeating the same narrative trick across volumes can become a Series Collision.

## 23. Model/agent use

Premium reasoning may be justified for:

- selecting narrative architecture;
- adversarial fairness review;
- culprit-POV analysis;
- unreliable-narrator design;
- whole-book information-flow diagnosis.

Routine scene realization should follow accepted authority and does not automatically require premium reasoning.

## 24. Principle

A mystery writer may misdirect the reader. The narrative itself must still play by rules.