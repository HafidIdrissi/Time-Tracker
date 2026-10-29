from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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

    def  test_unreadable_file_returns_defaults_without_modifying_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "preferences.json"
            path.write_text(
                '{"sample_seconds": "5", "idle_minutes": "10"}',
                encoding="utf-8",
            )
            original_bytes = path.read_bytes()

            with(
                patch.object(Path, "read_text", side_effect=PermissionError),
                patch.object(Path, "write_text") as write_text,
                patch.object(Path, "write_bytes") as write_bytes,
                patch("timetracker.preferences.os.replace") as replace,
      ):
                self.assertEqual(load_tracking_preferences(path), ("1", "3"))
                write_text.assert_not_called()
                write_bytes.assert_not_called()
                replace.assert_not_called()

            self.assertEqual(path.read_bytes(), original_bytes)
            self.assertEqual(load_tracking_preferences(path), ("5", "10"))


    def test_invalid_utf8_returns_defaults_without_modifying_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "preferences.json"
            invalid_bytes = b"\xff\xfe\xfa"
            path.write_bytes(invalid_bytes)

            with (
               patch.object(Path, "write_text") as write_text,
               patch.object(Path, "write_bytes") as write_bytes,
               patch("timetracker.preferences.os.replace") as replace,
            ):
               self.assertEqual(load_tracking_preferences(path), ("1", "3"))

            write_text.assert_not_called()
            write_bytes.assert_not_called()
            replace.assert_not_called()
            self.assertEqual(path.read_bytes(), invalid_bytes)

            path.write_text(
                '{"sample_seconds": "5", "idle_minutes": "10"}',
                encoding="utf-8",
            )
            self.assertEqual(load_tracking_preferences(path), ("5", "10"))


    def test_invalid_choices_are_rejected_before_filesystem_writes(self) -> None:
        invalid_pairs = (("4", "3"), ("5", "4"))

        for sample_seconds, idle_minutes in invalid_pairs:
            for existing_file in (True, False):
                with self.subTest(
                    sample_seconds=sample_seconds,
                    idle_minutes=idle_minutes,
                    existing_file=existing_file,
                ):
                    with tempfile.TemporaryDirectory() as directory:
                        root = Path(directory)
                        if existing_file:
                            path = root / "preferences.json"
                            original_bytes = (
                                b'{"sample_seconds": "5", "idle_minutes": "10"}\n'
                            )
                            path.write_bytes(original_bytes)
                        else:
                            path = root / "not-created" / "preferences.json"

                        with (
                            patch.object(Path, "mkdir") as mkdir,
                            patch.object(Path, "write_text") as write_text,
                            patch.object(Path, "write_bytes") as write_bytes,
                            patch("timetracker.preferences.os.replace") as replace,
                        ):
                            with self.assertRaises(ValueError):
                                save_tracking_preferences(
                                    path, sample_seconds, idle_minutes
                                )

                        mkdir.assert_not_called()
                        write_text.assert_not_called()
                        write_bytes.assert_not_called()
                        replace.assert_not_called()

                        if existing_file:
                            self.assertEqual(path.read_bytes(), original_bytes)
                            self.assertFalse(path.with_name(path.name + ".partial").exists())
                        else:
                            self.assertFalse(path.parent.exists())
                            self.assertFalse(path.with_name(path.name + ".partial").exists())


if __name__ == "__main__":
    unittest.main()

