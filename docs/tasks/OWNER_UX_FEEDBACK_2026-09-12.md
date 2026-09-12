# BOOK OS — Consolidated Owner UX Feedback

Date: 2026-09-12
Status: OWNER FEEDBACK / INPUT FOR ONE CONSOLIDATED CODEX TASK
Repository: `niknikdym-hue/book-os`

## Purpose

This document captures the owner's live observations from testing the BOOK OS desktop app during the last hour. It must be used to prepare ONE consolidated Codex implementation task. Do not treat the items as unrelated cosmetic tweaks: the central problem is that the panel exposes too much internal machinery and does not clearly tell the author what has started, what is working, what has finished, where the result is, and what remains.

Preserve all BOOK OS authority, approval, evidence, BookBench, Literary Master, series-uniqueness, cost and safety gates. Simplify the interface without weakening the underlying controls or deleting audit/provenance data.

Important: the current working branch may contain partial/incomplete attempts from the live debugging pass. Codex must inspect the current diff against `main`, keep only correct changes, complete the UX coherently, and rely on tests/CI rather than assuming partial edits are finished.

---

## 1. Permanent book deletion is broken

Owner observation:
- `Перенести в библиотеку` works.
- `Удалить навсегда` does not work.
- App shows `unsupported local-core API method`.

Confirmed repository cause:
- React sends `DELETE` correctly.
- Local Core already exposes DELETE endpoints for active books and library books.
- Tauri `core_api` proxy rejects DELETE because it only allows GET / POST / PUT.

Required result:
- permanent delete works from active list and library;
- retain the existing two-step destructive confirmation;
- after successful deletion the book disappears immediately;
- if the deleted book was open, clear the active book view;
- delete only that book project, not global BOOK OS data;
- add native regression coverage for DELETE on bounded `/api/...` paths while unsupported methods remain rejected.

---

## 2. Simplify the entire book launch flow

Owner observation: `вообще там черт ногу сломит`.

Required direction:
- one primary obvious launch route;
- remove duplicate/secondary controls from the main path;
- manual workflows stay available but collapsed under a clear optional section;
- technical budget and provider details go under `Расширенные настройки`;
- the author should not need to understand internal architecture just to launch a book.

Primary sequence should read visually as:
1. Fill required book data.
2. System becomes ready.
3. Owner authorizes the run.
4. Main launch button turns green.
5. User launches.
6. User sees visible progress and elapsed time.
7. User sees clear completion/result.

---

## 3. Mark all truly required fields

Owner requirement:
- clearly mark the minimum fields without which the system will not start;
- user must not guess why launch is disabled.

Required behavior:
- required fields visibly marked with `*`;
- missing/invalid fields show short human-readable explanations;
- launch remains disabled until all real prerequisites are satisfied;
- minimum Auto Book book length is 4,000 characters; values such as 1,800 must visibly fail validation.

---

## 4. Main Auto Book launch button must turn green when ready

Owner requirement:
- when all launch conditions are met, the launch button must visibly change color to green;
- before that it stays inactive/non-green.

Meaning of green: `можно нажимать сейчас — система действительно готова к запуску`.

---

## 5. Auto Book must show real progress instead of looking frozen

Owner observation:
- a spinner / wheel looks as if everything has frozen;
- after launch, the user needs to see visible creation progress.

Required progress block:
- current percentage;
- current stage;
- current chapter when applicable;
- AI request count;
- no endless generic spinner as the main feedback.

Suggested stages:
- Основа книги
- Архитектура
- Главы
- Финальная проверка
- Готово

If a resumable transient disconnect occurs, show that progress is saved and present one clear recovery action: `Продолжить с сохранённого места`.

Do not blindly retry uncertain paid requests automatically.

---

## 6. Add elapsed work time inside the progress block

Owner explicitly requested the clock **where the progress is shown**.

Display example:
`Время работы 00:12:47`

Acceptance criteria:
- format HH:MM:SS;
- live updates once per second while the run is active;
- based on real Auto Book `started_at`, not component mount time;
- if app closes/reopens, time does not reset;
- after completion, final elapsed duration remains visible/frozen;
- use stable/tabular digits.

---

## 7. Local Core startup must not break Auto Book

Owner encountered:
- `Server disconnected without sending a response.`
- `Local Core returned HTTP 500 Internal Server Error: Local Core did not provide a diagnostic`
- `local core is still starting`

Required behavior:
- do not forward user actions until Local Core is actually ready;
- show `Local Core запускается…` while waiting;
- all desktop API calls should share one readiness gate rather than racing startup;
- transient provider/network disconnects should preserve resumable progress when safe;
- uncertain paid model requests must not be automatically repeated if that could duplicate cost.

---

## 8. Book Contract approval must become visibly completed

Owner requirement:
After pressing `Утвердить контракт книги`, the button should clearly show that the operation is done so the user does not press it repeatedly.

Required behavior after successful approval:
- button becomes green;
- text becomes `Утверждено ✓`;
- button is disabled / no longer clickable;
- state is derived from real authority status, not a temporary UI flag;
- state survives refresh/reopen.

---

## 9. One-shot paid Astra permission must visibly arm the Astra button

Current owner-facing text:
`Разрешаю один следующий платный вызов с лимитом $0.50.`

Owner requirement:
- once checkbox is selected, if every other prerequisite is satisfied, `Запустить Astra` must immediately become green;
- green means the one paid call is truly ready to launch;
- permission remains one-shot;
- after launch/completion/failure, authorization resets according to existing safety rules;
- checkbox alone must not make the button green if another prerequisite is missing.

---

## 10. Biggest Writer UX defect: model state/result is not obvious

Owner identified this as the **main panel deficiency**.

Current problem:
- after clicking launch, it is not obvious whether the model actually started;
- not obvious what it is doing;
- not obvious when it finished;
- not obvious where the result is;
- user has to search around the panel;
- small text such as `ИСТОРИЯ ГЛАВЫ · 1 запусков · Последний результат показан в центре` is insufficient and too easy to miss.

Required redesign:
Create one visually dominant central area: `Состояние работы модели`.

The same area must show the lifecycle:
1. `Готово к запуску`.
2. Immediately after click: `Astra запущена · модель работает…`.
3. Show the current user task/objective in human language.
4. On success: `Готово · запуск №N`.
5. Show the actual result directly below this status.
6. Show model used in human-readable form, e.g. `GPT-6 Astra High`.
7. On error, show the error and safe recovery action in this same central area.

A user looking at one place must instantly answer:
- модель запустилась или нет;
- она ещё работает или закончила;
- что именно она сделала;
- где результат;
- какой это запуск.

`История главы` can remain secondary or be simplified, but it must not be the primary run-state indicator.

---

## 11. Remove technical provenance drawer from normal Writer UI

Owner explicitly requested removal of:
`Настройки / Advanced · технические данные запуска`

and the explanatory text:
`Эти данные нужны для аудита воспроизводимости и не являются частью обычной авторской панели.`

Requirement:
- remove this drawer from normal author-facing UI;
- DO NOT delete provenance/audit data from backend/system;
- keep it internally for reproducibility/debugging.

---

## 12. Research / fact-checking block needs built-in help

Owner says this block is not self-explanatory enough:
- `Проверка фактов и источников`;
- `Исследование и доказательства`;
- `Источник ≠ доказательство ≠ утверждение`;
- exact manuscript revision;
- claim type;
- evidence linking.

Add a visible collapsible help control near the top: `Как пользоваться`.

Help must explain the workflow in plain Russian:
1. Select ONE verifiable statement from the manuscript — a fact, number, attribution, causal claim, historical/legal statement, etc.; not an entire paragraph.
2. Add the claim and choose its type; explain briefly why type matters.
3. Find a source. Explain that a search result/source alone is not evidence.
4. Inspect the source and attach evidence with exact page/section/paragraph/URL pointer.
5. Mark whether evidence supports, partially supports, contradicts, or only provides context.
6. If manuscript text changes, explain that evidence attached to the old exact revision may become stale and should be checked/rebound.

Include one short practical example of `Источник ≠ доказательство ≠ утверждение`.

Raw revision IDs must not dominate the normal view; keep them secondary/advanced.

---

## 13. Editorial review block is not understandable for an author

Owner specifically marked this block as confusing.

Current UI exposes too much internal language:
- `M6 · РЕШЕНИЯ ЧЕЛОВЕКА`;
- `Замечание не равно правке. Предложение не равно authority...`;
- editor roles;
- statuses `OPEN / RESOLVED / WAIVED / SUPERSEDED / ALL`;
- severities `CRITICAL / MAJOR / MINOR / INFO`;
- `Run Фактчекер`;
- internal revision IDs/hashes;
- English decision buttons `Accept / Reject / Request revision / Waive`.

Required primary view:
Top actions only:
- `Проверить текущую главу`;
- `Проверить всю книгу`;
- `Проверить факты`.

While running:
- show a clear `Проверяю…` state on/near the action.

After completion:
- show a summary such as `Проверка завершена · найдено 4 замечания`.

For each finding, answer in plain Russian:
- Что найдено?
- Насколько это важно?
- Почему это проблема?
- Что изменится, если исправить?
- Какие риски у правки?
- Есть ли предложенный вариант текста?

Decision buttons must be Russian and action-oriented:
- `Принять правку`;
- `Отклонить`;
- `Попросить доработать`;
- `Оставить как есть`.

If a reason is required for audit, label it plainly:
`Почему вы приняли это решение?`

Filters:
- do not show empty filters before there are findings;
- put filters under a collapsed `Фильтры` drawer;
- only show filters when there is something useful to filter;
- all visible statuses/severities must be Russian.

Internal target IDs, revision IDs, hashes, raw status names and the word `authority` must not dominate normal UI.

---

## 14. `Что блокирует выпуск` is useful, but raw codes are not

Owner asked whether the block is needed.

Decision:
- concept is useful and should remain;
- raw blocker codes and internal IDs are not appropriate for normal author UI.

Do not show raw main-list items such as:
- `MANUSCRIPT_UNIT_NOT_APPROVED`;
- `CHAPTER_MANUSCRIPT_EMPTY`;
- `CHAPTER_CONTRACT_MISSING`;
- `BOOKBENCH_SNAPSHOT_MISSING`.

Rename user-facing section:
`Что осталось до готовой книги`

Human-readable examples:
- `Есть текст, который ещё не утверждён.`
- `Глава 2 — текст ещё не создан.`
- `Глава 3 — контракт главы ещё не создан / не утверждён.`
- `Финальная проверка BookBench ещё не выполнена.`

Where practical add direct action/navigation hints, e.g.:
- `Открыть главу 3`;
- `Перейти к BookBench`.

When all blockers are gone, make the positive `Книга готова` state equally obvious.

---

## 15. Book Memory is needed by BOOK OS, but current UI is too technical

Owner asked whether this block is needed:
- `M5 · ПРОИЗВОДНАЯ ПАМЯТЬ`;
- `Book Memory`;
- `EMPTY`;
- document/vector counts;
- lexical / semantic / hybrid modes;
- current/history scope;
- object kinds;
- embedding model;
- lexical sync / semantic rebuild;
- index configuration.

Decision:
- Book Memory is important internally;
- it should support finding earlier content, detecting repetitions, recovering contracts/claims and whole-book consistency;
- the author should not manually manage indexes, vectors, embeddings, or index configuration during normal work.

Required UX direction:
- make memory maintenance automatic where possible;
- move manual index sync/rebuild, embedding model selection, vector counts, hashes and lexical/semantic diagnostics to `Advanced` / diagnostics;
- in normal author UI keep at most a simple `Найти в книге` search;
- choose best available search mode automatically by default;
- optional filters should use plain language and stay secondary;
- hide internal object/revision/hash/rank/score detail from the default result card.

---

## 16. Global UX rule for BOOK OS

Every important user action must have an obvious state transition in the same visual location:

`готово к действию → выполняется → завершено / ошибка → следующий шаг`.

Do not make the user infer success from a distant badge, hidden history block, internal status code, or another part of the screen.

The normal author-facing panel should speak the language of creating/editing a book. Internal platform vocabulary (`M5`, `M6`, authority, revision hashes, vector counts, raw enums, technical run IDs) belongs in diagnostics/advanced/internal state unless it is truly necessary for an author decision.

---

## 17. Recommended Codex model / quota strategy

This task does **not** require GPT-6 Astra or an Extra High reasoning tier for the main implementation pass.

Recommended default:
- **Model: GPT-5.3-Codex**
- **Reasoning effort: Medium**

Why:
- task is predominantly repo-local React/Tauri UX work plus one bounded proxy bug;
- architecture and product intent are already specified in this document;
- most work is implementation, refactoring, UI state handling and regression tests rather than open-ended system design;
- GPT-5.3-Codex is the dedicated agentic coding model and supports configurable reasoning effort.

Escalation rule:
- stay on **GPT-5.3-Codex Medium** for implementation, tests and ordinary CI fixes;
- escalate only a genuinely difficult blocking issue to **GPT-5.3-Codex High**;
- do **not** use GPT-6 Astra / Extra High for routine implementation, formatting, UI copy, CSS, test repair or installation;
- for the final local Desktop replacement, no expensive reasoning model is needed at all — Codex should only install the already-built artifact.

Goal: preserve expensive quota for genuinely hard architectural/debugging problems, not routine UI implementation.

---

## 18. Implementation discipline for Codex

Codex must:
- start from actual current `main` and inspect any partial branch changes before using them;
- implement the owner UX as one coherent workflow, not as scattered CSS-only patches;
- keep safety/authority/evidence rules intact;
- add/repair regression tests for changed behavior;
- run exact-head CI;
- produce a self-contained macOS owner-test artifact;
- do not use paid model calls to test UI unless explicitly authorized;
- do not merge/deploy/install until the owner/central brain instructs it.
