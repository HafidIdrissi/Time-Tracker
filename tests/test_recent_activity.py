from __future__ import annotations

import sys
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

sys.modules.setdefault("tkinter", mock.MagicMock())
sys.modules.setdefault("tkinter.ttk", sys.modules["tkinter"].ttk)
sys.modules.setdefault("tkinter.messagebox", sys.modules["tkinter"].messagebox)
sys.modules.setdefault("tkinter.filedialog", sys.modules["tkinter"].filedialog)

import windows_app
from timetracker.models import ActivityPeriod


class FakeTree:
    def __init__(self) -> None:
        self.order: list[str] = []
        self.values: dict[str, tuple[object, ...]] = {}
        self._selection: tuple[str, ...] = ()
        self._focus = ""
        self._offset = 0.0
        self.seen = ""
        self.focus_set_calls = 0

    def get_children(self) -> tuple[str, ...]:
        return tuple(self.order)

    def delete(self, item: str) -> None:
        self.order.remove(item)
        del self.values[item]
        self._selection = tuple(selected for selected in self._selection if selected != item)
        if self._focus == item:
            self._focus = ""

    def exists(self, item: str) -> bool:
        return item in self.values

    def insert(self, _parent: str, index: int, iid: str, values: tuple[object, ...]) -> str:
        self.order.insert(index, iid)
        self.values[iid] = values
        return iid

    def item(self, item: str, **kwargs: object) -> None:
        if "values" in kwargs:
            self.values[item] = kwargs["values"]  # type: ignore[assignment]

    def move(self, item: str, _parent: str, index: int) -> None:
        self.order.remove(item)
        self.order.insert(index, item)

    def selection(self) -> tuple[str, ...]:
        return self._selection

    def selection_set(self, item: str) -> None:
        self._selection = (item,)

    def selection_remove(self, *items: str) -> None:
        removed = set(items)
        self._selection = tuple(item for item in self._selection if item not in removed)

    def focus(self, item: str | None = None) -> str:
        if item is None:
            return self._focus
        self._focus = item
        return item

    def focus_set(self) -> None:
        self.focus_set_calls += 1

    def yview(self) -> tuple[float, float]:
        return (self._offset, min(1.0, self._offset + 0.2))

    def yview_moveto(self, fraction: float) -> None:
        self._offset = fraction

    def see(self, item: str) -> None:
        self.seen = item


def period(period_id: int, minute: int, title: str) -> ActivityPeriod:
    start = datetime(2026, 1, 15, 9, minute, tzinfo=timezone.utc)
    return ActivityPeriod(period_id, "Code.exe", title, start, start + timedelta(minutes=1), 60, False)


class RecentActivityTests(unittest.TestCase):
    def _app(self, tree: FakeTree) -> windows_app.TimeTrackerApp:
        app = windows_app.TimeTrackerApp.__new__(windows_app.TimeTrackerApp)
        app.recent_tree = tree
        return app

    def test_selection_scroll_and_removal(self) -> None:
        tree = FakeTree()
        app = self._app(tree)
        first, second = period(1, 0, "Older"), period(2, 1, "Newer")
        app._show_recent_periods([second, first])
        tree.selection_set("1")
        tree.focus("1")
        tree._offset = 0.4
        updated = period(1, 0, "Older updated")
        newest = period(3, 2, "Newest")
        app._show_recent_periods([newest, second, updated])
        self.assertEqual(tree.order, ["3", "2", "1"])
        self.assertEqual(tree.selection(), ("1",))
        self.assertEqual(tree.focus(), "1")
        self.assertIn("Older updated", tree.values["1"])
        self.assertEqual(tree.seen, "1")
        self.assertEqual(tree.focus_set_calls, 0)

        tree._offset = 0.0
        app._show_recent_periods([newest, second, updated])
        self.assertEqual(tree.yview()[0], 0.0)

        app._show_recent_periods([newest])
        self.assertEqual(tree.selection(), ())
        self.assertEqual(tree.order, ["3"])

        app._show_recent_periods([])
        self.assertEqual(tree.get_children(), ())
        self.assertEqual(tree.selection(), ())


if __name__ == "__main__":
    unittest.main()
