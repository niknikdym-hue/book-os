# MYSTERY OS — NEW CHAT / INTERRUPTION HANDOFF — 2026-09-18

## Authority / source of truth

Repository: `niknikdym-hue/book-os`.

Do not merge anything without Owner permission.

MYSTERY OS goal: build a reusable editorial machine for professional publisher-level mystery fiction, later integrable into the wider BOOK OS publishing system. Quality target is world-class commercial fiction, not “good self-publishing”.

Key fixed principles:
- deterministic/local checks first;
- premium Astra/frontier/Agents API only for high-blast-radius editorial decisions where quality gain justifies cost;
- standard Writer for most scene drafting only after authority/gates pass;
- Agents API/Codex `EDITORIAL_PREP` must remain optional, explicitly launched, bounded-cost, proposal-only, no self-approval;
- hard anti-cliche / anti-template policy: cheap twists, stale mystic tropes, generic AI prose, repetitive series mechanisms are blocked/default-high-risk;
- no real `Линия 112` manuscript drafting until the editorial machine and pilot gates are ready.

## Foundation

Draft PR #41 — Task 022 MYSTERY OS foundation/design.
Branch: `brain/task-022-mystery-os-foundation-20260917`.

Contains genre canon, anti-cliche policy, NarrativeContract, Fiction Research & Realism, Professional Fiction Benchmark, quality routing, Agents API editorial-prep design, machine gate map and contracts.

No merge yet.

## MYS-01 — technically GREEN

Draft PR #42.
Branch: `codex/mys-01-fiction-authority-20260918`.
Exact GREEN head: `f980845f7d8d982022b8b934bb2ee7bc16900365`.

Implemented:
- immutable fiction authority revisions;
- strict supersedes lineage;
- HUMAN provenance for APPROVED/LOCKED;
- separate working/latest vs effective/accepted authority;
- exact-revision dependencies;
- transitive staleness;
- dependency immutability/cycle rejection;
- fail-closed WRITING_ALLOWED admission.

CI run #1680 / 35278929182:
PASS — Ruff format, Ruff check, strict mypy, full pytest, Desktop, Tauri smoke, native macOS launch, secret scan.
Only workflow failure: `macos-signing-preflight` because Apple distribution credentials are absent. This is an external distribution gate, not an MYS-01 defect.

Do not modify MYS-01 unless a concrete regression is found.

## MYS-02 — local-core GREEN; full infrastructure CI finishing

Draft PR #43.
Branch: `codex/mys-02-case-integrity-20260918`.

Purpose: deterministic case/timeline/knowledge/clue integrity.

Implemented:
- machine case clock;
- actor double-location / impossible travel;
- explicit TravelRule input, no guessed travel facts;
- character knowledge acquisition/use ordering;
- clue origin/exposure/payoff;
- reader exposure/payoff order separated from physical case chronology;
- temporal-rule refs for explicit supernatural exceptions;
- fair-play checks for decisive clues;
- clue dependency existence/cycles.

Important design correction already made:
case chronology != reader disclosure order, so flashbacks/nonlinear presentation do not create false timeline failures.

The handoff Ruff blocker was fixed on 2026-09-18.
Exact head: `8b2dc41d925eac8a9afb098c1115c03606f0be53`.
CI run #1682 / 35321868995 has PASS for Ruff format/check, strict mypy, full local-core pytest, Desktop and secret scan. At handoff refresh, Tauri/native macOS infrastructure jobs were still completing; macOS signing preflight remains the known external Apple-credentials gate.

NEXT STEP #1:
confirm the remaining infrastructure jobs for run #1682, then mark MYS-02 technically GREEN if no project defect appears.

## MYS-03 — code/tests created, PR NOT opened yet

Branch: `codex/mys-03-narrative-fairness-20260918`.
Branch is being rebuilt cleanly from MYS-02 exact head `8b2dc41d925eac8a9afb098c1115c03606f0be53`.

This branch is cleanly stacked on the formatted MYS-02 head; it does not carry the obsolete parallel formatting history.

Created:
- deterministic NarrativeContract / ReaderKnowledge / narrative-fairness validator;
- tests.

Core rule:
`case truth != character knowledge != narrator knowledge != reader knowledge != prose presentation`.

Validator is intentionally not a prose-quality judge. It checks planned information architecture:
- allowed POV ownership;
- grammatical person / tense contract;
- head-hopping / foreign interior access;
- reader facts unsupported by POV/observation;
- active material facts unfairly withheld;
- protected facts that may not be withheld at all;
- explicit allowed withholding mechanisms;
- unreliable narrator contract requirements/signals;
- unapproved narrative devices.

Important anti-overconstraint rule:
a POV character is NOT required to verbalize every fact they know. Fairness checks apply to material/consciously active facts and contractual withholding, otherwise the system would turn fiction into exposition.

NEXT STEP #2:
complete MYS-03 self-review/formatting, open a Draft stacked PR over MYS-02, and run CI. Central Brain review added explicit mode/person consistency, bounded unreliable-narrator source/domain/signal rules, and a dedicated culprit-POV fairness gate.

## Roadmap after MYS-03

From Task 022:
MYS-04 FictionResearchLedger / realism dependencies / research staleness.
MYS-05 EditorialMachineGateState + SceneContract + WRITING_ALLOWED.
MYS-06 representative sample / StyleProfile / Writer qualification.
MYS-07 MysteryBench + ColdReader/adversarial.
MYS-08 Professional Fiction Benchmark.
MYS-09 Series Brain / Book Passport / collision checks.
MYS-10 anti-cliche registry/scanners/exceptions.
MYS-11 quality routing/model-operation hooks.
MYS-12 author UX.
MYS-13 Agents API EDITORIAL_PREP runner/import path.
MYS-14 synthetic full-cycle fixture.
MYS-15 real `Линия 112` pilot under separate paid/private Owner gate.

## Resume instruction

On resume:
1. restore GitHub exact state;
2. do NOT start with `Линия 112` prose;
3. finish MYS-02 formatting + CI first;
4. then MYS-03 Draft PR/CI;
5. preserve stacked, bounded implementation slices;
6. no merge/release/paid editorial calls without Owner approval.
