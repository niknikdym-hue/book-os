import json
from pathlib import Path

import pytest
from fastapi import FastAPI, Header, HTTPException
from fastapi.testclient import TestClient

from book_os_core.auto_book_runtime import AutoBookIntent, AutoBookStage, DurableAutoBookRuntime
from book_os_core.book_context import ProfileCreateRequest, ProfileRegistry
from book_os_core.model_gateway import DeterministicFakeAdapter, ModelGateway
from book_os_core.series_costs import SeriesCostLedger
from book_os_core.series_studio_api import build_series_studio_router
from book_os_core.series_workspace import (
    SeriesBookCreateRequest,
    SeriesCreateRequest,
    SeriesWorkspaceService,
)


def build_series(tmp_path: Path) -> tuple[str, str]:
    profiles = ProfileRegistry(tmp_path)
    author = profiles.create_profile(
        ProfileCreateRequest(kind="AUTHOR", content={"author_name": "Елена Дым"})
    )
    author = profiles.approve_profile(author.profile_id)
    workspaces = SeriesWorkspaceService(tmp_path)
    series = workspaces.create_series(
        SeriesCreateRequest(
            series_name="Секреты продвижения услуг",
            author_profile_id=author.profile_id,
        )
    )
    book = workspaces.add_book(
        series.profile_id,
        SeriesBookCreateRequest(
            title="Как продавать услуги",
            ordinal=1,
            unique_idea="Система продажи нематериальной услуги",
            reader_problem="Покупатель не может оценить результат заранее",
            reader_result="Управляемая система доверия и продажи",
            unique_mechanism="Проектирование доказательств до покупки",
        ),
    )
    return series.profile_id, book.book_id


def test_series_costs_keep_series_work_separate_and_aggregate_durable_book_cost(
    tmp_path: Path,
) -> None:
    series_id, book_id = build_series(tmp_path)
    ledger = SeriesCostLedger(tmp_path)
    entry = ledger.record_series_creation(
        series_profile_ids=[series_id],
        provider="openai",
        model="gpt-6-astra",
        reasoning_effort="high",
        provider_run_id="provider-series-1",
        usage={
            "cost_guard": {
                "preflight_upper_bound_usd": 1.5,
                "estimated_actual_cost_usd": 0.42,
            }
        },
    )
    project_dir = tmp_path / "projects" / book_id
    (project_dir / "auto-book-run.json").write_text(
        json.dumps(
            {
                "confirmed_cost_usd": 2.4,
                "estimated_cost_usd": 5.75,
                "reserved_cost_usd": 0.5,
                "unknown_cost_usd": 0.25,
            }
        ),
        encoding="utf-8",
    )

    result = ledger.get(series_id)

    assert entry.confirmed_cost_usd == 0
    assert entry.estimated_cost_usd == pytest.approx(0.42)
    assert result.series_confirmed_cost_usd == 0
    assert result.books_confirmed_cost_usd == pytest.approx(2.4)
    assert result.total_confirmed_cost_usd == pytest.approx(2.4)
    assert result.total_estimated_cost_usd == pytest.approx(0.42)
    assert result.total_reserved_cost_usd == pytest.approx(0.5)
    assert result.total_unknown_cost_usd == pytest.approx(0.25)
    assert result.books[0].title == "Как продавать услуги"


def test_series_cost_entry_is_idempotent_and_unreconciled_cost_stays_unknown(
    tmp_path: Path,
) -> None:
    series_id, _ = build_series(tmp_path)
    ledger = SeriesCostLedger(tmp_path)
    request = {
        "series_profile_ids": [series_id],
        "provider": "openai",
        "model": "gpt-6-astra",
        "reasoning_effort": "medium",
        "provider_run_id": "provider-series-2",
        "usage": {"cost_guard": {"preflight_upper_bound_usd": 0.9}},
    }

    first = ledger.record_series_creation(**request)
    second = ledger.record_series_creation(**request)
    result = ledger.get(series_id)

    assert first.entry_id == second.entry_id
    assert result.series_confirmed_cost_usd == 0
    assert result.total_unknown_cost_usd == pytest.approx(0.9)
    assert len(result.operations) == 1


def test_series_cost_read_model_requires_local_core_authentication(tmp_path: Path) -> None:
    series_id, _ = build_series(tmp_path)

    def require_token(authorization: str | None = Header(default=None)) -> None:
        if authorization != "Bearer series-cost-token":
            raise HTTPException(status_code=401, detail="unauthorized")

    app = FastAPI()
    app.include_router(
        build_series_studio_router(
            tmp_path,
            require_token,
            ModelGateway({"openai": DeterministicFakeAdapter()}),
        )
    )
    client = TestClient(app)

    assert client.get(f"/api/series/{series_id}/costs").status_code == 401

    response = client.get(
        f"/api/series/{series_id}/costs",
        headers={"Authorization": "Bearer series-cost-token"},
    )
    assert response.status_code == 200
    assert response.json()["series_profile_id"] == series_id


def test_series_forecast_requires_a_completed_comparable_book(tmp_path: Path) -> None:
    profiles = ProfileRegistry(tmp_path)
    author = profiles.create_profile(
        ProfileCreateRequest(kind="AUTHOR", content={"author_name": "Автор"})
    )
    author = profiles.approve_profile(author.profile_id)
    series = profiles.create_profile(
        ProfileCreateRequest(
            kind="SERIES",
            content={
                "series_name": "Практическая серия",
                "author_profile_id": author.profile_id,
                "purpose_positioning": "Самостоятельные книги",
                "planned_books": ["Первая книга", "Будущая книга"],
            },
        )
    )
    series = profiles.approve_profile(series.profile_id)
    workspace = SeriesWorkspaceService(tmp_path)
    first = workspace.add_book(
        series.profile_id,
        SeriesBookCreateRequest(
            title="Первая книга",
            ordinal=1,
            unique_idea="Первый механизм",
            reader_problem="Первая задача",
            reader_result="Первый результат",
            unique_mechanism="Первое решение",
        ),
    )
    ledger = SeriesCostLedger(tmp_path)

    before = ledger.get(series.profile_id)
    assert before.production_forecast_status == "INSUFFICIENT_DATA"
    assert before.production_forecast_low_usd is None
    assert before.future_books[0].forecast_total_low_usd is None

    runtime = DurableAutoBookRuntime(tmp_path)
    run = runtime.create_run(
        first.book_id,
        AutoBookIntent(idea="Первая книга серии", author_name="Автор", max_total_cost_usd=20),
    )
    operation = runtime.ensure_operation(
        first.book_id,
        run.run_id,
        ordinal=1,
        stage=AutoBookStage.WRITING,
        operation="book-production",
        input_payload={"book": 1},
        estimated_cost_usd=12,
    )
    runtime.reserve(first.book_id, run.run_id, operation.operation_id, 12)
    runtime.complete_operation(
        first.book_id,
        run.run_id,
        operation.operation_id,
        output={"master": "ready"},
        confirmed_cost_usd=10,
    )
    runtime.set_stage(
        first.book_id,
        run.run_id,
        AutoBookStage.MASTER_AND_EXPORTS,
        message="ready",
        status="PACKAGE_READY",
    )

    after = ledger.get(series.profile_id)
    assert after.production_forecast_status == "COMPARABLE_COMPLETED_BOOKS"
    assert after.production_forecast_low_usd == pytest.approx(18.5)
    assert after.production_forecast_high_usd == pytest.approx(21.5)
    assert after.future_books[0].forecast_total_low_usd == pytest.approx(8.5)
    assert after.future_books[0].forecast_total_high_usd == pytest.approx(11.5)
