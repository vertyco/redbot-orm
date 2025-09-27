from __future__ import annotations

import textwrap
from pathlib import Path

__all__ = ["create_scaffold"]

_DIRECTORIES: tuple[Path, ...] = (
    Path("db"),
    Path("db") / "migrations",
)

_FILES: dict[Path, str] = {
    Path("db") / "tables.py": textwrap.dedent(
        """
        from piccolo.columns import BigInt, Timestamptz, Text, UUID
        from piccolo.columns.defaults.timestamptz import TimestamptzNow
        from piccolo.table import Table


        class Example(Table):
            id = UUID(primary_key=True)
            guild_id = BigInt(unique=True)
            name = Text()
            created_at = Timestamptz()  # Defaults to UTC
            updated_at = Timestamptz(auto_update=TimestamptzNow().python)
        """
    ).strip()
    + "\n",
    Path("db") / "piccolo_conf.py": textwrap.dedent(
        """
        import os

        from piccolo.conf.apps import AppRegistry
        from piccolo.engine.postgres import PostgresEngine
        from piccolo.engine.sqlite import SQLiteEngine


        def _has_postgres_credentials() -> bool:
            return any(
                os.environ.get(key)
                for key in (
                    "POSTGRES_DATABASE",
                    "POSTGRES_USER",
                    "POSTGRES_PASSWORD",
                    "POSTGRES_HOST",
                    "POSTGRES_PORT",
                )
            )


        if _has_postgres_credentials():
            DB = PostgresEngine(
                config={
                    "database": os.environ.get("POSTGRES_DATABASE", "postgres"),
                    "user": os.environ.get("POSTGRES_USER", "postgres"),
                    "password": os.environ.get("POSTGRES_PASSWORD", "postgres"),
                    "host": os.environ.get("POSTGRES_HOST", "localhost"),
                    "port": os.environ.get("POSTGRES_PORT", "5432"),
                }
            )
        else:
            DB = SQLiteEngine(path=os.environ["DB_PATH"])


        APP_REGISTRY = AppRegistry(apps=["db.piccolo_app"])
        """
    ).strip()
    + "\n",
    Path("db") / "piccolo_app.py": textwrap.dedent(
        """
        import os
        from piccolo.conf.apps import AppConfig, table_finder


        CURRENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


        APP_CONFIG = AppConfig(
            app_name=os.getenv("APP_NAME"),
            table_classes=table_finder(["db.tables"]),
            migrations_folder_path=os.path.join(CURRENT_DIRECTORY, "migrations"),
        )
        """
    ).strip()
    + "\n",
    Path("db") / "__init__.py": "__all__ = ['tables']\n",
    Path("build.py"): textwrap.dedent(
        """
        from __future__ import annotations

        import asyncio
        import os
        from pathlib import Path

        from dotenv import load_dotenv

        from redbot_orm import create_migrations, diagnose_issues, run_migrations


        load_dotenv()


        CONFIG = {
            "user": os.environ.get("POSTGRES_USER"),
            "password": os.environ.get("POSTGRES_PASSWORD"),
            "database": os.environ.get("POSTGRES_DATABASE"),
            "host": os.environ.get("POSTGRES_HOST"),
            "port": os.environ.get("POSTGRES_PORT"),
        }
        # SET CONFIG TO None TO USE SQLITE
        if not any(CONFIG.values()):
            CONFIG = None


        ROOT = Path(__file__).parent


        async def main() -> None:
            description = input("Enter a description for the migration: ")

            try:
                result = await create_migrations(
                    ROOT,
                    config=CONFIG,
                    trace=True,
                    description=description,
                    is_shell=True,
                )
                if not result:
                    print("No migration changes detected.")
                    return
                print(result)
            except Exception as exc:
                print(f"Error creating migrations: {exc}")
                print(await diagnose_issues(ROOT, config=CONFIG))

            print(await run_migrations(ROOT, config=CONFIG, trace=True))


        if __name__ == "__main__":
            asyncio.run(main())
        """
    ).strip()
    + "\n",
}


def create_scaffold(target: Path | str, *, overwrite: bool = False) -> list[Path]:
    """Create the standard redbot-orm directory and file layout."""

    base = Path(target).expanduser().resolve()
    created: list[Path] = []

    for directory in _DIRECTORIES:
        directory_path = base / directory
        directory_path.mkdir(parents=True, exist_ok=True)

    for relative_path, content in _FILES.items():
        file_path = base / relative_path
        if file_path.exists() and not overwrite:
            continue
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        created.append(file_path)

    return created
