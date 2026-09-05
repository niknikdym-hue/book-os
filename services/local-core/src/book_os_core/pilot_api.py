from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from .anti_junk import AntiJunkService
from .launch_api import build_launch_router
from .model_gateway import ModelGateway, OpenAIResponsesAdapter
from .model_gateway_anti_junk import AntiJunkModelGateway
from .pilot import (
    FinalDecision,
    PilotError,
    PilotGateError,
    PilotNotFound,
    PilotObservationRequest,
    PilotService,
    PilotStageEventRequest,
)
from .secrets import MacOSKeychainSecretStore


class PilotStartRequest(BaseModel):
    human_actor: str = Field(min_length=1, max_length=255)


class PilotObservationResolutionRequest(BaseModel):
    actor: str = Field(min_length=1, max_length=255)
    actor_kind: Literal["HUMAN", "SYSTEM"]
    reason: str = Field(min_length=1)


class OpenAIPreflightRequest(BaseModel):
    writer_model: str = Field(min_length=1, max_length=128)
    evaluator_model: str = Field(min_length=1, max_length=128)
    editor_lane: str = Field(default="deterministic-m6-current", min_length=1, max_length=128)
    max_requests: int = Field(gt=0)
    max_input_tokens: int = Field(gt=0)
    max_output_tokens: int = Field(gt=0)
    max_cost_usd: float = Field(gt=0)


class PilotFinalDecisionRequest(BaseModel):
    decision: FinalDecision
    actor: str = Field(min_length=1, max_length=255)
    actor_kind: Literal["HUMAN"] = "HUMAN"
    reason: str = Field(min_length=1)


def build_pilot_router(data_dir: Path, require_token: Callable[..., None]) -> APIRouter:
    service = PilotService(data_dir)
    router = APIRouter(dependencies=[Depends(require_token)])
    anti_junk = AntiJunkService(data_dir)
    launch_gateway = AntiJunkModelGateway(
        ModelGateway({"openai": OpenAIResponsesAdapter(MacOSKeychainSecretStore())}),
        anti_junk,
    )
    router.include_router(build_launch_router(data_dir, require_token, launch_gateway))

    def raise_http(exc: PilotError) -> None:
        if isinstance(exc, PilotNotFound):
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        if isinstance(exc, PilotGateError):
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/api/projects/{book_id}/pilots")
    def start_pilot(book_id: str, payload: PilotStartRequest) -> dict[str, object]:
        try:
            return service.start(book_id, human_actor=payload.human_actor).model_dump(mode="json")
        except PilotError as exc:
            raise_http(exc)
        raise AssertionError("unreachable")

    @router.get("/api/projects/{book_id}/pilots/active")
    def active_pilot(book_id: str) -> dict[str, object] | None:
        try:
            active = service.active(book_id)
            return active.model_dump(mode="json") if active is not None else None
        except PilotError as exc:
            raise_http(exc)
        raise AssertionError("unreachable")

    @router.get("/api/projects/{book_id}/pilots/{pilot_id}")
    def get_pilot(book_id: str, pilot_id: str) -> dict[str, object]:
        try:
            return service.get(book_id, pilot_id).model_dump(mode="json")
        except PilotError as exc:
            raise_http(exc)
        raise AssertionError("unreachable")

    @router.post("/api/projects/{book_id}/pilots/{pilot_id}/stage-events")
    def record_stage_event(
        book_id: str, pilot_id: str, payload: PilotStageEventRequest
    ) -> dict[str, object]:
        try:
            return service.record_stage_event(book_id, pilot_id, payload).model_dump(mode="json")
        except PilotError as exc:
            raise_http(exc)
        raise AssertionError("unreachable")

    @router.get("/api/projects/{book_id}/pilots/{pilot_id}/observations")
    def list_observations(
        book_id: str, pilot_id: str, open_only: bool = Query(default=False)
    ) -> list[dict[str, object]]:
        try:
            return [
                item.model_dump(mode="json")
                for item in service.list_observations(book_id, pilot_id, open_only=open_only)
            ]
        except PilotError as exc:
            raise_http(exc)
        raise AssertionError("unreachable")

    @router.post("/api/projects/{book_id}/pilots/{pilot_id}/observations")
    def add_observation(
        book_id: str, pilot_id: str, payload: PilotObservationRequest
    ) -> dict[str, object]:
        try:
            return service.add_observation(book_id, pilot_id, payload).model_dump(mode="json")
        except PilotError as exc:
            raise_http(exc)
        raise AssertionError("unreachable")

    @router.post("/api/projects/{book_id}/pilots/{pilot_id}/observations/{observation_id}/resolve")
    def resolve_observation(
        book_id: str,
        pilot_id: str,
        observation_id: str,
        payload: PilotObservationResolutionRequest,
    ) -> dict[str, object]:
        try:
            return service.resolve_observation(
                book_id,
                pilot_id,
                observation_id,
                actor=payload.actor,
                actor_kind=payload.actor_kind,
                reason=payload.reason,
            ).model_dump(mode="json")
        except PilotError as exc:
            raise_http(exc)
        raise AssertionError("unreachable")

    @router.get("/api/projects/{book_id}/pilots/{pilot_id}/summary")
    def pilot_summary(book_id: str, pilot_id: str) -> dict[str, object]:
        try:
            return service.summary(book_id, pilot_id).model_dump(mode="json")
        except PilotError as exc:
            raise_http(exc)
        raise AssertionError("unreachable")

    @router.post("/api/projects/{book_id}/pilots/{pilot_id}/openai-preflight")
    def openai_preflight(
        book_id: str, pilot_id: str, payload: OpenAIPreflightRequest
    ) -> dict[str, object]:
        try:
            service.get(book_id, pilot_id)
            return service.openai_preflight(
                MacOSKeychainSecretStore(),
                book_id=book_id,
                pilot_id=pilot_id,
                writer_model=payload.writer_model,
                evaluator_model=payload.evaluator_model,
                editor_lane=payload.editor_lane,
                max_requests=payload.max_requests,
                max_input_tokens=payload.max_input_tokens,
                max_output_tokens=payload.max_output_tokens,
                max_cost_usd=payload.max_cost_usd,
            ).model_dump(mode="json")
        except PilotError as exc:
            raise_http(exc)
        raise AssertionError("unreachable")

    @router.post("/api/projects/{book_id}/pilots/{pilot_id}/final-decision")
    def final_decision(
        book_id: str, pilot_id: str, payload: PilotFinalDecisionRequest
    ) -> dict[str, object]:
        try:
            return service.record_final_decision(
                book_id,
                pilot_id,
                decision=payload.decision,
                actor=payload.actor,
                actor_kind=payload.actor_kind,
                reason=payload.reason,
            ).model_dump(mode="json")
        except PilotError as exc:
            raise_http(exc)
        raise AssertionError("unreachable")

    return router
