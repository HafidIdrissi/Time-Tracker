"""Windows-specific foreground window and idle-time collection."""

from __future__ import annotations

import sys
from typing import Any

from .models import ActivitySnapshot, ActivityState


class WindowsActivityProvider:
    """Read the foreground process/window using pywin32 and psutil."""

    def __init__(self) -> None:
        if sys.platform != "win32":
            raise RuntimeError("Activity tracking is available on Windows only.")

        try:
            import psutil
            import win32api
            import win32gui
            import win32process
        except ImportError as exc:
            raise RuntimeError(
                "Windows dependencies are missing. Run: pip install -r requirements.txt"
            ) from exc

        self.psutil: Any = psutil
        self.win32api: Any = win32api
        self.win32gui: Any = win32gui
        self.win32process: Any = win32process

    def _idle_seconds(self) -> float:
        # GetTickCount wraps roughly every 49.7 days. The mask handles that wrap.
        last_input_tick = int(self.win32api.GetLastInputInfo())
        current_tick = int(self.win32api.GetTickCount())
        elapsed_ms = (current_tick - last_input_tick) & 0xFFFFFFFF
        return elapsed_ms / 1000.0

    def _foreground_window(self) -> tuple[str, str]:
        hwnd = self.win32gui.GetForegroundWindow()
        if not hwnd:
            return "System", "No active window"

        title = self.win32gui.GetWindowText(hwnd).strip() or "(Untitled)"
        try:
            _thread_id, process_id = self.win32process.GetWindowThreadProcessId(hwnd)
            application = self.psutil.Process(process_id).name()
        except (self.psutil.Error, OSError):
            application = "Unknown process"

        return application, title

    def sample(self) -> ActivitySnapshot:
        """Take one foreground-window and idle-time sample."""

        idle_seconds = self._idle_seconds()
        application, title = self._foreground_window()
        return ActivitySnapshot(
            state=ActivityState(application, title),
            idle_seconds=idle_seconds,
        )
