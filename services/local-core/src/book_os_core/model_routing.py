from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.engine import Engine

from .authority_types import utc_now
from .db import create_database
from .projects import ProjectService

SelectionMode = Literal["AUTO", "MANUAL"]
SelectionScope = Literal["OPERATION", "BOOK"]
WorkLevel = Literal["medium", "high", "xhigh"]


class ModelRoutingError(RuntimeError):
    pass


class ProviderModel(BaseModel):
    id: str
    label: str
    family: str | None = None
    work_levels: list[WorkLevel] = []


class ProviderView(BaseModel):
    id: str
    label: str
    models: list[ProviderModel]
    work_levels: list[WorkLevel]


class RoutingChoice(BaseModel):
    provider: str
    provider_label: str
    model: str
    selection_mode: SelectionMode
    selection_scope: SelectionScope | None
    operation: str
    rationale: str


class BookModelPinView(BaseModel):
    provider: str
    provider_label: str
    model: str


@dataclass(frozen=True)
class ProviderSpec:
    label: str
    models: tuple[tuple[str, str], ...]
    auto: dict[str, str]
    work_levels: tuple[WorkLevel, ...] = ()


PROVIDERS: dict[str, ProviderSpec] = {
    "openai": ProviderSpec(
        label="OpenAI",
        models=(
            ("gpt-6-astra", "GPT-6 Astra"),
            ("gpt-5.6-sol", "GPT-5.6 Sol"),
            ("gpt-5.6-terra", "GPT-5.6 Terra"),
            ("gpt-5.6-luna", "GPT-5.6 Luna"),
        ),
        auto={
            "BOOK_CONTRACT_PROPOSAL": "gpt-6-astra",
            "ARCHITECTURE_PROPOSAL": "gpt-6-astra",
            "CHAPTER_CONTRACT_PROPOSAL": "gpt-5.6-sol",
            # The Author Studio's automatic mode is Astra-only. It must not silently
            # replace an Astra choice with a different OpenAI family.
            "SECTION_DRAFT": "gpt-6-astra",
            "STYLE_PREVIEW": "gpt-5.6-terra",
            "ANNOTATION": "gpt-5.6-terra",
        },
        work_levels=("medium", "high", "xhigh"),
    ),
    "yandex": ProviderSpec(
        label="AI Ya",
        models=(
            ("aliceai-llm", "Alice AI LLM"),
            ("aliceai-llm-flash", "Alice AI LLM Flash"),
            ("yandexgpt-5.1", "YandexGPT Pro 5.1"),
            ("yandexgpt-5-pro", "YandexGPT Pro 5"),
            ("yandexgpt-5-lite", "YandexGPT Lite 5"),
        ),
        auto={
            "BOOK_CONTRACT_PROPOSAL": "aliceai-llm",
            "ARCHITECTURE_PROPOSAL": "aliceai-llm",
            "CHAPTER_CONTRACT_PROPOSAL": "aliceai-llm",
            "SECTION_DRAFT": "aliceai-llm",
            "STYLE_PREVIEW": "aliceai-llm",
            "ANNOTATION": "aliceai-llm-flash",
        },
    ),
}


class ModelRoutingService:
    def __init__(self, data_dir: Path) -> None:
        self.projects = ProjectService(data_dir)

    @staticmethod
    def provider_registry() -> list[ProviderView]:
        result: list[ProviderView] = []
        for provider_id, spec in PROVIDERS.items():
            models = [
                ProviderModel(
                    id=model_id,
                    label=label,
                    family="astra" if model_id == "gpt-6-astra" else None,
                    work_levels=list(spec.work_levels) if model_id == "gpt-6-astra" else [],
                )
                for model_id, label in spec.models
            ]
            result.append(
                ProviderView(
                    id=provider_id,
                    label=spec.label,
                    models=models,
                    work_levels=list(spec.work_levels),
                )
            )
        return result

    def _engine(self, book_id: str) -> Engine:
        self.projects.get_project(book_id)
        return create_database(self.projects.projects_dir / book_id / "project.sqlite")

    @staticmethod
    def _provider(provider: str) -> ProviderSpec:
        try:
            return PROVIDERS[provider]
        except KeyError as exc:
            raise ModelRoutingError(f"unsupported provider: {provider}") from exc

    @classmethod
    def validate_model(cls, provider: str, model: str) -> None:
        spec = cls._provider(provider)
        valid = {model_id for model_id, _ in spec.models}
        if model not in valid:
            raise ModelRoutingError(f"model {model} is not registered for provider {provider}")

    @classmethod
    def model_label(cls, provider: str, model: str) -> str:
        spec = cls._provider(provider)
        for model_id, label in spec.models:
            if model_id == model:
                return label
        raise ModelRoutingError(f"model {model} is not registered for provider {provider}")

    @classmethod
    def validate_work_level(cls, provider: str, model: str, work_level: str) -> None:
        spec = cls._provider(provider)
        model_work_levels = spec.work_levels if model == "gpt-6-astra" else ()
        if work_level not in model_work_levels:
            raise ModelRoutingError(
                f"work level {work_level} is not registered for {provider}/{model}"
            )

    def get_book_pin(self, book_id: str) -> BookModelPinView | None:
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                row = (
                    connection.execute(
                        text("SELECT provider,model FROM book_model_pins WHERE book_id=:book_id"),
                        {"book_id": book_id},
                    )
                    .mappings()
                    .first()
                )
        finally:
            engine.dispose()
        if row is None:
            return None
        provider = str(row["provider"])
        spec = self._provider(provider)
        return BookModelPinView(
            provider=provider,
            provider_label=spec.label,
            model=str(row["model"]),
        )

    def set_book_pin(self, book_id: str, provider: str, model: str) -> BookModelPinView:
        self.validate_model(provider, model)
        engine = self._engine(book_id)
        now = utc_now()
        try:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT INTO book_model_pins(book_id,provider,model,created_at,updated_at) "
                        "VALUES (:book_id,:provider,:model,:created_at,:updated_at) "
                        "ON CONFLICT(book_id) DO UPDATE SET provider=excluded.provider,"
                        "model=excluded.model,updated_at=excluded.updated_at"
                    ),
                    {
                        "book_id": book_id,
                        "provider": provider,
                        "model": model,
                        "created_at": now,
                        "updated_at": now,
                    },
                )
        finally:
            engine.dispose()
        pin = self.get_book_pin(book_id)
        assert pin is not None
        return pin

    def clear_book_pin(self, book_id: str) -> None:
        engine = self._engine(book_id)
        try:
            with engine.begin() as connection:
                connection.execute(
                    text("DELETE FROM book_model_pins WHERE book_id=:book_id"),
                    {"book_id": book_id},
                )
        finally:
            engine.dispose()

    def resolve(
        self,
        book_id: str,
        operation: str,
        *,
        provider: str,
        selection_mode: SelectionMode,
        selection_scope: SelectionScope | None,
        model: str | None,
    ) -> RoutingChoice:
        if selection_mode == "MANUAL":
            if selection_scope not in {"OPERATION", "BOOK"}:
                raise ModelRoutingError("manual model selection requires OPERATION or BOOK scope")
            if not model:
                raise ModelRoutingError("manual model selection requires an explicit model")
            self.validate_model(provider, model)
            spec = self._provider(provider)
            if selection_scope == "BOOK":
                self.set_book_pin(book_id, provider, model)
                rationale = "Human manual model pin for the entire book"
            else:
                rationale = f"Human manual model pin for operation {operation}"
            return RoutingChoice(
                provider=provider,
                provider_label=spec.label,
                model=model,
                selection_mode="MANUAL",
                selection_scope=selection_scope,
                operation=operation,
                rationale=rationale,
            )

        if selection_scope is not None:
            raise ModelRoutingError("AUTO selection cannot declare a manual scope")
        existing = self.get_book_pin(book_id)
        if existing is not None:
            return RoutingChoice(
                provider=existing.provider,
                provider_label=existing.provider_label,
                model=existing.model,
                selection_mode="MANUAL",
                selection_scope="BOOK",
                operation=operation,
                rationale="Existing human whole-book model pin overrides Auto routing",
            )
        spec = self._provider(provider)
        try:
            auto_model = spec.auto[operation]
        except KeyError as exc:
            raise ModelRoutingError(
                f"Auto routing is not defined for operation {operation}"
            ) from exc
        return RoutingChoice(
            provider=provider,
            provider_label=spec.label,
            model=auto_model,
            selection_mode="AUTO",
            selection_scope=None,
            operation=operation,
            rationale=f"BOOK OS Auto routing for {operation}",
        )

    def record_run(self, book_id: str, run_id: str, choice: RoutingChoice) -> None:
        engine = self._engine(book_id)
        try:
            with engine.begin() as connection:
                result = connection.execute(
                    text(
                        "UPDATE planning_runs SET selection_mode=:selection_mode,"
                        "selection_scope=:selection_scope,routing_rationale=:routing_rationale "
                        "WHERE run_id=:run_id"
                    ),
                    {
                        "selection_mode": choice.selection_mode,
                        "selection_scope": choice.selection_scope,
                        "routing_rationale": choice.rationale,
                        "run_id": run_id,
                    },
                )
                if result.rowcount != 1:
                    raise ModelRoutingError("planning run was not found for routing provenance")
        finally:
            engine.dispose()
