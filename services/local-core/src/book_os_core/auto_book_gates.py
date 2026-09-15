from __future__ import annotations

from itertools import combinations
import re
from typing import Any, Literal

from pydantic import BaseModel, Field

from .model_gateway import BookConceptProposalOutput
from .prompts import SECTION_DRAFT_V1


GateStatus = Literal["PASS", "BLOCKING"]


class EvidenceCheck(BaseModel):
    gate: str
    status: GateStatus
    evidence: dict[str, Any] = Field(min_length=1)
    evaluation_scope: Literal["STRUCTURAL_PREFLIGHT"] = "STRUCTURAL_PREFLIGHT"
    semantic_quality_claimed: Literal[False] = False


class EvidenceGateResult(BaseModel):
    status: GateStatus
    checks: list[EvidenceCheck] = Field(min_length=1)

    @property
    def blockers(self) -> list[str]:
        return [item.gate for item in self.checks if item.status == "BLOCKING"]

    def result_for(self, gate: str) -> GateStatus:
        return next(item.status for item in self.checks if item.gate == gate)


class AutoBookEvidenceGates:
    """Deterministic structural preflight gates; reaching a stage is never quality evidence.

    These checks validate completeness, distinct fields and cheap structural invariants only.
    They deliberately do not claim literary, intellectual, market or semantic quality.  Those
    properties are evaluated later against the exact whole-book snapshot by the independent
    critic and human authority.
    """

    _TOKEN = re.compile(r"[а-яёa-z0-9]{3,}", re.IGNORECASE)
    _GENERIC = {
        "книга о теме",
        "для всех",
        "целевая аудитория",
        "аудитория книги",
        "вопрос главы решен",
        "уникальная функция главы",
        "механизм уточнен",
        "практический результат",
    }

    @classmethod
    def _tokens(cls, value: object) -> set[str]:
        return set(cls._TOKEN.findall(str(value).casefold()))

    @classmethod
    def _specific(cls, value: object, *, minimum: int = 3) -> bool:
        normalized = " ".join(cls._TOKEN.findall(str(value).casefold()))
        return len(cls._tokens(value)) >= minimum and normalized not in cls._GENERIC

    @staticmethod
    def _check(gate: str, passed: bool, evidence: dict[str, Any]) -> EvidenceCheck:
        return EvidenceCheck(gate=gate, status="PASS" if passed else "BLOCKING", evidence=evidence)

    @classmethod
    def _result(cls, checks: list[EvidenceCheck]) -> EvidenceGateResult:
        return EvidenceGateResult(
            status=("BLOCKING" if any(item.status == "BLOCKING" for item in checks) else "PASS"),
            checks=checks,
        )

    @classmethod
    def concept(cls, concept: BookConceptProposalOutput) -> EvidenceGateResult:
        transformation_distinct = cls._tokens(concept.reader_problem) != cls._tokens(
            concept.reader_transformation
        )
        idea_distinct = cls._tokens(concept.central_idea) != cls._tokens(concept.central_promise)
        scopes_disjoint = bool(
            cls._tokens(" ".join(concept.scope_in)) - cls._tokens(" ".join(concept.scope_out))
        )
        checks = [
            cls._check(
                "reader_job",
                cls._specific(concept.reader_job),
                {"reader_job": concept.reader_job},
            ),
            cls._check(
                "reader_problem",
                cls._specific(concept.reader_problem, minimum=4),
                {"reader_problem": concept.reader_problem},
            ),
            cls._check(
                "reader_transformation",
                cls._specific(concept.reader_transformation, minimum=4) and transformation_distinct,
                {
                    "reader_transformation": concept.reader_transformation,
                    "distinct_from_problem": transformation_distinct,
                },
            ),
            cls._check(
                "central_idea_and_promise",
                cls._specific(concept.central_idea, minimum=4)
                and cls._specific(concept.central_promise, minimum=3)
                and idea_distinct,
                {
                    "central_idea": concept.central_idea,
                    "central_promise": concept.central_promise,
                    "distinct": idea_distinct,
                },
            ),
            cls._check(
                "differentiation",
                cls._specific(concept.differentiation, minimum=4),
                {"differentiation": concept.differentiation},
            ),
            cls._check(
                "why_now",
                cls._specific(concept.why_now, minimum=3),
                {"why_now": concept.why_now},
            ),
            cls._check(
                "scope",
                bool(concept.scope_in and concept.scope_out and scopes_disjoint),
                {
                    "scope_in": concept.scope_in,
                    "scope_out": concept.scope_out,
                    "has_distinct_in_scope": scopes_disjoint,
                },
            ),
            cls._check(
                "series_position",
                cls._specific(concept.series_place, minimum=3),
                {
                    "series_place": concept.series_place,
                    "overlap_risks": concept.overlap_risks,
                },
            ),
        ]
        return cls._result(checks)

    @classmethod
    def definition(
        cls,
        book_contract: dict[str, Any],
        concept: BookConceptProposalOutput,
    ) -> EvidenceGateResult:
        reader = str(book_contract.get("reader", ""))
        problem = str(book_contract.get("reader_problem", ""))
        promise = str(book_contract.get("central_promise", ""))
        thesis = str(book_contract.get("central_thesis", ""))
        angle = str(book_contract.get("unique_angle", ""))
        trajectory = str(book_contract.get("reader_trajectory", ""))
        exclusions = list(book_contract.get("explicit_exclusions", []))
        readiness = list(book_contract.get("readiness_criteria", []))
        checks = [
            cls._check(
                "ai_substitution_result",
                cls._specific(thesis, minimum=5)
                and cls._specific(angle, minimum=4)
                and cls._specific(concept.differentiation, minimum=4),
                {
                    "central_thesis": thesis,
                    "unique_angle": angle,
                    "concept_differentiation": concept.differentiation,
                },
            ),
            cls._check(
                "top_tier_global",
                all(
                    (
                        cls._specific(problem, minimum=4),
                        cls._specific(promise, minimum=4),
                        cls._specific(thesis, minimum=5),
                        bool(exclusions),
                    )
                ),
                {
                    "reader_problem": problem,
                    "central_promise": promise,
                    "central_thesis": thesis,
                    "explicit_exclusions": exclusions,
                },
            ),
            cls._check(
                "original_contribution",
                cls._specific(angle, minimum=4) and cls._tokens(angle) != cls._tokens(thesis),
                {
                    "unique_angle": angle,
                    "distinct_from_thesis": cls._tokens(angle) != cls._tokens(thesis),
                },
            ),
            cls._check(
                "practical_value",
                cls._specific(problem, minimum=4)
                and cls._specific(trajectory, minimum=4)
                and bool(readiness),
                {
                    "reader_problem": problem,
                    "reader_trajectory": trajectory,
                    "readiness_criteria": readiness,
                },
            ),
            cls._check(
                "target_market_quality",
                cls._specific(reader, minimum=3),
                {"reader": reader},
            ),
        ]
        return cls._result(checks)

    @classmethod
    def architecture(cls, architecture: dict[str, Any]) -> EvidenceGateResult:
        chapters = [
            chapter
            for part in architecture.get("parts", [])
            for chapter in part.get("chapters", [])
            if isinstance(chapter, dict)
        ]
        titles = [str(item.get("title", "")) for item in chapters]
        purposes = [str(item.get("purpose", "")) for item in chapters]
        contributions = [str(item.get("new_contribution", "")) for item in chapters]
        normalized_titles = [" ".join(sorted(cls._tokens(value))) for value in titles]
        normalized_purposes = [" ".join(sorted(cls._tokens(value))) for value in purposes]
        normalized_contributions = [" ".join(sorted(cls._tokens(value))) for value in contributions]
        pair_scores: list[float] = []
        for left, right in combinations(contributions, 2):
            left_tokens = cls._tokens(left)
            right_tokens = cls._tokens(right)
            union = left_tokens | right_tokens
            pair_scores.append(len(left_tokens & right_tokens) / len(union) if union else 1.0)
        distinct = (
            len(set(normalized_titles)) == len(titles)
            and len(set(normalized_purposes)) == len(purposes)
            and len(set(normalized_contributions)) == len(contributions)
            and all(score < 0.8 for score in pair_scores)
        )
        positioned = all(
            index == 0
            or bool(item.get("dependencies"))
            or cls._specific(item.get("transition", ""), minimum=2)
            for index, item in enumerate(chapters)
        )
        checks = [
            cls._check(
                "chapter_functions",
                bool(chapters)
                and all(cls._specific(value, minimum=3) for value in purposes)
                and distinct,
                {
                    "chapter_count": len(chapters),
                    "purposes": purposes,
                    "pairwise_contribution_jaccard": [round(score, 4) for score in pair_scores],
                },
            ),
            cls._check(
                "new_contributions",
                bool(contributions)
                and all(cls._specific(value, minimum=3) for value in contributions)
                and distinct,
                {"new_contributions": contributions, "distinct": distinct},
            ),
            cls._check(
                "dependency_and_position",
                positioned
                and cls._specific(architecture.get("intellectual_progression", ""), minimum=3)
                and cls._specific(architecture.get("major_transitions", ""), minimum=3),
                {
                    "positioned": positioned,
                    "intellectual_progression": architecture.get("intellectual_progression"),
                    "major_transitions": architecture.get("major_transitions"),
                },
            ),
        ]
        return cls._result(checks)

    @classmethod
    def chapter(
        cls,
        chapter_contract: dict[str, Any],
        *,
        architecture: dict[str, Any],
        chapter_ordinal: int,
        reader: str,
    ) -> EvidenceGateResult:
        architecture_result = cls.architecture(architecture)
        purpose = str(chapter_contract.get("chapter_purpose", ""))
        contribution = str(chapter_contract.get("new_contribution", ""))
        prior = str(chapter_contract.get("reader_prior_state", ""))
        after = str(chapter_contract.get("reader_after_state", ""))
        claims = list(chapter_contract.get("required_claims", []))
        research = list(chapter_contract.get("required_or_permitted_research", []))
        reserved = list(chapter_contract.get("reserved_elsewhere", []))
        opening = str(chapter_contract.get("opening_requirements", ""))
        ending = str(chapter_contract.get("ending_requirements", ""))
        draft_policy = SECTION_DRAFT_V1.developer_text.casefold()
        anti_junk_controls = {
            "fabricated_facts_prohibited": "do not fabricate facts" in draft_policy,
            "generic_padding_prohibited": "never pad, repeat, or add generic material"
            in draft_policy,
            "authority_self_approval_prohibited": "do not approve, lock" in draft_policy,
        }
        checks = [
            cls._check(
                "deletion_merge_test",
                architecture_result.status == "PASS"
                and cls._specific(purpose, minimum=3)
                and cls._specific(contribution, minimum=3),
                {
                    "chapter_ordinal": chapter_ordinal,
                    "chapter_purpose": purpose,
                    "new_contribution": contribution,
                    "architecture_gate": architecture_result.model_dump(mode="json"),
                },
            ),
            cls._check(
                "ai_substitution_result",
                bool(claims and research),
                {"required_claims": claims, "research_functions": research},
            ),
            cls._check(
                "top_tier_global",
                cls._specific(opening, minimum=3)
                and cls._specific(ending, minimum=3)
                and prior != after,
                {"opening": opening, "ending": ending, "reader_state_changes": prior != after},
            ),
            cls._check(
                "original_contribution",
                cls._specific(contribution, minimum=3),
                {"new_contribution": contribution},
            ),
            cls._check(
                "practical_value",
                cls._specific(prior, minimum=3)
                and cls._specific(after, minimum=3)
                and cls._tokens(prior) != cls._tokens(after),
                {"reader_prior_state": prior, "reader_after_state": after},
            ),
            cls._check(
                "target_market_quality",
                cls._specific(reader, minimum=3),
                {"reader": reader},
            ),
            cls._check(
                "boundaries_reservations",
                bool(reserved),
                {"reserved_elsewhere": reserved},
            ),
            cls._check(
                "evidence_readiness",
                bool(claims and research),
                {"required_claims": claims, "required_or_permitted_research": research},
            ),
            cls._check(
                "freshness",
                bool(research),
                {"research_plan": research},
            ),
            cls._check(
                "anti_junk_provenance",
                all(anti_junk_controls.values()) and len(SECTION_DRAFT_V1.prompt_hash) == 64,
                {
                    "prompt_id": SECTION_DRAFT_V1.prompt_id,
                    "prompt_version": SECTION_DRAFT_V1.version,
                    "prompt_hash": SECTION_DRAFT_V1.prompt_hash,
                    "verified_controls": anti_junk_controls,
                },
            ),
        ]
        return cls._result(checks)
