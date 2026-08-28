from pathlib import Path
p = Path('services/local-core/src/book_os_core/provider_lane.py')
s = p.read_text()
old = 'from typing import Any, Literal, cast\n'
new = 'from collections.abc import Callable\nfrom typing import Any, Literal, cast\n'
if old not in s:
    raise SystemExit('typing import not found')
p.write_text(s.replace(old, new, 1))
