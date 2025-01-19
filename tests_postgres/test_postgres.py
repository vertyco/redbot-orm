import os
from pathlib import Path
from unittest import TestCase

from dotenv import load_dotenv
from piccolo.engine.postgres import PostgresEngine
from piccolo.utils.sync import run_sync
from redbot_orm.postgres import (
    acquire_db_engine,
    create_migrations,
    db_name,
    diagnose_issues,
    ensure_database_exists,
    register_cog,
    reverse_migration,
    run_migrations,
)

from tests_postgres.tables import TABLES

load_dotenv()


cog_instance = Path(__file__).parent
migration_dir = cog_instance / "migrations"


def get_connection_info():
    return {
        "user": os.environ.get("POSTGRES_USER"),
        "password": os.environ.get("POSTGRES_PASSWORD"),
        "database": os.environ.get("POSTGRES_DATABASE"),
        "host": os.environ.get("POSTGRES_HOST"),
        "port": os.environ.get("POSTGRES_PORT"),
    }


class TestPostgres(TestCase):
    def setUp(self):
        engine = run_sync(acquire_db_engine(get_connection_info(), ("uuid-ossp",)))
        run_sync(
            engine._run_in_new_connection(
                "DROP DATABASE IF EXISTS tests_postgres WITH (FORCE)"
            )
        )

    def tearDown(self):
        engine = run_sync(acquire_db_engine(get_connection_info(), ("uuid-ossp",)))
        run_sync(
            engine._run_in_new_connection(
                "DROP DATABASE IF EXISTS tests_postgres WITH (FORCE)"
            )
        )
        # Delete everything in the migration folder
        for file in migration_dir.glob("tests_postgres*"):
            file.unlink()

    def test_ensure_database_exists(self):
        created = run_sync(ensure_database_exists(cog_instance, get_connection_info()))
        self.assertTrue(created, "Should return True if database was created")

    def test_create_migrations(self):
        result = run_sync(
            create_migrations(
                cog_instance, get_connection_info(), description="Test migration"
            )
        )
        self.assertIsInstance(result, str, "Should return a string")
        self.assertIn("🚀 Creating new migration", result)
        # Now make sure the migration file exists
        migration_files = [
            i for i in migration_dir.iterdir() if i.stem.startswith("tests_postgres")
        ]
        self.assertEqual(len(migration_files), 1, "Migration file not created")

    def test_register_cog(self):
        cog_engine = run_sync(register_cog(cog_instance, TABLES, get_connection_info()))
        self.assertIsInstance(
            cog_engine, PostgresEngine, "Should return a PostgresEngine instance"
        )

    def test_make_migrations(self):
        res = run_sync(create_migrations(cog_instance, get_connection_info()))
        self.assertIsInstance(res, str, "Should return a string")

    def test_run_migrations(self):
        res = run_sync(run_migrations(cog_instance, get_connection_info()))
        self.assertIsInstance(res, str, "Should return a string")

    def test_diagnose_issues(self):
        res = run_sync(diagnose_issues(cog_instance, get_connection_info()))
        self.assertIsInstance(res, str, "Should return a string")

    def test_reverse_migration(self):
        res = run_sync(
            reverse_migration(cog_instance, get_connection_info(), "20230101")
        )
        self.assertIsInstance(res, str, "Should return a string")

    def test_db_name_from_path(self):
        self.assertEqual(
            db_name(cog_instance),
            "tests_postgres",
            "Should return correct db name from Path",
        )

    def test_db_name_from_cog(self):
        class MockCog:
            qualified_name = "TestCog"

        mock_cog = MockCog()
        self.assertEqual(
            db_name(mock_cog), "testcog", "Should return lowercase cog name"
        )
