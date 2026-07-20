from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from timetracker.categories import CategoryConfigError, load_categorizer


class CategorizerTests(unittest.TestCase):
    def test_first_case_insensitive_keyword_wins(self) -> None:
        payload = {
            "default_category": "Other",
            "categories": [
                {"name": "Work", "color": "#111111", "keywords": ["GitHub"]},
                {"name": "Leisure", "color": "#222222", "keywords": ["Firefox"]},
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            categorizer = load_categorizer(path)

        self.assertEqual(
            categorizer.categorize("firefox.exe", "Pull request · github.com"),
            ("Work", "#111111"),
        )
        self.assertEqual(
            categorizer.categorize("unknown.exe", "No match"),
            ("Other", "#64748b"),
        )
        self.assertEqual(
            categorizer.categorize("code.exe", "Project", is_idle=True),
            ("Idle", "#94a3b8"),
        )

    def test_invalid_category_list_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text('{"categories": "non"}', encoding="utf-8")
            with self.assertRaises(CategoryConfigError):
                load_categorizer(path)


if __name__ == "__main__":
    unittest.main()
