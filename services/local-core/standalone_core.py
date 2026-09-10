from __future__ import annotations

import os
from pathlib import Path

from book_os_core.__main__ import main
from book_os_core.projects import NewBookRequest, ProjectService


def packaged_project_probe() -> None:
    """CI-only frozen-runtime probe for the first database-backed user action."""
    marker = os.environ.get("BOOK_OS_PACKAGED_PROJECT_PROBE_FILE")
    if not marker:
        return
    raw_data_dir = os.environ.get("BOOK_OS_DATA_DIR")
    if not raw_data_dir:
        raise RuntimeError("BOOK_OS_DATA_DIR is required for packaged project probe")
    project = ProjectService(Path(raw_data_dir)).create_project(
        NewBookRequest(
            working_title="BOOK OS packaged migration probe",
            primary_subtype="Strategy",
        )
    )
    Path(marker).write_text(project.book_id + "\n", encoding="utf-8")


if __name__ == "__main__":
    packaged_project_probe()
    main()
