from __future__ import annotations

import base64
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re
from statistics import median
from typing import Any, Literal
import xml.etree.ElementTree as ET
from zipfile import BadZipFile, ZipFile

from pydantic import BaseModel, Field

from .authority import new_ulid
from .authority_types import utc_now
from .book_context import (
    BookContextGateError,
    ProfileCreateRequest,
    ProfileRegistry,
    SeriesProfileContent,
)


ReferenceRole = Literal["DELIVERY_STYLE_REFERENCE"]


class SeriesReferenceError(RuntimeError):
    pass


class SeriesReferenceUploadRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    content_base64: str = Field(min_length=1, max_length=16_000_000)
    title: str = Field(default="", max_length=300)
    role: ReferenceRole = "DELIVERY_STYLE_REFERENCE"
    actor: str = Field(default="OWNER", min_length=1, max_length=255)
    owner_approves_derived_style: Literal[True]


class SeriesReferenceView(BaseModel):
    reference_id: str
    series_profile_id: str
    style_profile_id: str
    title: str
    filename: str
    format: Literal["TXT", "MARKDOWN", "DOCX"]
    role: ReferenceRole
    original_sha256: str
    text_sha256: str
    characters: int
    paragraphs: int
    calibration: dict[str, Any]
    representative_excerpts: list[str]
    usage_policy: str
    created_at: str
    actor: str


class SeriesReferenceService:
    """Local immutable series delivery reference.

    The imported book is evidence for presentation quality and manner only. It is
    never exposed as a reusable content source. A bounded, human-approved Style
    Profile is derived from the user-owned upload so normal BOOK OS generation can
    consume the calibration through the existing style authority path.
    """

    _MAX_BYTES = 8 * 1024 * 1024
    _REGISTRY_VERSION = 1
    USAGE_POLICY = (
        "Use only as a delivery/quality reference. Preserve explanatory depth, prose quality, "
        "rhythm and manner of presenting material. Never reuse this book's theses, mechanisms, "
        "arguments, scenes, examples, cases, metaphors, analogies, practical tools, composition "
        "patterns, chapter structure or distinctive wording. Series uniqueness authority and "
        "SeriesBench always take precedence."
    )
    ANTI_CLONE_RULES = [
        "Не копировать и не перефразировать содержание эталонной книги.",
        "Не повторять тезисы, механизмы, аргументы и исследовательские функции других книг серии.",
        "Не повторять сцены, примеры, кейсы, метафоры и аналогии других книг серии.",
        "Не повторять практические инструменты и композиционные паттерны других книг серии.",
        "Не копировать структуру глав, последовательность раскрытия мысли и distinctive wording эталона.",
        "Использовать эталон только для калибровки качества и манеры подачи материала.",
    ]

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.profiles = ProfileRegistry(data_dir)
        self.registry_path = data_dir / "series-reference-masters.json"
        self.storage_dir = data_dir / "series-reference-masters"

    def _read_registry(self) -> dict[str, Any]:
        if not self.registry_path.exists():
            return {"version": self._REGISTRY_VERSION, "series": {}}
        try:
            value = json.loads(self.registry_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SeriesReferenceError("Series Reference registry is unreadable") from exc
        if not isinstance(value, dict) or not isinstance(value.get("series"), dict):
            raise SeriesReferenceError("Series Reference registry has invalid structure")
        return value

    def _write_registry(self, value: dict[str, Any]) -> None:
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.registry_path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(self.registry_path)

    def _approved_series(self, series_profile_id: str) -> tuple[str, SeriesProfileContent]:
        profile = self.profiles.get_profile(series_profile_id)
        if profile.kind != "SERIES":
            raise SeriesReferenceError("reference master requires a Series Profile")
        if profile.status != "APPROVED":
            raise BookContextGateError("reference master requires an approved Series Profile")
        content = SeriesProfileContent.model_validate(profile.content)
        return profile.name, content

    @staticmethod
    def _decode_text(payload: bytes) -> str:
        for encoding in ("utf-8-sig", "utf-8", "cp1251"):
            try:
                return payload.decode(encoding)
            except UnicodeDecodeError:
                continue
        raise SeriesReferenceError("text file encoding is unsupported")

    @staticmethod
    def _extract_docx(payload: bytes) -> str:
        try:
            with ZipFile(BytesIO(payload)) as archive:
                raw = archive.read("word/document.xml")
        except (BadZipFile, KeyError) as exc:
            raise SeriesReferenceError("DOCX is invalid or has no document.xml") from exc
        try:
            root = ET.fromstring(raw)
        except ET.ParseError as exc:
            raise SeriesReferenceError("DOCX document.xml is invalid") from exc
        paragraphs: list[str] = []
        for paragraph in root.iter():
            if not paragraph.tag.endswith("}p"):
                continue
            parts = [
                node.text or ""
                for node in paragraph.iter()
                if node.tag.endswith("}t") and node.text
            ]
            value = "".join(parts).strip()
            if value:
                paragraphs.append(value)
        return "\n\n".join(paragraphs)

    @classmethod
    def _extract(
        cls, filename: str, payload: bytes
    ) -> tuple[str, Literal["TXT", "MARKDOWN", "DOCX"]]:
        suffix = Path(filename).suffix.casefold()
        if suffix == ".txt":
            return cls._decode_text(payload), "TXT"
        if suffix in {".md", ".markdown"}:
            return cls._decode_text(payload), "MARKDOWN"
        if suffix == ".docx":
            return cls._extract_docx(payload), "DOCX"
        raise SeriesReferenceError("supported reference formats are TXT, Markdown and DOCX")

    @staticmethod
    def _clean_text(value: str) -> str:
        normalized = value.replace("\r\n", "\n").replace("\r", "\n")
        paragraphs = [
            re.sub(r"[ \t]+", " ", item).strip() for item in re.split(r"\n\s*\n", normalized)
        ]
        return "\n\n".join(item for item in paragraphs if item)

    @staticmethod
    def _sentences(text_value: str) -> list[str]:
        return [item.strip() for item in re.split(r"(?<=[.!?…])\s+", text_value) if item.strip()]

    @classmethod
    def _calibration(cls, text_value: str) -> tuple[dict[str, Any], list[str]]:
        paragraphs = [item.strip() for item in text_value.split("\n\n") if item.strip()]
        lengths = [len(item) for item in paragraphs]
        sentences = cls._sentences(text_value)
        sentence_lengths = [len(item) for item in sentences]
        heading_like = [
            item
            for item in paragraphs
            if len(item) <= 120
            and len(item.split()) <= 14
            and not item.endswith((".", "!", "?", "…"))
        ]
        calibration = {
            "usage_scope": "delivery_style_only",
            "quality_intent": "preserve level without cloning content",
            "paragraph_count": len(paragraphs),
            "average_paragraph_characters": round(sum(lengths) / max(1, len(lengths)), 1),
            "median_paragraph_characters": round(float(median(lengths)), 1) if lengths else 0.0,
            "short_paragraph_share": round(
                sum(1 for value in lengths if value <= 220) / max(1, len(lengths)), 3
            ),
            "long_paragraph_share": round(
                sum(1 for value in lengths if value >= 800) / max(1, len(lengths)), 3
            ),
            "sentence_count": len(sentences),
            "average_sentence_characters": round(
                sum(sentence_lengths) / max(1, len(sentence_lengths)), 1
            ),
            "heading_like_paragraphs": len(heading_like),
        }

        candidates = [item for item in paragraphs if 220 <= len(item) <= 1200]
        if not candidates:
            candidates = [item for item in paragraphs if len(item) >= 120]
        excerpts: list[str] = []
        if candidates:
            indexes = {0, len(candidates) // 2, len(candidates) - 1}
            for index in sorted(indexes):
                excerpt = candidates[index][:900].strip()
                if excerpt and excerpt not in excerpts:
                    excerpts.append(excerpt)
        return calibration, excerpts[:3]

    @classmethod
    def _style_content(
        cls,
        *,
        series_name: str,
        series: SeriesProfileContent,
        reference_title: str,
        calibration: dict[str, Any],
        excerpts: list[str],
    ) -> dict[str, Any]:
        rhythm = (
            f"Эталон '{reference_title}': средний абзац ~"
            f"{calibration['average_paragraph_characters']} знаков, среднее предложение ~"
            f"{calibration['average_sentence_characters']} знаков. Сохранять живой вариативный "
            "ритм и плотность, но не копировать композицию эталонной книги."
        )
        return {
            "style_name": f"{series_name} — эталон подачи",
            "author_profile_id": series.author_profile_id,
            "literary_register": (
                "Манера подачи серии, откалиброванная по пользовательской эталонной книге; "
                "содержание каждой новой книги полностью уникально."
            ),
            "authorial_presence": "Сохранять уровень авторского присутствия эталона без имитации его содержания.",
            "directness": "Сохранять степень прямоты и ясности подачи на уровне эталона.",
            "sentence_paragraph_rhythm": rhythm,
            "scene_density": "Сохранять функциональную плотность примеров/сцен, создавая только новые материалы.",
            "evidence_density": "Сохранять доказательность и интеллектуальную плотность; факты требуют обычной проверки.",
            "analytical_depth": "Не снижать глубину объяснения механизмов и причинно-следственных связей относительно эталона.",
            "irony_humor": "Следовать авторскому профилю и уровню эталона без заимствования шуток или аналогий.",
            "emotional_temperature": "Сохранять общую эмоциональную температуру серии без повторения сцен и формулировок.",
            "practical_instruction_intensity": "Сохранять баланс анализа и практической ценности; практические инструменты должны быть новыми.",
            "terminology_level": "Сохранять уровень ясности и терминологической сложности эталона.",
            "prohibited_patterns": list(cls.ANTI_CLONE_RULES),
            "benchmark_excerpts": excerpts,
        }

    def upload(
        self, series_profile_id: str, request: SeriesReferenceUploadRequest
    ) -> SeriesReferenceView:
        series_name, series = self._approved_series(series_profile_id)
        try:
            payload = base64.b64decode(request.content_base64, validate=True)
        except ValueError as exc:
            raise SeriesReferenceError("reference payload is not valid base64") from exc
        if not payload:
            raise SeriesReferenceError("reference file is empty")
        if len(payload) > self._MAX_BYTES:
            raise SeriesReferenceError("reference file exceeds the 8 MB local limit")

        extracted, format_name = self._extract(request.filename, payload)
        text_value = self._clean_text(extracted)
        if len(text_value) < 4_000:
            raise SeriesReferenceError("reference master must contain at least 4000 characters")
        calibration, excerpts = self._calibration(text_value)
        original_hash = hashlib.sha256(payload).hexdigest()
        text_hash = hashlib.sha256(text_value.encode("utf-8")).hexdigest()
        reference_id = new_ulid()
        created_at = utc_now()
        title = request.title.strip() or Path(request.filename).stem

        style = self.profiles.create_profile(
            ProfileCreateRequest(
                kind="STYLE",
                content=self._style_content(
                    series_name=series_name,
                    series=series,
                    reference_title=title,
                    calibration=calibration,
                    excerpts=excerpts,
                ),
            )
        )
        if request.owner_approves_derived_style is not True:
            raise SeriesReferenceError(
                "explicit owner approval is required for derived Style Profile"
            )
        style = self.profiles.approve_profile(style.profile_id)

        series_dir = self.storage_dir / series_profile_id / reference_id
        series_dir.mkdir(parents=True, exist_ok=False)
        source_name = f"source{Path(request.filename).suffix.casefold()}"
        (series_dir / source_name).write_bytes(payload)
        (series_dir / "extracted.txt").write_text(text_value + "\n", encoding="utf-8")

        view = SeriesReferenceView(
            reference_id=reference_id,
            series_profile_id=series_profile_id,
            style_profile_id=style.profile_id,
            title=title,
            filename=Path(request.filename).name,
            format=format_name,
            role=request.role,
            original_sha256=original_hash,
            text_sha256=text_hash,
            characters=len(text_value),
            paragraphs=len([item for item in text_value.split("\n\n") if item.strip()]),
            calibration=calibration,
            representative_excerpts=excerpts,
            usage_policy=self.USAGE_POLICY,
            created_at=created_at,
            actor=request.actor.strip(),
        )

        registry = self._read_registry()
        raw_series = registry["series"].setdefault(
            series_profile_id, {"active_reference_id": None, "references": []}
        )
        if not isinstance(raw_series, dict) or not isinstance(raw_series.get("references"), list):
            raise SeriesReferenceError("Series Reference registry entry is invalid")
        raw_series["references"].append(view.model_dump(mode="json"))
        raw_series["active_reference_id"] = reference_id
        self._write_registry(registry)
        return view

    def current(self, series_profile_id: str) -> SeriesReferenceView | None:
        self._approved_series(series_profile_id)
        registry = self._read_registry()
        raw_series = registry["series"].get(series_profile_id)
        if not isinstance(raw_series, dict):
            return None
        reference_id = raw_series.get("active_reference_id")
        references = raw_series.get("references")
        if not isinstance(reference_id, str) or not isinstance(references, list):
            return None
        raw = next(
            (
                item
                for item in references
                if isinstance(item, dict) and item.get("reference_id") == reference_id
            ),
            None,
        )
        return SeriesReferenceView.model_validate(raw) if isinstance(raw, dict) else None
