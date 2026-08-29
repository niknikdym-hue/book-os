from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file = Path(path)
    text = file.read_text()
    if old not in text:
        raise SystemExit(f"target not found in {path}: {old[:80]!r}")
    file.write_text(text.replace(old, new, 1))


replace_once(
    "services/local-core/src/book_os_core/stage_b.py",
    '''class StageBCandidate:\n    provider: str\n    model: str\n    config_id: str\n    region: str\n    roles: tuple[str, ...]\n    require_embeddings: bool = False\n''',
    '''class StageBCandidate:\n    provider: str\n    model: str\n    config_id: str\n    region: str\n    roles: tuple[str, ...]\n    require_embeddings: bool = False\n    execution_model: str | None = None\n    embedding_execution_model: str | None = None\n''',
)

replace_once(
    "services/local-core/src/book_os_core/stage_b.py",
    '''class StageBPlan:\n    candidate: StageBCandidate\n    budget: StageBBudget\n    matrix_hash: str\n    matrix_version: str\n    credential_state: CredentialState\n    tls_ready: bool\n    estimated_cost: float | None\n    blockers: tuple[str, ...]\n\n    def canonical_payload(self) -> dict[str, object]:\n''',
    '''class StageBPlan:\n    candidate: StageBCandidate\n    budget: StageBBudget\n    matrix_hash: str\n    matrix_version: str\n    credential_state: CredentialState\n    tls_ready: bool\n    estimated_cost: float | None\n    exact_execution_identity_required: bool\n    blockers: tuple[str, ...]\n\n    @property\n    def generation_execution_model(self) -> str:\n        return self.candidate.execution_model or self.candidate.model\n\n    @property\n    def embedding_execution_model(self) -> str | None:\n        return self.candidate.embedding_execution_model\n\n    def canonical_payload(self) -> dict[str, object]:\n''',
)

replace_once(
    "services/local-core/src/book_os_core/stage_b.py",
    '''            "model": self.candidate.model,\n            "config_id": self.candidate.config_id,\n            "region": self.candidate.region,\n            "roles": list(self.candidate.roles),\n            "require_embeddings": self.candidate.require_embeddings,\n''',
    '''            "model": self.candidate.model,\n            "execution_model": self.generation_execution_model,\n            "embedding_execution_model": self.embedding_execution_model,\n            "config_id": self.candidate.config_id,\n            "region": self.candidate.region,\n            "roles": list(self.candidate.roles),\n            "require_embeddings": self.candidate.require_embeddings,\n            "exact_execution_identity_required": self.exact_execution_identity_required,\n''',
)

replace_once(
    "services/local-core/src/book_os_core/stage_b.py",
    '''        estimated_cost: float | None = None,\n        tls_ready: bool = True,\n    ) -> StageBPlan:\n''',
    '''        estimated_cost: float | None = None,\n        tls_ready: bool = True,\n        require_exact_execution_identity: bool = False,\n    ) -> StageBPlan:\n''',
)

replace_once(
    "services/local-core/src/book_os_core/stage_b.py",
    '''        if candidate.provider == "gigachat" and not tls_ready:\n            blockers.append("TLS_TRUST_NOT_READY")\n        if candidate.provider not in self._SECRET_NAMES:\n            blockers.append("PROVIDER_NOT_SUPPORTED_FOR_RU_STAGE_B")\n\n        return StageBPlan(\n''',
    '''        if candidate.provider == "gigachat" and not tls_ready:\n            blockers.append("TLS_TRUST_NOT_READY")\n        if candidate.provider not in self._SECRET_NAMES:\n            blockers.append("PROVIDER_NOT_SUPPORTED_FOR_RU_STAGE_B")\n        if require_exact_execution_identity and candidate.provider == "yandex":\n            if not candidate.execution_model or not candidate.execution_model.startswith("gpt://"):\n                blockers.append("EXECUTION_MODEL_REQUIRED")\n        if require_exact_execution_identity and candidate.require_embeddings:\n            embedding_model = candidate.embedding_execution_model\n            if not embedding_model:\n                blockers.append("EMBEDDING_EXECUTION_MODEL_REQUIRED")\n            elif candidate.provider == "yandex" and not embedding_model.startswith("emb://"):\n                blockers.append("EMBEDDING_EXECUTION_MODEL_REQUIRED")\n\n        return StageBPlan(\n''',
)

replace_once(
    "services/local-core/src/book_os_core/stage_b.py",
    '''            tls_ready=tls_ready,\n            estimated_cost=estimated_cost,\n            blockers=tuple(dict.fromkeys(blockers)),\n''',
    '''            tls_ready=tls_ready,\n            estimated_cost=estimated_cost,\n            exact_execution_identity_required=require_exact_execution_identity,\n            blockers=tuple(dict.fromkeys(blockers)),\n''',
)

replace_once(
    "services/local-core/src/book_os_core/stage_b.py",
    '''            estimated_cost=plan.estimated_cost,\n            tls_ready=plan.tls_ready,\n        )\n''',
    '''            estimated_cost=plan.estimated_cost,\n            tls_ready=plan.tls_ready,\n            require_exact_execution_identity=plan.exact_execution_identity_required,\n        )\n''',
)

replace_once(
    "services/local-core/src/book_os_core/stage_b.py",
    '''    if plan.blockers:\n        raise StageBGateError(f"Stage B preflight blocked: {','.join(plan.blockers)}")\n    ledger = StageBBudgetLedger(plan.budget)\n''',
    '''    if plan.blockers:\n        raise StageBGateError(f"Stage B preflight blocked: {','.join(plan.blockers)}")\n    if transport is None and plan.candidate.provider == "yandex":\n        if not plan.candidate.execution_model or not plan.candidate.execution_model.startswith("gpt://"):\n            raise StageBGateError("EXECUTION_MODEL_REQUIRED")\n    if transport is None and plan.candidate.require_embeddings:\n        embedding_model = plan.candidate.embedding_execution_model\n        if not embedding_model:\n            raise StageBGateError("EMBEDDING_EXECUTION_MODEL_REQUIRED")\n        if plan.candidate.provider == "yandex" and not embedding_model.startswith("emb://"):\n            raise StageBGateError("EMBEDDING_EXECUTION_MODEL_REQUIRED")\n    ledger = StageBBudgetLedger(plan.budget)\n''',
)

replace_once(
    "services/local-core/src/book_os_core/stage_b_execution.py",
    '''                    "model": plan.candidate.model,\n''',
    '''                    "model": plan.generation_execution_model,\n''',
)
replace_once(
    "services/local-core/src/book_os_core/stage_b_execution.py",
    '''            usage.setdefault("configured_model", plan.candidate.model)\n''',
    '''            usage.setdefault("policy_model", plan.candidate.model)\n            usage.setdefault("configured_model", plan.generation_execution_model)\n''',
)
replace_once(
    "services/local-core/src/book_os_core/stage_b_execution.py",
    '''                    configured_model=plan.candidate.model,\n''',
    '''                    configured_model=plan.generation_execution_model,\n''',
)

replace_once(
    "services/local-core/src/book_os_core/stage_b_bookbench.py",
    '''                    model=plan.candidate.model,\n''',
    '''                    model=plan.generation_execution_model,\n''',
)
replace_once(
    "services/local-core/src/book_os_core/stage_b_bookbench.py",
    '''                model=plan.candidate.model,\n            )\n''',
    '''                model=plan.embedding_execution_model or plan.generation_execution_model,\n            )\n''',
)
replace_once(
    "services/local-core/src/book_os_core/stage_b_bookbench.py",
    '''            configured_model=plan.candidate.model,\n''',
    '''            configured_model=plan.generation_execution_model,\n''',
)

replace_once(
    "services/local-core/src/book_os_core/stage_b_editor.py",
    '''            model=plan.candidate.model,\n''',
    '''            model=plan.generation_execution_model,\n''',
)
replace_once(
    "services/local-core/src/book_os_core/stage_b_editor.py",
    '''                model=plan.candidate.model,\n''',
    '''                model=plan.generation_execution_model,\n''',
)
replace_once(
    "services/local-core/src/book_os_core/stage_b_editor.py",
    '''            configured_model=plan.candidate.model,\n''',
    '''            configured_model=plan.generation_execution_model,\n''',
)

replace_once(
    "services/local-core/src/book_os_core/stage_b_judge.py",
    '''        "model": plan.candidate.model,\n''',
    '''        "model": plan.generation_execution_model,\n''',
)
replace_once(
    "services/local-core/src/book_os_core/stage_b_judge.py",
    '''                model=plan.candidate.model,\n''',
    '''                model=plan.generation_execution_model,\n''',
)

replace_once(
    "services/local-core/src/book_os_core/stage_b_cli.py",
    '''    parser.add_argument("--model", required=True)\n    parser.add_argument("--config-id", required=True)\n''',
    '''    parser.add_argument("--model", required=True, help="Policy/capability model identity")\n    parser.add_argument("--execution-model", help="Exact generation model identity; Yandex requires gpt:// URI")\n    parser.add_argument("--embedding-execution-model", help="Exact embedding model identity when embeddings are requested")\n    parser.add_argument("--config-id", required=True)\n''',
)
replace_once(
    "services/local-core/src/book_os_core/stage_b_cli.py",
    '''        roles=roles,\n        require_embeddings=embeddings,\n    )\n''',
    '''        roles=roles,\n        require_embeddings=embeddings,\n        execution_model=args.execution_model,\n        embedding_execution_model=args.embedding_execution_model,\n    )\n''',
)
replace_once(
    "services/local-core/src/book_os_core/stage_b_cli.py",
    '''        estimated_cost=args.estimated_cost,\n    )\n''',
    '''        estimated_cost=args.estimated_cost,\n        require_exact_execution_identity=True,\n    )\n''',
)

replace_once(
    "services/local-core/tests/test_stage_b_cli.py",
    '''        "--model",\n        "yandexgpt",\n        "--config-id",\n''',
    '''        "--model",\n        "yandexgpt",\n        "--execution-model",\n        "gpt://synthetic-folder/yandexgpt/latest",\n        "--config-id",\n''',
)
replace_once(
    "services/local-core/tests/test_stage_b_cli.py",
    '''    assert payload["credential_state"] == "AVAILABLE"\n    assert len(payload["plan_hash"]) == 64\n''',
    '''    assert payload["credential_state"] == "AVAILABLE"\n    assert payload["model"] == "yandexgpt"\n    assert payload["execution_model"] == "gpt://synthetic-folder/yandexgpt/latest"\n    assert len(payload["plan_hash"]) == 64\n''',
)

# Add a strict-preflight regression to the CLI tests.
cli_test = Path("services/local-core/tests/test_stage_b_cli.py")
cli_text = cli_test.read_text()
cli_text += '''\n\ndef test_cli_yandex_preflight_blocks_without_exact_execution_model(tmp_path, capsys) -> None:\n    args = _base_args(tmp_path)\n    marker = args.index("--execution-model")\n    del args[marker : marker + 2]\n    status = run(\n        ["preflight", *args, "--roles", "WRITER"],\n        secrets=DictSecretStore({"yandex_ai_studio_api_key": "secret"}),\n    )\n    assert status == 3\n    payload = json.loads(capsys.readouterr().out)\n    assert "EXECUTION_MODEL_REQUIRED" in payload["blockers"]\n'''
cli_test.write_text(cli_text)
