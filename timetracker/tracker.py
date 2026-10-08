"""Polling loop that turns Windows snapshots into continuous periods."""

from __future__ import annotations

import logging
import math
import threading
from datetime import datetime, timedelta
from typing import Callable, Protocol
from timetracker.database import ActivityDatabase, to_utc
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
        observed_utc=to_utc(observed_at)
        if self._watermark is not None and observed_utc < self._watermark:
            return

        state = self._state_for(snapshot)
        if self._state is None:
            self._start_period(state, observed_utc)
            self._watermark = observed_utc
            return

        if state == self._state:
            self._update_current(observed_utc)
            self._watermark = observed_utc
            return

        transition_at = observed_utc
        if state.is_idle and not self._state.is_idle:
            # Attribute only the time beyond the threshold to inactivity, despite
            # the polling interval discovering the transition a few seconds late.
            excess_idle = max(0.0, snapshot.idle_seconds - self.idle_threshold)
            transition_at = observed_utc - timedelta(seconds=excess_idle)
            if self._period_start is not None:
                transition_at = max(transition_at, self._period_start)
            if self._watermark is not None and transition_at < self._watermark:
                transition_at = self._watermark

        self._update_current(transition_at)
        self._start_period(state, transition_at)
        if transition_at != observed_utc:
            self._update_current(observed_utc)
        self._watermark = observed_utc
        
    def _start_period(self, state: ActivityState, started_at: datetime) -> None:
        started_utc = to_utc(started_at)
        period_id = self.database.create_period(state, started_utc)
        self._period_id = period_id
        self._period_start = started_utc
        self._state = state

    def _update_current(self, ended_at: datetime) -> None:
        if self._period_id is None or self._period_start is None:
            return
        ended_utc = to_utc(ended_at)
        self.database.update_period(self._period_id, self._period_start, ended_utc)
 
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
            stop_at = self._now()
            if self._watermark is not None and stop_at < self._watermark:
                stop_at = self._watermark
            self._update_current(stop_at)
            LOGGER.info("Tracker stopped")
            
           

    def stop(self) -> None:
        self._stop_event.set()

