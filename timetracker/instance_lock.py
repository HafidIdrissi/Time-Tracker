"""Per-database lock that keeps two desktop trackers off the same database."""

from __future__ import annotations

import ctypes
import hashlib
import os
import sys
from pathlib import Path
from typing import Any

ERROR_ALREADY_EXISTS = 183
LOCK_NAME_PREFIX = "Local\\LocalTimeTracker-"


def lock_name(database_path: Path) -> str:
    normalized = os.path.normcase(str(Path(database_path).resolve()))
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return LOCK_NAME_PREFIX + digest


def _kernel32() -> Any:
    if sys.platform != "win32":
        raise OSError("The database lock is available on Windows only.")
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateMutexW.argtypes = (wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR)
    kernel32.CreateMutexW.restype = wintypes.HANDLE
    kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel32.CloseHandle.restype = wintypes.BOOL
    return kernel32


class DatabaseLock:
    def __init__(self, database_path: Path) -> None:
        self.name = lock_name(database_path)
        self._handle: int | None = None
        self._kernel32: Any = None

    def acquire(self) -> bool:
        """Take the lock; return False if another process already holds it."""

        if self._handle is not None:
            return True

        kernel32 = _kernel32()
        ctypes.set_last_error(0)
        handle = kernel32.CreateMutexW(None, False, self.name)

        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())

        if ctypes.get_last_error() == ERROR_ALREADY_EXISTS:
            kernel32.CloseHandle(handle)
            return False

        self._handle = handle
        self._kernel32 = kernel32
        return True

    def release(self) -> None:
        if self._handle is None:
            return
        self._kernel32.CloseHandle(self._handle)
        self._handle = None
