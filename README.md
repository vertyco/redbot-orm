# redbot-orm

Database ORM integration for [Red-DiscordBot](https://github.com/Cog-Creators/Red-DiscordBot) cogs using [Piccolo ORM](https://piccolo-orm.readthedocs.io/en/latest/). Supports both PostgreSQL and SQLite.

[![PyPi](https://img.shields.io/pypi/v/redbot-orm)](https://pypi.org/project/redbot-orm/)
[![Pythons](https://img.shields.io/pypi/pyversions/redbot-orm)](https://pypi.org/project/redbot-orm/)

![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?logo=postgresql&logoColor=white)
![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?logo=sqlite&logoColor=white)
![Red-DiscordBot](https://img.shields.io/badge/Red%20DiscordBot-V3.5-red)

![black](https://img.shields.io/badge/style-black-000000?link=https://github.com/psf/black)
![license](https://img.shields.io/github/license/Vertyco/redbot-orm)

## Features

- Easy database integration for [Red-DiscordBot](https://github.com/Cog-Creators/Red-DiscordBot) cogs
- Support for both [PostgreSQL](https://piccolo-orm.readthedocs.io/en/latest/piccolo/engines/postgres_engine.html) and [SQLite](https://piccolo-orm.readthedocs.io/en/latest/piccolo/engines/sqlite_engine.html)
- Automatic database creation and [migration handling](https://piccolo-orm.readthedocs.io/en/latest/piccolo/migrations/create.html#auto-migrations)
- Clean separation of databases between different cogs
- Works with any Discord.py bot (not just Red)

## Installation

```bash
pip install redbot-orm
```

## File Structure

```
cog-folder/
    ├── db/
    │   ├── migrations/
    │   ├── piccolo_conf.py
    │   ├── piccolo_app.py
    │   ├── tables.py
    ├── __init__.py
    ├── cog.py
```

## Usage Examples

### PostgreSQL Example

```python
from redbot.core import commands
from redbot.core.bot import Red
from piccolo.engine.postgres import PostgresEngine
from redbot_orm.postgres import register_cog
from .db.tables import MyTable

class PostgresCog(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.db: PostgresEngine = None

    async def cog_load(self):
        config = await self.bot.get_shared_api_tokens("postgres")
        # OR
        config = {  # Example
            "database": "postgres",
            "host": "localhost",
            "port": "5432",
            "user": "postgres",
            "password": "postgres"
        }
        self.db = await register_cog(self, [MyTable], config)

    async def cog_unload(self):
        if self.db:
            self.db.pool.terminate()
```

### SQLite Example

```python
from redbot.core import commands
from redbot.core.bot import Red
from piccolo.engine.sqlite import SQLiteEngine
from redbot_orm.sqlite import register_cog
from .db.tables import MyTable

class SQLiteCog(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.db: SQLiteEngine = None

    async def cog_load(self):
        self.db = await register_cog(self, [MyTable])
```

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

Create a `build.py` for managing migrations:

```python
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from redbot_orm import postgres

load_dotenv()

config = {
    "user": os.environ.get("POSTGRES_USER"),
    "password": os.environ.get("POSTGRES_PASSWORD"),
    "database": os.environ.get("POSTGRES_DATABASE"),
    "host": os.environ.get("POSTGRES_HOST"),
    "port": os.environ.get("POSTGRES_PORT"),
}

root = Path(__file__).parent

async def main():
    description = input("Enter a description for the migration: ")
    print(await postgres.create_migrations(root, config, True, description))
    print(await postgres.run_migrations(root, config, True))

if __name__ == "__main__":
    asyncio.run(main())
```

## Notes

- Each cog gets its own database named after the cog's folder name (lowercase)
- For SQLite, databases are stored in the cog's data folder
- Migrations are handled automatically when the cog loads
