from pathlib import Path
import subprocess


def replace_once(path: str, old: str, new: str) -> None:
    file = Path(path)
    text = file.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"pattern missing in {path}: {old[:100]!r}")
    file.write_text(text.replace(old, new, 1), encoding="utf-8")


panel = "apps/desktop/src/ResearchPanel.tsx"
replace_once(
    panel,
    'import { useEffect, useMemo, useState } from "react";',
    'import { useCallback, useEffect, useMemo, useState } from "react";',
)
replace_once(
    panel,
    '''  async function reloadClaims(draft: DraftRunView) {\n    if (!chapter || !draft.unit_id) return;\n    const items = await api<ClaimView[]>(\n      "GET",\n      `/api/projects/${project.book_id}/claims?chapter_id=${encodeURIComponent(chapter.chapter_id)}&unit_id=${encodeURIComponent(draft.unit_id)}`,\n    );\n    setClaims(items);\n    setSelectedClaimId((current) =>\n      current && items.some((item) => item.claim_id === current)\n        ? current\n        : (items[0]?.claim_id ?? null),\n    );\n  }\n''',
    '''  const reloadClaims = useCallback(\n    async (draft: DraftRunView) => {\n      if (!chapter || !draft.unit_id) return;\n      const items = await api<ClaimView[]>(\n        "GET",\n        `/api/projects/${project.book_id}/claims?chapter_id=${encodeURIComponent(chapter.chapter_id)}&unit_id=${encodeURIComponent(draft.unit_id)}`,\n      );\n      setClaims(items);\n      setSelectedClaimId((current) =>\n        current && items.some((item) => item.claim_id === current)\n          ? current\n          : (items[0]?.claim_id ?? null),\n      );\n    },\n    [api, chapter, project.book_id],\n  );\n''',
)
replace_once(
    panel,
    '  }, [api, chapter, project.book_id]);',
    '  }, [api, chapter, project.book_id, reloadClaims]);',
)

for path in (
    "services/local-core/tests/test_authority.py",
    "services/local-core/tests/test_backup_compat.py",
    "services/local-core/tests/test_projects.py",
):
    file = Path(path)
    text = file.read_text(encoding="utf-8")
    text = text.replace('"0004"', '"0005"')
    file.write_text(text, encoding="utf-8")

subprocess.run(
    ["ruff", "format", "src/book_os_core/research.py", "src/book_os_core/research_adapters.py", "tests/test_research.py"],
    cwd="services/local-core",
    check=True,
)
