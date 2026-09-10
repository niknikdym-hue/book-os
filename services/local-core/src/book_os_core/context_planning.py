from __future__ import annotations

from pathlib import Path
from typing import Any

from .book_context import BookContextService
from .model_gateway import AuthorityInputRef, ModelGateway, ReasoningEffort
from .planning import PlanningGateError, PlanningService
from .prompts import PromptTemplate


class ContextAwarePlanningService(PlanningService):
    """PlanningService that always carries the exact bound book context into model input."""

    def __init__(self, data_dir: Path, gateway: ModelGateway) -> None:
        super().__init__(data_dir, gateway)
        self.contexts = BookContextService(data_dir)

    def _book_context_payload(self, book_id: str) -> dict[str, Any]:
        context = self.contexts.get_context(book_id)
        if not context.ready_for_planning:
            raise PlanningGateError(
                "approved Author/Style context and target length are required before AI planning"
            )
        return {
            "author_profile": (
                context.author_profile.model_dump(mode="json")
                if context.author_profile is not None
                else None
            ),
            "series_profile": (
                context.series_profile.model_dump(mode="json")
                if context.series_profile is not None
                else None
            ),
            "style_profile": (
                context.style_profile.model_dump(mode="json")
                if context.style_profile is not None
                else None
            ),
            "target_characters": context.target_characters,
            "min_characters": context.min_characters,
            "max_characters": context.max_characters,
            "include_bibliography": context.include_bibliography,
            "plan_illustrations": context.plan_illustrations,
            "visual_asset_format": context.visual_asset_format,
            "visual_materials_policy": context.visual_materials_policy,
            "characters_unit": context.characters_unit,
        }

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
        reasoning_effort: ReasoningEffort | None = None,
    ) -> tuple[str, dict[str, Any], dict[str, Any], str | None]:
        book_context = self._book_context_payload(book_id)
        return super()._run(
            book_id=book_id,
            chapter_id=chapter_id,
            run_kind=run_kind,
            provider=provider,
            model=model,
            prompt=prompt,
            objective=objective,
            authority_inputs=authority_inputs,
            authoritative_context={
                **authoritative_context,
                "book_context": book_context,
            },
            request_payload={
                **request_payload,
                "book_context": {
                    "author_profile_hash": (
                        book_context["author_profile"]["content_hash"]
                        if book_context["author_profile"]
                        else None
                    ),
                    "series_profile_hash": (
                        book_context["series_profile"]["content_hash"]
                        if book_context["series_profile"]
                        else None
                    ),
                    "style_profile_hash": (
                        book_context["style_profile"]["content_hash"]
                        if book_context["style_profile"]
                        else None
                    ),
                    "target_characters": book_context["target_characters"],
                    "min_characters": book_context["min_characters"],
                    "max_characters": book_context["max_characters"],
                    "include_bibliography": book_context["include_bibliography"],
                    "plan_illustrations": book_context["plan_illustrations"],
                    "visual_asset_format": book_context["visual_asset_format"],
                    "visual_materials_policy": book_context["visual_materials_policy"],
                    "characters_unit": book_context["characters_unit"],
                },
            },
            max_output_tokens=max_output_tokens,
            max_cost_usd=max_cost_usd,
            reasoning_effort=reasoning_effort,
        )
