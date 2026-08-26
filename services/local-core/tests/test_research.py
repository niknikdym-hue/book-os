from __future__ import annotations

from pathlib import Path
from typing import cast

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import text

from book_os_core.app import create_app
from book_os_core.db import create_database
from book_os_core.drafting import DraftSectionRequest, DraftingService
from book_os_core.model_gateway import DeterministicFakeAdapter, ModelGateway
from book_os_core.projects import (
    BookArchitecturePayload,
    BookContractPayload,
    ChapterContractPayload,
    NewBookRequest,
    ProjectService,
)
from book_os_core.research import (
    ClaimCreateRequest,
    ClaimReviewRequest,
    ClaimUpdateRequest,
    EvidenceCreateRequest,
    ResearchGateError,
    ResearchSearchRequest,
    ResearchService,
    SourceAccessRequest,
    SourceImportRequest,
)
from book_os_core.research_adapters import ResearchCandidate, ResearchGateway


def book_contract() -> BookContractPayload:
    return BookContractPayload(
        reader="Business leaders",
        reader_problem="They need an evidence-aware operating model",
        central_promise="A traceable model",
        central_thesis="Evidence and authority reduce editorial error",
        unique_angle="Treat factual support as explicit state",
        reader_trajectory="From assertion to evidence-backed claim",
        explicit_exclusions=["No invented citations"],
        evidence_policy="Material factual claims require traceable evidence",
        voice_genre_constraints="Precise business nonfiction",
        readiness_criteria=["Material claims are inspectable"],
    )


def architecture() -> BookArchitecturePayload:
    return BookArchitecturePayload.model_validate(
        {
            "parts": [
                {
                    "title": "Part I",
                    "purpose": "Build the evidence mechanism",
                    "chapters": [
                        {
                            "chapter_id": None,
                            "title": "Evidence",
                            "purpose": "Explain claim verification",
                            "new_contribution": "A traceable evidence ledger",
                            "dependencies": [],
                            "transition": "Move to application",
                        }
                    ],
                }
            ],
            "intellectual_progression": "claim → source → evidence",
            "concept_allocation": "One evidence concept per chapter",
            "promise_thesis_coverage": "The chapter advances the thesis",
            "major_transitions": "Evidence precedes publication",
        }
    )


def chapter_contract() -> ChapterContractPayload:
    return ChapterContractPayload(
        chapter_purpose="Explain evidence discipline",
        new_contribution="Separate Source, Evidence and Claim",
        reader_prior_state="Reader treats citation as proof",
        reader_after_state="Reader can distinguish metadata from evidence",
        required_claims=["Evidence quality changes verification confidence"],
        required_or_permitted_research=["Scholarly metadata and inspected sources"],
        required_scenes_examples=["One source-inspection example"],
        reserved_elsewhere=["Book Memory belongs later"],
        opening_requirements="Open with a citation failure",
        ending_requirements="End with a traceable claim",
        transition_requirements="Hand off retrieval",
    )


def ready_draft(data_dir: Path) -> tuple[str, str, str, str, str]:
    projects = ProjectService(data_dir)
    project = projects.create_project(
        NewBookRequest(working_title="Research Test Book", primary_subtype="Strategy")
    )
    projects.save_book_contract(project.book_id, book_contract())
    projects.approve_book_contract(project.book_id)
    projects.save_architecture(project.book_id, architecture())
    project = projects.approve_architecture(project.book_id)
    chapter_id = project.chapters[0].chapter_id
    projects.save_chapter_contract(project.book_id, chapter_id, chapter_contract())
    projects.approve_chapter_contract(project.book_id, chapter_id)

    drafting = DraftingService(
        data_dir,
        ModelGateway({"fake": DeterministicFakeAdapter()}),
    )
    draft = drafting.generate_section_draft(
        project.book_id,
        chapter_id,
        DraftSectionRequest(
            section_objective="Explain why evidence quality matters",
            provider="fake",
            model="fake-writer",
        ),
    )
    assert draft.unit_id and draft.revision_id and draft.revision_hash
    return project.book_id, chapter_id, draft.unit_id, draft.revision_id, draft.revision_hash


def candidate(
    provider: str,
    external_id: str,
    *,
    doi: str | None,
    title: str = "Evidence Quality and Decision Making",
    url: str | None = None,
    abstract: str | None = None,
) -> ResearchCandidate:
    return ResearchCandidate(
        provider=provider,
        external_id=external_id,
        title=title,
        authors=["A. Researcher"],
        publication_year=2024,
        doi=doi,
        canonical_url=url
        or (f"https://doi.org/{doi}" if doi else f"https://example.org/{external_id}"),
        container_title="Evidence Journal",
        abstract=abstract,
        provider_url=f"https://provider.test/{external_id}",
        raw_identifiers={provider: external_id},
    )


class StaticAdapter:
    provider_name = "openalex"

    def search(self, query: str, *, limit: int = 5) -> list[ResearchCandidate]:
        assert query
        return [candidate("openalex", "W-STATIC", doi="10.9999/static.1")][:limit]


def make_service(data_dir: Path) -> ResearchService:
    return ResearchService(data_dir, ResearchGateway({"openalex": StaticAdapter()}))


def create_claim(
    service: ResearchService,
    book_id: str,
    chapter_id: str,
    unit_id: str,
    revision_id: str,
    revision_hash: str,
):
    return service.create_claim(
        book_id,
        ClaimCreateRequest(
            chapter_id=chapter_id,
            unit_id=unit_id,
            manuscript_revision_id=revision_id,
            manuscript_revision_hash=revision_hash,
            normalized_text="Evidence quality changes verification confidence.",
            claim_type="EMPIRICAL",
            materiality="HIGH",
            required_evidence_level="INSPECTED_SOURCE",
        ),
    )


def test_m4_schema_and_claim_attach_to_exact_current_draft(tmp_path: Path) -> None:
    book_id, chapter_id, unit_id, revision_id, revision_hash = ready_draft(tmp_path)
    service = make_service(tmp_path)
    claim = create_claim(service, book_id, chapter_id, unit_id, revision_id, revision_hash)
    assert claim.verification_state == "UNREVIEWED"

    engine = create_database(tmp_path / "projects" / book_id / "project.sqlite")
    with engine.connect() as connection:
        assert (
            connection.execute(
                text("SELECT version FROM schema_metadata ORDER BY version DESC LIMIT 1")
            ).scalar_one()
            == "0006"
        )
        history = connection.execute(
            text("SELECT new_state,actor_kind FROM claim_state_history WHERE claim_id=:claim_id"),
            {"claim_id": claim.claim_id},
        ).one()
    assert history == ("UNREVIEWED", "HUMAN")

    with pytest.raises(ResearchGateError, match="exact current"):
        service.create_claim(
            book_id,
            ClaimCreateRequest(
                chapter_id=chapter_id,
                unit_id=unit_id,
                manuscript_revision_id=revision_id,
                manuscript_revision_hash="0" * 64,
                normalized_text="Stale claim",
                claim_type="EMPIRICAL",
            ),
        )


def test_same_doi_deduplicates_across_providers_but_title_alone_does_not(tmp_path: Path) -> None:
    book_id, *_ = ready_draft(tmp_path)
    service = make_service(tmp_path)
    first = service.import_source(
        book_id,
        SourceImportRequest(candidate=candidate("openalex", "W1", doi="10.1111/SAME.1")),
    )
    second = service.import_source(
        book_id,
        SourceImportRequest(
            candidate=candidate("crossref", "10.1111/same.1", doi="10.1111/same.1")
        ),
    )
    assert first.source_id == second.source_id
    merged = service.get_source(book_id, first.source_id)
    assert "openalex" in merged.identifiers
    assert "crossref" in merged.identifiers

    title_a = service.import_source(
        book_id,
        SourceImportRequest(
            candidate=candidate(
                "openalex",
                "W-TITLE-A",
                doi=None,
                title="Same Title",
                url="https://example.org/a",
            )
        ),
    )
    title_b = service.import_source(
        book_id,
        SourceImportRequest(
            candidate=candidate(
                "crossref",
                "TITLE-B",
                doi=None,
                title="Same Title",
                url="https://example.org/b",
            )
        ),
    )
    assert title_a.source_id != title_b.source_id


def test_candidate_or_metadata_source_never_auto_supports_claim(tmp_path: Path) -> None:
    book_id, chapter_id, unit_id, revision_id, revision_hash = ready_draft(tmp_path)
    service = make_service(tmp_path)
    claim = create_claim(service, book_id, chapter_id, unit_id, revision_id, revision_hash)

    assert service.search(ResearchSearchRequest(query="evidence quality", providers=["openalex"]))
    assert service.get_claim(book_id, claim.claim_id).verification_state == "UNREVIEWED"

    source = service.import_source(
        book_id,
        SourceImportRequest(candidate=candidate("openalex", "W2", doi="10.2222/meta.1")),
    )
    assert source.access_status == "METADATA_ONLY"
    assert service.get_claim(book_id, claim.claim_id).verification_state == "UNREVIEWED"

    service.add_evidence(
        book_id,
        claim.claim_id,
        EvidenceCreateRequest(
            source_id=source.source_id,
            relationship="SUPPORTS",
            pointer="Provider metadata page",
            note="Metadata exists, but the source itself has not been inspected.",
        ),
    )
    assert service.get_claim(book_id, claim.claim_id).verification_state == "UNREVIEWED"


def test_explicit_source_inspection_supports_and_claim_edit_invalidates_old_evidence(
    tmp_path: Path,
) -> None:
    book_id, chapter_id, unit_id, revision_id, revision_hash = ready_draft(tmp_path)
    service = make_service(tmp_path)
    claim = create_claim(service, book_id, chapter_id, unit_id, revision_id, revision_hash)
    source = service.import_source(
        book_id,
        SourceImportRequest(candidate=candidate("crossref", "CR3", doi="10.3333/full.1")),
    )
    service.mark_source_access(
        book_id,
        source.source_id,
        SourceAccessRequest(
            access_status="FULL_SOURCE_INSPECTED",
            actor="OWNER",
            note="Inspected the cited section in the source and recorded the locator.",
        ),
    )
    service.add_evidence(
        book_id,
        claim.claim_id,
        EvidenceCreateRequest(
            source_id=source.source_id,
            relationship="SUPPORTS",
            pointer="Section 3, paragraph 2",
            note="Directly supports the bounded claim.",
            strength="STRONG",
        ),
    )
    assert service.get_claim(book_id, claim.claim_id).verification_state == "SUPPORTED"

    updated = service.update_claim(
        book_id,
        claim.claim_id,
        ClaimUpdateRequest(
            manuscript_revision_id=revision_id,
            manuscript_revision_hash=revision_hash,
            normalized_text="A materially changed claim requiring new evidence.",
            claim_type="CAUSAL",
            materiality="CRITICAL",
            required_evidence_level="INSPECTED_SOURCE",
        ),
    )
    assert updated.claim_id == claim.claim_id
    assert updated.verification_state == "UNREVIEWED"
    evidence = service.list_evidence(book_id, claim.claim_id)
    assert evidence[0].status == "SUPERSEDED"


def test_partial_support_requires_limitation_and_contradiction_is_visible(tmp_path: Path) -> None:
    book_id, chapter_id, unit_id, revision_id, revision_hash = ready_draft(tmp_path)
    service = make_service(tmp_path)
    claim = create_claim(service, book_id, chapter_id, unit_id, revision_id, revision_hash)
    source = service.import_source(
        book_id,
        SourceImportRequest(
            candidate=candidate(
                "semantic_scholar",
                "S2-4",
                doi="10.4444/partial.1",
                abstract="The abstract provides only partial support.",
            )
        ),
    )
    with pytest.raises(ValueError, match="explicit limitation"):
        EvidenceCreateRequest(
            source_id=source.source_id,
            relationship="PARTIALLY_SUPPORTS",
            pointer="Abstract",
            limitations="",
        )

    service.add_evidence(
        book_id,
        claim.claim_id,
        EvidenceCreateRequest(
            source_id=source.source_id,
            relationship="PARTIALLY_SUPPORTS",
            pointer="Abstract, sentence 2",
            limitations="Only the provider-supplied abstract was inspected; full text was unavailable.",
        ),
    )
    assert service.get_claim(book_id, claim.claim_id).verification_state == "PARTIALLY_SUPPORTED"

    contradiction = service.import_source(
        book_id,
        SourceImportRequest(candidate=candidate("openalex", "W5", doi="10.5555/contra.1")),
    )
    service.add_evidence(
        book_id,
        claim.claim_id,
        EvidenceCreateRequest(
            source_id=contradiction.source_id,
            relationship="CONTRADICTS",
            pointer="Provider abstract/metadata record",
            note="Contradictory evidence requires review.",
        ),
    )
    assert service.get_claim(book_id, claim.claim_id).verification_state == "DISPUTED"


def test_citation_gate_requires_stored_source_and_evidence(tmp_path: Path) -> None:
    book_id, chapter_id, unit_id, revision_id, revision_hash = ready_draft(tmp_path)
    service = make_service(tmp_path)
    claim = create_claim(service, book_id, chapter_id, unit_id, revision_id, revision_hash)
    unresolved = service.check_citation(book_id, claim.claim_id, "10.6666/fabricated.1")
    assert not unresolved.resolved
    assert "UNVERIFIED_CANDIDATE" in unresolved.reason

    source = service.import_source(
        book_id,
        SourceImportRequest(candidate=candidate("crossref", "CR6", doi="10.6666/real.1")),
    )
    no_evidence = service.check_citation(book_id, claim.claim_id, "https://doi.org/10.6666/REAL.1")
    assert not no_evidence.resolved
    assert no_evidence.source_id == source.source_id

    evidence = service.add_evidence(
        book_id,
        claim.claim_id,
        EvidenceCreateRequest(
            source_id=source.source_id,
            relationship="CONTEXT_ONLY",
            pointer="Bibliographic record and bounded locator",
        ),
    )
    resolved = service.check_citation(book_id, claim.claim_id, "10.6666/real.1")
    assert resolved.resolved
    assert resolved.evidence_id == evidence.evidence_id


def test_explicit_reviewer_decision_is_audited(tmp_path: Path) -> None:
    book_id, chapter_id, unit_id, revision_id, revision_hash = ready_draft(tmp_path)
    service = make_service(tmp_path)
    claim = create_claim(service, book_id, chapter_id, unit_id, revision_id, revision_hash)
    rejected = service.review_claim(
        book_id,
        claim.claim_id,
        ClaimReviewRequest(
            state="REJECTED",
            actor="OWNER",
            reason="The claim is outside the approved chapter contract and should not be published.",
        ),
    )
    assert rejected.verification_state == "REJECTED"
    engine = create_database(tmp_path / "projects" / book_id / "project.sqlite")
    with engine.connect() as connection:
        row = connection.execute(
            text(
                "SELECT new_state,actor,actor_kind,reason FROM claim_state_history "
                "WHERE claim_id=:claim_id ORDER BY created_at DESC LIMIT 1"
            ),
            {"claim_id": claim.claim_id},
        ).one()
    assert row[0:3] == ("REJECTED", "OWNER", "HUMAN")
    assert "outside" in cast(str, row[3])


def test_authenticated_api_runs_claim_search_source_evidence_path_without_live_http(
    tmp_path: Path,
) -> None:
    book_id, chapter_id, unit_id, revision_id, revision_hash = ready_draft(tmp_path)
    research_gateway = ResearchGateway({"openalex": StaticAdapter()})
    client = TestClient(
        create_app(
            "token",
            tmp_path,
            gateway=ModelGateway({"fake": DeterministicFakeAdapter()}),
            research_gateway=research_gateway,
        )
    )
    claim_payload = {
        "chapter_id": chapter_id,
        "unit_id": unit_id,
        "manuscript_revision_id": revision_id,
        "manuscript_revision_hash": revision_hash,
        "normalized_text": "Evidence quality changes verification confidence.",
        "claim_type": "EMPIRICAL",
        "materiality": "HIGH",
        "required_evidence_level": "INSPECTED_SOURCE",
    }
    assert client.post(f"/api/projects/{book_id}/claims", json=claim_payload).status_code == 401
    headers = {"Authorization": "Bearer token"}
    claim_response = client.post(
        f"/api/projects/{book_id}/claims", headers=headers, json=claim_payload
    )
    assert claim_response.status_code == 200
    claim_id = claim_response.json()["claim_id"]

    search = client.post(
        f"/api/projects/{book_id}/research/search",
        headers=headers,
        json={"query": "evidence quality", "providers": ["openalex"], "limit_per_provider": 5},
    )
    assert search.status_code == 200
    imported = client.post(
        f"/api/projects/{book_id}/sources/import",
        headers=headers,
        json={"candidate": search.json()[0], "primary_secondary": "SECONDARY"},
    )
    assert imported.status_code == 200
    source_id = imported.json()["source_id"]
    inspected = client.post(
        f"/api/projects/{book_id}/sources/{source_id}/access",
        headers=headers,
        json={
            "access_status": "FULL_SOURCE_INSPECTED",
            "actor": "OWNER",
            "note": "Inspected the referenced source section.",
        },
    )
    assert inspected.status_code == 200
    evidence = client.post(
        f"/api/projects/{book_id}/claims/{claim_id}/evidence",
        headers=headers,
        json={
            "source_id": source_id,
            "relationship": "SUPPORTS",
            "pointer": "Section 2",
            "note": "Direct support",
            "strength": "STRONG",
            "limitations": "",
            "actor": "OWNER",
        },
    )
    assert evidence.status_code == 200
    claims = client.get(f"/api/projects/{book_id}/claims", headers=headers)
    assert claims.status_code == 200
    assert claims.json()[0]["verification_state"] == "SUPPORTED"
