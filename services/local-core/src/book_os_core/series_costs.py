from __future__ import annotations

import hashlib
import json
from pathlib import Path
import threading
from typing import Any

from pydantic import BaseModel, Field

from .authority import new_ulid
from .authority_types import utc_now
from .auto_book_runtime import DurableAutoBookRuntime
from .series_workspace import SeriesWorkspaceService


class SeriesCostEntry(BaseModel):
    entry_id: str
    operation_identity: str
    series_profile_ids: list[str]
    operation: str
    provider: str
    model: str
    reasoning_effort: str | None = None
    provider_run_id: str | None = None
    confirmed_cost_usd: float = Field(default=0, ge=0)
    estimated_cost_usd: float = Field(default=0, ge=0)
    unknown_cost_usd: float = Field(default=0, ge=0)
    created_at: str


class SeriesBookCost(BaseModel):
    book_id: str
    title: str
    confirmed_cost_usd: float = 0
    estimated_cost_usd: float = 0
    reserved_cost_usd: float = 0
    unknown_cost_usd: float = 0
    runtime_status: str | None = None
    forecast_total_low_usd: float | None = None
    forecast_total_high_usd: float | None = None


class SeriesFutureBookCost(BaseModel):
    title: str
    forecast_total_low_usd: float | None = None
    forecast_total_high_usd: float | None = None


class SeriesCostView(BaseModel):
    series_profile_id: str
    series_confirmed_cost_usd: float
    books_confirmed_cost_usd: float
    total_confirmed_cost_usd: float
    total_estimated_cost_usd: float
    total_reserved_cost_usd: float
    total_unknown_cost_usd: float
    current_books_forecast_low_usd: float | None = None
    current_books_forecast_high_usd: float | None = None
    production_forecast_low_usd: float | None = None
    production_forecast_high_usd: float | None = None
    production_forecast_status: str = "INSUFFICIENT_DATA"
    books: list[SeriesBookCost]
    future_books: list[SeriesFutureBookCost]
    operations: list[SeriesCostEntry]


class SeriesCostLedger:
    """Small durable read model for Owner-facing series production cost.

    Book costs remain owned by each book's durable Auto Book ledger.  This file stores only
    genuinely series-level paid operations, so those costs never disappear into one book or get
    counted once per generated concept candidate.
    """

    _LOCK = threading.RLock()

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.path = data_dir / "series-cost-ledger.json"
        self.workspaces = SeriesWorkspaceService(data_dir)
        self.runtime = DurableAutoBookRuntime(data_dir)

    def _read(self) -> list[SeriesCostEntry]:
        if not self.path.exists():
            return []
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return [SeriesCostEntry.model_validate(item) for item in payload.get("entries", [])]

    def _write(self, entries: list[SeriesCostEntry]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(
                {"version": 1, "entries": [item.model_dump(mode="json") for item in entries]},
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        temporary.replace(self.path)

    @staticmethod
    def _costs(usage: dict[str, Any]) -> tuple[float, float, float]:
        guard = usage.get("cost_guard")
        if not isinstance(guard, dict):
            return 0.0, 0.0, 0.0
        actual = guard.get("estimated_actual_cost_usd")
        preflight = guard.get("preflight_upper_bound_usd")
        if isinstance(actual, (int, float)) and actual >= 0:
            # Token-based pricing is still an estimate; only a provider-reconciled value may be
            # presented to the Owner as confirmed spend.
            value = round(float(actual), 6)
            return 0.0, value, 0.0
        if isinstance(preflight, (int, float)) and preflight >= 0:
            # The request completed but no provider-price reconciliation was available.  Keep the
            # bounded amount explicit as unknown instead of presenting it as paid or as zero.
            value = round(float(preflight), 6)
            return 0.0, value, value
        return 0.0, 0.0, 0.0

    def record_series_creation(
        self,
        *,
        series_profile_ids: list[str],
        provider: str,
        model: str,
        reasoning_effort: str | None,
        provider_run_id: str | None,
        usage: dict[str, Any],
    ) -> SeriesCostEntry:
        confirmed, estimated, unknown = self._costs(usage)
        identity_payload = {
            "series_profile_ids": sorted(series_profile_ids),
            "provider": provider,
            "model": model,
            "reasoning_effort": reasoning_effort,
            "provider_run_id": provider_run_id,
            "usage": usage,
        }
        identity = (
            provider_run_id
            or hashlib.sha256(
                json.dumps(identity_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
        )
        with self._LOCK:
            entries = self._read()
            existing = next(
                (item for item in entries if item.operation_identity == identity),
                None,
            )
            if existing is not None:
                return existing
            entry = SeriesCostEntry(
                entry_id=new_ulid(),
                operation_identity=identity,
                series_profile_ids=series_profile_ids,
                operation="SERIES_CONCEPT",
                provider=provider,
                model=model,
                reasoning_effort=reasoning_effort,
                provider_run_id=provider_run_id,
                confirmed_cost_usd=confirmed,
                estimated_cost_usd=estimated,
                unknown_cost_usd=unknown,
                created_at=utc_now(),
            )
            self._write([*entries, entry])
            return entry

    def _book_cost(self, book_id: str, title: str) -> SeriesBookCost:
        state_path = self.data_dir / "projects" / book_id / "auto-book-run.json"
        runtime = self.runtime.latest(book_id)
        if runtime is not None:
            return SeriesBookCost(
                book_id=book_id,
                title=title,
                confirmed_cost_usd=runtime.confirmed_cost_usd,
                estimated_cost_usd=sum(
                    item.estimated_cost_usd
                    for item in self.runtime.list_operations(book_id, runtime.run_id)
                ),
                reserved_cost_usd=runtime.reserved_cost_usd,
                unknown_cost_usd=runtime.unknown_cost_usd,
                runtime_status=runtime.status,
            )
        if not state_path.exists():
            return SeriesBookCost(book_id=book_id, title=title)
        payload = json.loads(state_path.read_text(encoding="utf-8"))
        # Runs created before the durable runtime ledger remain visible from their legacy state
        # file without rewriting owner data.  Their ``estimated_cost_usd`` was a budget ceiling,
        # not a forecast, and therefore must not leak into this read model.
        return SeriesBookCost(
            book_id=book_id,
            title=title,
            confirmed_cost_usd=float(payload.get("confirmed_cost_usd") or 0),
            # Legacy state used this field as a budget ceiling.  It cannot be represented as a
            # production forecast or operation estimate without misleading the Owner.
            estimated_cost_usd=0,
            reserved_cost_usd=float(payload.get("reserved_cost_usd") or 0),
            unknown_cost_usd=float(payload.get("unknown_cost_usd") or 0),
            runtime_status=str(payload.get("status")) if payload.get("status") else None,
        )

    def get(self, series_profile_id: str) -> SeriesCostView:
        books = [
            self._book_cost(item.book_id, item.title)
            for item in self.workspaces.books(series_profile_id)
        ]
        operations = [item for item in self._read() if series_profile_id in item.series_profile_ids]
        profile = self.workspaces.profiles.get_profile(series_profile_id)
        planned_titles = [
            str(item).strip()
            for item in profile.content.get("planned_books", [])
            if str(item).strip()
        ]
        existing_titles = {item.title for item in books}
        future_titles = [item for item in planned_titles if item not in existing_titles]
        completed = [
            item
            for item in books
            if item.runtime_status == "PACKAGE_READY" and item.confirmed_cost_usd > 0
        ]
        comparable_average = (
            sum(item.confirmed_cost_usd for item in completed) / len(completed)
            if completed
            else None
        )
        future_books = [
            SeriesFutureBookCost(
                title=title,
                forecast_total_low_usd=(
                    round(comparable_average * 0.85, 2) if comparable_average is not None else None
                ),
                forecast_total_high_usd=(
                    round(comparable_average * 1.15, 2) if comparable_average is not None else None
                ),
            )
            for title in future_titles
        ]
        unfinished = [item for item in books if item.runtime_status != "PACKAGE_READY"]
        current_low: float | None
        current_high: float | None
        production_low: float | None
        production_high: float | None
        if comparable_average is not None:
            for item in unfinished:
                item.forecast_total_low_usd = round(
                    max(item.confirmed_cost_usd, comparable_average * 0.85), 2
                )
                item.forecast_total_high_usd = round(
                    max(item.confirmed_cost_usd, comparable_average * 1.15), 2
                )
            current_low = round(sum(item.forecast_total_low_usd or 0 for item in unfinished), 2)
            current_high = round(sum(item.forecast_total_high_usd or 0 for item in unfinished), 2)
            series_confirmed_for_forecast = sum(item.confirmed_cost_usd for item in operations)
            completed_confirmed = sum(item.confirmed_cost_usd for item in completed)
            production_low = round(
                series_confirmed_for_forecast
                + completed_confirmed
                + current_low
                + sum(item.forecast_total_low_usd or 0 for item in future_books),
                2,
            )
            production_high = round(
                series_confirmed_for_forecast
                + completed_confirmed
                + current_high
                + sum(item.forecast_total_high_usd or 0 for item in future_books),
                2,
            )
        else:
            current_low = current_high = production_low = production_high = None
        series_confirmed = round(sum(item.confirmed_cost_usd for item in operations), 6)
        books_confirmed = round(sum(item.confirmed_cost_usd for item in books), 6)
        return SeriesCostView(
            series_profile_id=series_profile_id,
            series_confirmed_cost_usd=series_confirmed,
            books_confirmed_cost_usd=books_confirmed,
            total_confirmed_cost_usd=round(series_confirmed + books_confirmed, 6),
            total_estimated_cost_usd=round(
                sum(item.estimated_cost_usd for item in operations)
                + sum(item.estimated_cost_usd for item in books),
                6,
            ),
            total_reserved_cost_usd=round(sum(item.reserved_cost_usd for item in books), 6),
            total_unknown_cost_usd=round(
                sum(item.unknown_cost_usd for item in operations)
                + sum(item.unknown_cost_usd for item in books),
                6,
            ),
            current_books_forecast_low_usd=current_low,
            current_books_forecast_high_usd=current_high,
            production_forecast_low_usd=production_low,
            production_forecast_high_usd=production_high,
            production_forecast_status=(
                "COMPARABLE_COMPLETED_BOOKS"
                if comparable_average is not None
                else "INSUFFICIENT_DATA"
            ),
            books=books,
            future_books=future_books,
            operations=operations,
        )
