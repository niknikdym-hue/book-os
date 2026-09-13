from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import threading

from fastapi import APIRouter, Depends, HTTPException
import httpx
from pydantic import BaseModel, Field

from .auto_book import (
    AutoBookError,
    AutoBookGateError,
    AutoBookNotFound,
    AutoBookRunView,
    AutoBookService,
    AutoBookStartRequest,
)
from .auto_book_finalizer import AutoBookFinalizer
from .auto_book_runtime import AutoBookRuntimeError
from .book_costs import BookCostService
from .audio_script import (
    AudioScriptContent,
    AudioScriptError,
    AudioScriptGateError,
    AudioScriptService,
)
from .book_context import BookContextService
from .model_gateway import BookConceptProposalOutput, ModelGateway
from .research_adapters import ResearchGateway
from .series_workspace import SeriesWorkspaceGateError, SeriesWorkspaceService


class AutoBookChangeRequest(BaseModel):
    request_text: str = Field(min_length=1, max_length=12000)


class AutoBookConceptApprovalRequest(BaseModel):
    concept: BookConceptProposalOutput | None = None


class AutoBookConceptAlternativeRequest(BaseModel):
    feedback: str = Field(default="", max_length=4000)


class AudioScriptApprovalRequest(BaseModel):
    human_actor: str = Field(min_length=1, max_length=300)
    accepted_attention_codes: list[str] = Field(default_factory=list, max_length=100)


class AutoBookAudioRevisionRequest(BaseModel):
    content: AudioScriptContent
    human_actor: str = Field(min_length=1, max_length=300)
    change_summary: str = Field(min_length=3, max_length=4000)


def build_auto_book_router(
    data_dir: Path,
    require_token: Callable[..., None],
    gateway: ModelGateway,
    research_gateway: ResearchGateway | None = None,
) -> APIRouter:
    service = AutoBookService(data_dir, gateway, research_gateway)
    finalizer = AutoBookFinalizer(data_dir, gateway)
    audio_scripts = AudioScriptService(data_dir)
    contexts = BookContextService(data_dir)
    series_workspaces = SeriesWorkspaceService(data_dir)
    costs = BookCostService(data_dir)
    router = APIRouter(dependencies=[Depends(require_token)])
    workers_lock = threading.Lock()
    workers: dict[str, threading.Thread] = {}

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
        The uncertain call is conservatively reserved against the owner-authorized budget before the
        run is exposed as resumable.
        """

        state = service.get(book_id)
        if state is not None:
            try:
                uncertain_cap = service._remaining_call_cap(state)
            except AutoBookError:
                uncertain_cap = None
            if uncertain_cap is not None:
                service._consume_call(state, uncertain_cap)
            state.status = "RUNNING"
            state.error = str(exc)
            state.last_action = "Temporary model connection interruption; progress and budget saved"
            service._write(state)
        raise HTTPException(
            status_code=503,
            detail=(
                "Временный обрыв связи с моделью. Прогресс Auto Book сохранён, а возможная "
                "стоимость прерванного запроса учтена в лимите. Нажмите «Продолжить с "
                "сохранённого места»."
            ),
        ) from exc

    def stop_after_uncertain_provider_disconnect(book_id: str, exc: Exception) -> None:
        state = service.get(book_id)
        if state is None:
            return
        try:
            uncertain_cap = service._remaining_call_cap(state)
        except AutoBookError:
            uncertain_cap = 0.0
        if uncertain_cap > 0:
            service._consume_call(state, uncertain_cap)
            state.unknown_cost_usd = round(state.unknown_cost_usd + uncertain_cap, 6)
        state.status = "STOPPED"
        state.error = str(exc)
        state.last_action = (
            "Исход запроса неизвестен; автоматический повтор заблокирован до проверки"
        )
        service._write(state)

    def drive_in_local_core(book_id: str) -> None:
        try:
            for _ in range(500):
                current = service.get(book_id)
                if current is None or current.status != "RUNNING":
                    return
                if finalization_complete(current):
                    return
                require_series_writing_gate(book_id, current)
                advanced = service.advance(book_id)
                finalize_if_needed(book_id, advanced)
        except httpx.TransportError as exc:
            stop_after_uncertain_provider_disconnect(book_id, exc)
        except Exception as exc:
            current = service.get(book_id)
            if current is not None:
                current.status = "FAILED"
                current.error = str(exc)
                current.last_action = "Local Core остановил Auto Book на проверяемой ошибке"
                service._write(current)
        finally:
            with workers_lock:
                workers.pop(book_id, None)

    def schedule_local_core(book_id: str) -> None:
        with workers_lock:
            existing = workers.get(book_id)
            if existing is not None and existing.is_alive():
                return
            worker = threading.Thread(
                target=drive_in_local_core,
                args=(book_id,),
                name=f"book-os-auto-{book_id[-6:]}",
                daemon=True,
            )
            workers[book_id] = worker
            worker.start()

    def require_series_writing_gate(book_id: str, state: AutoBookRunView) -> None:
        if state.phase != "CHAPTER_DRAFT" or state.current_chapter_id is None:
            return
        context = contexts.get_context(book_id)
        if context.series_profile is None:
            return
        try:
            if series_workspaces.books(context.series_profile.profile_id):
                series_workspaces.require_current_map(context.series_profile.profile_id)
        except SeriesWorkspaceGateError as exc:
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
        except httpx.TransportError:
            if draft_output is not None:
                draft_output.unlink(missing_ok=True)
            state.status = "RUNNING"
            state.phase = "EXPORT"
            state.output_path = None
            service._write(state)
            raise
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
        state.output_files = result.output_files
        state.audio_script_id = result.audio_script_id
        state.error = None
        if result.awaiting_audio_approval:
            state.status = "AWAITING_AUDIO_APPROVAL"
            state.phase = "EXPORT"
            state.last_action = (
                "AudioScript подготовлен отдельно от рукописи и ждёт утверждения человеком"
            )
        else:
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
        except AutoBookRuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except AutoBookError as exc:
            raise_http(exc)
        raise AssertionError("unreachable")

    @router.get("/api/projects/{book_id}/auto-book/costs")
    def get_auto_book_costs(book_id: str) -> dict[str, object] | None:
        try:
            result = costs.get(book_id)
            return result.model_dump(mode="json") if result is not None else None
        except AutoBookRuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

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
        except httpx.TransportError as exc:
            pause_after_provider_disconnect(book_id, exc)
        except AutoBookError as exc:
            raise_http(exc)
        raise AssertionError("unreachable")

    @router.post("/api/projects/{book_id}/auto-book/concept/approve")
    def approve_auto_book_concept(
        book_id: str, payload: AutoBookConceptApprovalRequest
    ) -> dict[str, object]:
        try:
            return service.accept_concept(book_id, payload.concept).model_dump(mode="json")
        except AutoBookError as exc:
            raise_http(exc)
        raise AssertionError("unreachable")

    @router.post("/api/projects/{book_id}/auto-book/concept/alternative")
    def request_auto_book_concept_alternative(
        book_id: str, payload: AutoBookConceptAlternativeRequest
    ) -> dict[str, object]:
        try:
            return service.request_another_concept(book_id, payload.feedback).model_dump(
                mode="json"
            )
        except AutoBookError as exc:
            raise_http(exc)
        raise AssertionError("unreachable")

    @router.post("/api/projects/{book_id}/auto-book/resume")
    def resume_auto_book(book_id: str) -> dict[str, object]:
        try:
            current = service.get(book_id)
            if current is None:
                raise AutoBookNotFound("Auto Book has not been started for this book")
            if current.unknown_cost_usd > 0:
                raise AutoBookGateError(
                    "Нельзя слепо повторить запрос с неизвестным платным исходом; "
                    "сначала проверьте provider run в диагностике"
                )
            if current.status == "STOPPED":
                current.status = "RUNNING"
                current.error = None
                current.last_action = "Local Core продолжает с сохранённого checkpoint"
                service._write(current)
            if current.status == "RUNNING":
                schedule_local_core(book_id)
            return current.model_dump(mode="json")
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

    @router.post("/api/projects/{book_id}/auto-book/changes")
    def request_auto_book_change(
        book_id: str,
        payload: AutoBookChangeRequest,
    ) -> dict[str, object]:
        try:
            current = service.get(book_id)
            if current is None:
                raise AutoBookNotFound("Auto Book has not been started for this book")
            change_id = service.runtime.request_change(
                book_id,
                current.run_id,
                payload.request_text,
            )
            return {
                "change_id": change_id,
                "status": "SAVED",
                "message": (
                    "Запрос сохранён. BOOK OS обновит только затронутые части и зависимые проверки."
                ),
            }
        except AutoBookRuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except AutoBookError as exc:
            raise_http(exc)
        raise AssertionError("unreachable")

    @router.get("/api/projects/{book_id}/auto-book/audio-script")
    def get_auto_book_audio_script(book_id: str) -> dict[str, object] | None:
        current = service.get(book_id)
        if current is None or current.audio_script_id is None:
            return None
        try:
            return audio_scripts.get(book_id, current.audio_script_id).model_dump(mode="json")
        except AudioScriptError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post("/api/projects/{book_id}/auto-book/audio-script/approve")
    def approve_auto_book_audio_script(
        book_id: str,
        payload: AudioScriptApprovalRequest,
    ) -> dict[str, object]:
        current = service.get(book_id)
        if current is None or current.audio_script_id is None:
            raise HTTPException(status_code=404, detail="AudioScript has not been prepared")
        if current.status != "AWAITING_AUDIO_APPROVAL":
            raise HTTPException(status_code=409, detail="Auto Book is not awaiting audio approval")
        try:
            approved = audio_scripts.approve(
                book_id,
                current.audio_script_id,
                human_actor=payload.human_actor,
                accepted_attention_codes=payload.accepted_attention_codes,
            )
            result = finalizer.complete_audio_outputs(book_id, current, approved)
        except (AudioScriptGateError, AutoBookError, AutoBookRuntimeError) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        current.status = "DONE"
        current.phase = "DONE"
        current.output_files = result.output_files
        current.error = None
        current.last_action = "AudioScript утверждён человеком; аудиофайлы и handoff готовы"
        return service._write(current).model_dump(mode="json")

    @router.put("/api/projects/{book_id}/auto-book/audio-script")
    def revise_auto_book_audio_script(
        book_id: str,
        payload: AutoBookAudioRevisionRequest,
    ) -> dict[str, object]:
        current = service.get(book_id)
        if current is None or current.audio_script_id is None:
            raise HTTPException(status_code=404, detail="AudioScript has not been prepared")
        if current.status != "AWAITING_AUDIO_APPROVAL":
            raise HTTPException(status_code=409, detail="Auto Book is not awaiting audio revision")
        try:
            revised = audio_scripts.revise_by_human(
                book_id,
                current.audio_script_id,
                content=payload.content,
                human_actor=payload.human_actor,
                change_summary=payload.change_summary,
            )
        except AudioScriptError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        current.audio_script_id = revised.audio_script_id
        current.last_action = "AudioScript исправлен как новая версия и повторно проверен"
        service._write(current)
        return revised.model_dump(mode="json")

    return router
