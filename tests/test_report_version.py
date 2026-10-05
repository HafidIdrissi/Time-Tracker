from __future__ import annotations

import io
import unittest
from unittest import mock

import report
from timetracker import __version__


class ReportVersionTests(unittest.TestCase):
    def test_version_prints_program_name_and_exits_before_report(self) -> None:
        stdout = io.StringIO()
        with (
            mock.patch("sys.argv", ["report.py", "--version"]),
            mock.patch("sys.stdout", stdout),
            mock.patch("report.load_categorizer") as load_categorizer,
            mock.patch("report.generate_report") as generate_report,
        ):
            with self.assertRaises(SystemExit) as raised:
                report.main()
        self.assertEqual(raised.exception.code, 0)
        self.assertEqual(stdout.getvalue(), f"report.py {__version__}\n")
        self.assertNotEqual(__version__, "")
        load_categorizer.assert_not_called()
        generate_report.assert_not_called()


if __name__ == "__main__":
    unittest.main()