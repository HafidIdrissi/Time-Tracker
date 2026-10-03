from __future__ import annotations

import unittest

from timetracker.windows import WindowsActivityProvider


class FakeApi:
    def __init__(self, last_input: int, tick: int) -> None:
        self.last_input = last_input
        self.tick = tick

    def GetLastInputInfo(self) -> int:
        return self.last_input

    def GetTickCount(self) -> int:
        return self.tick


class FakeGui:
    def __init__(self, hwnd: int, title: str) -> None:
        self.hwnd = hwnd
        self.title = title

    def GetForegroundWindow(self) -> int:
        return self.hwnd

    def GetWindowText(self, _hwnd: int) -> str:
        return self.title


class FakeProcessApi:
    def __init__(self, process_id: int = 42, error: Exception | None = None) -> None:
        self.process_id = process_id
        self.error = error

    def GetWindowThreadProcessId(self, _hwnd: int) -> tuple[int, int]:
        if self.error is not None:
            raise self.error
        return (7, self.process_id)


class FakePsutil:
    class Error(Exception):
        pass

    def __init__(self, name: str = "Code.exe", error: Exception | None = None) -> None:
        self._name = name
        self._error = error

    def Process(self, _process_id: int) -> "FakePsutil":
        return self

    def name(self) -> str:
        if self._error is not None:
            raise self._error
        return self._name


def provider(
    *,
    last_input: int = 1_000,
    tick: int = 5_000,
    hwnd: int = 10,
    title: str = "Fictional document",
    process_error: Exception | None = None,
    process_name: str = "Code.exe",
    name_error: Exception | None = None,
) -> WindowsActivityProvider:
    fake = WindowsActivityProvider.__new__(WindowsActivityProvider)
    fake.win32api = FakeApi(last_input, tick)
    fake.win32gui = FakeGui(hwnd, title)
    fake.win32process = FakeProcessApi(error=process_error)
    fake.psutil = FakePsutil(process_name, name_error)
    return fake


class WindowsProviderTests(unittest.TestCase):
    def test_idle_seconds_and_tick_wraparound(self) -> None:
        self.assertEqual(provider().sample().idle_seconds, 4)
        wrapped = provider(last_input=0xFFFFFFF0, tick=1000)
        self.assertAlmostEqual(wrapped._idle_seconds(), 1.016)

    def test_foreground_fallbacks_use_synthetic_values(self) -> None:
        missing = provider(hwnd=0)
        self.assertEqual(missing._foreground_window(), ("System", "No active window"))

        untitled = provider(title="   ")
        self.assertEqual(untitled._foreground_window()[1], "(Untitled)")

        named = provider(process_name="FictionalApp.exe", title="Fictional document")
        self.assertEqual(named._foreground_window(), ("FictionalApp.exe", "Fictional document"))

        psutil_error = provider(name_error=FakePsutil.Error("lookup failed"))
        self.assertEqual(psutil_error._foreground_window()[0], "Unknown process")

        os_error = provider(process_error=OSError("access denied"))
        self.assertEqual(os_error._foreground_window()[0], "Unknown process")

    def test_sample_combines_foreground_state_and_idle_duration(self) -> None:
        snapshot = provider(process_name="notes.exe", title="Fictional note").sample()
        self.assertEqual(snapshot.state.application, "notes.exe")
        self.assertEqual(snapshot.state.window_title, "Fictional note")
        self.assertFalse(snapshot.state.is_idle)
        self.assertEqual(snapshot.idle_seconds, 4)


if __name__ == "__main__":
    unittest.main()
