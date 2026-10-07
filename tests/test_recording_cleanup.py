"""Cleanup guarantees for the Windows demo recorder's finally block.

Every test uses a fake process and a lightweight fixture stub so FFmpeg,
a Windows desktop, and a real Tk root are never required. The tests
verify that ``fixture.doCleanups()`` runs in every exit path and that
the terminate-then-kill fallback handles an unresponsive child.
"""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


class FakeProcess:
    """Simulates subprocess.Popen with configurable termination behaviour."""

    def __init__(self, *, already_exited: bool = False, terminate_works: bool = True) -> None:
        self._exited = already_exited
        self._terminate_works = terminate_works
        self._killed = False
        self.terminate_called = False
        self.kill_called = False
        self.returncode: int | None = 0 if already_exited else None

    def poll(self) -> int | None:
        if self._exited:
            return self.returncode
        return None

    def terminate(self) -> None:
        self.terminate_called = True
        if self._terminate_works:
            self._exited = True
            self.returncode = 1

    def kill(self) -> None:
        self.kill_called = True
        self._killed = True
        self._exited = True
        self.returncode = -9

    def wait(self, timeout: float | None = None) -> int:
        if not self._exited and not self._killed:
            raise subprocess.TimeoutExpired(cmd="ffmpeg", timeout=timeout or 0)
        assert self.returncode is not None
        return self.returncode


class FakeFixture:
    """Minimal stand-in for the NativeDesktopTests instance used by the recorder."""

    def __init__(self, *, setup_succeeds: bool = True) -> None:
        self.cleaned_up = False
        self._setup_succeeds = setup_succeeds

    def setUp(self) -> None:
        if not self._setup_succeeds:
            raise RuntimeError("Simulated setUp failure")

    def doCleanups(self) -> None:
        self.cleaned_up = True


def _run_finally_block(process, fixture: FakeFixture) -> None:
    """Execute only the recorder's finally-block logic (extracted for testing)."""

    try:
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
    finally:
        fixture.doCleanups()


class TestRecordingCleanup(unittest.TestCase):
    """Verify doCleanups runs unconditionally in every finally-block path."""

    def test_cleanup_when_process_already_exited(self) -> None:
        """A process that finished before the finally block should not be
        terminated, and doCleanups must still run."""

        process = FakeProcess(already_exited=True)
        fixture = FakeFixture()
        _run_finally_block(process, fixture)

        self.assertTrue(fixture.cleaned_up)
        self.assertFalse(process.terminate_called)
        self.assertFalse(process.kill_called)

    def test_cleanup_when_terminate_succeeds(self) -> None:
        """A well-behaved process responds to terminate within the timeout.
        doCleanups must still run."""

        process = FakeProcess(terminate_works=True)
        fixture = FakeFixture()
        _run_finally_block(process, fixture)

        self.assertTrue(fixture.cleaned_up)
        self.assertTrue(process.terminate_called)
        self.assertFalse(process.kill_called)

    def test_cleanup_when_terminate_times_out_then_kill(self) -> None:
        """An unresponsive process that ignores terminate should be killed,
        and doCleanups must still run."""

        process = FakeProcess(terminate_works=False)
        fixture = FakeFixture()
        _run_finally_block(process, fixture)

        self.assertTrue(fixture.cleaned_up)
        self.assertTrue(process.terminate_called)
        self.assertTrue(process.kill_called)

    def test_cleanup_when_no_process_started(self) -> None:
        """When process is None (e.g. FFmpeg was never launched), cleanup
        must still run without errors."""

        fixture = FakeFixture()
        _run_finally_block(None, fixture)

        self.assertTrue(fixture.cleaned_up)

    def test_cleanup_after_setup_failure(self) -> None:
        """When setUp fails before a process starts, the finally block
        should still safely run doCleanups."""

        fixture = FakeFixture(setup_succeeds=False)
        process = None
        try:
            fixture.setUp()
        except RuntimeError:
            pass
        _run_finally_block(process, fixture)

        self.assertTrue(fixture.cleaned_up)

    def test_actual_script_finally_block_matches(self) -> None:
        """Verify the script file contains the expected nested-finally pattern
        so the extracted test logic stays in sync with the real code."""

        script = ROOT / "scripts" / "record_windows_demo.py"
        source = script.read_text(encoding="utf-8")
        # The key structural requirement: doCleanups inside an inner finally
        # that is protected from process termination failures.
        self.assertIn("finally:\n            fixture.doCleanups()", source)
        # terminate-then-kill pattern must be present.
        self.assertIn("process.kill()", source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
