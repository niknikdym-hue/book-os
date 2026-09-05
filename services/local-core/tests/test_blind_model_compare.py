from __future__ import annotations

import json
from pathlib import Path

import pytest

from book_os_core.blind_model_compare import (
    AstraAwareOpenAIResponsesAdapter,
    BlindBookContractCompareRequest,
    BlindBookContractComparisonService,
    BlindBookContractSelectRequest,
    BlindComparisonGateError,
)
from book_os_core.model_gateway import ModelAdapterResult, ModelGateway, ModelTaskRequest
from book_os_core.projects import NewBookRequest, ProjectService
from book_os_core.prompts import PromptTemplate


class DifferentiatedBookContractAdapter:
    provider_name = "openai"

    def __init__(self) -> None:
        self.requests: list[ModelTaskRequest] = []

    def generate(
        self, request: ModelTaskRequest, prompt: PromptTemplate
    ) -> ModelAdapterResult:
        self.requests.append(request.model_copy(deep=True))
        identity = "ASTRA" if request.model == "gpt-6-astra" else "SOL"
        return ModelAdapterResult(
            provider_run_id=f"fake-{identity.casefold()}",
            output={
                "reader": "Владелец растущей компании",
                "reader_problem": "Решения постоянно возвращаются к владельцу",
                "central_promise": f"Понять механизм зависимости {identity}",
                "central_thesis": f"Тезис кандидата {identity}",
                "unique_angle": "Рассматривать зависимость как архитектуру прав решений",
                "reader_trajectory": "От ручного контроля к явной системе решений",
                "explicit_exclusions": ["Не мотивационная книга"],
                "evidence_policy": "Материальные утверждения проверяются по источникам",
                "voice_genre_constraints": "Точный деловой нон-фикшен",
                "readiness_criteria": ["Читатель умеет диагностировать зависимость"],
            },
            usage={"input_tokens": 100, "output_tokens": 200},
        )


def create_project(data_dir: Path) -> str:
    project = ProjectService(data_dir).create_project(
        NewBookRequest(
            working_title="Blind Pilot",
            primary_subtype="Strategy",
        )
    )
    return project.book_id


def test_astra_has_current_fail_closed_price_table() -> None:
    assert AstraAwareOpenAIResponsesAdapter._pricing("gpt-6-astra") == (10.0, 50.0)
    assert AstraAwareOpenAIResponsesAdapter._PRICING_SOURCE_DATE == "2026-09-06"


def test_blind_compare_keeps_models_hidden_until_human_selection(tmp_path: Path) -> None:
    book_id = create_project(tmp_path)
    adapter = DifferentiatedBookContractAdapter()
    service = BlindBookContractComparisonService(
        tmp_path,
        ModelGateway({"openai": adapter}),
    )

    comparison = service.compare(
        book_id,
        BlindBookContractCompareRequest(
            idea="Почему стратегия компании разваливается на уровне ежедневных решений",
            reader_hint="Владелец бизнеса",
            max_cost_usd_per_request=0.50,
        ),
    )

    assert ProjectService(tmp_path).get_project(book_id).book_contract is None
    assert comparison.models_revealed is False
    serialized = json.dumps(comparison.model_dump(mode="json"), ensure_ascii=False)
    assert "gpt-6-astra" not in serialized
    assert "gpt-5.6-sol" not in serialized
    assert {comparison.candidate_a.label, comparison.candidate_b.label} == {"A", "B"}
    assert adapter.requests[0].model == "gpt-6-astra"
    assert adapter.requests[1].model == "gpt-5.6-sol"
    assert adapter.requests[0].authoritative_context == adapter.requests[1].authoritative_context
    assert adapter.requests[0].prompt_id == adapter.requests[1].prompt_id
    assert comparison.total_cap_usd == 1.0

    selected_contract = comparison.candidate_a.contract
    selection = service.select(
        book_id,
        comparison.comparison_id,
        BlindBookContractSelectRequest(selected_label="A"),
    )

    assert selection.selected_label == "A"
    assert set(selection.revealed_models.values()) == {"gpt-6-astra", "gpt-5.6-sol"}
    assert selection.project.book_contract is not None
    assert selection.project.book_contract.status == "DRAFT"
    assert (
        selection.project.book_contract.content["central_thesis"]
        == selected_contract.central_thesis
    )

    record_path = (
        tmp_path
        / "projects"
        / book_id
        / "model-comparisons"
        / f"{comparison.comparison_id}.json"
    )
    record = json.loads(record_path.read_text(encoding="utf-8"))
    assert record["selected_label"] == "A"
    assert record["selected_at"]


def test_blind_preference_cannot_be_switched_after_reveal(tmp_path: Path) -> None:
    book_id = create_project(tmp_path)
    service = BlindBookContractComparisonService(
        tmp_path,
        ModelGateway({"openai": DifferentiatedBookContractAdapter()}),
    )
    comparison = service.compare(
        book_id,
        BlindBookContractCompareRequest(idea="Стратегия и ежедневные решения"),
    )
    service.select(
        book_id,
        comparison.comparison_id,
        BlindBookContractSelectRequest(selected_label="A"),
    )

    with pytest.raises(BlindComparisonGateError, match="already recorded"):
        service.select(
            book_id,
            comparison.comparison_id,
            BlindBookContractSelectRequest(selected_label="B"),
        )
