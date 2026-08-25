from pathlib import Path
import hmac
import os
from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import ValidationError

from . import __version__
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


def create_app(token: str | None = None, data_dir: Path | None = None) -> FastAPI:
    expected = token or os.environ.get("BOOK_OS_SESSION_TOKEN")
    if not expected:
        raise RuntimeError("BOOK_OS_SESSION_TOKEN is required")
    configured_data_dir = data_dir
    if configured_data_dir is None:
        raw_data_dir = os.environ.get("BOOK_OS_DATA_DIR")
        configured_data_dir = Path(raw_data_dir) if raw_data_dir else None
    projects = ProjectService(configured_data_dir) if configured_data_dir is not None else None

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

    @app.exception_handler(ProjectNotFound)
    async def project_not_found(_, exc: ProjectNotFound):
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ProjectGateError)
    async def project_gate_error(_, exc: ProjectGateError):
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(ProjectError)
    async def project_error(_, exc: ProjectError):
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(ValidationError)
    async def validation_error(_, exc: ValidationError):
        from fastapi.responses import JSONResponse

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

    return app
