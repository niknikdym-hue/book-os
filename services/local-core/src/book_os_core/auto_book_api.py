from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
import httpx

from .auto_book import (
    AutoBookError,
    AutoBookGateError,
    AutoBookNotFound,
    AutoBookRunView,
    AutoBookService,
    AutoBookStartRequest,
)
from .auto_book_finalizer import AutoBookFinalizer
from .book_context import BookContextService
from .model_gateway import ModelGateway, ModelProviderError
from .series_production import SeriesProductionGateError, SeriesProductionService


def build_auto_book_router(
    data_dir: Path,
    require_token: Callable[..., None],
    gateway: ModelGateway,
) -> APIRouter:
    service = AutoBookService(data_dir, gateway)
    finalizer = AutoBookFinalizer(data_dir, gateway)
    contexts = BookContextService(data_dir)
    series_production = SeriesProductionService(data_dir)
    router = APIRouter(dependencies=[Depends(require_token)])

    def raise_http(exc: AutoBookError) -> None:
        if isinstance(exc, AutoBookNotFound):
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        if isinstance(exc, AutoBookGateError):
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    def pause_after_provider_disconnect(book_id: str, exc: Exception) -> None:
        """Keep an Auto Book run resumable after a provider/network interruption.

        Model requests are intentionally not retried automatically: a transport failure can happen
        after the provider has already accepted a paid request. Retrying blindly could duplicate cost.
        The run stays RUNNING at the same phase so the owner can safely continue from the UI.
        """

        state = service.get(book_id)
        if state is not None:
            state.status = "RUNNING"
            state.error = str(exc)
            state.last_action = "Temporary model connection interruption; progress saved"
            service._write(state)
        raise HTTPException(
            status_code=503,
            detail=(
                "Временный обрыв связи с моделью. Прогресс Auto Book сохранён. "
                "Нажмите «Продолжить с сохранённого места»."
            ),
        ) from exc

    def require_series_writing_gate(book_id: str, state: AutoBookRunView) -> None:
        if state.phase != "CHAPTER_DRAFT" or state.current_chapter_id is None:
            return
        context = contexts.get_context(book_id)
        if context.series_profile is None:
            return
        try:
            series_production.require_writing_allowed(book_id, state.current_chapter_id)
        except SeriesProductionGateError as exc:
            raise AutoBookGateError(
                "Series Auto Book cannot bypass the approved cross-book uniqueness lane: "
                + str(exc)
            ) from exc

    def finalization_complete(state: AutoBookRunView) -> bool:
        if state.status != "DONE":
            return False
        if state.last_action.startswith("Literary Master locked"):
            return True
        return bool(state.output_path and Path(state.output_path).name == "litres-ready.docx")

    def finalize_if_needed(book_id: str, state: AutoBookRunView) -> AutoBookRunView:
        if state.status != "DONE" or finalization_complete(state):
            return state

        draft_output = Path(state.output_path) if state.output_path else None
        state.status = "RUNNING"
        state.phase = "EXPORT"
        state.output_path = None
        state.error = None
        state.last_action = "Final editorial pass, BookBench and Literary Master"
        service._write(state)
        try:
            result = finalizer.finalize(
                book_id,
                state,
                prepare_litres_docx=state.prepare_litres_docx,
            )
        except Exception as exc:
            if draft_output is not None:
                draft_output.unlink(missing_ok=True)
            state.status = "RUNNING"
            state.phase = "EXPORT"
            state.output_path = None
            state.error = str(exc)
            state.last_action = "Final review requires rework before Literary Master"
            service._write(state)
            if isinstance(exc, AutoBookError):
                raise
            raise AutoBookGateError(f"Auto Book finalization blocked: {exc}") from exc

        if draft_output is not None and (
            result.output_path is None or draft_output != Path(result.output_path)
        ):
            draft_output.unlink(missing_ok=True)
        state.status = "DONE"
        state.phase = "DONE"
        state.output_path = result.output_path
        state.error = None
        state.last_action = (
            "Literary Master locked; LitRes-ready DOCX created"
            if result.output_path
            else "Literary Master locked; final review completed"
        )
        return service._write(state)

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
            current = service.get(book_id)
            if current is None:
                raise AutoBookNotFound("Auto Book has not been started for this book")
            if finalization_complete(current):
                return current.model_dump(mode="json")
            require_series_writing_gate(book_id, current)
            state = service.advance(book_id)
            return finalize_if_needed(book_id, state).model_dump(mode="json")
        except (httpx.TransportError, ModelProviderError) as exc:
            pause_after_provider_disconnect(book_id, exc)
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
