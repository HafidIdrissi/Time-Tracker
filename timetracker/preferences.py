"""Local sampling and idle preferences, separate from category rules."""

from __future__ import annotations

import json
import os
from pathlib import Path

SAMPLE_SECONDS_CHOICES = ("1", "2", "5", "10")
IDLE_MINUTES_CHOICES = ("1", "3", "5", "10", "15")
DEFAULT_SAMPLE_SECONDS = "1"
DEFAULT_IDLE_MINUTES = "3"


def load_tracking_preferences(path: str | Path) -> tuple[str, str]:
    """Return valid sample seconds and idle minutes, using defaults when needed."""

    config_path = Path(path)
    sample_seconds = DEFAULT_SAMPLE_SECONDS
    idle_minutes = DEFAULT_IDLE_MINUTES
    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeError):
        return sample_seconds, idle_minutes
    if not isinstance(raw, dict):
        return sample_seconds, idle_minutes
    candidate_sample = raw.get("sample_seconds", DEFAULT_SAMPLE_SECONDS)
    candidate_idle = raw.get("idle_minutes", DEFAULT_IDLE_MINUTES)
    if isinstance(candidate_sample, str) and candidate_sample in SAMPLE_SECONDS_CHOICES:
        sample_seconds = candidate_sample
    if isinstance(candidate_idle, str) and candidate_idle in IDLE_MINUTES_CHOICES:
        idle_minutes = candidate_idle
    return sample_seconds, idle_minutes


def save_tracking_preferences(
    path: str | Path, sample_seconds: str, idle_minutes: str
) -> None:
    """Atomically store one valid pair of tracking options."""

    if sample_seconds not in SAMPLE_SECONDS_CHOICES:
        raise ValueError("sample_seconds is not a supported choice")
    if idle_minutes not in IDLE_MINUTES_CHOICES:
        raise ValueError("idle_minutes is not a supported choice")

    config_path = Path(path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "sample_seconds": sample_seconds,
        "idle_minutes": idle_minutes,
    }
    temporary = config_path.with_name(config_path.name + ".partial")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    try:
        os.replace(temporary, config_path)
    except OSError:
        temporary.unlink(missing_ok=True)
        raise
