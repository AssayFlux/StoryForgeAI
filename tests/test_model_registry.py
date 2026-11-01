"""Tests for explicit local GGUF model registration and integrity checks."""

import hashlib
from pathlib import Path
import sqlite3
import tempfile
import unittest

from storyforge.models import ModelRegistry, ModelRegistryError
from storyforge.storage import DataPaths, Database


def make_gguf(path: Path, payload: bytes = b"fixture weights") -> Path:
    path.write_bytes(b"GGUF" + (3).to_bytes(4, "little") + payload)
    return path


class ModelRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.database = Database(DataPaths.from_root(self.root / "data").database)
        self.registry = ModelRegistry(self.database)
        self.model_path = make_gguf(self.root / "sample.gguf")

    def register(self, **kwargs):
        defaults = {
            "name": "Sample model",
            "license_id": "Apache-2.0",
            "license_name": "Apache License 2.0",
            "source_name": "Local file supplied by user",
            "attribution": "Example attribution",
            "model_id": "sample-model",
        }
        defaults.update(kwargs)
        return self.registry.register_local_model(self.model_path, **defaults)

    def test_registers_metadata_checksum_and_provenance(self) -> None:
        model = self.register(source_uri="https://example.invalid/model")
        self.assertEqual(model["id"], "sample-model")
        self.assertEqual(model["format"], "gguf")
        self.assertEqual(model["integrity_status"], "valid")
        self.assertEqual(model["path"], str(self.model_path.resolve()))
        self.assertEqual(model["size_bytes"], self.model_path.stat().st_size)
        self.assertEqual(
            model["sha256"], hashlib.sha256(self.model_path.read_bytes()).hexdigest()
        )
        self.assertEqual(model["license_id"], "Apache-2.0")
        self.assertEqual(model["source_name"], "Local file supplied by user")
        self.assertEqual(model["attribution"], "Example attribution")
        self.assertTrue(self.model_path.exists(), "registration must not move the source file")

    def test_list_and_reopen_persist_model_metadata(self) -> None:
        self.register()
        reopened = ModelRegistry(Database(self.database.path))
        self.assertEqual(reopened.list_models()[0]["id"], "sample-model")
        self.assertEqual(reopened.get_model("sample-model")["name"], "Sample model")

    def test_rejects_missing_directory_empty_and_invalid_gguf(self) -> None:
        with self.assertRaisesRegex(ModelRegistryError, "does not exist"):
            self.registry.register_local_model(
                self.root / "missing.gguf", name="Missing",
                license_id="MIT", license_name="MIT",
            )
        with self.assertRaisesRegex(ModelRegistryError, "regular file"):
            self.registry.register_local_model(
                self.root, name="Directory", license_id="MIT", license_name="MIT",
            )
        empty = self.root / "empty.gguf"
        empty.touch()
        with self.assertRaisesRegex(ModelRegistryError, "empty"):
            self.registry.register_local_model(
                empty, name="Empty", license_id="MIT", license_name="MIT",
            )
        invalid = self.root / "invalid.gguf"
        invalid.write_bytes(b"not a GGUF file")
        with self.assertRaisesRegex(ModelRegistryError, "GGUF header"):
            self.registry.register_local_model(
                invalid, name="Invalid", license_id="MIT", license_name="MIT",
            )

    def test_rejects_unsupported_header_version_and_missing_license(self) -> None:
        unsupported = self.root / "future.gguf"
        unsupported.write_bytes(b"GGUF" + (99).to_bytes(4, "little") + b"payload")
        with self.assertRaisesRegex(ModelRegistryError, "Unsupported GGUF version"):
            self.registry.register_local_model(
                unsupported, name="Future", license_id="MIT", license_name="MIT",
            )
        with self.assertRaisesRegex(ModelRegistryError, "License ID"):
            self.registry.register_local_model(
                self.model_path, name="No license", license_id=" ", license_name=" ",
            )

    def test_duplicate_id_and_path_are_rejected_without_overwriting(self) -> None:
        self.register()
        with self.assertRaisesRegex(ModelRegistryError, "Could not register model"):
            self.register(name="Second model", model_id="second-id")
        other = make_gguf(self.root / "other.gguf")
        with self.assertRaisesRegex(ModelRegistryError, "Could not register model"):
            self.registry.register_local_model(
                other, name="Duplicate ID", license_id="MIT",
                license_name="MIT", model_id="sample-model",
            )
        self.assertEqual(len(self.registry.list_models()), 1)

    def test_integrity_check_detects_valid_modified_missing_and_invalid(self) -> None:
        self.register()
        self.assertEqual(
            self.registry.check_integrity("sample-model")["integrity_status"], "valid"
        )
        self.model_path.write_bytes(
            b"GGUF" + (3).to_bytes(4, "little") + b"tampered weights"
        )
        self.assertEqual(
            self.registry.check_integrity("sample-model")["integrity_status"], "modified"
        )
        self.model_path.write_bytes(b"not a gguf")
        self.assertEqual(
            self.registry.check_integrity("sample-model")["integrity_status"], "invalid"
        )
        self.model_path.unlink()
        self.assertEqual(
            self.registry.check_integrity("sample-model")["integrity_status"], "missing"
        )

    def test_unknown_model_integrity_check_is_rejected(self) -> None:
        with self.assertRaisesRegex(ModelRegistryError, "Unknown model ID"):
            self.registry.check_integrity("unknown")

    def test_schema_v1_database_migrates_to_v2_and_is_idempotent(self) -> None:
        self.database.initialize()
        with self.database.connection() as connection:
            connection.execute("DELETE FROM schema_migrations WHERE version = 2")
        # Recreate a genuine v1 migration state, then ensure v2 applies once.
        with self.database.connection() as connection:
            connection.execute("DROP TABLE model_licenses")
            connection.execute("DROP TABLE model_files")
            connection.execute("DROP TABLE models")
        self.database.initialize()
        self.database.initialize()
        with self.database.connection() as connection:
            versions = [
                row[0] for row in connection.execute(
                    "SELECT version FROM schema_migrations ORDER BY version"
                )
            ]
            tables = {
                row[0] for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
        self.assertEqual(versions, [1, 2])
        self.assertTrue({"models", "model_files", "model_licenses"} <= tables)

    def test_database_constraints_and_integrity(self) -> None:
        self.register()
        with self.assertRaises(sqlite3.IntegrityError):
            with self.database.connection() as connection:
                connection.execute(
                    "INSERT INTO models(id, name, format, created_at, updated_at) "
                    "VALUES ('bad', 'Bad', 'safetensors', 'now', 'now')"
                )
        self.assertEqual(self.database.integrity_check(), ["ok"])


if __name__ == "__main__":
    unittest.main()
