from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text()
    if old not in text:
        if new in text:
            return
        raise SystemExit(f"anchor missing in {path}: {old[:80]}")
    target.write_text(text.replace(old, new, 1))


def sync_schema_head() -> None:
    replace_once(
        "services/local-core/src/book_os_core/backup.py",
        'SUPPORTED_ALEMBIC_REVISION = "0003"',
        'SUPPORTED_ALEMBIC_REVISION = "0004"',
    )
    for path in (
        "services/local-core/tests/test_core.py",
        "services/local-core/tests/test_authority.py",
        "services/local-core/tests/test_projects.py",
        "services/local-core/tests/test_backup_compat.py",
    ):
        target = Path(path)
        text = target.read_text()
        text = text.replace('== "0003"', '== "0004"')
        text = text.replace('== ("0003",)', '== ("0004",)')
        if path.endswith("test_core.py"):
            text = text.replace(
                '{\n            "0001",\n            "0002",\n            "0003",\n        }',
                '{\n            "0001",\n            "0002",\n            "0003",\n            "0004",\n        }',
            )
        target.write_text(text)


def fix_fastapi_error_registration() -> None:
    path = Path("services/local-core/src/book_os_core/app.py")
    text = path.read_text()
    old = '''    @app.exception_handler((ModelProviderError, ModelOutputError, SecretNotFound))
    async def model_execution_error(_: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=502, content={"detail": str(exc)})
'''
    new = '''    @app.exception_handler(ModelProviderError)
    @app.exception_handler(ModelOutputError)
    @app.exception_handler(SecretNotFound)
    async def model_execution_error(_: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=502, content={"detail": str(exc)})
'''
    if old in text:
        text = text.replace(old, new, 1)
    path.write_text(text)


def persist_budget_metadata() -> None:
    path = Path("services/local-core/alembic/versions/0004_m3_model_gateway.py")
    text = path.read_text()
    anchor = '        sa.Column("untrusted_context_json", sa.Text(), nullable=False),\n'
    addition = (
        anchor
        + '        sa.Column("max_output_tokens", sa.Integer(), nullable=False),\n'
        + '        sa.Column("max_cost_usd", sa.Float(), nullable=True),\n'
    )
    if 'sa.Column("max_output_tokens"' not in text:
        text = text.replace(anchor, addition, 1)
    path.write_text(text)

    path = Path("services/local-core/src/book_os_core/drafting.py")
    text = path.read_text()
    old_columns = (
        '"prompt_id,prompt_version,prompt_hash,section_objective,untrusted_context_json,"\n'
        '                        "status,created_at,started_at) VALUES (:task_id,:book_id,:chapter_id,\'SECTION_DRAFT\',"\n'
    )
    new_columns = (
        '"prompt_id,prompt_version,prompt_hash,section_objective,untrusted_context_json,"\n'
        '                        "max_output_tokens,max_cost_usd,status,created_at,started_at) VALUES "\n'
        '                        "(:task_id,:book_id,:chapter_id,\'SECTION_DRAFT\',"\n'
    )
    if old_columns in text:
        text = text.replace(old_columns, new_columns, 1)
        text = text.replace(
            '":objective,:untrusted_context,\'RUNNING\',:created_at,:started_at)"',
            '":objective,:untrusted_context,:max_output_tokens,:max_cost_usd,\'RUNNING\',"\n'
            '                        ":created_at,:started_at)"',
            1,
        )
        text = text.replace(
            '"untrusted_context": canonical_json(\n                            {"items": cast(list[JSONValue], request.untrusted_context)}\n                        ),\n',
            '"untrusted_context": canonical_json(\n                            {"items": cast(list[JSONValue], request.untrusted_context)}\n                        ),\n'
            '                        "max_output_tokens": request.max_output_tokens,\n'
            '                        "max_cost_usd": request.max_cost_usd,\n',
            1,
        )
    path.write_text(text)


def wire_ui() -> None:
    path = Path("apps/desktop/src/App.tsx")
    text = path.read_text()
    import_line = 'import { coreApi } from "./api";\n'
    if 'import { DraftingPanel } from "./DraftingPanel";' not in text:
        text = text.replace(
            import_line,
            import_line + 'import { DraftingPanel } from "./DraftingPanel";\n',
            1,
        )
    render_line = '              <DraftingPanel project={project} chapter={selectedChapter} />\n'
    if render_line not in text:
        anchor = '            </>\n          )}\n        </section>\n'
        index = text.rfind(anchor)
        if index < 0:
            raise SystemExit("App.tsx final fragment anchor missing")
        text = text[:index] + render_line + text[index:]
    path.write_text(text)

    style = Path("apps/desktop/src/styles.css")
    css = style.read_text()
    extra = (
        ".drafting-panel{border-color:#c9bea9}.draft-result{margin-top:20px;padding-top:18px;border-top:1px solid #e1ddd5}"
        ".draft-copy{white-space:pre-wrap;line-height:1.65;padding:18px;background:#f8f5ef;border:1px solid #e2ddd3;border-radius:10px;margin-top:14px}"
        ".provenance-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin:14px 0 0}"
        ".provenance-grid div{padding:10px;background:#f5f2eb;border-radius:8px}.provenance-grid dt{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:#777165}"
        ".provenance-grid dd{margin:4px 0 0;font-size:12px;overflow-wrap:anywhere}.notes-list{color:#6c665d}.inline-alert{margin:16px 0 0}"
    )
    if ".drafting-panel{" not in css:
        style.write_text(css + extra)


sync_schema_head()
fix_fastapi_error_registration()
persist_budget_metadata()
wire_ui()
