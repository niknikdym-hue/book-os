from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import os

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from .anti_junk import AntiJunkCreateRequest, AntiJunkError, AntiJunkService
from .model_gateway import ModelGateway
from .planning import (
    ArchitecturePlanningRequest,
    BookContractPlanningRequest,
    ChapterContractPlanningRequest,
    PlanningError,
    PlanningGateError,
    PlanningService,
)
from .secrets import MacOSKeychainSecretStore, SecretNotFound, SecretWriteError


class OpenAIKeyRequest(BaseModel):
    api_key: str = Field(min_length=10, max_length=1000)


def build_launch_router(
    data_dir: Path,
    require_token: Callable[..., None],
    gateway: ModelGateway,
) -> APIRouter:
    anti_junk = AntiJunkService(data_dir)
    planning = PlanningService(data_dir, gateway)
    keychain = MacOSKeychainSecretStore()
    router = APIRouter(dependencies=[Depends(require_token)])

    @router.get("/api/launch/readiness")
    def launch_readiness() -> dict[str, object]:
        credential_state = "AVAILABLE"
        try:
            keychain.get_secret("openai_api_key")
        except SecretNotFound:
            credential_state = "NOT_AVAILABLE"
        return {
            "openai_credential_state": credential_state,
            "configured_model": os.environ.get("BOOK_OS_OPENAI_MODEL", "").strip() or None,
            "anti_junk_entry_count": len(anti_junk.list_entries()),
            "external_calls": 0,
            "paid_calls": 0,
        }

    @router.post("/api/launch/openai-key")
    def save_openai_key(payload: OpenAIKeyRequest) -> dict[str, object]:
        try:
            keychain.set_secret("openai_api_key", payload.api_key)
            keychain.get_secret("openai_api_key")
        except (SecretWriteError, SecretNotFound) as exc:
            raise HTTPException(
                status_code=503, detail="Не удалось сохранить ключ в macOS Keychain"
            ) from exc
        return {
            "openai_credential_state": "AVAILABLE",
            "secret_returned": False,
            "external_calls": 0,
            "paid_calls": 0,
        }

    @router.get("/api/anti-junk")
    def list_anti_junk() -> list[dict[str, object]]:
        return [entry.model_dump(mode="json") for entry in anti_junk.list_entries()]

    @router.post("/api/anti-junk")
    def add_anti_junk(payload: AntiJunkCreateRequest) -> dict[str, object]:
        try:
            return anti_junk.add(payload).model_dump(mode="json")
        except AntiJunkError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/api/anti-junk/{entry_id}/remove")
    def remove_anti_junk(entry_id: str) -> dict[str, bool]:
        try:
            anti_junk.remove(entry_id)
        except AntiJunkError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {"removed": True}

    @router.post("/api/projects/{book_id}/planning/book-contract")
    def propose_book_contract(
        book_id: str, payload: BookContractPlanningRequest
    ) -> dict[str, object]:
        try:
            return planning.propose_book_contract(book_id, payload).model_dump(mode="json")
        except PlanningGateError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except PlanningError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/api/projects/{book_id}/planning/architecture")
    def propose_architecture(
        book_id: str, payload: ArchitecturePlanningRequest
    ) -> dict[str, object]:
        try:
            return planning.propose_architecture(book_id, payload).model_dump(mode="json")
        except PlanningGateError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except PlanningError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/api/projects/{book_id}/chapters/{chapter_id}/planning/contract")
    def propose_chapter_contract(
        book_id: str,
        chapter_id: str,
        payload: ChapterContractPlanningRequest,
    ) -> dict[str, object]:
        try:
            return planning.propose_chapter_contract(book_id, chapter_id, payload).model_dump(
                mode="json"
            )
        except PlanningGateError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except PlanningError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return router
