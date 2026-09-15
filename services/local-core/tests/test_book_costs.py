from pathlib import Path

import pytest

from book_os_core.auto_book_runtime import (
    AutoBookIntent,
    AutoBookStage,
    DurableAutoBookRuntime,
)
from book_os_core.book_costs import BookCostService
from book_os_core.projects import NewBookRequest, ProjectService


def test_book_cost_read_model_uses_ledger_and_never_calls_budget_a_forecast(
    tmp_path: Path,
) -> None:
    book_id = (
        ProjectService(tmp_path)
        .create_project(NewBookRequest(working_title="Книга", primary_subtype="Strategy"))
        .book_id
    )
    runtime = DurableAutoBookRuntime(tmp_path)
    run = runtime.create_run(
        book_id,
        AutoBookIntent(
            idea="Проверяемая книга",
            author_name="Автор",
            max_total_cost_usd=25,
            max_cost_usd_per_request=1,
        ),
    )
    research = runtime.ensure_operation(
        book_id,
        run.run_id,
        ordinal=1,
        stage=AutoBookStage.RESEARCH,
        operation="research-map",
        input_payload={"topic": "evidence"},
        provider="openai",
        model="gpt-5.6-sol",
        estimated_cost_usd=0.5,
    )
    runtime.reserve(book_id, run.run_id, research.operation_id, 0.5)
    runtime.complete_operation(
        book_id,
        run.run_id,
        research.operation_id,
        output={"evidence": []},
        confirmed_cost_usd=0.18,
        provider_run_id="provider-1",
    )
    writing = runtime.ensure_operation(
        book_id,
        run.run_id,
        ordinal=2,
        stage=AutoBookStage.WRITING,
        operation="chapter-1",
        input_payload={"chapter": 1},
        provider="openai",
        model="gpt-6-astra",
        reasoning_effort="high",
        estimated_cost_usd=0.8,
    )
    runtime.reserve(book_id, run.run_id, writing.operation_id, 0.8)
    runtime.mark_unknown(book_id, run.run_id, writing.operation_id, provider_run_id="provider-2")

    result = BookCostService(tmp_path).get(book_id)

    assert result is not None
    assert result.confirmed_cost_usd == pytest.approx(0.18)
    assert result.unknown_cost_usd == pytest.approx(0.8)
    assert result.max_budget_usd == 25
    assert result.forecast_status == "INSUFFICIENT_DATA"
    assert result.forecast_total_low_usd is None
    assert result.forecast_total_high_usd is None
    assert result.max_budget_usd != result.estimated_operations_cost_usd
    assert [item.category for item in result.categories] == ["Research", "Написание"]
    assert result.categories[0].confirmed_cost_usd == pytest.approx(0.18)
    assert result.categories[0].reserved_cost_usd == 0
    assert result.categories[1].unknown_cost_usd == pytest.approx(0.8)
    assert len(result.operations) == 2
