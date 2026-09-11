from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from .book_context import BookContextError, BookContextGateError, ProfileNotFound
from .model_gateway import ModelBudgetError, ModelOutputError, ModelProviderError, ModelGateway
from .series_reference import (
    SeriesReferenceError,
    SeriesReferenceService,
    SeriesReferenceUploadRequest,
)
from .series_studio import SeriesCreateWithAIRequest, SeriesStudioError, SeriesStudioService


def build_series_studio_router(
    data_dir: Path,
    require_token: Callable[..., None],
    gateway: ModelGateway,
) -> APIRouter:
    studio = SeriesStudioService(data_dir, gateway)
    references = SeriesReferenceService(data_dir)
    router = APIRouter(dependencies=[Depends(require_token)])

    @router.post("/api/series/create-with-ai")
    def create_series_with_ai(payload: SeriesCreateWithAIRequest) -> dict[str, object]:
        try:
            return studio.create_with_ai(payload).model_dump(mode="json")
        except ProfileNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except (BookContextGateError, ModelBudgetError) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ModelProviderError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except ModelOutputError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        except (SeriesStudioError, BookContextError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/api/series/{series_profile_id}/delivery-reference")
    def upload_series_reference(
        series_profile_id: str,
        payload: SeriesReferenceUploadRequest,
    ) -> dict[str, object]:
        try:
            return references.upload(series_profile_id, payload).model_dump(mode="json")
        except ProfileNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except BookContextGateError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except (SeriesReferenceError, BookContextError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/api/series/{series_profile_id}/delivery-reference")
    def get_series_reference(series_profile_id: str) -> dict[str, object] | None:
        try:
            current = references.current(series_profile_id)
            return None if current is None else current.model_dump(mode="json")
        except ProfileNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except BookContextGateError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except (SeriesReferenceError, BookContextError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return router
