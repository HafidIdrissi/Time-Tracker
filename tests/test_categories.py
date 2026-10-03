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

    def test_configuration_rules_report_the_invalid_case(self) -> None:
        cases = {
            "invalid json": ("{", "Invalid JSON"),
            "root is not an object": ("[]", "must be a JSON object"),
            "missing categories": ("{}", "'categories' must be a list"),
            "empty name": (
                '{"categories": [{"name": "  ", "keywords": ["code"]}]}',
                "must be a non-empty string",
            ),
            "invalid color": (
                '{"categories": [{"name": "Work", "color": "blue", "keywords": ["code"]}]}',
                "#RRGGBB",
            ),
            "empty keywords": (
                '{"categories": [{"name": "Work", "keywords": []}]}',
                "non-empty list",
            ),
            "non-string keyword": (
                '{"categories": [{"name": "Work", "keywords": [1]}]}',
                "must be a non-empty string",
            ),
            "blank keyword": (
                '{"categories": [{"name": "Work", "keywords": ["  "]}]}',
                "must be a non-empty string",
            ),
            "duplicate name": (
                '{"categories": ['
                '{"name": "Work", "keywords": ["code"]},'
                '{"name": "work", "keywords": ["mail"]}'
                "]}",
                "Duplicate category",
            ),
        }
        for label, (payload, expected) in cases.items():
            with self.subTest(label):
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "config.json"
                    path.write_text(payload, encoding="utf-8")
                    with self.assertRaises(CategoryConfigError) as raised:
                        load_categorizer(path)
                self.assertIn(expected, str(raised.exception))

    def test_names_and_keywords_are_trimmed(self) -> None:
        payload = {
            "default_category": " Other ",
            "categories": [
                {"name": " Work ", "color": "#111111", "keywords": [" code.exe ", "Mail"]}
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            categorizer = load_categorizer(path)
        self.assertEqual(categorizer.default_name, "Other")
        self.assertEqual(categorizer.categories[0].name, "Work")
        self.assertEqual(categorizer.categories[0].keywords, ("code.exe", "Mail"))


if __name__ == "__main__":
    unittest.main()
