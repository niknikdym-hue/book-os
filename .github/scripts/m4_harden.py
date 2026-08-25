from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file = Path(path)
    text = file.read_text()
    if old not in text:
        raise SystemExit(f"pattern missing in {path}: {old[:80]!r}")
    file.write_text(text.replace(old, new, 1))


research = "services/local-core/src/book_os_core/research.py"
replace_once(
    research,
    '''class ClaimReviewRequest(BaseModel):\n    state: Literal["UNREVIEWED", "DISPUTED", "UNSUPPORTED", "REJECTED"]\n    actor: Annotated[str, Field(min_length=1, max_length=128)] = "OWNER"\n''',
    '''class ClaimReviewRequest(BaseModel):\n    state: Literal["UNREVIEWED", "DISPUTED", "UNSUPPORTED", "REJECTED"]\n    actor: Annotated[str, Field(min_length=1, max_length=128)] = "OWNER"\n    reason: NonEmpty\n''',
)
replace_once(
    research,
    '''class SourceImportRequest(BaseModel):\n    candidate: ResearchCandidate\n    primary_secondary: Literal["PRIMARY", "SECONDARY", "UNCLASSIFIED"] = "UNCLASSIFIED"\n\n\nclass SourceView(BaseModel):\n''',
    '''class SourceImportRequest(BaseModel):\n    candidate: ResearchCandidate\n    primary_secondary: Literal["PRIMARY", "SECONDARY", "UNCLASSIFIED"] = "UNCLASSIFIED"\n\n\nclass SourceAccessRequest(BaseModel):\n    access_status: Literal["METADATA_ONLY", "ABSTRACT_AVAILABLE", "FULL_SOURCE_INSPECTED"]\n    actor: Annotated[str, Field(min_length=1, max_length=128)] = "OWNER"\n    note: str = ""\n\n    @field_validator("actor", "note")\n    @classmethod\n    def strip_access_fields(cls, value: str) -> str:\n        return value.strip()\n\n    @model_validator(mode="after")\n    def inspected_requires_note(self) -> SourceAccessRequest:\n        if self.access_status == "FULL_SOURCE_INSPECTED" and not self.note:\n            raise ValueError("FULL_SOURCE_INSPECTED requires an inspection note")\n        return self\n\n\nclass SourceView(BaseModel):\n''',
)
replace_once(
    research,
    '''                    },\n                )\n            return self.get_claim(book_id, claim_id)\n        finally:\n            engine.dispose()\n\n    def update_claim(\n''',
    '''                    },\n                )\n                connection.execute(\n                    text(\n                        "INSERT INTO claim_state_history(state_event_id,claim_id,prior_state,new_state,"\n                        "actor,actor_kind,reason,created_at) VALUES (:event_id,:claim_id,NULL,"\n                        "'UNREVIEWED','OWNER','HUMAN','Claim registered',:created_at)"\n                    ),\n                    {"event_id": new_ulid(), "claim_id": claim_id, "created_at": now},\n                )\n            return self.get_claim(book_id, claim_id)\n        finally:\n            engine.dispose()\n\n    def update_claim(\n''',
)
replace_once(
    research,
    '"SELECT chapter_id,unit_id FROM claims "',
    '"SELECT chapter_id,unit_id,verification_state FROM claims "',
)
replace_once(
    research,
    '''            now = utc_now()\n            with engine.begin() as connection:\n                connection.execute(\n                    text(\n                        "UPDATE claims SET manuscript_revision_id=:revision_id,"\n                        "manuscript_revision_hash=:revision_hash,normalized_text=:normalized_text,"\n                        "claim_type=:claim_type,materiality=:materiality,"\n                        "required_evidence_level=:required_evidence_level,updated_at=:updated_at "\n                        "WHERE claim_id=:claim_id"\n                    ),\n                    {\n                        "revision_id": request.manuscript_revision_id,\n                        "revision_hash": request.manuscript_revision_hash,\n                        "normalized_text": request.normalized_text,\n                        "claim_type": request.claim_type,\n                        "materiality": request.materiality,\n                        "required_evidence_level": request.required_evidence_level,\n                        "updated_at": now,\n                        "claim_id": claim_id,\n                    },\n                )\n            return self.get_claim(book_id, claim_id)\n''',
    '''            now = utc_now()\n            prior_state = cast(str, row["verification_state"])\n            with engine.begin() as connection:\n                connection.execute(\n                    text(\n                        "UPDATE claims SET manuscript_revision_id=:revision_id,"\n                        "manuscript_revision_hash=:revision_hash,normalized_text=:normalized_text,"\n                        "claim_type=:claim_type,materiality=:materiality,"\n                        "required_evidence_level=:required_evidence_level,verification_state='UNREVIEWED',"\n                        "updated_at=:updated_at WHERE claim_id=:claim_id"\n                    ),\n                    {\n                        "revision_id": request.manuscript_revision_id,\n                        "revision_hash": request.manuscript_revision_hash,\n                        "normalized_text": request.normalized_text,\n                        "claim_type": request.claim_type,\n                        "materiality": request.materiality,\n                        "required_evidence_level": request.required_evidence_level,\n                        "updated_at": now,\n                        "claim_id": claim_id,\n                    },\n                )\n                connection.execute(\n                    text("UPDATE evidence SET status='SUPERSEDED' WHERE claim_id=:claim_id AND status='ACTIVE'"),\n                    {"claim_id": claim_id},\n                )\n                if prior_state != "UNREVIEWED":\n                    connection.execute(\n                        text(\n                            "INSERT INTO claim_state_history(state_event_id,claim_id,prior_state,new_state,"\n                            "actor,actor_kind,reason,created_at) VALUES (:event_id,:claim_id,:prior_state,"\n                            "'UNREVIEWED','SYSTEM','SYSTEM',"\n                            "'Claim edit invalidated prior evidence decision',:created_at)"\n                        ),\n                        {\n                            "event_id": new_ulid(),\n                            "claim_id": claim_id,\n                            "prior_state": prior_state,\n                            "created_at": now,\n                        },\n                    )\n            return self.get_claim(book_id, claim_id)\n''',
)
replace_once(
    research,
    '''                identifiers = [(candidate.provider, candidate.external_id, candidate.provider_url)]\n''',
    '''                if existing_id is None:\n                    connection.execute(\n                        text(\n                            "INSERT INTO source_access_history(access_event_id,source_id,access_status,"\n                            "actor,note,created_at) VALUES (:event_id,:source_id,:access_status,"\n                            "'SYSTEM','Imported provider metadata',:created_at)"\n                        ),\n                        {\n                            "event_id": new_ulid(),\n                            "source_id": source_id,\n                            "access_status": access_status,\n                            "created_at": now,\n                        },\n                    )\n                identifiers = [(candidate.provider, candidate.external_id, candidate.provider_url)]\n''',
)
replace_once(
    research,
    '''    def get_source(self, book_id: str, source_id: str) -> SourceView:\n''',
    '''    def mark_source_access(\n        self, book_id: str, source_id: str, request: SourceAccessRequest\n    ) -> SourceView:\n        engine = self._engine(book_id)\n        try:\n            now = utc_now()\n            with engine.begin() as connection:\n                result = connection.execute(\n                    text("UPDATE sources SET access_status=:status,updated_at=:updated_at WHERE source_id=:source_id"),\n                    {"status": request.access_status, "updated_at": now, "source_id": source_id},\n                )\n                if result.rowcount != 1:\n                    raise ResearchNotFound("source not found")\n                connection.execute(\n                    text(\n                        "INSERT INTO source_access_history(access_event_id,source_id,access_status,"\n                        "actor,note,created_at) VALUES (:event_id,:source_id,:status,:actor,:note,:created_at)"\n                    ),\n                    {\n                        "event_id": new_ulid(),\n                        "source_id": source_id,\n                        "status": request.access_status,\n                        "actor": request.actor,\n                        "note": request.note,\n                        "created_at": now,\n                    },\n                )\n            return self.get_source(book_id, source_id)\n        finally:\n            engine.dispose()\n\n    def get_source(self, book_id: str, source_id: str) -> SourceView:\n''',
)
replace_once(
    research,
    '''                        "SELECT relationship,limitations FROM evidence "\n                        "WHERE claim_id=:claim_id AND status='ACTIVE'"\n''',
    '''                        "SELECT e.relationship,e.limitations,s.access_status FROM evidence e "\n                        "JOIN sources s ON s.source_id=e.source_id "\n                        "WHERE e.claim_id=:claim_id AND e.status='ACTIVE'"\n''',
)
replace_once(
    research,
    '''            has_contradiction = any(item["relationship"] == "CONTRADICTS" for item in evidence)\n            has_support = any(item["relationship"] == "SUPPORTS" for item in evidence)\n            has_partial = any(\n                item["relationship"] == "PARTIALLY_SUPPORTS"\n                and bool(cast(str, item["limitations"]).strip())\n                for item in evidence\n            )\n            if has_contradiction:\n                state: VerificationState = "DISPUTED"\n            elif has_support:\n                state = "SUPPORTED"\n            elif has_partial:\n                state = "PARTIALLY_SUPPORTED"\n            else:\n                state = "UNREVIEWED"\n            with engine.begin() as connection:\n                connection.execute(\n                    text(\n                        "UPDATE claims SET verification_state=:state,updated_at=:updated_at "\n                        "WHERE claim_id=:claim_id"\n                    ),\n                    {"state": state, "updated_at": utc_now(), "claim_id": claim_id},\n                )\n            return self.get_claim(book_id, claim_id)\n''',
    '''            has_contradiction = any(item["relationship"] == "CONTRADICTS" for item in evidence)\n            has_full_support = any(\n                item["relationship"] == "SUPPORTS"\n                and item["access_status"] == "FULL_SOURCE_INSPECTED"\n                for item in evidence\n            )\n            has_partial = any(\n                item["relationship"] == "PARTIALLY_SUPPORTS"\n                and bool(cast(str, item["limitations"]).strip())\n                for item in evidence\n            )\n            if has_contradiction:\n                state: VerificationState = "DISPUTED"\n            elif has_full_support:\n                state = "SUPPORTED"\n            elif has_partial:\n                state = "PARTIALLY_SUPPORTED"\n            else:\n                state = "UNREVIEWED"\n            prior_state = cast(str, claim["verification_state"])\n            if prior_state != state:\n                now = utc_now()\n                with engine.begin() as connection:\n                    connection.execute(\n                        text(\n                            "UPDATE claims SET verification_state=:state,updated_at=:updated_at "\n                            "WHERE claim_id=:claim_id"\n                        ),\n                        {"state": state, "updated_at": now, "claim_id": claim_id},\n                    )\n                    connection.execute(\n                        text(\n                            "INSERT INTO claim_state_history(state_event_id,claim_id,prior_state,new_state,"\n                            "actor,actor_kind,reason,created_at) VALUES (:event_id,:claim_id,:prior_state,"\n                            ":new_state,'SYSTEM','SYSTEM','Deterministic evidence recalculation',:created_at)"\n                        ),\n                        {\n                            "event_id": new_ulid(),\n                            "claim_id": claim_id,\n                            "prior_state": prior_state,\n                            "new_state": state,\n                            "created_at": now,\n                        },\n                    )\n            return self.get_claim(book_id, claim_id)\n''',
)
old_review = '''    def review_claim(\n        self, book_id: str, claim_id: str, request: ClaimReviewRequest\n    ) -> ClaimView:\n        engine = self._engine(book_id)\n        try:\n            with engine.begin() as connection:\n                result = connection.execute(\n                    text(\n                        "UPDATE claims SET verification_state=:state,updated_at=:updated_at "\n                        "WHERE book_id=:book_id AND claim_id=:claim_id"\n                    ),\n                    {\n                        "state": request.state,\n                        "updated_at": utc_now(),\n                        "book_id": book_id,\n                        "claim_id": claim_id,\n                    },\n                )\n                if result.rowcount != 1:\n                    raise ResearchNotFound("claim not found")\n            return self.get_claim(book_id, claim_id)\n        finally:\n            engine.dispose()\n'''
new_review = '''    def review_claim(\n        self, book_id: str, claim_id: str, request: ClaimReviewRequest\n    ) -> ClaimView:\n        engine = self._engine(book_id)\n        try:\n            with engine.connect() as connection:\n                prior_state = connection.execute(\n                    text("SELECT verification_state FROM claims WHERE book_id=:book_id AND claim_id=:claim_id"),\n                    {"book_id": book_id, "claim_id": claim_id},\n                ).scalar_one_or_none()\n            if prior_state is None:\n                raise ResearchNotFound("claim not found")\n            now = utc_now()\n            with engine.begin() as connection:\n                connection.execute(\n                    text(\n                        "UPDATE claims SET verification_state=:state,updated_at=:updated_at "\n                        "WHERE book_id=:book_id AND claim_id=:claim_id"\n                    ),\n                    {\n                        "state": request.state,\n                        "updated_at": now,\n                        "book_id": book_id,\n                        "claim_id": claim_id,\n                    },\n                )\n                if prior_state != request.state:\n                    connection.execute(\n                        text(\n                            "INSERT INTO claim_state_history(state_event_id,claim_id,prior_state,new_state,"\n                            "actor,actor_kind,reason,created_at) VALUES (:event_id,:claim_id,:prior_state,"\n                            ":new_state,:actor,'HUMAN',:reason,:created_at)"\n                        ),\n                        {\n                            "event_id": new_ulid(),\n                            "claim_id": claim_id,\n                            "prior_state": prior_state,\n                            "new_state": request.state,\n                            "actor": request.actor,\n                            "reason": request.reason,\n                            "created_at": now,\n                        },\n                    )\n            return self.get_claim(book_id, claim_id)\n        finally:\n            engine.dispose()\n'''
replace_once(research, old_review, new_review)

replace_once(
    "services/local-core/src/book_os_core/drafting.py",
    '''    revision_id: str | None = None\n    revision_status: str | None = None\n''',
    '''    revision_id: str | None = None\n    revision_hash: str | None = None\n    revision_status: str | None = None\n''',
)
replace_once(
    "services/local-core/src/book_os_core/drafting.py",
    '''            revision_id=revision_id,\n            revision_status="DRAFT",\n''',
    '''            revision_id=revision_id,\n            revision_hash=digest,\n            revision_status="DRAFT",\n''',
)
replace_once(
    "services/local-core/src/book_os_core/drafting.py",
    '''                revision_id = None\n                revision_status = None\n''',
    '''                revision_id = None\n                revision_hash = None\n                revision_status = None\n''',
)
replace_once(
    "services/local-core/src/book_os_core/drafting.py",
    '''                    revision_id = head.revision_id\n                    revision_status = head.status\n''',
    '''                    revision_id = head.revision_id\n                    revision_hash = head.revision_hash\n                    revision_status = head.status\n''',
)
replace_once(
    "services/local-core/src/book_os_core/drafting.py",
    '''                        revision_id=revision_id,\n                        revision_status=revision_status,\n''',
    '''                        revision_id=revision_id,\n                        revision_hash=revision_hash,\n                        revision_status=revision_status,\n''',
)
replace_once(
    "apps/desktop/src/draftingTypes.ts",
    '''  revision_id: string | null;\n  revision_status: string | null;\n''',
    '''  revision_id: string | null;\n  revision_hash: string | null;\n  revision_status: string | null;\n''',
)
replace_once(
    "services/local-core/src/book_os_core/backup.py",
    'SUPPORTED_ALEMBIC_REVISION = "0004"',
    'SUPPORTED_ALEMBIC_REVISION = "0005"',
)
