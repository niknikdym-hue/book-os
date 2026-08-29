from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, cast

from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import text
from sqlalchemy.engine import Engine

from .authority import AuthorityService, canonical_json, content_hash, new_ulid
from .authority_types import JSONValue, utc_now
from .db import create_database
from .model_gateway import (
    AuthorityInputRef,
    ModelAdapterResult,
    ModelGateway,
    ModelOutputError,
    ModelTaskRequest,
    SectionDraftOutput,
)
from .prompts import SECTION_DRAFT_V1
from .projects import ProjectService


class DraftingError(RuntimeError):
    pass


class DraftingGateError(DraftingError):
    pass


class DraftSectionRequest(BaseModel):
    section_objective: str = Field(min_length=1, max_length=4000)
    provider: str = "openai"
    model: str | None = None
    untrusted_context: list[str] = Field(default_factory=list)
    max_output_tokens: int = Field(default=3500, ge=100, le=12000)
    max_cost_usd: float | None = Field(default=None, ge=0)


class DraftRunView(BaseModel):
    task_id: str
    run_id: str
    task_status: str
    run_status: str
    provider: str
    model: str
    prompt_id: str
    prompt_version: str
    prompt_hash: str
    input_revision_id: str
    input_revision_hash: str
    unit_id: str | None = None
    revision_id: str | None = None
    revision_hash: str | None = None
    revision_status: str | None = None
    text: str | None = None
    notes: list[str] = Field(default_factory=list)
    provider_run_id: str | None = None
    usage: dict[str, Any] = Field(default_factory=dict)
    error_code: str | None = None
    error_message: str | None = None


class DraftingService:
    def __init__(self, data_dir: Path, gateway: ModelGateway):
        self._projects = ProjectService(data_dir)
        self._gateway = gateway

    def _engine(self, book_id: str) -> Engine:
        self._projects.get_project(book_id)
        return create_database(self._projects.projects_dir / book_id / "project.sqlite")

    @staticmethod
    def _resolved_model(request: DraftSectionRequest) -> str:
        if request.model and request.model.strip():
            return request.model.strip()
        if request.provider == "openai":
            configured = os.environ.get("BOOK_OS_OPENAI_MODEL", "").strip()
            if configured:
                return configured
        raise DraftingGateError("model must be explicitly selected/configured")

    def generate_section_draft(
        self, book_id: str, chapter_id: str, request: DraftSectionRequest
    ) -> DraftRunView:
        engine = self._engine(book_id)
        authority = AuthorityService(engine)
        prompt = SECTION_DRAFT_V1
        model = self._resolved_model(request)
        now = utc_now()
        task_id = new_ulid()
        run_id = new_ulid()
        try:
            with engine.connect() as connection:
                chapter = (
                    connection.execute(
                        text(
                            "SELECT chapter_contract_entity_id,workflow_state FROM chapters "
                            "WHERE book_id=:book_id AND chapter_id=:chapter_id"
                        ),
                        {"book_id": book_id, "chapter_id": chapter_id},
                    )
                    .mappings()
                    .one_or_none()
                )
            if chapter is None or chapter["workflow_state"] == "SUPERSEDED":
                raise DraftingGateError("chapter is not in the current project architecture")
            contract_entity_id = cast(str | None, chapter["chapter_contract_entity_id"])
            if contract_entity_id is None:
                raise DraftingGateError("Chapter Contract must be approved before drafting")
            contract_head = authority.get_head(contract_entity_id)
            if contract_head.status not in {"APPROVED", "LOCKED"}:
                raise DraftingGateError("Chapter Contract must be approved before drafting")
            contract_revision = authority.get_revision(contract_head.revision_id)
            contract_content = cast(dict[str, Any], contract_revision["content"])

            with engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT INTO bounded_tasks("
                        "task_id,book_id,chapter_id,task_type,role,input_revision_id,input_revision_hash,"
                        "prompt_id,prompt_version,prompt_hash,section_objective,untrusted_context_json,"
                        "max_output_tokens,max_cost_usd,status,created_at,started_at) VALUES "
                        "(:task_id,:book_id,:chapter_id,'SECTION_DRAFT',"
                        "'WRITER',:revision_id,:revision_hash,:prompt_id,:prompt_version,:prompt_hash,"
                        ":objective,:untrusted_context,:max_output_tokens,:max_cost_usd,'RUNNING',"
                        ":created_at,:started_at)"
                    ),
                    {
                        "task_id": task_id,
                        "book_id": book_id,
                        "chapter_id": chapter_id,
                        "revision_id": contract_head.revision_id,
                        "revision_hash": contract_head.revision_hash,
                        "prompt_id": prompt.prompt_id,
                        "prompt_version": prompt.version,
                        "prompt_hash": prompt.prompt_hash,
                        "objective": request.section_objective,
                        "untrusted_context": canonical_json(
                            {"items": cast(list[JSONValue], request.untrusted_context)}
                        ),
                        "max_output_tokens": request.max_output_tokens,
                        "max_cost_usd": request.max_cost_usd,
                        "created_at": now,
                        "started_at": now,
                    },
                )
                connection.execute(
                    text(
                        "INSERT INTO model_runs(run_id,task_id,provider,model,status,prompt_id,"
                        "prompt_version,prompt_hash,usage_json,created_at) VALUES (:run_id,:task_id,"
                        ":provider,:model,'RUNNING',:prompt_id,:prompt_version,:prompt_hash,'{}',:created_at)"
                    ),
                    {
                        "run_id": run_id,
                        "task_id": task_id,
                        "provider": request.provider,
                        "model": model,
                        "prompt_id": prompt.prompt_id,
                        "prompt_version": prompt.version,
                        "prompt_hash": prompt.prompt_hash,
                        "created_at": now,
                    },
                )

            model_request = ModelTaskRequest(
                task_id=task_id,
                task_type="SECTION_DRAFT",
                role="WRITER",
                provider=request.provider,
                model=model,
                prompt_id=prompt.prompt_id,
                prompt_version=prompt.version,
                prompt_hash=prompt.prompt_hash,
                section_objective=request.section_objective,
                authority_inputs=[
                    AuthorityInputRef(
                        revision_id=contract_head.revision_id,
                        revision_hash=contract_head.revision_hash,
                        entity_type="chapter.contract",
                    )
                ],
                authoritative_context={"chapter_contract": contract_content},
                untrusted_context=request.untrusted_context,
                max_output_tokens=request.max_output_tokens,
                max_cost_usd=request.max_cost_usd,
            )

            result = self._gateway.generate(model_request, prompt)
            try:
                output = SectionDraftOutput.model_validate(result.output)
            except ValidationError as exc:
                raise ModelOutputError(
                    "model output failed SectionDraft schema validation"
                ) from exc

            latest_head = authority.get_head(contract_entity_id)
            if (
                latest_head.revision_id != contract_head.revision_id
                or latest_head.revision_hash != contract_head.revision_hash
                or latest_head.status not in {"APPROVED", "LOCKED"}
            ):
                raise DraftingGateError(
                    "Chapter Contract authority changed while drafting; result discarded"
                )

            return self._persist_success(
                engine,
                book_id=book_id,
                chapter_id=chapter_id,
                task_id=task_id,
                run_id=run_id,
                model_request=model_request,
                result=result,
                output=output,
            )
        except Exception as exc:
            self._persist_failure(engine, task_id, run_id, exc)
            raise
        finally:
            engine.dispose()

    def _persist_success(
        self,
        engine: Engine,
        *,
        book_id: str,
        chapter_id: str,
        task_id: str,
        run_id: str,
        model_request: ModelTaskRequest,
        result: ModelAdapterResult,
        output: SectionDraftOutput,
    ) -> DraftRunView:
        now = utc_now()
        unit_id = new_ulid()
        entity_id = new_ulid()
        revision_id = new_ulid()
        provenance_id = new_ulid()
        revision_payload: dict[str, JSONValue] = {
            "chapter_id": chapter_id,
            "section_objective": model_request.section_objective,
            "text": output.text,
            "notes": cast(list[JSONValue], output.notes),
        }
        serialized = canonical_json(revision_payload)
        digest = content_hash(revision_payload)
        transformation = canonical_json(
            {
                "run_id": run_id,
                "prompt_id": model_request.prompt_id,
                "prompt_version": model_request.prompt_version,
                "prompt_hash": model_request.prompt_hash,
                "provider_run_id": result.provider_run_id,
            }
        )
        with engine.begin() as connection:
            ordinal = cast(
                int,
                connection.execute(
                    text(
                        "SELECT COALESCE(MAX(ordinal),0)+1 FROM manuscript_units "
                        "WHERE chapter_id=:chapter_id"
                    ),
                    {"chapter_id": chapter_id},
                ).scalar_one(),
            )
            connection.execute(
                text(
                    "INSERT INTO provenance_records(provenance_id,origin,actor,task_id,provider,model,"
                    "model_version,transformation_json,created_at) VALUES (:provenance_id,'AI_GENERATED',"
                    ":actor,:task_id,:provider,:model,:model_version,:transformation,:created_at)"
                ),
                {
                    "provenance_id": provenance_id,
                    "actor": f"model:{model_request.provider}",
                    "task_id": task_id,
                    "provider": model_request.provider,
                    "model": model_request.model,
                    "model_version": str(result.usage.get("model_version") or model_request.model),
                    "transformation": transformation,
                    "created_at": now,
                },
            )
            input_ref = model_request.authority_inputs[0]
            connection.execute(
                text(
                    "INSERT INTO provenance_inputs(provenance_id,revision_id) "
                    "VALUES (:provenance_id,:revision_id)"
                ),
                {"provenance_id": provenance_id, "revision_id": input_ref.revision_id},
            )
            connection.execute(
                text(
                    "INSERT INTO authority_entities(entity_id,entity_type,created_at) "
                    "VALUES (:entity_id,'manuscript.unit',:created_at)"
                ),
                {"entity_id": entity_id, "created_at": now},
            )
            connection.execute(
                text(
                    "INSERT INTO revisions(revision_id,entity_id,entity_type,schema_name,schema_version,"
                    "content_json,content_hash,provenance_id,created_at) VALUES (:revision_id,:entity_id,"
                    "'manuscript.unit','manuscript.unit.section.v0.1','1',:content_json,:content_hash,"
                    ":provenance_id,:created_at)"
                ),
                {
                    "revision_id": revision_id,
                    "entity_id": entity_id,
                    "content_json": serialized,
                    "content_hash": digest,
                    "provenance_id": provenance_id,
                    "created_at": now,
                },
            )
            connection.execute(
                text(
                    "INSERT INTO revision_status_history(status_event_id,revision_id,status,actor,reason,"
                    "created_at) VALUES (:status_event_id,:revision_id,'DRAFT',:actor,"
                    "'AI-generated bounded section draft',:created_at)"
                ),
                {
                    "status_event_id": new_ulid(),
                    "revision_id": revision_id,
                    "actor": f"model:{model_request.provider}",
                    "created_at": now,
                },
            )
            connection.execute(
                text(
                    "INSERT INTO authority_heads(entity_id,revision_id,revision_hash,updated_at) "
                    "VALUES (:entity_id,:revision_id,:revision_hash,:updated_at)"
                ),
                {
                    "entity_id": entity_id,
                    "revision_id": revision_id,
                    "revision_hash": digest,
                    "updated_at": now,
                },
            )
            connection.execute(
                text(
                    "INSERT INTO manuscript_units(unit_id,book_id,chapter_id,unit_type,ordinal,"
                    "authority_entity_id,created_at,updated_at) VALUES (:unit_id,:book_id,:chapter_id,"
                    "'SECTION',:ordinal,:entity_id,:created_at,:updated_at)"
                ),
                {
                    "unit_id": unit_id,
                    "book_id": book_id,
                    "chapter_id": chapter_id,
                    "ordinal": ordinal,
                    "entity_id": entity_id,
                    "created_at": now,
                    "updated_at": now,
                },
            )
            connection.execute(
                text(
                    "UPDATE model_runs SET status='SUCCEEDED',provider_run_id=:provider_run_id,"
                    "usage_json=:usage_json,completed_at=:completed_at WHERE run_id=:run_id"
                ),
                {
                    "provider_run_id": result.provider_run_id,
                    "usage_json": json.dumps(result.usage, ensure_ascii=False, sort_keys=True),
                    "completed_at": now,
                    "run_id": run_id,
                },
            )
            connection.execute(
                text(
                    "UPDATE bounded_tasks SET status='SUCCEEDED',output_unit_id=:unit_id,"
                    "completed_at=:completed_at WHERE task_id=:task_id"
                ),
                {"unit_id": unit_id, "completed_at": now, "task_id": task_id},
            )
        return DraftRunView(
            task_id=task_id,
            run_id=run_id,
            task_status="SUCCEEDED",
            run_status="SUCCEEDED",
            provider=model_request.provider,
            model=model_request.model,
            prompt_id=model_request.prompt_id,
            prompt_version=model_request.prompt_version,
            prompt_hash=model_request.prompt_hash,
            input_revision_id=model_request.authority_inputs[0].revision_id,
            input_revision_hash=model_request.authority_inputs[0].revision_hash,
            unit_id=unit_id,
            revision_id=revision_id,
            revision_hash=digest,
            revision_status="DRAFT",
            text=output.text,
            notes=output.notes,
            provider_run_id=result.provider_run_id,
            usage=result.usage,
        )

    @staticmethod
    def _persist_failure(engine: Engine, task_id: str, run_id: str, exc: Exception) -> None:
        now = utc_now()
        message = str(exc)[:1000]
        code = type(exc).__name__
        try:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "UPDATE model_runs SET status='FAILED',error_code=:error_code,"
                        "error_message=:error_message,completed_at=:completed_at WHERE run_id=:run_id"
                    ),
                    {
                        "error_code": code,
                        "error_message": message,
                        "completed_at": now,
                        "run_id": run_id,
                    },
                )
                connection.execute(
                    text(
                        "UPDATE bounded_tasks SET status='FAILED',completed_at=:completed_at "
                        "WHERE task_id=:task_id"
                    ),
                    {"completed_at": now, "task_id": task_id},
                )
        except Exception:
            return

    def list_drafts(self, book_id: str, chapter_id: str) -> list[DraftRunView]:
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                rows = list(
                    connection.execute(
                        text(
                            "SELECT t.task_id,t.status AS task_status,t.input_revision_id,"
                            "t.input_revision_hash,t.prompt_id,t.prompt_version,t.prompt_hash,"
                            "r.run_id,r.status AS run_status,r.provider,r.model,r.provider_run_id,"
                            "r.usage_json,r.error_code,r.error_message,t.output_unit_id,"
                            "u.authority_entity_id FROM bounded_tasks t JOIN model_runs r "
                            "ON r.task_id=t.task_id LEFT JOIN manuscript_units u "
                            "ON u.unit_id=t.output_unit_id WHERE t.book_id=:book_id "
                            "AND t.chapter_id=:chapter_id ORDER BY t.created_at DESC"
                        ),
                        {"book_id": book_id, "chapter_id": chapter_id},
                    ).mappings()
                )
            authority = AuthorityService(engine)
            results: list[DraftRunView] = []
            for row in rows:
                revision_id = None
                revision_hash = None
                revision_status = None
                text_value = None
                notes: list[str] = []
                if row["authority_entity_id"] is not None:
                    head = authority.get_head(cast(str, row["authority_entity_id"]))
                    revision = authority.get_revision(head.revision_id)
                    revision_id = head.revision_id
                    revision_hash = head.revision_hash
                    revision_status = head.status
                    content = cast(dict[str, Any], revision["content"])
                    text_value = cast(str | None, content.get("text"))
                    notes = cast(list[str], content.get("notes", []))
                results.append(
                    DraftRunView(
                        task_id=cast(str, row["task_id"]),
                        run_id=cast(str, row["run_id"]),
                        task_status=cast(str, row["task_status"]),
                        run_status=cast(str, row["run_status"]),
                        provider=cast(str, row["provider"]),
                        model=cast(str, row["model"]),
                        prompt_id=cast(str, row["prompt_id"]),
                        prompt_version=cast(str, row["prompt_version"]),
                        prompt_hash=cast(str, row["prompt_hash"]),
                        input_revision_id=cast(str, row["input_revision_id"]),
                        input_revision_hash=cast(str, row["input_revision_hash"]),
                        unit_id=cast(str | None, row["output_unit_id"]),
                        revision_id=revision_id,
                        revision_hash=revision_hash,
                        revision_status=revision_status,
                        text=text_value,
                        notes=notes,
                        provider_run_id=cast(str | None, row["provider_run_id"]),
                        usage=json.loads(cast(str, row["usage_json"])),
                        error_code=cast(str | None, row["error_code"]),
                        error_message=cast(str | None, row["error_message"]),
                    )
                )
            return results
        finally:
            engine.dispose()
