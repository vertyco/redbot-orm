import os
from pathlib import Path
from unittest import TestCase

from piccolo.engine.sqlite import SQLiteEngine
from piccolo.utils.sync import run_sync
from redbot_orm.sqlite import (
    create_migrations,
    diagnose_issues,
    register_cog,
    run_migrations,
)

from tests_sqlite.tables import TABLES

cog_instance = Path(__file__).parent
migration_dir = cog_instance / "migrations"
db_path = cog_instance / "db.sqlite"


class TestCrud(TestCase):
    def setUp(self):
        os.environ["PICCOLO_CONF"] = "piccolo_conf_sqlite_test"
        # Delete everything in the migration folder
        for file in migration_dir.glob("tests_sqlite*"):
            file.unlink()

    def tearDown(self):
        db_path.unlink(missing_ok=True)
        # Delete everything in the migration folder
        for file in migration_dir.glob("tests_sqlite*"):
            file.unlink()

    def test_diagnose_issues(self):
        result = run_sync(diagnose_issues(cog_instance))
        self.assertIn("Everything OK", result)

    def test_create_migrations(self):
        result = run_sync(
            create_migrations(cog_instance, False, description="Test migration")
        )
        self.assertIsInstance(result, str, "Should return a string")
        self.assertIn("🚀 Creating new migration", result)
        # Now make sure the migration file exists
        migration_files = [
            i for i in migration_dir.iterdir() if i.stem.startswith("tests_sqlite")
        ]
        self.assertEqual(len(migration_files), 1, "Migration file not created")

    def test_register_cog(self):
        result = run_sync(register_cog(cog_instance, TABLES))
        self.assertIsInstance(
            result, SQLiteEngine, "Should return a SQLiteEngine instance"
        )
        self.assertTrue(db_path.exists(), "Database file not created")

    def test_run_migrations(self):
        result = run_sync(run_migrations(cog_instance))
        self.assertIsInstance(result, str, "Should return a string")
        self.assertIn(
            "No migrations need to be run", result, "Should have no migrations"
        )
