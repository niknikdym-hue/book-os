# MYSTERY OS — FICTION RESEARCH & REALISM v0.1

**Status:** INCUBATION DRAFT  
**Date:** 2026-09-18

## 1. Purpose

Mystery fiction can be invented; real-world systems cannot be invented accidentally.

MYSTERY OS therefore separates:

- **fiction truth** — invented case, characters, events and supernatural causality;
- **real-world truth** — law, medicine, emergency response, policing, forensics, technology, geography, finance, institutions and other facts a reader may reasonably expect to be authentic;
- **intentional fictionalization** — a conscious departure from reality for story reasons, recorded as such;
- **unknown / unverified** — a fact that must not silently enter approved prose as if verified.

The goal is not documentary overload. The goal is to prevent implausible procedures, impossible timings and false factual confidence from lowering the novel below professional publishing standards.

## 2. Core rule

A fictional case may be extraordinary. The ordinary world around it must behave credibly unless the story explicitly establishes otherwise.

Research exists to improve drama, not to create exposition.

The Writer must receive only the facts needed for the scene. Research notes are not prose.

## 3. Research-risk classes

Every factual dependency used materially by plot is classified.

### R0 — invented / self-contained

No external verification required because the fact is wholly fictional and cannot reasonably be mistaken for a real-world claim.

### R1 — low-risk texture

Examples:
- ordinary weather behavior;
- common household objects;
- non-material local color;
- generic workplace detail.

Spot-check when uncertain.

### R2 — material realism

The fact materially affects credibility or scene mechanics.

Examples:
- travel time;
- building access;
- phone behavior;
- common police procedure;
- basic medical response;
- camera coverage;
- emergency dispatch flow.

Requires a reliable source or expert-consistent verification before final use.

### R3 — plot-critical factual dependency

If wrong, the CaseSolution, clue logic, timeline or reveal may break.

Examples:
- time-of-death inference;
- toxicology window;
- digital metadata;
- emergency-call recording/access;
- legal search/arrest boundaries;
- pathology/forensic limits;
- telecom/network behavior;
- financial trace mechanism.

Requires stronger evidence, preferably primary/official or multiple independent authoritative sources, and explicit linkage to the dependent authority object.

### R4 — safety/legal/reputationally sensitive

Examples:
- actionable criminal techniques;
- self-harm methods;
- dangerous chemical/medical detail;
- named real persons accused of wrongdoing;
- defamation-sensitive claims;
- highly specific operational vulnerabilities.

Must receive appropriate safety/legal handling. Story usefulness never overrides safety, rights or publication risk.

## 4. Research domains for contemporary mystery

The system must support, when relevant:

- police and investigative procedure;
- emergency dispatch / 112 / 911-type services;
- ambulance and hospital workflow;
- pathology and forensic medicine;
- forensic biology / DNA limitations;
- fingerprints and trace evidence;
- CCTV / access-control systems;
- mobile devices, messaging and cloud services;
- telecom and location data;
- cybersecurity/digital forensics at a reader-facing level;
- law, warrants, detention, interviews and evidence rules;
- geography, transport and travel time;
- building layouts and physical access;
- fire behavior and emergency response;
- finance, banking and payment traces;
- journalism and public-information access;
- social services / schools / workplaces where material;
- cultural and institutional context of the setting.

This list is not a prompt checklist. Research is driven by the actual story.

## 5. Source hierarchy

For plot-critical facts prefer, in order where appropriate:

1. current official/primary sources;
2. professional bodies, manuals and standards;
3. peer-reviewed or academically reputable material;
4. high-quality specialist secondary sources;
5. reputable journalism for practice/context;
6. expert interviews or consultations;
7. community/anecdotal material only as supplementary texture.

A search-result snippet is not evidence.

An LLM statement is not a source.

A single forum post cannot carry a plot-critical mechanism.

## 6. Fiction Research Ledger

Each material fact should be represented by a `FictionResearchItem` with at least:

- `research_id`;
- question;
- risk class;
- domain;
- jurisdiction/location/time period;
- current assumed answer;
- source references;
- source date / access date;
- confidence;
- limitations/uncertainty;
- whether intentionally fictionalized;
- exact story objects/scenes dependent on it;
- freshness horizon when applicable;
- disposition: `VERIFIED | QUALIFIED | FICTIONALIZED | RESEARCH_NEEDED | REJECTED`.

## 7. Dependency rule

Research must connect to story authority.

Examples:

`FictionResearchItem -> CaseSolution`

`FictionResearchItem -> CaseTimeline`

`FictionResearchItem -> Clue`

`FictionResearchItem -> Location`

`FictionResearchItem -> SceneContract`

`FictionResearchItem -> PublishingRiskFinding`

Changing a plot-critical research conclusion makes dependent objects stale.

## 8. Jurisdiction and time

Procedures vary by country, region, agency and year.

Every material procedural/legal claim should therefore record:

- jurisdiction;
- time period;
- whether the story uses a real agency/institution or a fictional analogue;
- whether practice is mandatory law, policy, common practice or merely possible.

Do not universalize one country's rules.

Do not use a historical practice as if it were current without explicit story dating.

## 9. Emergency-service realism

For any series whose branding or plot touches emergency response, especially `Линия 112`, research must precede canonization of the recurring engine.

Before StoryDefinition/Series Bible approval, verify as applicable:

- what service the number actually reaches in the chosen jurisdiction;
- operator roles and escalation paths;
- what call metadata may exist;
- recording/retention/access constraints;
- caller-location capabilities and limitations;
- language/accessibility handling;
- interaction with police/fire/ambulance;
- what an operator can and cannot independently investigate;
- what information would realistically be available later to protagonists;
- legal/privacy boundaries around recordings and records.

The series title must not force an implausible professional role.

## 10. Forensic realism rule

Forensics is probabilistic and limited.

MYSTERY OS should flag:

- instant laboratory results without story justification;
- perfect time-of-death precision;
- DNA/fingerprint evidence treated as magic certainty;
- impossible certainty from body language;
- digital traces presented as complete omniscience;
- medical findings that uniquely identify a culprit when they normally do not;
- one-test solves-all-case structures;
- technologies used beyond documented capability.

A forensic fact should narrow, support or challenge hypotheses. It should not replace investigation through authorial magic.

## 11. Digital realism rule

Contemporary mysteries frequently fail because phones and networks behave only when convenient.

The system must explicitly model when material:

- device possession and access;
- battery/power state;
- network availability;
- account/session state;
- timestamps/time zones;
- deletion vs recoverability;
- cloud/local distinction;
- location accuracy/uncertainty;
- metadata vs message content;
- legal/access pathway;
- possibility of spoofing/manipulation;
- retention and logging limits.

A convenient outage or missing camera segment is an anti-cliche risk and requires causal support.

## 12. Geographic and physical realism

When movement matters, the CaseTimeline should use researched or measured:

- travel time ranges;
- route constraints;
- opening hours;
- access restrictions;
- building layout;
- visibility/acoustics;
- weather effect where material.

Do not let a city function as decorative wallpaper while characters teleport through it.

## 13. Intentional fictionalization

Fictionalization is allowed when it improves story, protects privacy/rights or avoids false precision.

It must be explicit internally.

A `FictionalizationDecision` should record:

- real-world baseline;
- what is changed;
- why;
- whether the change could mislead a reasonable reader;
- whether an author's note is appropriate;
- which story objects depend on the change.

The system must never label an error “intentional fictionalization” after the fact merely to avoid correction.

## 14. Research-to-prose boundary

Research quality and prose quality are separate.

Writers receive:

- verified fact;
- uncertainty;
- scene relevance;
- prohibited overclaim;
- optional authentic detail.

Writers do **not** receive a mandate to explain the source material to the reader.

Research that does not affect action, perception, clue logic, setting or consequence should usually remain off-page.

## 15. Research freshness

Current technology, platforms, law and procedures can age quickly.

Every time-sensitive research item should include a freshness horizon or recheck trigger.

Examples of recheck triggers:

- manuscript revised after a long pause;
- publication year changes;
- jurisdiction changes;
- platform/technology feature is central to the case;
- legal procedure is decisive;
- series reuses a recurring institutional process in a later book.

## 16. Factual realism gate before Writing

`WRITING_ALLOWED` fails closed for a scene when:

- it depends on an unresolved R3/R4 fact;
- a known factual contradiction breaks the CaseSolution;
- a key procedural assumption has no jurisdiction/time context;
- a research result changed and dependent authority is stale.

R1/R2 uncertainty may be admitted only when explicitly bounded and incapable of invalidating the scene's case logic.

## 17. Factual realism gate before Literary Master

Release is blocked by:

- unresolved plot-critical factual error;
- impossible procedure required for the solution;
- materially misleading real-world claim presented as fact;
- stale research affecting the case;
- invented institution/practice insufficiently distinguished where reader harm/confusion is plausible;
- factual contradiction between manuscript and accepted research authority.

## 18. Model/agent use

Research tasks may be routed to strong models/Agents API for:

- decomposition of research questions;
- source discovery;
- contradiction finding;
- synthesis across authoritative sources;
- identifying hidden factual dependencies in a CaseSolution;
- adversarial realism review.

But model prose cannot itself satisfy evidence.

Expensive reasoning is justified for high-blast-radius research questions, not routine texture.

## 19. Human/expert review

For highly technical or high-risk mechanisms, the system should support an `EXPERT_REVIEW_RECOMMENDED` finding.

Expert review is especially valuable when:

- the solution depends on a narrow medical/forensic point;
- procedural realism is central to brand promise;
- the story portrays a specialized profession extensively;
- published error would be obvious to the target readership.

## 20. Principle

Professional fiction does not show research by displaying it. It shows research by making the world behave as if the author knows what they are talking about.