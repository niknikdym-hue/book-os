from pathlib import Path

TESTS = Path("services/local-core/tests")


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one match, got {count}: {old!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_once(
    TESTS / "test_authority.py",
    '        assert connection.execute("SELECT version_num FROM alembic_version").fetchone() == ("0015",)\n',
    '        assert connection.execute("SELECT version_num FROM alembic_version").fetchone() == ("0016",)\n',
)

for name in ("test_bookbench.py", "test_editorial.py", "test_memory.py"):
    replace_once(
        TESTS / name,
        '            == "0015"\n',
        '            == "0016"\n',
    )

replace_once(
    TESTS / "test_research.py",
    '            == "0015"\n',
    '            == "0016"\n',
)
