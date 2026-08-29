from __future__ import annotations

import json
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DatabaseError

from book_os_core.authority import AuthorityService, new_ulid
from book_os_core.authority_types import utc_now
from book_os_core.backup import create_backup
from book_os_core.bookbench import BookBenchService
from book_os_core.db import create_database
from book_os_core.literary_master import LiteraryMasterGateError, LiteraryMasterService


def _build_release_fixture(
    data_dir: Path,
    *,
    unit_status: str = "APPROVED",
    bookbench_blocking: bool = False,
    stale_snapshot: bool = False,
) -> str:
    book_id = new_ulid()
    project_dir = data_dir / "projects" / book_id
    project_dir.mkdir(parents=True)
    engine = create_database(project_dir / "project.sqlite")
    authority = AuthorityService(engine)
    now = utc_now()

    book_contract = authority.register_entity(
        entity_type="book.contract",
        payload={"central_thesis": "Thesis"},
        schema_name="book.contract.v0.1",
        schema_version="1",
        actor="Owner",
        initial_status="APPROVED",
    )
    architecture = authority.register_entity(
        entity_type="book.architecture",
        payload={"parts": [{"title": "Part I"}]},
        schema_name="book.architecture.v0.1",
        schema_version="1",
        actor="Owner",
        initial_status="APPROVED",
    )
    chapter_contract = authority.register_entity(
        entity_type="chapter.contract",
        payload={"chapter_purpose": "Purpose"},
        schema_name="chapter.contract.v0.1",
        schema_version="1",
        actor="Owner",
        initial_status="APPROVED",
    )
    manuscript = authority.register_entity(
        entity_type="manuscript.unit",
        payload={"text": "Exact approved manuscript text.", "notes": []},
        schema_name="manuscript.unit.section.v0.1",
        schema_version="1",
        actor="Owner",
        initial_status=unit_status,
    )
    chapter_id = new_ulid()
    unit_id = new_ulid()
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO book_projects("
                "book_id,working_title,mode,domain,primary_subtype,profile_version,workflow_stage,"
                "book_contract_entity_id,architecture_entity_id,created_at,updated_at) VALUES "
                "(:book_id,'Release Test','BOOK_FROM_ZERO','BUSINESS_NONFICTION','Strategy',"
                "'business-nonfiction-v0.1','FINAL REVIEW',:book_contract,:architecture,:now,:now)"
            ),
            {
                "book_id": book_id,
                "book_contract": book_contract.entity_id,
                "architecture": architecture.entity_id,
                "now": now,
            },
        )
        connection.execute(
            text(
                "INSERT INTO chapters("
                "chapter_id,book_id,ordinal,working_title,architecture_role,chapter_contract_entity_id,"
                "workflow_state,created_at,updated_at) VALUES "
                "(:chapter_id,:book_id,1,'Chapter One','Open the argument',:contract,"
                "'CURRENT',:now,:now)"
            ),
            {
                "chapter_id": chapter_id,
                "book_id": book_id,
                "contract": chapter_contract.entity_id,
                "now": now,
            },
        )
        connection.execute(
            text(
                "INSERT INTO manuscript_units("
                "unit_id,book_id,chapter_id,unit_type,ordinal,authority_entity_id,created_at,updated_at) "
                "VALUES (:unit_id,:book_id,:chapter_id,'SECTION',1,:entity_id,:now,:now)"
            ),
            {
                "unit_id": unit_id,
                "book_id": book_id,
                "chapter_id": chapter_id,
                "entity_id": manuscript.entity_id,
                "now": now,
            },
        )

        snapshot_id = new_ulid()
        snapshot_hash = "a" * 64
        connection.execute(
            text(
                "INSERT INTO evaluation_snapshots("
                "snapshot_id,book_id,scope,snapshot_json,snapshot_hash,created_at) VALUES "
                "(:snapshot_id,:book_id,'BOOK','{}',:snapshot_hash,:now)"
            ),
            {
                "snapshot_id": snapshot_id,
                "book_id": book_id,
                "snapshot_hash": snapshot_hash,
                "now": now,
            },
        )
        targets = [
            (
                "BOOK_CONTRACT",
                book_contract.entity_id,
                None,
                None,
                book_contract.revision_id,
                book_contract.revision_hash,
            ),
            (
                "CHAPTER_CONTRACT",
                chapter_contract.entity_id,
                chapter_id,
                None,
                chapter_contract.revision_id,
                chapter_contract.revision_hash,
            ),
        ]
        if not stale_snapshot:
            targets.append(
                (
                    "MANUSCRIPT_UNIT",
                    unit_id,
                    chapter_id,
                    unit_id,
                    manuscript.revision_id,
                    manuscript.revision_hash,
                )
            )
        for ordinal, target in enumerate(targets, start=1):
            target_kind, target_id, target_chapter, target_unit, revision_id, revision_hash = target
            connection.execute(
                text(
                    "INSERT INTO evaluation_snapshot_targets("
                    "snapshot_id,ordinal,target_kind,target_id,chapter_id,unit_id,revision_id,"
                    "revision_hash,content_hash,source_status) VALUES "
                    "(:snapshot_id,:ordinal,:target_kind,:target_id,:chapter_id,:unit_id,"
                    ":revision_id,:revision_hash,:content_hash,'CURRENT')"
                ),
                {
                    "snapshot_id": snapshot_id,
                    "ordinal": ordinal,
                    "target_kind": target_kind,
                    "target_id": target_id,
                    "chapter_id": target_chapter,
                    "unit_id": target_unit,
                    "revision_id": revision_id,
                    "revision_hash": revision_hash,
                    "content_hash": revision_hash,
                },
            )

        evaluation_id = new_ulid()
        connection.execute(
            text(
                "INSERT INTO evaluation_runs("
                "evaluation_id,book_id,snapshot_id,check_id,check_version,registry_hash,dimension,"
                "evaluator_class,evaluator_id,evaluator_version,independence_state,input_hash,"
                "output_json,usage_json,latency_ms,status,created_at,completed_at) VALUES "
                "(:evaluation_id,:book_id,:snapshot_id,'release-test','1',:registry_hash,"
                "'BOOK_CONTRACT_FULFILLMENT','DETERMINISTIC','release-test','1',"
                "'NOT_APPLICABLE',:input_hash,'{}','{}',0,'SUCCEEDED',:now,:now)"
            ),
            {
                "evaluation_id": evaluation_id,
                "book_id": book_id,
                "snapshot_id": snapshot_id,
                "registry_hash": "b" * 64,
                "input_hash": "c" * 64,
                "now": now,
            },
        )
        deterministic_runs = (
            ("deterministic.repetition", "IDEA_REPETITION"),
            ("deterministic.statistics", "THOUGHT_DENSITY"),
            ("deterministic.specificity", "SPECIFICITY_GENERICNESS"),
            ("deterministic.evidence", "EVIDENCE_UNSUPPORTED_CLAIMS"),
            ("deterministic.contract_structure", "CHAPTER_CONTRACT_FULFILLMENT"),
            ("deterministic.ai_prose_pathology", "AI_PROSE_PATHOLOGY"),
            ("deterministic.opening_ending_transition", "OPENING_ENDING_TRANSITION"),
        )
        for check_id, dimension in deterministic_runs:
            connection.execute(
                text(
                    "INSERT INTO evaluation_runs("
                    "evaluation_id,book_id,snapshot_id,check_id,check_version,registry_hash,dimension,"
                    "evaluator_class,evaluator_id,evaluator_version,independence_state,input_hash,"
                    "output_json,usage_json,latency_ms,status,created_at,completed_at) VALUES "
                    "(:evaluation_id,:book_id,:snapshot_id,:check_id,'1.0.0',:registry_hash,:dimension,"
                    "'DETERMINISTIC',:check_id,'1.0.0','NOT_APPLICABLE',:input_hash,"
                    "'{}','{}',0,'SUCCEEDED',:now,:now)"
                ),
                {
                    "evaluation_id": new_ulid(),
                    "book_id": book_id,
                    "snapshot_id": snapshot_id,
                    "check_id": check_id,
                    "registry_hash": "b" * 64,
                    "dimension": dimension,
                    "input_hash": "d" * 64,
                    "now": now,
                },
            )

        if bookbench_blocking:
            connection.execute(
                text(
                    "INSERT INTO evaluation_findings("
                    "finding_id,evaluation_id,dimension,category,target_kind,target_id,chapter_id,"
                    "revision_id,revision_hash,location,evidence_json,severity,confidence,"
                    "recommended_action,created_at) VALUES "
                    "(:finding_id,:evaluation_id,'BOOK_CONTRACT_FULFILLMENT','release-test',"
                    "'BOOK_CONTRACT',:target_id,NULL,:revision_id,:revision_hash,'book','{}',"
                    "'BLOCKING',1.0,'fix before release',:now)"
                ),
                {
                    "finding_id": new_ulid(),
                    "evaluation_id": evaluation_id,
                    "target_id": book_contract.entity_id,
                    "revision_id": book_contract.revision_id,
                    "revision_hash": book_contract.revision_hash,
                    "now": now,
                },
            )
    engine.dispose()
    return book_id


def test_release_gate_rejects_unapproved_manuscript(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    book_id = _build_release_fixture(data_dir, unit_status="DRAFT")
    readiness = LiteraryMasterService(data_dir).readiness(book_id)
    assert readiness.ready is False
    assert "MANUSCRIPT_UNIT_NOT_APPROVED" in {item.code for item in readiness.blockers}


def test_release_gate_rejects_blocking_and_stale_bookbench(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    blocked_book = _build_release_fixture(data_dir, bookbench_blocking=True)
    stale_book = _build_release_fixture(data_dir, stale_snapshot=True)
    blocked = LiteraryMasterService(data_dir).readiness(blocked_book)
    stale = LiteraryMasterService(data_dir).readiness(stale_book)
    assert "BOOKBENCH_BLOCKING" in {item.code for item in blocked.blockers}
    assert "BOOKBENCH_SNAPSHOT_STALE" in {item.code for item in stale.blockers}


def test_master_and_exports_are_deterministic_and_append_only(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    book_id = _build_release_fixture(data_dir)
    service = LiteraryMasterService(data_dir)
    assert service.readiness(book_id).ready is True

    with pytest.raises(LiteraryMasterGateError, match="human actor"):
        service.create_master(book_id, human_actor="")

    first = service.create_master(book_id, human_actor="Elena")
    second = service.create_master(book_id, human_actor="Elena")
    assert first.master_id == second.master_id
    assert first.manifest_hash == second.manifest_hash
    assert first.status == "LOCKED"

    markdown_1 = service.export_markdown(book_id, first.master_id)
    markdown_2 = service.export_markdown(book_id, first.master_id)
    assert markdown_1.export_id == markdown_2.export_id
    assert markdown_1.content_hash == first.canonical_content_hash
    markdown_path = data_dir / "projects" / book_id / markdown_1.relative_path
    assert markdown_path.read_text(encoding="utf-8").startswith("# Release Test\n")

    handoff_1 = service.audiobook_handoff(book_id, first.master_id)
    handoff_2 = service.audiobook_handoff(book_id, first.master_id)
    assert handoff_1.export_id == handoff_2.export_id
    handoff_path = data_dir / "projects" / book_id / handoff_1.relative_path
    handoff = json.loads(handoff_path.read_text(encoding="utf-8"))
    assert handoff["literary_master_id"] == first.master_id
    assert handoff["canonical_manuscript_hash"] == first.canonical_content_hash

    database = data_dir / "projects" / book_id / "project.sqlite"
    engine = create_database(database)
    try:
        with pytest.raises(DatabaseError):
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "UPDATE literary_masters SET book_title='mutated' "
                        "WHERE master_id=:master_id"
                    ),
                    {"master_id": first.master_id},
                )
    finally:
        engine.dispose()

    backup_dir = tmp_path / "backup"
    _, manifest_path = create_backup(database, backup_dir)
    assert json.loads(manifest_path.read_text(encoding="utf-8"))["alembic_revision"] == "0009"


def test_release_gate_requires_full_deterministic_bookbench_suite(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    book_id = _build_release_fixture(data_dir)
    incomplete = BookBenchService(data_dir).create_snapshot(book_id, scope="BOOK")
    readiness = LiteraryMasterService(data_dir).readiness(book_id)
    assert readiness.snapshot_id == incomplete.snapshot_id
    assert readiness.ready is False
    assert "BOOKBENCH_REQUIRED_CHECKS_MISSING" in {item.code for item in readiness.blockers}


def test_material_editorial_waiver_requires_human_state_evidence(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    book_id = _build_release_fixture(data_dir)
    database = data_dir / "projects" / book_id / "project.sqlite"
    engine = create_database(database)
    finding_id = new_ulid()
    now = utc_now()
    try:
        with engine.begin() as connection:
            unit = (
                connection.execute(
                    text(
                        "SELECT mu.unit_id,mu.chapter_id,mu.authority_entity_id,h.revision_id,h.revision_hash "
                        "FROM manuscript_units mu JOIN authority_heads h ON h.entity_id=mu.authority_entity_id "
                        "WHERE mu.book_id=:book_id ORDER BY mu.ordinal LIMIT 1"
                    ),
                    {"book_id": book_id},
                )
                .mappings()
                .one()
            )
            connection.execute(
                text(
                    "INSERT INTO editorial_findings("
                    "finding_id,run_id,book_id,role,category,target_kind,target_entity_id,chapter_id,unit_id,"
                    "base_revision_id,base_revision_hash,diagnosis,why,evidence_json,severity,confidence,"
                    "expected_effect,risks,actor,actor_kind,status,created_at,resolved_at) VALUES "
                    "(:finding_id,NULL,:book_id,'LITERARY_EDITOR','release-waiver','MANUSCRIPT_UNIT',"
                    ":entity_id,:chapter_id,:unit_id,:revision_id,:revision_hash,'diagnosis','why','{}',"
                    "'CRITICAL',1.0,'effect','risk','AI','AI','WAIVED',:now,:now)"
                ),
                {
                    "finding_id": finding_id,
                    "book_id": book_id,
                    "entity_id": unit["authority_entity_id"],
                    "chapter_id": unit["chapter_id"],
                    "unit_id": unit["unit_id"],
                    "revision_id": unit["revision_id"],
                    "revision_hash": unit["revision_hash"],
                    "now": now,
                },
            )
            connection.execute(
                text(
                    "INSERT INTO editorial_finding_state_history("
                    "state_event_id,finding_id,prior_state,new_state,actor,actor_kind,reason,created_at) "
                    "VALUES (:event_id,:finding_id,'OPEN','WAIVED','AI','AI','invalid simulated waiver',:now)"
                ),
                {"event_id": new_ulid(), "finding_id": finding_id, "now": now},
            )
    finally:
        engine.dispose()

    readiness = LiteraryMasterService(data_dir).readiness(book_id)
    assert readiness.ready is False
    assert "EDITORIAL_WAIVER_NOT_HUMAN" in {item.code for item in readiness.blockers}
