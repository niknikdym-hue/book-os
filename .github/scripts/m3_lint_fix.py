from pathlib import Path

py = Path("services/local-core/src/book_os_core/drafting.py")
text = py.read_text()
text = text.replace("from collections.abc import Mapping\n", "", 1)
py.write_text(text)

panel = Path("apps/desktop/src/DraftingPanel.tsx")
text = panel.read_text()
text = text.replace(
    "  }, [chapter?.chapter_id, project.book_id]);\n",
    "  }, [chapter, project.book_id]);\n",
    1,
)
panel.write_text(text)
