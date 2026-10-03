from __future__ import annotations

import importlib.util
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile

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


if __name__ == "__main__":
    unittest.main()
