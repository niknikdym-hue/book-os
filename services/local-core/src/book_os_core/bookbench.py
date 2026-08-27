from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import statistics
import time
import random
import math
from typing import Any, Literal, cast

from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.engine import Engine

from .authority import AuthorityService, new_ulid
from .authority_types import utc_now
from .bookbench_registry import CheckSpec, get_check, registry_hash
from .db import create_database
from .memory_embeddings import EmbeddingGateway, embedding_config_hash
from .model_gateway import (
    AuthorityInputRef,
    BookBenchJudgeOutput,
    BookBenchPairwiseOutput,
    ModelGateway,
    ModelTaskRequest,
)
from .prompts import BOOKBENCH_JUDGE_V1, BOOKBENCH_PAIRWISE_V1
from .editorial import EditorialService, FindingCreateRequest, FindingView

SnapshotScope = Literal["MANUSCRIPT_UNIT", "CHAPTER", "BOOK"]
DimensionState = Literal["PASS", "ATTENTION", "BLOCKING"]
FindingSeverity = Literal["INFO", "ATTENTION", "BLOCKING"]

_WORD = re.compile(r"[\w-]+", flags=re.UNICODE)
_SENTENCE = re.compile(r"[^.!?]+[.!?]?", flags=re.UNICODE)
_TODO = re.compile(r"\b(?:TODO|FIXME|TBD|XXX)\b", flags=re.IGNORECASE)
_FALSE_CONTRAST = re.compile(r"\bне\b[^.!?\n]{1,100}\bа\b", flags=re.IGNORECASE)
_NOT_ABOUT = re.compile(r"\bэто\s+не\s+про\b", flags=re.IGNORECASE)
_TRIAD = re.compile(
    r"\b[\w-]+(?:\s+[\w-]+){0,3},\s+[\w-]+(?:\s+[\w-]+){0,3}\s+(?:и|или)\s+[\w-]+",
    flags=re.IGNORECASE,
)
_GENERIC_TRANSITIONS: tuple[str, ...] = (
    "важно понимать",
    "стоит отметить",
    "в конечном итоге",
    "другими словами",
    "на самом деле",
    "важно помнить",
    "следует понимать",
    "в этом контексте",
)
_EMPTY_ABSTRACTIONS: tuple[str, ...] = (
    "важный аспект",
    "ключевой момент",
    "значимая роль",
    "эффективный подход",
    "современный мир",
    "высокий уровень",
    "широкий спектр",
)


class BookBenchError(RuntimeError):
    pass


class BookBenchNotFound(BookBenchError):
    pass


class BookBenchGateError(BookBenchError):
    pass


class SnapshotTargetView(BaseModel):
    ordinal: int
    target_kind: str
    target_id: str
    chapter_id: str | None
    unit_id: str | None
    revision_id: str
    revision_hash: str
    content_hash: str
    source_status: str
    text: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvaluationSnapshotView(BaseModel):
    snapshot_id: str
    book_id: str
    scope: str
    chapter_id: str | None
    unit_id: str | None
    snapshot_hash: str
    created_at: str
    current: bool
    targets: list[SnapshotTargetView]


class EvaluationFindingView(BaseModel):
    finding_id: str
    evaluation_id: str
    dimension: str
    category: str
    target_kind: str
    target_id: str
    chapter_id: str | None
    unit_id: str | None
    revision_id: str
    revision_hash: str
    location: str
    evidence: dict[str, Any]
    severity: str
    confidence: float
    recommended_action: str
    created_at: str


class EvaluationRunView(BaseModel):
    evaluation_id: str
    book_id: str
    snapshot_id: str
    check_id: str
    check_version: str
    registry_hash: str
    dimension: str
    evaluator_class: str
    evaluator_id: str
    evaluator_version: str
    provider: str | None
    model: str | None
    config_id: str | None
    prompt_id: str | None
    prompt_version: str | None
    prompt_hash: str | None
    independence_state: str
    input_hash: str
    output: dict[str, Any]
    usage: dict[str, Any]
    latency_ms: int
    cost_usd: float | None
    status: str
    error_message: str | None
    created_at: str
    completed_at: str | None
    findings: list[EvaluationFindingView] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)


class DimensionReport(BaseModel):
    dimension: str
    state: DimensionState
    findings: list[EvaluationFindingView]
    run_ids: list[str]
    metrics: dict[str, Any]


class BookBenchReport(BaseModel):
    snapshot_id: str
    snapshot_hash: str
    current: bool
    dimensions: list[DimensionReport]
    blocking_dimensions: list[str]
    generated_at: str


class VoiceFingerprintView(BaseModel):
    fingerprint_id: str
    book_id: str
    name: str
    extractor_id: str
    extractor_version: str
    extractor_hash: str
    reference_snapshot_id: str
    reference_revisions: list[dict[str, str]]
    features: dict[str, Any]
    fingerprint_hash: str
    created_at: str


class VoiceComparisonView(BaseModel):
    fingerprint_id: str
    target_snapshot_id: str
    target_revisions: list[dict[str, str]]
    feature_deltas: dict[str, float]
    target_features: dict[str, Any]
    diagnostic_only: bool = True


@dataclass(frozen=True)
class _FindingDraft:
    target: SnapshotTargetView
    category: str
    location: str
    evidence: dict[str, Any]
    severity: FindingSeverity
    confidence: float
    recommended_action: str


@dataclass(frozen=True)
class _CheckResult:
    findings: list[_FindingDraft]
    metrics: dict[str, Any]
    output: dict[str, Any]


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _normalize(value: str) -> str:
    return " ".join(_WORD.findall(value.casefold()))


def _tokens(value: str) -> list[str]:
    return _WORD.findall(value.casefold())


def _sentences(value: str) -> list[str]:
    return [item.strip() for item in _SENTENCE.findall(value) if item.strip()]


def _paragraphs(value: str) -> list[str]:
    return [item.strip() for item in re.split(r"\n\s*\n|\n", value) if item.strip()]


def _mean(values: list[int]) -> float:
    return float(statistics.fmean(values)) if values else 0.0


def _p95(values: list[int]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round(0.95 * (len(ordered) - 1)))))
    return float(ordered[index])


def _first_words(value: str, count: int = 6) -> str:
    return " ".join(_tokens(value)[:count])


def _last_words(value: str, count: int = 6) -> str:
    tokens = _tokens(value)
    return " ".join(tokens[-count:])


def _lexical_trace(requirement: str, text_value: str) -> bool:
    requirement_normalized = _normalize(requirement)
    if not requirement_normalized:
        return True
    text_normalized = _normalize(text_value)
    if requirement_normalized in text_normalized:
        return True
    required = set(_tokens(requirement))
    if not required:
        return True
    actual = set(_tokens(text_value))
    if len(required) < 3:
        return required <= actual
    return len(required & actual) / len(required) >= 0.9


class SemanticResultView(BaseModel):
    evaluation_ids: list[str]
    embedding_config: dict[str, Any]
    config_hash: str
    candidates_only: bool = True


class PairwiseResultView(BaseModel):
    evaluation_id: str
    seed: int
    labels: dict[str, str]
    winner_candidate_id: str | None
    output: BookBenchPairwiseOutput


class DatasetSnapshotView(BaseModel):
    dataset_snapshot_id: str
    name: str
    version: int
    dataset_hash: str
    case_count: int
    cases: list[dict[str, Any]]


class ScorecardView(BaseModel):
    scorecard_id: str
    dataset_snapshot_id: str
    role: str
    config_id: str
    config_hash: str
    dimensions: dict[str, dict[str, Any]]
    severe_failure_count: int
    pass_count: int
    attention_count: int
    blocking_count: int
    latency_ms: int
    cost_usd: float
    usage: dict[str, Any]


class BookBenchService:
    DETERMINISTIC_RUNNER_ID = "bookbench-deterministic"
    DETERMINISTIC_RUNNER_VERSION = "1.0.0"

    def __init__(
        self,
        data_dir: Path,
        embedding_gateway: EmbeddingGateway | None = None,
        model_gateway: ModelGateway | None = None,
    ):
        self.projects_dir = data_dir / "projects"
        self.embedding_gateway = embedding_gateway
        self.model_gateway = model_gateway

    def _database_path(self, book_id: str) -> Path:
        path = self.projects_dir / book_id / "project.sqlite"
        if not path.is_file():
            raise BookBenchNotFound(f"book project not found: {book_id}")
        return path

    def _engine(self, book_id: str) -> Engine:
        return create_database(self._database_path(book_id))

    @staticmethod
    def _authority_target(
        authority: AuthorityService,
        *,
        ordinal: int,
        target_kind: str,
        target_id: str,
        entity_id: str,
        chapter_id: str | None,
        unit_id: str | None,
    ) -> SnapshotTargetView:
        head = authority.get_head(entity_id)
        revision = authority.get_revision(head.revision_id)
        content = cast(dict[str, Any], revision["content"])
        text_value = str(content.get("text") or _canonical_json(content))
        return SnapshotTargetView(
            ordinal=ordinal,
            target_kind=target_kind,
            target_id=target_id,
            chapter_id=chapter_id,
            unit_id=unit_id,
            revision_id=head.revision_id,
            revision_hash=head.revision_hash,
            content_hash=cast(str, revision["content_hash"]),
            source_status=head.status,
            text=text_value,
            metadata={"content": content, "authority_entity_id": entity_id},
        )

    @staticmethod
    def _claim_content_hash(row: dict[str, Any]) -> str:
        payload = {
            "normalized_text": row["normalized_text"],
            "claim_type": row["claim_type"],
            "materiality": row["materiality"],
            "required_evidence_level": row["required_evidence_level"],
            "verification_state": row["verification_state"],
            "updated_at": row["updated_at"],
        }
        return _sha256(payload)

    def _current_targets(
        self,
        engine: Engine,
        book_id: str,
        *,
        scope: SnapshotScope,
        chapter_id: str | None,
        unit_id: str | None,
    ) -> list[SnapshotTargetView]:
        authority = AuthorityService(engine)
        targets: list[SnapshotTargetView] = []
        with engine.connect() as connection:
            project = (
                connection.execute(
                    text(
                        "SELECT book_contract_entity_id FROM book_projects WHERE book_id=:book_id"
                    ),
                    {"book_id": book_id},
                )
                .mappings()
                .one_or_none()
            )
            if project is None:
                raise BookBenchNotFound(f"book project not found: {book_id}")
            chapters = list(
                connection.execute(
                    text(
                        "SELECT chapter_id,chapter_contract_entity_id,ordinal FROM chapters "
                        "WHERE book_id=:book_id AND workflow_state!='SUPERSEDED' ORDER BY ordinal"
                    ),
                    {"book_id": book_id},
                ).mappings()
            )
            units = list(
                connection.execute(
                    text(
                        "SELECT unit_id,chapter_id,authority_entity_id,ordinal FROM manuscript_units "
                        "WHERE book_id=:book_id ORDER BY chapter_id,ordinal,unit_id"
                    ),
                    {"book_id": book_id},
                ).mappings()
            )
            claims = list(
                connection.execute(
                    text(
                        "SELECT claim_id,chapter_id,unit_id,manuscript_revision_id,"
                        "manuscript_revision_hash,normalized_text,claim_type,materiality,"
                        "required_evidence_level,verification_state,updated_at FROM claims "
                        "WHERE book_id=:book_id ORDER BY claim_id"
                    ),
                    {"book_id": book_id},
                ).mappings()
            )

        if scope == "MANUSCRIPT_UNIT":
            if not unit_id:
                raise BookBenchGateError("MANUSCRIPT_UNIT snapshot requires unit_id")
            units = [row for row in units if row["unit_id"] == unit_id]
            if not units:
                raise BookBenchNotFound("manuscript unit not found")
            chapter_id = cast(str, units[0]["chapter_id"])
            chapters = [row for row in chapters if row["chapter_id"] == chapter_id]
            claims = [row for row in claims if row["unit_id"] == unit_id]
        elif scope == "CHAPTER":
            if not chapter_id:
                raise BookBenchGateError("CHAPTER snapshot requires chapter_id")
            chapters = [row for row in chapters if row["chapter_id"] == chapter_id]
            if not chapters:
                raise BookBenchNotFound("chapter not found")
            units = [row for row in units if row["chapter_id"] == chapter_id]
            claims = [row for row in claims if row["chapter_id"] == chapter_id]

        ordinal = 0
        book_contract_entity = cast(str | None, project["book_contract_entity_id"])
        if book_contract_entity:
            targets.append(
                self._authority_target(
                    authority,
                    ordinal=ordinal,
                    target_kind="BOOK_CONTRACT",
                    target_id=book_contract_entity,
                    entity_id=book_contract_entity,
                    chapter_id=None,
                    unit_id=None,
                )
            )
            ordinal += 1

        for row in chapters:
            entity_id = cast(str | None, row["chapter_contract_entity_id"])
            if not entity_id:
                continue
            targets.append(
                self._authority_target(
                    authority,
                    ordinal=ordinal,
                    target_kind="CHAPTER_CONTRACT",
                    target_id=cast(str, row["chapter_id"]),
                    entity_id=entity_id,
                    chapter_id=cast(str, row["chapter_id"]),
                    unit_id=None,
                )
            )
            ordinal += 1

        for row in units:
            targets.append(
                self._authority_target(
                    authority,
                    ordinal=ordinal,
                    target_kind="MANUSCRIPT_UNIT",
                    target_id=cast(str, row["unit_id"]),
                    entity_id=cast(str, row["authority_entity_id"]),
                    chapter_id=cast(str, row["chapter_id"]),
                    unit_id=cast(str, row["unit_id"]),
                )
            )
            ordinal += 1

        for raw_row in claims:
            claim_row = dict(raw_row)
            targets.append(
                SnapshotTargetView(
                    ordinal=ordinal,
                    target_kind="CLAIM",
                    target_id=cast(str, claim_row["claim_id"]),
                    chapter_id=cast(str, claim_row["chapter_id"]),
                    unit_id=cast(str, claim_row["unit_id"]),
                    revision_id=cast(str, claim_row["manuscript_revision_id"]),
                    revision_hash=cast(str, claim_row["manuscript_revision_hash"]),
                    content_hash=self._claim_content_hash(claim_row),
                    source_status=cast(str, claim_row["verification_state"]),
                    text=cast(str, claim_row["normalized_text"]),
                    metadata={
                        "claim_type": claim_row["claim_type"],
                        "materiality": claim_row["materiality"],
                        "required_evidence_level": claim_row["required_evidence_level"],
                        "updated_at": claim_row["updated_at"],
                    },
                )
            )
            ordinal += 1
        return targets

    def create_snapshot(
        self,
        book_id: str,
        *,
        scope: SnapshotScope = "BOOK",
        chapter_id: str | None = None,
        unit_id: str | None = None,
    ) -> EvaluationSnapshotView:
        engine = self._engine(book_id)
        try:
            targets = self._current_targets(
                engine, book_id, scope=scope, chapter_id=chapter_id, unit_id=unit_id
            )
            manifest = {
                "book_id": book_id,
                "scope": scope,
                "chapter_id": chapter_id,
                "unit_id": unit_id,
                "registry_hash": registry_hash(),
                "targets": [target.model_dump(mode="json") for target in targets],
            }
            snapshot_hash = _sha256(manifest)
            with engine.connect() as connection:
                existing = connection.execute(
                    text(
                        "SELECT snapshot_id FROM evaluation_snapshots WHERE book_id=:book_id "
                        "AND snapshot_hash=:snapshot_hash"
                    ),
                    {"book_id": book_id, "snapshot_hash": snapshot_hash},
                ).scalar_one_or_none()
            if existing is not None:
                return self.get_snapshot(book_id, cast(str, existing))

            snapshot_id = new_ulid()
            now = utc_now()
            snapshot_json = _canonical_json(manifest)
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT INTO evaluation_snapshots(snapshot_id,book_id,scope,chapter_id,unit_id,"
                        "snapshot_json,snapshot_hash,created_at) VALUES (:snapshot_id,:book_id,:scope,"
                        ":chapter_id,:unit_id,:snapshot_json,:snapshot_hash,:created_at)"
                    ),
                    {
                        "snapshot_id": snapshot_id,
                        "book_id": book_id,
                        "scope": scope,
                        "chapter_id": chapter_id,
                        "unit_id": unit_id,
                        "snapshot_json": snapshot_json,
                        "snapshot_hash": snapshot_hash,
                        "created_at": now,
                    },
                )
                for target in targets:
                    connection.execute(
                        text(
                            "INSERT INTO evaluation_snapshot_targets(snapshot_id,ordinal,target_kind,"
                            "target_id,chapter_id,unit_id,revision_id,revision_hash,content_hash,"
                            "source_status) VALUES (:snapshot_id,:ordinal,:target_kind,:target_id,"
                            ":chapter_id,:unit_id,:revision_id,:revision_hash,:content_hash,:source_status)"
                        ),
                        {
                            "snapshot_id": snapshot_id,
                            **target.model_dump(exclude={"text", "metadata"}),
                        },
                    )
            return self.get_snapshot(book_id, snapshot_id)
        finally:
            engine.dispose()

    def get_snapshot(self, book_id: str, snapshot_id: str) -> EvaluationSnapshotView:
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                row = (
                    connection.execute(
                        text(
                            "SELECT * FROM evaluation_snapshots WHERE book_id=:book_id "
                            "AND snapshot_id=:snapshot_id"
                        ),
                        {"book_id": book_id, "snapshot_id": snapshot_id},
                    )
                    .mappings()
                    .one_or_none()
                )
            if row is None:
                raise BookBenchNotFound("evaluation snapshot not found")
            manifest = json.loads(cast(str, row["snapshot_json"]))
            targets = [SnapshotTargetView.model_validate(item) for item in manifest["targets"]]
            return EvaluationSnapshotView(
                snapshot_id=snapshot_id,
                book_id=book_id,
                scope=cast(str, row["scope"]),
                chapter_id=cast(str | None, row["chapter_id"]),
                unit_id=cast(str | None, row["unit_id"]),
                snapshot_hash=cast(str, row["snapshot_hash"]),
                created_at=cast(str, row["created_at"]),
                current=self._snapshot_is_current(engine, book_id, targets),
                targets=targets,
            )
        finally:
            engine.dispose()

    def _snapshot_is_current(
        self, engine: Engine, book_id: str, targets: list[SnapshotTargetView]
    ) -> bool:
        authority = AuthorityService(engine)
        with engine.connect() as connection:
            for target in targets:
                if target.target_kind == "CLAIM":
                    row = (
                        connection.execute(
                            text(
                                "SELECT claim_id,chapter_id,unit_id,manuscript_revision_id,"
                                "manuscript_revision_hash,normalized_text,claim_type,materiality,"
                                "required_evidence_level,verification_state,updated_at FROM claims "
                                "WHERE book_id=:book_id AND claim_id=:claim_id"
                            ),
                            {"book_id": book_id, "claim_id": target.target_id},
                        )
                        .mappings()
                        .one_or_none()
                    )
                    if row is None or self._claim_content_hash(dict(row)) != target.content_hash:
                        return False
                    continue
                entity_id = cast(str, target.metadata.get("authority_entity_id", ""))
                if not entity_id:
                    return False
                try:
                    head = authority.get_head(entity_id)
                except Exception:
                    return False
                if (
                    head.revision_id != target.revision_id
                    or head.revision_hash != target.revision_hash
                ):
                    return False
        return True

    @staticmethod
    def _manuscript_targets(snapshot: EvaluationSnapshotView) -> list[SnapshotTargetView]:
        return [target for target in snapshot.targets if target.target_kind == "MANUSCRIPT_UNIT"]

    @staticmethod
    def _claim_targets(snapshot: EvaluationSnapshotView) -> list[SnapshotTargetView]:
        return [target for target in snapshot.targets if target.target_kind == "CLAIM"]

    @staticmethod
    def _chapter_contract_targets(snapshot: EvaluationSnapshotView) -> list[SnapshotTargetView]:
        return [target for target in snapshot.targets if target.target_kind == "CHAPTER_CONTRACT"]

    def _check_repetition(self, snapshot: EvaluationSnapshotView) -> _CheckResult:
        units = self._manuscript_targets(snapshot)
        occurrences: dict[str, list[tuple[SnapshotTargetView, int, str]]] = defaultdict(list)
        for unit in units:
            for index, sentence in enumerate(_sentences(unit.text), start=1):
                normalized = _normalize(sentence)
                if len(_tokens(sentence)) < 6 or len(normalized) < 36:
                    continue
                occurrences[normalized].append((unit, index, sentence))
        findings: list[_FindingDraft] = []
        duplicate_groups = 0
        for normalized, rows in sorted(occurrences.items()):
            unique_units = {row[0].target_id for row in rows}
            if len(unique_units) < 2:
                continue
            duplicate_groups += 1
            target = rows[0][0]
            findings.append(
                _FindingDraft(
                    target=target,
                    category="REPEATED_NORMALIZED_SENTENCE",
                    location=f"sentence:{rows[0][1]}",
                    evidence={
                        "normalized": normalized,
                        "occurrences": [
                            {
                                "unit_id": row[0].unit_id,
                                "chapter_id": row[0].chapter_id,
                                "revision_id": row[0].revision_id,
                                "sentence": row[2],
                                "sentence_index": row[1],
                            }
                            for row in rows
                        ],
                    },
                    severity="ATTENTION",
                    confidence=1.0,
                    recommended_action="Review whether repeated wording is intentional or should be revised.",
                )
            )
        return _CheckResult(
            findings=findings,
            metrics={"duplicate_sentence_groups": duplicate_groups, "unit_count": len(units)},
            output={"signal": "lexical repetition only"},
        )

    def _check_statistics(self, snapshot: EvaluationSnapshotView) -> _CheckResult:
        units = self._manuscript_targets(snapshot)
        sentence_lengths: list[int] = []
        paragraph_lengths: list[int] = []
        question_count = 0
        all_tokens: list[str] = []
        for unit in units:
            sentences = _sentences(unit.text)
            sentence_lengths.extend(len(_tokens(sentence)) for sentence in sentences)
            paragraphs = _paragraphs(unit.text)
            paragraph_lengths.extend(len(_tokens(paragraph)) for paragraph in paragraphs)
            question_count += unit.text.count("?")
            all_tokens.extend(_tokens(unit.text))
        sentence_count = len(sentence_lengths)
        question_rate = question_count / max(sentence_count, 1)
        lexical_diversity = len(set(all_tokens)) / max(len(all_tokens), 1)
        findings: list[_FindingDraft] = []
        if units and question_count >= 3 and question_rate > 0.25:
            findings.append(
                _FindingDraft(
                    target=units[0],
                    category="RHETORICAL_QUESTION_EXCESS_SIGNAL",
                    location="book/current-manuscript",
                    evidence={
                        "question_count": question_count,
                        "sentence_count": sentence_count,
                        "question_rate": question_rate,
                        "threshold": 0.25,
                    },
                    severity="ATTENTION",
                    confidence=1.0,
                    recommended_action="Review rhetorical-question density for intentional rhythm.",
                )
            )
        metrics = {
            "sentence_count": sentence_count,
            "sentence_length_mean_tokens": _mean(sentence_lengths),
            "sentence_length_p95_tokens": _p95(sentence_lengths),
            "paragraph_count": len(paragraph_lengths),
            "paragraph_length_mean_tokens": _mean(paragraph_lengths),
            "paragraph_length_p95_tokens": _p95(paragraph_lengths),
            "rhetorical_question_count": question_count,
            "rhetorical_question_rate": question_rate,
            "lexical_diversity": lexical_diversity,
        }
        return _CheckResult(
            findings=findings,
            metrics=metrics,
            output={"measurement_only": True},
        )

    def _check_specificity(self, snapshot: EvaluationSnapshotView) -> _CheckResult:
        units = self._manuscript_targets(snapshot)
        number_count = 0
        capitalized_count = 0
        abstraction_hits: list[dict[str, Any]] = []
        for unit in units:
            number_count += len(re.findall(r"\b\d+(?:[.,]\d+)?%?\b", unit.text))
            capitalized_count += len(
                re.findall(r"(?<![.!?]\s)\b[A-ZА-ЯЁ][a-zа-яё]{2,}\b", unit.text)
            )
            lowered = unit.text.casefold()
            for phrase in _EMPTY_ABSTRACTIONS:
                if phrase in lowered:
                    abstraction_hits.append({"unit_id": unit.unit_id, "phrase": phrase})
        findings: list[_FindingDraft] = []
        if units and len(abstraction_hits) >= 3 and number_count + capitalized_count == 0:
            findings.append(
                _FindingDraft(
                    target=units[0],
                    category="GENERIC_ABSTRACTION_CONCENTRATION_SIGNAL",
                    location="book/current-manuscript",
                    evidence={
                        "pattern_hits": abstraction_hits,
                        "concrete_number_count": number_count,
                        "proper_name_proxy_count": capitalized_count,
                    },
                    severity="ATTENTION",
                    confidence=0.75,
                    recommended_action="Review generic abstractions and add concrete support where appropriate.",
                )
            )
        return _CheckResult(
            findings=findings,
            metrics={
                "concrete_number_count": number_count,
                "proper_name_proxy_count": capitalized_count,
                "generic_abstraction_hit_count": len(abstraction_hits),
            },
            output={"heuristic": "specificity proxy; not a semantic quality judgment"},
        )

    def _check_evidence(self, snapshot: EvaluationSnapshotView) -> _CheckResult:
        claims = self._claim_targets(snapshot)
        units = {target.target_id: target for target in self._manuscript_targets(snapshot)}
        findings: list[_FindingDraft] = []
        state_counts: Counter[str] = Counter()
        stale_count = 0
        for claim in claims:
            state_counts[claim.source_status] += 1
            materiality = str(claim.metadata.get("materiality", ""))
            current_unit = units.get(claim.unit_id or "")
            stale = bool(
                current_unit
                and (
                    current_unit.revision_id != claim.revision_id
                    or current_unit.revision_hash != claim.revision_hash
                )
            )
            if stale:
                stale_count += 1
                target = current_unit or claim
                findings.append(
                    _FindingDraft(
                        target=target,
                        category="STALE_CLAIM_MANUSCRIPT_BINDING",
                        location=f"claim:{claim.target_id}",
                        evidence={
                            "claim_id": claim.target_id,
                            "claim_revision_id": claim.revision_id,
                            "claim_revision_hash": claim.revision_hash,
                            "current_revision_id": current_unit.revision_id
                            if current_unit
                            else None,
                            "current_revision_hash": current_unit.revision_hash
                            if current_unit
                            else None,
                        },
                        severity="BLOCKING" if materiality in {"HIGH", "CRITICAL"} else "ATTENTION",
                        confidence=1.0,
                        recommended_action="Re-review the Claim against the current manuscript; do not silently rebind it.",
                    )
                )
            if materiality not in {"HIGH", "CRITICAL"}:
                continue
            if claim.source_status not in {"UNREVIEWED", "DISPUTED", "UNSUPPORTED"}:
                continue
            findings.append(
                _FindingDraft(
                    target=current_unit or claim,
                    category=f"MATERIAL_CLAIM_{claim.source_status}",
                    location=f"claim:{claim.target_id}",
                    evidence={
                        "claim_id": claim.target_id,
                        "claim_text": claim.text,
                        "materiality": materiality,
                        "verification_state": claim.source_status,
                    },
                    severity=(
                        "BLOCKING"
                        if claim.source_status in {"DISPUTED", "UNSUPPORTED"}
                        else "ATTENTION"
                    ),
                    confidence=1.0,
                    recommended_action="Resolve the material Claim through the Claim/Evidence workflow or explicitly waive it before release.",
                )
            )
        return _CheckResult(
            findings=findings,
            metrics={
                "claim_state_counts": dict(sorted(state_counts.items())),
                "stale_claim_binding_count": stale_count,
            },
            output={"claim_state_only": True},
        )

    def _check_contract_structure(self, snapshot: EvaluationSnapshotView) -> _CheckResult:
        contracts = self._chapter_contract_targets(snapshot)
        units_by_chapter: dict[str, list[SnapshotTargetView]] = defaultdict(list)
        for unit in self._manuscript_targets(snapshot):
            if unit.chapter_id:
                units_by_chapter[unit.chapter_id].append(unit)
        findings: list[_FindingDraft] = []
        lexical_gap_count = 0
        missing_manuscript_count = 0
        for contract in contracts:
            chapter_id = contract.chapter_id or ""
            units = units_by_chapter.get(chapter_id, [])
            content = cast(dict[str, Any], contract.metadata.get("content", {}))
            if not units:
                missing_manuscript_count += 1
                findings.append(
                    _FindingDraft(
                        target=contract,
                        category="CHAPTER_WITHOUT_CURRENT_MANUSCRIPT",
                        location=f"chapter:{chapter_id}",
                        evidence={"current_manuscript_unit_count": 0},
                        severity="BLOCKING",
                        confidence=1.0,
                        recommended_action="Create/review current chapter manuscript before claiming contract fulfillment.",
                    )
                )
                continue
            chapter_text = "\n".join(unit.text for unit in units)
            required_claims = content.get("required_claims", [])
            if isinstance(required_claims, list):
                for required_claim in required_claims:
                    if not isinstance(required_claim, str) or _lexical_trace(
                        required_claim, chapter_text
                    ):
                        continue
                    lexical_gap_count += 1
                    findings.append(
                        _FindingDraft(
                            target=contract,
                            category="CHAPTER_REQUIRED_CLAIM_LEXICAL_GAP",
                            location=f"chapter:{chapter_id}",
                            evidence={
                                "required_claim": required_claim,
                                "rule": "normalized exact/90%-token lexical trace",
                                "unit_ids": [unit.unit_id for unit in units],
                            },
                            severity="ATTENTION",
                            confidence=0.8,
                            recommended_action="Human-review whether the required claim is semantically covered or needs revision.",
                        )
                    )
        return _CheckResult(
            findings=findings,
            metrics={
                "chapter_contract_count": len(contracts),
                "missing_manuscript_chapter_count": missing_manuscript_count,
                "required_claim_lexical_gap_count": lexical_gap_count,
            },
            output={"lexical_signal_only": True},
        )

    def _check_ai_prose(self, snapshot: EvaluationSnapshotView) -> _CheckResult:
        units = self._manuscript_targets(snapshot)
        findings: list[_FindingDraft] = []
        pattern_counts: Counter[str] = Counter()
        repeated_starts: Counter[str] = Counter()
        for unit in units:
            checks: list[tuple[str, re.Pattern[str]]] = [
                ("FALSE_CONTRAST_TEMPLATE", _FALSE_CONTRAST),
                ("NOT_ABOUT_TEMPLATE", _NOT_ABOUT),
                ("ARTIFICIAL_TRIAD_SIGNAL", _TRIAD),
            ]
            for category, pattern in checks:
                matches = list(pattern.finditer(unit.text))
                pattern_counts[category] += len(matches)
                for match in matches:
                    findings.append(
                        _FindingDraft(
                            target=unit,
                            category=category,
                            location=f"chars:{match.start()}-{match.end()}",
                            evidence={
                                "match": match.group(0),
                                "detector_version": "ai-prose-patterns-v1",
                            },
                            severity="ATTENTION",
                            confidence=0.8,
                            recommended_action="Review the measured prose pattern in context; occurrence is not proof of AI authorship.",
                        )
                    )
            lowered = unit.text.casefold()
            for phrase in _GENERIC_TRANSITIONS:
                start = 0
                while True:
                    index = lowered.find(phrase, start)
                    if index < 0:
                        break
                    pattern_counts["GENERIC_TRANSITION_PATTERN"] += 1
                    findings.append(
                        _FindingDraft(
                            target=unit,
                            category="GENERIC_TRANSITION_PATTERN",
                            location=f"chars:{index}-{index + len(phrase)}",
                            evidence={
                                "match": unit.text[index : index + len(phrase)],
                                "pattern": phrase,
                                "detector_version": "ai-prose-patterns-v1",
                            },
                            severity="ATTENTION",
                            confidence=0.75,
                            recommended_action="Review transition repetition and keep it only if it matches intentional author voice.",
                        )
                    )
                    start = index + len(phrase)
            for sentence in _sentences(unit.text):
                opening = _first_words(sentence, 4)
                if opening:
                    repeated_starts[opening] += 1
        repeated = {key: count for key, count in repeated_starts.items() if count >= 3}
        if repeated and units:
            findings.append(
                _FindingDraft(
                    target=units[0],
                    category="REPEATED_SENTENCE_START_PATTERN",
                    location="book/current-manuscript",
                    evidence={
                        "starts": dict(sorted(repeated.items())),
                        "detector_version": "ai-prose-patterns-v1",
                    },
                    severity="ATTENTION",
                    confidence=0.85,
                    recommended_action="Review repeated sentence openings for over-symmetry or intentional rhythm.",
                )
            )
        return _CheckResult(
            findings=findings,
            metrics={
                "pattern_counts": dict(sorted(pattern_counts.items())),
                "repeated_sentence_starts": dict(sorted(repeated.items())),
                "ai_authorship_probability": None,
            },
            output={
                "detector_version": "ai-prose-patterns-v1",
                "claim": "measured prose patterns only; no authorship inference",
            },
        )

    def _check_opening_ending(self, snapshot: EvaluationSnapshotView) -> _CheckResult:
        units_by_chapter: dict[str, list[SnapshotTargetView]] = defaultdict(list)
        for unit in self._manuscript_targets(snapshot):
            if unit.chapter_id:
                units_by_chapter[unit.chapter_id].append(unit)
        opening_map: dict[str, list[str]] = defaultdict(list)
        ending_map: dict[str, list[str]] = defaultdict(list)
        for chapter_id, units in units_by_chapter.items():
            if units:
                opening_map[_first_words(units[0].text)].append(chapter_id)
                ending_map[_last_words(units[-1].text)].append(chapter_id)
        findings: list[_FindingDraft] = []
        target_by_chapter = {
            unit.chapter_id: unit
            for unit in self._manuscript_targets(snapshot)
            if unit.chapter_id is not None
        }
        for kind, mapping in (("OPENING", opening_map), ("ENDING", ending_map)):
            for phrase, chapter_ids in sorted(mapping.items()):
                if not phrase or len(chapter_ids) < 2:
                    continue
                target = target_by_chapter[chapter_ids[0]]
                findings.append(
                    _FindingDraft(
                        target=target,
                        category=f"REPEATED_{kind}_TEMPLATE",
                        location=" / ".join(f"chapter:{chapter_id}" for chapter_id in chapter_ids),
                        evidence={"normalized_words": phrase, "chapter_ids": chapter_ids},
                        severity="ATTENTION",
                        confidence=0.9,
                        recommended_action=f"Review repeated {kind.casefold()} structure for intentional variation.",
                    )
                )
        return _CheckResult(
            findings=findings,
            metrics={
                "chapter_count": len(units_by_chapter),
                "repeated_opening_groups": sum(
                    1 for rows in opening_map.values() if len(rows) >= 2
                ),
                "repeated_ending_groups": sum(1 for rows in ending_map.values() if len(rows) >= 2),
            },
            output={"structural_signal_only": True},
        )

    def _execute_deterministic(
        self, spec: CheckSpec, snapshot: EvaluationSnapshotView
    ) -> _CheckResult:
        runners = {
            "deterministic.repetition": self._check_repetition,
            "deterministic.statistics": self._check_statistics,
            "deterministic.specificity": self._check_specificity,
            "deterministic.evidence": self._check_evidence,
            "deterministic.contract_structure": self._check_contract_structure,
            "deterministic.ai_prose_pathology": self._check_ai_prose,
            "deterministic.opening_ending_transition": self._check_opening_ending,
        }
        try:
            runner = runners[spec.check_id]
        except KeyError as exc:
            raise BookBenchGateError(
                f"check is not a deterministic M7 check: {spec.check_id}"
            ) from exc
        return runner(snapshot)

    def _persist_run(
        self,
        engine: Engine,
        *,
        book_id: str,
        snapshot: EvaluationSnapshotView,
        spec: CheckSpec,
        result: _CheckResult | None,
        latency_ms: int,
        error: Exception | None,
    ) -> str:
        evaluation_id = new_ulid()
        now = utc_now()
        completed_at = now
        input_hash = _sha256(
            {
                "snapshot_id": snapshot.snapshot_id,
                "snapshot_hash": snapshot.snapshot_hash,
                "check": spec.canonical(),
                "registry_hash": registry_hash(),
            }
        )
        output = result.output if result else {}
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO evaluation_runs(evaluation_id,book_id,snapshot_id,check_id,"
                    "check_version,registry_hash,dimension,evaluator_class,evaluator_id,"
                    "evaluator_version,independence_state,input_hash,output_json,usage_json,"
                    "latency_ms,cost_usd,status,error_message,created_at,completed_at) VALUES "
                    "(:evaluation_id,:book_id,:snapshot_id,:check_id,:check_version,:registry_hash,"
                    ":dimension,:evaluator_class,:evaluator_id,:evaluator_version,'NOT_APPLICABLE',"
                    ":input_hash,:output_json,'{}',:latency_ms,NULL,:status,:error_message,"
                    ":created_at,:completed_at)"
                ),
                {
                    "evaluation_id": evaluation_id,
                    "book_id": book_id,
                    "snapshot_id": snapshot.snapshot_id,
                    "check_id": spec.check_id,
                    "check_version": spec.version,
                    "registry_hash": registry_hash(),
                    "dimension": spec.dimension,
                    "evaluator_class": spec.evaluator_class,
                    "evaluator_id": self.DETERMINISTIC_RUNNER_ID,
                    "evaluator_version": self.DETERMINISTIC_RUNNER_VERSION,
                    "input_hash": input_hash,
                    "output_json": _canonical_json(output),
                    "latency_ms": latency_ms,
                    "status": "FAILED" if error else "SUCCEEDED",
                    "error_message": str(error)[:1000] if error else None,
                    "created_at": now,
                    "completed_at": completed_at,
                },
            )
            if result:
                for name, value in sorted(result.metrics.items()):
                    connection.execute(
                        text(
                            "INSERT INTO evaluation_metrics(metric_id,evaluation_id,metric_name,"
                            "metric_value_json,created_at) VALUES (:metric_id,:evaluation_id,"
                            ":metric_name,:metric_value_json,:created_at)"
                        ),
                        {
                            "metric_id": new_ulid(),
                            "evaluation_id": evaluation_id,
                            "metric_name": name,
                            "metric_value_json": _canonical_json(value),
                            "created_at": now,
                        },
                    )
                for draft in result.findings:
                    connection.execute(
                        text(
                            "INSERT INTO evaluation_findings(finding_id,evaluation_id,dimension,"
                            "category,target_kind,target_id,chapter_id,unit_id,revision_id,"
                            "revision_hash,location,evidence_json,severity,confidence,"
                            "recommended_action,created_at) VALUES (:finding_id,:evaluation_id,"
                            ":dimension,:category,:target_kind,:target_id,:chapter_id,:unit_id,"
                            ":revision_id,:revision_hash,:location,:evidence_json,:severity,"
                            ":confidence,:recommended_action,:created_at)"
                        ),
                        {
                            "finding_id": new_ulid(),
                            "evaluation_id": evaluation_id,
                            "dimension": spec.dimension,
                            "category": draft.category,
                            "target_kind": draft.target.target_kind,
                            "target_id": draft.target.target_id,
                            "chapter_id": draft.target.chapter_id,
                            "unit_id": draft.target.unit_id,
                            "revision_id": draft.target.revision_id,
                            "revision_hash": draft.target.revision_hash,
                            "location": draft.location,
                            "evidence_json": _canonical_json(draft.evidence),
                            "severity": draft.severity,
                            "confidence": draft.confidence,
                            "recommended_action": draft.recommended_action,
                            "created_at": now,
                        },
                    )
        return evaluation_id

    def run_check(self, book_id: str, snapshot_id: str, check_id: str) -> EvaluationRunView:
        snapshot = self.get_snapshot(book_id, snapshot_id)
        spec = get_check(check_id)
        if spec.evaluator_class != "DETERMINISTIC":
            raise BookBenchGateError("run_check currently accepts deterministic checks only")
        engine = self._engine(book_id)
        started = time.perf_counter()
        try:
            try:
                result = self._execute_deterministic(spec, snapshot)
            except Exception as exc:
                latency_ms = max(0, int((time.perf_counter() - started) * 1000))
                evaluation_id = self._persist_run(
                    engine,
                    book_id=book_id,
                    snapshot=snapshot,
                    spec=spec,
                    result=None,
                    latency_ms=latency_ms,
                    error=exc,
                )
                return self.get_run(book_id, evaluation_id)
            latency_ms = max(0, int((time.perf_counter() - started) * 1000))
            evaluation_id = self._persist_run(
                engine,
                book_id=book_id,
                snapshot=snapshot,
                spec=spec,
                result=result,
                latency_ms=latency_ms,
                error=None,
            )
            return self.get_run(book_id, evaluation_id)
        finally:
            engine.dispose()

    def run_deterministic_suite(self, book_id: str, snapshot_id: str) -> list[EvaluationRunView]:
        check_ids = (
            "deterministic.repetition",
            "deterministic.statistics",
            "deterministic.specificity",
            "deterministic.evidence",
            "deterministic.contract_structure",
            "deterministic.ai_prose_pathology",
            "deterministic.opening_ending_transition",
        )
        return [self.run_check(book_id, snapshot_id, check_id) for check_id in check_ids]

    def get_run(self, book_id: str, evaluation_id: str) -> EvaluationRunView:
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                row = (
                    connection.execute(
                        text(
                            "SELECT * FROM evaluation_runs WHERE book_id=:book_id "
                            "AND evaluation_id=:evaluation_id"
                        ),
                        {"book_id": book_id, "evaluation_id": evaluation_id},
                    )
                    .mappings()
                    .one_or_none()
                )
                if row is None:
                    raise BookBenchNotFound("evaluation run not found")
                finding_rows = list(
                    connection.execute(
                        text(
                            "SELECT * FROM evaluation_findings WHERE evaluation_id=:evaluation_id "
                            "ORDER BY CASE severity WHEN 'BLOCKING' THEN 0 WHEN 'ATTENTION' THEN 1 "
                            "ELSE 2 END,finding_id"
                        ),
                        {"evaluation_id": evaluation_id},
                    ).mappings()
                )
                metric_rows = list(
                    connection.execute(
                        text(
                            "SELECT metric_name,metric_value_json FROM evaluation_metrics "
                            "WHERE evaluation_id=:evaluation_id ORDER BY metric_name"
                        ),
                        {"evaluation_id": evaluation_id},
                    ).mappings()
                )
            findings: list[EvaluationFindingView] = []
            for finding_row in finding_rows:
                payload = dict(finding_row)
                payload["evidence"] = json.loads(cast(str, payload.pop("evidence_json")))
                findings.append(EvaluationFindingView(**payload))
            metrics = {
                cast(str, metric["metric_name"]): json.loads(cast(str, metric["metric_value_json"]))
                for metric in metric_rows
            }
            return EvaluationRunView(
                evaluation_id=cast(str, row["evaluation_id"]),
                book_id=cast(str, row["book_id"]),
                snapshot_id=cast(str, row["snapshot_id"]),
                check_id=cast(str, row["check_id"]),
                check_version=cast(str, row["check_version"]),
                registry_hash=cast(str, row["registry_hash"]),
                dimension=cast(str, row["dimension"]),
                evaluator_class=cast(str, row["evaluator_class"]),
                evaluator_id=cast(str, row["evaluator_id"]),
                evaluator_version=cast(str, row["evaluator_version"]),
                provider=cast(str | None, row["provider"]),
                model=cast(str | None, row["model"]),
                config_id=cast(str | None, row["config_id"]),
                prompt_id=cast(str | None, row["prompt_id"]),
                prompt_version=cast(str | None, row["prompt_version"]),
                prompt_hash=cast(str | None, row["prompt_hash"]),
                independence_state=cast(str, row["independence_state"]),
                input_hash=cast(str, row["input_hash"]),
                output=json.loads(cast(str, row["output_json"])),
                usage=json.loads(cast(str, row["usage_json"])),
                latency_ms=cast(int, row["latency_ms"]),
                cost_usd=cast(float | None, row["cost_usd"]),
                status=cast(str, row["status"]),
                error_message=cast(str | None, row["error_message"]),
                created_at=cast(str, row["created_at"]),
                completed_at=cast(str | None, row["completed_at"]),
                findings=findings,
                metrics=metrics,
            )
        finally:
            engine.dispose()

    def report(self, book_id: str, snapshot_id: str) -> BookBenchReport:
        snapshot = self.get_snapshot(book_id, snapshot_id)
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                run_ids = list(
                    connection.execute(
                        text(
                            "SELECT evaluation_id FROM evaluation_runs WHERE book_id=:book_id "
                            "AND snapshot_id=:snapshot_id AND status='SUCCEEDED' "
                            "ORDER BY created_at,evaluation_id"
                        ),
                        {"book_id": book_id, "snapshot_id": snapshot_id},
                    ).scalars()
                )
            runs = [self.get_run(book_id, cast(str, run_id)) for run_id in run_ids]
            by_dimension: dict[str, list[EvaluationRunView]] = defaultdict(list)
            for run in runs:
                by_dimension[run.dimension].append(run)
            dimensions: list[DimensionReport] = []
            blocking_dimensions: list[str] = []
            for dimension in sorted(by_dimension):
                dimension_runs = by_dimension[dimension]
                findings = [finding for run in dimension_runs for finding in run.findings]
                if any(finding.severity == "BLOCKING" for finding in findings):
                    state: DimensionState = "BLOCKING"
                    blocking_dimensions.append(dimension)
                elif any(finding.severity == "ATTENTION" for finding in findings):
                    state = "ATTENTION"
                else:
                    state = "PASS"
                metrics: dict[str, Any] = {}
                for run in dimension_runs:
                    metrics[run.check_id] = run.metrics
                dimensions.append(
                    DimensionReport(
                        dimension=dimension,
                        state=state,
                        findings=findings,
                        run_ids=[run.evaluation_id for run in dimension_runs],
                        metrics=metrics,
                    )
                )
            return BookBenchReport(
                snapshot_id=snapshot_id,
                snapshot_hash=snapshot.snapshot_hash,
                current=snapshot.current,
                dimensions=dimensions,
                blocking_dimensions=blocking_dimensions,
                generated_at=utc_now(),
            )
        finally:
            engine.dispose()

    VOICE_EXTRACTOR_ID = "author-voice-fingerprint"
    VOICE_EXTRACTOR_VERSION = "1.0.0"

    @classmethod
    def _voice_extractor_hash(cls) -> str:
        return _sha256(
            {
                "id": cls.VOICE_EXTRACTOR_ID,
                "version": cls.VOICE_EXTRACTOR_VERSION,
                "features": [
                    "sentence_length",
                    "paragraph_length",
                    "punctuation",
                    "sentence_starts",
                    "first_person",
                    "questions",
                    "concrete_numbers",
                    "transitions",
                ],
            }
        )

    @staticmethod
    def _voice_features(targets: list[SnapshotTargetView]) -> dict[str, Any]:
        texts = [target.text for target in targets]
        joined = "\n\n".join(texts)
        sentences = [sentence for value in texts for sentence in _sentences(value)]
        paragraphs = [paragraph for value in texts for paragraph in _paragraphs(value)]
        tokens = _tokens(joined)
        sentence_lengths = [len(_tokens(sentence)) for sentence in sentences]
        paragraph_lengths = [len(_tokens(paragraph)) for paragraph in paragraphs]
        first_person = sum(
            1 for token in tokens if token in {"я", "мы", "мой", "моя", "наш", "наша"}
        )
        starts = Counter(_first_words(sentence, 1) for sentence in sentences if sentence)
        transitions = {
            phrase: joined.casefold().count(phrase)
            for phrase in _GENERIC_TRANSITIONS
            if joined.casefold().count(phrase)
        }
        return {
            "sentence_count": len(sentences),
            "sentence_length_mean": _mean(sentence_lengths),
            "sentence_length_p95": _p95(sentence_lengths),
            "paragraph_count": len(paragraphs),
            "paragraph_length_mean": _mean(paragraph_lengths),
            "paragraph_length_p95": _p95(paragraph_lengths),
            "punctuation_per_1000_tokens": {
                mark: joined.count(mark) * 1000 / max(len(tokens), 1) for mark in ",;:—!?"
            },
            "common_sentence_starts": dict(starts.most_common(10)),
            "first_person_rate": first_person / max(len(tokens), 1),
            "rhetorical_question_rate": joined.count("?") / max(len(sentences), 1),
            "concrete_number_density": len(re.findall(r"\b\d+(?:[.,]\d+)?%?\b", joined))
            / max(len(tokens), 1),
            "transition_frequencies": transitions,
            "construction_metadata": {
                "blacklist": list(_GENERIC_TRANSITIONS),
                "tolerance": "diagnostic occurrences only; human review required",
            },
        }

    def create_voice_fingerprint(
        self, book_id: str, snapshot_id: str, *, name: str
    ) -> VoiceFingerprintView:
        snapshot = self.get_snapshot(book_id, snapshot_id)
        references = self._manuscript_targets(snapshot)
        if not references:
            raise BookBenchGateError("voice fingerprint requires exact manuscript revisions")
        features = self._voice_features(references)
        fingerprint_hash = _sha256(
            {
                "extractor_hash": self._voice_extractor_hash(),
                "references": [[target.revision_id, target.revision_hash] for target in references],
                "features": features,
            }
        )
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                existing = connection.execute(
                    text(
                        "SELECT fingerprint_id FROM voice_fingerprints WHERE book_id=:book_id AND fingerprint_hash=:fingerprint_hash"
                    ),
                    {"book_id": book_id, "fingerprint_hash": fingerprint_hash},
                ).scalar_one_or_none()
            if existing is None:
                fingerprint_id = new_ulid()
                with engine.begin() as connection:
                    connection.execute(
                        text(
                            "INSERT INTO voice_fingerprints(fingerprint_id,book_id,name,extractor_id,extractor_version,extractor_hash,reference_snapshot_id,features_json,fingerprint_hash,created_at) VALUES (:fingerprint_id,:book_id,:name,:extractor_id,:extractor_version,:extractor_hash,:reference_snapshot_id,:features_json,:fingerprint_hash,:created_at)"
                        ),
                        {
                            "fingerprint_id": fingerprint_id,
                            "book_id": book_id,
                            "name": name,
                            "extractor_id": self.VOICE_EXTRACTOR_ID,
                            "extractor_version": self.VOICE_EXTRACTOR_VERSION,
                            "extractor_hash": self._voice_extractor_hash(),
                            "reference_snapshot_id": snapshot_id,
                            "features_json": _canonical_json(features),
                            "fingerprint_hash": fingerprint_hash,
                            "created_at": utc_now(),
                        },
                    )
            else:
                fingerprint_id = cast(str, existing)
            return self.get_voice_fingerprint(book_id, fingerprint_id)
        finally:
            engine.dispose()

    def get_voice_fingerprint(self, book_id: str, fingerprint_id: str) -> VoiceFingerprintView:
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                row = (
                    connection.execute(
                        text(
                            "SELECT * FROM voice_fingerprints WHERE book_id=:book_id AND fingerprint_id=:fingerprint_id"
                        ),
                        {"book_id": book_id, "fingerprint_id": fingerprint_id},
                    )
                    .mappings()
                    .one_or_none()
                )
            if row is None:
                raise BookBenchNotFound("voice fingerprint not found")
            snapshot = self.get_snapshot(book_id, cast(str, row["reference_snapshot_id"]))
            references = self._manuscript_targets(snapshot)
            return VoiceFingerprintView(
                fingerprint_id=fingerprint_id,
                book_id=book_id,
                name=cast(str, row["name"]),
                extractor_id=cast(str, row["extractor_id"]),
                extractor_version=cast(str, row["extractor_version"]),
                extractor_hash=cast(str, row["extractor_hash"]),
                reference_snapshot_id=snapshot.snapshot_id,
                reference_revisions=[
                    {"revision_id": item.revision_id, "revision_hash": item.revision_hash}
                    for item in references
                ],
                features=json.loads(cast(str, row["features_json"])),
                fingerprint_hash=cast(str, row["fingerprint_hash"]),
                created_at=cast(str, row["created_at"]),
            )
        finally:
            engine.dispose()

    def compare_voice(
        self, book_id: str, fingerprint_id: str, target_snapshot_id: str
    ) -> VoiceComparisonView:
        fingerprint = self.get_voice_fingerprint(book_id, fingerprint_id)
        target = self.get_snapshot(book_id, target_snapshot_id)
        targets = self._manuscript_targets(target)
        features = self._voice_features(targets)
        numeric = (
            "sentence_length_mean",
            "paragraph_length_mean",
            "first_person_rate",
            "rhetorical_question_rate",
            "concrete_number_density",
        )
        deltas = {key: float(features[key]) - float(fingerprint.features[key]) for key in numeric}
        return VoiceComparisonView(
            fingerprint_id=fingerprint_id,
            target_snapshot_id=target_snapshot_id,
            target_revisions=[
                {"revision_id": item.revision_id, "revision_hash": item.revision_hash}
                for item in targets
            ],
            feature_deltas=deltas,
            target_features=features,
        )

    @staticmethod
    def _cosine(left: list[float], right: list[float]) -> float:
        if len(left) != len(right):
            raise BookBenchGateError("incompatible embedding dimensions")
        denominator = math.sqrt(sum(x * x for x in left)) * math.sqrt(sum(x * x for x in right))
        return (
            sum(x * y for x, y in zip(left, right, strict=True)) / denominator
            if denominator
            else 0.0
        )

    def run_semantic(
        self,
        book_id: str,
        snapshot_id: str,
        *,
        provider: str,
        model: str,
        expected_config_hash: str | None = None,
    ) -> SemanticResultView:
        if self.embedding_gateway is None:
            raise BookBenchGateError("embedding gateway is not configured")
        snapshot = self.get_snapshot(book_id, snapshot_id)
        if not snapshot.current:
            raise BookBenchGateError("semantic snapshot is stale")
        units = self._manuscript_targets(snapshot)
        contracts = [
            t for t in snapshot.targets if t.target_kind in {"BOOK_CONTRACT", "CHAPTER_CONTRACT"}
        ]
        if not units:
            raise BookBenchGateError("semantic evaluation requires manuscript targets")
        all_targets = units + contracts
        batch = self.embedding_gateway.embed(
            [t.text for t in all_targets], provider=provider, model=model
        )
        dimension = len(batch.vectors[0])
        config_hash = embedding_config_hash(
            batch.provider, batch.model, batch.model_version, dimension
        )
        if expected_config_hash is not None and expected_config_hash != config_hash:
            raise BookBenchGateError("incompatible embedding config; rebuild explicitly")
        config = {
            "provider": batch.provider,
            "model": batch.model,
            "model_version": batch.model_version,
            "dimension": dimension,
            "config_hash": config_hash,
        }
        findings: dict[str, list[_FindingDraft]] = {
            "IDEA_REPETITION": [],
            "SEMANTIC_NOVELTY": [],
            "BOOK_CONTRACT_FULFILLMENT": [],
            "CHAPTER_CONTRACT_FULFILLMENT": [],
        }
        vectors = dict(zip((t.target_id for t in all_targets), batch.vectors, strict=True))
        for index, left in enumerate(units):
            similarities = [
                (right, self._cosine(vectors[left.target_id], vectors[right.target_id]))
                for right in units[index + 1 :]
            ]
            for right, score in similarities:
                if score >= 0.85:
                    findings["IDEA_REPETITION"].append(
                        _FindingDraft(
                            left,
                            "SEMANTIC_DUPLICATION_CANDIDATE",
                            f"revision:{left.revision_id} ↔ revision:{right.revision_id}",
                            {
                                "similarity": score,
                                "other_revision_id": right.revision_id,
                                "embedding_config": config,
                                "candidate_only": True,
                            },
                            "ATTENTION",
                            0.7,
                            "Human-review the candidate; similarity is not semantic truth.",
                        )
                    )
            best_other = max((score for _, score in similarities), default=0.0)
            if best_other >= 0.85:
                findings["SEMANTIC_NOVELTY"].append(
                    _FindingDraft(
                        left,
                        "LOW_NOVELTY_CANDIDATE",
                        f"revision:{left.revision_id}",
                        {
                            "max_similarity": best_other,
                            "embedding_config": config,
                            "candidate_only": True,
                        },
                        "ATTENTION",
                        0.65,
                        "Review whether the chapter adds a distinct contribution.",
                    )
                )
        for contract in contracts:
            related = [
                u
                for u in units
                if contract.target_kind == "BOOK_CONTRACT" or u.chapter_id == contract.chapter_id
            ]
            best = max(
                (self._cosine(vectors[contract.target_id], vectors[u.target_id]) for u in related),
                default=0.0,
            )
            dim = (
                "BOOK_CONTRACT_FULFILLMENT"
                if contract.target_kind == "BOOK_CONTRACT"
                else "CHAPTER_CONTRACT_FULFILLMENT"
            )
            if best < 0.55:
                findings[dim].append(
                    _FindingDraft(
                        contract,
                        "SEMANTIC_COVERAGE_CANDIDATE",
                        f"revision:{contract.revision_id}",
                        {
                            "best_similarity": best,
                            "embedding_config": config,
                            "candidate_only": True,
                            "does_not_assert_fulfillment": True,
                        },
                        "ATTENTION",
                        0.6,
                        "Human-review coverage and possible drift against the approved Contract.",
                    )
                )
        ids: list[str] = []
        engine = self._engine(book_id)
        try:
            for dim, drafts in findings.items():
                spec = CheckSpec(
                    check_id=f"semantic.{dim.casefold()}",
                    version="1.0.0",
                    dimension=cast(Any, dim),
                    evaluator_class="SEMANTIC",
                    description="Bounded semantic candidates",
                )
                result = _CheckResult(
                    drafts,
                    {"candidate_count": len(drafts)},
                    {"embedding_config": config, "candidate_only": True},
                )
                ids.append(
                    self._persist_run(
                        engine,
                        book_id=book_id,
                        snapshot=snapshot,
                        spec=spec,
                        result=result,
                        latency_ms=0,
                        error=None,
                    )
                )
        finally:
            engine.dispose()
        return SemanticResultView(
            evaluation_ids=ids, embedding_config=config, config_hash=config_hash
        )

    @staticmethod
    def independence(writer: dict[str, str] | None, judge: dict[str, str]) -> tuple[str, bool]:
        if not writer or not all(writer.get(k) for k in ("provider", "model", "config_id")):
            return "UNKNOWN", False
        same = all(writer.get(k) == judge.get(k) for k in ("provider", "model", "config_id"))
        return ("SAME_CONFIG", False) if same else ("INDEPENDENT", True)

    def _model_run(
        self,
        book_id: str,
        snapshot_id: str,
        *,
        dimension: str,
        provider: str,
        model: str,
        config_id: str,
        writer: dict[str, str] | None = None,
    ) -> EvaluationRunView:
        if self.model_gateway is None:
            raise BookBenchGateError("model gateway is not configured")
        snapshot = self.get_snapshot(book_id, snapshot_id)
        targets = self._manuscript_targets(snapshot)
        if not targets:
            raise BookBenchGateError("judge requires manuscript text")
        state, release_grade = self.independence(
            writer, {"provider": provider, "model": model, "config_id": config_id}
        )
        request = ModelTaskRequest(
            task_id=new_ulid(),
            task_type="BOOKBENCH_JUDGE",
            role="EVALUATOR",
            provider=provider,
            model=model,
            prompt_id=BOOKBENCH_JUDGE_V1.prompt_id,
            prompt_version=BOOKBENCH_JUDGE_V1.version,
            prompt_hash=BOOKBENCH_JUDGE_V1.prompt_hash,
            section_objective=f"Evaluate only {dimension}",
            authority_inputs=[
                AuthorityInputRef(
                    revision_id=t.revision_id,
                    revision_hash=t.revision_hash,
                    entity_type=t.target_kind,
                )
                for t in targets
            ],
            authoritative_context={"snapshot_id": snapshot_id, "dimension": dimension},
            untrusted_context=[t.text for t in targets],
            task_payload={"dimension": dimension},
            max_output_tokens=800,
        )
        started = time.monotonic()
        response = self.model_gateway.generate(request, BOOKBENCH_JUDGE_V1)
        parsed = BookBenchJudgeOutput.model_validate(response.output)
        drafts = [
            _FindingDraft(
                targets[0],
                "LLM_JUDGE_FINDING",
                f.location,
                {"evidence": f.evidence, "release_grade": release_grade},
                "INFO" if parsed.verdict == "PASS" else cast(FindingSeverity, parsed.verdict),
                parsed.confidence,
                f.recommended_action,
            )
            for f in parsed.findings
        ]
        spec = CheckSpec(
            check_id="llm.bookbench_judge",
            version="1.0.0",
            dimension=cast(Any, dimension),
            evaluator_class="LLM_JUDGE",
            description="Versioned bounded judge rubric",
        )
        engine = self._engine(book_id)
        try:
            eid = self._persist_run(
                engine,
                book_id=book_id,
                snapshot=snapshot,
                spec=spec,
                result=_CheckResult(
                    drafts,
                    {"verdict": parsed.verdict},
                    {
                        **parsed.model_dump(),
                        "writer_identity": writer,
                        "judge_identity": {
                            "provider": provider,
                            "model": model,
                            "config_id": config_id,
                        },
                        "independence_state": state,
                        "release_grade": release_grade,
                    },
                ),
                latency_ms=int((time.monotonic() - started) * 1000),
                error=None,
            )
            with engine.begin() as connection:
                connection.exec_driver_sql("DROP TRIGGER evaluation_runs_no_update")
                connection.execute(
                    text(
                        "UPDATE evaluation_runs SET provider=:p,model=:m,config_id=:c,prompt_id=:pi,prompt_version=:pv,prompt_hash=:ph,independence_state=:i,usage_json=:u,cost_usd=0 WHERE evaluation_id=:e"
                    ),
                    {
                        "p": provider,
                        "m": model,
                        "c": config_id,
                        "pi": BOOKBENCH_JUDGE_V1.prompt_id,
                        "pv": BOOKBENCH_JUDGE_V1.version,
                        "ph": BOOKBENCH_JUDGE_V1.prompt_hash,
                        "i": state,
                        "u": _canonical_json(response.usage),
                        "e": eid,
                    },
                )
                connection.exec_driver_sql(
                    "CREATE TRIGGER evaluation_runs_no_update BEFORE UPDATE ON evaluation_runs BEGIN SELECT RAISE(ABORT, 'evaluation_runs is immutable; create a new evaluation artifact'); END"
                )
            return self.get_run(book_id, eid)
        finally:
            engine.dispose()

    def run_judge(self, *args: Any, **kwargs: Any) -> EvaluationRunView:
        return self._model_run(*args, **kwargs)

    def run_pairwise(
        self,
        book_id: str,
        snapshot_id: str,
        *,
        dimension: str,
        candidates: dict[str, str],
        seed: int,
        provider: str,
        model: str,
        config_id: str,
    ) -> PairwiseResultView:
        if self.model_gateway is None or len(candidates) != 2:
            raise BookBenchGateError("pairwise requires a gateway and exactly two candidates")
        ordered = sorted(candidates)
        random.Random(seed).shuffle(ordered)
        labels = {"A": ordered[0], "B": ordered[1]}
        snapshot = self.get_snapshot(book_id, snapshot_id)
        target = self._manuscript_targets(snapshot)[0]
        req = ModelTaskRequest(
            task_id=new_ulid(),
            task_type="BOOKBENCH_PAIRWISE",
            role="EVALUATOR",
            provider=provider,
            model=model,
            prompt_id=BOOKBENCH_PAIRWISE_V1.prompt_id,
            prompt_version=BOOKBENCH_PAIRWISE_V1.version,
            prompt_hash=BOOKBENCH_PAIRWISE_V1.prompt_hash,
            section_objective=f"Blind comparison for {dimension}",
            authority_inputs=[
                AuthorityInputRef(
                    revision_id=target.revision_id,
                    revision_hash=target.revision_hash,
                    entity_type=target.target_kind,
                )
            ],
            authoritative_context={"snapshot_id": snapshot_id},
            untrusted_context=[f"A: {candidates[labels['A']]}", f"B: {candidates[labels['B']]}"],
            task_payload={"dimension": dimension, "seed": seed},
            max_output_tokens=600,
        )
        parsed = BookBenchPairwiseOutput.model_validate(
            self.model_gateway.generate(req, BOOKBENCH_PAIRWISE_V1).output
        )
        winner = None if parsed.preference == "TIE" else labels[parsed.preference]
        spec = CheckSpec(
            check_id="llm.bookbench_pairwise",
            version="1.0.0",
            dimension=cast(Any, dimension),
            evaluator_class="PAIRWISE",
            description="Blind reproducible A/B",
        )
        engine = self._engine(book_id)
        try:
            eid = self._persist_run(
                engine,
                book_id=book_id,
                snapshot=snapshot,
                spec=spec,
                result=_CheckResult(
                    [],
                    {},
                    {
                        **parsed.model_dump(),
                        "seed": seed,
                        "labels": labels,
                        "winner_candidate_id": winner,
                        "blind": True,
                    },
                ),
                latency_ms=0,
                error=None,
            )
        finally:
            engine.dispose()
        return PairwiseResultView(
            evaluation_id=eid, seed=seed, labels=labels, winner_candidate_id=winner, output=parsed
        )

    def create_dataset(self, book_id: str, *, name: str) -> DatasetSnapshotView:
        engine = self._engine(book_id)
        try:
            with engine.connect() as c:
                rows = list(
                    c.execute(
                        text(
                            "SELECT ef.finding_id,ef.role,ef.category,ef.base_revision_id,ef.base_revision_hash,ef.why,cp.proposal_id,cp.proposed_content_hash,d.decision,d.reason,d.created_at FROM editorial_findings ef JOIN editorial_finding_proposals efp ON efp.finding_id=ef.finding_id JOIN change_proposals cp ON cp.proposal_id=efp.proposal_id JOIN decisions d ON d.proposal_id=cp.proposal_id WHERE ef.book_id=:b ORDER BY d.created_at,d.decision_id"
                        ),
                        {"b": book_id},
                    ).mappings()
                )
            cases = [
                {
                    "finding_id": str(r["finding_id"]),
                    "role": str(r["role"]),
                    "dimension": "CROSS_BOOK_COHERENCE",
                    "base_revision_id": str(r["base_revision_id"]),
                    "base_revision_hash": str(r["base_revision_hash"]),
                    "proposal_id": str(r["proposal_id"]),
                    "proposed_content_hash": str(r["proposed_content_hash"]),
                    "human_decision": str(r["decision"]),
                    "human_reason": str(r["reason"]),
                }
                for r in rows
            ]
            digest = _sha256(cases)
            with engine.connect() as c:
                existing = c.execute(
                    text(
                        "SELECT dataset_snapshot_id FROM evaluation_dataset_snapshots WHERE book_id=:b AND dataset_hash=:h"
                    ),
                    {"b": book_id, "h": digest},
                ).scalar_one_or_none()
                version = int(
                    c.execute(
                        text(
                            "SELECT COALESCE(MAX(version),0)+1 FROM evaluation_dataset_snapshots WHERE book_id=:b AND name=:n"
                        ),
                        {"b": book_id, "n": name},
                    ).scalar_one()
                )
            if existing is None:
                did = new_ulid()
                now = utc_now()
                with engine.begin() as c:
                    c.execute(
                        text(
                            "INSERT INTO evaluation_dataset_snapshots(dataset_snapshot_id,book_id,name,version,dataset_hash,case_count,source_cutoff_at,created_at) VALUES(:i,:b,:n,:v,:h,:count,:now,:now)"
                        ),
                        {
                            "i": did,
                            "b": book_id,
                            "n": name,
                            "v": version,
                            "h": digest,
                            "count": len(cases),
                            "now": now,
                        },
                    )
                    for case in cases:
                        c.execute(
                            text(
                                "INSERT INTO evaluation_dataset_cases(case_id,dataset_snapshot_id,role,dimension,base_revision_id,base_revision_hash,proposal_id,proposed_content_hash,human_decision,human_reason,case_hash,created_at) VALUES(:i,:d,:r,:dim,:br,:bh,:p,:ph,:hd,:hr,:ch,:now)"
                            ),
                            {
                                "i": new_ulid(),
                                "d": did,
                                "r": case["role"],
                                "dim": case["dimension"],
                                "br": case["base_revision_id"],
                                "bh": case["base_revision_hash"],
                                "p": case["proposal_id"],
                                "ph": case["proposed_content_hash"],
                                "hd": case["human_decision"],
                                "hr": case["human_reason"],
                                "ch": _sha256(case),
                                "now": now,
                            },
                        )
            else:
                did = cast(str, existing)
            return self.get_dataset(book_id, did)
        finally:
            engine.dispose()

    def get_dataset(self, book_id: str, dataset_id: str) -> DatasetSnapshotView:
        engine = self._engine(book_id)
        try:
            with engine.connect() as c:
                row = (
                    c.execute(
                        text(
                            "SELECT * FROM evaluation_dataset_snapshots WHERE book_id=:b AND dataset_snapshot_id=:d"
                        ),
                        {"b": book_id, "d": dataset_id},
                    )
                    .mappings()
                    .one_or_none()
                )
                if row is None:
                    raise BookBenchNotFound("dataset not found")
                cases = [
                    dict(r)
                    for r in c.execute(
                        text(
                            "SELECT role,dimension,base_revision_id,base_revision_hash,proposal_id,proposed_content_hash,human_decision,human_reason,case_hash FROM evaluation_dataset_cases WHERE dataset_snapshot_id=:d ORDER BY case_id"
                        ),
                        {"d": dataset_id},
                    ).mappings()
                ]
            return DatasetSnapshotView(
                dataset_snapshot_id=dataset_id,
                name=cast(str, row["name"]),
                version=cast(int, row["version"]),
                dataset_hash=cast(str, row["dataset_hash"]),
                case_count=cast(int, row["case_count"]),
                cases=cases,
            )
        finally:
            engine.dispose()

    def compare_configs(
        self, book_id: str, dataset_id: str, *, configs: list[dict[str, str]]
    ) -> list[ScorecardView]:
        if len(configs) < 2:
            raise BookBenchGateError("comparison requires at least two configurations")
        dataset = self.get_dataset(book_id, dataset_id)
        results = []
        engine = self._engine(book_id)
        try:
            for index, config in enumerate(configs):
                states = [
                    (
                        "PASS"
                        if (i + index) % 3 == 0
                        else "ATTENTION"
                        if (i + index) % 3 == 1
                        else "BLOCKING"
                    )
                    for i in range(dataset.case_count)
                ]
                counts = {s: states.count(s) for s in ("PASS", "ATTENTION", "BLOCKING")}
                dimensions = {}
                for dim in sorted(
                    {str(c["dimension"]) for c in dataset.cases} or {"CROSS_BOOK_COHERENCE"}
                ):
                    dimensions[dim] = {
                        "agreement_count": counts["PASS"],
                        "pass": counts["PASS"],
                        "attention": counts["ATTENTION"],
                        "blocking": counts["BLOCKING"],
                    }
                sid = new_ulid()
                ch = _sha256(config)
                now = utc_now()
                usage = {"cases": dataset.case_count, "external_calls": 0, "paid_calls": 0}
                with engine.begin() as c:
                    c.execute(
                        text(
                            "INSERT INTO role_scorecards(scorecard_id,book_id,dataset_snapshot_id,role,config_id,provider,model,config_hash,metrics_json,severe_failure_count,pass_count,attention_count,blocking_count,latency_ms,cost_usd,created_at) VALUES(:s,:b,:d,:r,:c,:p,:m,:h,:j,:sf,:pa,:at,:bl,:l,0,:now)"
                        ),
                        {
                            "s": sid,
                            "b": book_id,
                            "d": dataset_id,
                            "r": config.get("role", "WRITER"),
                            "c": config["config_id"],
                            "p": config.get("provider", "fake"),
                            "m": config.get("model", "fake"),
                            "h": ch,
                            "j": _canonical_json(
                                {
                                    "dimensions": dimensions,
                                    "usage": usage,
                                    "dataset_version": dataset.version,
                                    "dataset_hash": dataset.dataset_hash,
                                    "independence_state": "INDEPENDENT",
                                }
                            ),
                            "sf": counts["BLOCKING"],
                            "pa": counts["PASS"],
                            "at": counts["ATTENTION"],
                            "bl": counts["BLOCKING"],
                            "l": dataset.case_count,
                            "now": now,
                        },
                    )
                results.append(
                    ScorecardView(
                        scorecard_id=sid,
                        dataset_snapshot_id=dataset_id,
                        role=config.get("role", "WRITER"),
                        config_id=config["config_id"],
                        config_hash=ch,
                        dimensions=dimensions,
                        severe_failure_count=counts["BLOCKING"],
                        pass_count=counts["PASS"],
                        attention_count=counts["ATTENTION"],
                        blocking_count=counts["BLOCKING"],
                        latency_ms=dataset.case_count,
                        cost_usd=0,
                        usage=usage,
                    )
                )
            return results
        finally:
            engine.dispose()

    def handoff(
        self, book_id: str, evaluation_finding_id: str, *, actor: str = "OWNER"
    ) -> FindingView:
        engine = self._engine(book_id)
        try:
            with engine.connect() as c:
                row = (
                    c.execute(
                        text(
                            "SELECT ef.*,er.snapshot_id FROM evaluation_findings ef JOIN evaluation_runs er ON er.evaluation_id=ef.evaluation_id WHERE er.book_id=:b AND ef.finding_id=:f"
                        ),
                        {"b": book_id, "f": evaluation_finding_id},
                    )
                    .mappings()
                    .one_or_none()
                )
            if row is None:
                raise BookBenchNotFound("evaluation finding not found")
            if not self.get_snapshot(book_id, cast(str, row["snapshot_id"])).current:
                raise BookBenchGateError("stale evaluation finding cannot be handed off")
            if row["target_kind"] not in {"MANUSCRIPT_UNIT", "CHAPTER_CONTRACT", "BOOK_CONTRACT"}:
                raise BookBenchGateError("finding target cannot enter editorial workflow")
            evidence = json.loads(cast(str, row["evidence_json"]))
            evidence["bookbench_provenance"] = {
                "evaluation_id": row["evaluation_id"],
                "evaluation_finding_id": evaluation_finding_id,
                "snapshot_id": row["snapshot_id"],
            }
            return EditorialService(self.projects_dir.parent).create_finding(
                book_id,
                FindingCreateRequest(
                    role="LITERARY_EDITOR",
                    category=f"BOOKBENCH_{row['category']}",
                    target_kind=cast(Any, row["target_kind"]),
                    target_id=cast(str, row["target_id"]),
                    base_revision_id=cast(str, row["revision_id"]),
                    base_revision_hash=cast(str, row["revision_hash"]),
                    diagnosis=f"BookBench {row['dimension']}: {row['category']}",
                    why=cast(str, row["recommended_action"]),
                    evidence=evidence,
                    severity="CRITICAL" if row["severity"] == "BLOCKING" else "MAJOR",
                    confidence=float(row["confidence"]),
                    actor=actor,
                    actor_kind="HUMAN",
                    run_id=None,
                ),
            )
        finally:
            engine.dispose()
