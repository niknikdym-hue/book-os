from __future__ import annotations

import json
from typing import Any, cast
from collections.abc import Sequence

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

from .authority_types import (
    AuthorityError,
    AuthorityHead,
    AuthorityStatus,
    ProvenanceOrigin,
    new_ulid,
)


class AuthorityStore:
    def __init__(self, engine: Engine):
        self.engine = engine

    def get_head(self, entity_id: str) -> AuthorityHead:
        with self.engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        "SELECT h.entity_id, h.revision_id, h.revision_hash, "
                        "(SELECT s.status FROM revision_status_history s "
                        " WHERE s.revision_id=h.revision_id "
                        " ORDER BY s.created_at DESC, s.status_event_id DESC LIMIT 1) AS status "
                        "FROM authority_heads h WHERE h.entity_id=:entity_id"
                    ),
                    {"entity_id": entity_id},
                )
                .mappings()
                .one_or_none()
            )
        if row is None:
            raise AuthorityError(f"authority head not found for entity {entity_id}")
        return AuthorityHead(
            cast(str, row["entity_id"]),
            cast(str, row["revision_id"]),
            cast(str, row["revision_hash"]),
            cast(str, row["status"]),
        )

    def get_revision(self, revision_id: str) -> dict[str, Any]:
        with self.engine.connect() as connection:
            row = (
                connection.execute(
                    text("SELECT * FROM revisions WHERE revision_id=:revision_id"),
                    {"revision_id": revision_id},
                )
                .mappings()
                .one_or_none()
            )
        if row is None:
            raise AuthorityError(f"revision not found: {revision_id}")
        result = dict(row)
        result["content"] = json.loads(cast(str, result.pop("content_json")))
        return result

    def history(self, entity_id: str) -> dict[str, list[dict[str, Any]]]:
        with self.engine.connect() as connection:
            revisions = [
                dict(row)
                for row in connection.execute(
                    text("SELECT * FROM revisions WHERE entity_id=:entity_id ORDER BY created_at"),
                    {"entity_id": entity_id},
                ).mappings()
            ]
            statuses = [
                dict(row)
                for row in connection.execute(
                    text(
                        "SELECT s.* FROM revision_status_history s JOIN revisions r "
                        "ON r.revision_id=s.revision_id WHERE r.entity_id=:entity_id "
                        "ORDER BY s.created_at, s.status_event_id"
                    ),
                    {"entity_id": entity_id},
                ).mappings()
            ]
            proposals = [
                dict(row)
                for row in connection.execute(
                    text(
                        "SELECT * FROM change_proposals WHERE entity_id=:entity_id "
                        "ORDER BY created_at"
                    ),
                    {"entity_id": entity_id},
                ).mappings()
            ]
            decisions = [
                dict(row)
                for row in connection.execute(
                    text(
                        "SELECT d.* FROM decisions d JOIN change_proposals p "
                        "ON p.proposal_id=d.proposal_id WHERE p.entity_id=:entity_id "
                        "ORDER BY d.created_at"
                    ),
                    {"entity_id": entity_id},
                ).mappings()
            ]
            approvals = [
                dict(row)
                for row in connection.execute(
                    text(
                        "SELECT a.* FROM approvals a JOIN change_proposals p "
                        "ON p.proposal_id=a.proposal_id WHERE p.entity_id=:entity_id "
                        "ORDER BY a.created_at"
                    ),
                    {"entity_id": entity_id},
                ).mappings()
            ]
            provenance = [
                dict(row)
                for row in connection.execute(
                    text(
                        "SELECT DISTINCT pr.* FROM provenance_records pr "
                        "LEFT JOIN revisions r ON r.provenance_id=pr.provenance_id "
                        "LEFT JOIN change_proposals p ON p.provenance_id=pr.provenance_id "
                        "WHERE r.entity_id=:entity_id OR p.entity_id=:entity_id "
                        "ORDER BY pr.created_at"
                    ),
                    {"entity_id": entity_id},
                ).mappings()
            ]
            provenance_inputs = [
                dict(row)
                for row in connection.execute(
                    text(
                        "SELECT DISTINCT pi.* FROM provenance_inputs pi "
                        "JOIN provenance_records pr ON pr.provenance_id=pi.provenance_id "
                        "LEFT JOIN revisions r ON r.provenance_id=pr.provenance_id "
                        "LEFT JOIN change_proposals p ON p.provenance_id=pr.provenance_id "
                        "WHERE r.entity_id=:entity_id OR p.entity_id=:entity_id "
                        "ORDER BY pi.provenance_id, pi.revision_id"
                    ),
                    {"entity_id": entity_id},
                ).mappings()
            ]
        return {
            "revisions": revisions,
            "statuses": statuses,
            "proposals": proposals,
            "decisions": decisions,
            "approvals": approvals,
            "provenance": provenance,
            "provenance_inputs": provenance_inputs,
        }

    @staticmethod
    def _entity_type(connection: Connection, entity_id: str) -> str:
        value = connection.execute(
            text("SELECT entity_type FROM authority_entities WHERE entity_id=:entity_id"),
            {"entity_id": entity_id},
        ).scalar_one_or_none()
        if value is None:
            raise AuthorityError(f"entity not found: {entity_id}")
        return cast(str, value)

    @staticmethod
    def _insert_provenance(
        connection: Connection,
        *,
        provenance_id: str,
        origin: ProvenanceOrigin,
        actor: str,
        task_id: str | None,
        input_revision_ids: Sequence[str],
        created_at: str,
    ) -> None:
        connection.execute(
            text(
                "INSERT INTO provenance_records(provenance_id,origin,actor,task_id,created_at) "
                "VALUES (:provenance_id,:origin,:actor,:task_id,:created_at)"
            ),
            {
                "provenance_id": provenance_id,
                "origin": origin,
                "actor": actor,
                "task_id": task_id,
                "created_at": created_at,
            },
        )
        for revision_id in input_revision_ids:
            connection.execute(
                text(
                    "INSERT INTO provenance_inputs(provenance_id,revision_id) "
                    "VALUES (:provenance_id,:revision_id)"
                ),
                {"provenance_id": provenance_id, "revision_id": revision_id},
            )

    @staticmethod
    def _insert_revision(
        connection: Connection,
        *,
        revision_id: str,
        entity_id: str,
        entity_type: str,
        schema_name: str,
        schema_version: str,
        serialized: str,
        digest: str,
        provenance_id: str,
        parents: Sequence[str],
        created_at: str,
    ) -> None:
        connection.execute(
            text(
                "INSERT INTO revisions(revision_id,entity_id,entity_type,schema_name,schema_version,"
                "content_json,content_hash,provenance_id,created_at) VALUES (:revision_id,:entity_id,"
                ":entity_type,:schema_name,:schema_version,:content_json,:content_hash,"
                ":provenance_id,:created_at)"
            ),
            {
                "revision_id": revision_id,
                "entity_id": entity_id,
                "entity_type": entity_type,
                "schema_name": schema_name,
                "schema_version": schema_version,
                "content_json": serialized,
                "content_hash": digest,
                "provenance_id": provenance_id,
                "created_at": created_at,
            },
        )
        for parent in parents:
            connection.execute(
                text(
                    "INSERT INTO revision_parents(revision_id,parent_revision_id) "
                    "VALUES (:revision_id,:parent_revision_id)"
                ),
                {"revision_id": revision_id, "parent_revision_id": parent},
            )

    @staticmethod
    def _insert_status(
        connection: Connection,
        *,
        revision_id: str,
        status: AuthorityStatus,
        actor: str,
        reason: str,
        created_at: str,
    ) -> None:
        connection.execute(
            text(
                "INSERT INTO revision_status_history(status_event_id,revision_id,status,actor,reason,"
                "created_at) VALUES (:status_event_id,:revision_id,:status,:actor,:reason,:created_at)"
            ),
            {
                "status_event_id": new_ulid(),
                "revision_id": revision_id,
                "status": status,
                "actor": actor,
                "reason": reason,
                "created_at": created_at,
            },
        )

    @staticmethod
    def _effective_status(connection: Connection, revision_id: str) -> str:
        value = connection.execute(
            text(
                "SELECT status FROM revision_status_history WHERE revision_id=:revision_id "
                "ORDER BY created_at DESC, status_event_id DESC LIMIT 1"
            ),
            {"revision_id": revision_id},
        ).scalar_one_or_none()
        if value is None:
            raise AuthorityError(f"revision has no authority status: {revision_id}")
        return cast(str, value)
