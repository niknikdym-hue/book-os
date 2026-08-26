from __future__ import annotations

from pathlib import Path
import json
import re
from typing import Any, cast

from sqlalchemy import text
from sqlalchemy.engine import Engine

from .authority import AuthorityService, new_ulid
from .authority_types import utc_now
from .db import create_database
from .editorial import EditorialRunResult, EditorialService, FindingCreateRequest, FindingView

_WORD = re.compile(r"[\w-]+", flags=re.UNICODE)


def _normalize(value: str) -> str:
    return " ".join(_WORD.findall(value.casefold()))


def _tokens(value: str) -> set[str]:
    return set(_WORD.findall(value.casefold()))


def _lexically_present(requirement: str, chapter_text: str) -> bool:
    normalized_requirement = _normalize(requirement)
    normalized_chapter = _normalize(chapter_text)
    if not normalized_requirement:
        return True
    if normalized_requirement in normalized_chapter:
        return True
    required_tokens = _tokens(requirement)
    if len(required_tokens) < 3:
        return required_tokens <= _tokens(chapter_text)
    overlap = len(required_tokens & _tokens(chapter_text)) / len(required_tokens)
    return overlap >= 0.9


def _similarity(left: str, right: str) -> float:
    left_normalized = _normalize(left)
    right_normalized = _normalize(right)
    if not left_normalized or not right_normalized:
        return 0.0
    if left_normalized == right_normalized:
        return 1.0
    left_tokens = _tokens(left)
    right_tokens = _tokens(right)
    if len(left_tokens) < 8 or len(right_tokens) < 8:
        return 0.0
    union = left_tokens | right_tokens
    if not union:
        return 0.0
    return len(left_tokens & right_tokens) / len(union)


class EditorialDiagnostics:
    RUNNER_VERSION = "1.0.0"

    def __init__(self, data_dir: Path, service: EditorialService | None = None):
        self.data_dir = data_dir
        self.service = service or EditorialService(data_dir)
        self.projects_dir = data_dir / "projects"

    def _engine(self, book_id: str) -> Engine:
        path = self.projects_dir / book_id / "project.sqlite"
        if not path.is_file():
            raise FileNotFoundError(f"book project not found: {book_id}")
        return create_database(path)

    @staticmethod
    def _start_run(
        engine: Engine,
        *,
        book_id: str,
        role: str,
        runner_id: str,
        scope_kind: str,
        chapter_id: str | None,
        unit_id: str | None,
        snapshot: dict[str, Any],
    ) -> str:
        run_id = new_ulid()
        now = utc_now()
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO editorial_runs(run_id,book_id,role,runner_id,runner_version,"
                    "scope_kind,chapter_id,unit_id,input_snapshot_json,status,created_at) VALUES "
                    "(:run_id,:book_id,:role,:runner_id,:runner_version,:scope_kind,:chapter_id,"
                    ":unit_id,:snapshot,'RUNNING',:created_at)"
                ),
                {
                    "run_id": run_id,
                    "book_id": book_id,
                    "role": role,
                    "runner_id": runner_id,
                    "runner_version": EditorialDiagnostics.RUNNER_VERSION,
                    "scope_kind": scope_kind,
                    "chapter_id": chapter_id,
                    "unit_id": unit_id,
                    "snapshot": json.dumps(
                        snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":")
                    ),
                    "created_at": now,
                },
            )
        return run_id

    @staticmethod
    def _finish_run(engine: Engine, run_id: str, error: Exception | None = None) -> None:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE editorial_runs SET status=:status,error_message=:error_message,"
                    "completed_at=:completed_at WHERE run_id=:run_id"
                ),
                {
                    "status": "FAILED" if error else "SUCCEEDED",
                    "error_message": str(error)[:1000] if error else None,
                    "completed_at": utc_now(),
                    "run_id": run_id,
                },
            )

    @staticmethod
    def _current_units(engine: Engine, book_id: str, chapter_id: str | None = None) -> list[dict[str, Any]]:
        where = "mu.book_id=:book_id"
        params: dict[str, object] = {"book_id": book_id}
        if chapter_id:
            where += " AND mu.chapter_id=:chapter_id"
            params["chapter_id"] = chapter_id
        with engine.connect() as connection:
            rows = list(
                connection.execute(
                    text(
                        "SELECT mu.unit_id,mu.chapter_id,mu.authority_entity_id,ah.revision_id,"
                        "ah.revision_hash,r.content_json FROM manuscript_units mu "
                        "JOIN authority_heads ah ON ah.entity_id=mu.authority_entity_id "
                        "JOIN revisions r ON r.revision_id=ah.revision_id WHERE "
                        + where
                        + " ORDER BY mu.chapter_id,mu.ordinal,mu.unit_id"
                    ),
                    params,
                ).mappings()
            )
        units: list[dict[str, Any]] = []
        for row in rows:
            payload = json.loads(cast(str, row["content_json"]))
            units.append(
                {
                    "unit_id": cast(str, row["unit_id"]),
                    "chapter_id": cast(str, row["chapter_id"]),
                    "entity_id": cast(str, row["authority_entity_id"]),
                    "revision_id": cast(str, row["revision_id"]),
                    "revision_hash": cast(str, row["revision_hash"]),
                    "text": str(payload.get("text", "")),
                }
            )
        return units

    def run_developmental(self, book_id: str, chapter_id: str) -> EditorialRunResult:
        engine = self._engine(book_id)
        authority = AuthorityService(engine)
        run_id: str | None = None
        try:
            with engine.connect() as connection:
                row = (
                    connection.execute(
                        text(
                            "SELECT chapter_contract_entity_id FROM chapters WHERE book_id=:book_id "
                            "AND chapter_id=:chapter_id AND workflow_state!='SUPERSEDED'"
                        ),
                        {"book_id": book_id, "chapter_id": chapter_id},
                    )
                    .mappings()
                    .one_or_none()
                )
            if row is None or row["chapter_contract_entity_id"] is None:
                raise ValueError("approved/current Chapter Contract is required for developmental audit")
            entity_id = cast(str, row["chapter_contract_entity_id"])
            head = authority.get_head(entity_id)
            revision = authority.get_revision(head.revision_id)
            contract = cast(dict[str, Any], revision["content"])
            units = self._current_units(engine, book_id, chapter_id)
            snapshot = {
                "chapter_contract": {
                    "entity_id": entity_id,
                    "revision_id": head.revision_id,
                    "revision_hash": head.revision_hash,
                },
                "manuscript_units": [
                    {
                        "unit_id": unit["unit_id"],
                        "revision_id": unit["revision_id"],
                        "revision_hash": unit["revision_hash"],
                    }
                    for unit in units
                ],
            }
            run_id = self._start_run(
                engine,
                book_id=book_id,
                role="DEVELOPMENTAL_EDITOR",
                runner_id="chapter-contract-coverage",
                scope_kind="CHAPTER",
                chapter_id=chapter_id,
                unit_id=None,
                snapshot=snapshot,
            )
            findings: list[FindingView] = []
            if not units:
                findings.append(
                    self.service.create_finding(
                        book_id,
                        FindingCreateRequest(
                            role="DEVELOPMENTAL_EDITOR",
                            category="NO_CURRENT_MANUSCRIPT",
                            target_kind="CHAPTER_CONTRACT",
                            target_id=chapter_id,
                            base_revision_id=head.revision_id,
                            base_revision_hash=head.revision_hash,
                            diagnosis="Approved Chapter Contract has no current ManuscriptUnit.",
                            why="The chapter cannot yet satisfy its approved function without manuscript content.",
                            evidence={"rule": "current_manuscript_unit_count == 0"},
                            severity="MAJOR",
                            confidence=1.0,
                            expected_effect="Add bounded manuscript content before deeper editorial review.",
                            risks="This is a structural presence check, not a semantic quality judgment.",
                            actor="system:developmental-audit",
                            actor_kind="SYSTEM",
                            run_id=run_id,
                        ),
                    )
                )
            chapter_text = "\n".join(cast(str, unit["text"]) for unit in units)
            required_claims = contract.get("required_claims", [])
            if isinstance(required_claims, list) and units:
                for required_claim in required_claims:
                    if not isinstance(required_claim, str) or _lexically_present(
                        required_claim, chapter_text
                    ):
                        continue
                    findings.append(
                        self.service.create_finding(
                            book_id,
                            FindingCreateRequest(
                                role="DEVELOPMENTAL_EDITOR",
                                category="REQUIRED_CLAIM_LEXICAL_GAP",
                                target_kind="CHAPTER_CONTRACT",
                                target_id=chapter_id,
                                base_revision_id=head.revision_id,
                                base_revision_hash=head.revision_hash,
                                diagnosis=(
                                    "A Chapter Contract required claim has no conservative lexical "
                                    "trace in the current chapter manuscript."
                                ),
                                why=(
                                    "This is a deterministic coverage signal that should be reviewed "
                                    "before declaring the chapter contract fulfilled."
                                ),
                                evidence={
                                    "required_claim": required_claim,
                                    "rule": "normalized exact/90%-token lexical coverage",
                                    "manuscript_unit_ids": [unit["unit_id"] for unit in units],
                                },
                                severity="MAJOR",
                                confidence=0.8,
                                expected_effect="Review whether the required claim is genuinely covered or needs revision.",
                                risks="Lexical absence does not prove semantic absence.",
                                actor="system:developmental-audit",
                                actor_kind="SYSTEM",
                                run_id=run_id,
                            ),
                        )
                    )
            self._finish_run(engine, run_id)
            return EditorialRunResult(
                run_id=run_id, role="DEVELOPMENTAL_EDITOR", findings=findings
            )
        except Exception as exc:
            if run_id is not None:
                self._finish_run(engine, run_id, exc)
            raise
        finally:
            engine.dispose()

    def run_cross_book(self, book_id: str) -> EditorialRunResult:
        engine = self._engine(book_id)
        run_id: str | None = None
        try:
            units = self._current_units(engine, book_id)
            snapshot = {
                "manuscript_units": [
                    {
                        "unit_id": unit["unit_id"],
                        "revision_id": unit["revision_id"],
                        "revision_hash": unit["revision_hash"],
                    }
                    for unit in units
                ]
            }
            run_id = self._start_run(
                engine,
                book_id=book_id,
                role="CROSS_BOOK_AUDITOR",
                runner_id="current-unit-repetition",
                scope_kind="BOOK",
                chapter_id=None,
                unit_id=None,
                snapshot=snapshot,
            )
            findings: list[FindingView] = []
            for left_index, left in enumerate(units):
                for right in units[left_index + 1 :]:
                    similarity = _similarity(cast(str, left["text"]), cast(str, right["text"]))
                    if similarity < 0.9:
                        continue
                    findings.append(
                        self.service.create_finding(
                            book_id,
                            FindingCreateRequest(
                                role="CROSS_BOOK_AUDITOR",
                                category="NEAR_DUPLICATE_CURRENT_UNITS",
                                target_kind="MANUSCRIPT_UNIT",
                                target_id=cast(str, left["unit_id"]),
                                base_revision_id=cast(str, left["revision_id"]),
                                base_revision_hash=cast(str, left["revision_hash"]),
                                diagnosis="Two current manuscript units are lexically near-duplicate.",
                                why="Repeated passages can waste reader attention or signal accidental duplication.",
                                evidence={
                                    "similarity": similarity,
                                    "other_unit_id": right["unit_id"],
                                    "other_revision_id": right["revision_id"],
                                    "other_revision_hash": right["revision_hash"],
                                    "rule": "normalized token Jaccard >= 0.90",
                                },
                                severity="MAJOR",
                                confidence=min(1.0, similarity),
                                expected_effect="Human review can keep intentional repetition or propose a bounded edit.",
                                risks="High lexical overlap may still be intentional rhetoric.",
                                actor="system:cross-book-audit",
                                actor_kind="SYSTEM",
                                run_id=run_id,
                            ),
                        )
                    )
            self._finish_run(engine, run_id)
            return EditorialRunResult(
                run_id=run_id, role="CROSS_BOOK_AUDITOR", findings=findings
            )
        except Exception as exc:
            if run_id is not None:
                self._finish_run(engine, run_id, exc)
            raise
        finally:
            engine.dispose()

    def run_fact_checker(self, book_id: str) -> EditorialRunResult:
        engine = self._engine(book_id)
        run_id: str | None = None
        try:
            with engine.connect() as connection:
                claims = list(
                    connection.execute(
                        text(
                            "SELECT claim_id,chapter_id,unit_id,manuscript_revision_id,"
                            "manuscript_revision_hash,normalized_text,materiality,verification_state "
                            "FROM claims WHERE book_id=:book_id AND materiality IN ('HIGH','CRITICAL') "
                            "AND verification_state IN ('UNREVIEWED','DISPUTED','UNSUPPORTED') "
                            "ORDER BY claim_id"
                        ),
                        {"book_id": book_id},
                    ).mappings()
                )
            units = {
                cast(str, unit["unit_id"]): unit for unit in self._current_units(engine, book_id)
            }
            snapshot = {
                "claims": [
                    {
                        "claim_id": claim["claim_id"],
                        "verification_state": claim["verification_state"],
                        "manuscript_revision_id": claim["manuscript_revision_id"],
                        "manuscript_revision_hash": claim["manuscript_revision_hash"],
                    }
                    for claim in claims
                ]
            }
            run_id = self._start_run(
                engine,
                book_id=book_id,
                role="FACT_CHECKER",
                runner_id="material-claim-state",
                scope_kind="BOOK",
                chapter_id=None,
                unit_id=None,
                snapshot=snapshot,
            )
            findings: list[FindingView] = []
            for claim in claims:
                unit_id = cast(str, claim["unit_id"])
                current_unit = units.get(unit_id)
                if current_unit is None:
                    continue
                state = cast(str, claim["verification_state"])
                stale_binding = (
                    claim["manuscript_revision_id"] != current_unit["revision_id"]
                    or claim["manuscript_revision_hash"] != current_unit["revision_hash"]
                )
                category = "STALE_CLAIM_BINDING" if stale_binding else f"MATERIAL_CLAIM_{state}"
                severity = "CRITICAL" if state in {"DISPUTED", "UNSUPPORTED"} else "MAJOR"
                findings.append(
                    self.service.create_finding(
                        book_id,
                        FindingCreateRequest(
                            role="FACT_CHECKER",
                            category=category,
                            target_kind="MANUSCRIPT_UNIT",
                            target_id=unit_id,
                            base_revision_id=cast(str, current_unit["revision_id"]),
                            base_revision_hash=cast(str, current_unit["revision_hash"]),
                            diagnosis=(
                                "Material factual Claim requires human fact-check attention before release."
                                if not stale_binding
                                else "Material Claim is still bound to a prior manuscript revision."
                            ),
                            why=(
                                "Material claims must be resolved through Claim/Evidence workflow and "
                                "must not silently follow later manuscript edits."
                            ),
                            evidence={
                                "claim_id": claim["claim_id"],
                                "claim_text": claim["normalized_text"],
                                "materiality": claim["materiality"],
                                "verification_state": state,
                                "claim_revision_id": claim["manuscript_revision_id"],
                                "claim_revision_hash": claim["manuscript_revision_hash"],
                                "current_revision_id": current_unit["revision_id"],
                                "current_revision_hash": current_unit["revision_hash"],
                                "stale_binding": stale_binding,
                            },
                            severity=cast(Any, severity),
                            confidence=1.0,
                            expected_effect="Human review resolves the factual risk without auto-changing Claim state.",
                            risks="The diagnostic does not establish factual truth and does not rebind the Claim.",
                            actor="system:fact-check-audit",
                            actor_kind="SYSTEM",
                            run_id=run_id,
                        ),
                    )
                )
            self._finish_run(engine, run_id)
            return EditorialRunResult(run_id=run_id, role="FACT_CHECKER", findings=findings)
        except Exception as exc:
            if run_id is not None:
                self._finish_run(engine, run_id, exc)
            raise
        finally:
            engine.dispose()
