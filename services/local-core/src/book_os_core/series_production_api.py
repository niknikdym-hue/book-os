from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from .series_production import (
    ChapterAdmissionRequest,
    ChapterProductionContractApprovalRequest,
    ChapterProductionContractCreateRequest,
    DefinitionPackApprovalRequest,
    DefinitionPackCreateRequest,
    ProductionCheckpointRequest,
    SeriesCanonAssetCreateRequest,
    SeriesCanonTransitionRequest,
    SeriesClosureRequest,
    SeriesProductionError,
    SeriesProductionGateError,
    SeriesProductionService,
    UniquenessEvidenceRequest,
)


def build_series_production_router(
    data_dir: Path,
    require_token: Callable[..., None],
) -> APIRouter:
    service = SeriesProductionService(data_dir)
    router = APIRouter(dependencies=[Depends(require_token)])

    def raise_http(exc: SeriesProductionError) -> None:
        if isinstance(exc, SeriesProductionGateError):
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/api/projects/{book_id}/production/definition-packs")
    def create_definition(
        book_id: str,
        payload: DefinitionPackCreateRequest,
    ) -> dict[str, object]:
        try:
            return service.create_definition_pack(book_id, payload).model_dump(
                mode="json"
            )
        except SeriesProductionError as exc:
            raise_http(exc)
        raise AssertionError("unreachable")

    @router.get("/api/projects/{book_id}/production/definition-packs/current")
    def current_definition(book_id: str) -> dict[str, object] | None:
        try:
            current = service.latest_approved_definition(book_id)
            return None if current is None else current.model_dump(mode="json")
        except SeriesProductionError as exc:
            raise_http(exc)
        raise AssertionError("unreachable")

    @router.post(
        "/api/projects/{book_id}/production/definition-packs/"
        "{definition_id}/approve"
    )
    def approve_definition(
        book_id: str,
        definition_id: str,
        payload: DefinitionPackApprovalRequest,
    ) -> dict[str, object]:
        try:
            return service.approve_definition_pack(
                book_id,
                definition_id,
                payload,
            ).model_dump(mode="json")
        except SeriesProductionError as exc:
            raise_http(exc)
        raise AssertionError("unreachable")

    @router.post(
        "/api/projects/{book_id}/chapters/{chapter_id}/production-contracts"
    )
    def create_production_contract(
        book_id: str,
        chapter_id: str,
        payload: ChapterProductionContractCreateRequest,
    ) -> dict[str, object]:
        try:
            return service.create_production_contract(
                book_id,
                chapter_id,
                payload,
            ).model_dump(mode="json")
        except SeriesProductionError as exc:
            raise_http(exc)
        raise AssertionError("unreachable")

    @router.post(
        "/api/projects/{book_id}/chapters/{chapter_id}/production-contracts/"
        "{production_contract_id}/approve"
    )
    def approve_production_contract(
        book_id: str,
        chapter_id: str,
        production_contract_id: str,
        payload: ChapterProductionContractApprovalRequest,
    ) -> dict[str, object]:
        try:
            return service.approve_production_contract(
                book_id,
                chapter_id,
                production_contract_id,
                payload,
            ).model_dump(mode="json")
        except SeriesProductionError as exc:
            raise_http(exc)
        raise AssertionError("unreachable")

    @router.post("/api/projects/{book_id}/series-canon/assets")
    def create_canon_asset(
        book_id: str,
        payload: SeriesCanonAssetCreateRequest,
    ) -> dict[str, object]:
        try:
            effective = payload.model_copy(update={"book_id": book_id})
            return service.create_canon_asset(effective).model_dump(mode="json")
        except SeriesProductionError as exc:
            raise_http(exc)
        raise AssertionError("unreachable")

    @router.post(
        "/api/projects/{book_id}/series-canon/assets/{asset_id}/transition"
    )
    def transition_canon_asset(
        book_id: str,
        asset_id: str,
        payload: SeriesCanonTransitionRequest,
    ) -> dict[str, object]:
        try:
            return service.transition_canon_asset(
                book_id,
                asset_id,
                payload,
            ).model_dump(mode="json")
        except SeriesProductionError as exc:
            raise_http(exc)
        raise AssertionError("unreachable")

    @router.post("/api/projects/{book_id}/chapters/{chapter_id}/uniqueness")
    def record_uniqueness(
        book_id: str,
        chapter_id: str,
        payload: UniquenessEvidenceRequest,
    ) -> dict[str, object]:
        try:
            return service.record_uniqueness(
                book_id,
                chapter_id,
                payload,
            ).model_dump(mode="json")
        except SeriesProductionError as exc:
            raise_http(exc)
        raise AssertionError("unreachable")

    @router.get("/api/projects/{book_id}/chapters/{chapter_id}/admission")
    def admission_status(
        book_id: str,
        chapter_id: str,
    ) -> dict[str, object]:
        try:
            return service.admission_status(book_id, chapter_id).model_dump(
                mode="json"
            )
        except SeriesProductionError as exc:
            raise_http(exc)
        raise AssertionError("unreachable")

    @router.post("/api/projects/{book_id}/chapters/{chapter_id}/admission")
    def admit_chapter(
        book_id: str,
        chapter_id: str,
        payload: ChapterAdmissionRequest,
    ) -> dict[str, object]:
        try:
            return service.admit_chapter(
                book_id,
                chapter_id,
                payload,
            ).model_dump(mode="json")
        except SeriesProductionError as exc:
            raise_http(exc)
        raise AssertionError("unreachable")

    @router.post("/api/projects/{book_id}/production/checkpoints")
    def record_checkpoint(
        book_id: str,
        payload: ProductionCheckpointRequest,
    ) -> dict[str, object]:
        try:
            return service.record_checkpoint(book_id, payload).model_dump(
                mode="json"
            )
        except SeriesProductionError as exc:
            raise_http(exc)
        raise AssertionError("unreachable")

    @router.get(
        "/api/projects/{book_id}/production/adversarial-review-gate"
    )
    def adversarial_gate(book_id: str) -> dict[str, object]:
        try:
            ready, blockers = service.adversarial_review_gate(book_id)
            return {"ready": ready, "blockers": blockers}
        except SeriesProductionError as exc:
            raise_http(exc)
        raise AssertionError("unreachable")

    @router.post("/api/projects/{book_id}/production/series-closure")
    def close_series_book(
        book_id: str,
        payload: SeriesClosureRequest,
    ) -> dict[str, object]:
        try:
            return service.close_series_book(book_id, payload).model_dump(
                mode="json"
            )
        except SeriesProductionError as exc:
            raise_http(exc)
        raise AssertionError("unreachable")

    return router
