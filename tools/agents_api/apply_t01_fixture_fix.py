#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
path = root / "services/local-core/tests/test_auto_book_finalizer.py"
text = path.read_text(encoding="utf-8")
old = '''        if request.task_type == "BOOKBENCH_JUDGE":\n            return ModelAdapterResult(\n                provider_run_id="finalizer-happy-path-critic",\n                output={\n                    "verdict": "PASS",\n                    "findings": [],\n                    "confidence": 0.93,\n                    "rationale": "Finalizer happy-path fixture has no unresolved findings.",\n                },\n                usage={"input_tokens": 40, "output_tokens": 20},\n            )\n'''
new = '''        if request.task_type == "BOOKBENCH_JUDGE":\n            self.last_request = request\n            return ModelAdapterResult(\n                provider_run_id="finalizer-happy-path-critic",\n                output={\n                    "verdict": "PASS",\n                    "findings": [],\n                    "confidence": 0.75,\n                    "rationale": "Finalizer happy-path fixture has no unresolved findings.",\n                },\n                usage={"input_tokens": 40, "output_tokens": 20},\n            )\n'''
if text.count(old) != 1:
    raise SystemExit("expected exactly one finalizer happy-path fixture block")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("T01 finalizer fixture corrected")
