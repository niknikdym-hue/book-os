from __future__ import annotations

from pathlib import Path

ROOT = Path("services/local-core")
TESTS = ROOT / "tests"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one match, got {count}: {old!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


SUPPORT = '''from __future__ import annotations

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
'''

(TESTS / "test_support_task017.py").write_text(SUPPORT, encoding="utf-8")

# Drafting legacy positive fixture. The intentionally unapproved negative test does not use ready_project.
path = TESTS / "test_drafting.py"
replace_once(
    path,
    ")\n\n\ndef book_contract() -> BookContractPayload:",
    ")\nfrom test_support_task017 import ensure_writing_allowed_for_test\n\n\ndef book_contract() -> BookContractPayload:",
)
replace_once(
    path,
    "    service.approve_chapter_contract(project.book_id, chapter_id)\n    return service, project.book_id, chapter_id",
    "    service.approve_chapter_contract(project.book_id, chapter_id)\n    ensure_writing_allowed_for_test(data_dir, project.book_id, chapter_id)\n    return service, project.book_id, chapter_id",
)

# BookBench two-chapter positive fixture.
path = TESTS / "test_bookbench.py"
replace_once(
    path,
    "from book_os_core.research_adapters import ResearchGateway\n",
    "from book_os_core.research_adapters import ResearchGateway\nfrom test_support_task017 import ensure_writing_allowed_for_test\n",
)
replace_once(
    path,
    "    projects.approve_chapter_contract(project.book_id, second_chapter.chapter_id)\n\n    duplicate_objective = (",
    "    projects.approve_chapter_contract(project.book_id, second_chapter.chapter_id)\n    ensure_writing_allowed_for_test(data_dir, project.book_id, first_chapter.chapter_id)\n    ensure_writing_allowed_for_test(data_dir, project.book_id, second_chapter.chapter_id)\n\n    duplicate_objective = (",
)

# Editorial two-chapter positive fixture.
path = TESTS / "test_editorial.py"
replace_once(
    path,
    "from book_os_core.research_adapters import ResearchGateway\n",
    "from book_os_core.research_adapters import ResearchGateway\nfrom test_support_task017 import ensure_writing_allowed_for_test\n",
)
replace_once(
    path,
    "    projects.approve_chapter_contract(project.book_id, second_chapter.chapter_id)\n\n    duplicate_objective = (",
    "    projects.approve_chapter_contract(project.book_id, second_chapter.chapter_id)\n    ensure_writing_allowed_for_test(data_dir, project.book_id, first_chapter.chapter_id)\n    ensure_writing_allowed_for_test(data_dir, project.book_id, second_chapter.chapter_id)\n\n    duplicate_objective = (",
)

# Editorial API one-chapter positive fixture.
path = TESTS / "test_editorial_api.py"
replace_once(
    path,
    ")\n\n\ndef book_contract() -> BookContractPayload:",
    ")\nfrom test_support_task017 import ensure_writing_allowed_for_test\n\n\ndef book_contract() -> BookContractPayload:",
)
replace_once(
    path,
    "    projects.approve_chapter_contract(project.book_id, chapter_id)\n\n    drafting = DraftingService",
    "    projects.approve_chapter_contract(project.book_id, chapter_id)\n    ensure_writing_allowed_for_test(data_dir, project.book_id, chapter_id)\n\n    drafting = DraftingService",
)

# Memory two-chapter positive fixture.
path = TESTS / "test_memory.py"
replace_once(
    path,
    "from book_os_core.research_adapters import ResearchGateway\n",
    "from book_os_core.research_adapters import ResearchGateway\nfrom test_support_task017 import ensure_writing_allowed_for_test\n",
)
replace_once(
    path,
    "    projects.approve_chapter_contract(project.book_id, second_chapter.chapter_id)\n\n    drafting = DraftingService",
    "    projects.approve_chapter_contract(project.book_id, second_chapter.chapter_id)\n    ensure_writing_allowed_for_test(data_dir, project.book_id, first_chapter.chapter_id)\n    ensure_writing_allowed_for_test(data_dir, project.book_id, second_chapter.chapter_id)\n\n    drafting = DraftingService",
)

# Research one-chapter positive fixture.
path = TESTS / "test_research.py"
replace_once(
    path,
    "from book_os_core.research_adapters import ResearchCandidate, ResearchGateway\n",
    "from book_os_core.research_adapters import ResearchCandidate, ResearchGateway\nfrom test_support_task017 import ensure_writing_allowed_for_test\n",
)
replace_once(
    path,
    "    projects.approve_chapter_contract(project.book_id, chapter_id)\n\n    drafting = DraftingService(",
    "    projects.approve_chapter_contract(project.book_id, chapter_id)\n    ensure_writing_allowed_for_test(data_dir, project.book_id, chapter_id)\n\n    drafting = DraftingService(",
)

# Release fixture explicitly satisfies unrelated independent review prerequisite.
path = TESTS / "test_literary_master.py"
replace_once(
    path,
    "from book_os_core.literary_master import LiteraryMasterGateError, LiteraryMasterService\n",
    "from book_os_core.literary_master import LiteraryMasterGateError, LiteraryMasterService\nfrom test_support_task017 import record_independent_adversarial_review_for_test\n",
)
replace_once(
    path,
    "    engine.dispose()\n    return book_id",
    "    engine.dispose()\n    record_independent_adversarial_review_for_test(data_dir, book_id)\n    return book_id",
)
replace_once(path, '["alembic_revision"] == "0015"', '["alembic_revision"] == "0016"')

# Pilot temporal tests insert synthetic masters directly; add explicit review before only _insert_master.
path = TESTS / "test_pilot_temporal_evidence.py"
replace_once(
    path,
    "from book_os_core.projects import NewBookRequest, ProjectService\n",
    "from book_os_core.projects import NewBookRequest, ProjectService\nfrom test_support_task017 import record_independent_adversarial_review_for_test\n",
)
master_old = '''def _insert_master(
    data_dir: Path,
    book_id: str,
    book_contract_revision_id: str,
    book_contract_revision_hash: str,
    architecture_revision_id: str,
    architecture_revision_hash: str,
    *,
    master_id: str,
    created_at: str,
) -> None:
    database = data_dir / "projects" / book_id / "project.sqlite"
'''
master_new = '''def _insert_master(
    data_dir: Path,
    book_id: str,
    book_contract_revision_id: str,
    book_contract_revision_hash: str,
    architecture_revision_id: str,
    architecture_revision_hash: str,
    *,
    master_id: str,
    created_at: str,
) -> None:
    record_independent_adversarial_review_for_test(data_dir, book_id)
    database = data_dir / "projects" / book_id / "project.sqlite"
'''
replace_once(path, master_old, master_new)

# Assertions that mean current schema head now point to 0016.
path = TESTS / "test_authority.py"
replace_once(path, '            == "0015"\n', '            == "0016"\n')

path = TESTS / "test_core.py"
replace_once(path, '            == "0015"\n', '            == "0016"\n')
replace_once(path, '            "0015",\n        }', '            "0015",\n            "0016",\n        }')

path = TESTS / "test_pilot.py"
replace_once(path, '                == "0015"\n', '                == "0016"\n')

path = TESTS / "test_projects.py"
replace_once(path, '            == "0015"\n', '            == "0016"\n')
