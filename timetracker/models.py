"""Shared data models for tracking and reporting."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ActivityState:
    """The application/window currently observed by the tracker."""

    application: str
    window_title: str
    is_idle: bool = False


@dataclass(frozen=True, slots=True)
class ActivitySnapshot:
    """A point-in-time Windows activity measurement."""

    state: ActivityState
    idle_seconds: float


@dataclass(frozen=True, slots=True)
class ActivityPeriod:
    """A persisted continuous activity period."""

    id: int
    application: str
    window_title: str
    started_at: datetime
    ended_at: datetime
    duration_seconds: float
    is_idle: bool

