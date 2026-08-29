from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from .literary_master import (
    LiteraryMasterError,
    LiteraryMasterGateError,
    LiteraryMasterNotFound,
    LiteraryMasterService,
)


class LiteraryMasterCreateRequest(BaseModel):
    human_actor: str = Field(min_length=1, max_length=255)


def build_literary_master_router(
    data_dir: Path,
    require_token: Callable[..., None],
) -> APIRouter:
    service = LiteraryMasterService(data_dir)
    router = APIRouter(dependencies=[Depends(require_token)])

    def raise_http(exc: LiteraryMasterError) -> None:
        if isinstance(exc, LiteraryMasterNotFound):
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        if isinstance(exc, LiteraryMasterGateError):
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/api/projects/{book_id}/literary-master/readiness")
    def readiness(book_id: str) -> dict[str, object]:
        try:
            return service.readiness(book_id).model_dump(mode="json")
        except LiteraryMasterError as exc:
            raise_http(exc)
        raise AssertionError("unreachable")

    @router.post("/api/projects/{book_id}/literary-masters")
    def create_master(book_id: str, payload: LiteraryMasterCreateRequest) -> dict[str, object]:
        try:
            return service.create_master(
                book_id, human_actor=payload.human_actor
            ).model_dump(mode="json")
        except LiteraryMasterError as exc:
            raise_http(exc)
        raise AssertionError("unreachable")

    @router.get("/api/projects/{book_id}/literary-masters")
    def list_masters(book_id: str) -> list[dict[str, object]]:
        try:
            return [item.model_dump(mode="json") for item in service.list_masters(book_id)]
        except LiteraryMasterError as exc:
            raise_http(exc)
        raise AssertionError("unreachable")

    @router.get("/api/projects/{book_id}/literary-masters/{master_id}")
    def get_master(book_id: str, master_id: str) -> dict[str, object]:
        try:
            return service.get_master(book_id, master_id).model_dump(mode="json")
        except LiteraryMasterError as exc:
            raise_http(exc)
        raise AssertionError("unreachable")

    @router.post("/api/projects/{book_id}/literary-masters/{master_id}/exports/markdown")
    def export_markdown(book_id: str, master_id: str) -> dict[str, object]:
        try:
            return service.export_markdown(book_id, master_id).model_dump(mode="json")
        except LiteraryMasterError as exc:
            raise_http(exc)
        raise AssertionError("unreachable")

    @router.post("/api/projects/{book_id}/literary-masters/{master_id}/handoff/audiobook")
    def audiobook_handoff(book_id: str, master_id: str) -> dict[str, object]:
        try:
            return service.audiobook_handoff(book_id, master_id).model_dump(mode="json")
        except LiteraryMasterError as exc:
            raise_http(exc)
        raise AssertionError("unreachable")

    return router
