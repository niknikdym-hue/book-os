from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Literal

BookBenchDimension = Literal[
    "BOOK_CONTRACT_FULFILLMENT",
    "CHAPTER_CONTRACT_FULFILLMENT",
    "SEMANTIC_NOVELTY",
    "IDEA_REPETITION",
    "CONTRADICTION_INCONSISTENCY",
    "THOUGHT_DENSITY",
    "SPECIFICITY_GENERICNESS",
    "EVIDENCE_UNSUPPORTED_CLAIMS",
    "AUTHOR_VOICE",
    "AI_PROSE_PATHOLOGY",
    "OPENING_ENDING_TRANSITION",
    "CROSS_BOOK_COHERENCE",
]
EvaluatorClass = Literal["DETERMINISTIC", "SEMANTIC", "LLM_JUDGE", "PAIRWISE", "HUMAN_LABEL"]


@dataclass(frozen=True)
class CheckSpec:
    check_id: str
    version: str
    dimension: BookBenchDimension
    evaluator_class: EvaluatorClass
    description: str

    def canonical(self) -> dict[str, str]:
        return {
            "check_id": self.check_id,
            "version": self.version,
            "dimension": self.dimension,
            "evaluator_class": self.evaluator_class,
            "description": self.description,
        }


CHECKS: tuple[CheckSpec, ...] = (
    CheckSpec(
        "deterministic.repetition",
        "1.0.0",
        "IDEA_REPETITION",
        "DETERMINISTIC",
        "Exact/normalized repeated sentence and phrase signals across current manuscript units.",
    ),
    CheckSpec(
        "deterministic.statistics",
        "1.0.0",
        "THOUGHT_DENSITY",
        "DETERMINISTIC",
        "Sentence/paragraph length, lexical diversity and rhetorical-question measurements.",
    ),
    CheckSpec(
        "deterministic.specificity",
        "1.0.0",
        "SPECIFICITY_GENERICNESS",
        "DETERMINISTIC",
        "Concrete-number/proper-name versus versioned empty-abstraction signals.",
    ),
    CheckSpec(
        "deterministic.evidence",
        "1.0.0",
        "EVIDENCE_UNSUPPORTED_CLAIMS",
        "DETERMINISTIC",
        "Material unresolved Claim states and stale manuscript bindings.",
    ),
    CheckSpec(
        "deterministic.contract_structure",
        "1.0.0",
        "CHAPTER_CONTRACT_FULFILLMENT",
        "DETERMINISTIC",
        "Conservative lexical/structural Chapter Contract coverage signals.",
    ),
    CheckSpec(
        "deterministic.ai_prose_pathology",
        "1.0.0",
        "AI_PROSE_PATHOLOGY",
        "DETERMINISTIC",
        "Measured versioned prose-pattern occurrences; never an AI-authorship probability.",
    ),
    CheckSpec(
        "deterministic.opening_ending_transition",
        "1.0.0",
        "OPENING_ENDING_TRANSITION",
        "DETERMINISTIC",
        "Structural opening/ending/transition presence and repeated-template signals.",
    ),
    CheckSpec(
        "semantic.idea_duplication",
        "1.0.0",
        "SEMANTIC_NOVELTY",
        "SEMANTIC",
        "Embedding-based semantic duplication/novelty candidates across exact current revisions.",
    ),
    CheckSpec(
        "semantic.contract_coverage",
        "1.0.0",
        "BOOK_CONTRACT_FULFILLMENT",
        "SEMANTIC",
        "Embedding-based Contract coverage/drift candidates; not semantic truth.",
    ),
    CheckSpec(
        "judge.dimension",
        "1.0.0",
        "CROSS_BOOK_COHERENCE",
        "LLM_JUDGE",
        "Bounded structured LLM judge for one explicit BookBench dimension/rubric.",
    ),
    CheckSpec(
        "judge.pairwise",
        "1.0.0",
        "CROSS_BOOK_COHERENCE",
        "PAIRWISE",
        "Blind reproducible A/B comparison for one bounded dimension/rubric.",
    ),
)

CHECK_BY_ID = {check.check_id: check for check in CHECKS}


def registry_hash() -> str:
    payload = json.dumps(
        [check.canonical() for check in CHECKS],
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def get_check(check_id: str) -> CheckSpec:
    try:
        return CHECK_BY_ID[check_id]
    except KeyError as exc:
        raise KeyError(f"unknown BookBench check: {check_id}") from exc
