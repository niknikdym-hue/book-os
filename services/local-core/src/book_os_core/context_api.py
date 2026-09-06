from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException

from .book_context import (
    BookContextError,
    BookContextGateError,
    BookContextService,
    BookContextUpdateRequest,
    ProfileCreateRequest,
    ProfileNotFound,
    ProfileRegistry,
    ProfileUpdateRequest,
)


def build_context_router(data_dir: Path, require_token: Callable[..., None]) -> APIRouter:
    profiles = ProfileRegistry(data_dir)
    contexts = BookContextService(data_dir)
    router = APIRouter(dependencies=[Depends(require_token)])

    @router.get("/api/context/profiles")
    def list_profiles(
        kind: Literal["AUTHOR", "SERIES", "STYLE"] | None = None,
    ) -> list[dict[str, object]]:
        return [item.model_dump(mode="json") for item in profiles.list_profiles(kind)]

    @router.post("/api/context/profiles")
    def create_profile(payload: ProfileCreateRequest) -> dict[str, object]:
        try:
            return profiles.create_profile(payload).model_dump(mode="json")
        except BookContextError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.put("/api/context/profiles/{profile_id}")
    def update_profile(profile_id: str, payload: ProfileUpdateRequest) -> dict[str, object]:
        try:
            return profiles.update_profile(profile_id, payload).model_dump(mode="json")
        except ProfileNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except BookContextError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/api/context/profiles/{profile_id}/approve")
    def approve_profile(profile_id: str) -> dict[str, object]:
        try:
            return profiles.approve_profile(profile_id).model_dump(mode="json")
        except ProfileNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except BookContextGateError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except BookContextError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/api/projects/{book_id}/context")
    def get_book_context(book_id: str) -> dict[str, object]:
        try:
            return contexts.get_context(book_id).model_dump(mode="json")
        except BookContextError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.put("/api/projects/{book_id}/context")
    def save_book_context(
        book_id: str, payload: BookContextUpdateRequest
    ) -> dict[str, object]:
        try:
            return contexts.save_context(book_id, payload).model_dump(mode="json")
        except ProfileNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except BookContextGateError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except BookContextError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return router
