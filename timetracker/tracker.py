"""Polling loop that turns Windows snapshots into continuous periods."""

from __future__ import annotations

import logging
import threading
from datetime import datetime, timedelta
from typing import Callable, Protocol

from .database import ActivityDatabase
from .models import ActivitySnapshot, ActivityState

LOGGER = logging.getLogger(__name__)

IDLE_STATE = ActivityState(
    application="Inactif",
    window_title="Aucune activité clavier/souris",
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
        if poll_interval <= 0:
            raise ValueError("poll_interval must be greater than zero")
        if idle_threshold <= 0:
            raise ValueError("idle_threshold must be greater than zero")

        self.database = database
        self.provider = provider
        self.poll_interval = poll_interval
        self.idle_threshold = idle_threshold
        self._now = now or (lambda: datetime.now().astimezone())
        self._stop_event = threading.Event()
        self._period_id: int | None = None
        self._period_start: datetime | None = None
        self._state: ActivityState | None = None

    def _state_for(self, snapshot: ActivitySnapshot) -> ActivityState:
        return IDLE_STATE if snapshot.idle_seconds >= self.idle_threshold else snapshot.state

    def record_snapshot(self, snapshot: ActivitySnapshot, observed_at: datetime) -> None:
        """Record one snapshot. Kept separate from the loop for deterministic tests."""

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
        self._update_current(observed_at)

    def _start_period(self, state: ActivityState, started_at: datetime) -> None:
        self._state = state
        self._period_start = started_at
        self._period_id = self.database.create_period(state, started_at)

    def _update_current(self, ended_at: datetime) -> None:
        if self._period_id is None or self._period_start is None:
            return
        self.database.update_period(self._period_id, self._period_start, ended_at)

    def run(self) -> None:
        """Poll until ``stop`` is called or Ctrl+C is received."""

        LOGGER.info(
            "Tracker démarré (intervalle %.1fs, inactivité après %.0fs)",
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
                    LOGGER.exception("Impossible de lire la fenêtre active")
                self._stop_event.wait(self.poll_interval)
        finally:
            self._update_current(self._now())
            LOGGER.info("Tracker arrêté")

    def stop(self) -> None:
        self._stop_event.set()

