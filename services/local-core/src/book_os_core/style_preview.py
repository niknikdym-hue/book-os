from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.engine import Engine

from .authority import new_ulid
from .authority_types import utc_now
from .book_context import (
    AuthorProfileContent,
    BookContextGateError,
    ProfileRegistry,
    StyleProfileContent,
)
from .db import create_database
from .model_gateway import ModelGateway, ModelTaskRequest
from .model_routing import ModelRoutingService
from .projects import ProjectService
from .prompts import STYLE_PREVIEW_V1


class StylePreviewError(RuntimeError):
    pass


class StylePreviewRequest(BaseModel):
    author_profile_id: str = Field(min_length=26, max_length=26)
    style_profile_ids: list[str] = Field(min_length=2, max_length=3)
    content_brief: str = Field(min_length=20, max_length=5000)
    provider: Literal["openai", "yandex"]
    selection_mode: Literal["AUTO", "MANUAL"] = "AUTO"
    selection_scope: Literal["OPERATION", "BOOK"] | None = None
    model: str | None = None
    max_output_tokens: int = Field(default=900, ge=300, le=1800)
    max_cost_usd_per_request: float = Field(gt=0)


class StylePreviewItem(BaseModel):
    preview_id: str
    style_profile_id: str
    style_profile_hash: str
    style_name: str
    provider: str
    provider_label: str
    model: str
    selection_mode: str
    selection_scope: str | None
    text: str
    usage: dict[str, Any]


class StylePreviewBatch(BaseModel):
    batch_id: str
    brief_hash: str
    per_request_cap_usd: float
    total_cap_usd: float
    previews: list[StylePreviewItem]


class StylePreviewService:
    def __init__(self, data_dir: Path, gateway: ModelGateway) -> None:
        self.projects = ProjectService(data_dir)
        self.profiles = ProfileRegistry(data_dir)
        self.routing = ModelRoutingService(data_dir)
        self.gateway = gateway

    def _engine(self, book_id: str) -> Engine:
        self.projects.get_project(book_id)
        return create_database(self.projects.projects_dir / book_id / "project.sqlite")

    @staticmethod
    def _hash(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    @staticmethod
    def _dump(value: object) -> str:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    def _start_run(
        self,
        engine: Engine,
        *,
        preview_id: str,
        batch_id: str,
        book_id: str,
        author_id: str,
        author_hash: str,
        style_id: str,
        style_hash: str,
        provider: str,
        model: str,
        selection_mode: str,
        selection_scope: str | None,
        rationale: str,
        brief: str,
        brief_hash: str,
        max_output_tokens: int,
        max_cost_usd: float,
    ) -> None:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO style_preview_runs("
                    "preview_id,batch_id,book_id,author_profile_id,author_profile_hash,"
                    "style_profile_id,style_profile_hash,provider,model,selection_mode,selection_scope,"
                    "routing_rationale,prompt_id,prompt_version,prompt_hash,brief_hash,content_brief,"
                    "max_output_tokens,max_cost_usd,status,usage_json,created_at) VALUES ("
                    ":preview_id,:batch_id,:book_id,:author_id,:author_hash,:style_id,:style_hash,"
                    ":provider,:model,:selection_mode,:selection_scope,:rationale,:prompt_id,"
                    ":prompt_version,:prompt_hash,:brief_hash,:brief,:max_output_tokens,:max_cost_usd,"
                    "'RUNNING','{}',:created_at)"
                ),
                {
                    "preview_id": preview_id,
                    "batch_id": batch_id,
                    "book_id": book_id,
                    "author_id": author_id,
                    "author_hash": author_hash,
                    "style_id": style_id,
                    "style_hash": style_hash,
                    "provider": provider,
                    "model": model,
                    "selection_mode": selection_mode,
                    "selection_scope": selection_scope,
                    "rationale": rationale,
                    "prompt_id": STYLE_PREVIEW_V1.prompt_id,
                    "prompt_version": STYLE_PREVIEW_V1.version,
                    "prompt_hash": STYLE_PREVIEW_V1.prompt_hash,
                    "brief_hash": brief_hash,
                    "brief": brief,
                    "max_output_tokens": max_output_tokens,
                    "max_cost_usd": max_cost_usd,
                    "created_at": utc_now(),
                },
            )

    def _finish_run(
        self,
        engine: Engine,
        preview_id: str,
        *,
        output_text: str | None,
        usage: dict[str, Any] | None,
        provider_run_id: str | None,
        error: Exception | None,
    ) -> None:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE style_preview_runs SET status=:status,provider_run_id=:provider_run_id,"
                    "output_text=:output_text,usage_json=:usage_json,error_message=:error_message,"
                    "completed_at=:completed_at WHERE preview_id=:preview_id"
                ),
                {
                    "status": "FAILED" if error else "SUCCEEDED",
                    "provider_run_id": provider_run_id,
                    "output_text": output_text,
                    "usage_json": self._dump(usage or {}),
                    "error_message": str(error)[:2000] if error else None,
                    "completed_at": utc_now(),
                    "preview_id": preview_id,
                },
            )

    def generate(self, book_id: str, request: StylePreviewRequest) -> StylePreviewBatch:
        self.projects.get_project(book_id)
        if len(set(request.style_profile_ids)) != len(request.style_profile_ids):
            raise StylePreviewError("style preview profiles must be distinct")

        author = self.profiles.get_profile(request.author_profile_id)
        if author.kind != "AUTHOR" or author.status != "APPROVED":
            raise BookContextGateError("Style Preview requires an approved Author Profile")
        author_content = AuthorProfileContent.model_validate(author.content)

        styles = []
        for style_id in request.style_profile_ids:
            style = self.profiles.get_profile(style_id)
            if style.kind != "STYLE":
                raise StylePreviewError(f"profile {style_id} is not a Style Profile")
            style_content = StyleProfileContent.model_validate(style.content)
            if (
                style_content.author_profile_id
                and style_content.author_profile_id != author.profile_id
            ):
                raise BookContextGateError("Style Preview profile belongs to another author")
            styles.append((style, style_content))

        batch_id = new_ulid()
        brief = request.content_brief.strip()
        brief_hash = self._hash(brief)
        engine = self._engine(book_id)
        previews: list[StylePreviewItem] = []
        try:
            for style, style_content in styles:
                choice = self.routing.resolve(
                    book_id,
                    "STYLE_PREVIEW",
                    provider=request.provider,
                    selection_mode=request.selection_mode,
                    selection_scope=request.selection_scope,
                    model=request.model,
                )
                preview_id = new_ulid()
                self._start_run(
                    engine,
                    preview_id=preview_id,
                    batch_id=batch_id,
                    book_id=book_id,
                    author_id=author.profile_id,
                    author_hash=author.content_hash,
                    style_id=style.profile_id,
                    style_hash=style.content_hash,
                    provider=choice.provider,
                    model=choice.model,
                    selection_mode=choice.selection_mode,
                    selection_scope=choice.selection_scope,
                    rationale=choice.rationale,
                    brief=brief,
                    brief_hash=brief_hash,
                    max_output_tokens=request.max_output_tokens,
                    max_cost_usd=request.max_cost_usd_per_request,
                )
                try:
                    result = self.gateway.generate(
                        ModelTaskRequest(
                            task_id=preview_id,
                            task_type="SECTION_DRAFT",
                            role="WRITER",
                            provider=choice.provider,
                            model=choice.model,
                            prompt_id=STYLE_PREVIEW_V1.prompt_id,
                            prompt_version=STYLE_PREVIEW_V1.version,
                            prompt_hash=STYLE_PREVIEW_V1.prompt_hash,
                            section_objective=brief,
                            authority_inputs=[],
                            authoritative_context={
                                "preview_only": True,
                                "author_profile": author_content.model_dump(mode="json"),
                                "author_profile_hash": author.content_hash,
                                "style_profile": style_content.model_dump(mode="json"),
                                "style_profile_hash": style.content_hash,
                                "negative_style_constraints": [
                                    *author_content.prose_prohibitions,
                                    *style_content.prohibited_patterns,
                                ],
                            },
                            max_output_tokens=request.max_output_tokens,
                            max_cost_usd=request.max_cost_usd_per_request,
                        ),
                        STYLE_PREVIEW_V1,
                    )
                    output_text = result.output.get("text")
                    if not isinstance(output_text, str) or not output_text.strip():
                        raise StylePreviewError("style preview provider returned no text")
                    self._finish_run(
                        engine,
                        preview_id,
                        output_text=output_text,
                        usage=result.usage,
                        provider_run_id=result.provider_run_id,
                        error=None,
                    )
                    previews.append(
                        StylePreviewItem(
                            preview_id=preview_id,
                            style_profile_id=style.profile_id,
                            style_profile_hash=style.content_hash,
                            style_name=style.name,
                            provider=choice.provider,
                            provider_label=choice.provider_label,
                            model=choice.model,
                            selection_mode=choice.selection_mode,
                            selection_scope=choice.selection_scope,
                            text=output_text,
                            usage=result.usage,
                        )
                    )
                except Exception as exc:
                    self._finish_run(
                        engine,
                        preview_id,
                        output_text=None,
                        usage=None,
                        provider_run_id=None,
                        error=exc,
                    )
                    raise
        finally:
            engine.dispose()

        return StylePreviewBatch(
            batch_id=batch_id,
            brief_hash=brief_hash,
            per_request_cap_usd=request.max_cost_usd_per_request,
            total_cap_usd=request.max_cost_usd_per_request * len(styles),
            previews=previews,
        )

    def delete_preview(self, book_id: str, preview_id: str) -> None:
        """Delete an isolated preview only; manuscript and authority records are untouched."""
        engine = self._engine(book_id)
        try:
            with engine.begin() as connection:
                result = connection.execute(
                    text("DELETE FROM style_preview_runs WHERE book_id=:book_id AND preview_id=:preview_id"),
                    {"book_id": book_id, "preview_id": preview_id},
                )
                if result.rowcount != 1:
                    raise StylePreviewError("style preview was not found")
        finally:
            engine.dispose()
