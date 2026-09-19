#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
path = root / "services/local-core/tests/test_auto_book_quality.py"
text = path.read_text(encoding="utf-8")
old = '''    assert stale.status == "REWORK"\n    assert any(item.code == "STALE_CLAIM_EVIDENCE" for item in stale.findings)\n'''
new = '''    assert stale.status == "REWORK"\n    assert any(item.code == "UNREGISTERED_MATERIAL_CLAIM" for item in stale.findings)\n'''
if text.count(old) != 1:
    raise SystemExit("expected the pre-T02 semantic-revision assertion exactly once")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("T02 semantic-revision regression aligned to exact claim identity")
