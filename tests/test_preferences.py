from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from timetracker.preferences import load_tracking_preferences, save_tracking_preferences


class PreferenceTests(unittest.TestCase):
    def test_defaults_round_trip_and_invalid_values(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "preferences.json"
            self.assertEqual(load_tracking_preferences(path), ("1", "3"))
            save_tracking_preferences(path, "5", "10")
            self.assertEqual(load_tracking_preferences(path), ("5", "10"))
            path.write_text("{", encoding="utf-8")
            self.assertEqual(load_tracking_preferences(path), ("1", "3"))
            path.write_text('{"sample_seconds": "9", "idle_minutes": "3"}', encoding="utf-8")
            self.assertEqual(load_tracking_preferences(path), ("1", "3"))
            path.write_text("[]", encoding="utf-8")
            self.assertEqual(load_tracking_preferences(path), ("1", "3"))
            with self.assertRaises(ValueError):
                save_tracking_preferences(path, "4", "3")
            self.assertEqual(load_tracking_preferences(path), ("1", "3"))


if __name__ == "__main__":
    unittest.main()
