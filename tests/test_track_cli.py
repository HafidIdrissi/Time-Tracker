from __future__ import annotations

import unittest
from pathlib import Path
from unittest import mock

import track


class TrackCliTests(unittest.TestCase):
    def test_defaults_and_custom_values_reach_the_tracker(self) -> None:
        cases = [
            (["track.py"], Path("data/activity.db"), 5.0, 180.0),
            (
                ["track.py", "--interval", "2", "--idle-after", "30", "--database", "demo/activity.db"],
                Path("demo/activity.db"),
                2.0,
                30.0,
            ),
            (
                ["track.py", "--interval", "0.5", "--idle-after", "0.25"],
                Path("data/activity.db"),
                0.5,
                0.25,
            ),
        ]
        for argv, database_path, interval, idle_after in cases:
            with self.subTest(argv=argv):
                database = mock.MagicMock()
                with (
                    mock.patch("sys.argv", argv),
                    mock.patch("track.WindowsActivityProvider") as provider,
                    mock.patch("track.ActivityDatabase", return_value=database) as database_cls,
                    mock.patch("track.ActivityTracker") as tracker_cls,
                ):
                    self.assertEqual(track.main(), 0)
                provider.assert_called_once_with()
                database_cls.assert_called_once_with(database_path)
                self.assertEqual(tracker_cls.call_args.kwargs["poll_interval"], interval)
                self.assertEqual(tracker_cls.call_args.kwargs["idle_threshold"], idle_after)
                self.assertIs(tracker_cls.call_args.kwargs["database"], database.__enter__.return_value)
                tracker_cls.return_value.run.assert_called_once_with()
                database.__exit__.assert_called_once()

    def test_provider_runtime_error_exits_before_opening_a_database(self) -> None:
        with (
            mock.patch("sys.argv", ["track.py", "--database", "unused/activity.db"]),
            mock.patch("track.WindowsActivityProvider", side_effect=RuntimeError("Windows only")),
            mock.patch("track.ActivityDatabase") as database_cls,
        ):
            self.assertEqual(track.main(), 1)
        database_cls.assert_not_called()

    def test_invalid_settings_exit_before_constructing_dependencies(self) -> None:
        for option in ("--interval", "--idle-after"):
            for value in ("nan", "inf", "-inf", "0", "-1"):
                with self.subTest(option=option, value=value):
                    with (
                        mock.patch("sys.argv", ["track.py", f"{option}={value}"]),
                        mock.patch("track.WindowsActivityProvider") as provider,
                        mock.patch("track.ActivityDatabase") as database_cls,
                        mock.patch("track.ActivityTracker") as tracker_cls,
                        self.assertLogs(level="ERROR") as logs,
                    ):
                        self.assertEqual(track.main(), 1)

                    provider.assert_not_called()
                    database_cls.assert_not_called()
                    tracker_cls.assert_not_called()
                    self.assertIn(
                        f"{option} must be finite and greater than zero",
                        "\n".join(logs.output),
                    )

    def test_keyboard_interrupt_stops_the_tracker_and_closes_the_database(self) -> None:
        database = mock.MagicMock()
        tracker = mock.Mock()
        tracker.run.side_effect = KeyboardInterrupt
        with (
            mock.patch("sys.argv", ["track.py"]),
            mock.patch("track.WindowsActivityProvider"),
            mock.patch("track.ActivityDatabase", return_value=database),
            mock.patch("track.ActivityTracker", return_value=tracker),
        ):
            self.assertEqual(track.main(), 0)
        tracker.stop.assert_called_once_with()
        database.__exit__.assert_called_once()


if __name__ == "__main__":
    unittest.main()
