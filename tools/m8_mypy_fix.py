from pathlib import Path
p = Path('services/local-core/src/book_os_core/provider_lane.py')
s = p.read_text()
s = s.replace('from dataclasses import dataclass, replace\n', 'from collections.abc import Callable\nfrom dataclasses import dataclass, replace\n')
s = s.replace('        clock: Any = time.time,\n', '        clock: Callable[[], float] = time.time,\n')
p.write_text(s)
