from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
import hashlib
from typing import cast

from sqlalchemy import text

from .authority_store import AuthorityStore
from .authority_types import (
    ActorKind,
    AuthorityError,
    AuthorityHead,
    AuthorityStatus,
    HumanApprovalRequired,
    InvalidAuthorityOperation,
    JSONValue,
    ProposalAcceptance,
    ProposalStateError,
    ProvenanceOrigin,
    StaleBaselineError,
    canonical_json,
    content_hash,
    new_ulid,
    utc_now,
)

__all__ = [
    "AuthorityError",
    "AuthorityHead",
    "AuthorityService",
    "HumanApprovalRequired",
    "InvalidAuthorityOperation",
    "ProposalAcceptance",
    "ProposalStateError",
    "StaleBaselineError",
    "canonical_json",
    "content_hash",
    "new_ulid",
]


class AuthorityService(AuthorityStore):
    def register_entity(
        self,
        *,
        entity_type: str,
        payload: Mapping[str, JSONValue],
        schema_name: str,
        schema_version: str,
        actor: str,
        actor_kind: ActorKind = "HUMAN",
        origin: ProvenanceOrigin = "HUMAN_WRITTEN",
        initial_status: AuthorityStatus = "APPROVED",
    ) -> AuthorityHead:
        if initial_status in {"APPROVED", "LOCKED"} and actor_kind != "HUMAN":
            raise HumanApprovalRequired("initial approved/locked authority requires a human actor")
        now = utc_now()
        entity_id = new_ulid()
        revision_id = new_ulid()
        provenance_id = new_ulid()
        serialized = canonical_json(payload)
        digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        with self.engine.begin() as connection:
            self._insert_provenance(
                connection,
                provenance_id=provenance_id,
                origin=origin,
                actor=actor,
                task_id=None,
                input_revision_ids=(),
                created_at=now,
            )
            connection.execute(
                text(
                    "INSERT INTO authority_entities(entity_id, entity_type, created_at) "
                    "VALUES (:entity_id, :entity_type, :created_at)"
                ),
                {"entity_id": entity_id, "entity_type": entity_type, "created_at": now},
            )
            self._insert_revision(
                connection,
                revision_id=revision_id,
                entity_id=entity_id,
                entity_type=entity_type,
                schema_name=schema_name,
                schema_version=schema_version,
                serialized=serialized,
                digest=digest,
                provenance_id=provenance_id,
                parents=(),
                created_at=now,
            )
            self._insert_status(
                connection,
                revision_id=revision_id,
                status=initial_status,
                actor=actor,
                reason="initial authority",
                created_at=now,
            )
            connection.execute(
                text(
                    "INSERT INTO authority_heads(entity_id, revision_id, revision_hash, updated_at) "
                    "VALUES (:entity_id, :revision_id, :revision_hash, :updated_at)"
                ),
                {
                    "entity_id": entity_id,
                    "revision_id": revision_id,
                    "revision_hash": digest,
                    "updated_at": now,
                },
            )
        return AuthorityHead(entity_id, revision_id, digest, initial_status)

    def create_revision(
        self,
        *,
        entity_id: str,
        payload: Mapping[str, JSONValue],
        schema_name: str,
        schema_version: str,
        actor: str,
        origin: ProvenanceOrigin,
        status: AuthorityStatus = "DRAFT",
        parent_revision_ids: Sequence[str] = (),
        task_id: str | None = None,
        input_revision_ids: Sequence[str] = (),
    ) -> str:
        now = utc_now()
        revision_id = new_ulid()
        provenance_id = new_ulid()
        serialized = canonical_json(payload)
        digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        with self.engine.begin() as connection:
            entity_type = self._entity_type(connection, entity_id)
            self._insert_provenance(
                connection,
                provenance_id=provenance_id,
                origin=origin,
                actor=actor,
                task_id=task_id,
                input_revision_ids=input_revision_ids,
                created_at=now,
            )
            self._insert_revision(
                connection,
                revision_id=revision_id,
                entity_id=entity_id,
                entity_type=entity_type,
                schema_name=schema_name,
                schema_version=schema_version,
                serialized=serialized,
                digest=digest,
                provenance_id=provenance_id,
                parents=parent_revision_ids,
                created_at=now,
            )
            self._insert_status(
                connection,
                revision_id=revision_id,
                status=status,
                actor=actor,
                reason="revision created",
                created_at=now,
            )
        return revision_id

    def create_proposal(
        self,
        *,
        entity_id: str,
        base_revision_id: str,
        base_revision_hash: str,
        proposed_payload: Mapping[str, JSONValue],
        schema_name: str,
        schema_version: str,
        rationale: str,
        actor: str,
        origin: ProvenanceOrigin = "HUMAN_WRITTEN",
        task_id: str | None = None,
        input_revision_ids: Sequence[str] = (),
    ) -> str:
        proposal_id = new_ulid()
        provenance_id = new_ulid()
        now = utc_now()
        serialized = canonical_json(proposed_payload)
        digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        with self.engine.begin() as connection:
            base = connection.execute(
                text(
                    "SELECT entity_id, content_hash FROM revisions "
                    "WHERE revision_id=:revision_id"
                ),
                {"revision_id": base_revision_id},
            ).mappings().one_or_none()
            if base is None or base["entity_id"] != entity_id:
                raise AuthorityError("proposal base revision does not belong to target entity")
            if base["content_hash"] != base_revision_hash:
                raise AuthorityError("proposal base revision hash does not match stored revision")
            self._insert_provenance(
                connection,
                provenance_id=provenance_id,
                origin=origin,
                actor=actor,
                task_id=task_id,
                input_revision_ids=input_revision_ids,
                created_at=now,
            )
            connection.execute(
                text(
                    "INSERT INTO change_proposals("
                    "proposal_id,entity_id,base_revision_id,base_revision_hash,"
                    "proposed_schema_name,proposed_schema_version,proposed_content_json,"
                    "proposed_content_hash,rationale,status,provenance_id,created_at) "
                    "VALUES (:proposal_id,:entity_id,:base_revision_id,:base_revision_hash,"
                    ":schema_name,:schema_version,:content_json,:content_hash,:rationale,"
                    "'OPEN',:provenance_id,:created_at)"
                ),
                {
                    "proposal_id": proposal_id,
                    "entity_id": entity_id,
                    "base_revision_id": base_revision_id,
                    "base_revision_hash": base_revision_hash,
                    "schema_name": schema_name,
                    "schema_version": schema_version,
                    "content_json": serialized,
                    "content_hash": digest,
                    "rationale": rationale,
                    "provenance_id": provenance_id,
                    "created_at": now,
                },
            )
        return proposal_id

    def accept_proposal(
        self,
        proposal_id: str,
        *,
        actor: str,
        actor_kind: ActorKind,
        reason: str,
        gates: Mapping[str, JSONValue],
        fault_injector: Callable[[str], None] | None = None,
    ) -> ProposalAcceptance:
        if actor_kind != "HUMAN":
            raise HumanApprovalRequired("material authority acceptance requires a human actor")
        now = utc_now()
        decision_id = new_ulid()
        revision_id = new_ulid()
        approval_id = new_ulid()
        with self.engine.begin() as connection:
            proposal = connection.execute(
                text("SELECT * FROM change_proposals WHERE proposal_id=:proposal_id"),
                {"proposal_id": proposal_id},
            ).mappings().one_or_none()
            if proposal is None:
                raise AuthorityError(f"proposal not found: {proposal_id}")
            if proposal["status"] != "OPEN":
                raise ProposalStateError(f"proposal is {proposal['status']}, expected OPEN")

            head = connection.execute(
                text(
                    "SELECT revision_id,revision_hash FROM authority_heads "
                    "WHERE entity_id=:entity_id"
                ),
                {"entity_id": proposal["entity_id"]},
            ).mappings().one()
            if (
                head["revision_id"] != proposal["base_revision_id"]
                or head["revision_hash"] != proposal["base_revision_hash"]
            ):
                raise StaleBaselineError("proposal baseline no longer matches current authority")

            connection.execute(
                text(
                    "INSERT INTO decisions(decision_id,proposal_id,subject,actor,actor_kind,"
                    "decision,reason,created_at) VALUES (:decision_id,:proposal_id,:subject,"
                    ":actor,:actor_kind,'ACCEPT',:reason,:created_at)"
                ),
                {
                    "decision_id": decision_id,
                    "proposal_id": proposal_id,
                    "subject": f"proposal:{proposal_id}",
                    "actor": actor,
                    "actor_kind": actor_kind,
                    "reason": reason,
                    "created_at": now,
                },
            )
            self._fault(fault_injector, "after_decision")

            entity_type = self._entity_type(connection, cast(str, proposal["entity_id"]))
            self._insert_revision(
                connection,
                revision_id=revision_id,
                entity_id=cast(str, proposal["entity_id"]),
                entity_type=entity_type,
                schema_name=cast(str, proposal["proposed_schema_name"]),
                schema_version=cast(str, proposal["proposed_schema_version"]),
                serialized=cast(str, proposal["proposed_content_json"]),
                digest=cast(str, proposal["proposed_content_hash"]),
                provenance_id=cast(str, proposal["provenance_id"]),
                parents=(cast(str, proposal["base_revision_id"]),),
                created_at=now,
            )
            self._insert_status(
                connection,
                revision_id=revision_id,
                status="APPROVED",
                actor=actor,
                reason=reason,
                created_at=now,
            )
            self._insert_status(
                connection,
                revision_id=cast(str, proposal["base_revision_id"]),
                status="SUPERSEDED",
                actor=actor,
                reason=f"superseded by {revision_id}",
                created_at=now,
            )
            self._fault(fault_injector, "before_head_compare_and_set")

            result = connection.execute(
                text(
                    "UPDATE authority_heads SET revision_id=:new_revision_id,"
                    "revision_hash=:new_hash,updated_at=:updated_at "
                    "WHERE entity_id=:entity_id AND revision_id=:base_revision_id "
                    "AND revision_hash=:base_revision_hash"
                ),
                {
                    "new_revision_id": revision_id,
                    "new_hash": proposal["proposed_content_hash"],
                    "updated_at": now,
                    "entity_id": proposal["entity_id"],
                    "base_revision_id": proposal["base_revision_id"],
                    "base_revision_hash": proposal["base_revision_hash"],
                },
            )
            if result.rowcount != 1:
                raise StaleBaselineError("atomic authority compare-and-set failed")

            connection.execute(
                text(
                    "UPDATE change_proposals SET status='ACCEPTED',resolved_at=:resolved_at "
                    "WHERE proposal_id=:proposal_id AND status='OPEN'"
                ),
                {"resolved_at": now, "proposal_id": proposal_id},
            )
            connection.execute(
                text(
                    "INSERT INTO approvals(approval_id,proposal_id,decision_id,approved_revision_id,"
                    "prior_revision_id,approving_actor,approving_actor_kind,gates_json,created_at) "
                    "VALUES (:approval_id,:proposal_id,:decision_id,:approved_revision_id,"
                    ":prior_revision_id,:actor,:actor_kind,:gates_json,:created_at)"
                ),
                {
                    "approval_id": approval_id,
                    "proposal_id": proposal_id,
                    "decision_id": decision_id,
                    "approved_revision_id": revision_id,
                    "prior_revision_id": proposal["base_revision_id"],
                    "actor": actor,
                    "actor_kind": actor_kind,
                    "gates_json": canonical_json(gates),
                    "created_at": now,
                },
            )
            self._fault(fault_injector, "after_approval")
        return ProposalAcceptance(proposal_id, revision_id, decision_id, approval_id)

    def reject_proposal(
        self,
        proposal_id: str,
        *,
        actor: str,
        actor_kind: ActorKind,
        reason: str,
    ) -> str:
        if actor_kind != "HUMAN":
            raise HumanApprovalRequired("material proposal rejection requires a human actor")
        decision_id = new_ulid()
        now = utc_now()
        with self.engine.begin() as connection:
            proposal = connection.execute(
                text("SELECT status FROM change_proposals WHERE proposal_id=:proposal_id"),
                {"proposal_id": proposal_id},
            ).mappings().one_or_none()
            if proposal is None:
                raise AuthorityError(f"proposal not found: {proposal_id}")
            if proposal["status"] != "OPEN":
                raise ProposalStateError(f"proposal is {proposal['status']}, expected OPEN")
            connection.execute(
                text(
                    "INSERT INTO decisions(decision_id,proposal_id,subject,actor,actor_kind,"
                    "decision,reason,created_at) VALUES (:decision_id,:proposal_id,:subject,"
                    ":actor,:actor_kind,'REJECT',:reason,:created_at)"
                ),
                {
                    "decision_id": decision_id,
                    "proposal_id": proposal_id,
                    "subject": f"proposal:{proposal_id}",
                    "actor": actor,
                    "actor_kind": actor_kind,
                    "reason": reason,
                    "created_at": now,
                },
            )
            connection.execute(
                text(
                    "UPDATE change_proposals SET status='REJECTED',resolved_at=:resolved_at "
                    "WHERE proposal_id=:proposal_id AND status='OPEN'"
                ),
                {"resolved_at": now, "proposal_id": proposal_id},
            )
        return decision_id

    def advance_revision_status(
        self, revision_id: str, *, new_status: AuthorityStatus, actor: str, reason: str
    ) -> None:
        """Advance pre-authority review state without bypassing formal Approval semantics."""
        allowed = {("DRAFT", "PROPOSED"), ("PROPOSED", "REVIEWED")}
        with self.engine.begin() as connection:
            current = self._effective_status(connection, revision_id)
            if (current, new_status) not in allowed:
                raise InvalidAuthorityOperation(
                    f"invalid direct authority transition {current} -> {new_status}; "
                    "APPROVED/LOCKED/SUPERSEDED require formal authority operations"
                )
            self._insert_status(
                connection,
                revision_id=revision_id,
                status=new_status,
                actor=actor,
                reason=reason,
                created_at=utc_now(),
            )

    def lock_authority(self, entity_id: str, *, actor: str, actor_kind: ActorKind, reason: str) -> None:
        if actor_kind != "HUMAN":
            raise HumanApprovalRequired("locking authority requires a human actor")
        with self.engine.begin() as connection:
            head = connection.execute(
                text("SELECT revision_id FROM authority_heads WHERE entity_id=:entity_id"),
                {"entity_id": entity_id},
            ).mappings().one_or_none()
            if head is None:
                raise AuthorityError(f"authority head not found: {entity_id}")
            status = self._effective_status(connection, cast(str, head["revision_id"]))
            if status != "APPROVED":
                raise InvalidAuthorityOperation(f"only APPROVED authority can be locked, got {status}")
            self._insert_status(
                connection,
                revision_id=cast(str, head["revision_id"]),
                status="LOCKED",
                actor=actor,
                reason=reason,
                created_at=utc_now(),
            )

    @staticmethod
    def _fault(fault_injector: Callable[[str], None] | None, point: str) -> None:
        if fault_injector is not None:
            fault_injector(point)
