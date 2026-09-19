from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from .book_context import BookContextError, BookContextGateError, ProfileNotFound
from .model_gateway import ModelBudgetError, ModelGateway, ModelOutputError, ModelProviderError
from .series_costs import SeriesCostLedger
from .series_reference import (
    SeriesReferenceError,
    SeriesReferenceService,
    SeriesReferenceUploadRequest,
)
from .series_studio import SeriesCreateWithAIRequest, SeriesStudioError, SeriesStudioService
from .series_workspace import (
    SeriesBookCreateRequest,
    SeriesBookScopeRequest,
    SeriesCreateRequest,
    SeriesExportSelection,
    SeriesImportRequest,
    SeriesOverlapDispositionRequest,
    SeriesPresetRequest,
    SeriesTopicOwnershipRequest,
    SeriesWorkspaceError,
    SeriesWorkspaceGateError,
    SeriesWorkspaceService,
)


def build_series_studio_router(
    data_dir: Path,
    require_token: Callable[..., None],
    gateway: ModelGateway,
) -> APIRouter:
    studio = SeriesStudioService(data_dir, gateway)
    references = SeriesReferenceService(data_dir)
    workspaces = SeriesWorkspaceService(data_dir)
    costs = SeriesCostLedger(data_dir)
    router = APIRouter(dependencies=[Depends(require_token)])

    @router.post("/api/series/create-with-ai")
    def create_series_with_ai(payload: SeriesCreateWithAIRequest) -> dict[str, object]:
        try:
            result = studio.create_with_ai(payload)
            costs.record_series_creation(
                series_profile_ids=[item.profile_id for item in result.concepts],
                provider=result.provider,
                model=result.model,
                reasoning_effort=result.reasoning_effort,
                provider_run_id=result.provider_run_id,
                usage=result.usage,
            )
            return result.model_dump(mode="json")
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

    @router.get("/api/series/workspaces")
    def list_series_workspaces() -> list[dict[str, object]]:
        return [item.model_dump(mode="json") for item in workspaces.workspaces()]

    @router.get("/api/series/{series_profile_id}/costs")
    def get_series_costs(series_profile_id: str) -> dict[str, object]:
        try:
            return costs.get(series_profile_id).model_dump(mode="json")
        except ProfileNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post("/api/series/workspaces")
    def create_series_workspace(payload: SeriesCreateRequest) -> dict[str, object]:
        try:
            return dict(workspaces.create_series(payload).model_dump(mode="json"))
        except (SeriesWorkspaceError, BookContextError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/api/series/presets/services-promotion")
    def create_services_promotion_preset(payload: SeriesPresetRequest) -> dict[str, object]:
        try:
            return workspaces.create_services_promotion_preset(payload).model_dump(mode="json")
        except ProfileNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except SeriesWorkspaceGateError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except SeriesWorkspaceError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/api/series/{series_profile_id}/books/scope-check")
    def check_series_book_scope(
        series_profile_id: str,
        payload: SeriesBookScopeRequest,
    ) -> dict[str, object]:
        try:
            return workspaces.assess_book_scope(series_profile_id, payload).model_dump(mode="json")
        except SeriesWorkspaceError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/api/series/{series_profile_id}/books")
    def add_series_book(
        series_profile_id: str,
        payload: SeriesBookCreateRequest,
    ) -> dict[str, object]:
        try:
            # Imported books already exist as books outside BOOK OS. New/planned ideas, however,
            # must pass the explicit "new book or chapter of an existing one?" gate first.
            if payload.source_kind != "IMPORTED":
                assessment = workspaces.assess_book_scope(
                    series_profile_id,
                    SeriesBookScopeRequest(
                        idea=payload.unique_idea,
                        reader_problem=payload.reader_problem,
                        reader_result=payload.reader_result,
                        unique_mechanism=payload.unique_mechanism,
                    ),
                )
                if assessment.recommendation != "NEW_BOOK":
                    raise SeriesWorkspaceGateError(
                        "new-book scope is not clear: "
                        f"{assessment.recommendation}; compare with "
                        f"«{assessment.candidate_book_title or 'existing series book'}» before adding"
                    )
            return workspaces.add_book(series_profile_id, payload).model_dump(mode="json")
        except ProfileNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except SeriesWorkspaceGateError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except SeriesWorkspaceError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/api/series/{series_profile_id}/books/{book_id}/passport/approve")
    def approve_book_passport(
        series_profile_id: str,
        book_id: str,
        payload: dict[str, str],
    ) -> dict[str, object]:
        try:
            return workspaces.approve_book_passport(
                series_profile_id,
                book_id,
                payload.get("passport_hash", ""),
                payload.get("reason", ""),
            ).model_dump(mode="json")
        except SeriesWorkspaceGateError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except SeriesWorkspaceError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/api/series/{series_profile_id}/books/{book_id}/start-fresh")
    def start_fresh_series_book(series_profile_id: str, book_id: str) -> dict[str, object]:
        try:
            return workspaces.start_fresh_book(series_profile_id, book_id).model_dump(mode="json")
        except SeriesWorkspaceGateError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except SeriesWorkspaceError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/api/series/{series_profile_id}/books/{book_id}/imports")
    def import_series_book(
        series_profile_id: str,
        book_id: str,
        payload: SeriesImportRequest,
    ) -> dict[str, object]:
        try:
            return workspaces.import_source(series_profile_id, book_id, payload).model_dump(
                mode="json"
            )
        except SeriesWorkspaceError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/api/series/{series_profile_id}/topic-ownership")
    def list_topic_ownership(series_profile_id: str) -> list[dict[str, object]]:
        try:
            return [
                item.model_dump(mode="json")
                for item in workspaces.topic_ownerships(series_profile_id)
            ]
        except SeriesWorkspaceError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/api/series/{series_profile_id}/topic-ownership")
    def assign_topic_ownership(
        series_profile_id: str,
        payload: SeriesTopicOwnershipRequest,
    ) -> dict[str, object]:
        try:
            return workspaces.assign_topic_ownership(series_profile_id, payload).model_dump(
                mode="json"
            )
        except SeriesWorkspaceGateError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except SeriesWorkspaceError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/api/series/{series_profile_id}/analyze")
    def analyze_series(series_profile_id: str) -> dict[str, object]:
        try:
            return workspaces.analyze(series_profile_id).model_dump(mode="json")
        except SeriesWorkspaceGateError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except SeriesWorkspaceError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/api/series/{series_profile_id}/findings/{finding_id}/disposition")
    def dispose_series_overlap(
        series_profile_id: str,
        finding_id: str,
        payload: SeriesOverlapDispositionRequest,
    ) -> dict[str, object]:
        try:
            return workspaces.dispose_overlap(
                series_profile_id,
                finding_id,
                payload,
            ).model_dump(mode="json")
        except SeriesWorkspaceGateError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except SeriesWorkspaceError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/api/series/{series_profile_id}/maps/{map_hash}/approve")
    def approve_series_map(
        series_profile_id: str,
        map_hash: str,
        payload: dict[str, str],
    ) -> dict[str, object]:
        try:
            return workspaces.approve_map(
                series_profile_id,
                map_hash,
                payload.get("reason", ""),
            ).model_dump(mode="json")
        except SeriesWorkspaceGateError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except SeriesWorkspaceError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/api/series/{series_profile_id}/books/{book_id}/archive")
    def archive_series_book(series_profile_id: str, book_id: str) -> dict[str, object]:
        try:
            return workspaces.archive_book(series_profile_id, book_id).model_dump(mode="json")
        except SeriesWorkspaceError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.delete("/api/series/{series_profile_id}/books/{book_id}/imports/{source_id}")
    def delete_series_import(
        series_profile_id: str, book_id: str, source_id: str
    ) -> dict[str, object]:
        try:
            return workspaces.delete_import(series_profile_id, book_id, source_id).model_dump(
                mode="json"
            )
        except SeriesWorkspaceError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/api/series/{series_profile_id}/exports")
    def export_series(series_profile_id: str, payload: SeriesExportSelection) -> dict[str, object]:
        try:
            return workspaces.export_series(series_profile_id, payload).model_dump(mode="json")
        except SeriesWorkspaceGateError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except SeriesWorkspaceError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return router
