from __future__ import annotations

import json
from pathlib import Path

import httpx

from book_os_core.bookbench import BookBenchService
from book_os_core.db import create_database
from book_os_core.drafting import DraftSectionRequest, DraftingService
from book_os_core.editorial import EditorialService
from book_os_core.model_gateway import DeterministicFakeAdapter, ModelGateway
from book_os_core.provider_lane import ProviderLaneService
from book_os_core.secrets import DictSecretStore
from book_os_core.stage_b import StageBBudget, StageBCandidate, StageBPreflightService
from book_os_core.stage_b_bookbench import prepare_synthetic_project
from book_os_core.stage_b_editor import execute_editor_fixture
from book_os_core.stage_b_judge import execute_independent_judges


def _source_project(tmp_path: Path) -> str:
    project = prepare_synthetic_project(tmp_path)
    drafting = DraftingService(
        tmp_path,
        ModelGateway({"fake": DeterministicFakeAdapter()}),
    )
    drafting.generate_section_draft(
        project.book_id,
        project.chapter_ids[0],
        DraftSectionRequest(
            section_objective="Synthetic source manuscript for M8 EDITOR evaluation",
            provider="fake",
            model="fake-writer-v1",
        ),
    )
    return project.book_id


def test_editor_fixture_preserves_human_authority_and_supports_independent_bookbench_judge(
    tmp_path: Path, monkeypatch
) -> None:
    source_book_id = _source_project(tmp_path)
    before = BookBenchService(tmp_path).create_snapshot(source_book_id, scope="BOOK")
    before_units = [t for t in before.targets if t.target_kind == "MANUSCRIPT_UNIT"]
    assert len(before_units) == 1

    lane = ProviderLaneService(create_database(tmp_path / "editor-provider-lane.sqlite"))
    editor_secret = "M8-EDITOR-YANDEX-SECRET"
    editor_secrets = DictSecretStore({"yandex_ai_studio_api_key": editor_secret})
    editor_preflight = StageBPreflightService(lane, editor_secrets)
    editor_plan = editor_preflight.build_plan(
        StageBCandidate(
            "yandex",
            "yandexgpt",
            "latest-discovery",
            "RU",
            ("EDITOR",),
        ),
        StageBBudget(1, 0, 1),
    )
    editor_calls = 0

    def editor_handler(request: httpx.Request) -> httpx.Response:
        nonlocal editor_calls
        editor_calls += 1
        assert request.url.path == "/foundationModels/v1/completion"
        assert request.headers["Authorization"] == f"Api-Key {editor_secret}"
        return httpx.Response(
            200,
            json={
                "id": "m8-editor-yandex-run-1",
                "result": {
                    "alternatives": [
                        {
                            "message": {
                                "text": json.dumps(
                                    {
                                        "text": (
                                            "DIAGNOSIS: В исходном синтетическом фрагменте нужно яснее "
                                            "отделить наблюдение от интерпретации; внешние факты не нужны.\n"
                                            "PROPOSAL: Сначала зафиксируйте наблюдаемый сигнал. Затем назовите "
                                            "интерпретацию гипотезой и завершите одним измеримым следующим решением."
                                        ),
                                        "notes": ["synthetic editor fixture"],
                                    },
                                    ensure_ascii=False,
                                )
                            }
                        }
                    ],
                    "usage": {"inputTextTokens": "42", "completionTokens": "35"},
                    "modelVersion": "yandexgpt-editor-exact-v1",
                },
            },
        )

    monkeypatch.setenv("BOOK_OS_ALLOW_LIVE_PROVIDER", "1")
    editor = execute_editor_fixture(
        data_dir=tmp_path,
        source_book_id=source_book_id,
        preflight=editor_preflight,
        plan=editor_plan,
        authorized_plan_hash=editor_plan.plan_hash,
        lane=lane,
        secrets=editor_secrets,
        transport=httpx.MockTransport(editor_handler),
    )

    assert editor_calls == 1
    assert editor.returned_model_version == "yandexgpt-editor-exact-v1"
    assert editor.provider_run_id == "m8-editor-yandex-run-1"
    assert len(editor.artifact_hash) == 64
    assert len(editor.deterministic_evaluation_ids) == 7
    assert editor.budget_usage["generation_requests_used"] == 1
    assert editor.budget_usage["total_requests_used"] == 1

    editorial = EditorialService(tmp_path)
    finding = editorial.get_finding(source_book_id, editor.finding_id)
    proposal = editorial.get_proposal(source_book_id, editor.finding_id, editor.proposal_id)
    assert finding.status == "OPEN"
    assert finding.actor_kind == "AI"
    assert proposal.status == "OPEN"
    assert not proposal.stale

    after = BookBenchService(tmp_path).create_snapshot(source_book_id, scope="BOOK")
    after_units = [t for t in after.targets if t.target_kind == "MANUSCRIPT_UNIT"]
    assert len(after_units) == 1
    assert after_units[0].revision_id == before_units[0].revision_id
    assert after_units[0].revision_hash == before_units[0].revision_hash
    assert lane.promotion_evidence() == []

    judge_secret = "M8-EDITOR-GIGACHAT-JUDGE-SECRET"
    judge_secrets = DictSecretStore({"gigachat_authorization_key": judge_secret})
    judge_preflight = StageBPreflightService(lane, judge_secrets)
    judge_plan = judge_preflight.build_plan(
        StageBCandidate(
            "gigachat",
            "GigaChat-2-Pro",
            "b2b",
            "RU",
            ("EVALUATOR",),
        ),
        StageBBudget(
            max_generation_requests=2,
            max_embedding_requests=0,
            max_auth_requests=1,
            max_total_requests=3,
        ),
    )
    judge_calls: list[str] = []

    def judge_handler(request: httpx.Request) -> httpx.Response:
        judge_calls.append(request.url.path)
        if request.url.path.endswith("/api/v2/oauth"):
            assert request.headers["Authorization"] == f"Basic {judge_secret}"
            return httpx.Response(200, json={"access_token": "judge-access", "expires_in": 1800})
        assert request.url.path == "/v1/chat/completions"
        return httpx.Response(
            200,
            json={
                "id": f"m8-editor-judge-{len(judge_calls)}",
                "model": "GigaChat-2-Pro:judge-exact-v1",
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "verdict": "PASS",
                                    "findings": [],
                                    "confidence": 0.9,
                                    "rationale": "Synthetic editor artifact satisfies the bounded dimension.",
                                }
                            )
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"total_tokens": 50},
            },
        )

    judged = execute_independent_judges(
        data_dir=tmp_path,
        book_id=editor.evaluation_book_id,
        snapshot_id=editor.evaluation_snapshot_id,
        subject_identity={
            "provider": editor.provider,
            "model": editor.configured_model,
            "config_id": editor.config_id,
        },
        dimensions=("EDITOR_DIAGNOSIS_QUALITY", "EDITOR_AUTHORITY_PRESERVATION"),
        preflight=judge_preflight,
        plan=judge_plan,
        authorized_plan_hash=judge_plan.plan_hash,
        lane=lane,
        secrets=judge_secrets,
        transport=httpx.MockTransport(judge_handler),
    )
    assert judged.independence_state == "INDEPENDENT"
    assert len(judged.evaluation_ids) == 2
    assert len(judged.provider_probe_ids) == 2
    assert judged.budget_usage["auth_requests_used"] == 1
    assert judged.budget_usage["generation_requests_used"] == 2
    assert judged.budget_usage["total_requests_used"] == 3
    assert judge_calls == ["/api/v2/oauth", "/v1/chat/completions", "/v1/chat/completions"]

    finding_after_judge = editorial.get_finding(source_book_id, editor.finding_id)
    proposal_after_judge = editorial.get_proposal(source_book_id, editor.finding_id, editor.proposal_id)
    assert finding_after_judge.status == "OPEN"
    assert proposal_after_judge.status == "OPEN"
    assert lane.promotion_evidence() == []

    public_dump = json.dumps(
        {"editor": editor.public_dict(), "judge": judged.public_dict()},
        sort_keys=True,
    )
    assert editor_secret not in public_dump
    assert judge_secret not in public_dump
