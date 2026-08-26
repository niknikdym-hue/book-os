from pathlib import Path
import hmac
import os

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError

from . import __version__
from .drafting import DraftingError, DraftingGateError, DraftingService, DraftSectionRequest
from .memory import (
    BookMemoryService,
    MemoryError,
    MemoryGateError,
    MemoryNotFound,
    MemoryRebuildRequest,
    MemorySearchRequest,
)
from .memory_embeddings import (
    EmbeddingGateway,
    EmbeddingOutputError,
    EmbeddingProviderError,
    OpenAIEmbeddingAdapter,
)
from .model_gateway import (
    ModelBudgetError,
    ModelGateway,
    ModelOutputError,
    ModelProviderError,
    OpenAIResponsesAdapter,
)
from .projects import (
    BookArchitecturePayload,
    BookContractPayload,
    ChapterContractPayload,
    NewBookRequest,
    ProjectError,
    ProjectGateError,
    ProjectNotFound,
    ProjectService,
)
from .research import (
    ClaimCreateRequest,
    ClaimReviewRequest,
    ClaimUpdateRequest,
    EvidenceCreateRequest,
    ResearchError,
    ResearchGateError,
    ResearchNotFound,
    ResearchSearchRequest,
    ResearchService,
    SourceAccessRequest,
    SourceImportRequest,
)
from .research_adapters import (
    CrossrefAdapter,
    OpenAlexAdapter,
    ResearchGateway,
    ResearchProviderError,
    SemanticScholarAdapter,
)
from .secrets import MacOSKeychainSecretStore, SecretNotFound


class CitationIdentifierRequest(BaseModel):
    identifier: str = Field(min_length=1, max_length=1000)


def create_app(
    token: str | None = None,
    data_dir: Path | None = None,
    *,
    gateway: ModelGateway | None = None,
    research_gateway: ResearchGateway | None = None,
    embedding_gateway: EmbeddingGateway | None = None,
) -> FastAPI:
    expected = token or os.environ.get("BOOK_OS_SESSION_TOKEN")
    if not expected:
        raise RuntimeError("BOOK_OS_SESSION_TOKEN is required")
    configured_data_dir = data_dir
    if configured_data_dir is None:
        raw_data_dir = os.environ.get("BOOK_OS_DATA_DIR")
        configured_data_dir = Path(raw_data_dir) if raw_data_dir else None
    projects = ProjectService(configured_data_dir) if configured_data_dir is not None else None
    configured_gateway = gateway or ModelGateway(
        {"openai": OpenAIResponsesAdapter(MacOSKeychainSecretStore())}
    )
    drafting = (
        DraftingService(configured_data_dir, configured_gateway)
        if configured_data_dir is not None
        else None
    )
    configured_research_gateway = research_gateway or ResearchGateway(
        {
            "openalex": OpenAlexAdapter(),
            "crossref": CrossrefAdapter(mailto=os.environ.get("BOOK_OS_CROSSREF_MAILTO")),
            "semantic_scholar": SemanticScholarAdapter(),
        }
    )
    research = (
        ResearchService(configured_data_dir, configured_research_gateway)
        if configured_data_dir is not None
        else None
    )
    configured_embedding_gateway = embedding_gateway or EmbeddingGateway(
        {"openai": OpenAIEmbeddingAdapter(MacOSKeychainSecretStore())}
    )
    memory = (
        BookMemoryService(configured_data_dir, configured_embedding_gateway)
        if configured_data_dir is not None
        else None
    )

    app = FastAPI(title="BOOK OS Local Core", docs_url=None, redoc_url=None, openapi_url=None)

    def require_token(authorization: str | None = Header(default=None)) -> None:
        if (
            authorization is None
            or not authorization.startswith("Bearer ")
            or not hmac.compare_digest(authorization[7:], expected)
        ):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized")

    def project_service(_: None = Depends(require_token)) -> ProjectService:
        if projects is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="BOOK_OS_DATA_DIR is required for project operations",
            )
        return projects

    def drafting_service(_: None = Depends(require_token)) -> DraftingService:
        if drafting is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="BOOK_OS_DATA_DIR is required for drafting operations",
            )
        return drafting

    def research_service(_: None = Depends(require_token)) -> ResearchService:
        if research is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="BOOK_OS_DATA_DIR is required for research operations",
            )
        return research

    def memory_service(_: None = Depends(require_token)) -> BookMemoryService:
        if memory is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="BOOK_OS_DATA_DIR is required for Book Memory operations",
            )
        return memory

    @app.exception_handler(ProjectNotFound)
    async def project_not_found(_: Request, exc: ProjectNotFound) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ProjectGateError)
    async def project_gate_error(_: Request, exc: ProjectGateError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(ProjectError)
    async def project_error(_: Request, exc: ProjectError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(DraftingGateError)
    async def drafting_gate_error(_: Request, exc: DraftingGateError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(ModelBudgetError)
    async def model_budget_error(_: Request, exc: ModelBudgetError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(SecretNotFound)
    async def secret_not_found(_: Request, exc: SecretNotFound) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content={"detail": f"required provider secret is unavailable: {exc}"},
        )

    @app.exception_handler(ModelProviderError)
    async def model_provider_error(_: Request, exc: ModelProviderError) -> JSONResponse:
        return JSONResponse(status_code=502, content={"detail": str(exc)})

    @app.exception_handler(ModelOutputError)
    async def model_output_error(_: Request, exc: ModelOutputError) -> JSONResponse:
        return JSONResponse(status_code=502, content={"detail": str(exc)})

    @app.exception_handler(DraftingError)
    async def drafting_error(_: Request, exc: DraftingError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(ResearchNotFound)
    async def research_not_found(_: Request, exc: ResearchNotFound) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ResearchGateError)
    async def research_gate_error(_: Request, exc: ResearchGateError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(ResearchProviderError)
    async def research_provider_error(_: Request, exc: ResearchProviderError) -> JSONResponse:
        return JSONResponse(status_code=502, content={"detail": str(exc)})

    @app.exception_handler(ResearchError)
    async def research_error(_: Request, exc: ResearchError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(MemoryNotFound)
    async def memory_not_found(_: Request, exc: MemoryNotFound) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(MemoryGateError)
    async def memory_gate_error(_: Request, exc: MemoryGateError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(EmbeddingProviderError)
    async def embedding_provider_error(_: Request, exc: EmbeddingProviderError) -> JSONResponse:
        return JSONResponse(status_code=502, content={"detail": str(exc)})

    @app.exception_handler(EmbeddingOutputError)
    async def embedding_output_error(_: Request, exc: EmbeddingOutputError) -> JSONResponse:
        return JSONResponse(status_code=502, content={"detail": str(exc)})

    @app.exception_handler(MemoryError)
    async def memory_error(_: Request, exc: MemoryError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(ValidationError)
    async def validation_error(_: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": exc.errors()})

    @app.get("/health")
    def health(_: None = Depends(require_token)) -> dict[str, str]:
        return {"status": "healthy", "version": __version__}

    @app.get("/api/projects")
    def list_projects(
        service: ProjectService = Depends(project_service),
    ) -> list[dict[str, object]]:
        return [project.model_dump(mode="json") for project in service.list_projects()]

    @app.post("/api/projects")
    def create_project(
        request: NewBookRequest, service: ProjectService = Depends(project_service)
    ) -> dict[str, object]:
        return service.create_project(request).model_dump(mode="json")

    @app.get("/api/projects/{book_id}")
    def get_project(
        book_id: str, service: ProjectService = Depends(project_service)
    ) -> dict[str, object]:
        return service.get_project(book_id).model_dump(mode="json")

    @app.put("/api/projects/{book_id}/book-contract/draft")
    def save_book_contract(
        book_id: str,
        payload: BookContractPayload,
        service: ProjectService = Depends(project_service),
    ) -> dict[str, object]:
        return service.save_book_contract(book_id, payload).model_dump(mode="json")

    @app.post("/api/projects/{book_id}/book-contract/approve")
    def approve_book_contract(
        book_id: str, service: ProjectService = Depends(project_service)
    ) -> dict[str, object]:
        return service.approve_book_contract(book_id).model_dump(mode="json")

    @app.put("/api/projects/{book_id}/architecture/draft")
    def save_architecture(
        book_id: str,
        payload: BookArchitecturePayload,
        service: ProjectService = Depends(project_service),
    ) -> dict[str, object]:
        return service.save_architecture(book_id, payload).model_dump(mode="json")

    @app.post("/api/projects/{book_id}/architecture/approve")
    def approve_architecture(
        book_id: str, service: ProjectService = Depends(project_service)
    ) -> dict[str, object]:
        return service.approve_architecture(book_id).model_dump(mode="json")

    @app.put("/api/projects/{book_id}/chapters/{chapter_id}/contract/draft")
    def save_chapter_contract(
        book_id: str,
        chapter_id: str,
        payload: ChapterContractPayload,
        service: ProjectService = Depends(project_service),
    ) -> dict[str, object]:
        return service.save_chapter_contract(book_id, chapter_id, payload).model_dump(mode="json")

    @app.post("/api/projects/{book_id}/chapters/{chapter_id}/contract/approve")
    def approve_chapter_contract(
        book_id: str,
        chapter_id: str,
        service: ProjectService = Depends(project_service),
    ) -> dict[str, object]:
        return service.approve_chapter_contract(book_id, chapter_id).model_dump(mode="json")

    @app.get("/api/projects/{book_id}/chapters/{chapter_id}/drafts")
    def list_section_drafts(
        book_id: str,
        chapter_id: str,
        service: DraftingService = Depends(drafting_service),
    ) -> list[dict[str, object]]:
        return [item.model_dump(mode="json") for item in service.list_drafts(book_id, chapter_id)]

    @app.post("/api/projects/{book_id}/chapters/{chapter_id}/drafts")
    def generate_section_draft(
        book_id: str,
        chapter_id: str,
        payload: DraftSectionRequest,
        service: DraftingService = Depends(drafting_service),
    ) -> dict[str, object]:
        return service.generate_section_draft(book_id, chapter_id, payload).model_dump(mode="json")

    @app.get("/api/projects/{book_id}/claims")
    def list_claims(
        book_id: str,
        chapter_id: str | None = Query(default=None),
        unit_id: str | None = Query(default=None),
        verification_state: str | None = Query(default=None),
        service: ResearchService = Depends(research_service),
    ) -> list[dict[str, object]]:
        return [
            item.model_dump(mode="json")
            for item in service.list_claims(
                book_id,
                chapter_id=chapter_id,
                unit_id=unit_id,
                verification_state=verification_state,
            )
        ]

    @app.post("/api/projects/{book_id}/claims")
    def create_claim(
        book_id: str,
        payload: ClaimCreateRequest,
        service: ResearchService = Depends(research_service),
    ) -> dict[str, object]:
        return service.create_claim(book_id, payload).model_dump(mode="json")

    @app.put("/api/projects/{book_id}/claims/{claim_id}")
    def update_claim(
        book_id: str,
        claim_id: str,
        payload: ClaimUpdateRequest,
        service: ResearchService = Depends(research_service),
    ) -> dict[str, object]:
        return service.update_claim(book_id, claim_id, payload).model_dump(mode="json")

    @app.post("/api/projects/{book_id}/claims/{claim_id}/review")
    def review_claim(
        book_id: str,
        claim_id: str,
        payload: ClaimReviewRequest,
        service: ResearchService = Depends(research_service),
    ) -> dict[str, object]:
        return service.review_claim(book_id, claim_id, payload).model_dump(mode="json")

    @app.post("/api/projects/{book_id}/research/search")
    def research_search(
        book_id: str,
        payload: ResearchSearchRequest,
        service: ResearchService = Depends(research_service),
    ) -> list[dict[str, object]]:
        service.list_claims(book_id)
        return [candidate.model_dump(mode="json") for candidate in service.search(payload)]

    @app.get("/api/projects/{book_id}/sources")
    def list_sources(
        book_id: str, service: ResearchService = Depends(research_service)
    ) -> list[dict[str, object]]:
        return [source.model_dump(mode="json") for source in service.list_sources(book_id)]

    @app.post("/api/projects/{book_id}/sources/import")
    def import_source(
        book_id: str,
        payload: SourceImportRequest,
        service: ResearchService = Depends(research_service),
    ) -> dict[str, object]:
        return service.import_source(book_id, payload).model_dump(mode="json")

    @app.post("/api/projects/{book_id}/sources/{source_id}/access")
    def mark_source_access(
        book_id: str,
        source_id: str,
        payload: SourceAccessRequest,
        service: ResearchService = Depends(research_service),
    ) -> dict[str, object]:
        return service.mark_source_access(book_id, source_id, payload).model_dump(mode="json")

    @app.get("/api/projects/{book_id}/claims/{claim_id}/evidence")
    def list_evidence(
        book_id: str,
        claim_id: str,
        service: ResearchService = Depends(research_service),
    ) -> list[dict[str, object]]:
        return [item.model_dump(mode="json") for item in service.list_evidence(book_id, claim_id)]

    @app.post("/api/projects/{book_id}/claims/{claim_id}/evidence")
    def add_evidence(
        book_id: str,
        claim_id: str,
        payload: EvidenceCreateRequest,
        service: ResearchService = Depends(research_service),
    ) -> dict[str, object]:
        return service.add_evidence(book_id, claim_id, payload).model_dump(mode="json")

    @app.post("/api/projects/{book_id}/claims/{claim_id}/citation-check")
    def check_citation(
        book_id: str,
        claim_id: str,
        payload: CitationIdentifierRequest,
        service: ResearchService = Depends(research_service),
    ) -> dict[str, object]:
        return service.check_citation(book_id, claim_id, payload.identifier).model_dump(mode="json")

    @app.get("/api/projects/{book_id}/memory/status")
    def memory_status(
        book_id: str, service: BookMemoryService = Depends(memory_service)
    ) -> dict[str, object]:
        return service.status(book_id).model_dump(mode="json")

    @app.post("/api/projects/{book_id}/memory/sync")
    def memory_sync(
        book_id: str, service: BookMemoryService = Depends(memory_service)
    ) -> dict[str, object]:
        return service.synchronize(book_id).model_dump(mode="json")

    @app.post("/api/projects/{book_id}/memory/rebuild")
    def memory_rebuild(
        book_id: str,
        payload: MemoryRebuildRequest,
        service: BookMemoryService = Depends(memory_service),
    ) -> dict[str, object]:
        return service.rebuild(book_id, provider=payload.provider, model=payload.model).model_dump(
            mode="json"
        )

    @app.post("/api/projects/{book_id}/memory/search")
    def memory_search(
        book_id: str,
        payload: MemorySearchRequest,
        service: BookMemoryService = Depends(memory_service),
    ) -> list[dict[str, object]]:
        return [item.model_dump(mode="json") for item in service.search(book_id, payload)]

    return app
