from __future__ import annotations

from collections.abc import Callable
import os
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from .anti_junk import AntiJunkCreateRequest, AntiJunkError, AntiJunkService
from .blind_model_compare import (
    BlindBookContractCompareRequest,
    BlindBookContractComparisonService,
    BlindBookContractSelectRequest,
    BlindComparisonError,
    BlindComparisonGateError,
)
from .book_context import BookContextService
from .context_planning import ContextAwarePlanningService
from .model_gateway import ModelGateway
from .model_routing import ModelRoutingError, ModelRoutingService
from .planning import (
    ArchitecturePlanningRequest,
    BookContractPlanningRequest,
    ChapterContractPlanningRequest,
    PlanningError,
    PlanningGateError,
)
from .secrets import MacOSKeychainSecretStore, SecretNotFound, SecretWriteError


class OpenAIKeyRequest(BaseModel):
    api_key: str = Field(min_length=10, max_length=1000)


class YandexCredentialRequest(BaseModel):
    api_key: str = Field(min_length=10, max_length=1000)
    folder_id: str = Field(min_length=3, max_length=160)


class RoutedBookContractPlanningRequest(BookContractPlanningRequest):
    selection_mode: Literal["AUTO", "MANUAL"] = "AUTO"
    selection_scope: Literal["OPERATION", "BOOK"] | None = None


class RoutedArchitecturePlanningRequest(ArchitecturePlanningRequest):
    selection_mode: Literal["AUTO", "MANUAL"] = "AUTO"
    selection_scope: Literal["OPERATION", "BOOK"] | None = None


class RoutedChapterContractPlanningRequest(ChapterContractPlanningRequest):
    selection_mode: Literal["AUTO", "MANUAL"] = "AUTO"
    selection_scope: Literal["OPERATION", "BOOK"] | None = None


def build_launch_router(
    data_dir: Path,
    require_token: Callable[..., None],
    gateway: ModelGateway,
) -> APIRouter:
    anti_junk = AntiJunkService(data_dir)
    planning = ContextAwarePlanningService(data_dir, gateway)
    routing = ModelRoutingService(data_dir)
    contexts = BookContextService(data_dir)
    blind_compare = BlindBookContractComparisonService(data_dir)
    keychain = MacOSKeychainSecretStore()
    router = APIRouter(dependencies=[Depends(require_token)])

    def credential_state(*names: str) -> str:
        try:
            for name in names:
                keychain.get_secret(name)
        except SecretNotFound:
            return "NOT_AVAILABLE"
        return "AVAILABLE"

    def require_book_context(book_id: str) -> None:
        context = contexts.get_context(book_id)
        if not context.ready_for_planning:
            raise PlanningGateError(
                "Before AI planning, approve Author Profile and Style Profile, choose optional "
                "Series Profile, and set target length in characters including spaces"
            )

    @router.get("/api/launch/readiness")
    def launch_readiness() -> dict[str, object]:
        return {
            "openai_credential_state": credential_state("openai_api_key"),
            "yandex_credential_state": credential_state(
                "yandex_ai_studio_api_key", "yandex_folder_id"
            ),
            "configured_model": os.environ.get("BOOK_OS_OPENAI_MODEL", "").strip() or None,
            "providers": [item.model_dump(mode="json") for item in routing.provider_registry()],
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
                status_code=503, detail="Не удалось сохранить ключ AI Pro в macOS Keychain"
            ) from exc
        return {
            "openai_credential_state": "AVAILABLE",
            "secret_returned": False,
            "external_calls": 0,
            "paid_calls": 0,
        }

    @router.post("/api/launch/yandex-credentials")
    def save_yandex_credentials(payload: YandexCredentialRequest) -> dict[str, object]:
        try:
            keychain.set_secret("yandex_ai_studio_api_key", payload.api_key)
            keychain.set_secret("yandex_folder_id", payload.folder_id)
            keychain.get_secret("yandex_ai_studio_api_key")
            keychain.get_secret("yandex_folder_id")
        except (SecretWriteError, SecretNotFound) as exc:
            raise HTTPException(
                status_code=503, detail="Не удалось сохранить настройки AI Ya в macOS Keychain"
            ) from exc
        return {
            "yandex_credential_state": "AVAILABLE",
            "secret_returned": False,
            "external_calls": 0,
            "paid_calls": 0,
        }

    @router.get("/api/projects/{book_id}/model-routing")
    def get_model_routing(book_id: str) -> dict[str, object]:
        pin = routing.get_book_pin(book_id)
        return {
            "book_pin": pin.model_dump(mode="json") if pin is not None else None,
            "providers": [item.model_dump(mode="json") for item in routing.provider_registry()],
        }

    @router.post("/api/projects/{book_id}/model-routing/clear-book-pin")
    def clear_book_model_pin(book_id: str) -> dict[str, object]:
        routing.clear_book_pin(book_id)
        return {"book_pin": None}

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

    @router.post("/api/projects/{book_id}/planning/book-contract/blind-compare")
    def blind_compare_book_contract(
        book_id: str, payload: BlindBookContractCompareRequest
    ) -> dict[str, object]:
        try:
            require_book_context(book_id)
            return blind_compare.compare(book_id, payload).model_dump(mode="json")
        except PlanningGateError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except BlindComparisonGateError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except BlindComparisonError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post(
        "/api/projects/{book_id}/planning/book-contract/blind-compare/{comparison_id}/select"
    )
    def select_blind_book_contract(
        book_id: str,
        comparison_id: str,
        payload: BlindBookContractSelectRequest,
    ) -> dict[str, object]:
        try:
            return blind_compare.select(book_id, comparison_id, payload).model_dump(mode="json")
        except BlindComparisonGateError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except BlindComparisonError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/api/projects/{book_id}/planning/book-contract")
    def propose_book_contract(
        book_id: str, payload: RoutedBookContractPlanningRequest
    ) -> dict[str, object]:
        try:
            require_book_context(book_id)
            choice = routing.resolve(
                book_id,
                "BOOK_CONTRACT_PROPOSAL",
                provider=payload.provider,
                selection_mode=payload.selection_mode,
                selection_scope=payload.selection_scope,
                model=payload.model,
            )
            request = BookContractPlanningRequest.model_validate(
                {
                    **payload.model_dump(mode="json"),
                    "provider": choice.provider,
                    "model": choice.model,
                }
            )
            result = planning.propose_book_contract(book_id, request)
            routing.record_run(book_id, result.run_id, choice)
            return {
                **result.model_dump(mode="json"),
                "routing": choice.model_dump(mode="json"),
            }
        except ModelRoutingError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except PlanningGateError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except PlanningError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/api/projects/{book_id}/planning/architecture")
    def propose_architecture(
        book_id: str, payload: RoutedArchitecturePlanningRequest
    ) -> dict[str, object]:
        try:
            require_book_context(book_id)
            choice = routing.resolve(
                book_id,
                "ARCHITECTURE_PROPOSAL",
                provider=payload.provider,
                selection_mode=payload.selection_mode,
                selection_scope=payload.selection_scope,
                model=payload.model,
            )
            request = ArchitecturePlanningRequest.model_validate(
                {
                    **payload.model_dump(mode="json"),
                    "provider": choice.provider,
                    "model": choice.model,
                }
            )
            result = planning.propose_architecture(book_id, request)
            routing.record_run(book_id, result.run_id, choice)
            return {
                **result.model_dump(mode="json"),
                "routing": choice.model_dump(mode="json"),
            }
        except ModelRoutingError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except PlanningGateError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except PlanningError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/api/projects/{book_id}/chapters/{chapter_id}/planning/contract")
    def propose_chapter_contract(
        book_id: str,
        chapter_id: str,
        payload: RoutedChapterContractPlanningRequest,
    ) -> dict[str, object]:
        try:
            require_book_context(book_id)
            choice = routing.resolve(
                book_id,
                "CHAPTER_CONTRACT_PROPOSAL",
                provider=payload.provider,
                selection_mode=payload.selection_mode,
                selection_scope=payload.selection_scope,
                model=payload.model,
            )
            request = ChapterContractPlanningRequest.model_validate(
                {
                    **payload.model_dump(mode="json"),
                    "provider": choice.provider,
                    "model": choice.model,
                }
            )
            result = planning.propose_chapter_contract(book_id, chapter_id, request)
            routing.record_run(book_id, result.run_id, choice)
            return {
                **result.model_dump(mode="json"),
                "routing": choice.model_dump(mode="json"),
            }
        except ModelRoutingError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except PlanningGateError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except PlanningError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return router
