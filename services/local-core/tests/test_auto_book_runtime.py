from pathlib import Path

import pytest
from sqlalchemy import text

from book_os_core.auto_book_runtime import (
    AUTO_BOOK_STAGES,
    AutoBookAttachment,
    AutoBookBudgetError,
    AutoBookIntent,
    AutoBookLeaseError,
    AutoBookOutputSelection,
    AutoBookRuntimeError,
    AutoBookStage,
    DurableAutoBookRuntime,
)
from book_os_core.db import create_database
from book_os_core.projects import NewBookRequest, ProjectService


def project(tmp_path: Path) -> str:
    return (
        ProjectService(tmp_path)
        .create_project(
            NewBookRequest(working_title="Устойчивая Auto-книга", primary_subtype="Strategy")
        )
        .book_id
    )


def intent(**overrides: object) -> AutoBookIntent:
    values: dict[str, object] = {
        "idea": "Показать читателю полный проверяемый цикл создания сильной книги.",
        "author_name": "Елена Дым",
        "outputs": AutoBookOutputSelection(
            full_manuscript_docx=True,
            reading_pdf=True,
            voice_text_txt=True,
        ),
        "max_cost_usd_per_request": 1.0,
        "max_total_cost_usd": 10.0,
        "max_requests": 20,
    }
    values.update(overrides)
    return AutoBookIntent.model_validate(values)


def test_runtime_persists_authorization_and_fourteen_stage_plan(tmp_path: Path) -> None:
    book_id = project(tmp_path)
    runtime = DurableAutoBookRuntime(tmp_path)
    run = runtime.create_run(book_id, intent())

    assert run.status == "QUEUED"
    assert run.current_stage == AutoBookStage.DEFINITION
    assert len(AUTO_BOOK_STAGES) == 14
    assert run.progress_total == 17
    assert run.reserved_cost_usd == 2.5
    assert run.confirmed_cost_usd == 0
    assert run.unknown_cost_usd == 0

    restarted = DurableAutoBookRuntime(tmp_path).latest(book_id)
    assert restarted == run

    engine = create_database(tmp_path / "projects" / book_id / "project.sqlite")
    try:
        with engine.connect() as connection:
            authorization = (
                connection.execute(
                    text(
                        "SELECT authorized_by_kind,scope_json FROM auto_book_authorizations "
                        "WHERE run_id=:run_id"
                    ),
                    {"run_id": run.run_id},
                )
                .mappings()
                .one()
            )
    finally:
        engine.dispose()
    assert authorization["authorized_by_kind"] == "OWNER"
    assert "MASTER_AND_EXPORTS" in authorization["scope_json"]


def test_runtime_lease_prevents_two_workers_and_recovers_after_release(tmp_path: Path) -> None:
    book_id = project(tmp_path)
    runtime = DurableAutoBookRuntime(tmp_path)
    run = runtime.create_run(book_id, intent())

    assert runtime.claim(book_id, run.run_id, "worker-a").status == "RUNNING"
    with pytest.raises(AutoBookLeaseError):
        runtime.claim(book_id, run.run_id, "worker-b")
    runtime.release(book_id, run.run_id, "worker-a")
    assert runtime.claim(book_id, run.run_id, "worker-b").status == "RUNNING"


def test_runtime_is_idempotent_and_separates_reserved_confirmed_unknown_cost(
    tmp_path: Path,
) -> None:
    book_id = project(tmp_path)
    runtime = DurableAutoBookRuntime(tmp_path)
    run = runtime.create_run(book_id, intent())

    first = runtime.ensure_operation(
        book_id,
        run.run_id,
        ordinal=1,
        stage=AutoBookStage.RESEARCH,
        operation="research-map",
        input_payload={"question": "Что нужно проверить?"},
        provider="openai",
        model="gpt-5.6-sol",
        estimated_cost_usd=0.4,
    )
    same = runtime.ensure_operation(
        book_id,
        run.run_id,
        ordinal=1,
        stage=AutoBookStage.RESEARCH,
        operation="research-map",
        input_payload={"question": "Что нужно проверить?"},
        provider="openai",
        model="gpt-5.6-sol",
        estimated_cost_usd=0.4,
    )
    assert same.operation_id == first.operation_id

    runtime.reserve(book_id, run.run_id, first.operation_id, 0.4)
    completed = runtime.complete_operation(
        book_id,
        run.run_id,
        first.operation_id,
        output={"source_ids": ["source-1"]},
        confirmed_cost_usd=0.12,
        provider_run_id="resp_1",
    )
    assert completed.confirmed_cost_usd == pytest.approx(0.12)
    assert completed.reserved_cost_usd == pytest.approx(2.5)

    second = runtime.ensure_operation(
        book_id,
        run.run_id,
        ordinal=2,
        stage=AutoBookStage.WRITING,
        operation="chapter-1",
        input_payload={"chapter": 1},
        provider="openai",
        model="gpt-6-astra",
        reasoning_effort="high",
    )
    runtime.reserve(book_id, run.run_id, second.operation_id, 0.8)
    unknown = runtime.mark_unknown(
        book_id,
        run.run_id,
        second.operation_id,
        provider_run_id="resp_unknown",
    )
    assert unknown.status == "UNKNOWN_OUTCOME"
    assert unknown.unknown_cost_usd == pytest.approx(0.8)
    with pytest.raises(AutoBookRuntimeError, match="unknown paid outcome"):
        runtime.resume(book_id, run.run_id)


def test_budget_is_atomic_and_does_not_spend_release_reserve(tmp_path: Path) -> None:
    book_id = project(tmp_path)
    runtime = DurableAutoBookRuntime(tmp_path)
    run = runtime.create_run(
        book_id,
        intent(max_total_cost_usd=4.0, max_cost_usd_per_request=2.0),
    )
    operation = runtime.ensure_operation(
        book_id,
        run.run_id,
        ordinal=1,
        stage=AutoBookStage.WRITING,
        operation="oversized-draft",
        input_payload={"chapter": 1},
    )
    with pytest.raises(AutoBookBudgetError):
        runtime.reserve(book_id, run.run_id, operation.operation_id, 3.1)
    assert runtime.get(book_id, run.run_id).status == "BUDGET_REACHED"


def test_attachment_role_never_silently_guesses_legacy_intent() -> None:
    with pytest.raises(ValueError, match="explicit intent"):
        AutoBookAttachment(path="old-book.docx", role="LEGACY_BOOK")
    attachment = AutoBookAttachment(
        path="old-book.docx",
        role="LEGACY_BOOK",
        intent="WRITE_FROM_ZERO",
    )
    assert attachment.intent == "WRITE_FROM_ZERO"
