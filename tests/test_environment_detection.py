"""Tests for read-only runtime environment detection."""

from pathlib import Path
import tempfile
import unittest

from storyforge.core.environment import detect_environment


class EnvironmentDetectionTests(unittest.TestCase):
    def test_detects_termux_from_prefix(self) -> None:
        info = detect_environment(
            environ={"PREFIX": "/data/data/com.termux/files/usr"},
            os_name="Linux",
            machine="aarch64",
            python_version="3.12.1",
            android_api_level=35,
            meminfo_path=Path("/does/not/exist"),
        )

        self.assertTrue(info.is_android)
        self.assertTrue(info.is_termux)
        self.assertEqual(info.architecture, "arm64")
        self.assertEqual(info.android_api_level, 35)
        self.assertEqual(info.termux_prefix, "/data/data/com.termux/files/usr")

    def test_detects_termux_version_marker(self) -> None:
        info = detect_environment(
            environ={"TERMUX_VERSION": "0.118.0"},
            os_name="Linux",
            machine="x86_64",
            python_version="3.12.1",
            android_api_level=None,
            meminfo_path=Path("/does/not/exist"),
        )

        self.assertTrue(info.is_termux)
        self.assertTrue(info.is_android)

    def test_does_not_misclassify_regular_linux_as_android(self) -> None:
        info = detect_environment(
            environ={"HOME": "/home/test"},
            os_name="Linux",
            machine="x86_64",
            python_version="3.12.1",
            android_api_level=None,
            meminfo_path=Path("/does/not/exist"),
        )

        self.assertFalse(info.is_android)
        self.assertFalse(info.is_termux)

    def test_reads_total_memory_from_procfs_format(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            meminfo = Path(directory) / "meminfo"
            meminfo.write_text(
                "MemTotal:       8192000 kB\nMemFree:         100000 kB\n",
                encoding="ascii",
            )
            info = detect_environment(
                environ={},
                os_name="Linux",
                machine="aarch64",
                python_version="3.12.1",
                android_api_level=None,
                meminfo_path=meminfo,
            )

        self.assertEqual(info.total_memory_bytes, 8192000 * 1024)

    def test_missing_or_unreadable_memory_info_is_nonfatal(self) -> None:
        info = detect_environment(
            environ={},
            os_name="Linux",
            machine="armv7l",
            python_version="3.12.1",
            android_api_level=None,
            meminfo_path=Path("/does/not/exist"),
        )

        self.assertIsNone(info.total_memory_bytes)
        self.assertEqual(info.architecture, "armv7l")


if __name__ == "__main__":
    unittest.main()
