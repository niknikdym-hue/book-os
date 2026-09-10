from pathlib import Path


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one match, got {count}: {old!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


orchestrator = Path("services/local-core/src/book_os_core/quality_orchestrator.py")
replace_once(
    orchestrator,
    "                    actor_kind=\"AI\",\n                    run_id=run.run_id,\n",
    "                    actor_kind=\"AI\",\n                    run_id=None,\n",
)

test = Path("services/local-core/tests/test_task020_orchestrator.py")
replace_once(
    test,
    "    assert finding.run_id == result.run.run_id\n",
    "    assert finding.run_id is None\n    assert finding.evidence[\"quality_loop_run_id\"] == result.run.run_id\n",
)
