#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
path = root / "services/local-core/src/book_os_core/audio_script.py"
text = path.read_text(encoding="utf-8")
old = "        script_hash = audio_content_hash(content)\n        recording = content.clean_recording_text()\n        locations = [\n"
new = "        script_hash = audio_content_hash(content)\n        locations = [\n"
if text.count(old) != 1:
    raise SystemExit(f"T08 obsolete recording anchor is not exact: {text.count(old)}")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("T08 obsolete recording variable removed")
