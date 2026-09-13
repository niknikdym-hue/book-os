from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any, Literal, cast

from pydantic import BaseModel, Field, model_validator
from sqlalchemy import text
from sqlalchemy.engine import Engine

from .authority import canonical_json, new_ulid
from .authority_types import utc_now
from .db import create_database
from .projects import ProjectService


AudioAdaptationMode = Literal["SOURCE_FAITHFUL", "LISTENING_ADAPTATION", "AUDIO_NATIVE"]
AudioAuthorityStatus = Literal["DRAFT", "PROPOSED", "APPROVED", "SUPERSEDED"]
AudioCheckState = Literal["PASS", "ATTENTION", "BLOCKING"]
PronunciationCategory = Literal[
    "PERSON",
    "PLACE",
    "COMPANY_OR_PRODUCT",
    "ACRONYM",
    "FOREIGN",
    "PROFESSIONAL_TERM",
    "AMBIGUOUS_STRESS",
    "AUTHOR_WORD",
]
AudioDisposition = Literal[
    "SPOKEN_REWRITE",
    "AUDIO_EXPLANATION",
    "COMPANION_ARTIFACT",
    "SUPPLEMENT_REFERENCE",
    "OMIT_FROM_AUDIO",
    "BLOCKED",
]

MANDATORY_AUDIO_CHECKS: tuple[str, ...] = (
    "LISTENABILITY",
    "SOURCE_FIDELITY",
    "SEMANTIC_FIDELITY",
    "AUTHOR_VOICE_FOR_AUDIO",
    "VISUAL_DEPENDENCY_RESOLVED",
    "NUMBER_AND_SYMBOL_PRONUNCIATION",
    "ACRONYM_AND_TERM_PRONUNCIATION",
    "PAGE_DEPENDENT_LANGUAGE",
    "AUDIO_ORIENTATION",
    "AUDIO_REDUNDANCY",
    "CLEAN_RECORDING_TEXT",
    "AUDIO_COMPLETENESS",
)


class AudioScriptError(RuntimeError):
    pass


class AudioScriptGateError(AudioScriptError):
    pass


class AudioVisualDecision(BaseModel):
    object_id: str = Field(min_length=1, max_length=160)
    kind: Literal["TABLE", "CHART", "SCHEME", "ILLUSTRATION"]
    title: str = Field(min_length=1, max_length=500)
    significant: bool = True
    disposition: AudioDisposition
    placement_after_paragraph: int = Field(ge=0)
    explanation: str = Field(default="", max_length=12000)
    source_facts: list[str] = Field(default_factory=list, max_length=200)

    @model_validator(mode="after")
    def explanation_required(self) -> AudioVisualDecision:
        if self.disposition in {"SPOKEN_REWRITE", "AUDIO_EXPLANATION"} and not self.explanation:
            raise ValueError("spoken visual dispositions require an explanation")
        return self


class AudioScriptSection(BaseModel):
    source_chapter_id: str = Field(min_length=1, max_length=160)
    title: str = Field(min_length=1, max_length=500)
    paragraphs: list[str] = Field(min_length=1)
    visual_decisions: list[AudioVisualDecision] = Field(default_factory=list)

    def recording_paragraphs(self) -> list[str]:
        decisions: dict[int, list[str]] = {}
        for item in self.visual_decisions:
            if item.disposition in {"SPOKEN_REWRITE", "AUDIO_EXPLANATION"}:
                decisions.setdefault(item.placement_after_paragraph, []).append(item.explanation)
            elif item.disposition in {"COMPANION_ARTIFACT", "SUPPLEMENT_REFERENCE"}:
                decisions.setdefault(item.placement_after_paragraph, []).append(item.explanation)
        result: list[str] = []
        for index, paragraph in enumerate(self.paragraphs, start=1):
            result.append(paragraph)
            result.extend(decisions.get(index, []))
        result.extend(decisions.get(0, []))
        for placement in sorted(value for value in decisions if value > len(self.paragraphs)):
            result.extend(decisions[placement])
        return result


class AudioScriptContent(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    author: str = Field(min_length=1, max_length=300)
    language: str = "ru"
    sections: list[AudioScriptSection] = Field(min_length=1)

    def clean_recording_text(self) -> str:
        parts = [self.title, self.author]
        for section in self.sections:
            parts.append(section.title)
            parts.extend(section.recording_paragraphs())
        return "\n\n".join(value.strip() for value in parts if value.strip()) + "\n"


class AudioTransformation(BaseModel):
    source_unit_id: str = Field(min_length=1, max_length=300)
    outcome: Literal["PRESERVED", "REWRITTEN", "MOVED", "OMITTED", "ADDED"]
    summary: str = Field(min_length=1, max_length=4000)
    material: bool = False
    human_review_required: bool = False


class AudioQualityFinding(BaseModel):
    code: str
    location: str
    detail: str
    severity: Literal["ATTENTION", "BLOCKING"]


class AudioQualityCheck(BaseModel):
    check_kind: str
    state: AudioCheckState
    findings: list[AudioQualityFinding] = Field(default_factory=list)
    source_hash: str
    script_hash: str
    evaluator_kind: Literal["SYSTEM", "MODEL", "HUMAN"] = "SYSTEM"


class PronunciationEntry(BaseModel):
    term: str
    category: PronunciationCategory
    recommendation: str | None = None
    status: Literal["NEEDS_REVIEW", "VERIFIED", "REJECTED"] = "NEEDS_REVIEW"
    origin: str


class AudioScriptView(BaseModel):
    audio_script_id: str
    book_id: str
    source_kind: Literal["LITERARY_MASTER", "IMPORTED_SOURCE"]
    source_identity: str
    source_hash: str
    adaptation_mode: AudioAdaptationMode
    version: int
    status: AudioAuthorityStatus
    content: AudioScriptContent
    content_hash: str
    transformations: list[AudioTransformation]
    provenance: dict[str, Any]
    approval: dict[str, Any] | None
    quality_checks: list[AudioQualityCheck]
    pronunciation_entries: list[PronunciationEntry]
    stale_against_source: bool = False
    created_at: str
    updated_at: str

    @property
    def ready_for_export(self) -> bool:
        return (
            self.status == "APPROVED"
            and not self.stale_against_source
            and all(item.state != "BLOCKING" for item in self.quality_checks)
            and {item.check_kind for item in self.quality_checks} == set(MANDATORY_AUDIO_CHECKS)
        )


def audio_content_hash(content: AudioScriptContent) -> str:
    return hashlib.sha256(
        canonical_json(content.model_dump(mode="json")).encode("utf-8")
    ).hexdigest()


def _word_tokens(value: str) -> set[str]:
    return {
        token.casefold()
        for token in re.findall(r"[A-Za-zА-Яа-яЁё0-9]+", value)
        if len(token) >= 3 or token.isdigit()
    }


class AudioScriptService:
    """Versioned audio-editorial artifacts derived from an exact immutable source snapshot."""

    _PAGE_DEPENDENT = re.compile(
        r"\b(?:см\.?|смотрите|как показано)\s+(?:выше|ниже)|"
        r"\b(?:на|в)\s+(?:следующей|предыдущей)\s+страниц[еуы]|"
        r"\bв\s+(?:таблице|схеме|рисунке)\s+(?:выше|ниже)\b",
        re.IGNORECASE,
    )
    _TECHNICAL_RESIDUE = re.compile(
        r"(?:```|\*\*|^#{1,6}\s|</?[a-z][^>]*>|\[TODO\]|\{\{[^}]+\}\}|"
        r"audio_script_id|source_hash|system prompt|служебн(?:ая|ые) инструкц)",
        re.IGNORECASE | re.MULTILINE,
    )
    _RAW_URL = re.compile(r"https?://\S+", re.IGNORECASE)
    _SSML = re.compile(r"</?(?:speak|break|prosody|phoneme|say-as)\b", re.IGNORECASE)
    _FOOTNOTE_MARKER = re.compile(r"\[(?:\d+|[A-Za-zА-Яа-яЁё]+)\]")
    _AMBIGUOUS = {"атлас", "замок", "мука", "орган", "ирис", "характерный"}
    _PROFESSIONAL = {"маркетинг", "конверсия", "воронка", "лид", "юнит-экономика"}

    def __init__(self, data_dir: Path) -> None:
        self.projects = ProjectService(data_dir)

    def _engine(self, book_id: str) -> Engine:
        self.projects.get_project(book_id)
        return create_database(self.projects.projects_dir / book_id / "project.sqlite")

    @staticmethod
    def _visual_is_substantive(item: AudioVisualDecision) -> bool:
        if item.disposition in {"OMIT_FROM_AUDIO"}:
            return not item.significant
        if item.disposition == "BLOCKED":
            return False
        if len(_word_tokens(item.explanation)) < 7:
            return False
        required_numbers = {
            value for value in item.source_facts if re.fullmatch(r"[\d.,%]+", value)
        }
        audible_numbers: set[str] = set()
        for value in required_numbers:
            normalized = value.rstrip("%").replace(",", ".")
            audible_numbers.add(normalized)
            try:
                number = float(normalized)
                if number.is_integer():
                    audible_numbers.add(str(int(number)))
            except ValueError:
                pass
        if audible_numbers and not any(value in item.explanation for value in audible_numbers):
            return False
        source_tokens = _word_tokens(" ".join([item.title, *item.source_facts]))
        return not source_tokens or bool(source_tokens & _word_tokens(item.explanation))

    def evaluate(
        self,
        content: AudioScriptContent,
        *,
        source_hash: str,
        mode: AudioAdaptationMode,
        transformations: list[AudioTransformation],
    ) -> list[AudioQualityCheck]:
        script_hash = audio_content_hash(content)
        recording = content.clean_recording_text()
        locations = [
            (f"{section.source_chapter_id}:{index}", paragraph)
            for section in content.sections
            for index, paragraph in enumerate(section.recording_paragraphs(), start=1)
        ]

        def check(kind: str, findings: list[AudioQualityFinding]) -> AudioQualityCheck:
            state: AudioCheckState = (
                "BLOCKING"
                if any(item.severity == "BLOCKING" for item in findings)
                else "ATTENTION"
                if findings
                else "PASS"
            )
            return AudioQualityCheck(
                check_kind=kind,
                state=state,
                findings=findings,
                source_hash=source_hash,
                script_hash=script_hash,
            )

        page_findings = [
            AudioQualityFinding(
                code="PAGE_DEPENDENT_REFERENCE",
                location=location,
                detail="Фраза требует визуальной страницы и должна быть переписана для слуха.",
                severity="BLOCKING",
            )
            for location, paragraph in locations
            if self._PAGE_DEPENDENT.search(paragraph)
        ]
        clean_findings: list[AudioQualityFinding] = []
        for location, paragraph in locations:
            if self._TECHNICAL_RESIDUE.search(paragraph) or self._SSML.search(paragraph):
                clean_findings.append(
                    AudioQualityFinding(
                        code="RECORDING_TEXT_RESIDUE",
                        location=location,
                        detail="В тексте осталась разметка или служебная информация.",
                        severity="BLOCKING",
                    )
                )
            if self._RAW_URL.search(paragraph):
                clean_findings.append(
                    AudioQualityFinding(
                        code="RAW_URL_IN_NARRATION",
                        location=location,
                        detail="Сырой URL будет ошибочно прочитан вслух.",
                        severity="BLOCKING",
                    )
                )
            if self._FOOTNOTE_MARKER.search(paragraph):
                clean_findings.append(
                    AudioQualityFinding(
                        code="FOOTNOTE_REQUIRES_AUDIO_ATTRIBUTION",
                        location=location,
                        detail="В чистом тексте остался визуальный маркер сноски.",
                        severity="BLOCKING",
                    )
                )

        visual_findings: list[AudioQualityFinding] = []
        for section in content.sections:
            for item in section.visual_decisions:
                if item.significant and not self._visual_is_substantive(item):
                    visual_findings.append(
                        AudioQualityFinding(
                            code="VISUAL_DEPENDENCY_UNRESOLVED",
                            location=f"{section.source_chapter_id}:{item.object_id}",
                            detail=(
                                "Существенный визуальный материал не получил проверяемого "
                                "аудиообъяснения с сохранением данных и вывода."
                            ),
                            severity="BLOCKING",
                        )
                    )

        long_findings = [
            AudioQualityFinding(
                code="OVERLOADED_SENTENCE_FOR_LISTENING",
                location=location,
                detail="Предложение длиннее 45 слов и требует проверки чтением вслух.",
                severity="ATTENTION",
            )
            for location, paragraph in locations
            for sentence in re.split(r"(?<=[.!?])\s+", paragraph)
            if len(sentence.split()) > 45
        ]
        number_findings = [
            AudioQualityFinding(
                code="NUMBER_OR_SYMBOL_PRONUNCIATION_REVIEW",
                location=location,
                detail="Числа или символы требуют явной проверки произнесения.",
                severity="ATTENTION",
            )
            for location, paragraph in locations
            if re.search(r"\d{2,}|[%€$₽]|\b\d+[.,]\d+\b", paragraph)
        ]
        missing_sections = {
            item.source_unit_id for item in transformations if item.outcome != "ADDED"
        } - {section.source_chapter_id for section in content.sections}
        completeness = [
            AudioQualityFinding(
                code="SOURCE_SECTION_MISSING",
                location=source_id,
                detail="Исходный раздел отсутствует в карте покрытия AudioScript.",
                severity="BLOCKING",
            )
            for source_id in sorted(missing_sections)
        ]
        fidelity = [
            AudioQualityFinding(
                code="MATERIAL_CHANGE_REQUIRES_HUMAN",
                location=item.source_unit_id,
                detail=item.summary,
                severity="ATTENTION",
            )
            for item in transformations
            if item.material and item.outcome in {"OMITTED", "ADDED", "MOVED"}
        ]

        listenability_findings = [
            *page_findings,
            *long_findings,
            AudioQualityFinding(
                code="REAL_LISTENING_REVIEW_REQUIRED",
                location="whole-script",
                detail="Технические проверки не заменяют чтение вслух и оценку человеком.",
                severity="ATTENTION",
            ),
        ]
        fidelity_review = (
            []
            if mode == "AUDIO_NATIVE"
            else [
                AudioQualityFinding(
                    code=(
                        "SOURCE_FIDELITY_HUMAN_REVIEW_REQUIRED"
                        if mode == "SOURCE_FAITHFUL"
                        else "SEMANTIC_FIDELITY_HUMAN_REVIEW_REQUIRED"
                    ),
                    location="whole-script",
                    detail="Смысловую верность exact source snapshot должен подтвердить человек.",
                    severity="ATTENTION",
                )
            ]
        )
        voice_review = [
            AudioQualityFinding(
                code="AUTHOR_VOICE_AUDIO_REVIEW_REQUIRED",
                location="whole-script",
                detail="Сохранение авторского голоса требует редакционного прослушивания.",
                severity="ATTENTION",
            )
        ]
        pronunciation_review = (
            [
                AudioQualityFinding(
                    code="PRONUNCIATION_LEDGER_REVIEW_REQUIRED",
                    location="whole-script",
                    detail="Найденные имена, термины или сокращения требуют проверки произношения.",
                    severity="ATTENTION",
                )
            ]
            if re.search(r"\b(?:[А-ЯЁA-Z]{2,}|[A-Za-z][A-Za-z0-9.+-]{2,})\b", recording)
            else []
        )
        checks = [
            check("LISTENABILITY", listenability_findings),
            check(
                "SOURCE_FIDELITY",
                [*fidelity, *fidelity_review] if mode == "SOURCE_FAITHFUL" else [],
            ),
            check(
                "SEMANTIC_FIDELITY",
                [*fidelity, *fidelity_review] if mode == "LISTENING_ADAPTATION" else [],
            ),
            check("AUTHOR_VOICE_FOR_AUDIO", voice_review),
            check("VISUAL_DEPENDENCY_RESOLVED", visual_findings),
            check("NUMBER_AND_SYMBOL_PRONUNCIATION", number_findings),
            check("ACRONYM_AND_TERM_PRONUNCIATION", pronunciation_review),
            check("PAGE_DEPENDENT_LANGUAGE", page_findings),
            check(
                "AUDIO_ORIENTATION",
                [
                    AudioQualityFinding(
                        code="AUDIO_ORIENTATION_HUMAN_REVIEW_REQUIRED",
                        location="whole-script",
                        detail="Переходы и повторная ориентация требуют проверки слушателем.",
                        severity="ATTENTION",
                    )
                ],
            ),
            check(
                "AUDIO_REDUNDANCY",
                [
                    AudioQualityFinding(
                        code="AUDIO_REDUNDANCY_HUMAN_REVIEW_REQUIRED",
                        location="whole-script",
                        detail="Полезные повторы нужно отличить от механической избыточности.",
                        severity="ATTENTION",
                    )
                ],
            ),
            check("CLEAN_RECORDING_TEXT", clean_findings),
            check("AUDIO_COMPLETENESS", completeness),
        ]
        return checks

    def discover_pronunciation(self, content: AudioScriptContent) -> list[PronunciationEntry]:
        recording = content.clean_recording_text()
        entries: dict[str, PronunciationEntry] = {}

        def add(term: str, category: PronunciationCategory, origin: str) -> None:
            clean = term.strip(".,:;!?()[]{}«»\"'")
            if len(clean) < 2:
                return
            entries.setdefault(
                clean.casefold(),
                PronunciationEntry(term=clean, category=category, origin=origin),
            )

        for term in re.findall(r"\b[А-ЯЁA-Z]{2,}(?:[-–][А-ЯЁA-Z0-9]+)*\b", recording):
            add(term, "ACRONYM", "automatic: uppercase abbreviation")
        for term in re.findall(r"\b[A-Za-z][A-Za-z0-9.+-]{2,}\b", recording):
            add(term, "FOREIGN", "automatic: Latin-script term")
        for term in re.findall(r"\b[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)+\b", recording):
            add(term, "PERSON", "automatic: capitalized name candidate")
        for term in re.findall(r"\b[А-Яа-яЁё-]+\b", recording):
            lowered = term.casefold()
            if lowered in self._AMBIGUOUS:
                add(term, "AMBIGUOUS_STRESS", "automatic: ambiguous-stress lexicon")
            elif lowered in self._PROFESSIONAL:
                add(term, "PROFESSIONAL_TERM", "automatic: professional-term lexicon")
        return sorted(entries.values(), key=lambda item: item.term.casefold())

    def content_from_master(
        self,
        master: Any,
        *,
        adaptation_mode: AudioAdaptationMode,
        adapted_chapters: dict[str, str] | None = None,
    ) -> tuple[AudioScriptContent, list[AudioTransformation]]:
        """Bind edited prose and visual dispositions to one exact master-shaped snapshot.

        For a derived audio edition, callers must provide real chapter-level audio-editorial
        output. Falling back to the source paragraphs would recreate the forbidden mechanical
        export. AUDIO_NATIVE is the sole no-rewrite path because its Literary Master was authored
        and approved for listening from the beginning.
        """
        if adaptation_mode != "AUDIO_NATIVE" and adapted_chapters is None:
            raise AudioScriptGateError(
                "derived audio editions require explicit audio-editorial chapter output"
            )
        sections: list[AudioScriptSection] = []
        transformations: list[AudioTransformation] = []
        for chapter in master.chapters:
            if adaptation_mode == "AUDIO_NATIVE":
                paragraphs = list(chapter.paragraphs)
                outcome: Literal["PRESERVED", "REWRITTEN"] = "PRESERVED"
                summary = (
                    "Literary Master was authored and approved for listening; no redundant rewrite."
                )
            else:
                edited = (adapted_chapters or {}).get(chapter.chapter_id, "").strip()
                if not edited:
                    raise AudioScriptGateError(
                        f"audio-editorial output missing for chapter {chapter.chapter_id}"
                    )
                paragraphs = [
                    value.strip()
                    for value in edited.replace("\r\n", "\n").split("\n\n")
                    if value.strip()
                ]
                outcome = "REWRITTEN"
                summary = "Chapter rewritten for one-pass listening while the exact source remains immutable."
            decisions: list[AudioVisualDecision] = []
            for table in chapter.tables:
                facts = [*table.headers, *(cell for row in table.rows for cell in row)]
                decisions.append(
                    AudioVisualDecision(
                        object_id=table.object_id,
                        kind="TABLE",
                        title=table.title,
                        disposition=(
                            "AUDIO_EXPLANATION" if table.audio_equivalent.strip() else "BLOCKED"
                        ),
                        placement_after_paragraph=(
                            table.placement_after_paragraph
                            if table.placement_after_paragraph is not None
                            else len(paragraphs)
                        ),
                        explanation=table.audio_equivalent.strip(),
                        source_facts=facts,
                    )
                )
            for visual in chapter.visuals:
                facts = [
                    visual.caption,
                    visual.alt_text,
                    *(str(value) for pair in visual.data for value in pair),
                ]
                decisions.append(
                    AudioVisualDecision(
                        object_id=visual.object_id,
                        kind=visual.kind,
                        title=visual.title,
                        disposition=(
                            "AUDIO_EXPLANATION" if visual.audio_equivalent.strip() else "BLOCKED"
                        ),
                        placement_after_paragraph=(
                            visual.placement_after_paragraph
                            if visual.placement_after_paragraph is not None
                            else len(paragraphs)
                        ),
                        explanation=visual.audio_equivalent.strip(),
                        source_facts=facts,
                    )
                )
            sections.append(
                AudioScriptSection(
                    source_chapter_id=chapter.chapter_id,
                    title=chapter.title,
                    paragraphs=paragraphs,
                    visual_decisions=decisions,
                )
            )
            transformations.append(
                AudioTransformation(
                    source_unit_id=chapter.chapter_id,
                    outcome=outcome,
                    summary=summary,
                )
            )
        return (
            AudioScriptContent(
                title=master.title,
                author=master.author,
                language=master.language,
                sections=sections,
            ),
            transformations,
        )

    def create_proposal(
        self,
        book_id: str,
        *,
        source_kind: Literal["LITERARY_MASTER", "IMPORTED_SOURCE"],
        source_identity: str,
        source_hash: str,
        adaptation_mode: AudioAdaptationMode,
        content: AudioScriptContent,
        transformations: list[AudioTransformation],
        provenance: dict[str, Any],
    ) -> AudioScriptView:
        if len(source_hash) != 64:
            raise AudioScriptGateError("AudioScript requires the exact 64-character source hash")
        script_hash = audio_content_hash(content)
        checks = self.evaluate(
            content,
            source_hash=source_hash,
            mode=adaptation_mode,
            transformations=transformations,
        )
        pronunciation = self.discover_pronunciation(content)
        engine = self._engine(book_id)
        now = utc_now()
        audio_script_id = new_ulid()
        try:
            with engine.begin() as connection:
                version = int(
                    connection.execute(
                        text(
                            "SELECT COALESCE(MAX(version),0)+1 FROM audio_scripts "
                            "WHERE book_id=:book_id"
                        ),
                        {"book_id": book_id},
                    ).scalar_one()
                )
                connection.execute(
                    text(
                        "INSERT INTO audio_scripts(audio_script_id,book_id,source_kind,"
                        "source_identity,source_hash,adaptation_mode,version,status,content_json,"
                        "content_hash,transformation_json,provenance_json,approval_json,created_at,"
                        "updated_at) VALUES (:audio_script_id,:book_id,:source_kind,:source_identity,"
                        ":source_hash,:adaptation_mode,:version,'PROPOSED',:content_json,:content_hash,"
                        ":transformation_json,:provenance_json,NULL,:created_at,:updated_at)"
                    ),
                    {
                        "audio_script_id": audio_script_id,
                        "book_id": book_id,
                        "source_kind": source_kind,
                        "source_identity": source_identity,
                        "source_hash": source_hash,
                        "adaptation_mode": adaptation_mode,
                        "version": version,
                        "content_json": canonical_json(content.model_dump(mode="json")),
                        "content_hash": script_hash,
                        "transformation_json": json.dumps(
                            [item.model_dump(mode="json") for item in transformations],
                            ensure_ascii=False,
                            sort_keys=True,
                            separators=(",", ":"),
                        ),
                        "provenance_json": canonical_json(cast(Any, provenance)),
                        "created_at": now,
                        "updated_at": now,
                    },
                )
                for item in checks:
                    connection.execute(
                        text(
                            "INSERT INTO audio_script_quality_checks(check_id,audio_script_id,"
                            "source_hash,script_hash,check_kind,state,findings_json,evaluator_kind,"
                            "created_at) VALUES (:check_id,:audio_script_id,:source_hash,:script_hash,"
                            ":check_kind,:state,:findings_json,:evaluator_kind,:created_at)"
                        ),
                        {
                            "check_id": new_ulid(),
                            "audio_script_id": audio_script_id,
                            "source_hash": source_hash,
                            "script_hash": script_hash,
                            "check_kind": item.check_kind,
                            "state": item.state,
                            "findings_json": json.dumps(
                                [finding.model_dump(mode="json") for finding in item.findings],
                                ensure_ascii=False,
                                sort_keys=True,
                                separators=(",", ":"),
                            ),
                            "evaluator_kind": item.evaluator_kind,
                            "created_at": now,
                        },
                    )
                for pronunciation_item in pronunciation:
                    connection.execute(
                        text(
                            "INSERT INTO audio_pronunciation_entries(entry_id,audio_script_id,term,"
                            "category,recommendation,status,origin,created_at) VALUES (:entry_id,"
                            ":audio_script_id,:term,:category,:recommendation,:status,:origin,:created_at)"
                        ),
                        {
                            "entry_id": new_ulid(),
                            "audio_script_id": audio_script_id,
                            **pronunciation_item.model_dump(mode="python"),
                            "created_at": now,
                        },
                    )
        finally:
            engine.dispose()
        return self.get(book_id, audio_script_id)

    def _from_row(
        self,
        row: Any,
        checks: list[Any],
        pronunciation: list[Any],
        *,
        current_source_hash: str | None = None,
    ) -> AudioScriptView:
        return AudioScriptView(
            audio_script_id=str(row["audio_script_id"]),
            book_id=str(row["book_id"]),
            source_kind=cast(Any, str(row["source_kind"])),
            source_identity=str(row["source_identity"]),
            source_hash=str(row["source_hash"]),
            adaptation_mode=cast(Any, str(row["adaptation_mode"])),
            version=int(row["version"]),
            status=cast(Any, str(row["status"])),
            content=AudioScriptContent.model_validate_json(str(row["content_json"])),
            content_hash=str(row["content_hash"]),
            transformations=[
                AudioTransformation.model_validate(item)
                for item in json.loads(str(row["transformation_json"]))
            ],
            provenance=cast(dict[str, Any], json.loads(str(row["provenance_json"]))),
            approval=(
                cast(dict[str, Any], json.loads(str(row["approval_json"])))
                if row["approval_json"] is not None
                else None
            ),
            quality_checks=[
                AudioQualityCheck(
                    check_kind=str(item["check_kind"]),
                    state=cast(Any, str(item["state"])),
                    findings=[
                        AudioQualityFinding.model_validate(finding)
                        for finding in json.loads(str(item["findings_json"]))
                    ],
                    source_hash=str(item["source_hash"]),
                    script_hash=str(item["script_hash"]),
                    evaluator_kind=cast(Any, str(item["evaluator_kind"])),
                )
                for item in checks
            ],
            pronunciation_entries=[
                PronunciationEntry(
                    term=str(item["term"]),
                    category=cast(Any, str(item["category"])),
                    recommendation=(
                        str(item["recommendation"]) if item["recommendation"] is not None else None
                    ),
                    status=cast(Any, str(item["status"])),
                    origin=str(item["origin"]),
                )
                for item in pronunciation
            ],
            stale_against_source=(
                current_source_hash is not None and current_source_hash != str(row["source_hash"])
            ),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )

    def get(
        self,
        book_id: str,
        audio_script_id: str,
        *,
        current_source_hash: str | None = None,
    ) -> AudioScriptView:
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                row = (
                    connection.execute(
                        text(
                            "SELECT * FROM audio_scripts WHERE book_id=:book_id "
                            "AND audio_script_id=:audio_script_id"
                        ),
                        {"book_id": book_id, "audio_script_id": audio_script_id},
                    )
                    .mappings()
                    .one_or_none()
                )
                if row is None:
                    raise AudioScriptError(f"AudioScript not found: {audio_script_id}")
                resolved_source_hash = current_source_hash
                if resolved_source_hash is None and str(row["source_kind"]) == "LITERARY_MASTER":
                    latest_master_hash = connection.execute(
                        text(
                            "SELECT manifest_hash FROM literary_masters WHERE book_id=:book_id "
                            "ORDER BY created_at DESC,master_id DESC LIMIT 1"
                        ),
                        {"book_id": book_id},
                    ).scalar_one_or_none()
                    resolved_source_hash = (
                        str(latest_master_hash) if latest_master_hash is not None else None
                    )
                elif resolved_source_hash is None and str(row["source_kind"]) == "IMPORTED_SOURCE":
                    latest_import_hash = connection.execute(
                        text(
                            "SELECT source_hash FROM audio_scripts WHERE book_id=:book_id "
                            "AND source_kind='IMPORTED_SOURCE' "
                            "ORDER BY version DESC LIMIT 1"
                        ),
                        {"book_id": book_id},
                    ).scalar_one_or_none()
                    resolved_source_hash = (
                        str(latest_import_hash) if latest_import_hash is not None else None
                    )
                checks = list(
                    connection.execute(
                        text(
                            "SELECT * FROM audio_script_quality_checks WHERE "
                            "audio_script_id=:audio_script_id ORDER BY check_kind"
                        ),
                        {"audio_script_id": audio_script_id},
                    ).mappings()
                )
                pronunciation = list(
                    connection.execute(
                        text(
                            "SELECT * FROM audio_pronunciation_entries WHERE "
                            "audio_script_id=:audio_script_id ORDER BY lower(term),term"
                        ),
                        {"audio_script_id": audio_script_id},
                    ).mappings()
                )
            return self._from_row(
                row,
                checks,
                pronunciation,
                current_source_hash=resolved_source_hash,
            )
        finally:
            engine.dispose()

    def list_scripts(
        self, book_id: str, *, current_source_hash: str | None = None
    ) -> list[AudioScriptView]:
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                ids = list(
                    connection.execute(
                        text(
                            "SELECT audio_script_id FROM audio_scripts WHERE book_id=:book_id "
                            "ORDER BY version DESC"
                        ),
                        {"book_id": book_id},
                    ).scalars()
                )
        finally:
            engine.dispose()
        return [
            self.get(book_id, str(item), current_source_hash=current_source_hash) for item in ids
        ]

    def revise_by_human(
        self,
        book_id: str,
        audio_script_id: str,
        *,
        content: AudioScriptContent,
        human_actor: str,
        change_summary: str,
    ) -> AudioScriptView:
        current = self.get(book_id, audio_script_id)
        if current.status != "PROPOSED":
            raise AudioScriptGateError("only a proposed AudioScript can be revised")
        if not human_actor.strip():
            raise AudioScriptGateError("human revision requires an identified human actor")
        if not change_summary.strip():
            raise AudioScriptGateError("human revision requires a change summary")
        if (
            content.title != current.content.title
            or content.author != current.content.author
            or content.language != current.content.language
        ):
            raise AudioScriptGateError(
                "audio revision cannot silently change title, author, or language"
            )

        def structure(value: AudioScriptContent) -> list[tuple[str, list[tuple[object, ...]]]]:
            return [
                (
                    section.source_chapter_id,
                    [
                        (
                            visual.object_id,
                            visual.kind,
                            visual.title,
                            visual.significant,
                            visual.placement_after_paragraph,
                            tuple(visual.source_facts),
                        )
                        for visual in section.visual_decisions
                    ],
                )
                for section in value.sections
            ]

        current_sections = structure(current.content)
        revised_sections = structure(content)
        if revised_sections != current_sections:
            raise AudioScriptGateError(
                "audio revision must preserve source section order and immutable visual metadata"
            )
        revised = self.create_proposal(
            book_id,
            source_kind=current.source_kind,
            source_identity=current.source_identity,
            source_hash=current.source_hash,
            adaptation_mode=current.adaptation_mode,
            content=content,
            transformations=[
                AudioTransformation(
                    source_unit_id=section.source_chapter_id,
                    outcome="REWRITTEN",
                    summary=change_summary.strip(),
                    material=True,
                    human_review_required=True,
                )
                for section in content.sections
            ],
            provenance={
                **current.provenance,
                "revision_operation": "HUMAN_AUDIO_SCRIPT_REVISION",
                "parent_audio_script_id": current.audio_script_id,
                "parent_audio_script_hash": current.content_hash,
                "revision_actor": human_actor.strip(),
                "revision_actor_kind": "HUMAN",
                "change_summary": change_summary.strip(),
            },
        )
        engine = self._engine(book_id)
        try:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "UPDATE audio_scripts SET status='SUPERSEDED',updated_at=:updated_at "
                        "WHERE audio_script_id=:audio_script_id AND status='PROPOSED'"
                    ),
                    {
                        "audio_script_id": current.audio_script_id,
                        "updated_at": utc_now(),
                    },
                )
        finally:
            engine.dispose()
        return revised

    def approve(
        self,
        book_id: str,
        audio_script_id: str,
        *,
        human_actor: str,
        accepted_attention_codes: list[str] | None = None,
    ) -> AudioScriptView:
        current = self.get(book_id, audio_script_id)
        if current.status != "PROPOSED":
            raise AudioScriptGateError("only a proposed AudioScript can be human-approved")
        blocking = [item for item in current.quality_checks if item.state == "BLOCKING"]
        if blocking:
            raise AudioScriptGateError(
                "AudioScript has blocking checks: "
                + ", ".join(item.check_kind for item in blocking)
            )
        if not human_actor.strip():
            raise AudioScriptGateError("human approval requires an identified human actor")
        attention_codes = {
            finding.code
            for item in current.quality_checks
            for finding in item.findings
            if finding.severity == "ATTENTION"
        }
        accepted: set[str] = set(accepted_attention_codes or [])
        if attention_codes - accepted:
            raise AudioScriptGateError(
                "human must explicitly disposition every ATTENTION finding before approval"
            )
        approval = {
            "actor": human_actor,
            "actor_kind": "HUMAN",
            "approved_at": utc_now(),
            "source_hash": current.source_hash,
            "script_hash": current.content_hash,
            "accepted_attention_codes": sorted(accepted),
        }
        engine = self._engine(book_id)
        try:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "UPDATE audio_scripts SET status='APPROVED',approval_json=:approval_json,"
                        "updated_at=:updated_at WHERE audio_script_id=:audio_script_id "
                        "AND status='PROPOSED'"
                    ),
                    {
                        "approval_json": canonical_json(cast(Any, approval)),
                        "updated_at": approval["approved_at"],
                        "audio_script_id": audio_script_id,
                    },
                )
        finally:
            engine.dispose()
        return self.get(book_id, audio_script_id)

    @staticmethod
    def pronunciation_text(entries: list[PronunciationEntry]) -> str:
        header = "Термин\tКатегория\tПроизношение\tСтатус\tИсточник рекомендации\n"
        rows = [
            "\t".join(
                (
                    item.term,
                    item.category,
                    item.recommendation or "",
                    item.status,
                    item.origin,
                )
            )
            for item in entries
        ]
        return header + "\n".join(rows) + ("\n" if rows else "")

    def record_handoff(
        self,
        book_id: str,
        script: AudioScriptView,
        *,
        text_relative_path: str,
        text_payload: bytes,
    ) -> dict[str, Any]:
        if not script.ready_for_export:
            raise AudioScriptGateError(
                "only a current human-approved AudioScript may be handed off"
            )
        text_hash = hashlib.sha256(text_payload).hexdigest()
        manifest = {
            "handoff_version": "book-os-audiobook-handoff.v2",
            "book_id": book_id,
            "audio_script_id": script.audio_script_id,
            "audio_script_version": script.version,
            "audio_script_hash": script.content_hash,
            "source_kind": script.source_kind,
            "source_identity": script.source_identity,
            "source_hash": script.source_hash,
            "adaptation_mode": script.adaptation_mode,
            "authority_status": script.status,
            "approval": script.approval,
            "quality_checks": [item.model_dump(mode="json") for item in script.quality_checks],
            "transformation_map": [item.model_dump(mode="json") for item in script.transformations],
            "pronunciation_ledger": [
                item.model_dump(mode="json") for item in script.pronunciation_entries
            ],
            "recording_text": {
                "encoding": "UTF-8",
                "relative_path": text_relative_path,
                "content_hash": text_hash,
            },
            "created_at": utc_now(),
            "source_system": "BOOK OS",
        }
        engine = self._engine(book_id)
        try:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT OR REPLACE INTO audio_production_handoffs(handoff_id,"
                        "audio_script_id,script_hash,manifest_json,text_relative_path,"
                        "text_content_hash,created_at) VALUES (:handoff_id,:audio_script_id,"
                        ":script_hash,:manifest_json,:text_relative_path,:text_content_hash,"
                        ":created_at)"
                    ),
                    {
                        "handoff_id": new_ulid(),
                        "audio_script_id": script.audio_script_id,
                        "script_hash": script.content_hash,
                        "manifest_json": canonical_json(cast(Any, manifest)),
                        "text_relative_path": text_relative_path,
                        "text_content_hash": text_hash,
                        "created_at": manifest["created_at"],
                    },
                )
        finally:
            engine.dispose()
        return manifest
