import asyncio
import logging
import os
import typing as t
from collections.abc import Sequence
from pathlib import Path

import asyncpg
from discord.ext import commands
from piccolo.engine.postgres import PostgresEngine
from piccolo.table import Table

from .common import find_piccolo_executable, get_root, is_unc_path, run_shell
from .errors import ConnectionTimeoutError, DirectoryError, UNCPathError

log = logging.getLogger("red.orm.postgres")


async def register_cog(
    cog_instance: commands.Cog | Path,
    tables: list[type[Table]],
    config: dict[str, t.Any],
    *,
    trace: bool = False,
    max_size: int = 20,
    min_size: int = 1,
    skip_migrations: bool = False,
    extensions: Sequence[str] = ("uuid-ossp",),
) -> PostgresEngine:
    """Registers a Discord cog with a database connection and runs migrations.

    Args:
        cog_instance (commands.Cog | Path): The instance/path of the cog to register.
        tables (list[type[Table]]): List of Piccolo Table classes to associate with the database engine.
        config (dict): Configuration dictionary containing database connection details.
        trace (bool, optional): Whether to enable tracing for migrations. Defaults to False.
        max_size (int, optional): Maximum size of the database connection pool. Defaults to 20.
        min_size (int, optional): Minimum size of the database connection pool. Defaults to 1.
        skip_migrations (bool, optional): Whether to skip running migrations. Defaults to False.
        extensions (Sequence[str], optional): Postgres extensions to enable. Defaults to ("uuid-ossp",).

    Raises:
        UNCPathError: If the cog path is a UNC path, which is not supported.
        DirectoryError: If the cog files are not in a valid directory.

    Returns:
        PostgresEngine: The database engine associated with the registered cog.
    """
    assert isinstance(cog_instance, (commands.Cog, Path)), (
        "cog_instance must be a Cog instance or a Path to the cog directory"
    )
    cog_path = get_root(cog_instance)
    if is_unc_path(cog_path):
        raise UNCPathError(
            f"UNC paths are not supported, please move the cog's location: {cog_path}"
        )
    if not cog_path.is_dir():
        raise DirectoryError(f"Cog files are not in a valid directory: {cog_path}")

    # Only validate piccolo_app.py on disk when the user is relying on the
    # default scaffolded config.  When PICCOLO_CONF is already set the user
    # manages their own Piccolo configuration (e.g. via an installed package).
    if "PICCOLO_CONF" not in os.environ:
        db_folder = cog_path / "db"
        has_piccolo_app = (db_folder / "piccolo_app.py").exists() or (
            cog_path / "piccolo_app.py"
        ).exists()
        if not has_piccolo_app:
            raise DirectoryError(
                f"Missing piccolo_app.py in {cog_path} - run `redbot-orm scaffold` first"
            )

    if await ensure_database_exists(cog_instance, config):
        log.info(f"New database created for {cog_path.stem}")

    if not skip_migrations:
        log.info("Running migrations, if any")
        result = await run_migrations(cog_instance, config, trace)
        if "No migrations need to be run" in result:
            log.info("No migrations needed ✓")
        elif result:
            log.info(f"Migration result...\n{result}")
            if "Traceback" in result:
                diagnoses = await diagnose_issues(cog_instance, config)
                log.error(diagnoses + "\nOne or more migrations failed to run!")
        else:
            log.warning("No output from migration command, check your configuration and logs if things aren't working")

    temp_config = config.copy()
    temp_config["database"] = db_name(cog_instance)
    log.debug("Fetching database engine")
    engine = await acquire_db_engine(temp_config, extensions)
    log.debug("Database engine acquired, starting pool")
    await engine.start_connection_pool(min_size=min_size, max_size=max_size)
    log.info("Database connection pool started ✓")
    for table_class in tables:
        table_class._meta.db = engine
    return engine


async def run_migrations(
    cog_instance: commands.Cog | Path,
    config: dict[str, t.Any],
    trace: bool = False,
) -> str:
    """Runs database migrations for a given Discord cog.

    Args:
        cog_instance (commands.Cog | Path): The instance of the cog for which to run migrations.
        config (dict): Database connection details.
        trace (bool, optional): Whether to enable tracing for migrations. Defaults to False.

    Returns:
        str: The result of the migration process, including any output messages.
    """
    temp_config = config.copy()
    temp_config["database"] = db_name(cog_instance)
    commands = [
        str(find_piccolo_executable()),
        "migrations",
        "forwards",
        get_root(cog_instance).stem,
    ]
    if trace:
        commands.append("--trace")
    return await run_shell(cog_instance, commands, False, temp_config)


async def reverse_migration(
    cog_instance: commands.Cog | Path,
    config: dict[str, t.Any],
    timestamp: str,
    trace: bool = False,
) -> str:
    """Reverses a database migration for a given Discord cog to a specific timestamp.

    Args:
        cog_instance (commands.Cog | Path): The instance of the cog for which to reverse the migration.
        config (dict): Configuration dictionary containing database connection details.
        timestamp (str): The timestamp to which the migration should be reversed.
        trace (bool, optional): Whether to enable tracing for migrations. Defaults to False.

    Returns:
        str: The result of the reverse migration process, including any output messages.
    """
    temp_config = config.copy()
    temp_config["database"] = db_name(cog_instance)
    commands = [
        str(find_piccolo_executable()),
        "migrations",
        "backwards",
        get_root(cog_instance).stem,
        timestamp,
    ]
    if trace:
        commands.append("--trace")
    return await run_shell(cog_instance, commands, False, temp_config)


async def create_migrations(
    cog_instance: commands.Cog | Path,
    config: dict[str, t.Any],
    trace: bool = False,
    description: str | None = None,
    *,
    is_shell: bool = True,
) -> str:
    """Creates new database migrations for the cog

    THIS SHOULD BE RUN MANUALLY!

    Args:
        cog_instance (commands.Cog | Path): The instance of the cog for which to create migrations.
        config (dict): Configuration dictionary containing database connection details.
        trace (bool, optional): Whether to enable tracing for migrations. Defaults to False.
        description (str | None, optional): Description of the migration. Defaults to None.
        is_shell (bool, optional): Whether to stream output directly to the shell. Defaults to True.

    Returns:
        str: The result of the migration creation process, including any output messages.
    """
    temp_config = config.copy()
    temp_config["database"] = db_name(cog_instance)
    commands = [
        str(find_piccolo_executable()),
        "migrations",
        "new",
        get_root(cog_instance).stem,
        "--auto",
    ]
    if trace:
        commands.append("--trace")
    if description is not None:
        commands.append(f"--desc={description}")
    return await run_shell(cog_instance, commands, is_shell, temp_config)


async def diagnose_issues(
    cog_instance: commands.Cog | Path,
    config: dict[str, t.Any],
) -> str:
    """Diagnoses potential issues with the database setup for a given Discord cog.

    Args:
        cog_instance (commands.Cog | Path): The instance of the cog to diagnose.
        config (dict): Configuration dictionary containing database connection details.

    Returns:
        str: The result of the diagnosis process, including any output messages.
    """
    piccolo_path = find_piccolo_executable()
    temp_config = config.copy()
    temp_config["database"] = db_name(cog_instance)
    diagnoses = await run_shell(
        cog_instance,
        [str(piccolo_path), "--diagnose"],
        False,
        temp_config,
    )
    check = await run_shell(
        cog_instance,
        [str(piccolo_path), "migrations", "check"],
        False,
        temp_config,
    )
    return f"{diagnoses}\n{check}"


async def ensure_database_exists(
    cog_instance: commands.Cog | Path,
    config: dict[str, t.Any],
) -> bool:
    """Create a database for the cog if it doesn't exist.

    Args:
        cog_instance (commands.Cog | Path): The cog instance
        config (dict): the database connection information

    Returns:
        bool: True if a new database was created
    """
    tmp_config = config.copy()
    tmp_config["timeout"] = 10
    conn = await asyncpg.connect(**tmp_config)
    database_name = db_name(cog_instance)
    try:
        databases = await conn.fetch("SELECT datname FROM pg_database;")
        if database_name not in [db["datname"] for db in databases]:
            escaped_name = '"' + database_name.replace('"', '""') + '"'
            await conn.execute(f"CREATE DATABASE {escaped_name};")
            return True
    finally:
        await conn.close()
    return False


async def acquire_db_engine(config: dict, extensions: Sequence[str]) -> PostgresEngine:
    """Acquire a database engine
    The PostgresEngine constructor is blocking and must be run in a separate thread.

    Args:
        config (dict): The database connection information
        extensions (Sequence[str]): The Postgres extensions to enable

    Returns:
        PostgresEngine: The database engine
    """

    async def get_conn():
        return await asyncio.to_thread(
            PostgresEngine,
            config=config,
            extensions=extensions,
        )

    try:
        return await asyncio.wait_for(get_conn(), timeout=10)
    except asyncio.TimeoutError:
        raise ConnectionTimeoutError("Database connection timed out")


def db_name(cog_instance: commands.Cog | Path) -> str:
    """Get the name of the database for the cog

    Args:
        cog_instance (commands.Cog | Path): The cog instance

    Returns:
        str: The database name
    """
    if isinstance(cog_instance, Path):
        return cog_instance.stem.lower()
    return cog_instance.qualified_name.lower()
