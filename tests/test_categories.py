from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from timetracker.categories import CategoryConfigError, load_categorizer


class CategorizerTests(unittest.TestCase):
    def test_invalid_configs_still_raise_useful_errors(self) -> None:
        cases = [
            ('{"categories":', "Invalid JSON"),
            ("[]", "The configuration root must be a JSON object"),
            ('{"categories": "wrong"}', "'categories' must be a list"),
        ]

        with tempfile.TemporaryDirectory() as directory:
            for encoding in ("utf-8", "utf-8-sig"):
                for content, message in cases:
                    with self.subTest(encoding=encoding, content=content):
                        path = Path(directory) / "config.json"
                        path.write_text(content, encoding=encoding)

                        with self.assertRaises(CategoryConfigError) as caught:
                            load_categorizer(path)

                        self.assertIn(message, str(caught.exception))

    def test_utf8_encodings_preserve_non_ascii_content(self) -> None:
        payload = {
            "default_category": "其他",
            "categories": [
                {
                    "name": "学习",
                    "color": "#111111",
                    "keywords": ["论文", "编程"],
                }
            ],
        }
        results = []

        with tempfile.TemporaryDirectory() as directory:
            for encoding in ("utf-8", "utf-8-sig"):
                with self.subTest(encoding=encoding):
                    path = Path(directory) / f"{encoding}.json"
                    path.write_text(
                        json.dumps(payload, ensure_ascii=False),
                        encoding=encoding,
                    )
                    categorizer = load_categorizer(path)

                    self.assertEqual(categorizer.default_name, "其他")
                    self.assertEqual(categorizer.categories[0].name, "学习")
                    self.assertEqual(
                        categorizer.categories[0].keywords,
                        ("论文", "编程"),
                    )
                    self.assertEqual(
                        categorizer.categorize("editor", "阅读论文"),
                        ("学习", "#111111"),
                    )
                    results.append(categorizer)

        self.assertEqual(results[0].categories, results[1].categories)
        self.assertEqual(results[0].default_name, results[1].default_name)
        self.assertEqual(results[0].default_color, results[1].default_color)

    def test_utf8_bom_configuration_loads(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text('{"categories": []}', encoding="utf-8-sig")
            categorizer = load_categorizer(path)

        self.assertEqual(categorizer.categories, [])
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

    def test_unicode_casefold_keeps_the_first_matching_rule(self) -> None:
        payload = {
            "default_category": "Other",
            "default_color": "#64748b",
            "categories": [
                {"name": "Routes", "color": "#123456", "keywords": ["STRASSE"]},
                {"name": "Streets", "color": "#abcdef", "keywords": ["straße"]},
                {"name": "Notes", "color": "#0f172a", "keywords": ["ΣΗΜΕΙΩΣΕΙΣ"]},
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            categorizer = load_categorizer(path)

        self.assertEqual(categorizer.categorize("maps.exe", "Haupt Straße"), ("Routes", "#123456"))
        self.assertEqual(categorizer.categorize("σημειωσεις.exe", "Untitled"), ("Notes", "#0f172a"))
        self.assertEqual(categorizer.categorize("maps.exe", "Avenue"), ("Other", "#64748b"))
        self.assertEqual(
            categorizer.categorize("maps.exe", "Haupt Straße", is_idle=True),
            ("Idle", "#94a3b8"),
        )


    # ── Issue #200 ────────────────────────────────────────────────────────────

    def test_default_category_must_be_non_empty_string(self) -> None:
        """Blank or non-string default_category raises CategoryConfigError
        mentioning 'default_category'."""
        cases = [
            ("blank string", '{"default_category": "  ", "categories": []}'),
            ("int",          '{"default_category": 123,  "categories": []}'),
            ("None",         '{"default_category": null, "categories": []}'),
            ("empty string", '{"default_category": "",   "categories": []}'),
        ]
        with tempfile.TemporaryDirectory() as directory:
            for label, content in cases:
                with self.subTest(label=label):
                    path = Path(directory) / "config.json"
                    path.write_text(content, encoding="utf-8")
                    with self.assertRaises(CategoryConfigError) as raised:
                        load_categorizer(path)
                    self.assertIn("default_category", str(raised.exception))

    def test_default_color_must_be_hex_rrggbb(self) -> None:
        """A malformed or non-string default_color raises CategoryConfigError
        mentioning 'default_color'."""
        cases = [
            ("word color",   '{"default_color": "blue",   "categories": []}'),
            ("bad hex",      '{"default_color": "#xyz",   "categories": []}'),
            ("int",          '{"default_color": 123456,   "categories": []}'),
            ("None",         '{"default_color": null,     "categories": []}'),
        ]
        with tempfile.TemporaryDirectory() as directory:
            for label, content in cases:
                with self.subTest(label=label):
                    path = Path(directory) / "config.json"
                    path.write_text(content, encoding="utf-8")
                    with self.assertRaises(CategoryConfigError) as raised:
                        load_categorizer(path)
                    self.assertIn("default_color", str(raised.exception))

    def test_non_object_category_entries_report_literal_index(self) -> None:
        """Non-dict entries inside the categories list raise CategoryConfigError
        mentioning the exact literal index (e.g. 'categories[1]')."""
        valid0 = {"name": "Work",  "color": "#aabbcc", "keywords": ["code"]}
        valid1 = {"name": "Play",  "color": "#112233", "keywords": ["game"]}
        cases = [
            ("int at 0",      [42],                       0),
            ("string at 0",   ["string"],                 0),
            ("None at 0",     [None],                     0),
            ("list at 1",     [valid0, []],               1),
            ("int at 1",      [valid0, 42],               1),
            ("None at 2",     [valid0, valid1, None],     2),
        ]
        with tempfile.TemporaryDirectory() as directory:
            for label, cat_list, expected_index in cases:
                with self.subTest(label=label):
                    payload = json.dumps({"categories": cat_list})
                    path = Path(directory) / "config.json"
                    path.write_text(payload, encoding="utf-8")
                    with self.assertRaises(CategoryConfigError) as raised:
                        load_categorizer(path)
                    self.assertIn(
                        f"categories[{expected_index}]",
                        str(raised.exception),
                    )

    def test_omitted_defaults_use_documented_values(self) -> None:
        """When default_category and default_color are absent, the loader
        falls back to 'Other' and '#64748b' with an empty category list."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text('{"categories": []}', encoding="utf-8")
            categorizer = load_categorizer(path)
        self.assertEqual(categorizer.default_name, "Other")
        self.assertEqual(categorizer.default_color, "#64748b")
        self.assertEqual(categorizer.categories, [])

    def test_loading_does_not_mutate_file_bytes(self) -> None:
        """load_categorizer must not alter file content — verified by comparing
        read_bytes() before and after the call, for both valid and rejected
        inputs and for both utf-8 and utf-8-sig encodings."""
        valid_payload   = {"categories": [{"name": "Work", "color": "#aabbcc",
                                            "keywords": ["code"]}]}
        invalid_payload = {"default_category": 123, "categories": []}

        with tempfile.TemporaryDirectory() as directory:
            for encoding in ("utf-8", "utf-8-sig"):
                # Sub-case A: valid input — loader succeeds, bytes unchanged.
                with self.subTest(case="valid", encoding=encoding):
                    path = Path(directory) / f"valid_{encoding}.json"
                    path.write_text(
                        json.dumps(valid_payload), encoding=encoding
                    )
                    before = path.read_bytes()
                    load_categorizer(path)
                    self.assertEqual(before, path.read_bytes())

                # Sub-case B: invalid input — loader raises, bytes unchanged.
                with self.subTest(case="invalid", encoding=encoding):
                    path = Path(directory) / f"invalid_{encoding}.json"
                    path.write_text(
                        json.dumps(invalid_payload), encoding=encoding
                    )
                    before = path.read_bytes()
                    with self.assertRaises(CategoryConfigError):
                        load_categorizer(path)
                    self.assertEqual(before, path.read_bytes())


if __name__ == "__main__":
    unittest.main()
