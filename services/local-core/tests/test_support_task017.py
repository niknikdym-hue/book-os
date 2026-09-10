from __future__ import annotations

from pathlib import Path

from book_os_core.series_production import (
    AdmissionChecks,
    ChapterAdmissionRequest,
    ChapterProductionContractApprovalRequest,
    ChapterProductionContractContent,
    ChapterProductionContractCreateRequest,
    DefinitionPackApprovalRequest,
    DefinitionPackContent,
    DefinitionPackCreateRequest,
    PracticalValueItem,
    ProductionCheckpointRequest,
    SeriesProductionService,
    UniquenessEvidenceRequest,
)

_ACTOR = "Task 017 legacy test fixture"


def _definition_content() -> DefinitionPackContent:
    return DefinitionPackContent(
        reader_and_real_problem="Legacy success fixture with explicit Task 017 production authority",
        central_promise="Exercise the historical success path without bypassing production gates",
        central_thesis="Tests must satisfy the same explicit admission prerequisites as runtime",
        central_mechanism="Definition, contract, uniqueness evidence, then human chapter admission",
        not_this_book=["No autonomous approval"],
        category_competitor_substitute_map=["Synthetic deterministic test fixture"],
        world_class_benchmark=["Explicit reproducible gate evidence"],
        original_contribution_hypothesis="Preserve historical regression coverage under Task 017",
        research_evidence_functions=["Deterministic fixture evidence only"],
        practical_value_map=[
            PracticalValueItem(
                problem="A historical positive test predates the Task 017 writing gate",
                decision="Make its positive prerequisites explicit",
                action="Create current production evidence through the public service",
                artifact_output="A WRITING_ALLOWED chapter admission",
                observable_check="The admission status reports writing_allowed true",
            )
        ],
        target_market_application="Synthetic regression fixture; no market claim is made",
        uniqueness_overlap_proof="The fixture records an explicit current PASS for overlap evidence",
        ai_substitution_result="PASS",
        top_tier_global="PASS",
        original_contribution="PASS",
        practical_value="PASS",
        target_market_quality="PASS",
    )


def _production_contract_content() -> ChapterProductionContractContent:
    return ChapterProductionContractContent(
        unique_question="Can the historical positive path run while honoring Task 017?",
        mechanism_causal_chain="Current authority -> production contract -> uniqueness PASS -> admission",
        reader_prior_state="The legacy fixture has approved chapter authority but no production admission",
        reader_after_state="The fixture has explicit current production admission evidence",
        contribution_relative_to_adjacent="This contract exists only to preserve the isolated legacy success path",
        evidence_function="Provide deterministic fixture evidence for the production gate",
        evidence_limits="No external, provider, paid, or manuscript evidence is introduced",
        not_this_chapter=["No runtime auto-admission"],
        opening_intent="Start from the exact approved chapter authority",
        development_intent="Bind the production contract to the current authority heads",
        complication_intent="Require uniqueness evidence rather than assuming it",
        ending_intent="End only after explicit human/owner admission",
        decision_enabled="The legacy test may invoke Writer only after all gates pass",
        next_action="Run the bounded historical success-path assertion",
        practical_artifact="Current chapter production admission",
        observable_check="SeriesProductionService.admission_status is WRITING_ALLOWED",
        target_market_application="Synthetic test fixture only",
        composition_intent="Keep the fixture minimal and deterministic",
        deletion_merge_test="PASS",
        ai_substitution_result="PASS",
        top_tier_global="PASS",
        original_contribution="PASS",
        practical_value="PASS",
        target_market_quality="PASS",
    )


def ensure_writing_allowed_for_test(data_dir: Path, book_id: str, chapter_id: str) -> None:
    service = SeriesProductionService(data_dir)
    definition = service.latest_approved_definition(book_id)
    if definition is None:
        definition = service.create_definition_pack(
            book_id,
            DefinitionPackCreateRequest(
                content=_definition_content(),
                actor_kind="SYSTEM",
                actor=_ACTOR,
            ),
        )
        definition = service.approve_definition_pack(
            book_id,
            definition.definition_id,
            DefinitionPackApprovalRequest(actor_kind="OWNER", actor=_ACTOR),
        )

    contract = service.latest_approved_production_contract(book_id, chapter_id)
    if contract is None:
        contract = service.create_production_contract(
            book_id,
            chapter_id,
            ChapterProductionContractCreateRequest(
                content=_production_contract_content(),
                actor_kind="SYSTEM",
                actor=_ACTOR,
            ),
        )
        contract = service.approve_production_contract(
            book_id,
            chapter_id,
            contract.production_contract_id,
            ChapterProductionContractApprovalRequest(actor_kind="OWNER", actor=_ACTOR),
        )

    service.record_uniqueness(
        book_id,
        chapter_id,
        UniquenessEvidenceRequest(
            status="PASS",
            evidence={"fixture": "explicit-current-overlap-pass"},
            actor_kind="SYSTEM",
            actor=_ACTOR,
        ),
    )
    status = service.admit_chapter(
        book_id,
        chapter_id,
        ChapterAdmissionRequest(
            checks=AdmissionChecks(
                evidence_readiness="PASS",
                boundaries_reservations="PASS",
                top_tier_global="PASS",
                original_contribution="PASS",
                practical_value="PASS",
                target_market_application="PASS",
                freshness="PASS",
                anti_junk_provenance="PASS",
                deletion_merge_test="PASS",
                conditional_blockers_resolved=True,
            ),
            actor_kind="OWNER",
            actor=_ACTOR,
            reason="Historical positive fixture explicitly satisfies Task 017",
        ),
    )
    assert status.writing_allowed is True


def record_independent_adversarial_review_for_test(data_dir: Path, book_id: str) -> None:
    service = SeriesProductionService(data_dir)
    service.record_checkpoint(
        book_id,
        ProductionCheckpointRequest(
            kind="ADVERSARIAL_REVIEW",
            status="PASS",
            findings=[],
            actor_kind="SYSTEM",
            actor=_ACTOR,
            executor_identity="independent-task017-test-reviewer",
            independent=True,
        ),
    )
    allowed, blockers = service.adversarial_review_gate(book_id)
    assert allowed is True
    assert blockers == []
