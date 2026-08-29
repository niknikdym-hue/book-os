from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
from sqlalchemy import text

from book_os_core.db import create_database
from book_os_core.provider_lane import ProviderLaneService
from book_os_core.secrets import DictSecretStore
from book_os_core.stage_b import StageBBudget, StageBCandidate, StageBPreflightService
from book_os_core.stage_b_bookbench import (
    STAGE_B_FIXTURE_VERSION,
    execute_writer_bookbench_fixture,
    fixture_hash,
    fixture_payload,
)


def test_fixture_identity_is_stable_and_contains_only_synthetic_data() -> None:
    first = fixture_hash()
    second = fixture_hash()
    assert first == second
    assert len(first) == 64
    payload = fixture_payload()
    assert payload["version"] == STAGE_B_FIXTURE_VERSION
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    assert "support tickets" in serialized
    assert "Elena" not in serialized
    assert "Дымова" not in serialized


def test_writer_fixture_uses_real_drafting_and_bookbench_with_mocked_provider(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lane = ProviderLaneService(create_database(tmp_path / "provider-lane.sqlite"))
    sentinel = "M8-BOOKBENCH-YANDEX-SECRET"
    secrets = DictSecretStore({"yandex_ai_studio_api_key": sentinel})
    preflight = StageBPreflightService(lane, secrets)
    plan = preflight.build_plan(
        StageBCandidate(
            "yandex",
            "yandexgpt",
            "latest-discovery",
            "RU",
            ("WRITER",),
        ),
        StageBBudget(
            max_generation_requests=2,
            max_embedding_requests=0,
            max_total_requests=2,
        ),
    )
    calls: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/foundationModels/v1/completion"
        assert request.headers["Authorization"] == f"Api-Key {sentinel}"
        body = json.loads(request.content)
        calls.append(body)
        objective = str(body["messages"][1]["text"])
        return httpx.Response(
            200,
            json={
                "id": f"stage-b-yandex-{len(calls)}",
                "result": {
                    "alternatives": [
                        {
                            "message": {
                                "text": json.dumps(
                                    {
                                        "text": (
                                            "Наблюдение отделено от интерпретации. "
                                            f"Синтетический пример: {objective} "
                                            "Команда фиксирует следующий измеримый шаг без внешних фактов."
                                        ),
                                        "notes": ["synthetic M8 fixture"],
                                    },
                                    ensure_ascii=False,
                                )
                            }
                        }
                    ],
                    "usage": {"inputTextTokens": "31", "completionTokens": "29"},
                    "modelVersion": "yandexgpt-stage-b-exact-v1",
                },
            },
        )

    monkeypatch.setenv("BOOK_OS_ALLOW_LIVE_PROVIDER", "1")
    evidence = execute_writer_bookbench_fixture(
        data_dir=tmp_path,
        preflight=preflight,
        plan=plan,
        authorized_plan_hash=plan.plan_hash,
        lane=lane,
        secrets=secrets,
        transport=httpx.MockTransport(handler),
    )

    assert evidence.fixture_version == STAGE_B_FIXTURE_VERSION
    assert evidence.fixture_hash == fixture_hash()
    assert len(evidence.snapshot_hash) == 64
    assert len(evidence.evaluation_ids) == 7
    assert evidence.semantic_evaluation_ids == ()
    assert evidence.semantic_config_hash is None
    assert len(evidence.provider_probe_ids) == 2
    assert evidence.budget_usage["generation_requests_used"] == 2
    assert evidence.budget_usage["total_requests_used"] == 2
    assert len(calls) == 2

    probes = lane.probe_evidence()
    assert len(probes) == 2
    assert all(row["probe_type"] == "LIVE" for row in probes)
    assert sentinel not in json.dumps(probes, sort_keys=True)

    project_engine = create_database(
        tmp_path / "projects" / evidence.book_id / "project.sqlite"
    )
    with project_engine.connect() as connection:
        manuscript_count = connection.execute(
            text("SELECT COUNT(*) FROM manuscript_units WHERE book_id=:book_id"),
            {"book_id": evidence.book_id},
        ).scalar_one()
        model_versions = connection.execute(
            text(
                "SELECT DISTINCT pr.model_version FROM provenance_records pr "
                "JOIN revisions r ON r.provenance_id=pr.provenance_id "
                "WHERE r.entity_type='manuscript.unit'"
            )
        ).scalars().all()
        approvals = connection.execute(text("SELECT COUNT(*) FROM approvals")).scalar_one()
        snapshots = connection.execute(
            text("SELECT COUNT(*) FROM evaluation_snapshots")
        ).scalar_one()
        runs = connection.execute(text("SELECT COUNT(*) FROM evaluation_runs")).scalar_one()
    assert manuscript_count == 2
    assert model_versions == ["yandexgpt-stage-b-exact-v1"]
    assert approvals == 4  # Book + architecture/chapter human fixture approvals only; drafts stay DRAFT.
    assert snapshots == 1
    assert runs == 7
    assert lane.promotion_evidence() == []
