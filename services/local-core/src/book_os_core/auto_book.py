from __future__ import annotations

from html import escape as html_escape
import json
from pathlib import Path
from typing import Any, Literal, cast
from zipfile import ZIP_DEFLATED, ZipFile

from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.engine import Engine

from .authority import AuthorityService, InvalidAuthorityOperation, new_ulid
from .authority_types import JSONValue, utc_now
from .book_context import (
    BookContextService,
    BookContextUpdateRequest,
    ProfileCreateRequest,
)
from .context_planning import ContextAwarePlanningService
from .drafting import DraftSectionRequest, DraftingService
from .model_gateway import ModelGateway, ReasoningEffort
from .model_routing import ModelRoutingService, RoutingChoice
from .planning import (
    ArchitecturePlanningRequest,
    BookContractPlanningRequest,
    ChapterContractPlanningRequest,
    PlanningProposalView,
)
from .projects import DocumentView, ProjectService, ProjectView

AutoBookChoice = Literal["AUTO", "ASTRA_MEDIUM", "ASTRA_HIGH", "ASTRA_XHIGH", "SOL"]
AutoBookStatus = Literal["RUNNING", "DONE", "FAILED", "STOPPED"]
AutoBookPhase = Literal[
    "BOOK_CONTRACT",
    "APPROVE_BOOK_CONTRACT",
    "ARCHITECTURE",
    "APPROVE_ARCHITECTURE",
    "CHAPTER_CONTRACT",
    "APPROVE_CHAPTER",
    "CHAPTER_DRAFT",
    "EXPORT",
    "DONE",
]


class AutoBookError(RuntimeError):
    pass


class AutoBookGateError(AutoBookError):
    pass


class AutoBookNotFound(AutoBookError):
    pass


class AutoBookStartRequest(BaseModel):
    idea: str = Field(min_length=3, max_length=6000)
    reader_hint: str = Field(default="", max_length=4000)
    author_name: str = Field(default="", max_length=300)
    target_characters: int = Field(default=180_000, ge=4_000, le=2_000_000)
    model_choice: AutoBookChoice = "ASTRA_HIGH"
    max_cost_usd_per_request: float = Field(default=1.0, gt=0, le=20)
    max_total_cost_usd: float = Field(default=25.0, gt=0, le=500)
    max_requests: int = Field(default=40, ge=1, le=200)
    prepare_litres_docx: bool = True
    owner_authorizes_auto_progress: Literal[True]


class AutoBookRunView(BaseModel):
    run_id: str
    book_id: str
    status: AutoBookStatus
    phase: AutoBookPhase
    idea: str
    reader_hint: str
    model_choice: AutoBookChoice
    max_cost_usd_per_request: float
    max_total_cost_usd: float
    max_requests: int
    prepare_litres_docx: bool
    requests_used: int = 0
    authorized_cost_usd: float = 0.0
    current_chapter_id: str | None = None
    current_chapter_ordinal: int | None = None
    last_action: str = ""
    output_path: str | None = None
    error: str | None = None
    started_at: str
    updated_at: str


class _DelegatedProjectService(ProjectService):
    """ProjectService that records one owner authorization for an Auto Book run.

    The AI still cannot approve authority. The owner is the human actor; the audit
    reason records that the human approval was delegated in advance to this exact run.
    """

    def __init__(self, data_dir: Path, run_id: str) -> None:
        super().__init__(data_dir)
        self.run_id = run_id

    def _approve_entity(self, engine: Engine, entity_id: str) -> DocumentView:
        authority = AuthorityService(engine)
        head = authority.get_head(entity_id)
        if head.status == "LOCKED":
            raise InvalidAuthorityOperation("locked authority cannot be replaced in Auto Book")
        with engine.connect() as connection:
            working = connection.execute(
                text("SELECT revision_id FROM working_revisions WHERE entity_id=:entity_id"),
                {"entity_id": entity_id},
            ).scalar_one_or_none()
        source_revision_id = cast(str, working) if working is not None else head.revision_id
        source = authority.get_revision(source_revision_id)
        reason = f"Owner pre-authorized automatic progress for Auto Book run {self.run_id}"
        proposal_id = authority.create_proposal(
            entity_id=entity_id,
            base_revision_id=head.revision_id,
            base_revision_hash=head.revision_hash,
            proposed_payload=cast(dict[str, JSONValue], source["content"]),
            schema_name=cast(str, source["schema_name"]),
            schema_version=cast(str, source["schema_version"]),
            rationale=reason,
            actor="owner",
            origin="HUMAN_WRITTEN",
            task_id=f"auto-book:{self.run_id}",
            input_revision_ids=(source_revision_id,),
        )
        authority.accept_proposal(
            proposal_id,
            actor="owner",
            actor_kind="HUMAN",
            reason=reason,
            gates={
                "owner_auto_book_authorization": True,
                "per_step_human_review": False,
                "auto_book_run_id": self.run_id,
            },
        )
        with engine.begin() as connection:
            connection.execute(
                text("DELETE FROM working_revisions WHERE entity_id=:entity_id"),
                {"entity_id": entity_id},
            )
        view = self._document_view(engine, authority, entity_id)
        if view is None:
            raise AutoBookError("approved document disappeared")
        return view


class AutoBookService:
    _STATE_FILE = "auto-book-run.json"
    _LITRES_FORBIDDEN = str.maketrans("", "", "ˊˈʻʼˋʹːˌ")

    def __init__(self, data_dir: Path, gateway: ModelGateway) -> None:
        self.data_dir = data_dir
        self.projects = ProjectService(data_dir)
        self.contexts = BookContextService(data_dir)
        self.planning = ContextAwarePlanningService(data_dir, gateway)
        self.drafting = DraftingService(data_dir, gateway)
        self.routing = ModelRoutingService(data_dir)

    def _project_dir(self, book_id: str) -> Path:
        self.projects.get_project(book_id)
        return self.projects.projects_dir / book_id

    def _state_path(self, book_id: str) -> Path:
        return self._project_dir(book_id) / self._STATE_FILE

    def _write(self, state: AutoBookRunView) -> AutoBookRunView:
        state.updated_at = utc_now()
        path = self._state_path(state.book_id)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(state.model_dump(mode="json"), ensure_ascii=False, sort_keys=True, indent=2)
            + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
        return state

    def get(self, book_id: str) -> AutoBookRunView | None:
        path = self._state_path(book_id)
        if not path.exists():
            return None
        try:
            return AutoBookRunView.model_validate_json(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise AutoBookError("Auto Book state is unreadable") from exc

    def _ensure_context(self, book_id: str, request: AutoBookStartRequest) -> None:
        context = self.contexts.get_context(book_id)
        if context.ready_for_planning:
            return

        approved_authors = [
            item
            for item in self.contexts.profiles.list_profiles("AUTHOR")
            if item.status == "APPROVED"
        ]
        requested_name = request.author_name.strip()
        author = (
            next(
                (
                    item
                    for item in approved_authors
                    if item.name.casefold() == requested_name.casefold()
                ),
                None,
            )
            if requested_name
            else None
        )
        if author is None and not requested_name and len(approved_authors) == 1:
            author = approved_authors[0]
        if author is None and requested_name:
            author = self.contexts.profiles.create_profile(
                ProfileCreateRequest(kind="AUTHOR", content={"author_name": requested_name})
            )
            author = self.contexts.profiles.approve_profile(author.profile_id)
        if author is None:
            raise AutoBookGateError(
                "Choose an author/pseudonym for Auto Book "
                "(there is no single approved author to use)"
            )

        approved_styles = [
            item
            for item in self.contexts.profiles.list_profiles("STYLE")
            if item.status == "APPROVED"
            and item.content.get("author_profile_id") in {None, author.profile_id}
        ]
        style = approved_styles[0] if len(approved_styles) == 1 else None
        if style is None:
            style = self.contexts.profiles.create_profile(
                ProfileCreateRequest(
                    kind="STYLE",
                    content={
                        "style_name": f"{author.name} — BOOK OS Auto",
                        "author_profile_id": author.profile_id,
                        "literary_register": "Ясный современный нон-фикшн без канцелярита",
                        "directness": "Прямо и точно, без назидательности",
                        "sentence_paragraph_rhythm": (
                            "Естественно варьировать длину предложений и абзацев"
                        ),
                        "evidence_density": "Проверяемые утверждения отделять от авторских выводов",
                        "analytical_depth": "Высокая; объяснять механизм, а не только совет",
                        "practical_instruction_intensity": (
                            "Практика встроена в аргумент, без пустой мотивации"
                        ),
                        "prohibited_patterns": ["пустые повторы", "мета-комментарии о написании"],
                        "benchmark_excerpts": [],
                    },
                )
            )
            style = self.contexts.profiles.approve_profile(style.profile_id)

        self.contexts.save_context(
            book_id,
            BookContextUpdateRequest(
                author_profile_id=author.profile_id,
                style_profile_id=style.profile_id,
                target_characters=request.target_characters,
            ),
        )

    def start(self, book_id: str, request: AutoBookStartRequest) -> AutoBookRunView:
        current = self.get(book_id)
        if current is not None and current.status == "RUNNING":
            raise AutoBookGateError("Auto Book is already running for this book")
        self._ensure_context(book_id, request)
        if request.model_choice == "AUTO":
            # Main author Auto mode must not be silently hijacked by a legacy hidden book pin.
            self.routing.clear_book_pin(book_id)
        if request.max_total_cost_usd < request.max_cost_usd_per_request:
            raise AutoBookGateError(
                "total Auto Book budget must be at least one per-request budget"
            )
        now = utc_now()
        state = AutoBookRunView(
            run_id=new_ulid(),
            book_id=book_id,
            status="RUNNING",
            phase="BOOK_CONTRACT",
            idea=request.idea.strip(),
            reader_hint=request.reader_hint.strip(),
            model_choice=request.model_choice,
            max_cost_usd_per_request=request.max_cost_usd_per_request,
            max_total_cost_usd=request.max_total_cost_usd,
            max_requests=request.max_requests,
            prepare_litres_docx=request.prepare_litres_docx,
            started_at=now,
            updated_at=now,
            last_action="Auto Book authorized by owner",
        )

        # Continue useful existing work instead of forcing the author to restart a book.
        project = self.projects.get_project(book_id)
        if self._approved(project.architecture):
            pending = self._first_pending_chapter(project)
            if pending is None:
                state.phase = "EXPORT"
                state.last_action = "Existing planned chapters are ready for export"
            else:
                self._set_current_chapter(state, project, pending)
                chapter = next(item for item in project.chapters if item.chapter_id == pending)
                if self._approved(chapter.chapter_contract):
                    state.phase = "CHAPTER_DRAFT"
                elif chapter.chapter_contract is not None:
                    state.phase = "APPROVE_CHAPTER"
                else:
                    state.phase = "CHAPTER_CONTRACT"
                state.last_action = f"Continuing existing book from chapter {chapter.ordinal}"
        elif project.architecture is not None and self._approved(project.book_contract):
            state.phase = "APPROVE_ARCHITECTURE"
            state.last_action = "Continuing from existing Architecture draft"
        elif self._approved(project.book_contract):
            state.phase = "ARCHITECTURE"
            state.last_action = "Continuing from approved Book Contract"
        elif project.book_contract is not None:
            state.phase = "APPROVE_BOOK_CONTRACT"
            state.last_action = "Continuing from existing Book Contract draft"

        return self._write(state)

    def stop(self, book_id: str) -> AutoBookRunView:
        state = self._require_state(book_id)
        if state.status == "RUNNING":
            state.status = "STOPPED"
            state.last_action = "Stopped by owner"
            self._write(state)
        return state

    def _require_state(self, book_id: str) -> AutoBookRunView:
        state = self.get(book_id)
        if state is None:
            raise AutoBookNotFound("Auto Book has not been started for this book")
        return state

    @staticmethod
    def _choice(choice: AutoBookChoice) -> tuple[str | None, ReasoningEffort | None, str]:
        if choice == "AUTO":
            return None, None, "AUTO"
        if choice == "ASTRA_MEDIUM":
            return "gpt-6-astra", "medium", "MANUAL"
        if choice == "ASTRA_XHIGH":
            return "gpt-6-astra", "xhigh", "MANUAL"
        if choice == "SOL":
            return "gpt-5.6-sol", None, "MANUAL"
        return "gpt-6-astra", "high", "MANUAL"

    def _remaining_call_cap(self, state: AutoBookRunView) -> float:
        if state.requests_used >= state.max_requests:
            raise AutoBookGateError("Auto Book request limit reached")
        remaining = state.max_total_cost_usd - state.authorized_cost_usd
        cap = min(state.max_cost_usd_per_request, remaining)
        if cap <= 0:
            raise AutoBookGateError("Auto Book total cost authorization is exhausted")
        return cap

    @staticmethod
    def _consume_call(state: AutoBookRunView, cap: float) -> None:
        state.requests_used += 1
        state.authorized_cost_usd = round(state.authorized_cost_usd + cap, 6)

    def _planning_choice(
        self, state: AutoBookRunView, operation: str
    ) -> tuple[RoutingChoice, ReasoningEffort | None]:
        model, effort, mode = self._choice(state.model_choice)
        choice = self.routing.resolve(
            state.book_id,
            operation,
            provider="openai",
            selection_mode=cast(Any, mode),
            selection_scope="OPERATION" if mode == "MANUAL" else None,
            model=model,
        )
        return choice, effort if choice.model == "gpt-6-astra" else None

    def _book_contract(self, state: AutoBookRunView, cap: float) -> PlanningProposalView:
        choice, effort = self._planning_choice(state, "BOOK_CONTRACT_PROPOSAL")
        result = self.planning.propose_book_contract(
            state.book_id,
            BookContractPlanningRequest(
                idea=state.idea,
                reader_hint=state.reader_hint,
                provider=choice.provider,
                model=choice.model,
                reasoning_effort=effort,
                max_output_tokens=2600,
                max_cost_usd=cap,
            ),
        )
        self.routing.record_run(state.book_id, result.run_id, choice)
        return result

    def _architecture(self, state: AutoBookRunView, cap: float) -> PlanningProposalView:
        choice, effort = self._planning_choice(state, "ARCHITECTURE_PROPOSAL")
        result = self.planning.propose_architecture(
            state.book_id,
            ArchitecturePlanningRequest(
                planning_note=(
                    "Auto Book: build the strongest complete architecture "
                    "for the approved book contract."
                ),
                provider=choice.provider,
                model=choice.model,
                reasoning_effort=effort,
                max_output_tokens=5000,
                max_cost_usd=cap,
            ),
        )
        self.routing.record_run(state.book_id, result.run_id, choice)
        return result

    def _chapter_contract(self, state: AutoBookRunView, cap: float) -> PlanningProposalView:
        if state.current_chapter_id is None:
            raise AutoBookError("current chapter is missing")
        choice, effort = self._planning_choice(state, "CHAPTER_CONTRACT_PROPOSAL")
        result = self.planning.propose_chapter_contract(
            state.book_id,
            state.current_chapter_id,
            ChapterContractPlanningRequest(
                planning_note=(
                    "Auto Book: make this chapter distinct, necessary, and non-repetitive."
                ),
                provider=choice.provider,
                model=choice.model,
                reasoning_effort=effort,
                max_output_tokens=3200,
                max_cost_usd=cap,
            ),
        )
        self.routing.record_run(state.book_id, result.run_id, choice)
        return result

    def _draft_chapter(self, state: AutoBookRunView, cap: float) -> None:
        project = self.projects.get_project(state.book_id)
        chapter = next(
            (item for item in project.chapters if item.chapter_id == state.current_chapter_id),
            None,
        )
        if chapter is None:
            raise AutoBookError("current chapter is not in project")
        context = self.contexts.get_context(state.book_id)
        target = context.target_characters or 200_000
        per_chapter = max(8_000, min(45_000, target // max(1, len(project.chapters))))
        model, effort, mode = self._choice(state.model_choice)
        self.drafting.generate_section_draft(
            state.book_id,
            chapter.chapter_id,
            DraftSectionRequest(
                section_objective=(
                    f"Write the complete publication-ready text of chapter {chapter.ordinal}: "
                    f"{chapter.working_title}. Follow the approved chapter contract and "
                    "book context. "
                    f"Aim for about {per_chapter} characters with spaces. Avoid repetition, "
                    "filler, meta-commentary, author instructions, and placeholders. "
                    "Return only coherent book prose."
                ),
                provider="openai",
                model=model,
                selection_mode=cast(Any, mode),
                selection_scope="OPERATION" if mode == "MANUAL" else None,
                reasoning_effort=effort,
                max_output_tokens=12_000,
                max_cost_usd=cap,
            ),
        )

    @staticmethod
    def _approved(document: DocumentView | None) -> bool:
        return document is not None and document.authority_status in {"APPROVED", "LOCKED"}

    def _first_pending_chapter(self, project: ProjectView) -> str | None:
        for chapter in project.chapters:
            drafts = self.drafting.list_drafts(project.book_id, chapter.chapter_id)
            if not self._approved(chapter.chapter_contract) or not drafts:
                return chapter.chapter_id
        return None

    def _set_current_chapter(
        self, state: AutoBookRunView, project: ProjectView, chapter_id: str
    ) -> None:
        chapter = next(item for item in project.chapters if item.chapter_id == chapter_id)
        state.current_chapter_id = chapter.chapter_id
        state.current_chapter_ordinal = chapter.ordinal

    def advance(self, book_id: str) -> AutoBookRunView:
        state = self._require_state(book_id)
        if state.status != "RUNNING":
            return state
        delegated = _DelegatedProjectService(self.data_dir, state.run_id)
        try:
            if state.phase == "BOOK_CONTRACT":
                cap = self._remaining_call_cap(state)
                result = self._book_contract(state, cap)
                self._consume_call(state, cap)
                state.phase = "APPROVE_BOOK_CONTRACT"
                state.last_action = f"Book Contract proposed by {result.model}"

            elif state.phase == "APPROVE_BOOK_CONTRACT":
                delegated.approve_book_contract(book_id)
                state.phase = "ARCHITECTURE"
                state.last_action = "Book Contract accepted under owner Auto Book authorization"

            elif state.phase == "ARCHITECTURE":
                cap = self._remaining_call_cap(state)
                result = self._architecture(state, cap)
                self._consume_call(state, cap)
                state.phase = "APPROVE_ARCHITECTURE"
                state.last_action = f"Architecture proposed by {result.model}"

            elif state.phase == "APPROVE_ARCHITECTURE":
                project = delegated.approve_architecture(book_id)
                if not project.chapters:
                    raise AutoBookGateError("approved architecture contains no chapters")
                self._set_current_chapter(state, project, project.chapters[0].chapter_id)
                state.phase = "CHAPTER_CONTRACT"
                state.last_action = "Architecture accepted under owner Auto Book authorization"

            elif state.phase == "CHAPTER_CONTRACT":
                project = self.projects.get_project(book_id)
                if state.current_chapter_id is None:
                    pending = self._first_pending_chapter(project)
                    if pending is None:
                        state.phase = "EXPORT"
                    else:
                        self._set_current_chapter(state, project, pending)
                if state.phase == "CHAPTER_CONTRACT":
                    chapter = next(
                        item
                        for item in project.chapters
                        if item.chapter_id == state.current_chapter_id
                    )
                    if self._approved(chapter.chapter_contract):
                        state.phase = "CHAPTER_DRAFT"
                        state.last_action = f"Chapter {chapter.ordinal} contract already approved"
                    else:
                        cap = self._remaining_call_cap(state)
                        result = self._chapter_contract(state, cap)
                        self._consume_call(state, cap)
                        state.phase = "APPROVE_CHAPTER"
                        state.last_action = (
                            f"Chapter {chapter.ordinal} contract proposed by {result.model}"
                        )

            elif state.phase == "APPROVE_CHAPTER":
                if state.current_chapter_id is None:
                    raise AutoBookError("current chapter is missing")
                project = delegated.approve_chapter_contract(book_id, state.current_chapter_id)
                chapter = next(
                    item for item in project.chapters if item.chapter_id == state.current_chapter_id
                )
                state.current_chapter_ordinal = chapter.ordinal
                state.phase = "CHAPTER_DRAFT"
                state.last_action = (
                    f"Chapter {chapter.ordinal} contract accepted under owner "
                    "Auto Book authorization"
                )

            elif state.phase == "CHAPTER_DRAFT":
                if state.current_chapter_id is None:
                    raise AutoBookError("current chapter is missing")
                cap = self._remaining_call_cap(state)
                self._draft_chapter(state, cap)
                self._consume_call(state, cap)
                project = self.projects.get_project(book_id)
                current_ordinal = state.current_chapter_ordinal
                pending = self._first_pending_chapter(project)
                if pending is None:
                    state.current_chapter_id = None
                    state.current_chapter_ordinal = None
                    state.phase = "EXPORT"
                else:
                    self._set_current_chapter(state, project, pending)
                    state.phase = "CHAPTER_CONTRACT"
                state.last_action = f"Chapter {current_ordinal or '?'} drafted"

            elif state.phase == "EXPORT":
                state.output_path = (
                    self._export(book_id, state) if state.prepare_litres_docx else None
                )
                state.phase = "DONE"
                state.status = "DONE"
                state.last_action = (
                    "LitRes-ready DOCX created" if state.output_path else "Auto Book draft completed"
                )

            elif state.phase == "DONE":
                state.status = "DONE"

            return self._write(state)
        except Exception as exc:
            state.status = "FAILED"
            state.error = str(exc)
            state.last_action = "Auto Book stopped on an error"
            self._write(state)
            raise

    @classmethod
    def _clean_litres_text(cls, value: str) -> str:
        cleaned = value.translate(cls._LITRES_FORBIDDEN)
        # Remove common emoji/supplementary pictographs without damaging Cyrillic punctuation.
        cleaned = "".join(ch for ch in cleaned if not (0x1F000 <= ord(ch) <= 0x1FAFF))
        return cleaned.replace("\r\n", "\n").replace("\r", "\n").strip()

    @staticmethod
    def _xml_text(value: str) -> str:
        return html_escape(value, quote=False)

    def _export(self, book_id: str, state: AutoBookRunView) -> str:
        project = self.projects.get_project(book_id)
        chapters: list[tuple[str, str]] = []
        total_characters = 0
        for chapter in project.chapters:
            drafts = self.drafting.list_drafts(book_id, chapter.chapter_id)
            latest = next((item for item in drafts if item.text), None)
            if latest is None or not latest.text:
                raise AutoBookGateError(f"chapter {chapter.ordinal} has no generated text")
            text_value = self._clean_litres_text(latest.text)
            chapters.append((chapter.working_title, text_value))
            total_characters += len(text_value)
        if total_characters < 4_000:
            raise AutoBookGateError(
                "LitRes export requires at least 4000 characters with spaces in the manuscript"
            )

        export_dir = self._project_dir(book_id) / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        output = export_dir / f"litres-{state.run_id}.docx"

        body_parts: list[str] = []
        for title, chapter_text in chapters:
            body_parts.append(
                "<w:p><w:pPr><w:pStyle w:val=\"Heading1\"/></w:pPr>"
                f"<w:r><w:t>{self._xml_text(title)}</w:t></w:r></w:p>"
            )
            for paragraph in [item.strip() for item in chapter_text.split("\n\n") if item.strip()]:
                body_parts.append(
                    "<w:p><w:r><w:t xml:space=\"preserve\">"
                    f"{self._xml_text(paragraph)}"
                    "</w:t></w:r></w:p>"
                )

        document_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            "<w:body>"
            + "".join(body_parts)
            + '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1440" '
            'w:right="1440" w:bottom="1440" w:left="1440"/></w:sectPr></w:body></w:document>'
        )
        styles_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>'
            '<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/>'
            '<w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>'
            '<w:rPr><w:b/><w:sz w:val="32"/></w:rPr></w:style></w:styles>'
        )
        content_types = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
            "</Types>"
        )
        root_rels = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            "</Relationships>"
        )
        document_rels = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
            "</Relationships>"
        )

        with ZipFile(output, "w", ZIP_DEFLATED) as archive:
            archive.writestr("[Content_Types].xml", content_types)
            archive.writestr("_rels/.rels", root_rels)
            archive.writestr("word/document.xml", document_xml)
            archive.writestr("word/styles.xml", styles_xml)
            archive.writestr("word/_rels/document.xml.rels", document_rels)
        return str(output)
