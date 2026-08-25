from pathlib import Path

path = Path("apps/desktop/src/App.tsx")
text = path.read_text()
old_import = 'import { DraftingPanel } from "./DraftingPanel";\n'
new_import = old_import + 'import { ResearchPanel } from "./ResearchPanel";\n'
if old_import not in text:
    raise SystemExit("DraftingPanel import not found")
text = text.replace(old_import, new_import, 1)
old_render = '              <DraftingPanel project={project} chapter={selectedChapter} />\n'
new_render = old_render + '              <ResearchPanel project={project} chapter={selectedChapter} />\n'
if old_render not in text:
    raise SystemExit("DraftingPanel render not found")
text = text.replace(old_render, new_render, 1)
path.write_text(text)
