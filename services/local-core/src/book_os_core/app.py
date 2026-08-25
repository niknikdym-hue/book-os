from pathlib import Path
import hmac
import os
from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from . import __version__
from .drafting import DraftingError, DraftingGateError, DraftingService, DraftSectionRequest
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
from .secrets import MacOSKeychainSecretStore, SecretNotFound


def create_app(
    token: str | None = None,
    data_dir: Path | None = None,
    *,
    gateway: ModelGateway | None = None,
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

    return app
