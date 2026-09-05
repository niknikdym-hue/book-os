from __future__ import annotations

import json
from pathlib import Path
import secrets
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import text

from .anti_junk import AntiJunkService
from .authority import new_ulid
from .authority_types import utc_now
from .model_gateway import (
    BookContractProposalOutput,
    ModelBudgetError,
    ModelGateway,
    ModelOutputError,
    ModelProviderError,
    OpenAIResponsesAdapter,
)
from .model_gateway_anti_junk import AntiJunkModelGateway
from .planning import PlanningGateError, PlanningService
from .projects import BookContractPayload, ProjectService, ProjectView
from .prompts import BOOK_CONTRACT_PROPOSAL_V1
from .secrets import MacOSKeychainSecretStore


class BlindComparisonError(RuntimeError):
    pass


class BlindComparisonGateError(BlindComparisonError):
    pass


class AstraAwareOpenAIResponsesAdapter(OpenAIResponsesAdapter):
    """OpenAI adapter with the current bounded price table needed by the first blind pilot."""

    _PRICING_SOURCE_DATE = "2026-09-06"
    _PRICING_USD_PER_MILLION = {
        **OpenAIResponsesAdapter._PRICING_USD_PER_MILLION,
        "gpt-6-astra": (10.0, 50.0),
    }


class BlindBookContractCompareRequest(BaseModel):
    idea: str = Field(min_length=3, max_length=6000)
    reader_hint: str = Field(default="", max_length=4000)
    max_output_tokens: int = Field(default=2600, ge=500, le=8000)
    max_cost_usd_per_request: float = Field(default=0.50, gt=0, le=3.0)


class BlindBookContractCandidate(BaseModel):
    label: Literal["A", "B"]
    run_id: str
    contract: BookContractPayload


class BlindBookContractComparisonView(BaseModel):
    comparison_id: str
    candidate_a: BlindBookContractCandidate
    candidate_b: BlindBookContractCandidate
    per_request_cap_usd: float
    total_cap_usd: float
    models_revealed: bool = False


class BlindBookContractSelectRequest(BaseModel):
    selected_label: Literal["A", "B"]


class BlindBookContractSelectionView(BaseModel):
    comparison_id: str
    selected_label: Literal["A", "B"]
    revealed_models: dict[str, str]
    revealed_run_ids: dict[str, str]
    project: ProjectView


class BlindBookContractComparisonService:
    MODELS = ("gpt-6-astra", "gpt-5.6-sol")

    def __init__(self, data_dir: Path, gateway: ModelGateway | None = None) -> None:
        self.data_dir = data_dir
        self.projects = ProjectService(data_dir)
        if gateway is None:
            gateway = AntiJunkModelGateway(
                ModelGateway(
                    {
                        "openai": AstraAwareOpenAIResponsesAdapter(
                            MacOSKeychainSecretStore()
                        )
                    }
                ),
                AntiJunkService(data_dir),
            )
        self.planning = PlanningService(data_dir, gateway)

    def _comparison_dir(self, book_id: str) -> Path:
        self.projects.get_project(book_id)
        path = self.projects.projects_dir / book_id / "model-comparisons"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _record_path(self, book_id: str, comparison_id: str) -> Path:
        if not comparison_id or any(char not in "0123456789ABCDEFGHJKMNPQRSTVWXYZ" for char in comparison_id):
            raise BlindComparisonGateError("invalid blind comparison ID")
        return self._comparison_dir(book_id) / f"{comparison_id}.json"

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        temporary = path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)

    def _run_candidate(
        self,
        *,
        book_id: str,
        request: BlindBookContractCompareRequest,
        model: str,
        label: Literal["A", "B"],
    ) -> BlindBookContractCandidate:
        project = self.projects.get_project(book_id)
        objective = f"Сформировать Book Contract для идеи: {request.idea.strip()}"
        request_payload = {
            "idea": request.idea.strip(),
            "reader_hint": request.reader_hint.strip(),
            "provider": "openai",
            "model": model,
            "max_output_tokens": request.max_output_tokens,
            "max_cost_usd": request.max_cost_usd_per_request,
            "blind_candidate": label,
        }
        try:
            run_id, raw, _, _ = self.planning._run(
                book_id=book_id,
                chapter_id=None,
                run_kind="BOOK_CONTRACT_PROPOSAL",
                provider="openai",
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
                request_payload=request_payload,
                max_output_tokens=request.max_output_tokens,
                max_cost_usd=request.max_cost_usd_per_request,
            )
            proposal = BookContractProposalOutput.model_validate(raw)
            contract = BookContractPayload.model_validate(proposal.model_dump(mode="json"))
        except (ModelBudgetError, ModelOutputError, ModelProviderError) as exc:
            raise BlindComparisonError(str(exc)) from exc
        except ValidationError as exc:
            raise BlindComparisonError(
                "blind Book Contract candidate failed project schema validation"
            ) from exc
        return BlindBookContractCandidate(label=label, run_id=run_id, contract=contract)

    def compare(
        self, book_id: str, request: BlindBookContractCompareRequest
    ) -> BlindBookContractComparisonView:
        project = self.projects.get_project(book_id)
        if project.book_contract is not None and project.book_contract.authority_status in {
            "APPROVED",
            "LOCKED",
        }:
            raise BlindComparisonGateError(
                "approved Book Contract cannot be replaced by a blind comparison"
            )

        comparison_id = new_ulid()
        labels: list[Literal["A", "B"]] = ["A", "B"]
        if secrets.randbelow(2):
            labels.reverse()
        label_by_model = dict(zip(self.MODELS, labels, strict=True))

        # Execute Astra first. If the account cannot access the new model, the comparison
        # fails before spending a Sol request; labels remain randomized for the human review.
        candidates: dict[str, BlindBookContractCandidate] = {}
        for model in self.MODELS:
            label = label_by_model[model]
            candidates[label] = self._run_candidate(
                book_id=book_id,
                request=request,
                model=model,
                label=label,
            )

        record = {
            "comparison_id": comparison_id,
            "book_id": book_id,
            "operation": "BOOK_CONTRACT",
            "created_at": utc_now(),
            "selected_label": None,
            "selected_at": None,
            "candidates": {
                label: {
                    "run_id": candidate.run_id,
                    "model": model,
                }
                for model, label in label_by_model.items()
                for candidate in [candidates[label]]
            },
        }
        self._write_json(self._record_path(book_id, comparison_id), record)

        return BlindBookContractComparisonView(
            comparison_id=comparison_id,
            candidate_a=candidates["A"],
            candidate_b=candidates["B"],
            per_request_cap_usd=request.max_cost_usd_per_request,
            total_cap_usd=round(request.max_cost_usd_per_request * 2, 2),
        )

    def select(
        self,
        book_id: str,
        comparison_id: str,
        request: BlindBookContractSelectRequest,
    ) -> BlindBookContractSelectionView:
        path = self._record_path(book_id, comparison_id)
        if not path.is_file():
            raise BlindComparisonGateError("blind comparison not found")
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("book_id") != book_id or record.get("operation") != "BOOK_CONTRACT":
            raise BlindComparisonGateError("blind comparison does not belong to this book")
        candidates = record.get("candidates")
        if not isinstance(candidates, dict) or request.selected_label not in candidates:
            raise BlindComparisonGateError("blind comparison candidate is missing")
        previous = record.get("selected_label")
        if previous is not None and previous != request.selected_label:
            raise BlindComparisonGateError("blind comparison preference is already recorded")

        selected = candidates[request.selected_label]
        if not isinstance(selected, dict) or not isinstance(selected.get("run_id"), str):
            raise BlindComparisonGateError("blind comparison run is invalid")
        run_id = selected["run_id"]

        engine = self.planning._engine(book_id)
        try:
            with engine.connect() as connection:
                row = (
                    connection.execute(
                        text(
                            "SELECT output_json FROM planning_runs "
                            "WHERE run_id=:run_id AND book_id=:book_id "
                            "AND run_kind='BOOK_CONTRACT_PROPOSAL' AND status='SUCCEEDED'"
                        ),
                        {"run_id": run_id, "book_id": book_id},
                    )
                    .mappings()
                    .one_or_none()
                )
        finally:
            engine.dispose()
        if row is None or row["output_json"] is None:
            raise BlindComparisonGateError("selected blind comparison run is unavailable")
        try:
            raw = json.loads(str(row["output_json"]))
            proposal = BookContractProposalOutput.model_validate(raw)
            contract = BookContractPayload.model_validate(proposal.model_dump(mode="json"))
        except (json.JSONDecodeError, ValidationError) as exc:
            raise BlindComparisonError("selected blind candidate is not a valid Book Contract") from exc

        # Record the human preference before revealing model identity.
        if previous is None:
            record["selected_label"] = request.selected_label
            record["selected_at"] = utc_now()
            self._write_json(path, record)

        updated = self.projects.save_book_contract(book_id, contract)
        revealed_models = {
            label: str(value["model"])
            for label, value in candidates.items()
            if isinstance(value, dict) and isinstance(value.get("model"), str)
        }
        revealed_run_ids = {
            label: str(value["run_id"])
            for label, value in candidates.items()
            if isinstance(value, dict) and isinstance(value.get("run_id"), str)
        }
        return BlindBookContractSelectionView(
            comparison_id=comparison_id,
            selected_label=request.selected_label,
            revealed_models=revealed_models,
            revealed_run_ids=revealed_run_ids,
            project=updated,
        )
