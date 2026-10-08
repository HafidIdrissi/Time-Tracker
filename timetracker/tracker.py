"""Polling loop that turns Windows snapshots into continuous periods."""

from __future__ import annotations

import logging
import math
import threading
from datetime import datetime, timedelta
from typing import Callable, Protocol

from .database import ActivityDatabase
from .models import ActivitySnapshot, ActivityState

LOGGER = logging.getLogger(__name__)

IDLE_STATE = ActivityState(
    application="Idle",
    window_title="No keyboard or mouse activity",
    is_idle=True,
)


class ActivityProvider(Protocol):
    def sample(self) -> ActivitySnapshot: ...


class ActivityTracker:
    """Track foreground-window changes and explicit idle periods."""

    def __init__(
        self,
        database: ActivityDatabase,
        provider: ActivityProvider,
        poll_interval: float = 5.0,
        idle_threshold: float = 180.0,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        if not math.isfinite(poll_interval) or poll_interval <= 0:
            raise ValueError("poll_interval must be finite and greater than zero")
        if not math.isfinite(idle_threshold) or idle_threshold <= 0:
            raise ValueError("idle_threshold must be finite and greater than zero")

        self.database = database
        self.provider = provider
        self.poll_interval = poll_interval
        self.idle_threshold = idle_threshold
        self._now = now or (lambda: datetime.now().astimezone())
        self._stop_event = threading.Event()
        self._period_id: int | None = None
        self._period_start: datetime | None = None
        self._state: ActivityState | None = None
        self._watermark:datetime|None=None

    def _state_for(self, snapshot: ActivitySnapshot) -> ActivityState:
        return IDLE_STATE if snapshot.idle_seconds >= self.idle_threshold else snapshot.state

    def record_snapshot(self, snapshot: ActivitySnapshot, observed_at: datetime) -> None:
        """Record one snapshot. Kept separate from the loop for deterministic tests."""
        if self._watermark is not None and observed_at < self._watermark:
            return

        state = self._state_for(snapshot)
        if self._state is None:
            self._start_period(state, observed_at)
            return

        if state == self._state:
            self._update_current(observed_at)
            return

        transition_at = observed_at
        if state.is_idle and not self._state.is_idle:
            # Attribute only the time beyond the threshold to inactivity, despite
            # the polling interval discovering the transition a few seconds late.
            excess_idle = max(0.0, snapshot.idle_seconds - self.idle_threshold)
            transition_at = observed_at - timedelta(seconds=excess_idle)
            if self._period_start is not None:
                transition_at = max(transition_at, self._period_start)

        self._update_current(transition_at)
        self._start_period(state, transition_at)
        if transition_at != observed_at:
            self._update_current(observed_at)
        self._watermark = observed_at
        

    def _start_period(self, state: ActivityState, started_at: datetime) -> None:
        self._state = state
        self._period_start = started_at
        self._period_id = self.database.create_period(state, started_at)
        if self._watermark is None or started_at>self._watermark:
            self._watermark = started_at

    def _update_current(self, ended_at: datetime) -> None:
        if self._period_id is None or self._period_start is None:
            return
        if self._watermark is not None and ended_at < self._watermark:
            ended_at = self._watermark
        self.database.update_period(self._period_id, self._period_start, ended_at)
        if self._watermark is None or ended_at > self._watermark:
            self._watermark = ended_at
 
    def run(self) -> None:
        """Poll until ``stop`` is called or Ctrl+C is received."""

        LOGGER.info(
            "Tracker started (%.1fs interval, idle after %.0fs)",
            self.poll_interval,
            self.idle_threshold,
        )
        try:
            while not self._stop_event.is_set():
                observed_at = self._now()
                try:
                    snapshot = self.provider.sample()
                    self.record_snapshot(snapshot, observed_at)
                except Exception:
                    # A transient inaccessible window must not stop a day of tracking.
                    LOGGER.exception("Unable to read the active window")
                self._stop_event.wait(self.poll_interval)
        finally:
            self._update_current(self._now())
            LOGGER.info("Tracker stopped")
            
           

    def stop(self) -> None:
        self._stop_event.set()

def test_clock_jump_backwards_preserves_confirmed_period_and_avoids_overlap(self) -> None:
        origin = datetime(2026, 7, 20, 10, 0, 0, tzinfo=timezone.utc)
        clock = {"value": origin}

        def fake_now() -> datetime:
            current = clock["value"]
            clock["value"] = current + timedelta(seconds=1)
            return current

        tracker = ActivityTracker(
            database=self.database,
            provider=self.provider,
            poll_interval=1.0,
            idle_threshold=180.0,
            now=fake_now,
        )

        app_a = ActivitySnapshot(
            process_name="code.exe",
            window_title="Editor",
            state=ActivityState("active", "code.exe", "Editor"),
            idle_seconds=0.0,
        )
        app_b = ActivitySnapshot(
            process_name="browser.exe",
            window_title="Docs",
            state=ActivityState("active", "browser.exe", "Docs"),
            idle_seconds=0.0,
        )

        # 1. Accept initial observations
        tracker.record_snapshot(app_a, origin)
        tracker.record_snapshot(app_a, origin + timedelta(seconds=30))

        periods = self.database.list_periods()
        self.assertEqual(len(periods), 1)
        self.assertEqual(periods[0].start, origin)
        self.assertEqual(periods[0].end, origin + timedelta(seconds=30))
        self.assertEqual(periods[0].duration_seconds, 30)

        # 2. Backwards jump: older observation must be rejected and not regress the end
        backwards_time = origin + timedelta(seconds=10)
        tracker.record_snapshot(app_b, backwards_time)

        periods = self.database.list_periods()
        self.assertEqual(len(periods), 1)
        self.assertEqual(periods[0].end, origin + timedelta(seconds=30))
        self.assertEqual(periods[0].duration_seconds, 30)

        # 3. Recovery at/after watermark: transition accepted cleanly without backwards overlap
        recovery_time = origin + timedelta(seconds=35)
        tracker.record_snapshot(app_b, recovery_time)

        periods = self.database.list_periods()
        self.assertEqual(len(periods), 2)
        self.assertEqual(periods[0].end, origin + timedelta(seconds=30))
        self.assertEqual(periods[1].start, recovery_time)

        # 4. Finalization on backwards clock preserves end time
        tracker._period_id = periods[1].id
        tracker._update_current(backwards_time)

        periods = self.database.list_periods()
        self.assertEqual(periods[1].end, recovery_time)












