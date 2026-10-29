from __future__ import annotations

import argparse
import io
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from unittest import mock

import report
from timetracker.database import ActivityDatabase
from timetracker.models import ActivityState

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


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


class ReportCliHomePathTests(unittest.TestCase):
    def _run(self, arguments: list[str]) -> tuple[object, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            mock.patch("sys.argv", ["report.py", *arguments]),
            mock.patch("sys.stdout", stdout),
            mock.patch("sys.stderr", stderr),
        ):
            try:
                code: object = report.main()
            except SystemExit as exc:
                code = exc.code
        return code, stdout.getvalue(), stderr.getvalue()

    def test_expanded_paths_reach_configuration_reader_and_report_writer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = {
                "database": root / "activity.db",
                "config": root / "config.json",
                "output": root / "report.html",
            }

            def expand(path: Path) -> Path:
                if path.parts[0] == "~":
                    return root / path.relative_to("~")
                return path

            for option in paths:
                with self.subTest(option=option):
                    arguments = ["--date", "2026-07-20"]
                    for name, path in paths.items():
                        value = f"~/{path.name}" if name == option else str(path)
                        arguments.extend([f"--{name}", value])
                    with (
                        mock.patch.object(Path, "expanduser", autospec=True, side_effect=expand),
                        mock.patch("report.load_categorizer") as load,
                        mock.patch("report.generate_report", return_value=paths["output"]) as generate,
                    ):
                        code, stdout, stderr = self._run(arguments)

                    self.assertEqual(code, 0, stderr)
                    self.assertIn("Report generated:", stdout)
                    load.assert_called_once_with(paths["config"])
                    generate.assert_called_once_with(
                        database_path=paths["database"],
                        output_path=paths["output"],
                        start_day=date(2026, 7, 20),
                        end_day=date(2026, 7, 20),
                        categorizer=load.return_value,
                    )

    def test_ordinary_paths_and_environment_variable_text_stay_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            prefixes = ["relative folder", directory, "$HOME", "%USERPROFILE%"]
            for prefix in prefixes:
                with self.subTest(prefix=prefix):
                    database = Path(prefix) / "activity.db"
                    config = Path(prefix) / "config.json"
                    output = Path(prefix) / "report.html"
                    with (
                        mock.patch.object(Path, "expanduser", autospec=True, side_effect=lambda path: path),
                        mock.patch("report.load_categorizer") as load,
                        mock.patch("report.generate_report", return_value=output) as generate,
                    ):
                        code, _stdout, stderr = self._run([
                            "--database", str(database),
                            "--config", str(config),
                            "--output", str(output),
                        ])

                    self.assertEqual(code, 0, stderr)
                    load.assert_called_once_with(config)
                    self.assertEqual(generate.call_args.kwargs["database_path"], database)
                    self.assertEqual(generate.call_args.kwargs["output_path"], output)

    def test_default_paths_are_not_home_expanded(self) -> None:
        with (
            mock.patch.object(Path, "expanduser", side_effect=AssertionError("default path expanded")),
            mock.patch.object(Path, "exists", return_value=False),
            mock.patch("report.load_categorizer") as load,
            mock.patch("report.generate_report", return_value=Path("reports/report-2026-07-20.html")) as generate,
        ):
            code, _stdout, stderr = self._run(["--date", "2026-07-20"])

        self.assertEqual(code, 0, stderr)
        load.assert_called_once_with(Path("config.example.json"))
        self.assertEqual(generate.call_args.kwargs["database_path"], Path("data/activity.db"))
        self.assertEqual(generate.call_args.kwargs["output_path"], Path("reports/report-2026-07-20.html"))

    def test_invalid_date_arguments_do_not_read_or_write_home_paths(self) -> None:
        invalid_arguments = [
            ["--date", "not-a-date"],
            ["--to", "2026-07-20"],
            ["--date", "2026-07-20", "--from", "2026-07-01"],
            ["--from", "2026-07-20", "--to", "2026-07-01"],
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for arguments in invalid_arguments:
                with self.subTest(arguments=arguments):
                    with (
                        mock.patch.object(Path, "expanduser", autospec=True,
                                          side_effect=lambda path: root / path.relative_to("~")),
                        mock.patch("report.load_categorizer") as load,
                        mock.patch("report.generate_report") as generate,
                    ):
                        code, stdout, stderr = self._run([
                            "--database", "~/activity.db",
                            "--config", "~/config.json",
                            "--output", "~/report.html",
                            *arguments,
                        ])

                    self.assertEqual(code, 2)
                    self.assertIn("error:", stderr)
                    self.assertNotIn("Traceback", stderr)
                    self.assertEqual(stdout, "")
                    load.assert_not_called()
                    generate.assert_not_called()


class ReportCliFilesystemPathTests(unittest.TestCase):
    """End-to-end guard for paths with spaces and non-ASCII characters.

    Windows user folders routinely contain spaces and accented characters, so
    every path is passed as a separate argument entry and the CLI runs from an
    unrelated working directory that must stay untouched.
    """

    def test_cli_accepts_spaced_unicode_paths_from_a_separate_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture = root / "path with spaces & üñîçødê"
            fixture.mkdir()
            database = fixture / "activity dätäbase.db"
            config = fixture / "cönfig.json"
            config.write_text(
                '{"default_category": "Other", "categories": []}\n',
                encoding="utf-8",
            )
            output = root / "output påth" / "räpôrt.html"

            with ActivityDatabase(database) as opened:
                period = opened.create_period(
                    ActivityState("Code.exe", "Fictional résumé window"),
                    datetime(2026, 9, 16, 9, 0, tzinfo=timezone.utc),
                )
                opened.update_period(
                    period,
                    datetime(2026, 9, 16, 9, 0, tzinfo=timezone.utc),
                    datetime(2026, 9, 16, 9, 30, tzinfo=timezone.utc),
                )

            working_directory = root / "separate working directory"
            working_directory.mkdir()

            completed = subprocess.run(
                [
                    sys.executable,
                    str(REPOSITORY_ROOT / "report.py"),
                    "--database",
                    str(database),
                    "--config",
                    str(config),
                    "--from",
                    "2026-09-15",
                    "--to",
                    "2026-09-17",
                    "--output",
                    str(output),
                ],
                cwd=working_directory,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("Report generated:", completed.stdout)
            self.assertTrue(output.is_file(), f"missing report at {output}")
            html = output.read_text(encoding="utf-8")
            self.assertIn('<meta charset="utf-8">', html)
            self.assertIn("Activity Report", html)
            self.assertIn("Code.exe", html)
            self.assertEqual(
                [entry.name for entry in working_directory.iterdir()],
                [],
                "the CLI created unexpected files in the working directory",
            )


if __name__ == "__main__":
    unittest.main()
