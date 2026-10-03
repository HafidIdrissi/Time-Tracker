from __future__ import annotations

import sys
import unittest
from unittest import mock

sys.modules.setdefault("tkinter", mock.MagicMock())
sys.modules.setdefault("tkinter.ttk", sys.modules["tkinter"].ttk)
sys.modules.setdefault("tkinter.messagebox", sys.modules["tkinter"].messagebox)
sys.modules.setdefault("tkinter.filedialog", sys.modules["tkinter"].filedialog)

import windows_app


class ReportsFolderTests(unittest.TestCase):
    def _app(self) -> windows_app.TimeTrackerApp:
        return windows_app.TimeTrackerApp.__new__(windows_app.TimeTrackerApp)

    def test_creation_failure_does_not_open_the_folder(self) -> None:
        reports = mock.Mock()
        reports.mkdir.side_effect = PermissionError("denied")
        app = self._app()
        with (
            mock.patch.object(windows_app, "REPORTS_DIRECTORY", reports),
            mock.patch.object(windows_app.os, "startfile", create=True) as startfile,
            mock.patch.object(windows_app.messagebox, "showerror") as showerror,
        ):
            app.open_reports_directory()
        startfile.assert_not_called()
        showerror.assert_called_once()
        self.assertEqual(showerror.call_args.args[0], "Unable to open")

    def test_open_failure_shows_one_dialog(self) -> None:
        reports = mock.Mock()
        app = self._app()
        with (
            mock.patch.object(windows_app, "REPORTS_DIRECTORY", reports),
            mock.patch.object(windows_app.os, "startfile", create=True, side_effect=OSError("busy")),
            mock.patch.object(windows_app.messagebox, "showerror") as showerror,
        ):
            app.open_reports_directory()
        reports.mkdir.assert_called_once_with(parents=True, exist_ok=True)
        showerror.assert_called_once()

    def test_success_opens_the_created_folder(self) -> None:
        reports = mock.Mock()
        reports.__str__ = mock.Mock(return_value="C:/demo/reports")
        app = self._app()
        with (
            mock.patch.object(windows_app, "REPORTS_DIRECTORY", reports),
            mock.patch.object(windows_app.os, "startfile", create=True) as startfile,
            mock.patch.object(windows_app.messagebox, "showerror") as showerror,
        ):
            app.open_reports_directory()
        startfile.assert_called_once_with("C:/demo/reports")
        showerror.assert_not_called()


if __name__ == "__main__":
    unittest.main()
