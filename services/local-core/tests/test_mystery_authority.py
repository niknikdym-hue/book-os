from __future__ import annotations

import pytest

from book_os_core.authority_types import HumanApprovalRequired, InvalidAuthorityOperation
from book_os_core.mystery_authority import (
    AuthorityRequirement,
    MysteryAuthorityGraph,
    create_authority_revision,
    evaluate_writing_admission,
    revise_authority,
    transition_authority_status,
)


def _accepted_revision(entity_id: str, kind: str, marker: str):
    revision = create_authority_revision(
        entity_id=entity_id,
        kind=kind,  # type: ignore[arg-type]
        payload={"marker": marker},
    )
    revision = transition_authority_status(
        revision, target_status="PROPOSED", actor_kind="AI"
    )
    revision = transition_authority_status(
        revision, target_status="REVIEWED", actor_kind="AI"
    )
    return transition_authority_status(
        revision, target_status="APPROVED", actor_kind="HUMAN"
    )


def test_new_content_cannot_skip_human_approval() -> None:
    with pytest.raises(HumanApprovalRequired):
        create_authority_revision(
            entity_id="case-1",
            kind="CASE_SOLUTION",
            payload={"culprit": "A"},
            status="APPROVED",
        )


def test_ai_cannot_approve_or_lock_authority() -> None:
    revision = create_authority_revision(
        entity_id="case-1",
        kind="CASE_SOLUTION",
        payload={"culprit": "A"},
    )
    proposed = transition_authority_status(
        revision, target_status="PROPOSED", actor_kind="AI"
    )
    reviewed = transition_authority_status(
        proposed, target_status="REVIEWED", actor_kind="AI"
    )

    with pytest.raises(HumanApprovalRequired):
        transition_authority_status(
            reviewed, target_status="APPROVED", actor_kind="AI"
        )

    approved = transition_authority_status(
        reviewed, target_status="APPROVED", actor_kind="HUMAN"
    )
    with pytest.raises(HumanApprovalRequired):
        transition_authority_status(
            approved, target_status="LOCKED", actor_kind="SYSTEM"
        )


def test_revision_preserves_old_accepted_content_and_hash() -> None:
    approved = _accepted_revision("case-1", "CASE_SOLUTION", "first")
    replacement = revise_authority(approved, {"marker": "second"})

    assert approved.status == "APPROVED"
    assert approved.content_json == '{"marker":"first"}'
    assert replacement.status == "DRAFT"
    assert replacement.content_json == '{"marker":"second"}'
    assert replacement.revision_id != approved.revision_id
    assert replacement.revision_hash != approved.revision_hash
    assert replacement.supersedes_revision_id == approved.revision_id


def test_dependency_binding_uses_exact_upstream_revision() -> None:
    graph = MysteryAuthorityGraph()
    story = _accepted_revision("story", "STORY_DEFINITION", "v1")
    case = _accepted_revision("case", "CASE_SOLUTION", "v1")
    graph.register_head(story)
    graph.register_head(case)

    binding = graph.bind_dependency(
        dependent_entity_id="case",
        upstream_entity_id="story",
        reason="case architecture consumes story definition",
    )

    assert binding.upstream_revision_id == story.revision_id
    assert graph.is_fresh("case")


def test_upstream_revision_change_makes_dependents_stale_transitively() -> None:
    graph = MysteryAuthorityGraph()
    story = _accepted_revision("story", "STORY_DEFINITION", "v1")
    case = _accepted_revision("case", "CASE_SOLUTION", "v1")
    scene = _accepted_revision("scene", "SCENE_CONTRACT", "v1")
    graph.register_head(story)
    graph.register_head(case)
    graph.register_head(scene)
    graph.bind_dependency(
        dependent_entity_id="case",
        upstream_entity_id="story",
        reason="case consumes story",
    )
    graph.bind_dependency(
        dependent_entity_id="scene",
        upstream_entity_id="case",
        reason="scene consumes case truth",
    )

    revised_story = revise_authority(story, {"marker": "v2"})
    graph.register_head(revised_story)

    assert graph.stale_entities() == frozenset({"case", "scene"})
    assert not graph.is_fresh("case")
    assert not graph.is_fresh("scene")


def test_rebinding_to_new_upstream_revision_clears_direct_staleness() -> None:
    graph = MysteryAuthorityGraph()
    story = _accepted_revision("story", "STORY_DEFINITION", "v1")
    case = _accepted_revision("case", "CASE_SOLUTION", "v1")
    graph.register_head(story)
    graph.register_head(case)
    graph.bind_dependency(
        dependent_entity_id="case",
        upstream_entity_id="story",
        reason="case consumes story",
    )

    new_story = _accepted_revision("story", "STORY_DEFINITION", "v2")
    graph.register_head(new_story)
    assert "case" in graph.stale_entities()

    graph.bind_dependency(
        dependent_entity_id="case",
        upstream_entity_id="story",
        reason="case reviewed against revised story",
    )
    assert "case" not in graph.stale_entities()


def test_writing_admission_fails_closed_for_missing_unaccepted_or_stale_authority() -> None:
    graph = MysteryAuthorityGraph()
    story = _accepted_revision("story", "STORY_DEFINITION", "v1")
    case = _accepted_revision("case", "CASE_SOLUTION", "v1")
    scene = create_authority_revision(
        entity_id="scene",
        kind="SCENE_CONTRACT",
        payload={"marker": "draft"},
    )
    graph.register_head(story)
    graph.register_head(case)
    graph.register_head(scene)
    graph.bind_dependency(
        dependent_entity_id="scene",
        upstream_entity_id="case",
        reason="scene consumes case",
    )

    result = evaluate_writing_admission(
        graph,
        (
            AuthorityRequirement("story"),
            AuthorityRequirement("case"),
            AuthorityRequirement("scene"),
            AuthorityRequirement("narrative"),
        ),
    )

    assert not result.allowed
    assert "UNACCEPTED_AUTHORITY:scene:DRAFT" in result.blocking_reasons
    assert "MISSING_AUTHORITY:narrative" in result.blocking_reasons

    new_case = _accepted_revision("case", "CASE_SOLUTION", "v2")
    graph.register_head(new_case)
    stale_result = evaluate_writing_admission(
        graph,
        (
            AuthorityRequirement("story"),
            AuthorityRequirement("case"),
            AuthorityRequirement("scene", frozenset({"DRAFT", "APPROVED", "LOCKED"})),
        ),
    )
    assert not stale_result.allowed
    assert "STALE_AUTHORITY:scene" in stale_result.blocking_reasons


def test_writing_admission_passes_only_with_fresh_accepted_authority() -> None:
    graph = MysteryAuthorityGraph()
    story = _accepted_revision("story", "STORY_DEFINITION", "v1")
    case = _accepted_revision("case", "CASE_SOLUTION", "v1")
    narrative = _accepted_revision("narrative", "NARRATIVE_CONTRACT", "v1")
    scene = _accepted_revision("scene", "SCENE_CONTRACT", "v1")
    for revision in (story, case, narrative, scene):
        graph.register_head(revision)
    graph.bind_dependency(
        dependent_entity_id="case",
        upstream_entity_id="story",
        reason="case consumes story",
    )
    graph.bind_dependency(
        dependent_entity_id="scene",
        upstream_entity_id="case",
        reason="scene consumes case",
    )
    graph.bind_dependency(
        dependent_entity_id="scene",
        upstream_entity_id="narrative",
        reason="scene consumes narrative contract",
    )

    result = evaluate_writing_admission(
        graph,
        tuple(
            AuthorityRequirement(entity_id)
            for entity_id in ("story", "case", "narrative", "scene")
        ),
    )

    assert result.allowed
    assert result.blocking_reasons == ()
    assert len(result.authority_revision_refs) == 4


def test_entity_kind_cannot_change_under_same_identity() -> None:
    graph = MysteryAuthorityGraph()
    graph.register_head(_accepted_revision("entity", "CASE_SOLUTION", "v1"))

    with pytest.raises(InvalidAuthorityOperation):
        graph.register_head(_accepted_revision("entity", "STORY_DEFINITION", "v2"))
