from __future__ import annotations

import json
from pathlib import Path

import pytest

from book_os_core.db import create_database
from book_os_core.provider_lane import ProviderLaneService
from book_os_core.secrets import DictSecretStore
from book_os_core.stage_b import (
    StageBBudget,
    StageBCandidate,
    StageBGateError,
    StageBPreflightService,
    build_provider_runtime,
)
from book_os_core.stage_b_cli import run


def _lane(tmp_path: Path) -> ProviderLaneService:
    return ProviderLaneService(create_database(tmp_path / "execution-identity.sqlite"))


def test_real_yandex_runtime_refuses_policy_alias_as_execution_model(tmp_path: Path) -> None:
    lane = _lane(tmp_path)
    secrets = DictSecretStore({"yandex_ai_studio_api_key": "secret"})
    plan = StageBPreflightService(lane, secrets).build_plan(
        StageBCandidate("yandex", "yandexgpt", "latest-discovery", "RU", ("WRITER",)),
        StageBBudget(1, 0, 1),
    )
    assert plan.blockers == ()
    with pytest.raises(StageBGateError, match="EXECUTION_MODEL_REQUIRED"):
        build_provider_runtime(plan, secrets)


def test_exact_yandex_execution_model_is_plan_bound(tmp_path: Path) -> None:
    lane = _lane(tmp_path)
    secrets = DictSecretStore({"yandex_ai_studio_api_key": "secret"})
    preflight = StageBPreflightService(lane, secrets)
    first = preflight.build_plan(
        StageBCandidate(
            "yandex",
            "yandexgpt",
            "latest-discovery",
            "RU",
            ("WRITER",),
            execution_model="gpt://synthetic-folder/yandexgpt/latest",
        ),
        StageBBudget(1, 0, 1),
        require_exact_execution_identity=True,
    )
    second = preflight.build_plan(
        StageBCandidate(
            "yandex",
            "yandexgpt",
            "latest-discovery",
            "RU",
            ("WRITER",),
            execution_model="gpt://synthetic-folder/yandexgpt/other-version",
        ),
        StageBBudget(1, 0, 1),
        require_exact_execution_identity=True,
    )
    assert first.blockers == ()
    assert first.generation_execution_model == "gpt://synthetic-folder/yandexgpt/latest"
    assert first.plan_hash != second.plan_hash


def test_cli_semantic_preflight_requires_exact_embedding_model(tmp_path: Path, capsys) -> None:
    status = run(
        [
            "preflight",
            "--data-dir",
            str(tmp_path),
            "--provider",
            "yandex",
            "--model",
            "yandexgpt",
            "--execution-model",
            "gpt://synthetic-folder/yandexgpt/latest",
            "--config-id",
            "latest-discovery",
            "--max-generation",
            "1",
            "--max-embedding",
            "1",
            "--max-total",
            "2",
            "--roles",
            "WRITER",
            "--require-embeddings",
        ],
        secrets=DictSecretStore({"yandex_ai_studio_api_key": "secret"}),
    )
    assert status == 3
    payload = json.loads(capsys.readouterr().out)
    assert "EMBEDDING_EXECUTION_MODEL_REQUIRED" in payload["blockers"]
