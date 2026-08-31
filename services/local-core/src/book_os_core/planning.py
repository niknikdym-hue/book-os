from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, cast

from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import text
from sqlalchemy.engine import Engine

from .authority import new_ulid
from .authority_types import utc_now
from .db import create_database
from .model_gateway import (
    ArchitectureChapterProposalOutput,
    AuthorityInputRef,
    BookArchitectureProposalOutput,
    BookContractProposalOutput,
    ChapterContractProposalOutput,
    ModelGateway,
    ModelOutputError,
    ModelTaskRequest,
)
from .projects import (
    BookArchitecturePayload,
    BookContractPayload,
    ChapterContractPayload,
    ProjectService,
    ProjectView,
)
from .prompts import (
    ARCHITECTURE_PROPOSAL_V1,
    BOOK_CONTRACT_PROPOSAL_V1,
    CHAPTER_CONTRACT_PROPOSAL_V1,
    PromptTemplate,
)


class PlanningError(RuntimeError):
    pass


class PlanningGateError(PlanningError):
    pass


class BookContractPlanningRequest(BaseModel):
    idea: str = Field(min_length=3, max_length=6000)
    reader_hint: str = Field(default="", max_length=4000)
    provider: str = "openai"
    model: str | None = None
    max_output_tokens: int = Field(default=2600, ge=500, le=8000)
    max_cost_usd: float = Field(gt=0)


class ArchitecturePlanningRequest(BaseModel):
    planning_note: str = Field(default="", max_length=4000)
    provider: str = "openai"
    model: str | None = None
    max_output_tokens: int = Field(default=5000, ge=1000, le=12000)
    max_cost_usd: float = Field(gt=0)


class ChapterContractPlanningRequest(BaseModel):
    planning_note: str = Field(default="", max_length=4000)
    provider: str = "openai"
    model: str | None = None
    max_output_tokens: int = Field(default=3200, ge=500, le=8000)
    max_cost_usd: float = Field(gt=0)


class PlanningProposalView(BaseModel):
    run_id: str
    run_kind: str
    provider: str
    model: str
    provider_run_id: str | None
    prompt_id: str
    prompt_version: str
    prompt_hash: str
    usage: dict[str, Any]
    status: str
    project: ProjectView


class PlanningService:
    def __init__(self, data_dir: Path, gateway: ModelGateway):
        self.projects = ProjectService(data_dir)
        self.gateway = gateway

    def _engine(self, book_id: str) -> Engine:
        self.projects.get_project(book_id)
        return create_database(self.projects.projects_dir / book_id / "project.sqlite")

    @staticmethod
    def _resolved_model(provider: str, model: str | None) -> str:
        if model and model.strip():
            return model.strip()
        if provider == "openai":
            configured = os.environ.get("BOOK_OS_OPENAI_MODEL", "").strip()
            if configured:
                return configured
        raise PlanningGateError("model must be explicitly selected/configured")

    @staticmethod
    def _dump(value: object) -> str:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    def _start_run(
        self,
        engine: Engine,
        *,
        run_id: str,
        book_id: str,
        chapter_id: str | None,
        run_kind: str,
        provider: str,
        model: str,
        prompt: PromptTemplate,
        request_payload: dict[str, Any],
        max_output_tokens: int,
        max_cost_usd: float,
    ) -> None:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO planning_runs(run_id,book_id,chapter_id,run_kind,provider,model,"
                    "prompt_id,prompt_version,prompt_hash,request_json,usage_json,max_output_tokens,"
                    "max_cost_usd,status,created_at) VALUES (:run_id,:book_id,:chapter_id,:run_kind,"
                    ":provider,:model,:prompt_id,:prompt_version,:prompt_hash,:request_json,'{}',"
                    ":max_output_tokens,:max_cost_usd,'RUNNING',:created_at)"
                ),
                {
                    "run_id": run_id,
                    "book_id": book_id,
                    "chapter_id": chapter_id,
                    "run_kind": run_kind,
                    "provider": provider,
                    "model": model,
                    "prompt_id": prompt.prompt_id,
                    "prompt_version": prompt.version,
                    "prompt_hash": prompt.prompt_hash,
                    "request_json": self._dump(request_payload),
                    "max_output_tokens": max_output_tokens,
                    "max_cost_usd": max_cost_usd,
                    "created_at": utc_now(),
                },
            )

    def _finish_run(
        self,
        engine: Engine,
        run_id: str,
        *,
        output: dict[str, Any] | None,
        usage: dict[str, Any] | None,
        provider_run_id: str | None,
        error: Exception | None,
    ) -> None:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE planning_runs SET status=:status,provider_run_id=:provider_run_id,"
                    "output_json=:output_json,usage_json=:usage_json,error_message=:error_message,"
                    "completed_at=:completed_at WHERE run_id=:run_id"
                ),
                {
                    "status": "FAILED" if error else "SUCCEEDED",
                    "provider_run_id": provider_run_id,
                    "output_json": self._dump(output) if output is not None else None,
                    "usage_json": self._dump(usage or {}),
                    "error_message": str(error)[:2000] if error else None,
                    "completed_at": utc_now(),
                    "run_id": run_id,
                },
            )

    def _run(
        self,
        *,
        book_id: str,
        chapter_id: str | None,
        run_kind: str,
        provider: str,
        model: str,
        prompt: PromptTemplate,
        objective: str,
        authority_inputs: list[AuthorityInputRef],
        authoritative_context: dict[str, Any],
        request_payload: dict[str, Any],
        max_output_tokens: int,
        max_cost_usd: float,
    ) -> tuple[str, dict[str, Any], dict[str, Any], str | None]:
        engine = self._engine(book_id)
        run_id = new_ulid()
        self._start_run(
            engine,
            run_id=run_id,
            book_id=book_id,
            chapter_id=chapter_id,
            run_kind=run_kind,
            provider=provider,
            model=model,
            prompt=prompt,
            request_payload=request_payload,
            max_output_tokens=max_output_tokens,
            max_cost_usd=max_cost_usd,
        )
        try:
            result = self.gateway.generate(
                ModelTaskRequest(
                    task_id=run_id,
                    task_type=cast(Any, run_kind),
                    role="PLANNER",
                    provider=provider,
                    model=model,
                    prompt_id=prompt.prompt_id,
                    prompt_version=prompt.version,
                    prompt_hash=prompt.prompt_hash,
                    section_objective=objective,
                    authority_inputs=authority_inputs,
                    authoritative_context=authoritative_context,
                    max_output_tokens=max_output_tokens,
                    max_cost_usd=max_cost_usd,
                ),
                prompt,
            )
            self._finish_run(
                engine,
                run_id,
                output=result.output,
                usage=result.usage,
                provider_run_id=result.provider_run_id,
                error=None,
            )
            return run_id, result.output, result.usage, result.provider_run_id
        except Exception as exc:
            self._finish_run(
                engine,
                run_id,
                output=None,
                usage=None,
                provider_run_id=None,
                error=exc,
            )
            raise
        finally:
            engine.dispose()

    def propose_book_contract(
        self, book_id: str, request: BookContractPlanningRequest
    ) -> PlanningProposalView:
        project = self.projects.get_project(book_id)
        model = self._resolved_model(request.provider, request.model)
        objective = f"Сформировать Book Contract для идеи: {request.idea.strip()}"
        run_id, raw, usage, provider_run_id = self._run(
            book_id=book_id,
            chapter_id=None,
            run_kind="BOOK_CONTRACT_PROPOSAL",
            provider=request.provider,
            model=model,
            prompt=BOOK_CONTRACT_PROPOSAL_V1,
            objective=objective,
            authority_inputs=[],
            authoritative_context={
                "project": {
                    "working_title": project.working_title,
                    "domain": project.domain,
                    "primary_subtype": project.primary_subtype,
                    "secondary_subtype": project.secondary_subtype,
                },
                "idea": request.idea.strip(),
                "reader_hint": request.reader_hint.strip(),
            },
            request_payload=request.model_dump(mode="json"),
            max_output_tokens=request.max_output_tokens,
            max_cost_usd=request.max_cost_usd,
        )
        try:
            proposal = BookContractProposalOutput.model_validate(raw)
            payload = BookContractPayload.model_validate(proposal.model_dump(mode="json"))
        except ValidationError as exc:
            raise ModelOutputError(
                "Book Contract proposal failed project schema validation"
            ) from exc
        updated = self.projects.save_book_contract(book_id, payload)
        return PlanningProposalView(
            run_id=run_id,
            run_kind="BOOK_CONTRACT_PROPOSAL",
            provider=request.provider,
            model=model,
            provider_run_id=provider_run_id,
            prompt_id=BOOK_CONTRACT_PROPOSAL_V1.prompt_id,
            prompt_version=BOOK_CONTRACT_PROPOSAL_V1.version,
            prompt_hash=BOOK_CONTRACT_PROPOSAL_V1.prompt_hash,
            usage=usage,
            status="SUCCEEDED",
            project=updated,
        )

    def propose_architecture(
        self, book_id: str, request: ArchitecturePlanningRequest
    ) -> PlanningProposalView:
        project = self.projects.get_project(book_id)
        contract = project.book_contract
        if contract is None or contract.authority_status not in {"APPROVED", "LOCKED"}:
            raise PlanningGateError("Book Contract must be approved before architecture planning")
        model = self._resolved_model(request.provider, request.model)
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                revision_hash = connection.execute(
                    text("SELECT content_hash FROM revisions WHERE revision_id=:revision_id"),
                    {"revision_id": contract.authority_revision_id},
                ).scalar_one()
        finally:
            engine.dispose()
        authority_inputs = [
            AuthorityInputRef(
                revision_id=contract.authority_revision_id,
                revision_hash=str(revision_hash),
                entity_type="book.contract",
            )
        ]
        run_id, raw, usage, provider_run_id = self._run(
            book_id=book_id,
            chapter_id=None,
            run_kind="ARCHITECTURE_PROPOSAL",
            provider=request.provider,
            model=model,
            prompt=ARCHITECTURE_PROPOSAL_V1,
            objective="Сформировать архитектуру книги по утверждённому Book Contract",
            authority_inputs=authority_inputs,
            authoritative_context={
                "project": {
                    "working_title": project.working_title,
                    "primary_subtype": project.primary_subtype,
                },
                "approved_book_contract": contract.content,
                "planning_note": request.planning_note.strip(),
            },
            request_payload=request.model_dump(mode="json"),
            max_output_tokens=request.max_output_tokens,
            max_cost_usd=request.max_cost_usd,
        )
        try:
            proposal = BookArchitectureProposalOutput.model_validate(raw)
            payload = BookArchitecturePayload(
                parts=[
                    {
                        "title": part.title,
                        "purpose": part.purpose,
                        "chapters": [
                            {
                                **ArchitectureChapterProposalOutput.model_validate(
                                    chapter
                                ).model_dump(mode="json"),
                                "chapter_id": None,
                            }
                            for chapter in part.chapters
                        ],
                    }
                    for part in proposal.parts
                ],
                intellectual_progression=proposal.intellectual_progression,
                concept_allocation=proposal.concept_allocation,
                promise_thesis_coverage=proposal.promise_thesis_coverage,
                major_transitions=proposal.major_transitions,
            )
        except ValidationError as exc:
            raise ModelOutputError(
                "Architecture proposal failed project schema validation"
            ) from exc
        updated = self.projects.save_architecture(book_id, payload)
        return PlanningProposalView(
            run_id=run_id,
            run_kind="ARCHITECTURE_PROPOSAL",
            provider=request.provider,
            model=model,
            provider_run_id=provider_run_id,
            prompt_id=ARCHITECTURE_PROPOSAL_V1.prompt_id,
            prompt_version=ARCHITECTURE_PROPOSAL_V1.version,
            prompt_hash=ARCHITECTURE_PROPOSAL_V1.prompt_hash,
            usage=usage,
            status="SUCCEEDED",
            project=updated,
        )

    def propose_chapter_contract(
        self, book_id: str, chapter_id: str, request: ChapterContractPlanningRequest
    ) -> PlanningProposalView:
        project = self.projects.get_project(book_id)
        contract = project.book_contract
        architecture = project.architecture
        if contract is None or contract.authority_status not in {"APPROVED", "LOCKED"}:
            raise PlanningGateError(
                "Book Contract must be approved before Chapter Contract planning"
            )
        if architecture is None or architecture.authority_status not in {"APPROVED", "LOCKED"}:
            raise PlanningGateError(
                "Architecture must be approved before Chapter Contract planning"
            )
        chapter = next((item for item in project.chapters if item.chapter_id == chapter_id), None)
        if chapter is None:
            raise PlanningGateError("chapter is not in the current approved architecture")
        model = self._resolved_model(request.provider, request.model)
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                rows = connection.execute(
                    text(
                        "SELECT revision_id,content_hash FROM revisions WHERE revision_id IN "
                        "(:contract_revision,:architecture_revision)"
                    ),
                    {
                        "contract_revision": contract.authority_revision_id,
                        "architecture_revision": architecture.authority_revision_id,
                    },
                ).mappings()
                hashes = {str(row["revision_id"]): str(row["content_hash"]) for row in rows}
        finally:
            engine.dispose()
        authority_inputs = [
            AuthorityInputRef(
                revision_id=contract.authority_revision_id,
                revision_hash=hashes[contract.authority_revision_id],
                entity_type="book.contract",
            ),
            AuthorityInputRef(
                revision_id=architecture.authority_revision_id,
                revision_hash=hashes[architecture.authority_revision_id],
                entity_type="book.architecture",
            ),
        ]
        run_id, raw, usage, provider_run_id = self._run(
            book_id=book_id,
            chapter_id=chapter_id,
            run_kind="CHAPTER_CONTRACT_PROPOSAL",
            provider=request.provider,
            model=model,
            prompt=CHAPTER_CONTRACT_PROPOSAL_V1,
            objective=f"Сформировать Chapter Contract для главы {chapter.ordinal}: {chapter.working_title}",
            authority_inputs=authority_inputs,
            authoritative_context={
                "approved_book_contract": contract.content,
                "approved_architecture": architecture.content,
                "selected_chapter": chapter.model_dump(mode="json", exclude={"chapter_contract"}),
                "planning_note": request.planning_note.strip(),
            },
            request_payload=request.model_dump(mode="json"),
            max_output_tokens=request.max_output_tokens,
            max_cost_usd=request.max_cost_usd,
        )
        try:
            proposal = ChapterContractProposalOutput.model_validate(raw)
            payload = ChapterContractPayload.model_validate(proposal.model_dump(mode="json"))
        except ValidationError as exc:
            raise ModelOutputError(
                "Chapter Contract proposal failed project schema validation"
            ) from exc
        updated = self.projects.save_chapter_contract(book_id, chapter_id, payload)
        return PlanningProposalView(
            run_id=run_id,
            run_kind="CHAPTER_CONTRACT_PROPOSAL",
            provider=request.provider,
            model=model,
            provider_run_id=provider_run_id,
            prompt_id=CHAPTER_CONTRACT_PROPOSAL_V1.prompt_id,
            prompt_version=CHAPTER_CONTRACT_PROPOSAL_V1.version,
            prompt_hash=CHAPTER_CONTRACT_PROPOSAL_V1.prompt_hash,
            usage=usage,
            status="SUCCEEDED",
            project=updated,
        )
