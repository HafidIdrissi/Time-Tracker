from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import preview_category


class CategoryPreviewTests(unittest.TestCase):
    def _config(self, directory: Path) -> Path:
        path = directory / "config.json"
        path.write_text(
            json.dumps(
                {
                    "categories": [
                        {"name": "Work", "color": "#112233", "keywords": ["gmail"]},
                        {"name": "Leisure", "color": "#445566", "keywords": ["Video"]},
                    ]
                }
            ),
            encoding="utf-8",
        )
        return path

    def test_overlap_case_fallback_and_invalid_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = self._config(Path(directory))
            self.assertEqual(
                preview_category.main(
                    ["--config", str(config), "--application", "chrome.exe", "--title", "Fictional Gmail"]
                ),
                0,
            )
            with self.assertLogs(level="INFO") if False else self.subTest("work"):
                pass
            from io import StringIO
            from unittest import mock

            stdout = StringIO()
            with mock.patch("sys.stdout", stdout):
                code = preview_category.main(
                    ["--config", str(config), "--application", "chrome.exe", "--title", "Fictional Gmail"]
                )
            self.assertEqual(code, 0)
            self.assertEqual(stdout.getvalue(), "Work\n")

            stdout = StringIO()
            with mock.patch("sys.stdout", stdout):
                preview_category.main(
                    ["--config", str(config), "--application", "player.exe", "--title", "fictional video"]
                )
            self.assertEqual(stdout.getvalue(), "Leisure\n")

            stdout = StringIO()
            with mock.patch("sys.stdout", stdout):
                preview_category.main(
                    ["--config", str(config), "--application", "notes.exe", "--title", "Nothing"]
                )
            self.assertEqual(stdout.getvalue(), "Other\n")

            stdout = StringIO()
            with mock.patch("sys.stdout", stdout):
                preview_category.main(
                    ["--config", str(config), "--application", "notes.exe", "--title", "gmail", "--idle"]
                )
            self.assertEqual(stdout.getvalue(), "Idle\n")

            config.write_text("{", encoding="utf-8")
            stderr = StringIO()
            with mock.patch("sys.stderr", stderr):
                code = preview_category.main(
                    ["--config", str(config), "--application", "notes.exe", "--title", "x"]
                )
            self.assertEqual(code, 1)
            self.assertIn("Error:", stderr.getvalue())


    def test_duplicate_keys_exit_nonzero_without_dump(self) -> None:
        from io import StringIO
        from unittest import mock

        payload = (
            '{"categories": [{"name": "Work", "color": "#111111", '
            '"color": "#222222", "keywords": ["fictional-note"]}]}'
        )
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config.json"
            config.write_text(payload, encoding="utf-8")
            before = config.read_bytes()
            stderr = StringIO()
            with mock.patch("sys.stderr", stderr):
                code = preview_category.main(
                    ["--config", str(config), "--application", "notes.exe", "--title", "x"]
                )
            self.assertEqual(code, 1)
            output = stderr.getvalue()
            self.assertIn("Error:", output)
            self.assertIn("Duplicate", output)
            self.assertNotIn("#222222", output)
            self.assertEqual(before, config.read_bytes())


if __name__ == "__main__":
    unittest.main()
