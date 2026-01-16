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

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage Examples](#usage-examples)
- [Configuration](#configuration)
- [Development and Migrations](#development-and-migrations)
- [API Reference](#api-reference)
- [Troubleshooting](#troubleshooting)
- [Running Tests](#running-tests-optional)

## Features

- One-line database registration tailored for Red-DiscordBot cogs
- Automatic database creation, table binding, and Piccolo migrations
- Unified API for [PostgreSQL](https://piccolo-orm.readthedocs.io/en/latest/piccolo/engines/postgres_engine.html) and [SQLite](https://piccolo-orm.readthedocs.io/en/latest/piccolo/engines/sqlite_engine.html)
- Safe directory handling and UNC path checks for Windows compatibility
- Guided scaffolding command to bootstrap Piccolo project files

## Installation

```bash
pip install redbot-orm
```

## Quick Start

1. **Scaffold your cog** — run inside your cog folder to generate the Piccolo project structure:

   ```bash
   python -m redbot_orm scaffold .
   # or equivalently:
   redbot-orm scaffold .
   ```

   This creates the `db/` folder, Piccolo config files, migrations directory, and a starter `build.py` script. The generated `piccolo_conf.py` automatically switches between SQLite and Postgres depending on which environment variables are present.

2. **Define your tables** in `db/tables.py`:

   ```python
   from piccolo.columns import BigInt, Text, UUID
   from piccolo.table import Table

   class MyTable(Table):
       id = UUID(primary_key=True)
       guild_id = BigInt(unique=True)
       name = Text()
   ```

3. **Register in your cog's `cog_load`** to automatically create the database, bind tables, and run migrations:

   ```python
   from redbot_orm import register_cog
   from .db.tables import MyTable

   async def cog_load(self) -> None:
       self.db = await register_cog(self, [MyTable])
   ```

4. **Create migrations** when you change your tables by running `build.py` or using the helper functions.

**Expected cog layout:**

```
my_cog/
├── db/
│   ├── __init__.py
│   ├── migrations/
│   ├── piccolo_app.py
│   ├── piccolo_conf.py
│   └── tables.py
├── __init__.py
├── cog.py
└── build.py
```

If you're targeting Postgres, create a `.env` file in your cog's root with the required `POSTGRES_*` variables. Be sure to add `.env` to your `.gitignore` so credentials never end up in version control.

## Usage Examples

### SQLite Example

SQLite is the simplest option, no external database server required. Data is stored in the cog's data directory.

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
        self.db = await register_cog(self, [MyTable])

    async def cog_unload(self) -> None:
        # SQLite is file-based; no connection pool to close.
        pass
```

### PostgreSQL Example

PostgreSQL offers better performance for high-traffic bots and advanced features like JSON columns and full-text search.

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
        # Option A: fetch credentials from Red's shared API tokens (recommended)
        config = await self.bot.get_shared_api_tokens("postgres")

        # Option B: fallback to hardcoded defaults for local development
        if not config:
            config = {
                "database": "postgres",
                "host": "localhost",
                "port": 5432,
                "user": "postgres",
                "password": "postgres",
            }

        self.db = await register_cog(
            self,
            [MyTable],
            config=config,
            max_size=10,
            min_size=1,
            extensions=("uuid-ossp",),
        )

    async def cog_unload(self) -> None:
        if self.db:
            await self.db.close_connection_pool()
```

### Migration Helpers

The unified API exposes helper functions that automatically choose the correct backend based on whether a Postgres `config` is supplied:

| Function | Purpose |
| --- | --- |
| `create_migrations()` | Generates an auto migration |
| `run_migrations()` | Applies all pending forward migrations |
| `reverse_migration()` | Rolls back to a specific timestamp |
| `diagnose_issues()` | Runs Piccolo diagnostics |

```python
from redbot_orm import create_migrations, run_migrations, diagnose_issues

# SQLite (no config)
await run_migrations(cog_instance)

# PostgreSQL (with config)
await run_migrations(cog_instance, config=postgres_config)
```

## Configuration

### PostgreSQL Credentials

You can store Postgres credentials in Red's shared API tokens:

```bash
[p]set api postgres database,mydb host,localhost port,5432 user,postgres password,secret
```

Or as a dictionary in your code:

```python
config = {
    "database": "mydb",
    "host": "localhost",
    "port": 5432,  # Can be int or str
    "user": "postgres",
    "password": "secret",
}
```

### Environment Variables

For local development with the `build.py` script, create an `.env` file:

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DATABASE=mydb
```

> **Warning:** Add `.env` to your `.gitignore` to avoid committing credentials.

## Development and Migrations

The scaffolded `build.py` script provides an interactive way to create migrations during development:

```bash
python build.py
# Enter a description for the migration: added user preferences table
```

This runs `create_migrations()` under the hood. For SQLite, leave the `CONFIG` variable as `None`; for Postgres, populate it from environment variables.

## API Reference

### `register_cog`

```python
async def register_cog(
    cog_or_path,
    tables,
    *,
    config: dict[str, Any] | None = None,
    trace: bool = False,
    skip_migrations: bool = False,
    max_size: int = 20,
    min_size: int = 1,
    extensions: Sequence[str] = ("uuid-ossp",),
) -> PostgresEngine | SQLiteEngine
```

| Parameter | Description |
| --- | --- |
| `cog_or_path` | The cog instance (`self`) or a `Path` to the cog directory |
| `tables` | List of Piccolo `Table` classes to bind to the engine |
| `config` | Postgres connection dict; omit or pass `None` for SQLite |
| `trace` | Enable `--trace` flag for migration commands |
| `skip_migrations` | Skip automatic migration execution |
| `max_size` / `min_size` | Postgres connection pool sizing (ignored for SQLite) |
| `extensions` | Postgres extensions to enable, e.g. `("uuid-ossp",)` |

**Returns:** A fully initialized `PostgresEngine` or `SQLiteEngine` with all tables bound.

### Migration Functions

| Function | Signature |
| --- | --- |
| `create_migrations` | `(cog_or_path, *, config=None, trace=False, description=None, is_shell=True) -> str` |
| `run_migrations` | `(cog_or_path, *, config=None, trace=False) -> str` |
| `reverse_migration` | `(cog_or_path, *, timestamp, config=None, trace=False) -> str` |
| `diagnose_issues` | `(cog_or_path, *, config=None) -> str` |

All functions accept `config` to switch between Postgres and SQLite. Set `is_shell=False` in CI/tests to capture output instead of streaming to stdout.

## Troubleshooting

| Error | Solution |
| --- | --- |
| `ValueError: Postgres options can only be used when a config is provided.` | Provide Postgres credentials via `config`, or remove Postgres-only kwargs (`max_size`, `min_size`, `extensions`) when using SQLite. |
| `FileNotFoundError: Piccolo package not found!` | Install Piccolo in your environment: `pip install piccolo` |
| `DirectoryError: Missing db/piccolo_app.py` | Run `redbot-orm scaffold .` in your cog directory first |
| Migration tracebacks | Re-run with `trace=True` and call `diagnose_issues()` for guidance |
| Tables not appearing | Ensure tables are: (1) defined in `db/tables.py`, (2) listed in `table_finder()` in `piccolo_app.py`, and (3) passed to `register_cog()` |

## Running Tests (Optional)

Integration tests for both backends are included:

```bash
# Activate your virtual environment first
pytest                  # Run all tests
pytest tests_sqlite/    # SQLite only (no setup required)
pytest tests_postgres/  # Postgres only (requires POSTGRES_* env vars)
```

## Additional Notes

- **Database naming:** Each cog gets its own database named after the cog's folder (lowercase).
- **SQLite location:** Databases are stored in the cog's data directory via Red's `cog_data_path`.
- **Postgres auto-creation:** Databases are created automatically; ensure your user has `CREATE DATABASE` privileges.
- **Cross-backend compatibility:** Prefer column types supported by both backends (`UUID`, `Text`, `BigInt`, `Timestamptz`). Gate backend-specific columns behind conditional logic if needed.
- **Connection cleanup:** Always close the Postgres connection pool in `cog_unload` using `await self.db.close_connection_pool()`.
