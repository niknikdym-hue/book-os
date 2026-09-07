from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal, cast

from pydantic import BaseModel, Field, model_validator
from sqlalchemy import text
from sqlalchemy.engine import Engine

from .authority import AuthorityService, content_hash, new_ulid
from .authority_types import JSONValue, utc_now
from .book_context import BookContextService
from .db import create_database
from .projects import ProjectService

HumanActorKind = Literal["HUMAN", "OWNER"]
EvidenceActorKind = Literal["HUMAN", "OWNER", "AI", "SYSTEM"]
GateResult = Literal["PASS", "ATTENTION", "BLOCKING"]
QualityResult = Literal["PASS", "REWORK"]
CanonStatus = Literal[
    "PLANNED",
    "RESERVED",
    "USED_DRAFT",
    "USED_ACCEPTED",
    "CROSS_REFERENCE_ONLY",
    "LEGACY_PROTECTED",
    "RELEASED",
]


class SeriesProductionError(RuntimeError):
    pass


class SeriesProductionGateError(SeriesProductionError):
    pass


class PracticalValueItem(BaseModel):
    problem: str = Field(min_length=1, max_length=4000)
    decision: str = Field(min_length=1, max_length=4000)
    action: str = Field(min_length=1, max_length=4000)
    artifact_output: str = Field(min_length=1, max_length=4000)
    observable_check: str = Field(min_length=1, max_length=4000)


class DefinitionPackContent(BaseModel):
    reader_and_real_problem: str = Field(min_length=1, max_length=12000)
    central_promise: str = Field(min_length=1, max_length=12000)
    central_thesis: str = Field(min_length=1, max_length=12000)
    central_mechanism: str = Field(min_length=1, max_length=12000)
    not_this_book: list[str] = Field(min_length=1)
    series_future_book_boundaries: list[str] = Field(default_factory=list)
    category_competitor_substitute_map: list[str] = Field(min_length=1)
    world_class_benchmark: list[str] = Field(min_length=1)
    original_contribution_hypothesis: str = Field(min_length=1, max_length=12000)
    research_evidence_functions: list[str] = Field(min_length=1)
    practical_value_map: list[PracticalValueItem] = Field(min_length=1)
    target_market_application: str = Field(min_length=1, max_length=12000)
    freshness_risk_map: list[str] = Field(default_factory=list)
    uniqueness_overlap_proof: str = Field(min_length=1, max_length=12000)
    ai_substitution_result: QualityResult
    top_tier_global: QualityResult
    original_contribution: QualityResult
    practical_value: QualityResult
    target_market_quality: QualityResult
    density_rule: str = Field(
        default="NO PADDING: length may grow only through a new substantive function",
        min_length=1,
        max_length=4000,
    )

    def blockers(self) -> list[str]:
        values = {
            "ai_substitution_result": self.ai_substitution_result,
            "top_tier_global": self.top_tier_global,
            "original_contribution": self.original_contribution,
            "practical_value": self.practical_value,
            "target_market_quality": self.target_market_quality,
        }
        return [name for name, value in values.items() if value != "PASS"]


class DefinitionPackCreateRequest(BaseModel):
    content: DefinitionPackContent
    actor_kind: HumanActorKind
    actor: str = Field(min_length=1, max_length=255)


class DefinitionPackApprovalRequest(BaseModel):
    actor_kind: HumanActorKind
    actor: str = Field(min_length=1, max_length=255)


class DefinitionPackView(BaseModel):
    definition_id: str
    book_id: str
    revision: int
    content_hash: str
    content: DefinitionPackContent
    status: str
    created_by: str
    created_at: str
    approved_by: str | None = None
    approved_at: str | None = None


class ChapterProductionContractContent(BaseModel):
    unique_question: str = Field(min_length=1, max_length=8000)
    mechanism_causal_chain: str = Field(min_length=1, max_length=12000)
    reader_prior_state: str = Field(min_length=1, max_length=8000)
    reader_after_state: str = Field(min_length=1, max_length=8000)
    contribution_relative_to_adjacent: str = Field(min_length=1, max_length=8000)
    evidence_function: str = Field(min_length=1, max_length=8000)
    evidence_limits: str = Field(min_length=1, max_length=8000)
    scene_case_function: str = Field(default="", max_length=8000)
    not_this_chapter: list[str] = Field(min_length=1)
    opening_intent: str = Field(min_length=1, max_length=8000)
    development_intent: str = Field(min_length=1, max_length=8000)
    complication_intent: str = Field(min_length=1, max_length=8000)
    ending_intent: str = Field(min_length=1, max_length=8000)
    decision_enabled: str = Field(min_length=1, max_length=8000)
    next_action: str = Field(min_length=1, max_length=8000)
    practical_artifact: str = Field(min_length=1, max_length=8000)
    observable_check: str = Field(min_length=1, max_length=8000)
    target_market_application: str = Field(min_length=1, max_length=8000)
    freshness_requirements: list[str] = Field(default_factory=list)
    reserved_material: list[str] = Field(default_factory=list)
    composition_intent: str = Field(min_length=1, max_length=8000)
    deletion_merge_test: QualityResult
    ai_substitution_result: QualityResult
    top_tier_global: QualityResult
    original_contribution: QualityResult
    practical_value: QualityResult
    target_market_quality: QualityResult

    def blockers(self) -> list[str]:
        values = {
            "deletion_merge_test": self.deletion_merge_test,
            "ai_substitution_result": self.ai_substitution_result,
            "top_tier_global": self.top_tier_global,
            "original_contribution": self.original_contribution,
            "practical_value": self.practical_value,
            "target_market_quality": self.target_market_quality,
        }
        return [name for name, value in values.items() if value != "PASS"]


class ChapterProductionContractCreateRequest(BaseModel):
    content: ChapterProductionContractContent
    actor_kind: HumanActorKind
    actor: str = Field(min_length=1, max_length=255)


class ChapterProductionContractApprovalRequest(BaseModel):
    actor_kind: HumanActorKind
    actor: str = Field(min_length=1, max_length=255)


class ChapterProductionContractView(BaseModel):
    production_contract_id: str
    book_id: str
    chapter_id: str
    architecture_revision_id: str
    architecture_revision_hash: str
    chapter_contract_revision_id: str
    chapter_contract_revision_hash: str
    content_hash: str
    content: ChapterProductionContractContent
    status: str
    created_by: str
    created_at: str
    approved_by: str | None = None
    approved_at: str | None = None


class SeriesCanonAssetCreateRequest(BaseModel):
    series_profile_id: str = Field(min_length=26, max_length=26)
    book_id: str | None = Field(default=None, min_length=26, max_length=26)
    asset_type: str = Field(min_length=1, max_length=64)
    asset_key: str = Field(min_length=1, max_length=300)
    description: str = Field(min_length=1, max_length=12000)
    status: Literal["PLANNED", "LEGACY_PROTECTED"] = "PLANNED"
    source_revision_id: str | None = Field(default=None, min_length=26, max_length=26)
    source_revision_hash: str | None = Field(default=None, min_length=64, max_length=64)
    provenance: dict[str, Any] = Field(default_factory=dict)
    actor: str = Field(min_length=1, max_length=255)


class SeriesCanonTransitionRequest(BaseModel):
    status: CanonStatus
    actor: str = Field(min_length=1, max_length=255)
    evidence: dict[str, Any] = Field(default_factory=dict)


class SeriesCanonAssetView(BaseModel):
    asset_id: str
    series_profile_id: str
    book_id: str | None
    asset_type: str
    asset_key: str
    description: str
    status: CanonStatus
    source_revision_id: str | None
    source_revision_hash: str | None
    provenance: dict[str, Any]
    created_by: str
    created_at: str
    updated_at: str


class UniquenessEvidenceRequest(BaseModel):
    status: GateResult
    evidence: dict[str, Any] = Field(min_length=1)
    actor_kind: EvidenceActorKind
    actor: str = Field(min_length=1, max_length=255)


class UniquenessEvidenceView(BaseModel):
    ledger_id: str
    book_id: str
    chapter_id: str
    architecture_revision_id: str
    architecture_revision_hash: str
    chapter_contract_revision_id: str
    chapter_contract_revision_hash: str
    status: GateResult
    evidence: dict[str, Any]
    actor_kind: EvidenceActorKind
    actor: str
    created_at: str


class AdmissionChecks(BaseModel):
    evidence_readiness: Literal["PASS", "BLOCKING"]
    boundaries_reservations: Literal["PASS", "BLOCKING"]
    top_tier_global: QualityResult
    original_contribution: QualityResult
    practical_value: QualityResult
    target_market_application: QualityResult
    freshness: QualityResult
    anti_junk_provenance: Literal["PASS", "BLOCKING"]
    deletion_merge_test: QualityResult
    conditional_blockers_resolved: bool

    def blockers(self) -> list[str]:
        values = self.model_dump(mode="json")
        result: list[str] = []
        for name, value in values.items():
            if name == "conditional_blockers_resolved":
                if value is not True:
                    result.append(name)
            elif value != "PASS":
                result.append(name)
        return result


class ChapterAdmissionRequest(BaseModel):
    checks: AdmissionChecks
    actor_kind: HumanActorKind
    actor: str = Field(min_length=1, max_length=255)
    reason: str = Field(min_length=1, max_length=12000)


class ChapterAdmissionStatusView(BaseModel):
    book_id: str
    chapter_id: str
    writing_allowed: bool
    blockers: list[str]
    admission_id: str | None = None
    definition_id: str | None = None
    architecture_revision_id: str | None = None
    chapter_contract_revision_id: str | None = None
    production_contract_id: str | None = None


class ProductionCheckpointRequest(BaseModel):
    kind: Literal["MID_BOOK", "ADVERSARIAL_REVIEW"]
    progress_percent: float | None = None
    status: GateResult
    findings: list[dict[str, Any]] = Field(default_factory=list)
    actor_kind: EvidenceActorKind
    actor: str = Field(min_length=1, max_length=255)
    executor_identity: str | None = Field(default=None, max_length=255)
    snapshot_hash: str | None = Field(default=None, min_length=64, max_length=64)
    independent: bool = True

    @model_validator(mode="after")
    def validate_kind(self) -> ProductionCheckpointRequest:
        if self.kind == "MID_BOOK":
            if self.progress_percent is None or not 40 <= self.progress_percent <= 60:
                raise ValueError(
                    "MID_BOOK checkpoint requires progress_percent between 40 and 60"
                )
        elif self.progress_percent is not None:
            raise ValueError("ADVERSARIAL_REVIEW does not accept progress_percent")
        if self.kind == "ADVERSARIAL_REVIEW" and not self.independent:
            raise ValueError("Adversarial Review must be independent")
        return self


class ProductionCheckpointView(BaseModel):
    checkpoint_id: str
    book_id: str
    kind: str
    progress_percent: float | None
    status: GateResult
    findings: list[dict[str, Any]]
    actor_kind: EvidenceActorKind
    actor: str
    executor_identity: str | None
    snapshot_hash: str | None
    created_at: str


class SeriesClosureRequest(BaseModel):
    series_profile_id: str = Field(min_length=26, max_length=26)
    master_id: str = Field(min_length=1, max_length=64)
    master_manifest_hash: str = Field(min_length=64, max_length=64)
    used_asset_ids: list[str] = Field(default_factory=list)
    released_asset_ids: list[str] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(min_length=1)
    actor_kind: HumanActorKind
    actor: str = Field(min_length=1, max_length=255)


class SeriesClosureView(BaseModel):
    closure_id: str
    book_id: str
    series_profile_id: str
    master_id: str
    master_manifest_hash: str
    used_asset_ids: list[str]
    released_asset_ids: list[str]
    evidence: dict[str, Any]
    human_actor: str
    created_at: str


class SeriesProductionService:
    _CANON_TRANSITIONS: dict[str, set[str]] = {
        "PLANNED": {"RESERVED", "CROSS_REFERENCE_ONLY", "RELEASED"},
        "RESERVED": {"USED_DRAFT", "CROSS_REFERENCE_ONLY", "RELEASED"},
        "USED_DRAFT": {
            "RESERVED",
            "USED_ACCEPTED",
            "CROSS_REFERENCE_ONLY",
            "RELEASED",
        },
        "CROSS_REFERENCE_ONLY": {
            "RESERVED",
            "USED_DRAFT",
            "USED_ACCEPTED",
            "RELEASED",
        },
        "LEGACY_PROTECTED": {"RESERVED", "CROSS_REFERENCE_ONLY"},
        "USED_ACCEPTED": set(),
        "RELEASED": set(),
    }

    def __init__(self, data_dir: Path) -> None:
        self.projects = ProjectService(data_dir)
        self.contexts = BookContextService(data_dir)

    def _engine(self, book_id: str) -> Engine:
        self.projects.get_project(book_id)
        path = self.projects.projects_dir / book_id / "project.sqlite"
        return create_database(path)

    @staticmethod
    def _json(value: object) -> str:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

    @staticmethod
    def _loads(value: object, default: Any) -> Any:
        if not isinstance(value, str):
            return default
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return default

    @staticmethod
    def _require_human(actor_kind: str) -> None:
        if actor_kind not in {"HUMAN", "OWNER"}:
            raise SeriesProductionGateError(
                "this action requires HUMAN/OWNER authority"
            )

    def _current_heads(
        self,
        engine: Engine,
        book_id: str,
        chapter_id: str | None = None,
    ) -> tuple[Any, Any | None]:
        project = self.projects.get_project(book_id)
        architecture = project.architecture
        if architecture is None or architecture.authority_status not in {
            "APPROVED",
            "LOCKED",
        }:
            raise SeriesProductionGateError(
                "current Architecture must be HUMAN-approved"
            )
        authority = AuthorityService(engine)
        architecture_head = authority.get_head(architecture.entity_id)
        if architecture_head.status not in {"APPROVED", "LOCKED"}:
            raise SeriesProductionGateError(
                "current Architecture must be HUMAN-approved"
            )
        if chapter_id is None:
            return architecture_head, None
        chapter = next(
            (item for item in project.chapters if item.chapter_id == chapter_id),
            None,
        )
        if chapter is None or chapter.chapter_contract is None:
            raise SeriesProductionGateError("current Chapter Contract is missing")
        if chapter.chapter_contract.authority_status not in {"APPROVED", "LOCKED"}:
            raise SeriesProductionGateError(
                "current Chapter Contract must be HUMAN-approved"
            )
        chapter_head = authority.get_head(chapter.chapter_contract.entity_id)
        if chapter_head.status not in {"APPROVED", "LOCKED"}:
            raise SeriesProductionGateError(
                "current Chapter Contract must be HUMAN-approved"
            )
        return architecture_head, chapter_head

    def create_definition_pack(
        self,
        book_id: str,
        request: DefinitionPackCreateRequest,
    ) -> DefinitionPackView:
        self._require_human(request.actor_kind)
        engine = self._engine(book_id)
        try:
            payload = request.content.model_dump(mode="json")
            digest = content_hash(cast(dict[str, JSONValue], payload))
            definition_id = new_ulid()
            created_at = utc_now()
            with engine.begin() as connection:
                revision = int(
                    connection.execute(
                        text(
                            "SELECT COALESCE(MAX(revision),0)+1 "
                            "FROM definition_packs WHERE book_id=:book_id"
                        ),
                        {"book_id": book_id},
                    ).scalar_one()
                )
                connection.execute(
                    text(
                        "INSERT INTO definition_packs("
                        "definition_id,book_id,revision,content_json,content_hash,"
                        "status,created_by,created_at) VALUES "
                        "(:definition_id,:book_id,:revision,:content_json,:content_hash,"
                        "'DRAFT',:created_by,:created_at)"
                    ),
                    {
                        "definition_id": definition_id,
                        "book_id": book_id,
                        "revision": revision,
                        "content_json": self._json(payload),
                        "content_hash": digest,
                        "created_by": request.actor,
                        "created_at": created_at,
                    },
                )
        finally:
            engine.dispose()
        return self.get_definition_pack(book_id, definition_id)

    def _definition_view(self, row: Any) -> DefinitionPackView:
        return DefinitionPackView(
            definition_id=str(row["definition_id"]),
            book_id=str(row["book_id"]),
            revision=int(row["revision"]),
            content_hash=str(row["content_hash"]),
            content=DefinitionPackContent.model_validate(
                self._loads(row["content_json"], {})
            ),
            status=str(row["status"]),
            created_by=str(row["created_by"]),
            created_at=str(row["created_at"]),
            approved_by=cast(str | None, row["approved_by"]),
            approved_at=cast(str | None, row["approved_at"]),
        )

    def get_definition_pack(
        self,
        book_id: str,
        definition_id: str,
    ) -> DefinitionPackView:
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                row = (
                    connection.execute(
                        text(
                            "SELECT * FROM definition_packs "
                            "WHERE book_id=:book_id AND definition_id=:definition_id"
                        ),
                        {
                            "book_id": book_id,
                            "definition_id": definition_id,
                        },
                    )
                    .mappings()
                    .one_or_none()
                )
            if row is None:
                raise SeriesProductionError("Definition Pack not found")
            return self._definition_view(row)
        finally:
            engine.dispose()

    def latest_approved_definition(
        self,
        book_id: str,
    ) -> DefinitionPackView | None:
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                row = (
                    connection.execute(
                        text(
                            "SELECT * FROM definition_packs "
                            "WHERE book_id=:book_id AND status='APPROVED' "
                            "ORDER BY revision DESC LIMIT 1"
                        ),
                        {"book_id": book_id},
                    )
                    .mappings()
                    .one_or_none()
                )
            return None if row is None else self._definition_view(row)
        finally:
            engine.dispose()

    def approve_definition_pack(
        self,
        book_id: str,
        definition_id: str,
        request: DefinitionPackApprovalRequest,
    ) -> DefinitionPackView:
        self._require_human(request.actor_kind)
        current = self.get_definition_pack(book_id, definition_id)
        if current.status != "DRAFT":
            raise SeriesProductionGateError(
                "only a DRAFT Definition Pack can be approved"
            )
        blockers = current.content.blockers()
        if blockers:
            raise SeriesProductionGateError(
                "Definition Pack requires REWORK: " + ", ".join(blockers)
            )
        engine = self._engine(book_id)
        try:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "UPDATE definition_packs SET status='APPROVED',"
                        "approved_by=:actor,approved_at=:approved_at "
                        "WHERE definition_id=:definition_id AND status='DRAFT'"
                    ),
                    {
                        "actor": request.actor,
                        "approved_at": utc_now(),
                        "definition_id": definition_id,
                    },
                )
        finally:
            engine.dispose()
        return self.get_definition_pack(book_id, definition_id)

    def _production_contract_view(
        self,
        row: Any,
    ) -> ChapterProductionContractView:
        return ChapterProductionContractView(
            production_contract_id=str(row["production_contract_id"]),
            book_id=str(row["book_id"]),
            chapter_id=str(row["chapter_id"]),
            architecture_revision_id=str(row["architecture_revision_id"]),
            architecture_revision_hash=str(row["architecture_revision_hash"]),
            chapter_contract_revision_id=str(row["chapter_contract_revision_id"]),
            chapter_contract_revision_hash=str(
                row["chapter_contract_revision_hash"]
            ),
            content_hash=str(row["content_hash"]),
            content=ChapterProductionContractContent.model_validate(
                self._loads(row["content_json"], {})
            ),
            status=str(row["status"]),
            created_by=str(row["created_by"]),
            created_at=str(row["created_at"]),
            approved_by=cast(str | None, row["approved_by"]),
            approved_at=cast(str | None, row["approved_at"]),
        )

    def create_production_contract(
        self,
        book_id: str,
        chapter_id: str,
        request: ChapterProductionContractCreateRequest,
    ) -> ChapterProductionContractView:
        self._require_human(request.actor_kind)
        engine = self._engine(book_id)
        try:
            architecture_head, chapter_head = self._current_heads(
                engine,
                book_id,
                chapter_id,
            )
            assert chapter_head is not None
            payload = request.content.model_dump(mode="json")
            digest = content_hash(cast(dict[str, JSONValue], payload))
            contract_id = new_ulid()
            created_at = utc_now()
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT INTO chapter_production_contracts("
                        "production_contract_id,book_id,chapter_id,"
                        "architecture_revision_id,architecture_revision_hash,"
                        "chapter_contract_revision_id,chapter_contract_revision_hash,"
                        "content_json,content_hash,status,created_by,created_at) VALUES "
                        "(:id,:book_id,:chapter_id,:architecture_revision_id,"
                        ":architecture_revision_hash,:chapter_contract_revision_id,"
                        ":chapter_contract_revision_hash,:content_json,:content_hash,"
                        "'DRAFT',:created_by,:created_at)"
                    ),
                    {
                        "id": contract_id,
                        "book_id": book_id,
                        "chapter_id": chapter_id,
                        "architecture_revision_id": architecture_head.revision_id,
                        "architecture_revision_hash": architecture_head.revision_hash,
                        "chapter_contract_revision_id": chapter_head.revision_id,
                        "chapter_contract_revision_hash": chapter_head.revision_hash,
                        "content_json": self._json(payload),
                        "content_hash": digest,
                        "created_by": request.actor,
                        "created_at": created_at,
                    },
                )
        finally:
            engine.dispose()
        return self.get_production_contract(
            book_id,
            chapter_id,
            contract_id,
        )

    def get_production_contract(
        self,
        book_id: str,
        chapter_id: str,
        contract_id: str,
    ) -> ChapterProductionContractView:
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                row = (
                    connection.execute(
                        text(
                            "SELECT * FROM chapter_production_contracts "
                            "WHERE book_id=:book_id AND chapter_id=:chapter_id "
                            "AND production_contract_id=:contract_id"
                        ),
                        {
                            "book_id": book_id,
                            "chapter_id": chapter_id,
                            "contract_id": contract_id,
                        },
                    )
                    .mappings()
                    .one_or_none()
                )
            if row is None:
                raise SeriesProductionError(
                    "Chapter Production Contract not found"
                )
            return self._production_contract_view(row)
        finally:
            engine.dispose()

    def latest_approved_production_contract(
        self,
        book_id: str,
        chapter_id: str,
    ) -> ChapterProductionContractView | None:
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                row = (
                    connection.execute(
                        text(
                            "SELECT * FROM chapter_production_contracts "
                            "WHERE book_id=:book_id AND chapter_id=:chapter_id "
                            "AND status='APPROVED' ORDER BY created_at DESC LIMIT 1"
                        ),
                        {
                            "book_id": book_id,
                            "chapter_id": chapter_id,
                        },
                    )
                    .mappings()
                    .one_or_none()
                )
            return None if row is None else self._production_contract_view(row)
        finally:
            engine.dispose()

    def approve_production_contract(
        self,
        book_id: str,
        chapter_id: str,
        contract_id: str,
        request: ChapterProductionContractApprovalRequest,
    ) -> ChapterProductionContractView:
        self._require_human(request.actor_kind)
        current = self.get_production_contract(
            book_id,
            chapter_id,
            contract_id,
        )
        if current.status != "DRAFT":
            raise SeriesProductionGateError(
                "only a DRAFT Chapter Production Contract can be approved"
            )
        blockers = current.content.blockers()
        if blockers:
            raise SeriesProductionGateError(
                "Chapter Production Contract requires REWORK: "
                + ", ".join(blockers)
            )
        engine = self._engine(book_id)
        try:
            architecture_head, chapter_head = self._current_heads(
                engine,
                book_id,
                chapter_id,
            )
            assert chapter_head is not None
            if (
                current.architecture_revision_id
                != architecture_head.revision_id
                or current.architecture_revision_hash
                != architecture_head.revision_hash
                or current.chapter_contract_revision_id
                != chapter_head.revision_id
                or current.chapter_contract_revision_hash
                != chapter_head.revision_hash
            ):
                raise SeriesProductionGateError(
                    "Chapter Production Contract is stale against current authority"
                )
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "UPDATE chapter_production_contracts SET status='APPROVED',"
                        "approved_by=:actor,approved_at=:approved_at "
                        "WHERE production_contract_id=:contract_id AND status='DRAFT'"
                    ),
                    {
                        "actor": request.actor,
                        "approved_at": utc_now(),
                        "contract_id": contract_id,
                    },
                )
        finally:
            engine.dispose()
        return self.get_production_contract(
            book_id,
            chapter_id,
            contract_id,
        )

    def create_canon_asset(
        self,
        request: SeriesCanonAssetCreateRequest,
    ) -> SeriesCanonAssetView:
        if request.book_id is None:
            raise SeriesProductionGateError(
                "book_id is required in the first executable Series Canon slice"
            )
        engine = self._engine(request.book_id)
        try:
            asset_id = new_ulid()
            now = utc_now()
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT INTO series_canon_assets("
                        "asset_id,series_profile_id,book_id,asset_type,asset_key,"
                        "description,status,source_revision_id,source_revision_hash,"
                        "provenance_json,created_by,created_at,updated_at) VALUES "
                        "(:asset_id,:series_profile_id,:book_id,:asset_type,:asset_key,"
                        ":description,:status,:source_revision_id,:source_revision_hash,"
                        ":provenance_json,:created_by,:created_at,:updated_at)"
                    ),
                    {
                        "asset_id": asset_id,
                        "series_profile_id": request.series_profile_id,
                        "book_id": request.book_id,
                        "asset_type": request.asset_type,
                        "asset_key": request.asset_key,
                        "description": request.description,
                        "status": request.status,
                        "source_revision_id": request.source_revision_id,
                        "source_revision_hash": request.source_revision_hash,
                        "provenance_json": self._json(request.provenance),
                        "created_by": request.actor,
                        "created_at": now,
                        "updated_at": now,
                    },
                )
        finally:
            engine.dispose()
        return self.get_canon_asset(request.book_id, asset_id)

    def get_canon_asset(
        self,
        book_id: str,
        asset_id: str,
    ) -> SeriesCanonAssetView:
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                row = (
                    connection.execute(
                        text(
                            "SELECT * FROM series_canon_assets "
                            "WHERE asset_id=:asset_id"
                        ),
                        {"asset_id": asset_id},
                    )
                    .mappings()
                    .one_or_none()
                )
            if row is None:
                raise SeriesProductionError("Series Canon asset not found")
            return SeriesCanonAssetView(
                asset_id=str(row["asset_id"]),
                series_profile_id=str(row["series_profile_id"]),
                book_id=cast(str | None, row["book_id"]),
                asset_type=str(row["asset_type"]),
                asset_key=str(row["asset_key"]),
                description=str(row["description"]),
                status=cast(CanonStatus, row["status"]),
                source_revision_id=cast(
                    str | None,
                    row["source_revision_id"],
                ),
                source_revision_hash=cast(
                    str | None,
                    row["source_revision_hash"],
                ),
                provenance=cast(
                    dict[str, Any],
                    self._loads(row["provenance_json"], {}),
                ),
                created_by=str(row["created_by"]),
                created_at=str(row["created_at"]),
                updated_at=str(row["updated_at"]),
            )
        finally:
            engine.dispose()

    def transition_canon_asset(
        self,
        book_id: str,
        asset_id: str,
        request: SeriesCanonTransitionRequest,
    ) -> SeriesCanonAssetView:
        current = self.get_canon_asset(book_id, asset_id)
        if request.status == current.status:
            return current
        if request.status not in self._CANON_TRANSITIONS[current.status]:
            raise SeriesProductionGateError(
                "invalid Series Canon transition: "
                f"{current.status} -> {request.status}"
            )
        provenance = {
            **current.provenance,
            "last_transition": {
                "from": current.status,
                "to": request.status,
                "actor": request.actor,
                "evidence": request.evidence,
                "at": utc_now(),
            },
        }
        engine = self._engine(book_id)
        try:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "UPDATE series_canon_assets SET status=:status,"
                        "provenance_json=:provenance_json,updated_at=:updated_at "
                        "WHERE asset_id=:asset_id"
                    ),
                    {
                        "status": request.status,
                        "provenance_json": self._json(provenance),
                        "updated_at": utc_now(),
                        "asset_id": asset_id,
                    },
                )
        finally:
            engine.dispose()
        return self.get_canon_asset(book_id, asset_id)

    def record_uniqueness(
        self,
        book_id: str,
        chapter_id: str,
        request: UniquenessEvidenceRequest,
    ) -> UniquenessEvidenceView:
        engine = self._engine(book_id)
        try:
            architecture_head, chapter_head = self._current_heads(
                engine,
                book_id,
                chapter_id,
            )
            assert chapter_head is not None
            ledger_id = new_ulid()
            created_at = utc_now()
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT INTO book_uniqueness_ledger("
                        "ledger_id,book_id,chapter_id,architecture_revision_id,"
                        "architecture_revision_hash,chapter_contract_revision_id,"
                        "chapter_contract_revision_hash,status,evidence_json,actor_kind,"
                        "actor,created_at) VALUES (:ledger_id,:book_id,:chapter_id,"
                        ":architecture_revision_id,:architecture_revision_hash,"
                        ":chapter_contract_revision_id,:chapter_contract_revision_hash,"
                        ":status,:evidence_json,:actor_kind,:actor,:created_at)"
                    ),
                    {
                        "ledger_id": ledger_id,
                        "book_id": book_id,
                        "chapter_id": chapter_id,
                        "architecture_revision_id": architecture_head.revision_id,
                        "architecture_revision_hash": architecture_head.revision_hash,
                        "chapter_contract_revision_id": chapter_head.revision_id,
                        "chapter_contract_revision_hash": chapter_head.revision_hash,
                        "status": request.status,
                        "evidence_json": self._json(request.evidence),
                        "actor_kind": request.actor_kind,
                        "actor": request.actor,
                        "created_at": created_at,
                    },
                )
            return UniquenessEvidenceView(
                ledger_id=ledger_id,
                book_id=book_id,
                chapter_id=chapter_id,
                architecture_revision_id=architecture_head.revision_id,
                architecture_revision_hash=architecture_head.revision_hash,
                chapter_contract_revision_id=chapter_head.revision_id,
                chapter_contract_revision_hash=chapter_head.revision_hash,
                status=request.status,
                evidence=request.evidence,
                actor_kind=request.actor_kind,
                actor=request.actor,
                created_at=created_at,
            )
        finally:
            engine.dispose()

    @staticmethod
    def _latest_row(
        engine: Engine,
        query: str,
        params: dict[str, object],
    ) -> Any | None:
        with engine.connect() as connection:
            return (
                connection.execute(text(query), params)
                .mappings()
                .one_or_none()
            )

    def _latest_uniqueness(
        self,
        engine: Engine,
        book_id: str,
        chapter_id: str,
    ) -> Any | None:
        return self._latest_row(
            engine,
            "SELECT * FROM book_uniqueness_ledger "
            "WHERE book_id=:book_id AND chapter_id=:chapter_id "
            "ORDER BY created_at DESC LIMIT 1",
            {"book_id": book_id, "chapter_id": chapter_id},
        )

    def admit_chapter(
        self,
        book_id: str,
        chapter_id: str,
        request: ChapterAdmissionRequest,
    ) -> ChapterAdmissionStatusView:
        self._require_human(request.actor_kind)
        explicit_blockers = request.checks.blockers()
        if explicit_blockers:
            raise SeriesProductionGateError(
                "Chapter admission checks require REWORK: "
                + ", ".join(explicit_blockers)
            )
        definition = self.latest_approved_definition(book_id)
        if definition is None:
            raise SeriesProductionGateError(
                "current approved Definition Pack is required"
            )
        engine = self._engine(book_id)
        try:
            architecture_head, chapter_head = self._current_heads(
                engine,
                book_id,
                chapter_id,
            )
            assert chapter_head is not None
            production_contract = self.latest_approved_production_contract(
                book_id,
                chapter_id,
            )
            if production_contract is None:
                raise SeriesProductionGateError(
                    "current approved Chapter Production Contract is required"
                )
            if (
                production_contract.architecture_revision_id
                != architecture_head.revision_id
                or production_contract.architecture_revision_hash
                != architecture_head.revision_hash
                or production_contract.chapter_contract_revision_id
                != chapter_head.revision_id
                or production_contract.chapter_contract_revision_hash
                != chapter_head.revision_hash
            ):
                raise SeriesProductionGateError(
                    "Chapter Production Contract is stale"
                )
            uniqueness = self._latest_uniqueness(
                engine,
                book_id,
                chapter_id,
            )
            if uniqueness is None or uniqueness["status"] != "PASS":
                raise SeriesProductionGateError(
                    "current uniqueness / overlap evidence must PASS"
                )
            if (
                uniqueness["architecture_revision_id"]
                != architecture_head.revision_id
                or uniqueness["architecture_revision_hash"]
                != architecture_head.revision_hash
                or uniqueness["chapter_contract_revision_id"]
                != chapter_head.revision_id
                or uniqueness["chapter_contract_revision_hash"]
                != chapter_head.revision_hash
            ):
                raise SeriesProductionGateError(
                    "uniqueness evidence is stale"
                )
            admission_id = new_ulid()
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT INTO chapter_admissions("
                        "admission_id,book_id,chapter_id,definition_id,definition_hash,"
                        "architecture_revision_id,architecture_revision_hash,"
                        "chapter_contract_revision_id,chapter_contract_revision_hash,"
                        "production_contract_id,production_contract_hash,checks_json,"
                        "status,actor_kind,actor,reason,created_at) VALUES "
                        "(:admission_id,:book_id,:chapter_id,:definition_id,"
                        ":definition_hash,:architecture_revision_id,"
                        ":architecture_revision_hash,:chapter_contract_revision_id,"
                        ":chapter_contract_revision_hash,:production_contract_id,"
                        ":production_contract_hash,:checks_json,'WRITING_ALLOWED',"
                        ":actor_kind,:actor,:reason,:created_at)"
                    ),
                    {
                        "admission_id": admission_id,
                        "book_id": book_id,
                        "chapter_id": chapter_id,
                        "definition_id": definition.definition_id,
                        "definition_hash": definition.content_hash,
                        "architecture_revision_id": architecture_head.revision_id,
                        "architecture_revision_hash": architecture_head.revision_hash,
                        "chapter_contract_revision_id": chapter_head.revision_id,
                        "chapter_contract_revision_hash": chapter_head.revision_hash,
                        "production_contract_id": (
                            production_contract.production_contract_id
                        ),
                        "production_contract_hash": (
                            production_contract.content_hash
                        ),
                        "checks_json": self._json(
                            request.checks.model_dump(mode="json")
                        ),
                        "actor_kind": request.actor_kind,
                        "actor": request.actor,
                        "reason": request.reason,
                        "created_at": utc_now(),
                    },
                )
        finally:
            engine.dispose()
        return self.admission_status(book_id, chapter_id)

    def _latest_checkpoint(
        self,
        engine: Engine,
        book_id: str,
        kind: str,
    ) -> Any | None:
        return self._latest_row(
            engine,
            "SELECT * FROM production_checkpoints "
            "WHERE book_id=:book_id AND kind=:kind "
            "ORDER BY created_at DESC LIMIT 1",
            {"book_id": book_id, "kind": kind},
        )

    def _current_character_count(
        self,
        engine: Engine,
        book_id: str,
    ) -> int:
        with engine.connect() as connection:
            rows = connection.execute(
                text(
                    "SELECT r.content_json FROM manuscript_units u "
                    "JOIN authority_heads h ON h.entity_id=u.authority_entity_id "
                    "JOIN revisions r ON r.revision_id=h.revision_id "
                    "WHERE u.book_id=:book_id ORDER BY u.ordinal"
                ),
                {"book_id": book_id},
            ).all()
        total = 0
        for row in rows:
            payload = self._loads(row[0], {})
            if isinstance(payload, dict) and isinstance(payload.get("text"), str):
                total += len(payload["text"])
        return total

    def _mid_book_blocker(
        self,
        engine: Engine,
        book_id: str,
    ) -> str | None:
        with engine.connect() as connection:
            target = connection.execute(
                text(
                    "SELECT target_characters FROM book_context_settings "
                    "WHERE book_id=:book_id"
                ),
                {"book_id": book_id},
            ).scalar_one_or_none()
        if not isinstance(target, int) or target <= 0:
            return None
        progress = self._current_character_count(engine, book_id) / target * 100
        if progress < 40:
            return None
        latest = self._latest_checkpoint(engine, book_id, "MID_BOOK")
        if latest is None:
            return "MID_BOOK audit required after 40% planned manuscript progress"
        if latest["status"] == "BLOCKING":
            return "MID_BOOK audit has unresolved BLOCKING findings"
        return None

    def admission_status(
        self,
        book_id: str,
        chapter_id: str,
    ) -> ChapterAdmissionStatusView:
        blockers: list[str] = []
        definition = self.latest_approved_definition(book_id)
        if definition is None:
            blockers.append("approved Definition Pack missing")
        engine = self._engine(book_id)
        try:
            try:
                architecture_head, chapter_head = self._current_heads(
                    engine,
                    book_id,
                    chapter_id,
                )
            except SeriesProductionGateError as exc:
                return ChapterAdmissionStatusView(
                    book_id=book_id,
                    chapter_id=chapter_id,
                    writing_allowed=False,
                    blockers=[str(exc)],
                )
            assert chapter_head is not None
            production_contract = self.latest_approved_production_contract(
                book_id,
                chapter_id,
            )
            if production_contract is None:
                blockers.append("approved Chapter Production Contract missing")
            uniqueness = self._latest_uniqueness(
                engine,
                book_id,
                chapter_id,
            )
            if uniqueness is None:
                blockers.append("uniqueness evidence missing")
            elif uniqueness["status"] != "PASS":
                blockers.append("uniqueness evidence is not PASS")
            elif (
                uniqueness["architecture_revision_id"]
                != architecture_head.revision_id
                or uniqueness["architecture_revision_hash"]
                != architecture_head.revision_hash
                or uniqueness["chapter_contract_revision_id"]
                != chapter_head.revision_id
                or uniqueness["chapter_contract_revision_hash"]
                != chapter_head.revision_hash
            ):
                blockers.append("uniqueness evidence is stale")
            admission = self._latest_row(
                engine,
                "SELECT * FROM chapter_admissions "
                "WHERE book_id=:book_id AND chapter_id=:chapter_id "
                "ORDER BY created_at DESC LIMIT 1",
                {"book_id": book_id, "chapter_id": chapter_id},
            )
            if admission is None:
                blockers.append("HUMAN chapter admission missing")
            elif admission["status"] != "WRITING_ALLOWED":
                blockers.append("latest chapter admission is revoked")
            else:
                if definition is None or (
                    admission["definition_id"] != definition.definition_id
                    or admission["definition_hash"] != definition.content_hash
                ):
                    blockers.append(
                        "chapter admission is stale against Definition Pack"
                    )
                if (
                    admission["architecture_revision_id"]
                    != architecture_head.revision_id
                    or admission["architecture_revision_hash"]
                    != architecture_head.revision_hash
                    or admission["chapter_contract_revision_id"]
                    != chapter_head.revision_id
                    or admission["chapter_contract_revision_hash"]
                    != chapter_head.revision_hash
                ):
                    blockers.append(
                        "chapter admission is stale against current authority"
                    )
                if production_contract is None or (
                    admission["production_contract_id"]
                    != production_contract.production_contract_id
                    or admission["production_contract_hash"]
                    != production_contract.content_hash
                ):
                    blockers.append(
                        "chapter admission is stale against production contract"
                    )
            mid_book = self._mid_book_blocker(engine, book_id)
            if mid_book is not None:
                blockers.append(mid_book)
            return ChapterAdmissionStatusView(
                book_id=book_id,
                chapter_id=chapter_id,
                writing_allowed=not blockers,
                blockers=blockers,
                admission_id=(
                    str(admission["admission_id"])
                    if admission is not None
                    else None
                ),
                definition_id=(
                    definition.definition_id
                    if definition is not None
                    else None
                ),
                architecture_revision_id=architecture_head.revision_id,
                chapter_contract_revision_id=chapter_head.revision_id,
                production_contract_id=(
                    production_contract.production_contract_id
                    if production_contract is not None
                    else None
                ),
            )
        finally:
            engine.dispose()

    def require_writing_allowed(
        self,
        book_id: str,
        chapter_id: str,
    ) -> None:
        status = self.admission_status(book_id, chapter_id)
        if not status.writing_allowed:
            raise SeriesProductionGateError(
                "WRITING_NOT_ALLOWED: " + "; ".join(status.blockers)
            )

    def record_checkpoint(
        self,
        book_id: str,
        request: ProductionCheckpointRequest,
    ) -> ProductionCheckpointView:
        if request.kind == "ADVERSARIAL_REVIEW" and not request.executor_identity:
            raise SeriesProductionGateError(
                "Adversarial Review requires an explicit independent executor identity"
            )
        engine = self._engine(book_id)
        try:
            checkpoint_id = new_ulid()
            created_at = utc_now()
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT INTO production_checkpoints("
                        "checkpoint_id,book_id,kind,progress_percent,status,findings_json,"
                        "actor_kind,actor,executor_identity,snapshot_hash,created_at) VALUES "
                        "(:checkpoint_id,:book_id,:kind,:progress_percent,:status,"
                        ":findings_json,:actor_kind,:actor,:executor_identity,"
                        ":snapshot_hash,:created_at)"
                    ),
                    {
                        "checkpoint_id": checkpoint_id,
                        "book_id": book_id,
                        "kind": request.kind,
                        "progress_percent": request.progress_percent,
                        "status": request.status,
                        "findings_json": self._json(
                            {
                                "independent": request.independent,
                                "findings": request.findings,
                            }
                        ),
                        "actor_kind": request.actor_kind,
                        "actor": request.actor,
                        "executor_identity": request.executor_identity,
                        "snapshot_hash": request.snapshot_hash,
                        "created_at": created_at,
                    },
                )
            return ProductionCheckpointView(
                checkpoint_id=checkpoint_id,
                book_id=book_id,
                kind=request.kind,
                progress_percent=request.progress_percent,
                status=request.status,
                findings=request.findings,
                actor_kind=request.actor_kind,
                actor=request.actor,
                executor_identity=request.executor_identity,
                snapshot_hash=request.snapshot_hash,
                created_at=created_at,
            )
        finally:
            engine.dispose()

    def adversarial_review_gate(
        self,
        book_id: str,
    ) -> tuple[bool, list[str]]:
        engine = self._engine(book_id)
        try:
            latest = self._latest_checkpoint(
                engine,
                book_id,
                "ADVERSARIAL_REVIEW",
            )
            if latest is None:
                return False, ["independent Adversarial Review missing"]
            if latest["status"] == "BLOCKING":
                return False, [
                    "Adversarial Review has unresolved BLOCKING findings"
                ]
            payload = self._loads(latest["findings_json"], {})
            if not isinstance(payload, dict) or payload.get("independent") is not True:
                return False, [
                    "Adversarial Review independence evidence missing"
                ]
            return True, []
        finally:
            engine.dispose()

    def close_series_book(
        self,
        book_id: str,
        request: SeriesClosureRequest,
    ) -> SeriesClosureView:
        self._require_human(request.actor_kind)
        context = self.contexts.get_context(book_id)
        if (
            context.series_profile is None
            or context.series_profile.profile_id != request.series_profile_id
        ):
            raise SeriesProductionGateError(
                "Series Closure must use the book's bound Series Profile"
            )
        engine = self._engine(book_id)
        try:
            master = self._latest_row(
                engine,
                "SELECT master_id,manifest_hash,status FROM literary_masters "
                "WHERE book_id=:book_id AND master_id=:master_id",
                {
                    "book_id": book_id,
                    "master_id": request.master_id,
                },
            )
            if master is None or master["status"] != "LOCKED":
                raise SeriesProductionGateError(
                    "exact LOCKED Literary Master is required"
                )
            if master["manifest_hash"] != request.master_manifest_hash:
                raise SeriesProductionGateError(
                    "Literary Master manifest hash mismatch"
                )
            overlap = set(request.used_asset_ids) & set(
                request.released_asset_ids
            )
            if overlap:
                raise SeriesProductionGateError(
                    "an asset cannot be both used and released"
                )
            for asset_id in request.used_asset_ids:
                self.transition_canon_asset(
                    book_id,
                    asset_id,
                    SeriesCanonTransitionRequest(
                        status="USED_ACCEPTED",
                        actor=request.actor,
                        evidence={
                            "literary_master_id": request.master_id,
                            "manifest_hash": request.master_manifest_hash,
                            **request.evidence,
                        },
                    ),
                )
            for asset_id in request.released_asset_ids:
                self.transition_canon_asset(
                    book_id,
                    asset_id,
                    SeriesCanonTransitionRequest(
                        status="RELEASED",
                        actor=request.actor,
                        evidence={
                            "literary_master_id": request.master_id,
                            "manifest_hash": request.master_manifest_hash,
                            **request.evidence,
                        },
                    ),
                )
            closure_id = new_ulid()
            created_at = utc_now()
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT INTO series_closures("
                        "closure_id,book_id,series_profile_id,master_id,"
                        "master_manifest_hash,used_asset_ids_json,"
                        "released_asset_ids_json,evidence_json,human_actor,created_at) "
                        "VALUES (:closure_id,:book_id,:series_profile_id,:master_id,"
                        ":master_manifest_hash,:used_asset_ids_json,"
                        ":released_asset_ids_json,:evidence_json,:human_actor,:created_at)"
                    ),
                    {
                        "closure_id": closure_id,
                        "book_id": book_id,
                        "series_profile_id": request.series_profile_id,
                        "master_id": request.master_id,
                        "master_manifest_hash": request.master_manifest_hash,
                        "used_asset_ids_json": self._json(
                            request.used_asset_ids
                        ),
                        "released_asset_ids_json": self._json(
                            request.released_asset_ids
                        ),
                        "evidence_json": self._json(request.evidence),
                        "human_actor": request.actor,
                        "created_at": created_at,
                    },
                )
            return SeriesClosureView(
                closure_id=closure_id,
                book_id=book_id,
                series_profile_id=request.series_profile_id,
                master_id=request.master_id,
                master_manifest_hash=request.master_manifest_hash,
                used_asset_ids=request.used_asset_ids,
                released_asset_ids=request.released_asset_ids,
                evidence=request.evidence,
                human_actor=request.actor,
                created_at=created_at,
            )
        finally:
            engine.dispose()
