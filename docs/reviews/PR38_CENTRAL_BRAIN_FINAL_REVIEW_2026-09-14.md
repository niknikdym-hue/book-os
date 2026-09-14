# PR #38 — Central Brain final review status

Date: 2026-09-14
PR: #38 — Task 021: complete Auto Book cycle and Series Studio
Branch: `codex/auto-book-complete-cycle-20260913`

## Review boundary

This note records the final free/deterministic review boundary before Owner acceptance. It does not authorize merge, production deployment, notarization, installed-app replacement/update, paid model calls, TTS calls, or the bounded literary-quality trial.

## Closure status

The current branch contains code and regression coverage for the complete 2026-09-13/14 implementation package:

- Auto routing clears stale book pins in Auto mode and uses bounded escalation; Extra High is not the default for routine/high-risk work.
- Durable change requests have an execution path and invalidate/rebuild affected downstream work instead of only storing text.
- Auto Book carries real table/visual assets with placement, provenance, alt text and audio equivalents into the structured master/export path.
- Pre-writing admission no longer fabricates quality PASS or personal Owner approvals; automatic execution is recorded as SYSTEM under a durable delegated authorization.
- Final human acceptance uses an exact candidate snapshot before Literary Master lock when human acceptance is required.
- Research/evidence gates cover material claims in the current manuscript, including quantitative, empirical/causal, historical, attribution, legal/regulatory, consensus and time-sensitive market/platform claims; source discovery alone is not evidence.
- Short 1–3 sentence ideas can be developed into a reviewed concept before Book Definition; audience remains optional.
- Series Create/Auto Book binds to one exact owned Series Profile and does not silently fall back to standalone.
- Series anti-duplication includes deterministic semantic/structural checks for paraphrased theses, profession/domain-swapped architecture, reworded cases, renamed tools and profession-swapped templates.
- The linked «Как продать онлайн-курсы» deterministic fixture now has a genuinely course-specific unit-economics mechanism instead of weakening the Series Duplication Gate to accept generic overlap.
- Series governance includes a new-book-vs-existing-chapter preflight, append-only Topic Ownership, explicit overlap disposition with Owner reason, whole-import duplicate scanning beyond the opening sample, workflow lifecycle synchronization, review-first external-series approval and physical packaging of selected READY derivatives.
- Series Map freshness follows material semantic comparison inputs and does not become stale merely because a book advances through WRITING / EDITING / FINAL_REVIEW.
- New-series planning provides 3–5 alternative concepts; external and existing BOOK OS series remain separate paths with explicit rights and immutable input.
- Bibliography remains nonfiction-default ON and is built only from actually used/current verified evidence; public omission preserves internal provenance/audit.
- Mandatory mid-book audit is threshold-crossing/idempotent and finalization fails closed if it is missing.
- Paid/provider operation paths use durable operation reservation/recovery and block blind retries on unknown outcomes.
- AudioScript remains exact-source/versioned and HUMAN-approved; existing/Auto Book approval now fails closed unless every exact ATTENTION finding is individually dispositioned by its code + location + detail. The Desktop presents each current ATTENTION separately before approval, and already-approved exact scripts remain retryable after transient export failure without re-approving the same findings.
- Audiobook Studio handoff remains immutable/idempotent for the same approved AudioScript snapshot.
- Author Experience v2 keeps the author workflow primary (`Главная / Серии / Книги / Библиотека / Настройки`, unified Create and seven book stages) while technical routing/provenance/cost controls remain progressively disclosed.
- Book/series cost views distinguish confirmed, reserved, unknown and forecast cost.

## Known bounded limitations — do not overclaim

These are explicit technical/product boundaries, not incomplete last-24h assignments:

1. **Scanned PDF OCR.** A PDF whose text cannot be extracted remains `PARTIAL` with the warning that OCR is required. Series/source quality fails closed. BOOK OS does not claim arbitrary scans are fully imported.
2. **Rendered export / platform certification.** DOCX/PDF/EPUB checks are structural and reopen/reference checks. They are not pixel-level viewer certification. The LitRes profile keeps `platform_acceptance_claimed=false`; a local file/profile is not proof that LitRes accepted the file.
3. **Literary quality.** Deterministic/mock tests prove orchestration, invariants and fail-closed behavior, not publishable literary quality. Any real paid quality comparison remains a separate Owner Gate and is not authorized by this note.

## Safety / cost boundary

Implementation and deterministic CI must make 0 production/provider/model/TTS calls and 0 paid calls. No private manuscript, API key or credential may be committed. PR remains Draft and unmerged until the Owner explicitly authorizes another gate.

## Exact-head evidence rule

The only acceptable technical completion evidence is a workflow run whose checkout contains the exact final PR head (or GitHub's merge ref whose second parent is that exact head), with Local Core full pytest, Ruff format/check, mypy, Desktop lint/typecheck/tests/build/audit, Rust/Tauri checks, secret scan and macOS native launch all passing. Apple distribution signing may remain the sole documented external-credential failure if the required Apple secrets are still absent.

After that exact-head verification, the Owner's instruction is to **STOP before any change/update/replacement of the Desktop application**. No application installation or replacement is authorized by technical completion alone.
