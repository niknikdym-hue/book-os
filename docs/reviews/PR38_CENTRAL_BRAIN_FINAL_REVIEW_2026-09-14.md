# PR #38 — Central Brain final review status

Date: 2026-09-14
PR: #38 — Task 021: complete Auto Book cycle and Series Studio
Branch: `codex/auto-book-complete-cycle-20260913`

## Review boundary

This note records the final free/deterministic review boundary before Owner acceptance. It does not authorize merge, production deployment, notarization, installed-app replacement, paid model calls, TTS calls, or the bounded literary-quality trial.

## P1 closure status

The current branch contains code and regression coverage for the previously identified merge-blocking items:

- Auto routing clears stale book pins in Auto mode and uses bounded escalation; Extra High is not the default for routine/high-risk work.
- Durable change requests have an execution path and invalidate/rebuild affected downstream work instead of only storing text.
- Auto Book carries real table/visual assets with placement, provenance, alt text and audio equivalents into the structured master/export path.
- Pre-writing admission no longer fabricates quality PASS or personal Owner approvals; automatic execution is recorded as SYSTEM under a durable delegated authorization.
- Final human acceptance uses an exact candidate snapshot before Literary Master lock when human acceptance is required.
- Research/evidence gates cover material claims in the current manuscript, including quantitative, empirical/causal, historical, attribution, legal/regulatory, consensus and time-sensitive market/platform claims; source discovery alone is not evidence.
- Series Create/Auto Book binds to one exact owned Series Profile and does not silently fall back to standalone.
- Series anti-duplication includes deterministic semantic/structural checks for paraphrased theses, profession/domain-swapped architecture, reworded cases, renamed tools and profession-swapped templates.
- Series governance includes a new-book-vs-existing-chapter preflight, append-only Topic Ownership, explicit overlap disposition with Owner reason, whole-import duplicate scanning beyond the opening sample, workflow lifecycle synchronization, review-first external-series approval and physical packaging of selected READY derivatives.
- Bibliography remains nonfiction-default ON and is built only from actually used/current verified evidence; public omission preserves internal provenance/audit.
- Mandatory mid-book audit is threshold-crossing/idempotent and finalization fails closed if it is missing.
- Paid/provider operation paths use durable operation reservation/recovery and block blind retries on unknown outcomes.

## Known non-P1 limitations — do not overclaim

These are explicit technical limitations, not evidence of platform certification:

1. **Scanned PDF OCR.** A PDF whose text cannot be extracted remains `PARTIAL` with the warning that OCR is required. Series/source quality fails closed. BOOK OS must not claim that arbitrary scans are fully imported until a bounded OCR lane is implemented and tested.
2. **Rendered export / platform certification.** DOCX/PDF/EPUB checks are structural and reopen/reference checks. They are not pixel-level viewer certification. The LitRes profile must keep `platform_acceptance_claimed=false`; a local file/profile must not be described as proof that LitRes accepted the file.
3. **Audio ATTENTION acknowledgement UI.** The current desktop review surface may summarize a check with the first finding while the backend accepts a set of ATTENTION codes. Until the UI shows every individual finding/location (or requires per-finding acknowledgement), Owner acceptance must treat the aggregate checkbox as insufficient evidence that every hidden location was reviewed. This is a P2 UX/audit limitation and must not be represented as per-finding review.
4. **Literary quality.** Deterministic/mock tests prove orchestration and invariants, not publishable literary quality. The separate bounded paid quality trial remains an Owner Gate and is not authorized by this note.

## Safety / cost boundary

Implementation and deterministic CI must make 0 production/provider/model/TTS calls and 0 paid calls. No private manuscript, API key or credential may be committed. PR remains Draft and unmerged until the Owner explicitly authorizes the next gate.

## Exact-head evidence rule

Do not copy an older green run into the PR body after this commit. The only acceptable completion evidence is a workflow run whose checkout contains the exact current PR head (or GitHub's merge ref whose second parent is that exact head), with Local Core full pytest, Ruff format/check, mypy, Desktop lint/typecheck/tests/build/audit, Rust/Tauri checks, secret scan and macOS native launch all passing. Apple distribution signing may remain the sole documented external-credential failure if the required Apple secrets are still absent.
