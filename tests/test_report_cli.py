from __future__ import annotations

import argparse
import io
import sqlite3
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

import report


class ReportCliSqliteFailureTests(unittest.TestCase):
    def test_fake_database_error_exits_nonzero_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            database = root / "activity.db"
            database.write_bytes(b"")
            config = root / "config.json"
            config.write_text(
                '{"default_category": "Other", "categories": []}',
                encoding="utf-8",
            )
            output = root / "report.html"
            argv = [
                "report.py",
                "--database",
                str(database),
                "--config",
                str(config),
                "--output",
                str(output),
            ]
            stderr = io.StringIO()
            with (
                mock.patch("sys.argv", argv),
                mock.patch("report.generate_report", side_effect=sqlite3.DatabaseError("database is locked")),
                mock.patch("sys.stderr", stderr),
            ):
                with self.assertRaises(SystemExit) as raised:
                    report.main()

            self.assertEqual(raised.exception.code, 1)
            message = stderr.getvalue()
            self.assertIn("Error:", message)
            self.assertIn("database is locked", message)
            self.assertNotIn("Traceback", message)
            self.assertFalse(output.exists())
            self.assertEqual(database.read_bytes(), b"")

    def test_corrupt_database_exits_nonzero_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            database = root / "activity.db"
            database.write_bytes(b"this is not a sqlite database")
            original = database.read_bytes()
            config = root / "config.json"
            config.write_text(
                '{"default_category": "Other", "categories": []}',
                encoding="utf-8",
            )
            output = root / "report.html"
            argv = [
                "report.py",
                "--database",
                str(database),
                "--config",
                str(config),
                "--output",
                str(output),
            ]
            stderr = io.StringIO()
            stdout = io.StringIO()
            with (
                mock.patch("sys.argv", argv),
                mock.patch("sys.stderr", stderr),
                mock.patch("sys.stdout", stdout),
            ):
                with self.assertRaises(SystemExit) as raised:
                    report.main()

            self.assertEqual(raised.exception.code, 1)
            message = stderr.getvalue()
            self.assertIn("Error:", message)
            self.assertNotIn("Traceback", message)
            self.assertNotIn("Report generated:", stdout.getvalue())
            self.assertFalse(output.exists())
            self.assertEqual(database.read_bytes(), original)


class ReportCliValidationTests(unittest.TestCase):
    def test_parse_date_accepts_iso_and_rejects_other_text(self) -> None:
        self.assertEqual(report.parse_date("2026-07-20"), date(2026, 7, 20))
        with self.assertRaises(argparse.ArgumentTypeError):
            report.parse_date("20/07/2026")

    def _run(self, argv: list[str]) -> tuple[object, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            mock.patch("sys.argv", argv),
            mock.patch("sys.stdout", stdout),
            mock.patch("sys.stderr", stderr),
        ):
            try:
                code: object = report.main()
            except SystemExit as exc:
                code = exc.code
        return code, stdout.getvalue(), stderr.getvalue()

    def test_rejected_date_combinations(self) -> None:
        code, _stdout, stderr = self._run(["report.py", "--to", "2026-07-20"])
        self.assertEqual(code, 2)
        self.assertIn("--to", stderr)

        code, _stdout, stderr = self._run(
            ["report.py", "--date", "2026-07-20", "--from", "2026-07-01"]
        )
        self.assertEqual(code, 2)
        self.assertIn("not allowed", stderr)

        code, _stdout, stderr = self._run(
            ["report.py", "--from", "2026-07-20", "--to", "2026-07-01"]
        )
        self.assertEqual(code, 2)
        self.assertIn("--to", stderr)

    def test_default_and_explicit_output_names(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "config.json"
            config.write_text('{"categories": []}', encoding="utf-8")
            output = root / "chosen.html"
            with (
                mock.patch("report.date") as date_cls,
                mock.patch("report.generate_report", return_value=output) as generate,
            ):
                date_cls.today.return_value = date(2026, 7, 20)
                date_cls.fromisoformat.side_effect = date.fromisoformat
                code, stdout, _stderr = self._run(
                    ["report.py", "--config", str(config), "--database", str(root / "missing.db")]
                )
            self.assertEqual(code, 0)
            self.assertIn("Report generated:", stdout)
            self.assertEqual(
                generate.call_args.kwargs["output_path"],
                Path("reports/report-2026-07-20.html"),
            )

            with mock.patch("report.generate_report", return_value=output) as generate:
                code, _stdout, _stderr = self._run(
                    [
                        "report.py",
                        "--config",
                        str(config),
                        "--from",
                        "2026-07-14",
                        "--to",
                        "2026-07-20",
                        "--output",
                        str(output),
                    ]
                )
            self.assertEqual(code, 0)
            self.assertEqual(generate.call_args.kwargs["output_path"], output)
            self.assertEqual(generate.call_args.kwargs["start_day"], date(2026, 7, 14))
            self.assertEqual(generate.call_args.kwargs["end_day"], date(2026, 7, 20))

    def test_invalid_configuration_returns_a_concise_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config.json"
            config.write_text("{", encoding="utf-8")
            code, stdout, stderr = self._run(["report.py", "--config", str(config)])
        self.assertEqual(code, 1)
        self.assertIn("Error:", stderr)
        self.assertNotIn("Traceback", stderr)
        self.assertNotIn("Report generated:", stdout)


if __name__ == "__main__":
    unittest.main()
