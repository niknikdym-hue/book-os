from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import re
import shutil

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

from .db import create_database
from .projects import ProjectSummary

_BOOK_ID = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$")


class ProjectLifecycleError(RuntimeError):
    pass


class ProjectLifecycleNotFound(ProjectLifecycleError):
    pass


class ProjectLifecycleConflict(ProjectLifecycleError):
    pass


class ProjectLifecycleService:
    def __init__(self, data_dir: Path):
        self.projects_dir = data_dir / "projects"
        self.library_dir = data_dir / "library"
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self.library_dir.mkdir(parents=True, exist_ok=True)

    def _book_dir(self, root: Path, book_id: str) -> Path:
        if not _BOOK_ID.fullmatch(book_id):
            raise ProjectLifecycleNotFound("invalid book project ID")
        return root / book_id

    def _require_project_dir(self, root: Path, book_id: str) -> Path:
        project_dir = self._book_dir(root, book_id)
        if project_dir.is_symlink():
            raise ProjectLifecycleError("book project directory must not be a symlink")
        if not project_dir.is_dir():
            raise ProjectLifecycleNotFound(f"book project not found: {book_id}")
        if not (project_dir / "project.sqlite").is_file():
            raise ProjectLifecycleError(f"book project database is missing: {book_id}")
        if not (project_dir / "project-manifest.json").is_file():
            raise ProjectLifecycleError(f"book project manifest is missing: {book_id}")
        return project_dir

    def _summary(self, root: Path, book_id: str) -> ProjectSummary:
        project_dir = self._require_project_dir(root, book_id)
        engine = create_database(project_dir / "project.sqlite")
        try:
            with engine.connect() as connection:
                row = (
                    connection.execute(
                        text(
                            "SELECT book_id,working_title,primary_subtype,secondary_subtype,"
                            "workflow_stage FROM book_projects WHERE book_id=:book_id"
                        ),
                        {"book_id": book_id},
                    )
                    .mappings()
                    .one_or_none()
                )
            if row is None:
                raise ProjectLifecycleError(f"book project metadata is missing: {book_id}")
            return ProjectSummary(
                book_id=str(row["book_id"]),
                working_title=str(row["working_title"]),
                primary_subtype=str(row["primary_subtype"]),
                secondary_subtype=(
                    str(row["secondary_subtype"])
                    if row["secondary_subtype"] is not None
                    else None
                ),
                workflow_stage=str(row["workflow_stage"]),
            )
        finally:
            engine.dispose()

    def list_library(self) -> list[ProjectSummary]:
        projects: list[ProjectSummary] = []
        for manifest in sorted(self.library_dir.glob("*/project-manifest.json")):
            try:
                projects.append(self._summary(self.library_dir, manifest.parent.name))
            except (OSError, ValueError, ProjectLifecycleError):
                continue
        return sorted(projects, key=lambda item: item.working_title.casefold())

    def archive(self, book_id: str) -> ProjectSummary:
        source = self._require_project_dir(self.projects_dir, book_id)
        destination = self._book_dir(self.library_dir, book_id)
        if destination.exists():
            raise ProjectLifecycleConflict(f"book already exists in library: {book_id}")
        try:
            source.rename(destination)
        except OSError as exc:
            raise ProjectLifecycleError(f"failed to move book to library: {book_id}") from exc
        return self._summary(self.library_dir, book_id)

    def restore(self, book_id: str) -> ProjectSummary:
        source = self._require_project_dir(self.library_dir, book_id)
        destination = self._book_dir(self.projects_dir, book_id)
        if destination.exists():
            raise ProjectLifecycleConflict(f"active book already exists: {book_id}")
        try:
            source.rename(destination)
        except OSError as exc:
            raise ProjectLifecycleError(f"failed to restore book from library: {book_id}") from exc
        return self._summary(self.projects_dir, book_id)

    def delete_active(self, book_id: str) -> None:
        self._delete(self.projects_dir, book_id)

    def delete_archived(self, book_id: str) -> None:
        self._delete(self.library_dir, book_id)

    def _delete(self, root: Path, book_id: str) -> None:
        project_dir = self._require_project_dir(root, book_id)
        try:
            shutil.rmtree(project_dir)
        except OSError as exc:
            raise ProjectLifecycleError(f"failed to delete book project: {book_id}") from exc


def build_project_lifecycle_router(
    data_dir: Path, require_token: Callable[..., None]
) -> APIRouter:
    service = ProjectLifecycleService(data_dir)
    router = APIRouter(dependencies=[Depends(require_token)])

    def raise_http(exc: ProjectLifecycleError) -> None:
        if isinstance(exc, ProjectLifecycleNotFound):
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        if isinstance(exc, ProjectLifecycleConflict):
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/api/library")
    def list_library() -> list[dict[str, object]]:
        return [item.model_dump(mode="json") for item in service.list_library()]

    @router.post("/api/projects/{book_id}/archive")
    def archive_project(book_id: str) -> dict[str, object]:
        try:
            return service.archive(book_id).model_dump(mode="json")
        except ProjectLifecycleError as exc:
            raise_http(exc)
        raise AssertionError("unreachable")

    @router.post("/api/library/{book_id}/restore")
    def restore_project(book_id: str) -> dict[str, object]:
        try:
            return service.restore(book_id).model_dump(mode="json")
        except ProjectLifecycleError as exc:
            raise_http(exc)
        raise AssertionError("unreachable")

    @router.delete("/api/projects/{book_id}")
    def delete_project(book_id: str) -> dict[str, object]:
        try:
            service.delete_active(book_id)
            return {"deleted": True, "book_id": book_id}
        except ProjectLifecycleError as exc:
            raise_http(exc)
        raise AssertionError("unreachable")

    @router.delete("/api/library/{book_id}")
    def delete_archived_project(book_id: str) -> dict[str, object]:
        try:
            service.delete_archived(book_id)
            return {"deleted": True, "book_id": book_id}
        except ProjectLifecycleError as exc:
            raise_http(exc)
        raise AssertionError("unreachable")

    return router
