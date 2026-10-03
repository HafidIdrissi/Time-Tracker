from __future__ import annotations

import io
import unittest
from unittest import mock

import track
from timetracker import __version__


class TrackVersionTests(unittest.TestCase):
    def test_version_prints_program_name_and_exits_before_tracking(self) -> None:
        stdout = io.StringIO()
        with (
            mock.patch("sys.argv", ["track.py", "--version"]),
            mock.patch("sys.stdout", stdout),
            mock.patch("track.WindowsActivityProvider") as provider,
            mock.patch("track.ActivityDatabase") as database,
        ):
            with self.assertRaises(SystemExit) as raised:
                track.main()
        self.assertEqual(raised.exception.code, 0)
        self.assertEqual(stdout.getvalue(), f"track.py {__version__}\n")
        self.assertNotEqual(__version__, "")
        provider.assert_not_called()
        database.assert_not_called()


if __name__ == "__main__":
    unittest.main()
