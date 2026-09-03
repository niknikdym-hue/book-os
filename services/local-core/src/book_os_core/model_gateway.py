from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Protocol
import json

import httpx
from pydantic import BaseModel, Field, ValidationError

from .prompts import PromptTemplate
from .secrets import SecretStore


class ModelProviderError(RuntimeError):
    pass


class ModelOutputError(RuntimeError):
    pass


class ModelBudgetError(RuntimeError):
    pass


class AuthorityInputRef(BaseModel):
    revision_id: str
    revision_hash: str
    entity_type: str


class SectionDraftOutput(BaseModel):
    text: str = Field(min_length=1)
    notes: list[str] = Field(default_factory=list)


class BookContractProposalOutput(BaseModel):
    reader: str = Field(min_length=1)
    reader_problem: str = Field(min_length=1)
    central_promise: str = Field(min_length=1)
    central_thesis: str = Field(min_length=1)
    unique_angle: str = Field(min_length=1)
    reader_trajectory: str = Field(min_length=1)
    explicit_exclusions: list[str] = Field(min_length=1)
    evidence_policy: str = Field(min_length=1)
    voice_genre_constraints: str = Field(min_length=1)
    readiness_criteria: list[str] = Field(min_length=1)


class ArchitectureChapterProposalOutput(BaseModel):
    title: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    new_contribution: str = Field(min_length=1)
    dependencies: list[str] = Field(default_factory=list)
    transition: str = ""


class ArchitecturePartProposalOutput(BaseModel):
    title: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    chapters: list[ArchitectureChapterProposalOutput] = Field(min_length=1)


class BookArchitectureProposalOutput(BaseModel):
    parts: list[ArchitecturePartProposalOutput] = Field(min_length=1)
    intellectual_progression: str = Field(min_length=1)
    concept_allocation: str = Field(min_length=1)
    promise_thesis_coverage: str = Field(min_length=1)
    major_transitions: str = Field(min_length=1)


class ChapterContractProposalOutput(BaseModel):
    chapter_purpose: str = Field(min_length=1)
    new_contribution: str = Field(min_length=1)
    reader_prior_state: str = Field(min_length=1)
    reader_after_state: str = Field(min_length=1)
    required_claims: list[str] = Field(min_length=1)
    required_or_permitted_research: list[str] = Field(min_length=1)
    required_scenes_examples: list[str] = Field(min_length=1)
    reserved_elsewhere: list[str] = Field(default_factory=list)
    opening_requirements: str = Field(min_length=1)
    ending_requirements: str = Field(min_length=1)
    transition_requirements: str = Field(min_length=1)


class JudgeFindingOutput(BaseModel):
    location: str = Field(min_length=1)
    evidence: str = Field(min_length=1)
    recommended_action: str = Field(min_length=1)


class BookBenchJudgeOutput(BaseModel):
    verdict: Literal["PASS", "ATTENTION", "BLOCKING"]
    findings: list[JudgeFindingOutput] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    rationale: str = Field(min_length=1)


class BookBenchPairwiseOutput(BaseModel):
    preference: Literal["A", "B", "TIE"]
    dimension: str = Field(min_length=1)
    evidence: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    rationale: str = Field(min_length=1)


class ModelTaskRequest(BaseModel):
    task_id: str
    task_type: Literal[
        "SECTION_DRAFT",
        "BOOK_CONTRACT_PROPOSAL",
        "ARCHITECTURE_PROPOSAL",
        "CHAPTER_CONTRACT_PROPOSAL",
        "BOOKBENCH_JUDGE",
        "BOOKBENCH_PAIRWISE",
    ]
    role: Literal["WRITER", "PLANNER", "EVALUATOR"]
    provider: str
    model: str
    prompt_id: str
    prompt_version: str
    prompt_hash: str
    section_objective: str = Field(min_length=1, max_length=4000)
    authority_inputs: list[AuthorityInputRef] = Field(default_factory=list)
    authoritative_context: dict[str, Any]
    untrusted_context: list[str] = Field(default_factory=list)
    task_payload: dict[str, Any] = Field(default_factory=dict)
    max_output_tokens: int = Field(default=3500, ge=100, le=12000)
    max_cost_usd: float | None = Field(default=None, ge=0)


@dataclass(frozen=True)
class ModelAdapterResult:
    provider_run_id: str | None
    output: dict[str, Any]
    usage: dict[str, Any]


class ModelAdapter(Protocol):
    provider_name: str

    def generate(self, request: ModelTaskRequest, prompt: PromptTemplate) -> ModelAdapterResult: ...


class ModelGateway:
    def __init__(self, adapters: dict[str, ModelAdapter]):
        self._adapters = dict(adapters)

    def generate(self, request: ModelTaskRequest, prompt: PromptTemplate) -> ModelAdapterResult:
        try:
            adapter = self._adapters[request.provider]
        except KeyError as exc:
            raise ModelProviderError(f"provider is not configured: {request.provider}") from exc
        return adapter.generate(request, prompt)


class DeterministicFakeAdapter:
    provider_name = "fake"

    def __init__(
        self,
        *,
        mode: Literal["success", "malformed", "provider_error", "budget_error"] = "success",
    ) -> None:
        self.mode = mode
        self.last_request: ModelTaskRequest | None = None

    def generate(self, request: ModelTaskRequest, prompt: PromptTemplate) -> ModelAdapterResult:
        self.last_request = request
        if self.mode == "provider_error":
            raise ModelProviderError("deterministic provider failure")
        if self.mode == "budget_error":
            raise ModelBudgetError("deterministic budget guard failure")
        if self.mode == "malformed":
            return ModelAdapterResult(
                provider_run_id="fake-malformed",
                output={"notes": ["missing required text"]},
                usage={"input_tokens": 10, "output_tokens": 2},
            )
        if request.task_type == "BOOK_CONTRACT_PROPOSAL":
            return ModelAdapterResult(
                provider_run_id="fake-book-contract",
                output={
                    "reader": "Владелец растущей компании",
                    "reader_problem": "Компания зависит от постоянных решений владельца",
                    "central_promise": "Понять и перестроить критические зависимости управления",
                    "central_thesis": "Качество управления растёт, когда права решений и контроль становятся явной системой",
                    "unique_angle": "Разбирать зависимость бизнеса от владельца как архитектурную проблему",
                    "reader_trajectory": "От личного контроля к управляемой системе решений",
                    "explicit_exclusions": ["Не тайм-менеджмент", "Не мотивационная книга"],
                    "evidence_policy": "Материальные утверждения требуют проверяемых источников",
                    "voice_genre_constraints": "Точный деловой нон-фикшен без рекламных клише",
                    "readiness_criteria": [
                        "Читатель может диагностировать зависимости",
                        "Рекомендации привязаны к механизмам",
                    ],
                },
                usage={"input_tokens": 120, "output_tokens": 180},
            )
        if request.task_type == "ARCHITECTURE_PROPOSAL":
            return ModelAdapterResult(
                provider_run_id="fake-architecture",
                output={
                    "parts": [
                        {
                            "title": "Часть I",
                            "purpose": "Диагностировать механизм зависимости",
                            "chapters": [
                                {
                                    "title": "Где застревают решения",
                                    "purpose": "Показать реальную точку ограничения",
                                    "new_contribution": "Карта возврата решений к владельцу",
                                    "dependencies": [],
                                    "transition": "От симптомов к устройству контроля",
                                },
                                {
                                    "title": "Как устроить права решений",
                                    "purpose": "Перенести часть контроля в систему",
                                    "new_contribution": "Практическая модель прав решений",
                                    "dependencies": [],
                                    "transition": "От модели к внедрению",
                                },
                            ],
                        }
                    ],
                    "intellectual_progression": "Диагностика → механизм → перестройка → проверка",
                    "concept_allocation": "Каждая глава владеет отдельным механизмом",
                    "promise_thesis_coverage": "Архитектура последовательно выполняет обещание контракта",
                    "major_transitions": "Каждый переход закрывает один вопрос и открывает следующий",
                },
                usage={"input_tokens": 180, "output_tokens": 260},
            )
        if request.task_type == "CHAPTER_CONTRACT_PROPOSAL":
            return ModelAdapterResult(
                provider_run_id="fake-chapter-contract",
                output={
                    "chapter_purpose": "Выполнить уникальную функцию выбранной главы",
                    "new_contribution": "Добавить один новый механизм, не повторяя другие главы",
                    "reader_prior_state": "Читатель видит симптомы, но не умеет диагностировать механизм",
                    "reader_after_state": "Читатель может применить механизм к своей компании",
                    "required_claims": [
                        "Ключевой механизм главы должен быть сформулирован и проверяем"
                    ],
                    "required_or_permitted_research": [
                        "Проверить материальные организационные утверждения"
                    ],
                    "required_scenes_examples": ["Один конкретный управленческий эпизод или кейс"],
                    "reserved_elsewhere": ["Не повторять материал соседних глав"],
                    "opening_requirements": "Начать с конкретной наблюдаемой ситуации",
                    "ending_requirements": "Закончить изменившейся моделью читателя",
                    "transition_requirements": "Передать следующий нерешённый вопрос следующей главе",
                },
                usage={"input_tokens": 160, "output_tokens": 220},
            )
        if request.task_type == "BOOKBENCH_JUDGE":
            return ModelAdapterResult(
                provider_run_id="fake-judge-success",
                output={
                    "verdict": "ATTENTION",
                    "findings": [
                        {
                            "location": "candidate:1",
                            "evidence": "bounded synthetic signal",
                            "recommended_action": "Human review.",
                        }
                    ],
                    "confidence": 0.75,
                    "rationale": "Deterministic fake judge fixture.",
                },
                usage={"input_tokens": 40, "output_tokens": 20},
            )
        if request.task_type == "BOOKBENCH_PAIRWISE":
            return ModelAdapterResult(
                provider_run_id="fake-pairwise-success",
                output={
                    "preference": "A",
                    "dimension": str(request.task_payload.get("dimension", "IDEA_REPETITION")),
                    "evidence": ["bounded synthetic comparison"],
                    "confidence": 0.8,
                    "rationale": "Deterministic fake pairwise fixture.",
                },
                usage={"input_tokens": 50, "output_tokens": 20},
            )
        return ModelAdapterResult(
            provider_run_id="fake-success",
            output={
                "text": f"Draft for: {request.section_objective}",
                "notes": ["deterministic fake adapter"],
            },
            usage={"input_tokens": 100, "output_tokens": 40},
        )


class OpenAIResponsesAdapter:
    provider_name = "openai"
    _PRICING_SOURCE_DATE = "2026-09-03"
    _PRICING_USD_PER_MILLION: dict[str, tuple[float, float]] = {
        "gpt-5.6-sol": (4.0, 20.0),
        "gpt-5.6": (4.0, 20.0),
        "gpt-5.6-terra": (2.0, 12.0),
        "gpt-5.6-luna": (0.2, 1.2),
    }
    _INPUT_TOKEN_OVERHEAD = 4096

    def __init__(
        self,
        secret_store: SecretStore,
        *,
        client: httpx.Client | None = None,
        endpoint: str = "https://api.openai.com/v1/responses",
        timeout_seconds: float = 90.0,
    ) -> None:
        self._secret_store = secret_store
        self._client = client or httpx.Client(timeout=timeout_seconds)
        self._endpoint = endpoint
        self._timeout_seconds = timeout_seconds

    @staticmethod
    def output_schema(task_type: str = "SECTION_DRAFT") -> dict[str, Any]:
        if task_type == "BOOK_CONTRACT_PROPOSAL":
            return BookContractProposalOutput.model_json_schema()
        if task_type == "ARCHITECTURE_PROPOSAL":
            return BookArchitectureProposalOutput.model_json_schema()
        if task_type == "CHAPTER_CONTRACT_PROPOSAL":
            return ChapterContractProposalOutput.model_json_schema()
        if task_type == "BOOKBENCH_JUDGE":
            return BookBenchJudgeOutput.model_json_schema()
        if task_type == "BOOKBENCH_PAIRWISE":
            return BookBenchPairwiseOutput.model_json_schema()
        return SectionDraftOutput.model_json_schema()

    def _body(self, request: ModelTaskRequest, prompt: PromptTemplate) -> dict[str, Any]:
        user_payload = {
            "task_type": request.task_type,
            "section_objective": request.section_objective,
            "authority_inputs": [item.model_dump(mode="json") for item in request.authority_inputs],
            "authoritative_context": request.authoritative_context,
            "untrusted_context": request.untrusted_context,
            "task_payload": request.task_payload,
        }
        return {
            "model": request.model,
            "store": False,
            "input": [
                {
                    "role": "developer",
                    "content": [{"type": "input_text", "text": prompt.developer_text}],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": json.dumps(user_payload, ensure_ascii=False, sort_keys=True),
                        }
                    ],
                },
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": request.task_type.casefold(),
                    "strict": True,
                    "schema": self.output_schema(request.task_type),
                }
            },
            "max_output_tokens": request.max_output_tokens,
        }

    @classmethod
    def _pricing(cls, model: str) -> tuple[float, float]:
        try:
            return cls._PRICING_USD_PER_MILLION[model]
        except KeyError as exc:
            raise ModelBudgetError(
                f"cost cap cannot be enforced for unpriced OpenAI model: {model}"
            ) from exc

    @classmethod
    def _budget_guard(
        cls,
        request: ModelTaskRequest,
        body: dict[str, Any],
    ) -> dict[str, Any] | None:
        if request.max_cost_usd is None:
            return None
        input_price, output_price = cls._pricing(request.model)
        serialized = json.dumps(
            body, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        input_token_upper_bound = len(serialized) + cls._INPUT_TOKEN_OVERHEAD
        preflight_upper_bound_usd = (
            input_token_upper_bound * input_price + request.max_output_tokens * output_price
        ) / 1_000_000
        if preflight_upper_bound_usd > request.max_cost_usd:
            raise ModelBudgetError(
                "worst-case OpenAI request cost "
                f"${preflight_upper_bound_usd:.6f} exceeds cap ${request.max_cost_usd:.6f}"
            )
        return {
            "max_cost_usd": request.max_cost_usd,
            "preflight_upper_bound_usd": round(preflight_upper_bound_usd, 6),
            "input_token_upper_bound": input_token_upper_bound,
            "max_output_tokens": request.max_output_tokens,
            "input_usd_per_million": input_price,
            "output_usd_per_million": output_price,
            "pricing_source_date": cls._PRICING_SOURCE_DATE,
        }

    @classmethod
    def _usage_with_cost_guard(
        cls,
        usage: object,
        guard: dict[str, Any] | None,
    ) -> dict[str, Any]:
        result = dict(usage) if isinstance(usage, dict) else {}
        if guard is None:
            return result
        audited_guard = dict(guard)
        input_tokens = result.get("input_tokens")
        output_tokens = result.get("output_tokens")
        if (
            isinstance(input_tokens, (int, float))
            and not isinstance(input_tokens, bool)
            and isinstance(output_tokens, (int, float))
            and not isinstance(output_tokens, bool)
        ):
            estimated_actual_cost_usd = (
                float(input_tokens) * float(guard["input_usd_per_million"])
                + float(output_tokens) * float(guard["output_usd_per_million"])
            ) / 1_000_000
            audited_guard["estimated_actual_cost_usd"] = round(estimated_actual_cost_usd, 6)
        result["cost_guard"] = audited_guard
        return result

    @staticmethod
    def _output_text(payload: dict[str, Any]) -> str:
        direct = payload.get("output_text")
        if isinstance(direct, str) and direct:
            return direct
        for output in payload.get("output", []):
            if not isinstance(output, dict):
                continue
            for content in output.get("content", []):
                if isinstance(content, dict) and content.get("type") == "output_text":
                    text_value = content.get("text")
                    if isinstance(text_value, str) and text_value:
                        return text_value
        raise ModelOutputError("OpenAI response contains no output_text")

    def generate(self, request: ModelTaskRequest, prompt: PromptTemplate) -> ModelAdapterResult:
        body = self._body(request, prompt)
        cost_guard = self._budget_guard(request, body)
        api_key = self._secret_store.get_secret("openai_api_key")
        response = self._client.post(
            self._endpoint,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=body,
            timeout=self._timeout_seconds,
        )
        if response.status_code >= 400:
            raise ModelProviderError(f"OpenAI HTTP {response.status_code}")
        payload = response.json()
        if not isinstance(payload, dict):
            raise ModelOutputError("OpenAI response JSON must be an object")
        output_text = self._output_text(payload)
        try:
            parsed = json.loads(output_text)
        except json.JSONDecodeError as exc:
            raise ModelOutputError("OpenAI structured output is not JSON") from exc
        if not isinstance(parsed, dict):
            raise ModelOutputError("OpenAI structured output must be an object")
        try:
            output_type: type[BaseModel] = SectionDraftOutput
            if request.task_type == "BOOK_CONTRACT_PROPOSAL":
                output_type = BookContractProposalOutput
            elif request.task_type == "ARCHITECTURE_PROPOSAL":
                output_type = BookArchitectureProposalOutput
            elif request.task_type == "CHAPTER_CONTRACT_PROPOSAL":
                output_type = ChapterContractProposalOutput
            elif request.task_type == "BOOKBENCH_JUDGE":
                output_type = BookBenchJudgeOutput
            elif request.task_type == "BOOKBENCH_PAIRWISE":
                output_type = BookBenchPairwiseOutput
            validated = output_type.model_validate(parsed)
        except ValidationError as exc:
            raise ModelOutputError("OpenAI structured output failed schema validation") from exc
        usage = self._usage_with_cost_guard(payload.get("usage"), cost_guard)
        return ModelAdapterResult(
            provider_run_id=str(payload["id"]) if payload.get("id") is not None else None,
            output=validated.model_dump(mode="json"),
            usage=usage,
        )
