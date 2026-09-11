from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from .auto_book import (
    AutoBookError,
    AutoBookGateError,
    AutoBookNotFound,
    AutoBookService,
    AutoBookStartRequest,
)
from .model_gateway import ModelGateway


def build_auto_book_router(
    data_dir: Path,
    require_token: Callable[..., None],
    gateway: ModelGateway,
) -> APIRouter:
    service = AutoBookService(data_dir, gateway)
    router = APIRouter(dependencies=[Depends(require_token)])

    def raise_http(exc: AutoBookError) -> None:
        if isinstance(exc, AutoBookNotFound):
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        if isinstance(exc, AutoBookGateError):
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/api/projects/{book_id}/auto-book")
    def get_auto_book(book_id: str) -> dict[str, object] | None:
        try:
            state = service.get(book_id)
            return state.model_dump(mode="json") if state is not None else None
        except AutoBookError as exc:
            raise_http(exc)
        raise AssertionError("unreachable")

    @router.post("/api/projects/{book_id}/auto-book/start")
    def start_auto_book(book_id: str, payload: AutoBookStartRequest) -> dict[str, object]:
        try:
            return service.start(book_id, payload).model_dump(mode="json")
        except AutoBookError as exc:
            raise_http(exc)
        raise AssertionError("unreachable")

    @router.post("/api/projects/{book_id}/auto-book/advance")
    def advance_auto_book(book_id: str) -> dict[str, object]:
        try:
            return service.advance(book_id).model_dump(mode="json")
        except AutoBookError as exc:
            raise_http(exc)
        raise AssertionError("unreachable")

    @router.post("/api/projects/{book_id}/auto-book/stop")
    def stop_auto_book(book_id: str) -> dict[str, object]:
        try:
            return service.stop(book_id).model_dump(mode="json")
        except AutoBookError as exc:
            raise_http(exc)
        raise AssertionError("unreachable")

    return router
