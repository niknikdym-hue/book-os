from __future__ import annotations

from typing import Any

from .anti_junk import AntiJunkService
from .model_gateway import ModelAdapterResult, ModelGateway, ModelOutputError, ModelTaskRequest
from .prompts import PromptTemplate


class AntiJunkModelGateway:
    """Gateway wrapper that supplies current anti-junk constraints and fail-closes Writer output."""

    def __init__(self, inner: ModelGateway, anti_junk: AntiJunkService):
        self.inner = inner
        self.anti_junk = anti_junk

    @staticmethod
    def _text_values(value: Any) -> list[str]:
        if isinstance(value, str):
            return [value]
        if isinstance(value, dict):
            result: list[str] = []
            for child in value.values():
                result.extend(AntiJunkModelGateway._text_values(child))
            return result
        if isinstance(value, list):
            result = []
            for child in value:
                result.extend(AntiJunkModelGateway._text_values(child))
            return result
        return []

    def generate(self, request: ModelTaskRequest, prompt: PromptTemplate) -> ModelAdapterResult:
        bounded = request.model_copy(deep=True)
        if bounded.role in {"WRITER", "PLANNER"}:
            bounded.authoritative_context = {
                **bounded.authoritative_context,
                "negative_style_constraints": self.anti_junk.generation_constraints(),
            }
        result = self.inner.generate(bounded, prompt)
        if bounded.role in {"WRITER", "PLANNER"}:
            banned_hits: list[dict[str, object]] = []
            for text in self._text_values(result.output):
                banned_hits.extend(
                    hit for hit in self.anti_junk.scan(text) if hit["kind"] == "BANNED_TEMPLATE"
                )
            if banned_hits:
                examples = ", ".join(
                    sorted({str(hit["match"]) for hit in banned_hits})[:5]
                )
                raise ModelOutputError(
                    "generated output violates BOOK OS prose anti-junk rules: " + examples
                )
        return result
