from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.modules.setdefault("tkinter", mock.MagicMock())
sys.modules.setdefault("tkinter.ttk", sys.modules["tkinter"].ttk)
sys.modules.setdefault("tkinter.messagebox", sys.modules["tkinter"].messagebox)
sys.modules.setdefault("tkinter.filedialog", sys.modules["tkinter"].filedialog)

import windows_app


class ConfigurationPathTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory(prefix="time-tracker-config-")
        self.addCleanup(self.directory.cleanup)
        self.base = Path(self.directory.name)
        patch = mock.patch.object(windows_app, "APP_DIRECTORY", self.base)
        patch.start()
        self.addCleanup(patch.stop)
        self.app = windows_app.TimeTrackerApp.__new__(windows_app.TimeTrackerApp)

    def test_personal_config_is_selected_first(self) -> None:
        personal = self.base / "config.json"
        personal.write_text(
            json.dumps(
                {
                    "categories": [
                        {"name": "Work", "color": "#112233", "keywords": ["notes"]}
                    ]
                }
            ),
            encoding="utf-8",
        )
        example = self.base / "config.example.json"
        example.write_text('{"categories": []}', encoding="utf-8")
        before_personal = personal.read_bytes()
        before_example = example.read_bytes()

        selected = self.app._configuration_path()

        self.assertEqual(selected, personal)
        self.assertEqual(personal.read_bytes(), before_personal)
        self.assertEqual(example.read_bytes(), before_example)

    def test_local_example_is_selected_when_personal_is_absent(self) -> None:
        example = self.base / "config.example.json"
        example.write_text(
            json.dumps(
                {
                    "categories": [
                        {"name": "Leisure", "color": "#445566", "keywords": ["video"]}
                    ]
                }
            ),
            encoding="utf-8",
        )
        before = example.read_bytes()
        selected = self.app._configuration_path()
        self.assertEqual(selected, example)
        self.assertEqual(example.read_bytes(), before)

    def test_bundled_example_is_selected_when_no_local_file_exists(self) -> None:
        bundled = Path(self.directory.name) / "bundled" / "config.example.json"
        bundled.parent.mkdir()
        bundled.write_text('{"categories": [{"name": "Bundled", "color": "#010101", "keywords": ["x"]}]}', encoding="utf-8")
        with mock.patch.object(windows_app, "bundled_resource", return_value=bundled) as resolver:
            selected = self.app._configuration_path()
        resolver.assert_called_once_with("config.example.json")
        self.assertEqual(selected, bundled)
        self.assertFalse((self.base / "config.json").exists())
        self.assertFalse((self.base / "config.example.json").exists())

    def test_invalid_personal_config_is_still_selected(self) -> None:
        personal = self.base / "config.json"
        personal.write_text("{not-json", encoding="utf-8")
        example = self.base / "config.example.json"
        example.write_text(
            json.dumps(
                {
                    "categories": [
                        {"name": "Work", "color": "#112233", "keywords": ["notes"]}
                    ]
                }
            ),
            encoding="utf-8",
        )
        before_personal = personal.read_bytes()
        before_example = example.read_bytes()

        selected = self.app._configuration_path()

        self.assertEqual(selected, personal)
        self.assertEqual(personal.read_bytes(), before_personal)
        self.assertEqual(example.read_bytes(), before_example)


if __name__ == "__main__":
    unittest.main()
