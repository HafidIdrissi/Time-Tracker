"""Test that existing recording output files prevent recording from starting
unless overwrite is enabled. Verify that only known recorder outputs block
recording, unrelated files are preserved, and checks occur before recording.
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


class TestRecordingOutputs(unittest.TestCase):
    def _assert_existing_files_fails_early(
        self,
        filename: str,
    ) -> None:
        """Assert that an existing recorder output aborts before fixture or process setup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "demo"
            output.mkdir()

            existing_file = output / filename
            existing_file.write_text("disposable test content")

            with (
                mock.patch.object(
                    RECORDER, "NativeDesktopTests"
                ) as mock_fixture,
                mock.patch.object(
                    RECORDER.subprocess, "Popen"
                ) as mock_popen,
            ):
                with self.assertRaisesRegex(
                    RuntimeError, "already exists"
                ):
                    RECORDER.record(output, overwrite=False)

                mock_fixture.assert_not_called()
                mock_popen.assert_not_called()
    
    def test_existing_mp4_fails_early(self) -> None:
        """Refuse to record when the demo MP4 already exists."""
        self._assert_existing_files_fails_early(
            "LocalTimeTracker-demo.mp4"
        )

    def test_existing_text_file_fails_early(self) -> None:
        """Refuse to record when the demo text file already exists."""
        self._assert_existing_files_fails_early(
            "LocalTimeTracker-demo.txt"
        )

    def test_existing_log_file_fails_early(self) -> None:
        """Refuse to record when the recording log already exists."""
        self._assert_existing_files_fails_early(
            "recording.log"
        )

    def test_unrelated_file_does_not_block_recording(self) -> None:
        """Allow recording when the output directory contains unrelated files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "demo"
            output.mkdir()
            unrelated = output / "notes.txt"
            unrelated.write_text("keep me")

            RECORDER._check_recording_outputs(
                output, overwrite=False
            )

            self.assertEqual(unrelated.read_text(), "keep me")

    def test_overwrite(self) -> None:
        """Allow existing recorder outputs when overwrite is enabled."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "demo"
            output.mkdir()

            existing_file = output / "LocalTimeTracker-demo.mp4"
            existing_file.write_text("disposable test content")

            # Should not raise exception when overwrite is enabled
            RECORDER._check_recording_outputs(
                output, overwrite=True
            )

    def test_no_existing_outputs(self) -> None:
        """Allow recording when no known output files exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "demo"
            output.mkdir()

            RECORDER._check_recording_outputs(
                output, overwrite=False
            )

if __name__ == "main":
    unittest.main()
