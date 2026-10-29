"""Tests for FFmpeg and FFprobe preflight checks.

Verify that missing recording tools cause record() to fail before
creating the output directory, setting up the desktop fixture, or
launching a subprocess.
"""
from __future__ import annotations

import importlib.util

from pathlib import Path
import tempfile
import unittest
from unittest import mock


def _load_recorder_module():
    """Load scripts/record_windows_demo.py without modifying global sys.path."""
    path = (
        Path(__file__).resolve().parents[1] 
        / "scripts" 
        / "record_windows_demo.py"
    )
    spec = importlib.util.spec_from_file_location(
        "record_windows_demo", path
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RECORDER = _load_recorder_module()


class TestRecordingPreflight(unittest.TestCase):
    def _assert_missing_tool_fails_early(
        self, which_results: list[str | None], missing_tool: str
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "demo"

            with (
                mock.patch.object(
                    RECORDER.shutil, "which",
                    side_effect=which_results,
                ) as which_mock,
                mock.patch.object(
                    RECORDER, "NativeDesktopTests"
                ) as fixture_mock,
                mock.patch.object(
                    RECORDER.subprocess, "Popen"
                ) as popen_mock,
            ):
                with self.assertRaisesRegex(
                    RuntimeError, missing_tool
                ):
                    RECORDER.record(output)

                fixture_mock.assert_not_called()
                popen_mock.assert_not_called()
                self.assertFalse(output.exists())

                self.assertEqual(
                    which_mock.call_args_list,
                    [
                        mock.call("ffmpeg"),
                        mock.call("ffprobe"),
                    ],
                )

    def test_missing_ffmpeg_fails_before_recording(self) -> None:
        """Verify recording fails early when FFmpeg is missing."""
        self._assert_missing_tool_fails_early(
            [None, "fake_ffprobe"], "FFmpeg"
        )

    def test_missing_ffprobe_fails_before_recording(self) -> None:
        """Verify recording fails early when FFprobe is missing."""
        self._assert_missing_tool_fails_early(
            ["fake_ffmpeg", None], "FFprobe"
        )

    def test_both_tools_available(
            self) -> None:
        """
        Verify that _resolve_recording_tools() succeeds when both
        FFmpeg and FFprobe are available.
        """
        with mock.patch.object(
            RECORDER.shutil,
            "which",
            side_effect=["fake_ffmpeg", "fake_ffprobe"],
        ) as which_mock:
            ffmpeg, probe = RECORDER._resolve_recording_tools()

        self.assertEqual(ffmpeg, "fake_ffmpeg")
        self.assertEqual(probe, "fake_ffprobe")
        self.assertEqual(
            which_mock.call_args_list,
            [
                mock.call("ffmpeg"),
                mock.call("ffprobe"),
            ],
        )

if __name__ == "main":
    unittest.main()