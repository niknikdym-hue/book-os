from __future__ import annotations

import hashlib
import json
from pathlib import Path
import threading
from typing import Any

from pydantic import BaseModel, Field

from .authority import new_ulid
from .authority_types import utc_now
from .auto_book_runtime import AutoBookRuntimeError, DurableAutoBookRuntime
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


class SeriesCostView(BaseModel):
    series_profile_id: str
    series_confirmed_cost_usd: float
    books_confirmed_cost_usd: float
    total_confirmed_cost_usd: float
    total_estimated_cost_usd: float
    total_reserved_cost_usd: float
    total_unknown_cost_usd: float
    books: list[SeriesBookCost]
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
        if not state_path.exists():
            return SeriesBookCost(book_id=book_id, title=title)
        payload = json.loads(state_path.read_text(encoding="utf-8"))
        try:
            runtime = self.runtime.get(book_id, str(payload["run_id"]))
            return SeriesBookCost(
                book_id=book_id,
                title=title,
                confirmed_cost_usd=runtime.confirmed_cost_usd,
                estimated_cost_usd=runtime.estimated_cost_usd,
                reserved_cost_usd=runtime.reserved_cost_usd,
                unknown_cost_usd=runtime.unknown_cost_usd,
            )
        except (AutoBookRuntimeError, KeyError):
            # Runs created before the durable runtime ledger remain visible from their legacy
            # state file without rewriting owner data.
            pass
        return SeriesBookCost(
            book_id=book_id,
            title=title,
            confirmed_cost_usd=float(payload.get("confirmed_cost_usd") or 0),
            estimated_cost_usd=float(payload.get("estimated_cost_usd") or 0),
            reserved_cost_usd=float(payload.get("reserved_cost_usd") or 0),
            unknown_cost_usd=float(payload.get("unknown_cost_usd") or 0),
        )

    def get(self, series_profile_id: str) -> SeriesCostView:
        books = [
            self._book_cost(item.book_id, item.title)
            for item in self.workspaces.books(series_profile_id)
        ]
        operations = [item for item in self._read() if series_profile_id in item.series_profile_ids]
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
            books=books,
            operations=operations,
        )
