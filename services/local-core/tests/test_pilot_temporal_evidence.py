from __future__ import annotations

from pathlib import Path

from sqlalchemy import text

from book_os_core.authority import AuthorityService
from book_os_core.bookbench_registry import registry_hash
from book_os_core.db import create_database
from book_os_core.pilot import PilotService
from book_os_core.projects import NewBookRequest, ProjectService


def _project_with_revision_refs(data_dir: Path) -> tuple[str, str, str, str, str]:
    project = ProjectService(data_dir).create_project(
        NewBookRequest(working_title="Temporal Pilot Book", primary_subtype="Strategy")
    )
    database = data_dir / "projects" / project.book_id / "project.sqlite"
    engine = create_database(database)
    authority = AuthorityService(engine)
    book_contract = authority.register_entity(
        entity_type="book.contract",
        payload={"central_thesis": "Synthetic temporal test"},
        schema_name="book.contract.v0.1",
        schema_version="1",
        actor="Owner",
        initial_status="APPROVED",
    )
    architecture = authority.register_entity(
        entity_type="book.architecture",
        payload={"parts": []},
        schema_name="book.architecture.v0.1",
        schema_version="1",
        actor="Owner",
        initial_status="APPROVED",
    )
    engine.dispose()
    return (
        project.book_id,
        book_contract.revision_id,
        book_contract.revision_hash,
        architecture.revision_id,
        architecture.revision_hash,
    )


def _insert_master(
    data_dir: Path,
    book_id: str,
    book_contract_revision_id: str,
    book_contract_revision_hash: str,
    architecture_revision_id: str,
    architecture_revision_hash: str,
    *,
    master_id: str,
    created_at: str,
) -> None:
    database = data_dir / "projects" / book_id / "project.sqlite"
    engine = create_database(database)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO literary_masters("
                    "master_id,book_id,manifest_version,manifest_json,manifest_hash,book_title,"
                    "book_contract_revision_id,book_contract_revision_hash,architecture_revision_id,"
                    "architecture_revision_hash,ordered_manifest_json,canonical_content_hash,"
                    "release_gate_json,human_actor,created_at,status) VALUES "
                    "(:master_id,:book_id,'literary-master.v1','{}',:manifest_hash,'Temporal Pilot Book',"
                    ":book_contract_revision_id,:book_contract_revision_hash,:architecture_revision_id,"
                    ":architecture_revision_hash,'{}',:content_hash,'{}','Owner',:created_at,'LOCKED')"
                ),
                {
                    "master_id": master_id,
                    "book_id": book_id,
                    "manifest_hash": (master_id[0] * 64),
                    "book_contract_revision_id": book_contract_revision_id,
                    "book_contract_revision_hash": book_contract_revision_hash,
                    "architecture_revision_id": architecture_revision_id,
                    "architecture_revision_hash": architecture_revision_hash,
                    "content_hash": (master_id[-1] * 64),
                    "created_at": created_at,
                },
            )
    finally:
        engine.dispose()


def _insert_snapshot(data_dir: Path, book_id: str, *, snapshot_id: str, created_at: str) -> None:
    database = data_dir / "projects" / book_id / "project.sqlite"
    engine = create_database(database)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO evaluation_snapshots("
                    "snapshot_id,book_id,scope,snapshot_json,snapshot_hash,created_at) VALUES "
                    "(:snapshot_id,:book_id,'BOOK',:snapshot_json,:snapshot_hash,:created_at)"
                ),
                {
                    "snapshot_id": snapshot_id,
                    "book_id": book_id,
                    "snapshot_json": '{"registry_hash":"' + registry_hash() + '"}',
                    "snapshot_hash": snapshot_id[0] * 64,
                    "created_at": created_at,
                },
            )
    finally:
        engine.dispose()


def test_preexisting_master_and_bookbench_snapshot_do_not_satisfy_new_pilot(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    (
        book_id,
        book_contract_revision_id,
        book_contract_revision_hash,
        architecture_revision_id,
        architecture_revision_hash,
    ) = _project_with_revision_refs(data_dir)

    _insert_master(
        data_dir,
        book_id,
        book_contract_revision_id,
        book_contract_revision_hash,
        architecture_revision_id,
        architecture_revision_hash,
        master_id="a" * 32,
        created_at="2000-01-01T00:00:00.000000Z",
    )
    _insert_snapshot(
        data_dir,
        book_id,
        snapshot_id="b" * 26,
        created_at="2000-01-01T00:00:00.000000Z",
    )

    service = PilotService(data_dir)
    pilot = service.start(book_id, human_actor="Elena")
    summary = service.summary(book_id, pilot.pilot_id)

    assert summary.latest_literary_master_id is None
    assert summary.latest_bookbench_snapshot_id is None
    assert "LITERARY_MASTER_MISSING" in summary.go_no_go.blockers
    assert "BOOKBENCH_SNAPSHOT_MISSING" in summary.go_no_go.blockers


def test_post_start_master_and_bookbench_snapshot_are_visible_to_pilot(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    (
        book_id,
        book_contract_revision_id,
        book_contract_revision_hash,
        architecture_revision_id,
        architecture_revision_hash,
    ) = _project_with_revision_refs(data_dir)
    service = PilotService(data_dir)
    pilot = service.start(book_id, human_actor="Elena")

    _insert_master(
        data_dir,
        book_id,
        book_contract_revision_id,
        book_contract_revision_hash,
        architecture_revision_id,
        architecture_revision_hash,
        master_id="c" * 32,
        created_at="9999-01-01T00:00:00.000000Z",
    )
    _insert_snapshot(
        data_dir,
        book_id,
        snapshot_id="d" * 26,
        created_at="9999-01-01T00:00:00.000000Z",
    )

    summary = service.summary(book_id, pilot.pilot_id)
    assert summary.latest_literary_master_id == "c" * 32
    assert summary.latest_bookbench_snapshot_id == "d" * 26
    assert "BOOKBENCH_MASTER_MISMATCH" in summary.go_no_go.blockers
