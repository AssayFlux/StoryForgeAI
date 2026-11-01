"""Regression tests for the initial repository foundation."""

from pathlib import Path
import tomllib
import unittest

import storyforge


ROOT = Path(__file__).resolve().parents[1]


class ProjectFoundationTests(unittest.TestCase):
    def test_package_has_expected_initial_version(self) -> None:
        self.assertEqual(storyforge.__version__, "0.1.0")

    def test_project_metadata_is_valid_and_dependency_free(self) -> None:
        with (ROOT / "pyproject.toml").open("rb") as config_file:
            metadata = tomllib.load(config_file)

        project = metadata["project"]
        self.assertEqual(project["name"], "storyforge-ai")
        self.assertGreaterEqual(project["requires-python"], ">=3.11")
        self.assertEqual(project["dependencies"], [])

    def test_default_configuration_is_valid_toml(self) -> None:
        with (ROOT / "config" / "default.toml").open("rb") as config_file:
            config = tomllib.load(config_file)

        self.assertTrue(config["application"]["offline_first"])
        self.assertFalse(config["application"]["allow_network_by_default"])
        self.assertEqual(config["hardware"]["max_loaded_models"], 1)

    def test_user_generated_data_is_ignored_by_git(self) -> None:
        ignore_rules = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("/models/*", ignore_rules)
        self.assertIn("/projects/*", ignore_rules)


if __name__ == "__main__":
    unittest.main()
