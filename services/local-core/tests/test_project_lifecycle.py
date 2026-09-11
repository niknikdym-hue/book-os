from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from book_os_core.app import create_app
from book_os_core.project_lifecycle import ProjectLifecycleService
from book_os_core.projects import NewBookRequest, ProjectService


def create_project(tmp_path: Path, title: str = "Lifecycle Book"):
    return ProjectService(tmp_path).create_project(
        NewBookRequest(working_title=title, primary_subtype="Strategy")
    )


def test_archive_moves_complete_project_to_library_and_restore_preserves_it(tmp_path: Path) -> None:
    project = create_project(tmp_path)
    active_dir = tmp_path / "projects" / project.book_id
    marker = active_dir / "owner-note.txt"
    marker.write_text("keep me", encoding="utf-8")

    lifecycle = ProjectLifecycleService(tmp_path)
    archived = lifecycle.archive(project.book_id)

    assert archived.book_id == project.book_id
    assert not active_dir.exists()
    library_dir = tmp_path / "library" / project.book_id
    assert (library_dir / "project.sqlite").is_file()
    assert (library_dir / "project-manifest.json").is_file()
    assert (library_dir / "owner-note.txt").read_text(encoding="utf-8") == "keep me"
    assert ProjectService(tmp_path).list_projects() == []
    assert [item.book_id for item in lifecycle.list_library()] == [project.book_id]

    restored = lifecycle.restore(project.book_id)
    assert restored.book_id == project.book_id
    assert not library_dir.exists()
    assert (active_dir / "owner-note.txt").read_text(encoding="utf-8") == "keep me"
    assert [item.book_id for item in ProjectService(tmp_path).list_projects()] == [project.book_id]


def test_permanent_delete_removes_entire_active_project_tree(tmp_path: Path) -> None:
    project = create_project(tmp_path)
    active_dir = tmp_path / "projects" / project.book_id
    (active_dir / "nested").mkdir()
    (active_dir / "nested" / "material.txt").write_text("delete me", encoding="utf-8")

    ProjectLifecycleService(tmp_path).delete_active(project.book_id)

    assert not active_dir.exists()
    assert ProjectService(tmp_path).list_projects() == []


def test_authenticated_lifecycle_api_archives_restores_and_deletes(tmp_path: Path) -> None:
    client = TestClient(create_app("token", tmp_path))
    headers = {"Authorization": "Bearer token"}
    created = client.post(
        "/api/projects",
        headers=headers,
        json={"working_title": "API Lifecycle Book", "primary_subtype": "Strategy"},
    )
    assert created.status_code == 200
    book_id = created.json()["book_id"]

    archived = client.post(f"/api/projects/{book_id}/archive", headers=headers)
    assert archived.status_code == 200
    assert client.get("/api/projects", headers=headers).json() == []
    library = client.get("/api/library", headers=headers)
    assert library.status_code == 200
    assert [item["book_id"] for item in library.json()] == [book_id]

    restored = client.post(f"/api/library/{book_id}/restore", headers=headers)
    assert restored.status_code == 200
    assert [item["book_id"] for item in client.get("/api/projects", headers=headers).json()] == [
        book_id
    ]

    deleted = client.delete(f"/api/projects/{book_id}", headers=headers)
    assert deleted.status_code == 200
    assert deleted.json() == {"deleted": True, "book_id": book_id}
    assert client.get(f"/api/projects/{book_id}", headers=headers).status_code == 404
