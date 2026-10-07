"""Cleanup guarantees for the Windows demo recorder.

Every test uses fake/mocked processes and fixture stubs so FFmpeg,
a Windows desktop, and a real Tk root are never required.

Tests exercise the production ``cleanup_recorder`` helper and ``record()``
entry point directly, verifying that ``fixture.doCleanups()`` runs exactly
once in every execution path, timeouts remain strictly bounded, primary
recording errors are preserved as the top-level exception, and secondary
cleanup errors are reported to stderr or propagated when no primary error exists.
"""
from __future__ import annotations

import importlib.util
import io
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock


def _load_recorder_module():
    """Load scripts/record_windows_demo.py without modifying global sys.path."""
    path = Path(__file__).resolve().parents[1] / "scripts" / "record_windows_demo.py"
    spec = importlib.util.spec_from_file_location("record_windows_demo", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RECORDER = _load_recorder_module()
cleanup_recorder = RECORDER.cleanup_recorder


class FakeProcess:
    """Simulates subprocess.Popen with configurable termination and wait behaviour."""

    def __init__(
        self,
        *,
        already_exited: bool = False,
        terminate_works: bool = True,
        terminate_raises: BaseException | None = None,
        kill_works: bool = True,
        kill_raises: BaseException | None = None,
        final_wait_times_out: bool = False,
    ) -> None:
        self._exited = already_exited
        self._terminate_works = terminate_works
        self._terminate_raises = terminate_raises
        self._kill_works = kill_works
        self._kill_raises = kill_raises
        self._final_wait_times_out = final_wait_times_out
        self.terminate_called = False
        self.kill_called = False
        self.wait_calls: list[float | None] = []
        self.returncode: int | None = 0 if already_exited else None

    def poll(self) -> int | None:
        if self._exited:
            return self.returncode
        return None

    def terminate(self) -> None:
        self.terminate_called = True
        if self._terminate_raises is not None:
            raise self._terminate_raises
        if self._terminate_works:
            self._exited = True
            self.returncode = 1

    def kill(self) -> None:
        self.kill_called = True
        if self._kill_raises is not None:
            raise self._kill_raises
        if self._kill_works:
            self._exited = True
            self.returncode = -9

    def wait(self, timeout: float | None = None) -> int:
        self.wait_calls.append(timeout)
        if self.kill_called and self._final_wait_times_out:
            raise subprocess.TimeoutExpired(cmd="fake_ffmpeg", timeout=timeout or 0)
        if not self._exited:
            raise subprocess.TimeoutExpired(cmd="fake_ffmpeg", timeout=timeout or 0)
        assert self.returncode is not None
        return self.returncode


class FakeFixture:
    """Minimal stand-in for the NativeDesktopTests instance used by the recorder."""

    def __init__(self, *, setup_succeeds: bool = True) -> None:
        self.cleanup_call_count = 0
        self._setup_succeeds = setup_succeeds

    def setUp(self) -> None:
        if not self._setup_succeeds:
            raise RuntimeError("Simulated setUp failure")

    def doCleanups(self) -> None:
        self.cleanup_call_count += 1


class TestRecordingCleanup(unittest.TestCase):
    """Verify production cleanup_recorder and record guarantees."""

    def test_cleanup_when_process_already_exited(self) -> None:
        """A process that finished before cleanup should not be terminated or killed."""
        process = FakeProcess(already_exited=True)
        fixture = FakeFixture()

        cleanup_recorder(process, fixture)

        self.assertEqual(fixture.cleanup_call_count, 1)
        self.assertFalse(process.terminate_called)
        self.assertFalse(process.kill_called)
        self.assertEqual(process.wait_calls, [])

    def test_cleanup_when_no_process_started(self) -> None:
        """When process is None (e.g. FFmpeg was never launched), cleanup runs safely."""
        fixture = FakeFixture()

        cleanup_recorder(None, fixture)

        self.assertEqual(fixture.cleanup_call_count, 1)

    def test_cleanup_when_terminate_succeeds(self) -> None:
        """A responsive process terminates within timeout; cleanup runs and wait is bounded."""
        process = FakeProcess(terminate_works=True)
        fixture = FakeFixture()

        cleanup_recorder(process, fixture)

        self.assertEqual(fixture.cleanup_call_count, 1)
        self.assertTrue(process.terminate_called)
        self.assertFalse(process.kill_called)
        self.assertEqual(process.wait_calls, [10])

    def test_cleanup_when_terminate_times_out_then_kill_succeeds(self) -> None:
        """An unresponsive process that ignores terminate is killed with bounded waits."""
        process = FakeProcess(terminate_works=False, kill_works=True)
        fixture = FakeFixture()
        stderr = io.StringIO()

        with mock.patch("sys.stderr", stderr):
            cleanup_recorder(process, fixture)

        self.assertEqual(fixture.cleanup_call_count, 1)
        self.assertTrue(process.terminate_called)
        self.assertTrue(process.kill_called)
        self.assertEqual(process.wait_calls, [10, 5])
        self.assertIn("killing", stderr.getvalue())

    def test_cleanup_after_setup_failure(self) -> None:
        """When setUp fails, cleanup runs unconditionally and setup error is preserved."""
        fixture = FakeFixture(setup_succeeds=False)
        with self.assertRaises(RuntimeError) as ctx:
            try:
                fixture.setUp()
            except BaseException as exc:
                cleanup_recorder(None, fixture, primary_error=exc)
                raise

        self.assertEqual(str(ctx.exception), "Simulated setUp failure")
        self.assertEqual(fixture.cleanup_call_count, 1)

    def test_cleanup_when_terminate_raises_without_primary_error(self) -> None:
        """When terminate() raises unexpectedly and no recording error occurred, propagate it."""
        process = FakeProcess(terminate_raises=OSError("terminate access denied"))
        fixture = FakeFixture()

        with self.assertRaises(OSError) as ctx:
            cleanup_recorder(process, fixture, primary_error=None)

        self.assertEqual(str(ctx.exception), "terminate access denied")
        self.assertEqual(fixture.cleanup_call_count, 1)

    def test_cleanup_when_kill_raises_without_primary_error(self) -> None:
        """When kill() raises unexpectedly and no recording error occurred, propagate it."""
        process = FakeProcess(terminate_works=False, kill_raises=OSError("kill failed"))
        fixture = FakeFixture()
        stderr = io.StringIO()

        with mock.patch("sys.stderr", stderr):
            with self.assertRaises(OSError) as ctx:
                cleanup_recorder(process, fixture, primary_error=None)

        self.assertEqual(str(ctx.exception), "kill failed")
        self.assertEqual(fixture.cleanup_call_count, 1)

    def test_cleanup_when_final_wait_times_out_without_primary_error(self) -> None:
        """When wait(timeout=5) after kill times out and no recording error occurred, propagate it."""
        process = FakeProcess(terminate_works=False, final_wait_times_out=True)
        fixture = FakeFixture()
        stderr = io.StringIO()

        with mock.patch("sys.stderr", stderr):
            with self.assertRaises(subprocess.TimeoutExpired):
                cleanup_recorder(process, fixture, primary_error=None)

        self.assertEqual(fixture.cleanup_call_count, 1)
        self.assertEqual(process.wait_calls, [10, 5])

    def test_primary_recording_error_preserved_when_kill_fails(self) -> None:
        """Regression test: preserve primary recording error when process stop/kill fails."""
        primary_error = RuntimeError("Recording exceeded 70-second guard.")
        process = FakeProcess(terminate_works=False, kill_raises=OSError("kill failed"))
        fixture = FakeFixture()
        stderr = io.StringIO()

        with mock.patch("sys.stderr", stderr):
            cleanup_recorder(process, fixture, primary_error=primary_error)

        self.assertEqual(fixture.cleanup_call_count, 1)
        self.assertIn("Secondary cleanup failure after recording error", stderr.getvalue())
        self.assertIn("kill failed", stderr.getvalue())

    def test_primary_recording_error_preserved_when_terminate_raises(self) -> None:
        """Preserve primary recording error when terminate raises unexpectedly."""
        primary_error = RuntimeError("Tk errors in callbacks")
        process = FakeProcess(terminate_raises=OSError("terminate error"))
        fixture = FakeFixture()
        stderr = io.StringIO()

        with mock.patch("sys.stderr", stderr):
            cleanup_recorder(process, fixture, primary_error=primary_error)

        self.assertEqual(fixture.cleanup_call_count, 1)
        self.assertIn("Secondary cleanup failure after recording error", stderr.getvalue())
        self.assertIn("terminate error", stderr.getvalue())

    def test_record_entrypoint_drives_cleanup_and_preserves_primary_error(self) -> None:
        """Drive record() with mocked dependencies to verify end-to-end cleanup integration."""
        fixture = FakeFixture()
        mock_output = mock.MagicMock(spec=Path)

        with (
            mock.patch.object(RECORDER.shutil, "which", return_value="fake_ffmpeg"),
            mock.patch.object(RECORDER, "NativeDesktopTests", return_value=fixture),
            mock.patch.object(fixture, "setUp", side_effect=RuntimeError("Primary setUp error")),
        ):
            with self.assertRaises(RuntimeError) as ctx:
                RECORDER.record(mock_output)

        self.assertEqual(str(ctx.exception), "Primary setUp error")
        self.assertEqual(fixture.cleanup_call_count, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
