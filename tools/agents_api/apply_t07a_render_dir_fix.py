#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]).resolve()
PATH = ROOT / "services/local-core/src/book_os_core/auto_book_exports.py"
text = PATH.read_text(encoding="utf-8")
old = '''    def _render_visual(self, visual: MasterVisual, output_dir: Path) -> Path:\n        output = output_dir / f"{visual.object_id}.png"\n'''
new = '''    def _render_visual(self, visual: MasterVisual, output_dir: Path) -> Path:\n        output_dir.mkdir(parents=True, exist_ok=True)\n        output = output_dir / f"{visual.object_id}.png"\n'''
if text.count(old) != 1:
    raise SystemExit("expected exactly one _render_visual output anchor")
PATH.write_text(text.replace(old, new, 1), encoding="utf-8")
print("T07 visual render directory ownership applied")
