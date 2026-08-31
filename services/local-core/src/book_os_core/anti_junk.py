from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Literal

from pydantic import BaseModel, Field

from .authority import new_ulid
from .authority_types import utc_now

AntiJunkKind = Literal["BANNED_TEMPLATE", "CONTEXT_REVIEW"]
AntiJunkSource = Literal["SYSTEM", "USER"]


class AntiJunkEntry(BaseModel):
    entry_id: str
    value: str
    kind: AntiJunkKind
    source: AntiJunkSource
    created_at: str | None = None


class AntiJunkCreateRequest(BaseModel):
    value: str = Field(min_length=1, max_length=300)
    kind: AntiJunkKind = "BANNED_TEMPLATE"


class AntiJunkError(RuntimeError):
    pass


_NEGATIVE_FIRST_PRINCIPLE = (
    "Запрещённый нейросетевой приём: сначала искусственно объявлять, чем текст, книга, "
    "идея или явление НЕ является, вместо того чтобы сразу сформулировать точную мысль. "
    "Если мысль можно сказать прямо, начинай с неё; не создавай отрицательный тезис ради "
    "декоративного контраста."
)

_SYSTEM_VALUES: tuple[tuple[str, AntiJunkKind], ...] = (
    ("эта книга не о том", "BANNED_TEMPLATE"),
    ("эта книга не о", "BANNED_TEMPLATE"),
    ("эта книга не про", "BANNED_TEMPLATE"),
    ("это не про", "BANNED_TEMPLATE"),
    ("это про", "BANNED_TEMPLATE"),
    ("речь не о", "BANNED_TEMPLATE"),
    ("здесь речь не о", "BANNED_TEMPLATE"),
    ("дело не в", "BANNED_TEMPLATE"),
    ("без ручного управления", "BANNED_TEMPLATE"),
    ("без хаоса", "BANNED_TEMPLATE"),
    ("без давления", "BANNED_TEMPLATE"),
    ("без суеты", "BANNED_TEMPLATE"),
    ("без лишней суеты", "BANNED_TEMPLATE"),
    ("без лишнего шума", "BANNED_TEMPLATE"),
    ("без перегруза", "BANNED_TEMPLATE"),
    ("без лишней теории", "BANNED_TEMPLATE"),
    ("без потери контроля", "BANNED_TEMPLATE"),
    ("без стресса", "BANNED_TEMPLATE"),
    ("без выгорания", "BANNED_TEMPLATE"),
    ("без страха", "BANNED_TEMPLATE"),
    ("без усилий", "BANNED_TEMPLATE"),
    ("не обязан", "CONTEXT_REVIEW"),
    ("шум", "CONTEXT_REVIEW"),
    ("информационный шум", "BANNED_TEMPLATE"),
    ("отделить шум от сигнала", "BANNED_TEMPLATE"),
    ("иллюзия", "CONTEXT_REVIEW"),
    ("иллюзии контроля", "BANNED_TEMPLATE"),
    ("иллюзия выбора", "BANNED_TEMPLATE"),
    ("иллюзия безопасности", "BANNED_TEMPLATE"),
    ("волшебство", "CONTEXT_REVIEW"),
    ("магия", "CONTEXT_REVIEW"),
    ("чудеса", "CONTEXT_REVIEW"),
    ("волшебная таблетка", "BANNED_TEMPLATE"),
    ("магическая кнопка", "BANNED_TEMPLATE"),
    ("в тишине", "BANNED_TEMPLATE"),
    ("тихие смыслы", "BANNED_TEMPLATE"),
    ("в суете", "CONTEXT_REVIEW"),
    ("суетиться", "CONTEXT_REVIEW"),
    ("мир меняется", "BANNED_TEMPLATE"),
    ("мир быстро меняется", "BANNED_TEMPLATE"),
    ("скорость изменений", "BANNED_TEMPLATE"),
    ("в быстро меняющемся мире", "BANNED_TEMPLATE"),
    ("в современном мире", "BANNED_TEMPLATE"),
    ("погрузимся", "BANNED_TEMPLATE"),
    ("давайте погрузимся", "BANNED_TEMPLATE"),
    ("давайте разберёмся", "BANNED_TEMPLATE"),
    ("разберёмся, почему", "BANNED_TEMPLATE"),
    ("попробуем разобраться", "BANNED_TEMPLATE"),
    ("давайте посмотрим", "BANNED_TEMPLATE"),
    ("звучать", "CONTEXT_REVIEW"),
    ("опора", "CONTEXT_REVIEW"),
    ("важно понимать", "BANNED_TEMPLATE"),
    ("стоит отметить", "BANNED_TEMPLATE"),
    ("в конечном итоге", "BANNED_TEMPLATE"),
    ("другими словами", "BANNED_TEMPLATE"),
    ("на самом деле", "CONTEXT_REVIEW"),
    ("важно помнить", "BANNED_TEMPLATE"),
    ("следует понимать", "BANNED_TEMPLATE"),
    ("в этом контексте", "BANNED_TEMPLATE"),
)

_NEGATIVE_FIRST_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bэта\s+книга\s+не\s+(?:о|про)\b", re.IGNORECASE),
    re.compile(r"\b(?:это|речь|дело)\s+не\b[^.!?\n]{1,120}\b(?:а|но)\b", re.IGNORECASE),
    re.compile(r"\bне\b[^.!?\n]{1,90}\bа\b", re.IGNORECASE),
)


def _normalize(value: str) -> str:
    return " ".join(value.strip().casefold().split())


class AntiJunkService:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.path = data_dir / "prose-anti-junk-user.json"

    @staticmethod
    def system_entries() -> list[AntiJunkEntry]:
        seen: set[str] = set()
        entries: list[AntiJunkEntry] = []
        for index, (value, kind) in enumerate(_SYSTEM_VALUES, start=1):
            normalized = _normalize(value)
            if normalized in seen:
                continue
            seen.add(normalized)
            entries.append(
                AntiJunkEntry(
                    entry_id=f"SYSTEM-{index:03d}",
                    value=value,
                    kind=kind,
                    source="SYSTEM",
                )
            )
        return entries

    def _user_entries(self) -> list[AntiJunkEntry]:
        if not self.path.is_file():
            return []
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise AntiJunkError("user anti-junk dictionary is unreadable") from exc
        if not isinstance(payload, list):
            raise AntiJunkError("user anti-junk dictionary must contain a list")
        return [AntiJunkEntry.model_validate(item) for item in payload]

    def _write_user_entries(self, entries: list[AntiJunkEntry]) -> None:
        temp = self.path.with_suffix(".tmp")
        temp.write_text(
            json.dumps(
                [entry.model_dump(mode="json") for entry in entries],
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        temp.replace(self.path)

    def list_entries(self) -> list[AntiJunkEntry]:
        return self.system_entries() + self._user_entries()

    def add(self, request: AntiJunkCreateRequest) -> AntiJunkEntry:
        value = " ".join(request.value.strip().split())
        normalized = _normalize(value)
        if not normalized:
            raise AntiJunkError("anti-junk entry must not be blank")
        existing = self.list_entries()
        duplicate = next(
            (entry for entry in existing if _normalize(entry.value) == normalized), None
        )
        if duplicate is not None:
            return duplicate
        entry = AntiJunkEntry(
            entry_id=new_ulid(),
            value=value,
            kind=request.kind,
            source="USER",
            created_at=utc_now(),
        )
        users = self._user_entries()
        users.append(entry)
        users.sort(key=lambda item: (item.value.casefold(), item.entry_id))
        self._write_user_entries(users)
        return entry

    def remove(self, entry_id: str) -> None:
        users = self._user_entries()
        retained = [entry for entry in users if entry.entry_id != entry_id]
        if len(retained) == len(users):
            raise AntiJunkError("user anti-junk entry not found")
        self._write_user_entries(retained)

    def generation_constraints(self) -> dict[str, object]:
        entries = self.list_entries()
        return {
            "principle": _NEGATIVE_FIRST_PRINCIPLE,
            "banned_templates": [
                entry.value for entry in entries if entry.kind == "BANNED_TEMPLATE"
            ],
            "context_review_terms": [
                entry.value for entry in entries if entry.kind == "CONTEXT_REVIEW"
            ],
            "rule": (
                "Avoid banned templates in generated prose. Context-review terms are not globally "
                "forbidden, but prefer a more concrete formulation unless the literal meaning is necessary."
            ),
        }

    def scan(self, text: str) -> list[dict[str, object]]:
        findings: list[dict[str, object]] = []
        lowered = text.casefold()
        seen: set[tuple[str, int, int]] = set()
        for entry in self.list_entries():
            needle = entry.value.casefold()
            start = 0
            while needle:
                index = lowered.find(needle, start)
                if index < 0:
                    break
                key = (entry.entry_id, index, index + len(needle))
                if key not in seen:
                    seen.add(key)
                    findings.append(
                        {
                            "entry_id": entry.entry_id,
                            "value": entry.value,
                            "kind": entry.kind,
                            "source": entry.source,
                            "start": index,
                            "end": index + len(needle),
                            "match": text[index : index + len(needle)],
                        }
                    )
                start = index + max(1, len(needle))
        for pattern_index, pattern in enumerate(_NEGATIVE_FIRST_PATTERNS, start=1):
            for match in pattern.finditer(text):
                findings.append(
                    {
                        "entry_id": f"PATTERN-NEGATIVE-FIRST-{pattern_index}",
                        "value": "NEGATIVE_FIRST_FRAMING",
                        "kind": "BANNED_TEMPLATE",
                        "source": "SYSTEM",
                        "start": match.start(),
                        "end": match.end(),
                        "match": match.group(0),
                    }
                )
        return sorted(findings, key=lambda item: (int(item["start"]), str(item["entry_id"])))
