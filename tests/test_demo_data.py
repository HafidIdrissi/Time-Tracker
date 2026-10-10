from __future__ import annotations

import importlib.util
import io
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from timetracker.categories import load_categorizer
from timetracker.database import ActivityDatabase


def load_generator():
    path = Path(__file__).resolve().parents[1] / "scripts" / "generate_demo_data.py"
    spec = importlib.util.spec_from_file_location("generate_demo_data", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def stored_rows(path: Path) -> list[tuple[str, str, float, bool]]:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    end = datetime(2027, 1, 1, tzinfo=timezone.utc)
    with ActivityDatabase(path) as database:
        periods = database.periods_between(start, end)
    return [
        (period.application, period.window_title, period.duration_seconds, period.is_idle)
        for period in periods
    ]


class DemoDataTests(unittest.TestCase):
    def test_repeated_generation_matches_and_refuses_overwrite(self) -> None:
        generator = load_generator()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = generator.generate_demo_database(root / "one")
            second = generator.generate_demo_database(root / "two")
            rows = stored_rows(first)
            self.assertEqual(stored_rows(second), rows)
            self.assertGreaterEqual(len(rows), 4)
            self.assertTrue(any(is_idle for *_rest, is_idle in rows))
            self.assertTrue(any(application == "chrome.exe" for application, *_rest in rows))

            start = datetime(2026, 1, 1, tzinfo=timezone.utc)
            with ActivityDatabase(first) as database:
                periods = database.periods_between(start, start + timedelta(days=400))
            self.assertTrue(any(period.started_at.date() != period.ended_at.date() for period in periods))
            categorizer = load_categorizer(Path(__file__).resolve().parents[1] / "config.example.json")
            categories = {
                categorizer.categorize(period.application, period.window_title, period.is_idle)[0]
                for period in periods
            }
            self.assertGreaterEqual(categories, {"Work", "Games", "Entertainment", "Idle"})
            with self.assertRaises(FileExistsError):
                generator.generate_demo_database(root / "one")

    def test_documented_command_imports_the_project(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        script = repository / "scripts" / "generate_demo_data.py"
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "demo"
            environment = os.environ.copy()
            environment.pop("PYTHONPATH", None)
            completed = subprocess.run(
                [sys.executable, str(script), "--output", str(output)],
                cwd=repository,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue((output / "activity.db").is_file())

    def test_output_path_beneath_file_exits_nonzero_without_traceback(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        script = repository / "scripts" / "generate_demo_data.py"
        with tempfile.TemporaryDirectory() as directory:
            dummy_file = Path(directory) / "existing_file"
            dummy_file.write_text("not a directory", encoding="utf-8")
            output = dummy_file / "nested_dir"
            completed = subprocess.run(
                [sys.executable, str(script), "--output", str(output)],
                cwd=repository,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 1)
            self.assertIn("Error:", completed.stderr)
            self.assertNotIn("Traceback", completed.stderr)
            self.assertEqual(dummy_file.read_text(encoding="utf-8"), "not a directory")

    def test_sqlite_failure_exits_nonzero_without_traceback(self) -> None:
        generator = load_generator()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "demo"
            existing_file = Path(directory) / "existing.txt"
            existing_file.write_text("keep this intact", encoding="utf-8")
            stderr = io.StringIO()
            with (
                mock.patch("timetracker.database.ActivityDatabase._create_schema", side_effect=sqlite3.OperationalError("disk I/O error")),
                mock.patch("sys.stderr", stderr),
            ):
                code = generator.main(["--output", str(output)])

            self.assertEqual(code, 1)
            message = stderr.getvalue()
            self.assertIn("Error:", message)
            self.assertIn("disk I/O error", message)
            self.assertNotIn("Traceback", message)
            self.assertEqual(existing_file.read_text(encoding="utf-8"), "keep this intact")

    def test_existing_wal_sidecar_is_left_untouched(self) -> None:
        generator = load_generator()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "demo"
            output.mkdir()
            wal = output / "activity.db-wal"
            wal.write_bytes(b"sentinel-wal")
            other = output / "notes.txt"
            other.write_bytes(b"leave me")

            with mock.patch.object(
                generator, "ActivityDatabase", side_effect=AssertionError("constructed")
            ) as database_type:
                with self.assertRaises(FileExistsError):
                    generator.generate_demo_database(output)
            database_type.assert_not_called()
            self.assertEqual(wal.read_bytes(), b"sentinel-wal")
            self.assertEqual(other.read_bytes(), b"leave me")
            self.assertEqual(sorted(path.name for path in output.iterdir()), ["activity.db-wal", "notes.txt"])

            clean = generator.generate_demo_database(root / "clean")
            self.assertTrue(clean.is_file())
            self.assertGreaterEqual(len(stored_rows(clean)), 4)

    def test_version_exits_without_output_or_database_access(self) -> None:
        generator = load_generator()
        repository = Path(__file__).resolve().parents[1]
        script = repository / "scripts" / "generate_demo_data.py"

        with tempfile.TemporaryDirectory() as directory:
            working_directory = Path(directory)
            environment = os.environ.copy()
            environment.pop("PYTHONPATH", None)

            completed = subprocess.run(
                [sys.executable, str(script), "--version"],
                cwd=working_directory,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(
                completed.stdout,
                f"{script.name} {generator.__version__}\n",
            )
            self.assertEqual(completed.stderr, "")
            self.assertEqual(list(working_directory.iterdir()), [])

            stdout = io.StringIO()
            with (
                mock.patch.object(
                    generator, "ActivityDatabase"
                ) as database_type,
                mock.patch("sys.stdout", stdout),
                mock.patch("sys.argv", [str(script), "--version"]),
            ):
                with self.assertRaises(SystemExit) as raised:
                    generator.build_parser().parse_args(["--version"])

            self.assertEqual(raised.exception.code, 0)
            self.assertEqual(
                stdout.getvalue(),
                f"{script.name} {generator.__version__}\n",
            )
            database_type.assert_not_called()
            self.assertEqual(list(working_directory.iterdir()), [])


if __name__ == "__main__":
    unittest.main()