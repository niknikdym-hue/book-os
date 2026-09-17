from __future__ import annotations

from dataclasses import replace

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


def _approve_in_graph(
    graph: MysteryAuthorityGraph, revision: MysteryAuthorityRevision
) -> MysteryAuthorityRevision:
    revision = transition_authority_status(revision, target_status="PROPOSED", actor_kind="AI")
    graph.register_head(revision)
    revision = transition_authority_status(revision, target_status="REVIEWED", actor_kind="AI")
    graph.register_head(revision)
    revision = transition_authority_status(revision, target_status="APPROVED", actor_kind="HUMAN")
    graph.register_head(revision)
    return revision


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

    with pytest.raises(InvalidAuthorityOperation):
        create_authority_revision(
            entity_id="case-1",
            kind="CASE_SOLUTION",
            payload={"culprit": "A"},
            status="PROPOSED",
        )


def test_ai_cannot_approve_or_lock_authority() -> None:
    revision = _draft_revision("case-1", "CASE_SOLUTION", "v1")
    proposed = transition_authority_status(revision, target_status="PROPOSED", actor_kind="AI")
    reviewed = transition_authority_status(proposed, target_status="REVIEWED", actor_kind="AI")

    with pytest.raises(HumanApprovalRequired):
        transition_authority_status(reviewed, target_status="APPROVED", actor_kind="AI")

    approved = transition_authority_status(reviewed, target_status="APPROVED", actor_kind="HUMAN")
    with pytest.raises(HumanApprovalRequired):
        transition_authority_status(approved, target_status="LOCKED", actor_kind="SYSTEM")


def test_graph_rejects_forged_accepted_status_without_human_provenance() -> None:
    graph = MysteryAuthorityGraph()
    draft = _draft_revision("case", "CASE_SOLUTION", "v1")
    forged = replace(draft, status="APPROVED", last_transition_actor="AI")

    with pytest.raises(HumanApprovalRequired):
        graph.register_head(forged)


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


def test_same_revision_id_cannot_change_content_or_lineage() -> None:
    graph = MysteryAuthorityGraph()
    revision = _draft_revision("case", "CASE_SOLUTION", "v1")
    graph.register_head(revision)

    tampered = replace(revision, content_json='{"marker":"tampered"}')
    with pytest.raises(InvalidAuthorityOperation, match="revision identity is immutable"):
        graph.register_head(tampered)


def test_detached_revision_cannot_replace_current_working_head() -> None:
    graph = MysteryAuthorityGraph()
    current = _accepted_revision("case", "CASE_SOLUTION", "v1")
    graph.register_head(current)
    detached = _draft_revision("case", "CASE_SOLUTION", "detached")

    with pytest.raises(InvalidAuthorityOperation, match="directly supersede"):
        graph.register_head(detached)


def test_new_superseding_revision_must_enter_graph_as_draft() -> None:
    graph = MysteryAuthorityGraph()
    current = _accepted_revision("case", "CASE_SOLUTION", "v1")
    graph.register_head(current)
    replacement = _approve(revise_authority(current, {"marker": "v2"}))

    with pytest.raises(InvalidAuthorityOperation, match="must enter the graph as DRAFT"):
        graph.register_head(replacement)


def test_draft_revision_does_not_displace_effective_authority() -> None:
    graph = MysteryAuthorityGraph()
    story_v1 = _accepted_revision("story", "STORY_DEFINITION", "v1")
    graph.register_head(story_v1)

    story_v2 = revise_authority(story_v1, {"marker": "v2 draft"})
    graph.register_head(story_v2)

    assert graph.latest("story") == story_v2
    assert graph.effective("story") == story_v1
    assert graph.head("story") == story_v1
    assert graph.stale_entities() == frozenset()

    admission = evaluate_writing_admission(graph, (AuthorityRequirement("story"),))
    assert admission.allowed
    assert admission.authority_revision_refs == (story_v1.revision_ref,)


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
    assert graph.dependencies_for("case") == (binding,)


def test_unapproved_upstream_draft_does_not_stale_effective_dependents() -> None:
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
    story = _approve_in_graph(graph, story)
    case = _approve_in_graph(graph, case)
    _approve_in_graph(graph, scene)

    story_v2 = revise_authority(story, {"marker": "v2 draft"})
    graph.register_head(story_v2)

    assert graph.effective("story") == story
    assert graph.stale_entities() == frozenset()
    assert graph.is_fresh("case")
    assert graph.is_fresh("scene")


def test_accepted_upstream_revision_makes_dependents_stale_transitively() -> None:
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
    story = _approve_in_graph(graph, story)
    _approve_in_graph(graph, case)
    _approve_in_graph(graph, scene)

    story_v2 = revise_authority(story, {"marker": "v2"})
    graph.register_head(story_v2)
    story_v2 = _approve_in_graph(graph, story_v2)

    assert graph.effective("story") == story_v2
    assert graph.stale_entities() == frozenset({"case", "scene"})
    assert not graph.is_fresh("case")
    assert not graph.is_fresh("scene")


def test_default_binding_prefers_effective_over_parallel_working_draft() -> None:
    graph = MysteryAuthorityGraph()
    story_v1 = _accepted_revision("story", "STORY_DEFINITION", "v1")
    graph.register_head(story_v1)
    story_v2 = revise_authority(story_v1, {"marker": "v2 draft"})
    graph.register_head(story_v2)
    case = _draft_revision("case", "CASE_SOLUTION", "v1")
    graph.register_head(case)

    default_binding = graph.bind_dependency(
        dependent_entity_id="case",
        upstream_entity_id="story",
        reason="consume governing story",
    )
    assert default_binding.upstream_revision_id == story_v1.revision_id

    working_binding = graph.bind_dependency(
        dependent_entity_id="case",
        upstream_entity_id="story",
        reason="explicitly co-develop against story draft",
        use_working_upstream=True,
    )
    assert working_binding.upstream_revision_id == story_v2.revision_id


def test_dependent_cannot_be_accepted_against_unaccepted_upstream_revision() -> None:
    graph = MysteryAuthorityGraph()
    story_v1 = _accepted_revision("story", "STORY_DEFINITION", "v1")
    graph.register_head(story_v1)
    story_v2 = revise_authority(story_v1, {"marker": "v2 draft"})
    graph.register_head(story_v2)
    case = _draft_revision("case", "CASE_SOLUTION", "v1")
    graph.register_head(case)
    graph.bind_dependency(
        dependent_entity_id="case",
        upstream_entity_id="story",
        reason="case intentionally built against story draft",
        use_working_upstream=True,
    )

    case = transition_authority_status(case, target_status="PROPOSED", actor_kind="AI")
    graph.register_head(case)
    case = transition_authority_status(case, target_status="REVIEWED", actor_kind="AI")
    graph.register_head(case)
    case = transition_authority_status(case, target_status="APPROVED", actor_kind="HUMAN")
    with pytest.raises(InvalidAuthorityOperation, match="dependency on story@"):
        graph.register_head(case)


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
    case = _approve_in_graph(graph, case)

    new_story = revise_authority(story, {"marker": "v2"})
    graph.register_head(new_story)
    _approve_in_graph(graph, new_story)
    assert "case-b" in graph.stale_entities()

    with pytest.raises(InvalidAuthorityOperation):
        graph.bind_dependency(
            dependent_entity_id="case-b",
            upstream_entity_id="story",
            reason="illegal silent rebind",
        )


def test_new_dependent_revision_inherits_staleness_until_rebound() -> None:
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
    story = _approve_in_graph(graph, story)
    case = _approve_in_graph(graph, case)

    story_v2 = revise_authority(story, {"marker": "v2"})
    graph.register_head(story_v2)
    story_v2 = _approve_in_graph(graph, story_v2)
    assert "case" in graph.stale_entities()

    case_v2 = revise_authority(case, {"marker": "v2 reviewed against new story"})
    graph.register_head(case_v2)
    inherited = graph.dependencies_for("case")
    assert len(inherited) == 1
    assert inherited[0].dependent_revision_id == case_v2.revision_id
    assert inherited[0].upstream_revision_id == story.revision_id

    rebound = graph.bind_dependency(
        dependent_entity_id="case",
        upstream_entity_id="story",
        reason="new case revision reviewed against revised story",
    )
    assert rebound.dependent_revision_id == case_v2.revision_id
    assert rebound.upstream_revision_id == story_v2.revision_id

    case_v2 = _approve_in_graph(graph, case_v2)
    assert graph.effective("case") == case_v2
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
    scene = _draft_revision("scene", "SCENE_CONTRACT", "draft")
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
    graph.register_head(new_case)
    _approve_in_graph(graph, new_case)
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
    _approve_in_graph(graph, story)
    _approve_in_graph(graph, case)
    _approve_in_graph(graph, narrative)
    _approve_in_graph(graph, scene)

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
