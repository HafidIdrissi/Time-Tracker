from __future__ import annotations

import io
import unittest
from unittest import mock

import preview_category
from timetracker import __version__


class PreviewCategoryVersionTests(unittest.TestCase):
    def test_version_prints_program_name_and_exits_before_config(self) -> None:
        stdout = io.StringIO()
        with (
            mock.patch("sys.argv", ["preview_category.py", "--version"]),
            mock.patch("sys.stdout", stdout),
            mock.patch("preview_category.load_categorizer") as load_categorizer,
        ):
            with self.assertRaises(SystemExit) as raised:
                preview_category.main()
        self.assertEqual(raised.exception.code, 0)
        self.assertEqual(stdout.getvalue(), f"preview_category.py {__version__}\n")
        self.assertNotEqual(__version__, "")
        load_categorizer.assert_not_called()


if __name__ == "__main__":
    unittest.main()