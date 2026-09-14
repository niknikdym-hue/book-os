#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]).resolve()


def replace_once(rel: str, old: str, new: str) -> None:
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit(f"expected one match in {rel}: {old[:120]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def append(rel: str, block: str) -> None:
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    if block.strip() in text:
        raise SystemExit(f"block already present in {rel}")
    path.write_text(text.rstrip() + "\n\n" + block.strip() + "\n", encoding="utf-8")


SRC = "services/local-core/src/book_os_core/auto_book_exports.py"
TEST = "services/local-core/tests/test_auto_book_exports.py"

# Shared ordering helper. placement=0 is before paragraph 1; placement=N is immediately after
# paragraph N; None/out-of-range is appended at chapter end. Stable list order is preserved.
marker = '''    def _docx(\n'''
helper = '''    @staticmethod\n    def _ordered_chapter_blocks(chapter: MasterChapter) -> list[tuple[str, Any]]:\n        slots: dict[int, list[tuple[str, Any]]] = {}\n        tail: list[tuple[str, Any]] = []\n        paragraph_count = len(chapter.paragraphs)\n        for kind, values in (("TABLE", chapter.tables), ("VISUAL", chapter.visuals)):\n            for value in values:\n                placement = value.placement_after_paragraph\n                if placement is None or placement > paragraph_count:\n                    tail.append((kind, value))\n                else:\n                    slots.setdefault(max(0, placement), []).append((kind, value))\n        blocks: list[tuple[str, Any]] = [*slots.get(0, [])]\n        for index, paragraph in enumerate(chapter.paragraphs, start=1):\n            blocks.append(("PARAGRAPH", paragraph))\n            blocks.extend(slots.get(index, []))\n        blocks.extend(tail)\n        return blocks\n\n'''
path = ROOT / SRC
text = path.read_text(encoding="utf-8")
if helper.strip() not in text:
    if text.count(marker) != 1:
        raise SystemExit("could not locate _docx insertion point")
    path.write_text(text.replace(marker, helper + marker, 1), encoding="utf-8")

old_docx = '''        for chapter in master.chapters:\n            if include_extras_only and not chapter.tables:\n                continue\n            document.add_heading(chapter.title, level=1)\n            if not include_extras_only:\n                for paragraph in chapter.paragraphs:\n                    document.add_paragraph(paragraph)\n            for table in chapter.tables:\n                if audio:\n                    document.add_heading(f"Смысл таблицы «{table.title}»", level=2)\n                    document.add_paragraph(table.audio_equivalent)\n                    continue\n                document.add_heading(table.title, level=2)\n                word_table = document.add_table(rows=1, cols=len(table.headers))\n                word_table.style = "Table Grid"\n                for index, value in enumerate(table.headers):\n                    word_table.rows[0].cells[index].text = value\n                for row in table.rows:\n                    cells = word_table.add_row().cells\n                    for index, value in enumerate(row):\n                        cells[index].text = value\n                expected_tables += 1\n            if include_extras_only:\n                continue\n            for visual in chapter.visuals:\n                if audio:\n                    document.add_heading(f"Смысл материала «{visual.title}»", level=2)\n                    document.add_paragraph(visual.audio_equivalent)\n                    continue\n                image_path = self._render_visual(visual, visual_dir)\n                document.add_picture(str(image_path), width=Inches(6.2))\n                picture_paragraph = document.paragraphs[-1]\n                picture_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER\n                document.add_paragraph(f"{visual.caption}\\nАльтернативный текст: {visual.alt_text}")\n                expected_visuals += 1\n'''
new_docx = '''        def add_table(table: MasterTable) -> None:\n            nonlocal expected_tables\n            if audio:\n                document.add_heading(f"Смысл таблицы «{table.title}»", level=2)\n                document.add_paragraph(table.audio_equivalent)\n                return\n            document.add_heading(table.title, level=2)\n            word_table = document.add_table(rows=1, cols=len(table.headers))\n            word_table.style = "Table Grid"\n            for index, value in enumerate(table.headers):\n                word_table.rows[0].cells[index].text = value\n            for row in table.rows:\n                cells = word_table.add_row().cells\n                for index, value in enumerate(row):\n                    cells[index].text = value\n            expected_tables += 1\n\n        def add_visual(visual: MasterVisual) -> None:\n            nonlocal expected_visuals\n            if audio:\n                document.add_heading(f"Смысл материала «{visual.title}»", level=2)\n                document.add_paragraph(visual.audio_equivalent)\n                return\n            image_path = self._render_visual(visual, visual_dir)\n            document.add_picture(str(image_path), width=Inches(6.2))\n            picture_paragraph = document.paragraphs[-1]\n            picture_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER\n            document.add_paragraph(f"{visual.caption}\\nАльтернативный текст: {visual.alt_text}")\n            expected_visuals += 1\n\n        for chapter in master.chapters:\n            if include_extras_only and not chapter.tables:\n                continue\n            document.add_heading(chapter.title, level=1)\n            if include_extras_only:\n                for table in chapter.tables:\n                    add_table(table)\n                continue\n            for block_kind, block in self._ordered_chapter_blocks(chapter):\n                if block_kind == "PARAGRAPH":\n                    document.add_paragraph(str(block))\n                elif block_kind == "TABLE":\n                    add_table(block)\n                else:\n                    add_visual(block)\n'''
replace_once(SRC, old_docx, new_docx)

old_pdf = '''        for chapter in master.chapters:\n            story.extend([Paragraph(escape(chapter.title), heading), Spacer(1, 4 * mm)])\n            for paragraph in chapter.paragraphs:\n                story.extend([Paragraph(escape(paragraph), body), Spacer(1, 2.5 * mm)])\n            for table in chapter.tables:\n                story.append(Paragraph(escape(table.title), heading))\n                data = [[Paragraph(escape(cell), body) for cell in table.headers]]\n                data.extend([[Paragraph(escape(cell), body) for cell in row] for row in table.rows])\n                rendered = Table(data, repeatRows=1, hAlign="LEFT")\n                rendered.setStyle(\n                    TableStyle(\n                        [\n                            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),\n                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eaf0fb")),\n                            ("VALIGN", (0, 0), (-1, -1), "TOP"),\n                        ]\n                    )\n                )\n                story.extend([rendered, Spacer(1, 4 * mm)])\n            for visual in chapter.visuals:\n                image_path = self._render_visual(visual, visual_dir)\n                story.extend(\n                    [\n                        PdfImage(str(image_path), width=160 * mm, height=90 * mm),\n                        Paragraph(escape(visual.caption), body),\n                    ]\n                )\n'''
new_pdf = '''        for chapter in master.chapters:\n            story.extend([Paragraph(escape(chapter.title), heading), Spacer(1, 4 * mm)])\n            for block_kind, block in self._ordered_chapter_blocks(chapter):\n                if block_kind == "PARAGRAPH":\n                    story.extend([Paragraph(escape(str(block)), body), Spacer(1, 2.5 * mm)])\n                elif block_kind == "TABLE":\n                    table = block\n                    story.append(Paragraph(escape(table.title), heading))\n                    data = [[Paragraph(escape(cell), body) for cell in table.headers]]\n                    data.extend([[Paragraph(escape(cell), body) for cell in row] for row in table.rows])\n                    rendered = Table(data, repeatRows=1, hAlign="LEFT")\n                    rendered.setStyle(\n                        TableStyle(\n                            [\n                                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),\n                                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eaf0fb")),\n                                ("VALIGN", (0, 0), (-1, -1), "TOP"),\n                            ]\n                        )\n                    )\n                    story.extend([rendered, Spacer(1, 4 * mm)])\n                else:\n                    visual = block\n                    image_path = self._render_visual(visual, visual_dir)\n                    story.extend(\n                        [\n                            PdfImage(str(image_path), width=160 * mm, height=90 * mm),\n                            Paragraph(escape(visual.caption), body),\n                        ]\n                    )\n'''
replace_once(SRC, old_pdf, new_pdf)

old_epub_sig = '''    @staticmethod\n    def _epub(master: StructuredBookMaster, output: Path) -> dict[str, Any]:\n'''
new_epub_sig = '''    def _epub(\n        self, master: StructuredBookMaster, output: Path, visual_dir: Path\n    ) -> dict[str, Any]:\n'''
replace_once(SRC, old_epub_sig, new_epub_sig)

old_epub_body = '''            parts = [f"<h1>{escape(chapter.title)}</h1>"]\n            parts.extend(f"<p>{escape(paragraph)}</p>" for paragraph in chapter.paragraphs)\n            for table in chapter.tables:\n                parts.append(f"<h2>{escape(table.title)}</h2><table><thead><tr>")\n                parts.extend(f"<th>{escape(value)}</th>" for value in table.headers)\n                parts.append("</tr></thead><tbody>")\n                for row in table.rows:\n                    parts.append(\n                        "<tr>" + "".join(f"<td>{escape(value)}</td>" for value in row) + "</tr>"\n                    )\n                parts.append("</tbody></table>")\n            item.content = "".join(parts)\n'''
new_epub_body = '''            parts = [f"<h1>{escape(chapter.title)}</h1>"]\n            for block_kind, block in self._ordered_chapter_blocks(chapter):\n                if block_kind == "PARAGRAPH":\n                    parts.append(f"<p>{escape(str(block))}</p>")\n                elif block_kind == "TABLE":\n                    table = block\n                    parts.append(f"<h2>{escape(table.title)}</h2><table><thead><tr>")\n                    parts.extend(f"<th>{escape(value)}</th>" for value in table.headers)\n                    parts.append("</tr></thead><tbody>")\n                    for row in table.rows:\n                        parts.append(\n                            "<tr>"\n                            + "".join(f"<td>{escape(value)}</td>" for value in row)\n                            + "</tr>"\n                        )\n                    parts.append("</tbody></table>")\n                else:\n                    visual = block\n                    image_path = self._render_visual(visual, visual_dir)\n                    image_name = f"images/{visual.object_id}.png"\n                    image_item = epub.EpubImage(\n                        uid=f"visual-{visual.object_id}",\n                        file_name=image_name,\n                        media_type="image/png",\n                        content=image_path.read_bytes(),\n                    )\n                    book.add_item(image_item)\n                    parts.append(\n                        f'<figure><img src="{escape(image_name)}" alt="{escape(visual.alt_text)}" />'\n                        f'<figcaption>{escape(visual.caption)}</figcaption></figure>'\n                    )\n            item.content = "".join(parts)\n'''
replace_once(SRC, old_epub_body, new_epub_body)

replace_once(
    SRC,
    '''            elif kind == "EPUB":\n                qa = self._epub(master, output)\n''',
    '''            elif kind == "EPUB":\n                qa = self._epub(master, output, visual_dir)\n''',
)

# Strengthen EPUB QA with visual count.
replace_once(
    SRC,
    '''        expected_documents = len(master.chapters) + (1 if master.bibliography else 0)\n        if document_count < expected_documents:\n            raise AutoBookExportError("EPUB structural QA failed")\n        return {\n            "passed": True,\n            "document_count": document_count,\n            "bibliography_document": bool(master.bibliography),\n            "viewer_review_required": True,\n        }\n''',
    '''        expected_documents = len(master.chapters) + (1 if master.bibliography else 0)\n        expected_visuals = sum(len(chapter.visuals) for chapter in master.chapters)\n        image_count = len(list(reopened.get_items_of_type(ebooklib.ITEM_IMAGE)))\n        if document_count < expected_documents or image_count < expected_visuals:\n            raise AutoBookExportError("EPUB structural QA failed")\n        return {\n            "passed": True,\n            "document_count": document_count,\n            "expected_visual_count": expected_visuals,\n            "image_count": image_count,\n            "bibliography_document": bool(master.bibliography),\n            "viewer_review_required": True,\n        }\n''',
)

append(TEST, r'''
def test_ordered_blocks_preserve_between_paragraph_placement() -> None:
    chapter = MasterChapter(
        chapter_id="c1",
        title="Глава",
        paragraphs=["Первый абзац.", "Второй абзац.", "Третий абзац."],
        tables=[
            MasterTable(
                object_id="t1",
                title="Таблица",
                headers=["A", "B"],
                rows=[["1", "2"]],
                audio_equivalent="A один, B два.",
                placement_after_paragraph=1,
            )
        ],
        visuals=[
            MasterVisual(
                object_id="v1",
                kind="CHART",
                title="Диаграмма",
                caption="Подпись",
                alt_text="Столбец один.",
                audio_equivalent="Значение один.",
                data=[("Один", 1.0)],
                placement_after_paragraph=2,
            )
        ],
    )
    blocks = AutoBookExporter._ordered_chapter_blocks(chapter)
    assert [(kind, getattr(value, "object_id", value)) for kind, value in blocks] == [
        ("PARAGRAPH", "Первый абзац."),
        ("TABLE", "t1"),
        ("PARAGRAPH", "Второй абзац."),
        ("VISUAL", "v1"),
        ("PARAGRAPH", "Третий абзац."),
    ]


def test_epub_physically_contains_visual_and_alt_text(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path)
    exporter = AutoBookExporter(tmp_path, runtime)
    master = StructuredBookMaster(
        title="Книга",
        author="Автор",
        chapters=[
            MasterChapter(
                chapter_id="c1",
                title="Глава",
                paragraphs=["До изображения.", "После изображения."],
                visuals=[
                    MasterVisual(
                        object_id="visual-one",
                        kind="CHART",
                        title="Диаграмма",
                        caption="Проверенная подпись",
                        alt_text="Альтернативное описание диаграммы",
                        audio_equivalent="Диаграмма показывает значение десять.",
                        data=[("Показатель", 10.0)],
                        placement_after_paragraph=1,
                    )
                ],
            )
        ],
    )
    output = tmp_path / "visual.epub"
    qa = exporter._epub(master, output, tmp_path / "visuals")
    assert qa["expected_visual_count"] == 1
    assert qa["image_count"] >= 1
    reopened = epub.read_epub(str(output))
    chapter = next(iter(reopened.get_items_of_type(ebooklib.ITEM_DOCUMENT)))
    content = chapter.get_content().decode("utf-8")
    assert "Альтернативное описание диаграммы" in content
    assert content.index("До изображения") < content.index("visual-one.png") < content.index("После изображения")
''')

print("T07 ordered export hardening applied")
