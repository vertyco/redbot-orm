from __future__ import annotations

from pathlib import Path

from redbot_orm.scaffold import create_scaffold


def _relative(path: Path, base: Path) -> Path:
    return path.relative_to(base)


def test_create_scaffold_creates_expected_files(tmp_path: Path) -> None:
    created = create_scaffold(tmp_path)

    expected = {
        Path("db") / "tables.py",
        Path("db") / "piccolo_conf.py",
        Path("db") / "piccolo_app.py",
        Path("db") / "__init__.py",
        Path("db") / "migrations",
        Path("build.py"),
    }

    created_rel = {_relative(path, tmp_path) for path in created}

    assert expected - {Path("db") / "migrations"} <= created_rel
    assert (tmp_path / "db" / "migrations").exists()

    piccolo_conf = (tmp_path / "db" / "piccolo_conf.py").read_text(encoding="utf-8")
    assert "PostgresEngine" in piccolo_conf
    assert "SQLiteEngine" in piccolo_conf
    assert "_has_postgres_credentials" in piccolo_conf

    tables_py = (tmp_path / "db" / "tables.py").read_text(encoding="utf-8")
    assert "UUID(primary_key=True)" in tables_py
    assert "Timestamptz" in tables_py
    assert "auto_update" in tables_py


def test_create_scaffold_respects_overwrite(tmp_path: Path) -> None:
    target = tmp_path / "cog"
    target.mkdir()

    tables_file = target / "db" / "tables.py"
    tables_file.parent.mkdir(parents=True)
    tables_file.write_text("original", encoding="utf-8")

    create_scaffold(target)
    assert tables_file.read_text(encoding="utf-8") == "original"

    create_scaffold(target, overwrite=True)
    assert tables_file.read_text(encoding="utf-8") != "original"
