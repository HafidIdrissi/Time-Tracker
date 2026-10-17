from __future__ import annotations

import queue
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

sys.modules.setdefault("tkinter", mock.MagicMock())
sys.modules.setdefault("tkinter.ttk", sys.modules["tkinter"].ttk)
sys.modules.setdefault("tkinter.messagebox", sys.modules["tkinter"].messagebox)
sys.modules.setdefault("tkinter.filedialog", sys.modules["tkinter"].filedialog)

import windows_app
from timetracker.instance_lock import DatabaseLock, lock_name

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESS_TIMEOUT = 10

HOLDER_SCRIPT = """
import sys
from pathlib import Path
from timetracker.instance_lock import DatabaseLock

lock = DatabaseLock(Path(sys.argv[1]))
print("acquired" if lock.acquire() else "busy", flush=True)
sys.stdin.read()
"""


class LockNameTests(unittest.TestCase):
    def test_relative_segments_resolve_to_the_same_name(self) -> None:
        base = Path(tempfile.gettempdir())

        self.assertEqual(
            lock_name(base / "data" / "activity.db"),
            lock_name(base / "data" / ".." / "data" / "activity.db"),
        )

    @unittest.skipUnless(sys.platform == "win32", "Windows paths ignore letter case")
    def test_letter_case_does_not_change_the_name(self) -> None:
        path = Path(tempfile.gettempdir()) / "Data" / "Activity.db"

        self.assertEqual(lock_name(path), lock_name(Path(str(path).upper())))

    def test_separately_located_databases_get_different_names(self) -> None:
        base = Path(tempfile.gettempdir())

        self.assertNotEqual(
            lock_name(base / "installed" / "data" / "activity.db"),
            lock_name(base / "portable" / "data" / "activity.db"),
        )


@unittest.skipUnless(sys.platform == "win32", "The database lock uses a Windows mutex")
class DatabaseLockTests(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.database = Path(directory.name) / "data" / "activity.db"
        self.other_database = Path(directory.name) / "portable" / "data" / "activity.db"

    def new_lock(self, path: Path) -> DatabaseLock:
        lock = DatabaseLock(path)
        self.addCleanup(lock.release)
        return lock

    def start_holder(self, path: Path) -> subprocess.Popen[str]:
        process = subprocess.Popen(
            [sys.executable, "-c", HOLDER_SCRIPT, str(path)],
            cwd=PROJECT_ROOT,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
        )

        def stop() -> None:
            if process.poll() is None:
                process.kill()
            process.communicate(timeout=PROCESS_TIMEOUT)

        self.addCleanup(stop)
        return process

    def read_status(self, process: subprocess.Popen[str]) -> str:

        lines: queue.Queue[str] = queue.Queue()
        threading.Thread(target=lambda: lines.put(process.stdout.readline()), daemon=True).start()

        try:
            return lines.get(timeout=PROCESS_TIMEOUT).strip()
        except queue.Empty:
            self.fail(f"Holder process did not report within {PROCESS_TIMEOUT} s")

    def test_release_makes_the_lock_available_again(self) -> None:
        first = self.new_lock(self.database)
        self.assertTrue(first.acquire())

        first.release()

        self.assertTrue(self.new_lock(self.database).acquire())

    def test_release_without_acquire_does_nothing(self) -> None:
        self.new_lock(self.database).release()

        self.assertTrue(self.new_lock(self.database).acquire())

    def test_lock_held_by_another_process_is_refused(self) -> None:
        holder = self.start_holder(self.database)
        self.assertEqual(self.read_status(holder), "acquired")

        self.assertFalse(self.new_lock(self.database).acquire())
        self.assertTrue(self.new_lock(self.other_database).acquire())

    def test_equivalent_path_in_another_process_shares_the_lock(self) -> None:
        equivalent = self.database.parent / ".." / "DATA" / "ACTIVITY.db"
        holder = self.start_holder(equivalent)
        self.assertEqual(self.read_status(holder), "acquired")

        self.assertFalse(self.new_lock(self.database).acquire())

    def test_lock_is_released_when_the_holding_process_exits(self) -> None:
        holder = self.start_holder(self.database)
        self.assertEqual(self.read_status(holder), "acquired")

        holder.communicate(input="", timeout=PROCESS_TIMEOUT)

        self.assertEqual(holder.returncode, 0)
        self.assertTrue(self.new_lock(self.database).acquire())

    def test_lock_is_released_when_the_holding_process_is_killed(self) -> None:
        holder = self.start_holder(self.database)
        self.assertEqual(self.read_status(holder), "acquired")

        holder.kill()
        holder.communicate(timeout=PROCESS_TIMEOUT)

        self.assertNotEqual(holder.returncode, 0)
        self.assertTrue(self.new_lock(self.database).acquire())


class MainLockTests(unittest.TestCase):
    def run_main(
        self,
        acquired: bool,
        app_error: Exception | None = None,
        loop_error: Exception | None = None,
    ):
        self.lock = lock = mock.Mock()

        lock.acquire.return_value = acquired
        root = mock.Mock()
        root.mainloop.side_effect = loop_error
        with(
            mock.patch.object(windows_app.sys, "platform", "win32"),
            mock.patch.object(windows_app, "DatabaseLock", return_value=lock) as lock_class,
            mock.patch.object(windows_app.tk, "Tk", return_value=root),
            mock.patch.object(windows_app, "TimeTrackerApp", side_effect=app_error) as app_class,
            mock.patch.object(windows_app, "show_already_running") as already_running,
        ):
            result = windows_app.main()

        return result, lock, lock_class, app_class, already_running

    def test_main_locks_the_configured_database(self) -> None:
        result, lock, lock_class, app_class, already_running = self.run_main(True)

        self.assertEqual(result, 0)
        lock_class.assert_called_once_with(windows_app.DATABASE_PATH)
        app_class.assert_called_once()
        already_running.assert_not_called()
        lock.release.assert_called_once_with()

    def test_second_copy_shows_message_and_does_not_start_tracker(self) -> None:
        result, _, _, app_class, already_running = self.run_main(False)

        self.assertEqual(result, 1)
        already_running.assert_called_once_with()
        app_class.assert_not_called()

    def test_lock_is_released_when_the_window_fails_to_start(self) -> None:
        with self.assertRaises(RuntimeError):
            self.run_main(True, app_error=RuntimeError("window failed"))

        self.lock.release.assert_called_once_with()

    def test_lock_is_released_when_the_window_loop_fails(self) -> None:
        with self.assertRaises(RuntimeError):
            self.run_main(True, loop_error=RuntimeError("window loop failed"))

        self.lock.release.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
