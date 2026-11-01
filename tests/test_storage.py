"""Tests for local data paths and SQLite persistence."""

from pathlib import Path
import sqlite3
import tempfile
import unittest

from storyforge.storage import DataPaths, Database


class DataPathsTests(unittest.TestCase):
    def test_environment_override_takes_precedence(self) -> None:
        paths = DataPaths.from_environment(
            environ={"STORYFORGE_HOME": "~/storyforge-data", "XDG_DATA_HOME": "/xdg"},
            home="/home/test",
        )
        self.assertEqual(paths.root, Path("~/storyforge-data").expanduser().resolve())

    def test_configured_root_is_used_after_environment_override(self) -> None:
        configured = DataPaths.from_environment(
            environ={}, home="/home/test", configured_root="/configured/storyforge"
        )
        overridden = DataPaths.from_environment(
            environ={"STORYFORGE_HOME": "/environment/storyforge"},
            configured_root="/configured/storyforge",
        )
        self.assertEqual(configured.root, Path("/configured/storyforge"))
        self.assertEqual(overridden.root, Path("/environment/storyforge"))

    def test_xdg_and_default_roots_are_resolved(self) -> None:
        xdg = DataPaths.from_environment(
            environ={"XDG_DATA_HOME": "/tmp/app-data"}, home="/home/test"
        )
        default = DataPaths.from_environment(environ={}, home="/home/test")
        self.assertEqual(xdg.root, Path("/tmp/app-data/storyforge-ai"))
        self.assertEqual(default.root, Path("/home/test/.local/share/storyforge-ai"))

    def test_ensure_creates_expected_directories_idempotently(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = DataPaths.from_root(Path(directory) / "data")
            self.assertIs(paths.ensure(), paths)
            paths.ensure()
            for path in (
                paths.root, paths.projects, paths.models, paths.assets,
                paths.cache, paths.backups, paths.logs,
            ):
                self.assertTrue(path.is_dir(), path)


class DatabaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.paths = DataPaths.from_root(self.temp_dir.name).ensure()
        self.database = Database(self.paths.database)

    def test_initializes_schema_and_is_idempotent(self) -> None:
        self.database.initialize()
        self.database.initialize()
        with self.database.connection() as connection:
            tables = {
                row["name"] for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            version = connection.execute(
                "SELECT MAX(version) FROM schema_migrations"
            ).fetchone()[0]
        self.assertTrue({"schema_migrations", "projects", "generation_jobs"} <= tables)
        self.assertEqual(version, 1)

    def test_project_and_job_round_trip(self) -> None:
        self.database.initialize()
        project = self.database.create_project("  Test Story  ")
        self.assertEqual(project["name"], "Test Story")
        self.assertEqual(self.database.get_project(project["id"])["id"], project["id"])

        job = self.database.create_generation_job(
            project["id"], "story_outline", {"language": "en", "chapter": 1}
        )
        self.assertEqual(job["status"], "queued")
        self.assertEqual(job["payload"], {"language": "en", "chapter": 1})
        self.assertEqual(self.database.get_generation_job(job["id"])["payload"], job["payload"])

    def test_rejects_invalid_records_and_enforces_foreign_keys(self) -> None:
        self.database.initialize()
        with self.assertRaises(ValueError):
            self.database.create_project("  ")
        with self.assertRaises(sqlite3.IntegrityError):
            self.database.create_generation_job("missing-project", "story")
        with self.assertRaises(sqlite3.IntegrityError):
            with self.database.connection() as connection:
                connection.execute(
                    "INSERT INTO projects(id, name, created_at, updated_at) "
                    "VALUES ('bad', '', 'now', 'now')"
                )

    def test_rejects_a_database_from_a_newer_schema_version(self) -> None:
        self.database.initialize()
        with self.database.connection() as connection:
            connection.execute(
                "UPDATE schema_migrations SET version = 999 WHERE version = 1"
            )
        with self.assertRaisesRegex(RuntimeError, "newer than supported"):
            self.database.initialize()

    def test_reopens_existing_database_and_checks_integrity(self) -> None:
        self.database.initialize()
        project = self.database.create_project("Persisted project")
        reopened = Database(self.paths.database)
        reopened.initialize()
        self.assertEqual(reopened.get_project(project["id"])["name"], "Persisted project")
        self.assertEqual(reopened.integrity_check(), ["ok"])


if __name__ == "__main__":
    unittest.main()
