from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, cast

from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.engine import Engine

from .authority import canonical_json
from .authority_types import utc_now
from .db import create_database
from .projects import ProjectService


class LiteraryMasterError(RuntimeError):
    pass


class LiteraryMasterGateError(LiteraryMasterError):
    pass


class LiteraryMasterNotFound(LiteraryMasterError):
    pass


class ReleaseBlocker(BaseModel):
    code: str
    detail: str


class ReleaseReadiness(BaseModel):
    book_id: str
    ready: bool
    blockers: list[ReleaseBlocker] = Field(default_factory=list)
    snapshot_id: str | None = None
    snapshot_hash: str | None = None


class LiteraryMasterView(BaseModel):
    master_id: str
    book_id: str
    manifest_version: str
    manifest_hash: str
    canonical_content_hash: str
    book_title: str
    human_actor: str
    created_at: str
    status: str
    manifest: dict[str, Any]


class LiteraryMasterExportView(BaseModel):
    export_id: str
    master_id: str
    format: str
    content_hash: str
    byte_length: int
    relative_path: str
    created_at: str


@dataclass(frozen=True)
class _Head:
    entity_id: str
    revision_id: str
    revision_hash: str
    status: str
    content: dict[str, Any]


@dataclass(frozen=True)
class _ReleaseState:
    book_id: str
    title: str
    book_contract: _Head
    architecture: _Head
    chapters: list[dict[str, Any]]
    units: list[dict[str, Any]]
    snapshot_id: str
    snapshot_hash: str
    editorial_waived_count: int


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_bytes(value: object) -> bytes:
    return canonical_json(cast(Any, value)).encode("utf-8")


class LiteraryMasterService:
    MANIFEST_VERSION = "literary-master.v1"
    HANDOFF_VERSION = "book-os-audiobook-handoff.v1"
    REQUIRED_DETERMINISTIC_CHECK_IDS = (
        "deterministic.repetition",
        "deterministic.statistics",
        "deterministic.specificity",
        "deterministic.evidence",
        "deterministic.contract_structure",
        "deterministic.ai_prose_pathology",
        "deterministic.opening_ending_transition",
    )

    def __init__(self, data_dir: Path):
        self._projects = ProjectService(data_dir)

    def _database_path(self, book_id: str) -> Path:
        return self._projects._database_path(book_id)

    def _engine(self, book_id: str) -> Engine:
        return create_database(self._database_path(book_id))

    @staticmethod
    def _head(connection: Any, entity_id: str) -> _Head:
        row = (
            connection.execute(
                text(
                    "SELECT h.entity_id,h.revision_id,h.revision_hash,r.content_json,"
                    "(SELECT s.status FROM revision_status_history s "
                    "WHERE s.revision_id=h.revision_id "
                    "ORDER BY s.created_at DESC,s.status_event_id DESC LIMIT 1) AS status "
                    "FROM authority_heads h JOIN revisions r ON r.revision_id=h.revision_id "
                    "WHERE h.entity_id=:entity_id"
                ),
                {"entity_id": entity_id},
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            raise LiteraryMasterGateError(f"authority head missing for entity {entity_id}")
        return _Head(
            str(row["entity_id"]),
            str(row["revision_id"]),
            str(row["revision_hash"]),
            str(row["status"]),
            cast(dict[str, Any], json.loads(str(row["content_json"]))),
        )

    @staticmethod
    def _approved(head: _Head) -> bool:
        return head.status in {"APPROVED", "LOCKED"}

    def readiness(self, book_id: str) -> ReleaseReadiness:
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                state, blockers = self._collect_state(connection, book_id)
            return ReleaseReadiness(
                book_id=book_id,
                ready=not blockers,
                blockers=blockers,
                snapshot_id=state.snapshot_id if state else None,
                snapshot_hash=state.snapshot_hash if state else None,
            )
        finally:
            engine.dispose()

    def _collect_state(
        self, connection: Any, book_id: str
    ) -> tuple[_ReleaseState | None, list[ReleaseBlocker]]:
        blockers: list[ReleaseBlocker] = []
        project = (
            connection.execute(
                text(
                    "SELECT book_id,working_title,book_contract_entity_id,architecture_entity_id "
                    "FROM book_projects WHERE book_id=:book_id"
                ),
                {"book_id": book_id},
            )
            .mappings()
            .one_or_none()
        )
        if project is None:
            raise LiteraryMasterNotFound(f"book project not found: {book_id}")

        if project["book_contract_entity_id"] is None:
            blockers.append(
                ReleaseBlocker(code="BOOK_CONTRACT_MISSING", detail="Book Contract missing")
            )
        if project["architecture_entity_id"] is None:
            blockers.append(
                ReleaseBlocker(code="ARCHITECTURE_MISSING", detail="Architecture missing")
            )
        if blockers:
            return None, blockers

        book_contract = self._head(connection, str(project["book_contract_entity_id"]))
        architecture = self._head(connection, str(project["architecture_entity_id"]))
        if not self._approved(book_contract):
            blockers.append(
                ReleaseBlocker(
                    code="BOOK_CONTRACT_NOT_APPROVED",
                    detail=f"Book Contract status is {book_contract.status}",
                )
            )
        if not self._approved(architecture):
            blockers.append(
                ReleaseBlocker(
                    code="ARCHITECTURE_NOT_APPROVED",
                    detail=f"Architecture status is {architecture.status}",
                )
            )

        chapter_rows = list(
            connection.execute(
                text(
                    "SELECT chapter_id,ordinal,working_title,chapter_contract_entity_id "
                    "FROM chapters WHERE book_id=:book_id AND workflow_state!='SUPERSEDED' "
                    "ORDER BY ordinal,chapter_id"
                ),
                {"book_id": book_id},
            ).mappings()
        )
        chapters: list[dict[str, Any]] = []
        expected_snapshot: dict[tuple[str, str], tuple[str, str]] = {
            ("BOOK_CONTRACT", book_contract.entity_id): (
                book_contract.revision_id,
                book_contract.revision_hash,
            )
        }
        all_units: list[dict[str, Any]] = []
        for row in chapter_rows:
            chapter_id = str(row["chapter_id"])
            contract_entity = row["chapter_contract_entity_id"]
            if contract_entity is None:
                blockers.append(
                    ReleaseBlocker(
                        code="CHAPTER_CONTRACT_MISSING",
                        detail=f"Chapter {row['ordinal']} has no Chapter Contract",
                    )
                )
                contract_head = None
            else:
                contract_head = self._head(connection, str(contract_entity))
                if not self._approved(contract_head):
                    blockers.append(
                        ReleaseBlocker(
                            code="CHAPTER_CONTRACT_NOT_APPROVED",
                            detail=f"Chapter {row['ordinal']} contract status is {contract_head.status}",
                        )
                    )
                expected_snapshot[("CHAPTER_CONTRACT", contract_head.entity_id)] = (
                    contract_head.revision_id,
                    contract_head.revision_hash,
                )

            unit_rows = list(
                connection.execute(
                    text(
                        "SELECT unit_id,ordinal,authority_entity_id FROM manuscript_units "
                        "WHERE book_id=:book_id AND chapter_id=:chapter_id ORDER BY ordinal,unit_id"
                    ),
                    {"book_id": book_id, "chapter_id": chapter_id},
                ).mappings()
            )
            if not unit_rows:
                blockers.append(
                    ReleaseBlocker(
                        code="CHAPTER_MANUSCRIPT_EMPTY",
                        detail=f"Chapter {row['ordinal']} has no manuscript units",
                    )
                )
            units: list[dict[str, Any]] = []
            for unit_row in unit_rows:
                head = self._head(connection, str(unit_row["authority_entity_id"]))
                if not self._approved(head):
                    blockers.append(
                        ReleaseBlocker(
                            code="MANUSCRIPT_UNIT_NOT_APPROVED",
                            detail=f"Unit {unit_row['unit_id']} status is {head.status}",
                        )
                    )
                text_value = head.content.get("text")
                if not isinstance(text_value, str):
                    blockers.append(
                        ReleaseBlocker(
                            code="MANUSCRIPT_TEXT_MISSING",
                            detail=f"Unit {unit_row['unit_id']} has no text",
                        )
                    )
                    text_value = ""
                expected_snapshot[("MANUSCRIPT_UNIT", str(unit_row["unit_id"]))] = (
                    head.revision_id,
                    head.revision_hash,
                )
                unit = {
                    "unit_id": str(unit_row["unit_id"]),
                    "ordinal": int(unit_row["ordinal"]),
                    "revision_id": head.revision_id,
                    "revision_hash": head.revision_hash,
                    "content_hash": _sha256_bytes(text_value.encode("utf-8")),
                    "text": text_value,
                }
                units.append(unit)
                all_units.append({**unit, "chapter_id": chapter_id})
            chapters.append(
                {
                    "chapter_id": chapter_id,
                    "ordinal": int(row["ordinal"]),
                    "title": str(row["working_title"]),
                    "contract_revision_id": contract_head.revision_id if contract_head else None,
                    "contract_revision_hash": contract_head.revision_hash
                    if contract_head
                    else None,
                    "units": units,
                }
            )

        if not all_units:
            blockers.append(
                ReleaseBlocker(code="MANUSCRIPT_EMPTY", detail="Book has no manuscript units")
            )

        open_editorial = list(
            connection.execute(
                text(
                    "SELECT finding_id,severity FROM editorial_findings "
                    "WHERE book_id=:book_id AND status='OPEN' AND severity IN ('MAJOR','CRITICAL')"
                ),
                {"book_id": book_id},
            ).mappings()
        )
        for finding in open_editorial:
            blockers.append(
                ReleaseBlocker(
                    code="EDITORIAL_BLOCKING_OPEN",
                    detail=f"Open {finding['severity']} editorial finding {finding['finding_id']}",
                )
            )
        waived_count = 0
        waived_editorial = list(
            connection.execute(
                text(
                    "SELECT f.finding_id,f.severity,"
                    "(SELECT h.actor_kind FROM editorial_finding_state_history h "
                    "WHERE h.finding_id=f.finding_id AND h.new_state='WAIVED' "
                    "ORDER BY h.created_at DESC,h.state_event_id DESC LIMIT 1) AS waiver_actor_kind "
                    "FROM editorial_findings f WHERE f.book_id=:book_id "
                    "AND f.status='WAIVED' AND f.severity IN ('MAJOR','CRITICAL')"
                ),
                {"book_id": book_id},
            ).mappings()
        )
        for finding in waived_editorial:
            if str(finding["waiver_actor_kind"]) != "HUMAN":
                blockers.append(
                    ReleaseBlocker(
                        code="EDITORIAL_WAIVER_NOT_HUMAN",
                        detail=f"Material waiver {finding['finding_id']} lacks human decision evidence",
                    )
                )
            else:
                waived_count += 1

        snapshot = (
            connection.execute(
                text(
                    "SELECT snapshot_id,snapshot_hash,created_at FROM evaluation_snapshots "
                    "WHERE book_id=:book_id AND scope='BOOK' ORDER BY created_at DESC,snapshot_id DESC LIMIT 1"
                ),
                {"book_id": book_id},
            )
            .mappings()
            .one_or_none()
        )
        snapshot_id = ""
        snapshot_hash = ""
        if snapshot is None:
            blockers.append(
                ReleaseBlocker(
                    code="BOOKBENCH_SNAPSHOT_MISSING", detail="No BOOK BookBench snapshot exists"
                )
            )
        else:
            snapshot_id = str(snapshot["snapshot_id"])
            snapshot_hash = str(snapshot["snapshot_hash"])
            actual_snapshot: dict[tuple[str, str], tuple[str, str]] = {}
            for target in connection.execute(
                text(
                    "SELECT target_kind,target_id,revision_id,revision_hash "
                    "FROM evaluation_snapshot_targets WHERE snapshot_id=:snapshot_id "
                    "AND target_kind IN ('BOOK_CONTRACT','CHAPTER_CONTRACT','MANUSCRIPT_UNIT')"
                ),
                {"snapshot_id": snapshot_id},
            ).mappings():
                actual_snapshot[(str(target["target_kind"]), str(target["target_id"]))] = (
                    str(target["revision_id"]),
                    str(target["revision_hash"]),
                )
            if actual_snapshot != expected_snapshot:
                blockers.append(
                    ReleaseBlocker(
                        code="BOOKBENCH_SNAPSHOT_STALE",
                        detail="Latest BookBench snapshot does not match exact release revisions",
                    )
                )
            snapshot_claim_count = int(
                connection.execute(
                    text(
                        "SELECT COUNT(*) FROM evaluation_snapshot_targets "
                        "WHERE snapshot_id=:snapshot_id AND target_kind='CLAIM'"
                    ),
                    {"snapshot_id": snapshot_id},
                ).scalar_one()
            )
            current_claim_count = int(
                connection.execute(
                    text("SELECT COUNT(*) FROM claims WHERE book_id=:book_id"),
                    {"book_id": book_id},
                ).scalar_one()
            )
            claims_changed_after_snapshot = int(
                connection.execute(
                    text(
                        "SELECT COUNT(*) FROM claims WHERE book_id=:book_id AND updated_at>:snapshot_created_at"
                    ),
                    {
                        "book_id": book_id,
                        "snapshot_created_at": str(snapshot["created_at"]),
                    },
                ).scalar_one()
            )
            if snapshot_claim_count != current_claim_count or claims_changed_after_snapshot:
                blockers.append(
                    ReleaseBlocker(
                        code="BOOKBENCH_CLAIM_STATE_STALE",
                        detail="Claim state changed after the latest BookBench release snapshot",
                    )
                )
            succeeded_check_ids = {
                str(value)
                for value in connection.execute(
                    text(
                        "SELECT DISTINCT check_id FROM evaluation_runs "
                        "WHERE snapshot_id=:snapshot_id AND status='SUCCEEDED'"
                    ),
                    {"snapshot_id": snapshot_id},
                ).scalars()
            }
            missing_checks = [
                check_id
                for check_id in self.REQUIRED_DETERMINISTIC_CHECK_IDS
                if check_id not in succeeded_check_ids
            ]
            if missing_checks:
                blockers.append(
                    ReleaseBlocker(
                        code="BOOKBENCH_REQUIRED_CHECKS_MISSING",
                        detail="Required deterministic BookBench checks missing: "
                        + ", ".join(missing_checks),
                    )
                )
            blocking = list(
                connection.execute(
                    text(
                        "SELECT f.finding_id,f.dimension FROM evaluation_findings f "
                        "JOIN evaluation_runs r ON r.evaluation_id=f.evaluation_id "
                        "WHERE r.snapshot_id=:snapshot_id AND r.status='SUCCEEDED' "
                        "AND f.severity='BLOCKING'"
                    ),
                    {"snapshot_id": snapshot_id},
                ).mappings()
            )
            for finding in blocking:
                blockers.append(
                    ReleaseBlocker(
                        code="BOOKBENCH_BLOCKING",
                        detail=f"{finding['dimension']} finding {finding['finding_id']} is BLOCKING",
                    )
                )

        state = _ReleaseState(
            book_id=book_id,
            title=str(project["working_title"]),
            book_contract=book_contract,
            architecture=architecture,
            chapters=chapters,
            units=all_units,
            snapshot_id=snapshot_id,
            snapshot_hash=snapshot_hash,
            editorial_waived_count=waived_count,
        )
        return state, blockers

    @staticmethod
    def _canonical_manuscript(state: _ReleaseState) -> bytes:
        pieces: list[str] = [f"# {state.title}\n"]
        for chapter in state.chapters:
            pieces.append(f"\n## {chapter['ordinal']}. {chapter['title']}\n")
            for unit in chapter["units"]:
                pieces.append("\n")
                pieces.append(cast(str, unit["text"]))
                pieces.append("\n")
        text_value = "".join(pieces).replace("\r\n", "\n").replace("\r", "\n")
        if not text_value.endswith("\n"):
            text_value += "\n"
        return text_value.encode("utf-8")

    @staticmethod
    def _manifest(state: _ReleaseState, canonical_content_hash: str) -> dict[str, Any]:
        return {
            "manifest_version": LiteraryMasterService.MANIFEST_VERSION,
            "book_id": state.book_id,
            "book_title": state.title,
            "book_contract": {
                "revision_id": state.book_contract.revision_id,
                "revision_hash": state.book_contract.revision_hash,
            },
            "architecture": {
                "revision_id": state.architecture.revision_id,
                "revision_hash": state.architecture.revision_hash,
            },
            "chapters": [
                {
                    "chapter_id": chapter["chapter_id"],
                    "ordinal": chapter["ordinal"],
                    "title": chapter["title"],
                    "contract_revision_id": chapter["contract_revision_id"],
                    "contract_revision_hash": chapter["contract_revision_hash"],
                    "units": [
                        {
                            "unit_id": unit["unit_id"],
                            "ordinal": unit["ordinal"],
                            "revision_id": unit["revision_id"],
                            "revision_hash": unit["revision_hash"],
                            "content_hash": unit["content_hash"],
                        }
                        for unit in chapter["units"]
                    ],
                }
                for chapter in state.chapters
            ],
            "bookbench": {
                "snapshot_id": state.snapshot_id,
                "snapshot_hash": state.snapshot_hash,
            },
            "editorial": {"material_waived_count": state.editorial_waived_count},
            "canonical_content_hash": canonical_content_hash,
        }

    def create_master(self, book_id: str, *, human_actor: str) -> LiteraryMasterView:
        actor = human_actor.strip()
        if not actor:
            raise LiteraryMasterGateError(
                "Literary Master creation requires an explicit human actor"
            )
        engine = self._engine(book_id)
        try:
            with engine.begin() as connection:
                state, blockers = self._collect_state(connection, book_id)
                if state is None or blockers:
                    details = "; ".join(f"{item.code}: {item.detail}" for item in blockers)
                    raise LiteraryMasterGateError(f"release gate failed: {details}")
                canonical_bytes = self._canonical_manuscript(state)
                canonical_hash = _sha256_bytes(canonical_bytes)
                manifest = self._manifest(state, canonical_hash)
                manifest_json = canonical_json(cast(Any, manifest))
                manifest_hash = _sha256_bytes(manifest_json.encode("utf-8"))
                master_id = manifest_hash[:32]
                existing = (
                    connection.execute(
                        text(
                            "SELECT * FROM literary_masters WHERE book_id=:book_id "
                            "AND manifest_hash=:manifest_hash"
                        ),
                        {"book_id": book_id, "manifest_hash": manifest_hash},
                    )
                    .mappings()
                    .one_or_none()
                )
                if existing is None:
                    now = utc_now()
                    connection.execute(
                        text(
                            "INSERT INTO literary_masters("
                            "master_id,book_id,manifest_version,manifest_json,manifest_hash,book_title,"
                            "book_contract_revision_id,book_contract_revision_hash,"
                            "architecture_revision_id,architecture_revision_hash,ordered_manifest_json,"
                            "canonical_content_hash,release_gate_json,human_actor,created_at,status) VALUES "
                            "(:master_id,:book_id,:manifest_version,:manifest_json,:manifest_hash,:book_title,"
                            ":book_contract_revision_id,:book_contract_revision_hash,"
                            ":architecture_revision_id,:architecture_revision_hash,:ordered_manifest_json,"
                            ":canonical_content_hash,:release_gate_json,:human_actor,:created_at,'LOCKED')"
                        ),
                        {
                            "master_id": master_id,
                            "book_id": book_id,
                            "manifest_version": self.MANIFEST_VERSION,
                            "manifest_json": manifest_json,
                            "manifest_hash": manifest_hash,
                            "book_title": state.title,
                            "book_contract_revision_id": state.book_contract.revision_id,
                            "book_contract_revision_hash": state.book_contract.revision_hash,
                            "architecture_revision_id": state.architecture.revision_id,
                            "architecture_revision_hash": state.architecture.revision_hash,
                            "ordered_manifest_json": canonical_json(
                                cast(Any, {"chapters": manifest["chapters"]})
                            ),
                            "canonical_content_hash": canonical_hash,
                            "release_gate_json": canonical_json(
                                cast(
                                    Any,
                                    {
                                        "bookbench_snapshot_id": state.snapshot_id,
                                        "bookbench_snapshot_hash": state.snapshot_hash,
                                        "material_waived_count": state.editorial_waived_count,
                                        "blockers": [],
                                    },
                                )
                            ),
                            "human_actor": actor,
                            "created_at": now,
                        },
                    )
                row = (
                    connection.execute(
                        text("SELECT * FROM literary_masters WHERE master_id=:master_id"),
                        {"master_id": master_id},
                    )
                    .mappings()
                    .one()
                )
            return self._master_view(row)
        finally:
            engine.dispose()

    @staticmethod
    def _master_view(row: Any) -> LiteraryMasterView:
        return LiteraryMasterView(
            master_id=str(row["master_id"]),
            book_id=str(row["book_id"]),
            manifest_version=str(row["manifest_version"]),
            manifest_hash=str(row["manifest_hash"]),
            canonical_content_hash=str(row["canonical_content_hash"]),
            book_title=str(row["book_title"]),
            human_actor=str(row["human_actor"]),
            created_at=str(row["created_at"]),
            status=str(row["status"]),
            manifest=cast(dict[str, Any], json.loads(str(row["manifest_json"]))),
        )

    def get_master(self, book_id: str, master_id: str) -> LiteraryMasterView:
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                row = (
                    connection.execute(
                        text(
                            "SELECT * FROM literary_masters WHERE book_id=:book_id "
                            "AND master_id=:master_id"
                        ),
                        {"book_id": book_id, "master_id": master_id},
                    )
                    .mappings()
                    .one_or_none()
                )
            if row is None:
                raise LiteraryMasterNotFound(f"Literary Master not found: {master_id}")
            return self._master_view(row)
        finally:
            engine.dispose()

    def list_masters(self, book_id: str) -> list[LiteraryMasterView]:
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                rows = list(
                    connection.execute(
                        text(
                            "SELECT * FROM literary_masters WHERE book_id=:book_id "
                            "ORDER BY created_at,master_id"
                        ),
                        {"book_id": book_id},
                    ).mappings()
                )
            return [self._master_view(row) for row in rows]
        finally:
            engine.dispose()

    def _canonical_bytes_from_master(self, master: LiteraryMasterView) -> bytes:
        pieces: list[str] = [f"# {master.book_title}\n"]
        engine = self._engine(master.book_id)
        try:
            with engine.connect() as connection:
                for chapter in cast(list[dict[str, Any]], master.manifest["chapters"]):
                    pieces.append(f"\n## {chapter['ordinal']}. {chapter['title']}\n")
                    for unit in cast(list[dict[str, Any]], chapter["units"]):
                        row = (
                            connection.execute(
                                text(
                                    "SELECT content_json,content_hash FROM revisions "
                                    "WHERE revision_id=:revision_id"
                                ),
                                {"revision_id": unit["revision_id"]},
                            )
                            .mappings()
                            .one_or_none()
                        )
                        if row is None or str(row["content_hash"]) != str(unit["revision_hash"]):
                            raise LiteraryMasterError(
                                "master revision is unavailable or hash-mismatched"
                            )
                        content = cast(dict[str, Any], json.loads(str(row["content_json"])))
                        text_value = content.get("text")
                        if not isinstance(text_value, str):
                            raise LiteraryMasterError("master manuscript revision has no text")
                        pieces.append("\n")
                        pieces.append(text_value)
                        pieces.append("\n")
        finally:
            engine.dispose()
        value = "".join(pieces).replace("\r\n", "\n").replace("\r", "\n")
        if not value.endswith("\n"):
            value += "\n"
        output = value.encode("utf-8")
        if _sha256_bytes(output) != master.canonical_content_hash:
            raise LiteraryMasterError("rebuild does not match Literary Master canonical hash")
        return output

    def _record_export(
        self,
        book_id: str,
        master_id: str,
        *,
        format_name: str,
        relative_path: str,
        payload: bytes,
    ) -> LiteraryMasterExportView:
        engine = self._engine(book_id)
        try:
            digest = _sha256_bytes(payload)
            export_id = _sha256_bytes(f"{master_id}|{format_name}|{digest}".encode("utf-8"))[:32]
            now = utc_now()
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT OR IGNORE INTO literary_master_exports("
                        "export_id,master_id,format,content_hash,byte_length,relative_path,created_at) "
                        "VALUES (:export_id,:master_id,:format,:content_hash,:byte_length,:relative_path,:created_at)"
                    ),
                    {
                        "export_id": export_id,
                        "master_id": master_id,
                        "format": format_name,
                        "content_hash": digest,
                        "byte_length": len(payload),
                        "relative_path": relative_path,
                        "created_at": now,
                    },
                )
                row = (
                    connection.execute(
                        text(
                            "SELECT * FROM literary_master_exports "
                            "WHERE master_id=:master_id AND format=:format"
                        ),
                        {"master_id": master_id, "format": format_name},
                    )
                    .mappings()
                    .one()
                )
            return LiteraryMasterExportView(**dict(row))
        finally:
            engine.dispose()

    def export_markdown(self, book_id: str, master_id: str) -> LiteraryMasterExportView:
        master = self.get_master(book_id, master_id)
        payload = self._canonical_bytes_from_master(master)
        relative = f"exports/{master.master_id}/manuscript.md"
        path = self._projects.projects_dir / book_id / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        if _sha256_bytes(path.read_bytes()) != master.canonical_content_hash:
            raise LiteraryMasterError("Markdown export checksum verification failed")
        return self._record_export(
            book_id,
            master_id,
            format_name="MARKDOWN",
            relative_path=relative,
            payload=payload,
        )

    def audiobook_handoff(self, book_id: str, master_id: str) -> LiteraryMasterExportView:
        master = self.get_master(book_id, master_id)
        markdown = self.export_markdown(book_id, master_id)
        handoff = {
            "schema_version": self.HANDOFF_VERSION,
            "book_os_book_id": book_id,
            "literary_master_id": master.master_id,
            "title": master.book_title,
            "canonical_manuscript_hash": master.canonical_content_hash,
            "markdown_export": {
                "relative_path": markdown.relative_path,
                "content_hash": markdown.content_hash,
            },
            "chapters": [
                {
                    "chapter_id": chapter["chapter_id"],
                    "ordinal": chapter["ordinal"],
                    "title": chapter["title"],
                    "units": [
                        {
                            "unit_id": unit["unit_id"],
                            "ordinal": unit["ordinal"],
                            "revision_id": unit["revision_id"],
                            "revision_hash": unit["revision_hash"],
                        }
                        for unit in chapter["units"]
                    ],
                }
                for chapter in cast(list[dict[str, Any]], master.manifest["chapters"])
            ],
        }
        payload = _canonical_bytes(handoff) + b"\n"
        relative = f"exports/{master.master_id}/audiobook-handoff.json"
        path = self._projects.projects_dir / book_id / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        return self._record_export(
            book_id,
            master_id,
            format_name="AUDIOBOOK_HANDOFF_JSON",
            relative_path=relative,
            payload=payload,
        )
