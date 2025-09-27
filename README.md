# redbot-orm

Database ORM integration for [Red-DiscordBot](https://github.com/Cog-Creators/Red-DiscordBot) cogs using [Piccolo ORM](https://piccolo-orm.readthedocs.io/en/latest/).

`redbot-orm` streamlines database setup, migrations, and lifecycle management for both PostgreSQL and SQLite backends, so cog authors can focus on their domain logic instead of plumbing.

> **Note:** The helpers rely on Red-DiscordBot's data manager and event hooks; they aren't intended as a drop-in replacement for arbitrary `discord.py` bots.

[![PyPi](https://img.shields.io/pypi/v/redbot-orm)](https://pypi.org/project/redbot-orm/)
[![Pythons](https://img.shields.io/pypi/pyversions/redbot-orm)](https://pypi.org/project/redbot-orm/)

![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?logo=postgresql&logoColor=white)
![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?logo=sqlite&logoColor=white)
![Red-DiscordBot](https://img.shields.io/badge/Red%20DiscordBot-V3.5-red)

![black](https://img.shields.io/badge/style-black-000000?link=https://github.com/psf/black)
![license](https://img.shields.io/github/license/Vertyco/redbot-orm)

## Features

- One-line database registration tailored for Red-DiscordBot cogs
- Automatic database creation, table binding, and Piccolo migrations
- Unified API for [PostgreSQL](https://piccolo-orm.readthedocs.io/en/latest/piccolo/engines/postgres_engine.html) and [SQLite](https://piccolo-orm.readthedocs.io/en/latest/piccolo/engines/sqlite_engine.html)
- Safe directory handling and UNC path checks for Windows compatibility
- Guided scaffolding command to bootstrap Piccolo project files

## Installation
```python
from redbot.core import commands
from redbot.core.bot import Red
from piccolo.engine.sqlite import SQLiteEngine
from redbot_orm import register_cog
from .db.tables import MyTable


class SQLiteCog(commands.Cog):
    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.db: SQLiteEngine | None = None

    async def cog_load(self) -> None:
        self.db = await register_cog(
            self,
            [MyTable],
            trace=False,
            skip_migrations=False,
        )

    async def cog_unload(self) -> None:
        # SQLite uses file-based storage and no connection pools.
        pass
```

Example cog layout:

```
cog-folder/
├── db/
│   ├── migrations/
│   ├── piccolo_conf.py
│   ├── piccolo_app.py
│   └── tables.py
├── __init__.py
└── cog.py
```

Generate the Piccolo scaffolding with the built-in helper:

```powershell
python -m redbot_orm scaffold .
```

This command (or the equivalent `redbot-orm scaffold .`) creates the `db` folder, Piccolo config files, migrations directory, and a starter `build.py` script in the target directory (use `.` for the current cog root). The generated `piccolo_conf.py` automatically switches between SQLite and Postgres depending on which environment variables are present, so you can target either backend without editing the file.

## Quick Start

1. Install the package (`pip install redbot-orm`).
2. Run `python -m redbot_orm scaffold .` inside your cog folder to generate the Piccolo project structure.
3. Define your Piccolo `Table` classes in `db/tables.py`.
4. Call `register_cog` inside your cog's `cog_load` method to automatically create the database, bind tables, and run migrations.
5. Use the helper utilities to create or run migrations from scripts or CI.

The generated Piccolo configuration already reads from environment variables, so in most cases no manual edits are required.

If you're targeting Postgres, create a `.env` file in your cog's root with the required `POSTGRES_*` variables. Be sure to add `.env` to your cog's `.gitignore` so credentials never end up in version control.

## Usage Examples

### PostgreSQL Example

```python
from redbot.core import commands
from redbot.core.bot import Red
from piccolo.engine.postgres import PostgresEngine
from redbot_orm import register_cog
from .db.tables import MyTable


class PostgresCog(commands.Cog):
    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.db: PostgresEngine | None = None

    async def cog_load(self) -> None:
        # Option A: fetch a shared Red API token (recommended for hosted bots)
        config = await self.bot.get_shared_api_tokens("postgres")

        # Option B: load from environment variables / .env file
        if not config:
            config = {
                "database": "postgres",
                "host": "localhost",
                "port": "5432",
                "user": "postgres",
                "password": "postgres",
            }

        self.db = await register_cog(
            self,
            [MyTable],
            config=config,
            trace=False,
            skip_migrations=False,
            max_size=10,
            min_size=1,
            extensions=("uuid-ossp",),
        )

    async def cog_unload(self) -> None:
        if self.db:
            self.db.pool.terminate()
```

### SQLite Example

```python
from redbot.core import commands
from redbot.core.bot import Red
from piccolo.engine.sqlite import SQLiteEngine
from redbot_orm import register_cog
from .db.tables import MyTable

class SQLiteCog(commands.Cog):
    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.db: SQLiteEngine | None = None

    async def cog_load(self) -> None:
        self.db = await register_cog(
            self,
            [MyTable],
            trace=False,
            skip_migrations=False,
        )

    async def cog_unload(self) -> None:
        # SQLite uses file-based storage and no connection pools.
        pass

```

### Migration Helpers

The unified API also exposes helper functions which automatically choose the correct backend based on whether a Postgres `config` is supplied:

- `create_migrations(cog_or_path, *, config=None, trace=False, description=None, is_shell=True)`
- `run_migrations(cog_or_path, *, config=None, trace=False)`
- `reverse_migration(cog_or_path, *, timestamp, config=None, trace=False)`
- `diagnose_issues(cog_or_path, *, config=None)`

Pass your Postgres connection dictionary via `config` to target Postgres; omit it to operate on SQLite data stored in the cog's data folder.

## Configuration

### PostgreSQL Configuration
Required shared API tokens for PostgreSQL:

```json
{
    "database": "postgres",
    "host": "127.0.0.1",
    "port": "5432",
    "user": "postgres",
    "password": "postgres"
}
```

### Piccolo Configuration Files

#### piccolo_conf.py
```python
import os
from piccolo.conf.apps import AppRegistry
from piccolo.engine.postgres import PostgresEngine

DB = PostgresEngine(
    config={
        "database": os.environ.get("POSTGRES_DATABASE"),
        "user": os.environ.get("POSTGRES_USER"),
        "password": os.environ.get("POSTGRES_PASSWORD"),
        "host": os.environ.get("POSTGRES_HOST"),
        "port": os.environ.get("POSTGRES_PORT"),
    }
)

APP_REGISTRY = AppRegistry(apps=["db.piccolo_app"])
```

#### piccolo_app.py
```python
import os
from piccolo.conf.apps import AppConfig, table_finder

CURRENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))

APP_CONFIG = AppConfig(
    app_name=os.getenv("APP_NAME"),
    table_classes=table_finder(["db.tables"]),
    migrations_folder_path=os.path.join(CURRENT_DIRECTORY, "migrations"),
)
```

## Development and Migrations

For local development, create an `.env` file in your cog's root:

```env
# Only for PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DATABASE=postgres
```

Keep this file alongside your cog during development, but list `.env` in your `.gitignore` (and any repo-specific ignore files) to avoid committing secrets.

Create a `build.py` for managing migrations:

```python
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

from redbot_orm import create_migrations, diagnose_issues, run_migrations


load_dotenv()

config = {
    "user": os.environ.get("POSTGRES_USER"),
    "password": os.environ.get("POSTGRES_PASSWORD"),
    "database": os.environ.get("POSTGRES_DATABASE"),
    "host": os.environ.get("POSTGRES_HOST"),
    "port": os.environ.get("POSTGRES_PORT"),
}

root = Path(__file__).parent


async def main() -> None:
    description = input("Enter a description for the migration: ")
    try:
        result = await create_migrations(
            root,
            config=config,
            trace=True,
            description=description,
            is_shell=True,
        )
        if "The command failed." in result:
            raise Exception("Migration creation failed")
        print(result)
    except Exception as e:
        print(f"Error creating migrations: {e}")
        print(await diagnose_issues(root, config=config))


if __name__ == "__main__":
    asyncio.run(main())
```

## API Reference

### `register_cog`

```python
await register_cog(
    cog_or_path,
    tables,
    *,
    config: dict[str, object] | None = None,
    trace: bool = False,
    skip_migrations: bool = False,
    max_size: int = 20,
    min_size: int = 1,
    extensions: tuple[str, ...] = ("uuid-ossp",),
)
```

- `cog_or_path`: the Cog instance (`self`) or a `Path` to the cog directory.
- `tables`: iterable of Piccolo `Table` classes to bind to the database engine.
- `config`: Postgres connection details. Leave `None` to use SQLite.
- `trace`: forwards the `--trace` flag to Piccolo migration commands.
- `skip_migrations`: if `True`, migrations are not executed automatically.
- `max_size` / `min_size`: Postgres connection pool sizing (ignored for SQLite).
- `extensions`: Postgres extensions to enable (e.g. `uuid-ossp`).

Returns a fully initialised `PostgresEngine` or `SQLiteEngine` with all provided tables bound via Piccolo.

### Migration Helpers

All helper functions accept the same `config` switch to choose Postgres vs SQLite:

| Function | Purpose |
| --- | --- |
| `create_migrations(cog_or_path, *, config=None, trace=False, description=None, is_shell=True)` | Generates an auto migration (`piccolo migrations new --auto`). Set `is_shell=False` for CI/tests to capture output instead of streaming to stdout. |
| `run_migrations(cog_or_path, *, config=None, trace=False)` | Applies all forward migrations (`piccolo migrations forwards`). |
| `reverse_migration(cog_or_path, *, timestamp, config=None, trace=False)` | Rolls back migrations to the given timestamp (`piccolo migrations backwards`). |
| `diagnose_issues(cog_or_path, *, config=None)` | Runs Piccolo diagnostics (`piccolo --diagnose` + `migrations check`). |

## Troubleshooting

- **`ValueError: Postgres options can only be used when a config is provided.`** → Provide Postgres credentials via `config`, or omit Postgres-only kwargs when using SQLite.
- **`FileNotFoundError: Piccolo package not found!`** → Ensure the Piccolo CLI is installed in the active environment (`pip install piccolo`).
- **Migration output contains tracebacks** → Re-run with `trace=True` and call `diagnose_issues` for more detailed guidance.
- **Tables not appearing in the database** → Confirm each table class is (a) imported in `db/tables.py`, (b) returned by `table_finder` in `piccolo_app.py`, and (c) passed to `register_cog`.

## Running Tests (Optional)

Integration tests for both backends are included. With your virtual environment activated run:

```powershell
python -m pytest
```

The SQLite tests require no additional setup. The Postgres tests expect a database accessible through the usual `POSTGRES_*` environment variables.

## Additional Notes

- Each cog gets its own database named after the cog's folder name (lowercase).
- SQLite databases live inside the cog's data directory, managed by Red's `cog_data_path` helper.
- Postgres databases are created automatically when missing; ensure your user has `CREATE DATABASE` privileges.
- Not every Piccolo column type behaves the same across SQLite and Postgres—prefer types supported by both backends (like `UUID`, `Text`, `BigInt`, `Timestamptz`) or gate backend-specific columns behind conditional migrations.
- When using Postgres, remember to close the connection pool in `cog_unload` (as shown in the example).
