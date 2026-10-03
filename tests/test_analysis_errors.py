from __future__ import annotations

import sys
import unittest
from unittest import mock

sys.modules.setdefault("tkinter", mock.MagicMock())
sys.modules.setdefault("tkinter.ttk", sys.modules["tkinter"].ttk)
sys.modules.setdefault("tkinter.messagebox", sys.modules["tkinter"].messagebox)
sys.modules.setdefault("tkinter.filedialog", sys.modules["tkinter"].filedialog)

import windows_app
from timetracker.categories import CategoryConfigError


class AnalysisErrorTests(unittest.TestCase):
    def _app(self) -> windows_app.TimeTrackerApp:
        app = windows_app.TimeTrackerApp.__new__(windows_app.TimeTrackerApp)
        app.closing = True
        app.analysis_error = False
        app.analysis_data = object()
        app.analysis_range = mock.Mock()
        app.analysis_range.get.return_value = "today"
        for name in (
            "analysis_period_text",
            "analysis_total_text",
            "analysis_average_text",
            "analysis_longest_text",
        ):
            setattr(app, name, mock.Mock())
        app._replace_tree_rows = mock.Mock()
        app._draw_usage_chart = mock.Mock()
        app._populate_analysis_rankings = mock.Mock()
        app.category_tree = mock.Mock()
        app.analysis_app_tree = mock.Mock()
        app.analysis_tab_tree = mock.Mock()
        app.root = mock.Mock()
        return app

    def test_failed_refresh_clears_stale_metrics_and_recovers(self) -> None:
        app = self._app()
        with mock.patch.object(
            windows_app,
            "load_categorizer",
            side_effect=CategoryConfigError("configuration could not be read"),
        ):
            app._refresh_analysis(schedule=False)
        self.assertTrue(app.analysis_error)
        self.assertIsNone(app.analysis_data)
        app.analysis_period_text.set.assert_called_with("Analysis unavailable")
        app.analysis_total_text.set.assert_called_with("—")
        self.assertNotIn("window", app.analysis_period_text.set.call_args.args[0].casefold())

        app._populate_analysis_rankings.reset_mock()
        database = mock.MagicMock()
        with (
            mock.patch.object(windows_app, "load_categorizer", return_value=mock.Mock()),
            mock.patch.object(windows_app, "ActivityDatabase", return_value=database),
            mock.patch.object(windows_app, "collect_periods", return_value=[]),
        ):
            app._refresh_analysis(schedule=False)
        self.assertFalse(app.analysis_error)
        app.analysis_total_text.set.assert_called_with("0 min")
        app._populate_analysis_rankings.assert_called_once()
        app._draw_usage_chart.assert_called()


if __name__ == "__main__":
    unittest.main()
