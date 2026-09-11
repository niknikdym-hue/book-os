from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal, cast

from pydantic import BaseModel, Field, ValidationError

from .authority import new_ulid
from .book_context import (
    AuthorProfileContent,
    BookContextGateError,
    ProfileCreateRequest,
    ProfileRegistry,
    ProfileView,
    SeriesProfileContent,
)
from .model_gateway import (
    ModelGateway,
    ModelOutputError,
    ModelTaskRequest,
    ReasoningEffort,
    SectionDraftOutput,
)
from .model_routing import ModelRoutingService
from .prompts import PromptTemplate


SeriesModelChoice = Literal["ASTRA_MEDIUM", "ASTRA_HIGH", "ASTRA_XHIGH", "SOL"]


class SeriesStudioError(RuntimeError):
    pass


class SeriesCreateWithAIRequest(BaseModel):
    author_profile_id: str = Field(min_length=26, max_length=26)
    brief: str = Field(min_length=20, max_length=8000)
    model_choice: SeriesModelChoice = "ASTRA_HIGH"
    max_cost_usd: float = Field(default=1.5, gt=0, le=20)
    max_output_tokens: int = Field(default=5000, ge=1200, le=8000)
    owner_authorizes_paid_call: Literal[True]


class SeriesCreateWithAIView(BaseModel):
    profile: ProfileView
    provider: Literal["openai"] = "openai"
    model: str
    reasoning_effort: ReasoningEffort | None
    provider_run_id: str | None
    usage: dict[str, Any]


SERIES_PROFILE_PROPOSAL_V1 = PromptTemplate(
    prompt_id="series_profile_proposal_v1",
    version="1.0.0",
    developer_text=(
        "You are the bounded BOOK OS Series Planner. Propose one professional nonfiction Series "
        "Profile from the user's brief and approved Author Profile. Every planned book must be a "
        "genuinely unique book, not a clone or variant. The series may share quality, voice and "
        "positioning, but books must not repeat theses, mechanisms, arguments, research functions, "
        "examples, cases, scenes, metaphors, analogies, practical tools, composition patterns or "
        "distinctive wording. Reserve future-book material explicitly. Return outer JSON matching "
        "the SectionDraft schema; its `text` field must contain ONLY a valid JSON object with these "
        "keys: series_name, purpose_positioning, planned_books, thematic_territories, "
        "shared_invariants, future_book_reservations, cross_book_uniqueness_rules, "
        "exclusion_dimensions, prewriting_overlap_requirements, whole_book_audit_requirements. "
        "Do not include author_profile_id; BOOK OS binds it deterministically. For Russian input, "
        "write natural professional Russian. Do not invent market statistics or factual evidence."
    ),
)


class SeriesStudioService:
    REQUIRED_UNIQUENESS_RULES = [
        "Каждая книга серии имеет собственный центральный тезис, механизм, архитектуру и интеллектуальный вклад.",
        "Запрещён смысловой overlap с другими книгами серии.",
        "Не повторять аргументы, исследовательские функции, сцены, примеры и кейсы других книг серии.",
        "Не повторять метафоры, аналогии, практические инструменты и композиционные паттерны других книг серии.",
        "Не копировать структуру глав, openings/endings и distinctive wording других книг серии.",
    ]
    REQUIRED_EXCLUSION_DIMENSIONS = [
        "тезисы",
        "механизмы",
        "аргументы",
        "исследовательские функции",
        "сцены",
        "примеры и кейсы",
        "метафоры и аналогии",
        "практические инструменты",
        "композиционные паттерны",
        "структура глав",
        "distinctive wording / recycled AI phrasing",
    ]
    REQUIRED_PREWRITING = [
        "До написания построить cross-book overlap map против cumulative exclusion corpus ранее принятых Literary Masters.",
        "Материал, уже принадлежащий другой книге серии, не допускается в writing lane новой книги.",
    ]
    REQUIRED_WHOLE_BOOK_AUDIT = [
        "Перед Literary Master провести whole-book SeriesBench / cross-series audit.",
        "Release допускается только после устранения или явного HUMAN disposition всех блокирующих cross-book findings.",
    ]

    def __init__(self, data_dir: Path, gateway: ModelGateway) -> None:
        self.profiles = ProfileRegistry(data_dir)
        self.gateway = gateway

    @staticmethod
    def _choice(choice: SeriesModelChoice) -> tuple[str, ReasoningEffort | None]:
        if choice == "ASTRA_MEDIUM":
            return "gpt-6-astra", "medium"
        if choice == "ASTRA_XHIGH":
            return "gpt-6-astra", "xhigh"
        if choice == "SOL":
            return "gpt-5.6-sol", None
        return "gpt-6-astra", "high"

    @staticmethod
    def _unique(values: list[str]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for item in values:
            normalized = item.strip()
            key = normalized.casefold()
            if normalized and key not in seen:
                seen.add(key)
                result.append(normalized)
        return result

    @classmethod
    def _harden(cls, content: SeriesProfileContent) -> SeriesProfileContent:
        payload = content.model_dump(mode="json")
        payload["shared_invariants"] = cls._unique(
            [
                *cast(list[str], payload.get("shared_invariants", [])),
                "Серия сохраняет общий уровень качества и узнаваемую манеру, но книги не являются клонами.",
            ]
        )
        payload["cross_book_uniqueness_rules"] = cls._unique(
            [
                *cast(list[str], payload.get("cross_book_uniqueness_rules", [])),
                *cls.REQUIRED_UNIQUENESS_RULES,
            ]
        )
        payload["exclusion_dimensions"] = cls._unique(
            [
                *cast(list[str], payload.get("exclusion_dimensions", [])),
                *cls.REQUIRED_EXCLUSION_DIMENSIONS,
            ]
        )
        payload["prewriting_overlap_requirements"] = cls._unique(
            [
                *cast(list[str], payload.get("prewriting_overlap_requirements", [])),
                *cls.REQUIRED_PREWRITING,
            ]
        )
        payload["whole_book_audit_requirements"] = cls._unique(
            [
                *cast(list[str], payload.get("whole_book_audit_requirements", [])),
                *cls.REQUIRED_WHOLE_BOOK_AUDIT,
            ]
        )
        return SeriesProfileContent.model_validate(payload)

    @staticmethod
    def _decode_inner_json(value: str) -> dict[str, Any]:
        stripped = value.strip()
        if stripped.startswith("```"):
            lines = stripped.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            stripped = "\n".join(lines).strip()
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise ModelOutputError("series planner returned invalid JSON in text") from exc
        if not isinstance(payload, dict):
            raise ModelOutputError("series planner text must contain a JSON object")
        return cast(dict[str, Any], payload)

    def create_with_ai(self, request: SeriesCreateWithAIRequest) -> SeriesCreateWithAIView:
        author = self.profiles.get_profile(request.author_profile_id)
        if author.kind != "AUTHOR" or author.status != "APPROVED":
            raise BookContextGateError("AI series creation requires an approved Author Profile")
        author_content = AuthorProfileContent.model_validate(author.content)

        model, effort = self._choice(request.model_choice)
        ModelRoutingService.validate_model("openai", model)
        if effort is not None:
            ModelRoutingService.validate_work_level("openai", model, effort)

        task_id = new_ulid()
        objective = (
            "Create a Series Profile proposal for this owner brief:\n\n"
            + request.brief.strip()
            + "\n\nThe output must separate every planned book by unique promise and territory."
        )
        result = self.gateway.generate(
            ModelTaskRequest(
                task_id=task_id,
                task_type="SECTION_DRAFT",
                role="PLANNER",
                provider="openai",
                model=model,
                prompt_id=SERIES_PROFILE_PROPOSAL_V1.prompt_id,
                prompt_version=SERIES_PROFILE_PROPOSAL_V1.version,
                prompt_hash=SERIES_PROFILE_PROPOSAL_V1.prompt_hash,
                section_objective=objective,
                authority_inputs=[],
                authoritative_context={
                    "author_profile": author_content.model_dump(mode="json"),
                    "author_profile_hash": author.content_hash,
                    "owner_series_authority": {
                        "books_are_unique": True,
                        "semantic_overlap_forbidden": True,
                        "series_reference_is_delivery_only": True,
                    },
                },
                reasoning_effort=effort,
                max_output_tokens=request.max_output_tokens,
                max_cost_usd=request.max_cost_usd,
            ),
            SERIES_PROFILE_PROPOSAL_V1,
        )
        try:
            outer = SectionDraftOutput.model_validate(result.output)
            raw = self._decode_inner_json(outer.text)
            raw["author_profile_id"] = author.profile_id
            proposed = SeriesProfileContent.model_validate(raw)
        except ValidationError as exc:
            raise ModelOutputError(
                "series planner output failed Series Profile validation"
            ) from exc

        hardened = self._harden(proposed)
        profile = self.profiles.create_profile(
            ProfileCreateRequest(kind="SERIES", content=hardened.model_dump(mode="json"))
        )
        return SeriesCreateWithAIView(
            profile=profile,
            model=model,
            reasoning_effort=effort,
            provider_run_id=result.provider_run_id,
            usage=result.usage,
        )
