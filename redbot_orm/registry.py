from __future__ import annotations

import typing as t
from pathlib import Path

from discord.ext import commands
from piccolo.engine.postgres import PostgresEngine
from piccolo.engine.sqlite import SQLiteEngine
from piccolo.table import Table

from . import postgres as postgres_impl
from . import sqlite as sqlite_impl

Config = dict[str, t.Any]
Tables = list[type[Table]]
Engine = PostgresEngine | SQLiteEngine


async def register_cog(
    cog_instance: commands.Cog | Path,
    tables: Tables,
    *,
    config: Config | None = None,
    trace: bool = False,
    skip_migrations: bool = False,
    max_size: int = 20,
    min_size: int = 1,
    extensions: tuple[str, ...] = ("uuid-ossp",),
) -> Engine:
    if config is not None and len(config) == 0:
        config = None
    if config is None and (
        max_size != 20 or min_size != 1 or extensions != ("uuid-ossp",)
    ):
        raise ValueError("Postgres options can only be used when a config is provided.")
    if config is not None:
        return await postgres_impl.register_cog(
            cog_instance,
            tables,
            config,
            trace=trace,
            max_size=max_size,
            min_size=min_size,
            skip_migrations=skip_migrations,
            extensions=list(extensions),
        )
    return await sqlite_impl.register_cog(
        cog_instance,
        tables,
        trace=trace,
        skip_migrations=skip_migrations,
    )


async def run_migrations(
    cog_instance: commands.Cog | Path,
    *,
    config: Config | None = None,
    trace: bool = False,
) -> str:
    if config is not None and len(config) == 0:
        config = None
    if config is not None:
        return await postgres_impl.run_migrations(
            cog_instance,
            config,
            trace=trace,
        )
    return await sqlite_impl.run_migrations(
        cog_instance,
        trace=trace,
    )


async def reverse_migration(
    cog_instance: commands.Cog | Path,
    *,
    timestamp: str,
    config: Config | None = None,
    trace: bool = False,
) -> str:
    if config is not None and len(config) == 0:
        config = None
    if config is not None:
        return await postgres_impl.reverse_migration(
            cog_instance,
            config,
            timestamp,
            trace=trace,
        )
    return await sqlite_impl.reverse_migration(
        cog_instance,
        timestamp,
        trace=trace,
    )


async def create_migrations(
    cog_instance: commands.Cog | Path,
    *,
    config: Config | None = None,
    trace: bool = False,
    description: str | None = None,
    is_shell: bool = True,
) -> str:
    if config is not None and len(config) == 0:
        config = None
    if config is not None:
        return await postgres_impl.create_migrations(
            cog_instance,
            config,
            trace=trace,
            description=description,
            is_shell=is_shell,
        )
    return await sqlite_impl.create_migrations(
        cog_instance,
        trace=trace,
        description=description,
        is_shell=is_shell,
    )


async def diagnose_issues(
    cog_instance: commands.Cog | Path,
    *,
    config: Config | None = None,
) -> str:
    if config is not None and len(config) == 0:
        config = None
    if config is not None:
        return await postgres_impl.diagnose_issues(
            cog_instance,
            config,
        )
    return await sqlite_impl.diagnose_issues(
        cog_instance,
    )
