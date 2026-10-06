#!/usr/bin/env python
"""Graphical Windows application for Local Time Tracker."""

from __future__ import annotations

import os
import queue
import sqlite3
import sys
import threading
from datetime import date, datetime, timedelta
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from timetracker import __version__
from timetracker.analytics import UsageAnalytics, analyze_usage, usage_analysis_range
from timetracker.backup import backup_activity_database as copy_activity_database
from timetracker.categories import CategoryConfigError, load_categorizer
from timetracker.database import ActivityDatabase
from timetracker.exporting import export_activity
from timetracker.models import ActivityPeriod, ActivitySnapshot
from timetracker.preferences import load_tracking_preferences, save_tracking_preferences
from timetracker.reporting import (
    collect_periods,
    format_duration,
    generate_report,
    local_midnight,
)
from timetracker.tracker import ActivityTracker
from timetracker.windows import WindowsActivityProvider


def application_directory() -> Path:
    """Return the folder containing the script or packaged executable."""

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def bundled_resource(name: str) -> Path:
    """Locate a file embedded by PyInstaller, with a source-tree fallback."""

    bundle_dir = getattr(sys, "_MEIPASS", None)
    if bundle_dir:
        return Path(bundle_dir) / name
    return application_directory() / name


PORTABLE_MARKER = "portable.mode"


def is_portable_mode() -> bool:
    """Return whether the packaged application explicitly requests portable mode."""

    if not getattr(sys, "frozen", False):
        return False
    return (application_directory() / PORTABLE_MARKER).is_file()


def get_installation_mode() -> str:
    """Determine whether running in source, portable, or installed mode."""
    if not getattr(sys, "frozen", False):
        return "source"
    if is_portable_mode():
        return "portable"
    executable_directory = application_directory()
    project_candidate = executable_directory.parent.parent
    if (
        executable_directory.parent.name.casefold() == "dist"
        and (project_candidate / "track.py").is_file()
        and (project_candidate / "timetracker").is_dir()
    ):
        return "source"
    return "installed"


def storage_directory() -> Path:
    """Choose the writable data folder for the current application mode."""

    executable_directory = application_directory()

    if not getattr(sys, "frozen", False):
        return executable_directory

    if is_portable_mode():
        return executable_directory

    project_candidate = executable_directory.parent.parent
    if (
        executable_directory.parent.name.casefold() == "dist"
        and (project_candidate / "track.py").is_file()
        and (project_candidate / "timetracker").is_dir()
    ):
        return project_candidate

    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "LocalTimeTracker"
    return executable_directory


APP_DIRECTORY = storage_directory()
DATABASE_PATH = APP_DIRECTORY / "data" / "activity.db"
REPORTS_DIRECTORY = APP_DIRECTORY / "reports"


class TimeTrackerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Local Time Tracker")
        self.root.geometry("820x640")
        self.root.minsize(700, 520)

        self.status_text = tk.StringVar(value="Initializing...")
        self.window_text = tk.StringVar(value="Waiting for activity...")

        self.create_menu()
        self.create_widgets()

    def create_menu(self) -> None:
        menubar = tk.Menu(self.root)
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About Time Tracker", command=self.show_about_dialog, accelerator="F1")
        menubar.add_cascade(label="Help", menu=help_menu)
        self.root.config(menu=menubar)
        self.root.bind("<F1>", lambda event: self.show_about_dialog())

    def create_widgets(self) -> None:
        main_frame = ttk.Frame(self.root, padding=12)
        main_frame.pack(fill=tk.BOTH, expand=True)

        status_label = ttk.Label(main_frame, textvariable=self.status_text, font=("Segoe UI", 11, "bold"))
        status_label.pack(anchor=tk.W, pady=(0, 8))

        window_label = ttk.Label(main_frame, textvariable=self.window_text, font=("Segoe UI", 10))
        window_label.pack(anchor=tk.W, pady=(0, 16))

    def show_about_dialog(self) -> None:
        """Display an offline, keyboard-accessible About dialog."""
        dialog = tk.Toplevel(self.root)
        dialog.title("About Time Tracker")
        dialog.geometry("380x260")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        mode = get_installation_mode()

        content_frame = ttk.Frame(dialog, padding=16)
        content_frame.pack(fill=tk.BOTH, expand=True)

        title_label = ttk.Label(content_frame, text="Local Time Tracker", font=("Segoe UI", 12, "bold"))
        title_label.pack(anchor=tk.W, pady=(0, 4))

        version_label = ttk.Label(content_frame, text=f"Version: {__version__}", font=("Segoe UI", 10))
        version_label.pack(anchor=tk.W, pady=(0, 2))

        mode_label = ttk.Label(content_frame, text=f"Installation Mode: {mode}", font=("Segoe UI", 10))
        mode_label.pack(anchor=tk.W, pady=(0, 12))

        desc_label = ttk.Label(
            content_frame,
            text="An offline activity tracking and reporting utility for Windows.",
            font=("Segoe UI", 9),
            wraplength=340,
        )
        desc_label.pack(anchor=tk.W, pady=(0, 20))

        close_button = ttk.Button(content_frame, text="Close", command=dialog.destroy)
        close_button.pack(anchor=tk.E)
        close_button.focus_set()

        dialog.bind("<Escape>", lambda event: dialog.destroy())
        
        def on_close() -> None:
            dialog.destroy()
            try:
                self.root.focus_set()
            except Exception:
                pass

        dialog.protocol("WM_DELETE_WINDOW", on_close)
