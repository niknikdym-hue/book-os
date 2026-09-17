from __future__ import annotations

import pytest

from book_os_core.authority_types import HumanApprovalRequired, InvalidAuthorityOperation
from book_os_core.mystery_authority import (
    AuthorityRequirement,
    MysteryAuthorityGraph,
    MysteryAuthorityKind,
    MysteryAuthorityRevision,
    create_authority_revision,
    evaluate_writing_admission,
    revise_authority,
    transition_authority_status,
)


def _draft_revision(
    entity_id: str, kind: MysteryAuthorityKind, marker: str
) -> MysteryAuthorityRevision:
    return create_authority_revision(
        entity_id=entity_id,
        kind=kind,
        payload={"marker": marker},
    )


def _approve(revision: MysteryAuthorityRevision) -> MysteryAuthorityRevision:
    revision = transition_authority_status(revision, target_status="PROPOSED", actor_kind="AI")
    revision = transition_authority_status(revision, target_status="REVIEWED", actor_kind="AI")
    return transition_authority_status(revision, target_status="APPROVED", actor_kind="HUMAN")


def _accepted_revision(
    entity_id: str, kind: MysteryAuthorityKind, marker: str
) -> MysteryAuthorityRevision:
    return _approve(_draft_revision(entity_id, kind, marker))


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
    proposed = transition_authority_status(revision, target_status="PROPOSED", actor_kind="AI")
    reviewed = transition_authority_status(proposed, target_status="REVIEWED", actor_kind="AI")

    with pytest.raises(HumanApprovalRequired):
        transition_authority_status(reviewed, target_status="APPROVED", actor_kind="AI")

    approved = transition_authority_status(reviewed, target_status="APPROVED", actor_kind="HUMAN")
    with pytest.raises(HumanApprovalRequired):
        transition_authority_status(approved, target_status="LOCKED", actor_kind="SYSTEM")


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


def test_dependency_binding_uses_both_exact_revision_ids() -> None:
    graph = MysteryAuthorityGraph()
    story = _draft_revision("story", "STORY_DEFINITION", "v1")
    case = _draft_revision("case", "CASE_SOLUTION", "v1")
    graph.register_head(story)
    graph.register_head(case)

    binding = graph.bind_dependency(
        dependent_entity_id="case",
        upstream_entity_id="story",
        reason="case architecture consumes story definition",
    )

    assert binding.dependent_revision_id == case.revision_id
    assert binding.upstream_revision_id == story.revision_id
    assert graph.is_fresh("case")


def test_upstream_revision_change_makes_dependents_stale_transitively() -> None:
    graph = MysteryAuthorityGraph()
    story = _draft_revision("story", "STORY_DEFINITION", "v1")
    case = _draft_revision("case", "CASE_SOLUTION", "v1")
    scene = _draft_revision("scene", "SCENE_CONTRACT", "v1")
    for revision in (story, case, scene):
        graph.register_head(revision)
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
    story = _approve(story)
    case = _approve(case)
    scene = _approve(scene)
    for revision in (story, case, scene):
        graph.register_head(revision)

    revised_story = revise_authority(story, {"marker": "v2"})
    graph.register_head(revised_story)

    assert graph.stale_entities() == frozenset({"case", "scene"})
    assert not graph.is_fresh("case")
    assert not graph.is_fresh("scene")


def test_accepted_revision_cannot_gain_or_change_dependencies() -> None:
    graph = MysteryAuthorityGraph()
    story = _accepted_revision("story", "STORY_DEFINITION", "v1")
    case_without_binding = _accepted_revision("case-a", "CASE_SOLUTION", "v1")
    graph.register_head(story)
    graph.register_head(case_without_binding)

    with pytest.raises(InvalidAuthorityOperation):
        graph.bind_dependency(
            dependent_entity_id="case-a",
            upstream_entity_id="story",
            reason="late dependency addition",
        )

    case = _draft_revision("case-b", "CASE_SOLUTION", "v1")
    graph.register_head(case)
    graph.bind_dependency(
        dependent_entity_id="case-b",
        upstream_entity_id="story",
        reason="case consumes story",
    )
    case = _approve(case)
    graph.register_head(case)

    new_story = revise_authority(story, {"marker": "v2"})
    new_story = _approve(new_story)
    graph.register_head(new_story)
    assert "case-b" in graph.stale_entities()

    with pytest.raises(InvalidAuthorityOperation):
        graph.bind_dependency(
            dependent_entity_id="case-b",
            upstream_entity_id="story",
            reason="illegal silent rebind",
        )


def test_new_dependent_revision_inherits_staleness_until_reviewed_and_rebound() -> None:
    graph = MysteryAuthorityGraph()
    story = _draft_revision("story", "STORY_DEFINITION", "v1")
    case = _draft_revision("case", "CASE_SOLUTION", "v1")
    graph.register_head(story)
    graph.register_head(case)
    graph.bind_dependency(
        dependent_entity_id="case",
        upstream_entity_id="story",
        reason="case consumes story",
    )
    story = _approve(story)
    case = _approve(case)
    graph.register_head(story)
    graph.register_head(case)

    new_story = revise_authority(story, {"marker": "v2"})
    new_story = _approve(new_story)
    graph.register_head(new_story)
    case_v2 = revise_authority(case, {"marker": "v2 reviewed against new story"})
    graph.register_head(case_v2)

    inherited = graph.dependencies_for("case")
    assert len(inherited) == 1
    assert inherited[0].dependent_revision_id == case_v2.revision_id
    assert inherited[0].upstream_revision_id == story.revision_id
    assert "case" in graph.stale_entities()

    rebound = graph.bind_dependency(
        dependent_entity_id="case",
        upstream_entity_id="story",
        reason="new case revision reviewed against revised story",
    )
    assert rebound.dependent_revision_id == case_v2.revision_id
    assert rebound.upstream_revision_id == new_story.revision_id
    assert "case" not in graph.stale_entities()


def test_dependency_cycles_are_rejected() -> None:
    graph = MysteryAuthorityGraph()
    story = _draft_revision("story", "STORY_DEFINITION", "v1")
    case = _draft_revision("case", "CASE_SOLUTION", "v1")
    graph.register_head(story)
    graph.register_head(case)
    graph.bind_dependency(
        dependent_entity_id="case",
        upstream_entity_id="story",
        reason="case consumes story",
    )

    with pytest.raises(InvalidAuthorityOperation, match="dependency cycle rejected"):
        graph.bind_dependency(
            dependent_entity_id="story",
            upstream_entity_id="case",
            reason="invalid reverse dependency",
        )


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

    new_case = revise_authority(case, {"marker": "v2"})
    new_case = _approve(new_case)
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
    story = _draft_revision("story", "STORY_DEFINITION", "v1")
    case = _draft_revision("case", "CASE_SOLUTION", "v1")
    narrative = _draft_revision("narrative", "NARRATIVE_CONTRACT", "v1")
    scene = _draft_revision("scene", "SCENE_CONTRACT", "v1")
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
    for revision in (story, case, narrative, scene):
        graph.register_head(_approve(revision))

    result = evaluate_writing_admission(
        graph,
        tuple(
            AuthorityRequirement(entity_id) for entity_id in ("story", "case", "narrative", "scene")
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
