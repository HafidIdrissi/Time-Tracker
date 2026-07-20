"""SQLite persistence for activity periods."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .models import ActivityPeriod, ActivityState


def to_utc(value: datetime) -> datetime:
    """Return an aware datetime normalized to UTC."""

    if value.tzinfo is None:
        raise ValueError("A timezone-aware datetime is required")
    return value.astimezone(timezone.utc)


def to_storage(value: datetime) -> str:
    """Serialize an aware datetime in a stable, sortable UTC format."""

    return to_utc(value).isoformat(timespec="milliseconds")


class ActivityDatabase:
    """Small SQLite repository designed to be safe alongside live reports."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path, timeout=10)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA journal_mode = WAL")
        self.connection.execute("PRAGMA synchronous = NORMAL")
        self._create_schema()

    def _create_schema(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS activity_periods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                application TEXT NOT NULL,
                window_title TEXT NOT NULL,
                started_at TEXT NOT NULL,
                ended_at TEXT NOT NULL,
                duration_seconds REAL NOT NULL DEFAULT 0
                    CHECK (duration_seconds >= 0),
                is_idle INTEGER NOT NULL DEFAULT 0
                    CHECK (is_idle IN (0, 1))
            );

            CREATE INDEX IF NOT EXISTS idx_activity_periods_time
            ON activity_periods (started_at, ended_at);
            """
        )
        self.connection.commit()

    def create_period(self, state: ActivityState, started_at: datetime) -> int:
        """Create a period immediately so recent data survives an abrupt exit."""

        stored_start = to_storage(started_at)
        cursor = self.connection.execute(
            """
            INSERT INTO activity_periods (
                application, window_title, started_at, ended_at,
                duration_seconds, is_idle
            ) VALUES (?, ?, ?, ?, 0, ?)
            """,
            (
                state.application,
                state.window_title,
                stored_start,
                stored_start,
                int(state.is_idle),
            ),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def update_period(
        self, period_id: int, started_at: datetime, ended_at: datetime
    ) -> None:
        """Advance a period's end time and stored duration."""

        start_utc = to_utc(started_at)
        end_utc = max(to_utc(ended_at), start_utc)
        duration = (end_utc - start_utc).total_seconds()
        self.connection.execute(
            """
            UPDATE activity_periods
            SET ended_at = ?, duration_seconds = ?
            WHERE id = ?
            """,
            (to_storage(end_utc), duration, period_id),
        )
        self.connection.commit()

    def periods_between(
        self, range_start: datetime, range_end: datetime
    ) -> list[ActivityPeriod]:
        """Return periods overlapping the half-open interval [start, end)."""

        rows = self.connection.execute(
            """
            SELECT id, application, window_title, started_at, ended_at,
                   duration_seconds, is_idle
            FROM activity_periods
            WHERE ended_at > ? AND started_at < ?
            ORDER BY started_at ASC, id ASC
            """,
            (to_storage(range_start), to_storage(range_end)),
        ).fetchall()
        return [
            self._period_from_row(row)
            for row in rows
        ]

    @staticmethod
    def _period_from_row(row: sqlite3.Row) -> ActivityPeriod:
        return ActivityPeriod(
            id=row["id"],
            application=row["application"],
            window_title=row["window_title"],
            started_at=datetime.fromisoformat(row["started_at"]),
            ended_at=datetime.fromisoformat(row["ended_at"]),
            duration_seconds=float(row["duration_seconds"]),
            is_idle=bool(row["is_idle"]),
        )

    def recent_periods(self, limit: int = 12) -> list[ActivityPeriod]:
        """Return the most recently observed periods, newest first."""

        if limit <= 0:
            raise ValueError("limit must be greater than zero")
        rows = self.connection.execute(
            """
            SELECT id, application, window_title, started_at, ended_at,
                   duration_seconds, is_idle
            FROM activity_periods
            ORDER BY ended_at DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [self._period_from_row(row) for row in rows]

    def clear_periods(self) -> None:
        """Permanently remove all recorded activity periods."""

        self.connection.execute("DELETE FROM activity_periods")
        self.connection.execute(
            "DELETE FROM sqlite_sequence WHERE name = 'activity_periods'"
        )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "ActivityDatabase":
        return self

    def __exit__(self, *_exc_info: object) -> None:
        self.close()
