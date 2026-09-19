from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from .auto_book_runtime import AutoBookOperationView, AutoBookStage, DurableAutoBookRuntime


class BookCostCategory(BaseModel):
    category: str
    confirmed_cost_usd: float
    estimated_cost_usd: float
    reserved_cost_usd: float
    unknown_cost_usd: float


class BookCostOperation(BaseModel):
    operation_id: str
    operation: str
    user_stage: str
    status: str
    confirmed_cost_usd: float
    estimated_cost_usd: float
    reserved_cost_usd: float
    unknown_cost_usd: float
    provider: str | None
    model: str | None
    reasoning_effort: str | None
    created_at: str


class BookCostView(BaseModel):
    book_id: str
    run_id: str
    confirmed_cost_usd: float
    estimated_operations_cost_usd: float
    reserved_cost_usd: float
    unknown_cost_usd: float
    max_budget_usd: float
    forecast_remaining_low_usd: float | None = None
    forecast_remaining_high_usd: float | None = None
    forecast_total_low_usd: float | None = None
    forecast_total_high_usd: float | None = None
    forecast_status: str = "INSUFFICIENT_DATA"
    categories: list[BookCostCategory]
    operations: list[BookCostOperation]


_CATEGORY_BY_STAGE: dict[AutoBookStage, str] = {
    AutoBookStage.DEFINITION: "Замысел / План",
    AutoBookStage.RESEARCH: "Research",
    AutoBookStage.ARCHITECTURE: "Архитектура",
    AutoBookStage.CHAPTER_CONTEXT: "Архитектура",
    AutoBookStage.WRITING: "Написание",
    AutoBookStage.CHAPTER_REVIEW: "Редактура",
    AutoBookStage.MIDBOOK_AUDIT: "Редактура",
    AutoBookStage.WHOLE_BOOK_EDIT: "Редактура",
    AutoBookStage.FACT_CHECK: "Проверка / BookBench",
    AutoBookStage.LITERARY_EDIT: "Редактура",
    AutoBookStage.VISUALS: "Визуальные материалы",
    AutoBookStage.INDEPENDENT_CRITIQUE: "Проверка / BookBench",
    AutoBookStage.CORRECTION: "Редактура",
    AutoBookStage.AUDIO_EDITORIAL: "Аудиоредакция",
    AutoBookStage.MASTER_AND_EXPORTS: "Выпуск",
}


def _operation_cost(operation: AutoBookOperationView) -> tuple[float, float, float, float]:
    confirmed = float(operation.confirmed_cost_usd or 0)
    estimated = float(operation.estimated_cost_usd or 0)
    raw_reserved = float(operation.reserved_cost_usd or 0)
    reserved = raw_reserved if operation.state in {"RESERVED", "RUNNING"} else 0.0
    unknown = max(raw_reserved, estimated) if operation.state == "UNKNOWN" else 0.0
    return confirmed, estimated, reserved, unknown


class BookCostService:
    """Owner-facing read model over the existing idempotent Auto Book ledger.

    The runtime's ``estimated_cost_usd`` is a safety ceiling, so it is deliberately not exposed as
    a forecast.  Forecast fields remain empty until a separate evidence-backed estimator exists.
    """

    def __init__(self, data_dir: Path) -> None:
        self.runtime = DurableAutoBookRuntime(data_dir)

    def get(self, book_id: str) -> BookCostView | None:
        run = self.runtime.latest(book_id)
        if run is None:
            return None
        operations = self.runtime.list_operations(book_id, run.run_id)
        grouped: dict[str, list[float]] = {}
        operation_views: list[BookCostOperation] = []
        for operation in operations:
            category = _CATEGORY_BY_STAGE[operation.stage]
            confirmed, estimated, reserved, unknown = _operation_cost(operation)
            totals = grouped.setdefault(category, [0.0, 0.0, 0.0, 0.0])
            totals[0] += confirmed
            totals[1] += estimated
            totals[2] += reserved
            totals[3] += unknown
            operation_views.append(
                BookCostOperation(
                    operation_id=operation.operation_id,
                    operation=operation.operation,
                    user_stage=category,
                    status=operation.state,
                    confirmed_cost_usd=confirmed,
                    estimated_cost_usd=estimated,
                    reserved_cost_usd=reserved,
                    unknown_cost_usd=unknown,
                    provider=operation.provider,
                    model=operation.model,
                    reasoning_effort=operation.reasoning_effort,
                    created_at=operation.created_at,
                )
            )
        categories = [
            BookCostCategory(
                category=category,
                confirmed_cost_usd=round(values[0], 6),
                estimated_cost_usd=round(values[1], 6),
                reserved_cost_usd=round(values[2], 6),
                unknown_cost_usd=round(values[3], 6),
            )
            for category, values in grouped.items()
            if any(value > 0 for value in values)
        ]
        return BookCostView(
            book_id=book_id,
            run_id=run.run_id,
            confirmed_cost_usd=run.confirmed_cost_usd,
            estimated_operations_cost_usd=round(
                sum(item.estimated_cost_usd for item in operations), 6
            ),
            reserved_cost_usd=run.reserved_cost_usd,
            unknown_cost_usd=run.unknown_cost_usd,
            max_budget_usd=run.intent.max_total_cost_usd,
            categories=categories,
            operations=operation_views,
        )
