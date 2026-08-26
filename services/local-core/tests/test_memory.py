from __future__ import annotations

from pathlib import Path
import time
from typing import cast

import numpy as np
import pytest
from sqlalchemy import text

from book_os_core.authority import AuthorityService, new_ulid
from book_os_core.authority_types import utc_now
from book_os_core.db import create_database
from book_os_core.drafting import DraftSectionRequest, DraftingService
from book_os_core.memory import BookMemoryService, MemoryGateError
from book_os_core.memory_embeddings import (
    DeterministicFakeEmbeddingAdapter,
    EmbeddingGateway,
)
from book_os_core.model_gateway import DeterministicFakeAdapter, ModelGateway
from book_os_core.projects import (
    BookArchitecturePayload,
    BookContractPayload,
    ChapterContractPayload,
    NewBookRequest,
    ProjectService,
)
from book_os_core.research import ClaimCreateRequest, ClaimUpdateRequest, ResearchService
from book_os_core.research_adapters import ResearchGateway


def book_contract(version: str = "v1") -> BookContractPayload:
    return BookContractPayload(
        reader="Business leaders",
        reader_problem=f"They forget cross-book context {version}",
        central_promise="Reliable whole-book recall",
        central_thesis="Structured memory prevents local-context drift",
        unique_angle="Treat retrieval as derived revision-aware state",
        reader_trajectory="From isolated chapter edits to whole-book awareness",
        explicit_exclusions=["No chatbot memory as authority"],
        evidence_policy="Material claims require traceable evidence",
        voice_genre_constraints="Precise business nonfiction",
        readiness_criteria=["Current context is retrievable without stale leakage"],
    )


def architecture() -> BookArchitecturePayload:
    return BookArchitecturePayload.model_validate(
        {
            "parts": [
                {
                    "title": "Part I",
                    "purpose": "Build memory discipline",
                    "chapters": [
                        {
                            "chapter_id": None,
                            "title": "Retrieval",
                            "purpose": "Explain retrieval",
                            "new_contribution": "Hybrid whole-book recall",
                            "dependencies": [],
                            "transition": "Move to consistency",
                        },
                        {
                            "chapter_id": None,
                            "title": "Consistency",
                            "purpose": "Explain revision isolation",
                            "new_contribution": "Current-versus-history discipline",
                            "dependencies": [],
                            "transition": "Move to editorial workflows",
                        },
                    ],
                }
            ],
            "intellectual_progression": "retrieval → revision isolation",
            "concept_allocation": "One memory concept per chapter",
            "promise_thesis_coverage": "Both chapters support whole-book recall",
            "major_transitions": "Retrieval precedes editorial use",
        }
    )


def chapter_contract(name: str) -> ChapterContractPayload:
    return ChapterContractPayload(
        chapter_purpose=f"Explain {name}",
        new_contribution=f"One distinct {name} mechanism",
        reader_prior_state="Reader sees only the active passage",
        reader_after_state="Reader can recover relevant whole-book context",
        required_claims=[f"{name} reduces context loss"],
        required_or_permitted_research=["Use already verified evidence only"],
        required_scenes_examples=[f"One {name} example"],
        reserved_elsewhere=["Editorial decisions belong to M6"],
        opening_requirements="Open with a context failure",
        ending_requirements="End with a stable retrieval reference",
        transition_requirements="Hand off the next memory question",
    )


def ready_memory_book(data_dir: Path) -> dict[str, str]:
    projects = ProjectService(data_dir)
    project = projects.create_project(
        NewBookRequest(working_title="Memory Test Book", primary_subtype="Strategy")
    )
    projects.save_book_contract(project.book_id, book_contract())
    project = projects.approve_book_contract(project.book_id)
    assert project.book_contract is not None
    projects.save_architecture(project.book_id, architecture())
    project = projects.approve_architecture(project.book_id)
    first_chapter = project.chapters[0]
    second_chapter = project.chapters[1]
    projects.save_chapter_contract(
        project.book_id, first_chapter.chapter_id, chapter_contract("retrieval")
    )
    projects.approve_chapter_contract(project.book_id, first_chapter.chapter_id)
    projects.save_chapter_contract(
        project.book_id, second_chapter.chapter_id, chapter_contract("consistency")
    )
    projects.approve_chapter_contract(project.book_id, second_chapter.chapter_id)

    drafting = DraftingService(data_dir, ModelGateway({"fake": DeterministicFakeAdapter()}))
    first = drafting.generate_section_draft(
        project.book_id,
        first_chapter.chapter_id,
        DraftSectionRequest(
            section_objective="Explain the blue lighthouse retrieval mechanism",
            provider="fake",
            model="fake-writer",
        ),
    )
    second = drafting.generate_section_draft(
        project.book_id,
        second_chapter.chapter_id,
        DraftSectionRequest(
            section_objective="Explain the copper compass consistency mechanism",
            provider="fake",
            model="fake-writer",
        ),
    )
    assert first.unit_id and first.revision_id and first.revision_hash and first.text
    assert second.unit_id and second.revision_id and second.revision_hash and second.text

    research = ResearchService(data_dir, ResearchGateway({}))
    claim = research.create_claim(
        project.book_id,
        ClaimCreateRequest(
            chapter_id=first_chapter.chapter_id,
            unit_id=first.unit_id,
            manuscript_revision_id=first.revision_id,
            manuscript_revision_hash=first.revision_hash,
            normalized_text="Hybrid memory reduces context loss across chapters.",
            claim_type="EMPIRICAL",
            materiality="HIGH",
            required_evidence_level="TRACEABLE_SOURCE",
        ),
    )
    return {
        "book_id": project.book_id,
        "book_contract_entity": project.book_contract.entity_id,
        "chapter_1": first_chapter.chapter_id,
        "chapter_2": second_chapter.chapter_id,
        "unit_1": first.unit_id,
        "unit_2": second.unit_id,
        "revision_1": first.revision_id,
        "revision_hash_1": first.revision_hash,
        "revision_2": second.revision_id,
        "revision_hash_2": second.revision_hash,
        "text_1": first.text,
        "text_2": second.text,
        "claim_id": claim.claim_id,
    }


def memory_service(
    data_dir: Path, mapping: dict[str, list[float]] | None = None
) -> BookMemoryService:
    adapter = DeterministicFakeEmbeddingAdapter(mapping=mapping, dimension=3)
    return BookMemoryService(data_dir, EmbeddingGateway({"fake": adapter}))


def test_m5_schema_fts_exact_phrase_and_filters(tmp_path: Path) -> None:
    state = ready_memory_book(tmp_path)
    service = memory_service(tmp_path)
    status = service.synchronize(state["book_id"])
    assert status.status == "LEXICAL_READY"
    assert status.document_count == 6

    engine = create_database(tmp_path / "projects" / state["book_id"] / "project.sqlite")
    with engine.connect() as connection:
        assert (
            connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
            == "0006"
        )
        assert (
            connection.execute(
                text("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='memory_fts'")
            ).scalar_one()
            == 1
        )

    phrase = service.lexical_search(
        state["book_id"],
        "blue lighthouse retrieval mechanism",
        exact_phrase=True,
        object_kinds=["MANUSCRIPT_UNIT"],
    )
    assert len(phrase) == 1
    assert phrase[0].object_id == state["unit_1"]
    assert phrase[0].revision_id == state["revision_1"]
    assert phrase[0].revision_hash == state["revision_hash_1"]
    assert phrase[0].currentness == "CURRENT"

    assert (
        service.lexical_search(
            state["book_id"],
            "blue lighthouse",
            chapter_id=state["chapter_2"],
            object_kinds=["MANUSCRIPT_UNIT"],
        )
        == []
    )
    assert (
        service.lexical_search(
            state["book_id"],
            "copper compass",
            chapter_id=state["chapter_2"],
            object_kinds=["MANUSCRIPT_UNIT"],
        )[0].object_id
        == state["unit_2"]
    )


def test_semantic_paraphrase_and_hybrid_are_deterministic(tmp_path: Path) -> None:
    state = ready_memory_book(tmp_path)
    mapping = {
        state["text_1"]: [1.0, 0.0, 0.0],
        state["text_2"]: [0.0, 1.0, 0.0],
        "find the beacon that restores remembered context": [0.99, 0.01, 0.0],
    }
    service = memory_service(tmp_path, mapping)
    status = service.rebuild(state["book_id"], provider="fake", model="memory-test")
    assert status.status == "SEMANTIC_READY"
    assert status.embedding_count == status.document_count

    semantic = service.semantic_search(
        state["book_id"],
        "find the beacon that restores remembered context",
        object_kinds=["MANUSCRIPT_UNIT"],
        provider="fake",
        model="memory-test",
    )
    assert semantic[0].object_id == state["unit_1"]
    assert semantic[0].semantic_score is not None
    assert semantic[0].semantic_score > semantic[1].semantic_score

    first = service.hybrid_search(
        state["book_id"],
        "blue lighthouse retrieval mechanism",
        object_kinds=["MANUSCRIPT_UNIT"],
        provider="fake",
        model="memory-test",
    )
    second = service.hybrid_search(
        state["book_id"],
        "blue lighthouse retrieval mechanism",
        object_kinds=["MANUSCRIPT_UNIT"],
        provider="fake",
        model="memory-test",
    )
    assert [item.memory_id for item in first] == [item.memory_id for item in second]
    assert first[0].object_id == state["unit_1"]
    assert first[0].fused_rank == 1


def test_manuscript_revision_change_invalidates_semantics_and_isolates_history(
    tmp_path: Path,
) -> None:
    state = ready_memory_book(tmp_path)
    service = memory_service(
        tmp_path,
        {
            state["text_1"]: [1.0, 0.0, 0.0],
            state["text_2"]: [0.0, 1.0, 0.0],
            "new memory phrase": [1.0, 0.0, 0.0],
        },
    )
    service.rebuild(state["book_id"], provider="fake", model="memory-test")

    engine = create_database(tmp_path / "projects" / state["book_id"] / "project.sqlite")
    with engine.connect() as connection:
        entity_id = cast(
            str,
            connection.execute(
                text("SELECT authority_entity_id FROM manuscript_units WHERE unit_id=:unit_id"),
                {"unit_id": state["unit_1"]},
            ).scalar_one(),
        )
    authority = AuthorityService(engine)
    new_revision = authority.create_revision(
        entity_id=entity_id,
        payload={
            "chapter_id": state["chapter_1"],
            "section_objective": "Revised memory section",
            "text": "new memory phrase replaces the obsolete passage",
            "notes": [],
        },
        schema_name="manuscript.unit.section.v0.1",
        schema_version="1",
        actor="owner",
        origin="HUMAN_WRITTEN",
        parent_revision_ids=(state["revision_1"],),
    )
    revision = authority.get_revision(new_revision)
    new_hash = cast(str, revision["content_hash"])
    with engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE authority_heads SET revision_id=:revision_id,revision_hash=:revision_hash,"
                "updated_at=:updated_at WHERE entity_id=:entity_id"
            ),
            {
                "revision_id": new_revision,
                "revision_hash": new_hash,
                "updated_at": utc_now(),
                "entity_id": entity_id,
            },
        )

    status = service.synchronize(state["book_id"])
    assert status.status == "LEXICAL_READY"
    with pytest.raises(MemoryGateError, match="rebuild required"):
        service.semantic_search(
            state["book_id"], "new memory phrase", provider="fake", model="memory-test"
        )

    assert (
        service.lexical_search(
            state["book_id"], "blue lighthouse", object_kinds=["MANUSCRIPT_UNIT"]
        )
        == []
    )
    current = service.lexical_search(
        state["book_id"], "new memory phrase", object_kinds=["MANUSCRIPT_UNIT"]
    )
    assert current[0].revision_id == new_revision
    assert current[0].currentness == "CURRENT"

    history = service.lexical_search(
        state["book_id"],
        "blue lighthouse",
        scope="HISTORY",
        object_kinds=["MANUSCRIPT_UNIT"],
    )
    assert history[0].revision_id == state["revision_1"]
    assert history[0].currentness == "HISTORY"


def test_contract_and_claim_changes_create_new_current_memory_identity(tmp_path: Path) -> None:
    state = ready_memory_book(tmp_path)
    service = memory_service(tmp_path)
    service.synchronize(state["book_id"])
    engine = create_database(tmp_path / "projects" / state["book_id"] / "project.sqlite")
    with engine.connect() as connection:
        before_contract = connection.execute(
            text(
                "SELECT revision_id FROM memory_documents WHERE book_id=:book_id "
                "AND object_kind='BOOK_CONTRACT' AND currentness='CURRENT'"
            ),
            {"book_id": state["book_id"]},
        ).scalar_one()
        before_claim = connection.execute(
            text(
                "SELECT content_hash FROM memory_documents WHERE book_id=:book_id "
                "AND object_kind='CLAIM' AND object_id=:claim_id AND currentness='CURRENT'"
            ),
            {"book_id": state["book_id"], "claim_id": state["claim_id"]},
        ).scalar_one()

    projects = ProjectService(tmp_path)
    projects.save_book_contract(state["book_id"], book_contract("v2"))
    project = projects.approve_book_contract(state["book_id"])
    assert project.book_contract is not None
    assert project.book_contract.authority_revision_id != before_contract

    research = ResearchService(tmp_path, ResearchGateway({}))
    claim = research.get_claim(state["book_id"], state["claim_id"])
    research.update_claim(
        state["book_id"],
        state["claim_id"],
        ClaimUpdateRequest(
            manuscript_revision_id=claim.manuscript_revision_id,
            manuscript_revision_hash=claim.manuscript_revision_hash,
            normalized_text="Hybrid memory reduces repeated context loss across the whole book.",
            claim_type="EMPIRICAL",
            materiality="HIGH",
            required_evidence_level="TRACEABLE_SOURCE",
        ),
    )

    service.synchronize(state["book_id"])
    with engine.connect() as connection:
        current_contract = connection.execute(
            text(
                "SELECT revision_id FROM memory_documents WHERE book_id=:book_id "
                "AND object_kind='BOOK_CONTRACT' AND currentness='CURRENT'"
            ),
            {"book_id": state["book_id"]},
        ).scalar_one()
        current_claim = connection.execute(
            text(
                "SELECT content_hash FROM memory_documents WHERE book_id=:book_id "
                "AND object_kind='CLAIM' AND object_id=:claim_id AND currentness='CURRENT'"
            ),
            {"book_id": state["book_id"], "claim_id": state["claim_id"]},
        ).scalar_one()
        history_contracts = connection.execute(
            text(
                "SELECT COUNT(*) FROM memory_documents WHERE book_id=:book_id "
                "AND object_kind='BOOK_CONTRACT' AND currentness='HISTORY'"
            ),
            {"book_id": state["book_id"]},
        ).scalar_one()
        history_claims = connection.execute(
            text(
                "SELECT COUNT(*) FROM memory_documents WHERE book_id=:book_id "
                "AND object_kind='CLAIM' AND object_id=:claim_id AND currentness='HISTORY'"
            ),
            {"book_id": state["book_id"], "claim_id": state["claim_id"]},
        ).scalar_one()
    assert current_contract != before_contract
    assert current_claim != before_claim
    assert history_contracts >= 1
    assert history_claims >= 1


def test_rebuild_is_idempotent_and_config_change_requires_rebuild(tmp_path: Path) -> None:
    state = ready_memory_book(tmp_path)
    service = memory_service(tmp_path)
    first = service.rebuild(state["book_id"], provider="fake", model="model-a")
    engine = create_database(tmp_path / "projects" / state["book_id"] / "project.sqlite")
    with engine.connect() as connection:
        first_ids = tuple(
            connection.execute(
                text(
                    "SELECT memory_id FROM memory_documents WHERE book_id=:book_id "
                    "AND currentness='CURRENT' ORDER BY memory_id"
                ),
                {"book_id": state["book_id"]},
            ).scalars()
        )
    second = service.rebuild(state["book_id"], provider="fake", model="model-a")
    with engine.connect() as connection:
        second_ids = tuple(
            connection.execute(
                text(
                    "SELECT memory_id FROM memory_documents WHERE book_id=:book_id "
                    "AND currentness='CURRENT' ORDER BY memory_id"
                ),
                {"book_id": state["book_id"]},
            ).scalars()
        )
    assert first_ids == second_ids
    assert first.document_count == second.document_count
    assert first.config_hash == second.config_hash

    with pytest.raises(MemoryGateError, match="requires rebuild"):
        service.semantic_search(state["book_id"], "context", provider="fake", model="model-b")


def test_failed_embedding_rebuild_does_not_mutate_authority(tmp_path: Path) -> None:
    state = ready_memory_book(tmp_path)
    engine = create_database(tmp_path / "projects" / state["book_id"] / "project.sqlite")
    with engine.connect() as connection:
        entity_id = cast(
            str,
            connection.execute(
                text("SELECT authority_entity_id FROM manuscript_units WHERE unit_id=:unit_id"),
                {"unit_id": state["unit_1"]},
            ).scalar_one(),
        )
    authority = AuthorityService(engine)
    before = authority.get_head(entity_id)

    failing = BookMemoryService(
        tmp_path,
        EmbeddingGateway({"fake": DeterministicFakeEmbeddingAdapter(fail=True, dimension=3)}),
    )
    with pytest.raises(Exception, match="embedding failure"):
        failing.rebuild(state["book_id"], provider="fake", model="broken")
    assert AuthorityService(engine).get_head(entity_id) == before
    assert failing.status(state["book_id"], synchronize=False).status == "FAILED"


def test_2000_document_exact_semantic_history_query_is_under_two_seconds(tmp_path: Path) -> None:
    projects = ProjectService(tmp_path)
    project = projects.create_project(
        NewBookRequest(working_title="Memory Benchmark", primary_subtype="Strategy")
    )
    projects.save_book_contract(project.book_id, book_contract())
    projects.approve_book_contract(project.book_id)

    query_text = "benchmark semantic query"
    adapter = DeterministicFakeEmbeddingAdapter(mapping={query_text: [1.0, 0.0, 0.0]}, dimension=3)
    service = BookMemoryService(tmp_path, EmbeddingGateway({"fake": adapter}))
    ready = service.rebuild(project.book_id, provider="fake", model="benchmark")
    assert ready.status == "SEMANTIC_READY"
    assert ready.config_hash

    engine = create_database(tmp_path / "projects" / project.book_id / "project.sqlite")
    now = utc_now()
    with engine.begin() as connection:
        for index in range(2000):
            memory_id = new_ulid()
            vector = np.asarray(
                [1.0, 0.0, 0.0] if index == 777 else [0.0, 1.0, float(index % 7) / 7.0],
                dtype=np.float32,
            )
            connection.execute(
                text(
                    "INSERT INTO memory_documents(memory_id,book_id,object_kind,object_id,chapter_id,"
                    "revision_id,revision_hash,content_hash,text,source_status,currentness,created_at,"
                    "indexed_at) VALUES (:memory_id,:book_id,'CLAIM',:object_id,NULL,:revision_id,"
                    ":revision_hash,:content_hash,:text,'UNREVIEWED','HISTORY',:created_at,:indexed_at)"
                ),
                {
                    "memory_id": memory_id,
                    "book_id": project.book_id,
                    "object_id": f"H{index:025d}"[-26:],
                    "revision_id": f"R{index:025d}"[-26:],
                    "revision_hash": f"{index:064x}"[-64:],
                    "content_hash": f"{index + 1:064x}"[-64:],
                    "text": f"synthetic history memory document {index}",
                    "created_at": now,
                    "indexed_at": now,
                },
            )
            connection.execute(
                text(
                    "INSERT INTO memory_embeddings(embedding_id,memory_id,provider,model,model_version,"
                    "config_hash,dimension,vector_blob,created_at) VALUES (:embedding_id,:memory_id,"
                    "'fake','benchmark','fake-v1',:config_hash,3,:vector_blob,:created_at)"
                ),
                {
                    "embedding_id": new_ulid(),
                    "memory_id": memory_id,
                    "config_hash": ready.config_hash,
                    "vector_blob": vector.tobytes(order="C"),
                    "created_at": now,
                },
            )

    started = time.perf_counter()
    results = service.semantic_search(
        project.book_id,
        query_text,
        scope="HISTORY",
        provider="fake",
        model="benchmark",
        limit=5,
    )
    elapsed = time.perf_counter() - started
    assert elapsed < 2.0
    assert results[0].text == "synthetic history memory document 777"
    assert results[0].semantic_score == pytest.approx(1.0)
