from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import windows_app


class StorageDirectoryTests(unittest.TestCase):
    def test_source_mode_uses_application_directory(self) -> None:
        with patch.object(windows_app.sys, "frozen", False, create=True):
            with patch.object(
                windows_app,
                "application_directory",
                return_value=Path("C:/Time-Tracker"),
            ):
                self.assertEqual(
                    windows_app.storage_directory(),
                    Path("C:/Time-Tracker"),
                )

    def test_portable_mode_uses_executable_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            executable_directory = Path(directory)
            marker = executable_directory / windows_app.PORTABLE_MARKER
            marker.touch()

            with patch.object(windows_app.sys, "frozen", True, create=True):
                with patch.object(
                    windows_app,
                    "application_directory",
                    return_value=executable_directory,
                ):
                    self.assertTrue(windows_app.is_portable_mode())
                    self.assertEqual(
                        windows_app.storage_directory(),
                        executable_directory,
                    )

    def test_missing_portable_marker_does_not_enable_portable_mode(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            executable_directory = Path(directory)

            with patch.object(windows_app.sys, "frozen", True, create=True):
                with patch.object(
                    windows_app,
                    "application_directory",
                    return_value=executable_directory,
                ):
                    self.assertFalse(windows_app.is_portable_mode())


if __name__ == "__main__":
    unittest.main()