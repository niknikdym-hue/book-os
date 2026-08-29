from pathlib import Path

bookbench = Path("services/local-core/src/book_os_core/bookbench.py")
text = bookbench.read_text()
old = '''        parsed = BookBenchJudgeOutput.model_validate(response.output)\n        drafts = [\n'''
new = '''        parsed = BookBenchJudgeOutput.model_validate(response.output)\n        raw_cost = response.usage.get("cost_usd")\n        cost_usd = (\n            float(raw_cost)\n            if isinstance(raw_cost, (int, float)) and not isinstance(raw_cost, bool)\n            else None\n        )\n        drafts = [\n'''
if old not in text:
    raise SystemExit("BookBench judge cost insertion target not found")
text = text.replace(old, new, 1)
old_sql = '"UPDATE evaluation_runs SET provider=:p,model=:m,config_id=:c,prompt_id=:pi,prompt_version=:pv,prompt_hash=:ph,independence_state=:i,usage_json=:u,cost_usd=0 WHERE evaluation_id=:e"'
new_sql = '"UPDATE evaluation_runs SET provider=:p,model=:m,config_id=:c,prompt_id=:pi,prompt_version=:pv,prompt_hash=:ph,independence_state=:i,usage_json=:u,cost_usd=:cost WHERE evaluation_id=:e"'
if old_sql not in text:
    raise SystemExit("BookBench judge cost SQL target not found")
text = text.replace(old_sql, new_sql, 1)
old_dict = '''                        "u": _canonical_json(response.usage),\n                        "e": eid,\n'''
new_dict = '''                        "u": _canonical_json(response.usage),\n                        "cost": cost_usd,\n                        "e": eid,\n'''
if old_dict not in text:
    raise SystemExit("BookBench judge cost params target not found")
bookbench.write_text(text.replace(old_dict, new_dict, 1))

test = Path("services/local-core/tests/test_bookbench.py")
test_text = test.read_text()
old_assert = '''    assert run.independence_state == "SAME_CONFIG" and run.output["release_grade"] is False\n'''
new_assert = '''    assert run.independence_state == "SAME_CONFIG" and run.output["release_grade"] is False\n    assert run.cost_usd is None\n'''
if old_assert not in test_text:
    raise SystemExit("BookBench cost regression assertion target not found")
test.write_text(test_text.replace(old_assert, new_assert, 1))
