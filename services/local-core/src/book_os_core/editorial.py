from __future__ import annotations

from dataclasses import dataclass
import difflib
import json
from pathlib import Path
import re
from typing import Annotated, Any, Literal, cast

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import text
from sqlalchemy.engine import Engine

from .authority import (
    AuthorityService,
    HumanApprovalRequired,
    ProposalStateError,
    StaleBaselineError,
    new_ulid,
)
from .authority_types import JSONValue, utc_now
from .db import create_database

EditorialRole = Literal[
    "DEVELOPMENTAL_EDITOR",
    "CROSS_BOOK_AUDITOR",
    "FACT_CHECKER",
    "LITERARY_EDITOR",
    "STYLE_GUARDIAN",
]
FindingSeverity = Literal["INFO", "MINOR", "MAJOR", "CRITICAL"]
FindingStatus = Literal["OPEN", "RESOLVED", "WAIVED", "SUPERSEDED"]
FindingTargetKind = Literal["MANUSCRIPT_UNIT", "CHAPTER_CONTRACT", "BOOK_CONTRACT"]
ActorKind = Literal["HUMAN", "SYSTEM", "AI"]

_BOOK_ID = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$")
NonEmpty = Annotated[str, Field(min_length=1, max_length=12000)]


class EditorialError(RuntimeError):
    pass


class EditorialNotFound(EditorialError):
    pass


class EditorialGateError(EditorialError):
    pass


class EditorialDecisionError(EditorialError):
    pass


class FindingCreateRequest(BaseModel):
    role: EditorialRole
    category: Annotated[str, Field(min_length=1, max_length=96)]
    target_kind: FindingTargetKind
    target_id: str
    base_revision_id: str
    base_revision_hash: Annotated[str, Field(min_length=64, max_length=64)]
    diagnosis: NonEmpty
    why: NonEmpty
    evidence: dict[str, Any] = Field(default_factory=dict)
    severity: FindingSeverity = "MAJOR"
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    expected_effect: str = ""
    risks: str = ""
    actor: Annotated[str, Field(min_length=1, max_length=128)] = "OWNER"
    actor_kind: ActorKind = "HUMAN"
    run_id: str | None = None

    @field_validator(
        "category",
        "target_id",
        "base_revision_id",
        "base_revision_hash",
        "diagnosis",
        "why",
        "expected_effect",
        "risks",
        "actor",
    )
    @classmethod
    def strip_strings(cls, value: str) -> str:
        return value.strip()


class FindingView(BaseModel):
    finding_id: str
    run_id: str | None
    book_id: str
    role: str
    category: str
    target_kind: str
    target_entity_id: str
    chapter_id: str | None
    unit_id: str | None
    base_revision_id: str
    base_revision_hash: str
    diagnosis: str
    why: str
    evidence: dict[str, Any]
    severity: str
    confidence: float
    expected_effect: str
    risks: str
    actor: str
    actor_kind: str
    status: str
    created_at: str
    resolved_at: str | None


class ProposalCreateRequest(BaseModel):
    proposed_text: NonEmpty
    rationale: NonEmpty
    actor: Annotated[str, Field(min_length=1, max_length=128)] = "OWNER"
    actor_kind: ActorKind = "HUMAN"

    @field_validator("proposed_text", "rationale", "actor")
    @classmethod
    def strip_proposal_strings(cls, value: str) -> str:
        return value.strip()


class ProposalView(BaseModel):
    proposal_id: str
    finding_id: str
    status: str
    stale: bool
    base_revision_id: str
    base_revision_hash: str
    proposed_content_hash: str
    rationale: str
    proposed_text: str
    diff: str
    created_at: str


class DecisionRequest(BaseModel):
    actor: Annotated[str, Field(min_length=1, max_length=128)] = "OWNER"
    actor_kind: ActorKind = "HUMAN"
    reason: NonEmpty

    @field_validator("actor", "reason")
    @classmethod
    def strip_decision_strings(cls, value: str) -> str:
        return value.strip()


class DecisionResult(BaseModel):
    decision: str
    decision_id: str
    finding: FindingView
    proposal: ProposalView | None = None
    accepted_revision_id: str | None = None
    approval_id: str | None = None


class InboxItem(BaseModel):
    finding: FindingView
    proposals: list[ProposalView]
    latest_proposal: ProposalView | None
    stale: bool


class EditorialRunResult(BaseModel):
    run_id: str
    role: str
    findings: list[FindingView]


@dataclass(frozen=True)
class _TargetRef:
    target_kind: FindingTargetKind
    target_entity_id: str
    chapter_id: str | None
    unit_id: str | None
    revision_id: str
    revision_hash: str


class EditorialService:
    def __init__(self, data_dir: Path):
        self.projects_dir = data_dir / "projects"

    def _database_path(self, book_id: str) -> Path:
        if not _BOOK_ID.fullmatch(book_id):
            raise EditorialNotFound("invalid book project ID")
        path = self.projects_dir / book_id / "project.sqlite"
        if not path.is_file():
            raise EditorialNotFound(f"book project not found: {book_id}")
        return path

    def _engine(self, book_id: str) -> Engine:
        return create_database(self._database_path(book_id))

    @staticmethod
    def _resolve_target(
        engine: Engine, book_id: str, target_kind: FindingTargetKind, target_id: str
    ) -> _TargetRef:
        authority = AuthorityService(engine)
        with engine.connect() as connection:
            if target_kind == "MANUSCRIPT_UNIT":
                row = (
                    connection.execute(
                        text(
                            "SELECT mu.unit_id,mu.chapter_id,mu.authority_entity_id "
                            "FROM manuscript_units mu WHERE mu.book_id=:book_id AND mu.unit_id=:target_id"
                        ),
                        {"book_id": book_id, "target_id": target_id},
                    )
                    .mappings()
                    .one_or_none()
                )
                if row is None:
                    raise EditorialNotFound("manuscript unit target not found")
                entity_id = cast(str, row["authority_entity_id"])
                head = authority.get_head(entity_id)
                return _TargetRef(
                    target_kind=target_kind,
                    target_entity_id=entity_id,
                    chapter_id=cast(str, row["chapter_id"]),
                    unit_id=cast(str, row["unit_id"]),
                    revision_id=head.revision_id,
                    revision_hash=head.revision_hash,
                )

            if target_kind == "CHAPTER_CONTRACT":
                row = (
                    connection.execute(
                        text(
                            "SELECT chapter_id,chapter_contract_entity_id FROM chapters "
                            "WHERE book_id=:book_id AND chapter_id=:target_id "
                            "AND workflow_state!='SUPERSEDED'"
                        ),
                        {"book_id": book_id, "target_id": target_id},
                    )
                    .mappings()
                    .one_or_none()
                )
                if row is None or row["chapter_contract_entity_id"] is None:
                    raise EditorialNotFound("current Chapter Contract target not found")
                entity_id = cast(str, row["chapter_contract_entity_id"])
                head = authority.get_head(entity_id)
                return _TargetRef(
                    target_kind=target_kind,
                    target_entity_id=entity_id,
                    chapter_id=cast(str, row["chapter_id"]),
                    unit_id=None,
                    revision_id=head.revision_id,
                    revision_hash=head.revision_hash,
                )

            row = (
                connection.execute(
                    text(
                        "SELECT book_contract_entity_id FROM book_projects WHERE book_id=:book_id"
                    ),
                    {"book_id": book_id},
                )
                .mappings()
                .one_or_none()
            )
            if row is None or row["book_contract_entity_id"] is None:
                raise EditorialNotFound("current Book Contract target not found")
            entity_id = cast(str, row["book_contract_entity_id"])
            head = authority.get_head(entity_id)
            return _TargetRef(
                target_kind=target_kind,
                target_entity_id=entity_id,
                chapter_id=None,
                unit_id=None,
                revision_id=head.revision_id,
                revision_hash=head.revision_hash,
            )

    @staticmethod
    def _insert_finding_state(
        connection: Any,
        *,
        finding_id: str,
        prior_state: str | None,
        new_state: str,
        actor: str,
        actor_kind: ActorKind,
        reason: str,
        created_at: str,
    ) -> None:
        connection.execute(
            text(
                "INSERT INTO editorial_finding_state_history(state_event_id,finding_id,prior_state,"
                "new_state,actor,actor_kind,reason,created_at) VALUES (:event_id,:finding_id,"
                ":prior_state,:new_state,:actor,:actor_kind,:reason,:created_at)"
            ),
            {
                "event_id": new_ulid(),
                "finding_id": finding_id,
                "prior_state": prior_state,
                "new_state": new_state,
                "actor": actor,
                "actor_kind": actor_kind,
                "reason": reason,
                "created_at": created_at,
            },
        )

    def _create_finding_for_target(
        self,
        engine: Engine,
        book_id: str,
        target: _TargetRef,
        *,
        role: EditorialRole,
        category: str,
        diagnosis: str,
        why: str,
        evidence: dict[str, Any],
        severity: FindingSeverity,
        confidence: float,
        expected_effect: str,
        risks: str,
        actor: str,
        actor_kind: ActorKind,
        run_id: str | None,
    ) -> str:
        finding_id = new_ulid()
        now = utc_now()
        serialized_evidence = json.dumps(
            evidence, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO editorial_findings(finding_id,run_id,book_id,role,category,"
                    "target_kind,target_entity_id,chapter_id,unit_id,base_revision_id,"
                    "base_revision_hash,diagnosis,why,evidence_json,severity,confidence,"
                    "expected_effect,risks,actor,actor_kind,status,created_at) VALUES "
                    "(:finding_id,:run_id,:book_id,:role,:category,:target_kind,:target_entity_id,"
                    ":chapter_id,:unit_id,:base_revision_id,:base_revision_hash,:diagnosis,:why,"
                    ":evidence_json,:severity,:confidence,:expected_effect,:risks,:actor,:actor_kind,"
                    "'OPEN',:created_at)"
                ),
                {
                    "finding_id": finding_id,
                    "run_id": run_id,
                    "book_id": book_id,
                    "role": role,
                    "category": category,
                    "target_kind": target.target_kind,
                    "target_entity_id": target.target_entity_id,
                    "chapter_id": target.chapter_id,
                    "unit_id": target.unit_id,
                    "base_revision_id": target.revision_id,
                    "base_revision_hash": target.revision_hash,
                    "diagnosis": diagnosis,
                    "why": why,
                    "evidence_json": serialized_evidence,
                    "severity": severity,
                    "confidence": confidence,
                    "expected_effect": expected_effect,
                    "risks": risks,
                    "actor": actor,
                    "actor_kind": actor_kind,
                    "created_at": now,
                },
            )
            self._insert_finding_state(
                connection,
                finding_id=finding_id,
                prior_state=None,
                new_state="OPEN",
                actor=actor,
                actor_kind=actor_kind,
                reason="Editorial finding registered",
                created_at=now,
            )
        return finding_id

    def create_finding(self, book_id: str, request: FindingCreateRequest) -> FindingView:
        engine = self._engine(book_id)
        try:
            target = self._resolve_target(engine, book_id, request.target_kind, request.target_id)
            if (
                target.revision_id != request.base_revision_id
                or target.revision_hash != request.base_revision_hash
            ):
                raise EditorialGateError("finding baseline must match the exact current target revision")
            finding_id = self._create_finding_for_target(
                engine,
                book_id,
                target,
                role=request.role,
                category=request.category,
                diagnosis=request.diagnosis,
                why=request.why,
                evidence=request.evidence,
                severity=request.severity,
                confidence=request.confidence,
                expected_effect=request.expected_effect,
                risks=request.risks,
                actor=request.actor,
                actor_kind=request.actor_kind,
                run_id=request.run_id,
            )
            return self.get_finding(book_id, finding_id)
        finally:
            engine.dispose()

    def get_finding(self, book_id: str, finding_id: str) -> FindingView:
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                row = (
                    connection.execute(
                        text(
                            "SELECT * FROM editorial_findings WHERE book_id=:book_id "
                            "AND finding_id=:finding_id"
                        ),
                        {"book_id": book_id, "finding_id": finding_id},
                    )
                    .mappings()
                    .one_or_none()
                )
            if row is None:
                raise EditorialNotFound("editorial finding not found")
            payload = dict(row)
            payload["evidence"] = json.loads(cast(str, payload.pop("evidence_json")))
            return FindingView(**payload)
        finally:
            engine.dispose()

    def list_findings(
        self,
        book_id: str,
        *,
        role: str | None = None,
        status: str | None = None,
        severity: str | None = None,
    ) -> list[FindingView]:
        engine = self._engine(book_id)
        try:
            clauses = ["book_id=:book_id"]
            params: dict[str, object] = {"book_id": book_id}
            for key, value in (("role", role), ("status", status), ("severity", severity)):
                if value:
                    clauses.append(f"{key}=:{key}")
                    params[key] = value
            statement = text(
                "SELECT * FROM editorial_findings WHERE "
                + " AND ".join(clauses)
                + " ORDER BY CASE severity WHEN 'CRITICAL' THEN 0 WHEN 'MAJOR' THEN 1 "
                "WHEN 'MINOR' THEN 2 ELSE 3 END,created_at,finding_id"
            )
            with engine.connect() as connection:
                rows = list(connection.execute(statement, params).mappings())
            findings: list[FindingView] = []
            for row in rows:
                payload = dict(row)
                payload["evidence"] = json.loads(cast(str, payload.pop("evidence_json")))
                findings.append(FindingView(**payload))
            return findings
        finally:
            engine.dispose()

    @staticmethod
    def _proposal_origin(actor_kind: ActorKind) -> Literal[
        "HUMAN_WRITTEN", "AI_ASSISTED", "SYSTEM_DERIVED"
    ]:
        if actor_kind == "AI":
            return "AI_ASSISTED"
        if actor_kind == "SYSTEM":
            return "SYSTEM_DERIVED"
        return "HUMAN_WRITTEN"

    def create_manuscript_proposal(
        self, book_id: str, finding_id: str, request: ProposalCreateRequest
    ) -> ProposalView:
        engine = self._engine(book_id)
        try:
            finding = self.get_finding(book_id, finding_id)
            if finding.status != "OPEN":
                raise EditorialGateError(f"finding is {finding.status}, expected OPEN")
            if finding.target_kind != "MANUSCRIPT_UNIT" or not finding.unit_id:
                raise EditorialGateError("M6 manuscript proposal requires a ManuscriptUnit finding")
            target = self._resolve_target(engine, book_id, "MANUSCRIPT_UNIT", finding.unit_id)
            if (
                target.revision_id != finding.base_revision_id
                or target.revision_hash != finding.base_revision_hash
            ):
                raise EditorialGateError("finding baseline is stale; re-review is required")
            authority = AuthorityService(engine)
            revision = authority.get_revision(finding.base_revision_id)
            content = cast(dict[str, JSONValue], dict(revision["content"]))
            if "text" not in content or not isinstance(content["text"], str):
                raise EditorialGateError("target manuscript revision has no editable text field")
            content["text"] = request.proposed_text
            proposal_id = authority.create_proposal(
                entity_id=finding.target_entity_id,
                base_revision_id=finding.base_revision_id,
                base_revision_hash=finding.base_revision_hash,
                proposed_payload=content,
                schema_name=cast(str, revision["schema_name"]),
                schema_version=cast(str, revision["schema_version"]),
                rationale=f"Editorial finding {finding_id}: {request.rationale}",
                actor=request.actor,
                origin=self._proposal_origin(request.actor_kind),
                task_id=f"editorial:{finding_id}",
            )
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT INTO editorial_finding_proposals(finding_id,proposal_id,created_at) "
                        "VALUES (:finding_id,:proposal_id,:created_at)"
                    ),
                    {
                        "finding_id": finding_id,
                        "proposal_id": proposal_id,
                        "created_at": utc_now(),
                    },
                )
            return self.get_proposal(book_id, finding_id, proposal_id)
        finally:
            engine.dispose()

    @staticmethod
    def _unified_diff(before: str, after: str) -> str:
        return "".join(
            difflib.unified_diff(
                before.splitlines(keepends=True),
                after.splitlines(keepends=True),
                fromfile="current",
                tofile="proposed",
                lineterm="\n",
            )
        )

    def get_proposal(self, book_id: str, finding_id: str, proposal_id: str) -> ProposalView:
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                row = (
                    connection.execute(
                        text(
                            "SELECT p.* FROM change_proposals p JOIN editorial_finding_proposals efp "
                            "ON efp.proposal_id=p.proposal_id JOIN editorial_findings f "
                            "ON f.finding_id=efp.finding_id WHERE f.book_id=:book_id "
                            "AND f.finding_id=:finding_id AND p.proposal_id=:proposal_id"
                        ),
                        {
                            "book_id": book_id,
                            "finding_id": finding_id,
                            "proposal_id": proposal_id,
                        },
                    )
                    .mappings()
                    .one_or_none()
                )
                if row is None:
                    raise EditorialNotFound("editorial proposal not found")
                head = (
                    connection.execute(
                        text(
                            "SELECT revision_id,revision_hash FROM authority_heads "
                            "WHERE entity_id=:entity_id"
                        ),
                        {"entity_id": row["entity_id"]},
                    )
                    .mappings()
                    .one()
                )
                base_content_json = connection.execute(
                    text("SELECT content_json FROM revisions WHERE revision_id=:revision_id"),
                    {"revision_id": row["base_revision_id"]},
                ).scalar_one()
            base_content = json.loads(cast(str, base_content_json))
            proposed_content = json.loads(cast(str, row["proposed_content_json"]))
            before = str(base_content.get("text", ""))
            after = str(proposed_content.get("text", ""))
            stale = (
                head["revision_id"] != row["base_revision_id"]
                or head["revision_hash"] != row["base_revision_hash"]
            )
            return ProposalView(
                proposal_id=cast(str, row["proposal_id"]),
                finding_id=finding_id,
                status=cast(str, row["status"]),
                stale=stale,
                base_revision_id=cast(str, row["base_revision_id"]),
                base_revision_hash=cast(str, row["base_revision_hash"]),
                proposed_content_hash=cast(str, row["proposed_content_hash"]),
                rationale=cast(str, row["rationale"]),
                proposed_text=after,
                diff=self._unified_diff(before, after),
                created_at=cast(str, row["created_at"]),
            )
        finally:
            engine.dispose()

    def list_proposals(self, book_id: str, finding_id: str) -> list[ProposalView]:
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                ids = list(
                    connection.execute(
                        text(
                            "SELECT p.proposal_id FROM change_proposals p "
                            "JOIN editorial_finding_proposals efp ON efp.proposal_id=p.proposal_id "
                            "JOIN editorial_findings f ON f.finding_id=efp.finding_id "
                            "WHERE f.book_id=:book_id AND f.finding_id=:finding_id "
                            "ORDER BY p.created_at,p.proposal_id"
                        ),
                        {"book_id": book_id, "finding_id": finding_id},
                    ).scalars()
                )
            return [self.get_proposal(book_id, finding_id, cast(str, item)) for item in ids]
        finally:
            engine.dispose()

    def inbox(
        self,
        book_id: str,
        *,
        role: str | None = None,
        status: str | None = "OPEN",
        severity: str | None = None,
    ) -> list[InboxItem]:
        items: list[InboxItem] = []
        for finding in self.list_findings(
            book_id, role=role, status=status, severity=severity
        ):
            proposals = self.list_proposals(book_id, finding.finding_id)
            latest = proposals[-1] if proposals else None
            items.append(
                InboxItem(
                    finding=finding,
                    proposals=proposals,
                    latest_proposal=latest,
                    stale=bool(latest and latest.stale),
                )
            )
        return items

    def _transition_finding(
        self,
        engine: Engine,
        finding_id: str,
        *,
        new_state: FindingStatus,
        actor: str,
        actor_kind: ActorKind,
        reason: str,
    ) -> None:
        if actor_kind != "HUMAN" and new_state in {"RESOLVED", "WAIVED"}:
            raise HumanApprovalRequired("material editorial finding resolution requires a human actor")
        now = utc_now()
        with engine.begin() as connection:
            prior = connection.execute(
                text("SELECT status FROM editorial_findings WHERE finding_id=:finding_id"),
                {"finding_id": finding_id},
            ).scalar_one_or_none()
            if prior is None:
                raise EditorialNotFound("editorial finding not found")
            if prior == new_state:
                return
            connection.execute(
                text(
                    "UPDATE editorial_findings SET status=:status,resolved_at=:resolved_at "
                    "WHERE finding_id=:finding_id"
                ),
                {
                    "status": new_state,
                    "resolved_at": now if new_state != "OPEN" else None,
                    "finding_id": finding_id,
                },
            )
            self._insert_finding_state(
                connection,
                finding_id=finding_id,
                prior_state=cast(str, prior),
                new_state=new_state,
                actor=actor,
                actor_kind=actor_kind,
                reason=reason,
                created_at=now,
            )

    @staticmethod
    def _require_human(request: DecisionRequest) -> None:
        if request.actor_kind != "HUMAN":
            raise HumanApprovalRequired("material editorial decision requires a human actor")

    def accept(
        self, book_id: str, finding_id: str, proposal_id: str, request: DecisionRequest
    ) -> DecisionResult:
        self._require_human(request)
        proposal = self.get_proposal(book_id, finding_id, proposal_id)
        if proposal.stale:
            raise StaleBaselineError("editorial proposal baseline is stale")
        engine = self._engine(book_id)
        try:
            accepted = AuthorityService(engine).accept_proposal(
                proposal_id,
                actor=request.actor,
                actor_kind="HUMAN",
                reason=request.reason,
                gates={"editorial_human_review": True, "finding_id": finding_id},
            )
            self._transition_finding(
                engine,
                finding_id,
                new_state="RESOLVED",
                actor=request.actor,
                actor_kind="HUMAN",
                reason=request.reason,
            )
            return DecisionResult(
                decision="ACCEPT",
                decision_id=accepted.decision_id,
                finding=self.get_finding(book_id, finding_id),
                proposal=self.get_proposal(book_id, finding_id, proposal_id),
                accepted_revision_id=accepted.revision_id,
                approval_id=accepted.approval_id,
            )
        finally:
            engine.dispose()

    def reject(
        self, book_id: str, finding_id: str, proposal_id: str, request: DecisionRequest
    ) -> DecisionResult:
        self._require_human(request)
        self.get_proposal(book_id, finding_id, proposal_id)
        engine = self._engine(book_id)
        try:
            decision_id = AuthorityService(engine).reject_proposal(
                proposal_id,
                actor=request.actor,
                actor_kind="HUMAN",
                reason=request.reason,
            )
            return DecisionResult(
                decision="REJECT",
                decision_id=decision_id,
                finding=self.get_finding(book_id, finding_id),
                proposal=self.get_proposal(book_id, finding_id, proposal_id),
            )
        finally:
            engine.dispose()

    def request_revision(
        self, book_id: str, finding_id: str, proposal_id: str, request: DecisionRequest
    ) -> DecisionResult:
        self._require_human(request)
        proposal = self.get_proposal(book_id, finding_id, proposal_id)
        if proposal.status != "OPEN":
            raise ProposalStateError(f"proposal is {proposal.status}, expected OPEN")
        engine = self._engine(book_id)
        now = utc_now()
        decision_id = new_ulid()
        try:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT INTO decisions(decision_id,proposal_id,subject,actor,actor_kind,"
                        "decision,reason,created_at) VALUES (:decision_id,:proposal_id,:subject,"
                        ":actor,'HUMAN','REQUEST_REVISION',:reason,:created_at)"
                    ),
                    {
                        "decision_id": decision_id,
                        "proposal_id": proposal_id,
                        "subject": f"proposal:{proposal_id}",
                        "actor": request.actor,
                        "reason": request.reason,
                        "created_at": now,
                    },
                )
                result = connection.execute(
                    text(
                        "UPDATE change_proposals SET status='SUPERSEDED',resolved_at=:resolved_at "
                        "WHERE proposal_id=:proposal_id AND status='OPEN'"
                    ),
                    {"resolved_at": now, "proposal_id": proposal_id},
                )
                if result.rowcount != 1:
                    raise ProposalStateError("proposal is no longer OPEN")
            return DecisionResult(
                decision="REQUEST_REVISION",
                decision_id=decision_id,
                finding=self.get_finding(book_id, finding_id),
                proposal=self.get_proposal(book_id, finding_id, proposal_id),
            )
        finally:
            engine.dispose()

    def waive(
        self,
        book_id: str,
        finding_id: str,
        request: DecisionRequest,
        proposal_id: str | None = None,
    ) -> DecisionResult:
        self._require_human(request)
        finding = self.get_finding(book_id, finding_id)
        if finding.status != "OPEN":
            raise EditorialDecisionError(f"finding is {finding.status}, expected OPEN")
        engine = self._engine(book_id)
        now = utc_now()
        decision_id = new_ulid()
        try:
            with engine.begin() as connection:
                linked_open = list(
                    connection.execute(
                        text(
                            "SELECT p.proposal_id FROM change_proposals p "
                            "JOIN editorial_finding_proposals efp ON efp.proposal_id=p.proposal_id "
                            "WHERE efp.finding_id=:finding_id AND p.status='OPEN'"
                        ),
                        {"finding_id": finding_id},
                    ).scalars()
                )
                if proposal_id is not None and proposal_id not in linked_open:
                    existing = connection.execute(
                        text(
                            "SELECT 1 FROM editorial_finding_proposals WHERE finding_id=:finding_id "
                            "AND proposal_id=:proposal_id"
                        ),
                        {"finding_id": finding_id, "proposal_id": proposal_id},
                    ).scalar_one_or_none()
                    if existing is None:
                        raise EditorialNotFound("proposal is not linked to finding")
                decision_proposal = proposal_id or (cast(str, linked_open[-1]) if linked_open else None)
                connection.execute(
                    text(
                        "INSERT INTO decisions(decision_id,proposal_id,subject,actor,actor_kind,"
                        "decision,reason,created_at) VALUES (:decision_id,:proposal_id,:subject,"
                        ":actor,'HUMAN','WAIVE',:reason,:created_at)"
                    ),
                    {
                        "decision_id": decision_id,
                        "proposal_id": decision_proposal,
                        "subject": f"finding:{finding_id}",
                        "actor": request.actor,
                        "reason": request.reason,
                        "created_at": now,
                    },
                )
                for open_id in linked_open:
                    connection.execute(
                        text(
                            "UPDATE change_proposals SET status='SUPERSEDED',resolved_at=:resolved_at "
                            "WHERE proposal_id=:proposal_id AND status='OPEN'"
                        ),
                        {"resolved_at": now, "proposal_id": open_id},
                    )
            self._transition_finding(
                engine,
                finding_id,
                new_state="WAIVED",
                actor=request.actor,
                actor_kind="HUMAN",
                reason=request.reason,
            )
            return DecisionResult(
                decision="WAIVE",
                decision_id=decision_id,
                finding=self.get_finding(book_id, finding_id),
                proposal=(
                    self.get_proposal(book_id, finding_id, proposal_id)
                    if proposal_id is not None
                    else None
                ),
            )
        finally:
            engine.dispose()

    def decision_corpus(self, book_id: str, finding_id: str) -> dict[str, Any]:
        engine = self._engine(book_id)
        try:
            finding = self.get_finding(book_id, finding_id)
            proposals = self.list_proposals(book_id, finding_id)
            proposal_ids = [proposal.proposal_id for proposal in proposals]
            with engine.connect() as connection:
                base_revision = (
                    connection.execute(
                        text(
                            "SELECT revision_id,entity_id,content_json,content_hash,created_at "
                            "FROM revisions WHERE revision_id=:revision_id"
                        ),
                        {"revision_id": finding.base_revision_id},
                    )
                    .mappings()
                    .one()
                )
                if proposal_ids:
                    placeholders = ",".join(f":p{index}" for index in range(len(proposal_ids)))
                    params: dict[str, object] = {
                        f"p{index}": proposal_id
                        for index, proposal_id in enumerate(proposal_ids)
                    }
                    decisions = list(
                        connection.execute(
                            text(
                                f"SELECT * FROM decisions WHERE proposal_id IN ({placeholders}) "
                                "ORDER BY created_at,decision_id"
                            ),
                            params,
                        ).mappings()
                    )
                    approvals = list(
                        connection.execute(
                            text(
                                f"SELECT * FROM approvals WHERE proposal_id IN ({placeholders}) "
                                "ORDER BY created_at,approval_id"
                            ),
                            params,
                        ).mappings()
                    )
                else:
                    decisions = list(
                        connection.execute(
                            text(
                                "SELECT * FROM decisions WHERE proposal_id IS NULL "
                                "AND subject=:subject ORDER BY created_at,decision_id"
                            ),
                            {"subject": f"finding:{finding_id}"},
                        ).mappings()
                    )
                    approvals = []
                head = (
                    connection.execute(
                        text(
                            "SELECT ah.revision_id,ah.revision_hash,r.content_json,"
                            "r.content_hash FROM authority_heads ah JOIN revisions r "
                            "ON r.revision_id=ah.revision_id WHERE ah.entity_id=:entity_id"
                        ),
                        {"entity_id": finding.target_entity_id},
                    )
                    .mappings()
                    .one()
                )
            return {
                "finding": finding.model_dump(mode="json"),
                "original_revision": dict(base_revision),
                "proposals": [proposal.model_dump(mode="json") for proposal in proposals],
                "decisions": [dict(row) for row in decisions],
                "approvals": [dict(row) for row in approvals],
                "current_final_revision": dict(head),
            }
        finally:
            engine.dispose()
