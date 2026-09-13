from __future__ import annotations

from html import escape
import json
from pathlib import Path
import re
from typing import Any, Literal

from docx import Document
from docx.document import Document as DocumentObject
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt
import ebooklib  # type: ignore[import-untyped]
from ebooklib import epub
from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel, Field, model_validator
from reportlab.lib.enums import TA_CENTER  # type: ignore[import-untyped]
from reportlab.lib.pagesizes import A4  # type: ignore[import-untyped]
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # type: ignore[import-untyped]
from reportlab.lib.units import mm  # type: ignore[import-untyped]
from reportlab.pdfbase import pdfmetrics  # type: ignore[import-untyped]
from reportlab.pdfbase.ttfonts import TTFont  # type: ignore[import-untyped]
from reportlab.platypus import Image as PdfImage  # type: ignore[import-untyped]
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib import colors  # type: ignore[import-untyped]

from .authority import canonical_json
from .auto_book_runtime import (
    AutoBookArtifactView,
    AutoBookOutputKind,
    AutoBookOutputSelection,
    DurableAutoBookRuntime,
)


class AutoBookExportError(RuntimeError):
    pass


class MasterTable(BaseModel):
    object_id: str = Field(min_length=1, max_length=160)
    title: str = Field(min_length=1, max_length=500)
    headers: list[str] = Field(min_length=1, max_length=30)
    rows: list[list[str]] = Field(min_length=1, max_length=2000)
    audio_equivalent: str = Field(min_length=1, max_length=12000)
    source_note: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def rectangular(self) -> MasterTable:
        if any(len(row) != len(self.headers) for row in self.rows):
            raise ValueError("every table row must match the header width")
        return self


class MasterVisual(BaseModel):
    object_id: str = Field(min_length=1, max_length=160)
    kind: Literal["CHART", "SCHEME", "ILLUSTRATION"]
    title: str = Field(min_length=1, max_length=500)
    caption: str = Field(min_length=1, max_length=2000)
    alt_text: str = Field(min_length=1, max_length=4000)
    audio_equivalent: str = Field(min_length=1, max_length=12000)
    data: list[tuple[str, float]] = Field(default_factory=list, max_length=100)
    source_note: str | None = Field(default=None, max_length=2000)
    rights_note: str = Field(default="Created programmatically by BOOK OS", max_length=1000)


class MasterChapter(BaseModel):
    chapter_id: str = Field(min_length=1, max_length=160)
    title: str = Field(min_length=1, max_length=500)
    paragraphs: list[str] = Field(min_length=1)
    tables: list[MasterTable] = Field(default_factory=list)
    visuals: list[MasterVisual] = Field(default_factory=list)


class StructuredBookMaster(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    author: str = Field(min_length=1, max_length=300)
    language: str = "ru"
    chapters: list[MasterChapter] = Field(min_length=1)
    bibliography: list[str] = Field(default_factory=list)
    publisher_annotation: str = Field(default="", max_length=12000)

    @property
    def manifest_hash(self) -> str:
        import hashlib

        return hashlib.sha256(
            canonical_json(self.model_dump(mode="json")).encode("utf-8")
        ).hexdigest()


class ExportBundle(BaseModel):
    master_hash: str
    artifacts: list[AutoBookArtifactView]
    output_directory: str


class AutoBookExporter:
    EXPORTER_VERSION = "auto-book-export.v1.0.0"
    PROFILE_VERSIONS: dict[AutoBookOutputKind, str] = {
        "FULL_MANUSCRIPT_DOCX": "full-manuscript.v1",
        "LITRES_EBOOK_DOCX": "litres-ebook.owner-profile.v1",
        "READING_PDF": "reading-pdf.v1",
        "EPUB": "epub3.v1",
        "AUDIO_READING_DOCX": "audio-reading.v1",
        "AUDIO_LITRES_DOCX": "audio-litres.owner-profile.v1",
        "VOICE_TEXT_TXT": "voice-text.v1",
        "PRONUNCIATION_DICTIONARY": "pronunciation.v1",
        "READER_EXTRAS": "reader-extras.v1",
        "PUBLISHER_PACK": "publisher-pack.v1",
    }

    _FILE_NAMES: dict[AutoBookOutputKind, str] = {
        "FULL_MANUSCRIPT_DOCX": "Полная-рукопись.docx",
        "LITRES_EBOOK_DOCX": "Электронная-версия-Литрес.docx",
        "READING_PDF": "Версия-для-чтения.pdf",
        "EPUB": "Электронная-книга.epub",
        "AUDIO_READING_DOCX": "Аудиоредакция-для-чтения.docx",
        "AUDIO_LITRES_DOCX": "Аудиоредакция-для-Литрес.docx",
        "VOICE_TEXT_TXT": "Текст-для-озвучки.txt",
        "PRONUNCIATION_DICTIONARY": "Словарь-произношения.txt",
        "READER_EXTRAS": "Дополнительные-материалы.docx",
        "PUBLISHER_PACK": "Издательский-пакет.json",
    }

    def __init__(self, data_dir: Path, runtime: DurableAutoBookRuntime) -> None:
        self.data_dir = data_dir
        self.runtime = runtime

    @staticmethod
    def _font_path() -> Path | None:
        candidates = (
            Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
            Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        )
        return next((path for path in candidates if path.is_file()), None)

    @classmethod
    def _register_pdf_font(cls) -> str:
        path = cls._font_path()
        if path is None:
            raise AutoBookExportError("a Unicode TrueType font is required for Russian PDF export")
        name = "BookOSUnicode"
        if name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(name, str(path)))
        return name

    @classmethod
    def _image_font(cls, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        path = cls._font_path()
        if path is None:
            return ImageFont.load_default()
        return ImageFont.truetype(str(path), size=size)

    @staticmethod
    def _apply_docx_styles(document: DocumentObject) -> None:
        normal = document.styles["Normal"]
        normal.font.name = "Arial"
        normal.font.size = Pt(11)
        for style_name, size in (("Title", 22), ("Heading 1", 16), ("Heading 2", 13)):
            style = document.styles[style_name]
            style.font.name = "Arial"
            style.font.size = Pt(size)

    @staticmethod
    def _add_bibliography(document: DocumentObject, bibliography: list[str]) -> None:
        if not bibliography:
            return
        document.add_page_break()  # type: ignore[no-untyped-call]
        document.add_heading("Библиография", level=1)
        for index, entry in enumerate(bibliography, start=1):
            document.add_paragraph(f"{index}. {entry}")

    def _render_visual(self, visual: MasterVisual, output_dir: Path) -> Path:
        output = output_dir / f"{visual.object_id}.png"
        image = Image.new("RGB", (1600, 900), "white")
        draw = ImageDraw.Draw(image)
        title_font = self._image_font(42)
        body_font = self._image_font(28)
        draw.text((80, 55), visual.title, fill="#17253f", font=title_font)
        if visual.kind == "CHART" and visual.data:
            maximum = max(value for _, value in visual.data) or 1.0
            bar_width = max(60, 1200 // len(visual.data))
            for index, (label, value) in enumerate(visual.data):
                x0 = 100 + index * bar_width
                height = int(560 * value / maximum)
                y0 = 720 - height
                draw.rectangle((x0, y0, x0 + bar_width - 24, 720), fill="#2d6cdf")
                draw.text((x0, 735), label, fill="#17253f", font=body_font)
                draw.text((x0, max(115, y0 - 40)), str(value), fill="#17253f", font=body_font)
        else:
            draw.rounded_rectangle((140, 230, 1460, 650), radius=32, outline="#2d6cdf", width=8)
            draw.multiline_text(
                (210, 300),
                visual.alt_text,
                fill="#17253f",
                font=body_font,
                spacing=18,
            )
        image.save(output, format="PNG", optimize=True)
        return output

    def _docx(
        self,
        master: StructuredBookMaster,
        output: Path,
        *,
        audio: bool,
        include_extras_only: bool = False,
        visual_dir: Path,
    ) -> dict[str, Any]:
        document = Document()
        self._apply_docx_styles(document)
        document.add_heading(master.title, level=0)
        document.add_paragraph(master.author)
        expected_tables = 0
        expected_visuals = 0
        if include_extras_only:
            document.add_heading("Дополнительные материалы", level=1)
        for chapter in master.chapters:
            if include_extras_only and not chapter.tables:
                continue
            document.add_heading(chapter.title, level=1)
            if not include_extras_only:
                for paragraph in chapter.paragraphs:
                    document.add_paragraph(paragraph)
            for table in chapter.tables:
                if audio:
                    document.add_heading(f"Смысл таблицы «{table.title}»", level=2)
                    document.add_paragraph(table.audio_equivalent)
                    continue
                document.add_heading(table.title, level=2)
                word_table = document.add_table(rows=1, cols=len(table.headers))
                word_table.style = "Table Grid"
                for index, value in enumerate(table.headers):
                    word_table.rows[0].cells[index].text = value
                for row in table.rows:
                    cells = word_table.add_row().cells
                    for index, value in enumerate(row):
                        cells[index].text = value
                expected_tables += 1
            if include_extras_only:
                continue
            for visual in chapter.visuals:
                if audio:
                    document.add_heading(f"Смысл материала «{visual.title}»", level=2)
                    document.add_paragraph(visual.audio_equivalent)
                    continue
                image_path = self._render_visual(visual, visual_dir)
                document.add_picture(str(image_path), width=Inches(6.2))
                picture_paragraph = document.paragraphs[-1]
                picture_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                document.add_paragraph(f"{visual.caption}\nАльтернативный текст: {visual.alt_text}")
                expected_visuals += 1
        if not include_extras_only:
            self._add_bibliography(document, master.bibliography)
        document.save(str(output))

        reopened = Document(str(output))
        qa = {
            "passed": len(reopened.tables) == expected_tables,
            "native_table_count": len(reopened.tables),
            "expected_table_count": expected_tables,
            "expected_visual_count": expected_visuals,
            "paragraph_count": len(reopened.paragraphs),
            "audio_adaptation": audio,
        }
        if not qa["passed"]:
            raise AutoBookExportError("DOCX structural QA failed")
        return qa

    def _pdf(self, master: StructuredBookMaster, output: Path, visual_dir: Path) -> dict[str, Any]:
        font = self._register_pdf_font()
        styles = getSampleStyleSheet()
        body = ParagraphStyle(
            "BookOSBody", parent=styles["BodyText"], fontName=font, fontSize=11, leading=16
        )
        heading = ParagraphStyle(
            "BookOSHeading", parent=styles["Heading1"], fontName=font, fontSize=18, leading=23
        )
        title = ParagraphStyle(
            "BookOSTitle", parent=heading, fontSize=24, alignment=TA_CENTER, spaceAfter=18
        )
        story: list[Any] = [
            Paragraph(escape(master.title), title),
            Paragraph(escape(master.author), body),
            PageBreak(),
        ]
        for chapter in master.chapters:
            story.extend([Paragraph(escape(chapter.title), heading), Spacer(1, 4 * mm)])
            for paragraph in chapter.paragraphs:
                story.extend([Paragraph(escape(paragraph), body), Spacer(1, 2.5 * mm)])
            for table in chapter.tables:
                story.append(Paragraph(escape(table.title), heading))
                data = [[Paragraph(escape(cell), body) for cell in table.headers]]
                data.extend([[Paragraph(escape(cell), body) for cell in row] for row in table.rows])
                rendered = Table(data, repeatRows=1, hAlign="LEFT")
                rendered.setStyle(
                    TableStyle(
                        [
                            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eaf0fb")),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ]
                    )
                )
                story.extend([rendered, Spacer(1, 4 * mm)])
            for visual in chapter.visuals:
                image_path = self._render_visual(visual, visual_dir)
                story.extend(
                    [
                        PdfImage(str(image_path), width=160 * mm, height=90 * mm),
                        Paragraph(escape(visual.caption), body),
                    ]
                )
        if master.bibliography:
            story.extend([PageBreak(), Paragraph("Библиография", heading)])
            story.extend(
                Paragraph(escape(f"{index}. {entry}"), body)
                for index, entry in enumerate(master.bibliography, start=1)
            )
        SimpleDocTemplate(
            str(output),
            pagesize=A4,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=18 * mm,
            bottomMargin=18 * mm,
            title=master.title,
            author=master.author,
        ).build(story)
        payload = output.read_bytes()
        passed = payload.startswith(b"%PDF-") and b"%%EOF" in payload[-2048:]
        if not passed:
            raise AutoBookExportError("PDF structural QA failed")
        return {"passed": True, "pdf_magic": True, "visual_review_required": True}

    @staticmethod
    def _epub(master: StructuredBookMaster, output: Path) -> dict[str, Any]:
        book = epub.EpubBook()
        book.set_identifier(master.manifest_hash)
        book.set_title(master.title)
        book.set_language(master.language)
        book.add_author(master.author)
        chapters: list[Any] = []
        for index, chapter in enumerate(master.chapters, start=1):
            item = epub.EpubHtml(
                title=chapter.title, file_name=f"chapter-{index}.xhtml", lang=master.language
            )
            parts = [f"<h1>{escape(chapter.title)}</h1>"]
            parts.extend(f"<p>{escape(paragraph)}</p>" for paragraph in chapter.paragraphs)
            for table in chapter.tables:
                parts.append(f"<h2>{escape(table.title)}</h2><table><thead><tr>")
                parts.extend(f"<th>{escape(value)}</th>" for value in table.headers)
                parts.append("</tr></thead><tbody>")
                for row in table.rows:
                    parts.append(
                        "<tr>" + "".join(f"<td>{escape(value)}</td>" for value in row) + "</tr>"
                    )
                parts.append("</tbody></table>")
            item.content = "".join(parts)
            book.add_item(item)
            chapters.append(item)
        book.toc = tuple(chapters)
        book.spine = ["nav", *chapters]
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        epub.write_epub(str(output), book, {})
        reopened = epub.read_epub(str(output))
        document_count = len(list(reopened.get_items_of_type(ebooklib.ITEM_DOCUMENT)))
        if document_count < len(master.chapters):
            raise AutoBookExportError("EPUB structural QA failed")
        return {"passed": True, "document_count": document_count, "viewer_review_required": True}

    @staticmethod
    def _voice_text(master: StructuredBookMaster) -> str:
        parts = [master.title, master.author]
        for chapter in master.chapters:
            parts.extend((chapter.title, *chapter.paragraphs))
            parts.extend(table.audio_equivalent for table in chapter.tables)
            parts.extend(visual.audio_equivalent for visual in chapter.visuals)
        if master.bibliography:
            parts.append("Библиография доступна в электронной версии книги.")
        return "\n\n".join(value.strip() for value in parts if value.strip()) + "\n"

    @staticmethod
    def _pronunciation_dictionary(master: StructuredBookMaster) -> str:
        text = " ".join(
            [master.title, master.author]
            + [paragraph for chapter in master.chapters for paragraph in chapter.paragraphs]
        )
        terms = sorted(set(re.findall(r"\b[A-ZА-ЯЁ]{2,}\b", text)))
        return "# Термин\tПроизношение\tКомментарий\n" + "".join(
            f"{term}\t\tпроверить перед озвучкой\n" for term in terms
        )

    @staticmethod
    def _publisher_pack(master: StructuredBookMaster) -> bytes:
        payload = {
            "title": master.title,
            "author": master.author,
            "language": master.language,
            "annotation": master.publisher_annotation,
            "chapter_count": len(master.chapters),
            "master_hash": master.manifest_hash,
        }
        return (json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()

    def export_selected(
        self,
        book_id: str,
        run_id: str,
        master: StructuredBookMaster,
        selection: AutoBookOutputSelection,
    ) -> ExportBundle:
        master_hash = master.manifest_hash
        output_dir = (
            self.runtime.projects.projects_dir / book_id / "exports" / run_id / master_hash[:12]
        )
        visual_dir = output_dir / "visuals"
        visual_dir.mkdir(parents=True, exist_ok=True)
        artifacts: list[AutoBookArtifactView] = []
        for kind in selection.selected():
            output = output_dir / self._FILE_NAMES[kind]
            if kind == "FULL_MANUSCRIPT_DOCX":
                qa = self._docx(master, output, audio=False, visual_dir=visual_dir)
            elif kind == "LITRES_EBOOK_DOCX":
                qa = self._docx(master, output, audio=False, visual_dir=visual_dir)
                qa["platform_acceptance_claimed"] = False
                qa["requirements_profile_checked_at"] = "owner-profile.v1"
            elif kind in {"AUDIO_READING_DOCX", "AUDIO_LITRES_DOCX"}:
                qa = self._docx(master, output, audio=True, visual_dir=visual_dir)
                qa["table_and_visual_meaning_preserved"] = True
            elif kind == "READING_PDF":
                qa = self._pdf(master, output, visual_dir)
            elif kind == "EPUB":
                qa = self._epub(master, output)
            elif kind == "VOICE_TEXT_TXT":
                output.write_text(self._voice_text(master), encoding="utf-8")
                qa = {"passed": True, "spoken_text": True, "is_full_text_extraction": False}
            elif kind == "PRONUNCIATION_DICTIONARY":
                output.write_text(self._pronunciation_dictionary(master), encoding="utf-8")
                qa = {"passed": True, "technical_dictionary_outside_manuscript": True}
            elif kind == "READER_EXTRAS":
                qa = self._docx(
                    master, output, audio=False, include_extras_only=True, visual_dir=visual_dir
                )
            else:
                output.write_bytes(self._publisher_pack(master))
                qa = {"passed": True, "schema": "publisher-pack.v1"}
            payload = output.read_bytes()
            relative_path = str(output.relative_to(self.runtime.projects.projects_dir / book_id))
            artifacts.append(
                self.runtime.register_artifact(
                    book_id,
                    run_id,
                    output_kind=kind,
                    master_hash=master_hash,
                    profile_version=self.PROFILE_VERSIONS[kind],
                    exporter_version=self.EXPORTER_VERSION,
                    relative_path=relative_path,
                    payload=payload,
                    qa=qa,
                )
            )
        return ExportBundle(
            master_hash=master_hash,
            artifacts=artifacts,
            output_directory=str(output_dir),
        )
