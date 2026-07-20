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
from tkinter import messagebox, ttk

from timetracker.analytics import UsageAnalytics, analyze_usage
from timetracker.categories import CategoryConfigError, load_categorizer
from timetracker.database import ActivityDatabase
from timetracker.models import ActivityPeriod, ActivitySnapshot
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


def storage_directory() -> Path:
    """Choose a writable data folder that survives rebuilding the executable."""

    executable_directory = application_directory()
    if not getattr(sys, "frozen", False):
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


def format_clock(seconds: float) -> str:
    """Format a live duration without rounding away seconds."""

    total_seconds = max(0, int(seconds))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, remaining_seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{remaining_seconds:02d}"


class ObservableActivityProvider:
    """Forward Windows samples to the tracker and to the user interface."""

    def __init__(
        self,
        provider: WindowsActivityProvider,
        messages: queue.Queue[tuple[str, object]],
    ) -> None:
        self.provider = provider
        self.messages = messages

    def sample(self) -> ActivitySnapshot:
        snapshot = self.provider.sample()
        self.messages.put(("sample", snapshot))
        return snapshot


class TimeTrackerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.messages: queue.Queue[tuple[str, object]] = queue.Queue()
        self.tracker: ActivityTracker | None = None
        self.tracker_thread: threading.Thread | None = None
        self.stop_requested = False
        self.closing = False
        self.pending_reset = False
        self.restart_after_reset = False
        self.running_idle_threshold = 180.0
        self.running_poll_interval = 1.0
        self.analysis_data: UsageAnalytics | None = None
        self.current_signature: tuple[str, str] | None = None
        self.current_since: datetime | None = None
        self.tracking_started_at: datetime | None = None

        self.status_text = tk.StringVar(value="Arrêté")
        self.status_detail = tk.StringVar(value="Le suivi n'est pas en cours")
        self.application_text = tk.StringVar(value="—")
        self.window_text = tk.StringVar(value="Aucune fenêtre observée")
        self.active_text = tk.StringVar(value="0 min")
        self.idle_text = tk.StringVar(value="0 min")
        self.app_count_text = tk.StringVar(value="0")
        self.period_count_text = tk.StringVar(value="0")
        self.current_duration_text = tk.StringVar(value="00:00:00")
        self.tracking_duration_text = tk.StringVar(value="00:00:00")
        self.last_measure_text = tk.StringVar(value="—")
        self.live_idle_text = tk.StringVar(value="0 s")
        self.poll_interval_text = tk.StringVar(value="1")
        self.idle_threshold_text = tk.StringVar(value="3")
        self.analysis_range = tk.StringVar(value="today")
        self.analysis_period_text = tk.StringVar(value="Aujourd'hui")
        self.analysis_total_text = tk.StringVar(value="0 min")
        self.analysis_average_text = tk.StringVar(value="0 min")
        self.analysis_longest_text = tk.StringVar(value="0 min")
        self.report_date = tk.StringVar(value=date.today().isoformat())

        self._configure_window()
        self._configure_styles()
        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(150, self._process_messages)
        self.root.after(500, self._refresh_summary)
        self.root.after(700, self._refresh_analysis)
        self.root.after(1000, self._update_live_durations)
        self.root.after(250, self.start_tracking)

    def _configure_window(self) -> None:
        self.root.title("Local Time Tracker")
        self.root.geometry("1060x850")
        self.root.minsize(860, 680)
        self.root.configure(background="#f1f5f9")

    def _configure_styles(self) -> None:
        style = ttk.Style(self.root)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        style.configure("App.TFrame", background="#f1f5f9")
        style.configure("Card.TFrame", background="#ffffff")
        style.configure(
            "Title.TLabel",
            background="#f1f5f9",
            foreground="#162033",
            font=("Segoe UI Semibold", 24),
        )
        style.configure(
            "Subtitle.TLabel",
            background="#f1f5f9",
            foreground="#64748b",
            font=("Segoe UI", 10),
        )
        style.configure(
            "CardTitle.TLabel",
            background="#ffffff",
            foreground="#64748b",
            font=("Segoe UI", 9),
        )
        style.configure(
            "Metric.TLabel",
            background="#ffffff",
            foreground="#162033",
            font=("Segoe UI Semibold", 20),
        )
        style.configure(
            "CurrentApp.TLabel",
            background="#ffffff",
            foreground="#162033",
            font=("Segoe UI Semibold", 14),
        )
        style.configure(
            "CurrentWindow.TLabel",
            background="#ffffff",
            foreground="#64748b",
            font=("Segoe UI", 10),
        )
        style.configure("Accent.TButton", font=("Segoe UI Semibold", 10), padding=(16, 9))
        style.configure("App.TButton", font=("Segoe UI", 10), padding=(14, 9))
        style.configure("Danger.TButton", font=("Segoe UI Semibold", 10), padding=(14, 9))
        style.configure("Treeview", rowheight=27, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", font=("Segoe UI Semibold", 9))

    def _build_ui(self) -> None:
        container = ttk.Frame(self.root, style="App.TFrame", padding=(26, 22))
        container.pack(fill="both", expand=True)

        header = ttk.Frame(container, style="App.TFrame")
        header.pack(fill="x", pady=(0, 16))
        heading = ttk.Frame(header, style="App.TFrame")
        heading.pack(side="left", fill="x", expand=True)
        ttk.Label(heading, text="Local Time Tracker", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            heading,
            text="Suivi d'activité local et privé sur cet ordinateur",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(3, 0))

        status = tk.Label(
            header,
            textvariable=self.status_text,
            bg="#e2e8f0",
            fg="#475569",
            font=("Segoe UI Semibold", 10),
            padx=14,
            pady=7,
        )
        status.pack(side="right")
        self.status_badge = status

        controls = ttk.Frame(container, style="App.TFrame")
        controls.pack(fill="x", pady=(0, 14))
        action_buttons = ttk.Frame(controls, style="App.TFrame")
        action_buttons.pack(side="left")
        self.start_button = ttk.Button(
            action_buttons,
            text="Démarrer le suivi",
            command=self.start_tracking,
            style="Accent.TButton",
        )
        self.start_button.pack(side="left")
        self.stop_button = ttk.Button(
            action_buttons,
            text="Arrêter",
            command=self.stop_tracking,
            style="App.TButton",
            state="disabled",
        )
        self.stop_button.pack(side="left", padx=(10, 0))
        self.reset_button = ttk.Button(
            action_buttons,
            text="Réinitialiser",
            command=self.reset_activity,
            style="Danger.TButton",
        )
        self.reset_button.pack(side="left", padx=(10, 0))

        settings = ttk.Frame(controls, style="App.TFrame")
        settings.pack(side="right")
        ttk.Label(settings, text="Mesure", style="Subtitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        self.interval_box = ttk.Combobox(
            settings,
            textvariable=self.poll_interval_text,
            values=("1", "2", "5", "10"),
            width=4,
            state="readonly",
        )
        self.interval_box.grid(row=1, column=0, sticky="w", pady=(3, 0))
        ttk.Label(settings, text="seconde(s)", style="Subtitle.TLabel").grid(
            row=1, column=1, padx=(5, 18), pady=(3, 0)
        )
        ttk.Label(settings, text="Inactif après", style="Subtitle.TLabel").grid(
            row=0, column=2, sticky="w"
        )
        self.idle_box = ttk.Combobox(
            settings,
            textvariable=self.idle_threshold_text,
            values=("1", "3", "5", "10", "15"),
            width=4,
            state="readonly",
        )
        self.idle_box.grid(row=1, column=2, sticky="w", pady=(3, 0))
        ttk.Label(settings, text="minute(s)", style="Subtitle.TLabel").grid(
            row=1, column=3, padx=(5, 0), pady=(3, 0)
        )

        ttk.Label(container, textvariable=self.status_detail, style="Subtitle.TLabel").pack(
            anchor="w", pady=(0, 10)
        )

        notebook = ttk.Notebook(container)
        notebook.pack(fill="both", expand=True)
        dashboard = ttk.Frame(notebook, style="App.TFrame", padding=(0, 14, 0, 0))
        analysis_tab = ttk.Frame(notebook, style="App.TFrame", padding=(0, 14, 0, 0))
        reports_tab = ttk.Frame(notebook, style="App.TFrame", padding=(0, 14, 0, 0))
        notebook.add(dashboard, text="  Tableau de bord  ")
        notebook.add(analysis_tab, text="  Analyse d'utilisation  ")
        notebook.add(reports_tab, text="  Rapports et données  ")

        current_card = ttk.Frame(dashboard, style="Card.TFrame", padding=(20, 17))
        current_card.pack(fill="x", pady=(0, 14))
        current_card.columnconfigure(0, weight=1)
        ttk.Label(
            current_card,
            text="UTILISATION EN DIRECT",
            style="CardTitle.TLabel",
        ).grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(
            current_card,
            textvariable=self.application_text,
            style="CurrentApp.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(8, 1))
        ttk.Label(
            current_card,
            textvariable=self.window_text,
            style="CurrentWindow.TLabel",
            wraplength=680,
        ).grid(row=2, column=0, sticky="w")

        live_details = ttk.Frame(current_card, style="Card.TFrame")
        live_details.grid(row=1, column=1, rowspan=2, sticky="e", padx=(20, 0))
        self._detail_value(live_details, 0, "Fenêtre active depuis", self.current_duration_text)
        self._detail_value(live_details, 1, "Inactivité clavier/souris", self.live_idle_text)
        self._detail_value(live_details, 2, "Dernière mesure", self.last_measure_text)

        metrics = ttk.Frame(dashboard, style="App.TFrame")
        metrics.pack(fill="x", pady=(0, 14))
        for column in range(4):
            metrics.columnconfigure(column, weight=1, uniform="metrics")
        self._metric_card(metrics, 0, "TEMPS ACTIF AUJOURD'HUI", self.active_text)
        self._metric_card(metrics, 1, "TEMPS INACTIF", self.idle_text, padx=10)
        self._metric_card(metrics, 2, "APPLICATIONS", self.app_count_text, padx=10)
        self._metric_card(metrics, 3, "PÉRIODES DÉTECTÉES", self.period_count_text, padx=10)

        recent_card = ttk.Frame(dashboard, style="Card.TFrame", padding=(18, 15))
        recent_card.pack(fill="both", expand=True)
        recent_header = ttk.Frame(recent_card, style="Card.TFrame")
        recent_header.pack(fill="x", pady=(0, 10))
        ttk.Label(recent_header, text="ACTIVITÉ RÉCENTE", style="CardTitle.TLabel").pack(
            side="left"
        )
        ttk.Label(
            recent_header,
            text="Durée du suivi :",
            background="#ffffff",
            foreground="#64748b",
        ).pack(side="right")
        ttk.Label(
            recent_header,
            textvariable=self.tracking_duration_text,
            background="#ffffff",
            foreground="#162033",
            font=("Segoe UI Semibold", 9),
        ).pack(side="right", padx=(0, 5))

        columns = ("start", "application", "title", "duration", "state")
        self.recent_tree = ttk.Treeview(
            recent_card,
            columns=columns,
            show="headings",
            height=6,
            selectmode="browse",
        )
        headings = {
            "start": "Début",
            "application": "Application",
            "title": "Fenêtre",
            "duration": "Durée",
            "state": "État",
        }
        widths = {"start": 85, "application": 130, "title": 470, "duration": 90, "state": 75}
        for column in columns:
            self.recent_tree.heading(column, text=headings[column])
            self.recent_tree.column(
                column,
                width=widths[column],
                minwidth=60,
                anchor="w" if column not in {"duration", "state"} else "center",
                stretch=column == "title",
            )
        scrollbar = ttk.Scrollbar(recent_card, orient="vertical", command=self.recent_tree.yview)
        self.recent_tree.configure(yscrollcommand=scrollbar.set)
        self.recent_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self._build_analysis_tab(analysis_tab)

        report_card = ttk.Frame(reports_tab, style="Card.TFrame", padding=(20, 18))
        report_card.pack(fill="x", pady=(0, 14))
        ttk.Label(report_card, text="CONSULTER UNE JOURNÉE", style="CardTitle.TLabel").grid(
            row=0, column=0, columnspan=3, sticky="w"
        )
        ttk.Label(
            report_card,
            text="Date (AAAA-MM-JJ)",
            background="#ffffff",
            foreground="#475569",
        ).grid(row=1, column=0, sticky="w", pady=(12, 4))
        date_entry = ttk.Entry(report_card, textvariable=self.report_date, width=18)
        date_entry.grid(row=2, column=0, sticky="w")
        self.report_button = ttk.Button(
            report_card,
            text="Générer et ouvrir le rapport",
            command=self.generate_selected_report,
            style="Accent.TButton",
        )
        self.report_button.grid(row=2, column=1, sticky="w", padx=(12, 0))
        ttk.Button(
            report_card,
            text="Ouvrir le dossier des rapports",
            command=self.open_reports_directory,
            style="App.TButton",
        ).grid(row=2, column=2, sticky="w", padx=(10, 0))
        report_card.columnconfigure(3, weight=1)

        data_card = ttk.Frame(reports_tab, style="Card.TFrame", padding=(20, 18))
        data_card.pack(fill="x")
        ttk.Label(data_card, text="GESTION DES DONNÉES", style="CardTitle.TLabel").pack(
            anchor="w"
        )
        ttk.Label(
            data_card,
            text=f"Base locale : {DATABASE_PATH}",
            background="#ffffff",
            foreground="#475569",
            wraplength=900,
        ).pack(anchor="w", pady=(12, 3))
        ttk.Label(
            data_card,
            text="Réinitialiser efface définitivement toutes les périodes enregistrées. "
            "Les rapports HTML déjà générés sont conservés.",
            background="#ffffff",
            foreground="#64748b",
            wraplength=900,
        ).pack(anchor="w", pady=(0, 12))
        self.reset_data_button = ttk.Button(
            data_card,
            text="Réinitialiser tout l'historique",
            command=self.reset_activity,
            style="Danger.TButton",
        )
        self.reset_data_button.pack(anchor="w")

        ttk.Label(
            container,
            text="L'application continue à enregistrer lorsqu'elle est réduite. "
            "Fermer cette fenêtre arrête le suivi.",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(14, 0))

    def _detail_value(
        self,
        parent: ttk.Frame,
        row: int,
        label: str,
        value: tk.StringVar,
    ) -> None:
        ttk.Label(
            parent,
            text=label,
            background="#ffffff",
            foreground="#64748b",
            font=("Segoe UI", 8),
        ).grid(row=row, column=0, sticky="e", padx=(0, 8), pady=1)
        ttk.Label(
            parent,
            textvariable=value,
            background="#ffffff",
            foreground="#162033",
            font=("Segoe UI Semibold", 9),
        ).grid(row=row, column=1, sticky="e", pady=1)

    def _build_analysis_tab(self, parent: ttk.Frame) -> None:
        selector = ttk.Frame(parent, style="Card.TFrame", padding=(18, 12))
        selector.pack(fill="x", pady=(0, 12))
        ttk.Label(selector, text="PÉRIODE ANALYSÉE", style="CardTitle.TLabel").pack(
            side="left", padx=(0, 18)
        )
        ttk.Radiobutton(
            selector,
            text="Aujourd'hui",
            variable=self.analysis_range,
            value="today",
            command=lambda: self._refresh_analysis(schedule=False),
        ).pack(side="left")
        ttk.Radiobutton(
            selector,
            text="7 derniers jours",
            variable=self.analysis_range,
            value="week",
            command=lambda: self._refresh_analysis(schedule=False),
        ).pack(side="left", padx=(16, 0))
        ttk.Label(
            selector,
            textvariable=self.analysis_period_text,
            background="#ffffff",
            foreground="#64748b",
        ).pack(side="right")

        summary = ttk.Frame(parent, style="App.TFrame")
        summary.pack(fill="x", pady=(0, 12))
        for column in range(3):
            summary.columnconfigure(column, weight=1, uniform="analysis")
        self._metric_card(summary, 0, "TEMPS D'ÉCRAN ACTIF", self.analysis_total_text)
        self._metric_card(summary, 1, "MOYENNE PAR JOUR", self.analysis_average_text, padx=10)
        self._metric_card(summary, 2, "SESSION LA PLUS LONGUE", self.analysis_longest_text, padx=10)

        chart_card = ttk.Frame(parent, style="Card.TFrame", padding=(18, 14))
        chart_card.pack(fill="x", pady=(0, 12))
        ttk.Label(chart_card, text="RÉPARTITION DANS LE TEMPS", style="CardTitle.TLabel").pack(
            anchor="w", pady=(0, 7)
        )
        self.usage_canvas = tk.Canvas(
            chart_card,
            height=130,
            background="#ffffff",
            highlightthickness=0,
        )
        self.usage_canvas.pack(fill="x")
        self.usage_canvas.bind("<Configure>", lambda _event: self._draw_usage_chart())

        rankings = ttk.Frame(parent, style="App.TFrame")
        rankings.pack(fill="both", expand=True)
        for column, weight in enumerate((1, 1, 2)):
            rankings.columnconfigure(column, weight=weight)
        rankings.rowconfigure(0, weight=1)

        category_card = ttk.Frame(rankings, style="Card.TFrame", padding=(14, 12))
        category_card.grid(row=0, column=0, sticky="nsew")
        ttk.Label(category_card, text="CATÉGORIES", style="CardTitle.TLabel").pack(
            anchor="w", pady=(0, 8)
        )
        self.category_tree = self._create_ranking_tree(
            category_card,
            ("name", "duration", "share"),
            ("Type", "Durée", "%"),
            (100, 65, 36),
        )

        app_card = ttk.Frame(rankings, style="Card.TFrame", padding=(14, 12))
        app_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        ttk.Label(app_card, text="APPLICATIONS LES PLUS UTILISÉES", style="CardTitle.TLabel").pack(
            anchor="w", pady=(0, 8)
        )
        self.analysis_app_tree = self._create_ranking_tree(
            app_card,
            ("application", "duration", "share"),
            ("Application", "Durée", "%"),
            (105, 65, 36),
        )

        tab_card = ttk.Frame(rankings, style="Card.TFrame", padding=(14, 12))
        tab_card.grid(row=0, column=2, sticky="nsew", padx=(10, 0))
        ttk.Label(tab_card, text="ONGLETS DE NAVIGATEUR LES PLUS UTILISÉS", style="CardTitle.TLabel").pack(
            anchor="w", pady=(0, 8)
        )
        self.analysis_tab_tree = self._create_ranking_tree(
            tab_card,
            ("title", "application", "duration"),
            ("Onglet", "Navigateur", "Durée"),
            (210, 85, 65),
        )

    def _create_ranking_tree(
        self,
        parent: ttk.Frame,
        columns: tuple[str, ...],
        headings: tuple[str, ...],
        widths: tuple[int, ...],
    ) -> ttk.Treeview:
        tree = ttk.Treeview(
            parent,
            columns=columns,
            show="headings",
            height=3,
            selectmode="browse",
        )
        for index, column in enumerate(columns):
            tree.heading(column, text=headings[index])
            is_last = index == len(columns) - 1
            tree.column(
                column,
                width=widths[index],
                minwidth=40,
                anchor="center" if is_last else "w",
                stretch=index == 0,
            )
        tree.pack(fill="both", expand=True)
        return tree

    def _metric_card(
        self,
        parent: ttk.Frame,
        column: int,
        label: str,
        value: tk.StringVar,
        padx: int = 0,
    ) -> None:
        card = ttk.Frame(parent, style="Card.TFrame", padding=(18, 16))
        card.grid(row=0, column=column, sticky="nsew", padx=(padx, 0))
        ttk.Label(card, text=label, style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(card, textvariable=value, style="Metric.TLabel").pack(
            anchor="w", pady=(7, 0)
        )

    def _set_status(self, status: str, detail: str, running: bool) -> None:
        self.status_text.set(status)
        self.status_detail.set(detail)
        if running:
            self.status_badge.configure(bg="#dcfce7", fg="#166534")
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            self.interval_box.configure(state="disabled")
            self.idle_box.configure(state="disabled")
        else:
            self.status_badge.configure(bg="#e2e8f0", fg="#475569")
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            self.interval_box.configure(state="readonly")
            self.idle_box.configure(state="readonly")

    def start_tracking(self) -> None:
        if self.tracker_thread and self.tracker_thread.is_alive():
            return
        try:
            poll_interval = float(self.poll_interval_text.get())
            idle_threshold = float(self.idle_threshold_text.get()) * 60
        except ValueError:
            messagebox.showwarning("Réglage invalide", "Vérifiez les options de suivi.")
            return
        self.running_poll_interval = poll_interval
        self.running_idle_threshold = idle_threshold
        self.stop_requested = False
        self.tracking_started_at = datetime.now().astimezone()
        self._set_status("Démarrage…", "Initialisation du suivi", running=True)
        self.tracker_thread = threading.Thread(
            target=self._tracking_worker,
            args=(poll_interval, idle_threshold),
            name="activity-tracker",
            daemon=True,
        )
        self.tracker_thread.start()

    def _tracking_worker(self, poll_interval: float, idle_threshold: float) -> None:
        try:
            provider = ObservableActivityProvider(WindowsActivityProvider(), self.messages)
            with ActivityDatabase(DATABASE_PATH) as database:
                tracker = ActivityTracker(
                    database=database,
                    provider=provider,
                    poll_interval=poll_interval,
                    idle_threshold=idle_threshold,
                )
                self.tracker = tracker
                if self.stop_requested:
                    tracker.stop()
                self.messages.put(("tracker_started", None))
                tracker.run()
        except Exception as exc:
            self.messages.put(("tracker_error", str(exc)))
        finally:
            self.tracker = None
            self.messages.put(("tracker_stopped", None))

    def stop_tracking(self) -> None:
        if not self.tracker_thread or not self.tracker_thread.is_alive():
            return
        self.stop_requested = True
        tracker = self.tracker
        if tracker is not None:
            tracker.stop()
        self.status_detail.set("Arrêt en cours…")
        self.stop_button.configure(state="disabled")

    def _process_messages(self) -> None:
        try:
            while True:
                kind, payload = self.messages.get_nowait()
                if kind == "tracker_started":
                    interval = f"{self.running_poll_interval:g}"
                    self._set_status(
                        "En cours",
                        f"Surveillance active · mesure toutes les {interval} seconde(s)",
                        running=True,
                    )
                elif kind == "tracker_stopped":
                    self._set_status("Arrêté", "Le suivi n'est pas en cours", running=False)
                    if self.closing:
                        self.root.destroy()
                        return
                    if self.pending_reset:
                        self.root.after(100, self._perform_reset)
                elif kind == "tracker_error":
                    self._set_status("Erreur", "Le suivi n'a pas pu démarrer", running=False)
                    if not self.closing:
                        messagebox.showerror("Local Time Tracker", str(payload))
                elif kind == "sample":
                    snapshot = payload
                    if isinstance(snapshot, ActivitySnapshot):
                        observed_at = datetime.now().astimezone()
                        self.last_measure_text.set(observed_at.strftime("%H:%M:%S"))
                        self.live_idle_text.set(f"{int(snapshot.idle_seconds)} s")
                        if snapshot.idle_seconds >= self.running_idle_threshold:
                            application = "Inactif"
                            window_title = "Aucune activité clavier/souris"
                        else:
                            application = snapshot.state.application
                            window_title = snapshot.state.window_title
                        signature = (application, window_title)
                        if signature != self.current_signature:
                            self.current_signature = signature
                            self.current_since = observed_at
                        self.application_text.set(application)
                        self.window_text.set(window_title)
                elif kind == "report_ready":
                    self.report_button.configure(state="normal")
                    try:
                        os.startfile(str(payload))
                    except OSError as exc:
                        messagebox.showerror("Ouverture impossible", str(exc))
                elif kind == "report_error":
                    self.report_button.configure(state="normal")
                    messagebox.showerror("Rapport impossible", str(payload))
        except queue.Empty:
            pass
        if not self.closing:
            self.root.after(150, self._process_messages)

    def _update_live_durations(self) -> None:
        now = datetime.now().astimezone()
        if self.current_since is not None:
            self.current_duration_text.set(
                format_clock((now - self.current_since).total_seconds())
            )
        if (
            self.tracking_started_at is not None
            and self.tracker_thread is not None
            and self.tracker_thread.is_alive()
        ):
            self.tracking_duration_text.set(
                format_clock((now - self.tracking_started_at).total_seconds())
            )
        if not self.closing:
            self.root.after(1000, self._update_live_durations)

    def _refresh_summary(self) -> None:
        try:
            if DATABASE_PATH.exists():
                range_start = local_midnight(date.today())
                range_end = local_midnight(date.today() + timedelta(days=1))
                with ActivityDatabase(DATABASE_PATH) as database:
                    periods = database.periods_between(range_start, range_end)
                    recent_periods = database.recent_periods(limit=15)
                active_seconds = 0.0
                idle_seconds = 0.0
                applications: set[str] = set()
                for period in periods:
                    start = max(period.started_at, range_start.astimezone(period.started_at.tzinfo))
                    end = min(period.ended_at, range_end.astimezone(period.ended_at.tzinfo))
                    seconds = max(0.0, (end - start).total_seconds())
                    if period.is_idle:
                        idle_seconds += seconds
                    else:
                        active_seconds += seconds
                        applications.add(period.application)
                self.active_text.set(format_duration(active_seconds))
                self.idle_text.set(format_duration(idle_seconds))
                self.app_count_text.set(str(len(applications)))
                self.period_count_text.set(str(len(periods)))
                self._show_recent_periods(recent_periods)
        except (OSError, sqlite3.Error):
            pass
        if not self.closing:
            self.root.after(2000, self._refresh_summary)

    def _refresh_analysis(self, schedule: bool = True) -> None:
        try:
            end_day = date.today()
            start_day = (
                end_day - timedelta(days=6)
                if self.analysis_range.get() == "week"
                else end_day
            )
            self.analysis_period_text.set(
                end_day.strftime("Aujourd'hui · %d/%m/%Y")
                if start_day == end_day
                else f"Du {start_day:%d/%m} au {end_day:%d/%m/%Y}"
            )
            categorizer = load_categorizer(self._configuration_path())
            range_start = local_midnight(start_day)
            range_end = local_midnight(end_day + timedelta(days=1))
            with ActivityDatabase(DATABASE_PATH) as database:
                periods = collect_periods(
                    database,
                    categorizer,
                    range_start,
                    range_end,
                )
            analytics = analyze_usage(periods, start_day, end_day)
            self.analysis_data = analytics
            self.analysis_total_text.set(format_duration(analytics.active_seconds))
            self.analysis_average_text.set(format_duration(analytics.average_daily_seconds))
            self.analysis_longest_text.set(
                format_duration(analytics.longest_session_seconds)
            )
            self._populate_analysis_rankings(analytics)
            self._draw_usage_chart()
        except (CategoryConfigError, OSError, sqlite3.Error, ValueError):
            self.analysis_data = None
        if schedule and not self.closing:
            self.root.after(5000, self._refresh_analysis)

    def _replace_tree_rows(
        self,
        tree: ttk.Treeview,
        rows: list[tuple[tuple[object, ...], str | None]],
        empty_message: str,
    ) -> None:
        for item in tree.get_children():
            tree.delete(item)
        if not rows:
            tree.insert("", "end", values=(empty_message, "", ""))
            return
        for values, tag in rows:
            tree.insert("", "end", values=values, tags=(tag,) if tag else ())

    def _populate_analysis_rankings(self, analytics: UsageAnalytics) -> None:
        total = analytics.active_seconds
        category_rows: list[tuple[tuple[object, ...], str | None]] = []
        for index, (name, color, seconds) in enumerate(analytics.categories[:8]):
            tag = f"category-{index}"
            self.category_tree.tag_configure(tag, foreground=color)
            category_rows.append(
                (
                    (
                        name,
                        format_duration(seconds),
                        f"{100 * seconds / total:.0f} %" if total else "0 %",
                    ),
                    tag,
                )
            )
        self._replace_tree_rows(
            self.category_tree,
            category_rows,
            "Aucune activité",
        )

        app_rows = [
            (
                (
                    application,
                    format_duration(seconds),
                    f"{100 * seconds / total:.0f} %" if total else "0 %",
                ),
                None,
            )
            for application, seconds in analytics.applications[:10]
        ]
        self._replace_tree_rows(
            self.analysis_app_tree,
            app_rows,
            "Aucune application",
        )

        tab_rows = [
            ((title, application, format_duration(seconds)), None)
            for application, title, seconds in analytics.browser_tabs[:12]
        ]
        self._replace_tree_rows(
            self.analysis_tab_tree,
            tab_rows,
            "Aucun onglet détecté",
        )

    def _draw_usage_chart(self) -> None:
        if not hasattr(self, "usage_canvas"):
            return
        canvas = self.usage_canvas
        canvas.delete("all")
        analytics = self.analysis_data
        if analytics is None or not analytics.buckets:
            canvas.create_text(
                12,
                80,
                anchor="w",
                text="Aucune activité sur cette période",
                fill="#94a3b8",
                font=("Segoe UI", 10),
            )
            return

        width = max(500, canvas.winfo_width())
        height = max(150, canvas.winfo_height())
        left, right, top, bottom = 48, 10, 12, 26
        chart_width = width - left - right
        chart_height = height - top - bottom
        maximum = max((bucket.total_seconds for bucket in analytics.buckets), default=0)
        maximum = max(maximum, 1)

        for index in range(5):
            ratio = index / 4
            y = top + chart_height * ratio
            canvas.create_line(left, y, width - right, y, fill="#e2e8f0")
        canvas.create_text(
            left - 6,
            top,
            anchor="e",
            text=format_duration(maximum),
            fill="#94a3b8",
            font=("Segoe UI", 8),
        )
        canvas.create_text(
            left - 6,
            top + chart_height,
            anchor="e",
            text="0",
            fill="#94a3b8",
            font=("Segoe UI", 8),
        )

        count = len(analytics.buckets)
        slot_width = chart_width / count
        bar_width = max(3, min(34, slot_width * 0.62))
        category_order = [
            (name, color) for name, color, _seconds in analytics.categories
        ]
        for index, bucket in enumerate(analytics.buckets):
            x1 = left + index * slot_width + (slot_width - bar_width) / 2
            x2 = x1 + bar_width
            current_bottom = top + chart_height
            bucket_values = {
                (name, color): seconds
                for name, color, seconds in bucket.categories
            }
            for name, color in category_order:
                seconds = bucket_values.get((name, color), 0)
                segment_height = chart_height * seconds / maximum
                if segment_height <= 0:
                    continue
                y1 = current_bottom - segment_height
                canvas.create_rectangle(
                    x1,
                    y1,
                    x2,
                    current_bottom,
                    fill=color,
                    outline="",
                )
                current_bottom = y1

            show_label = count <= 7 or index in {0, 6, 12, 18, count - 1}
            if show_label:
                canvas.create_text(
                    (x1 + x2) / 2,
                    height - 10,
                    text=bucket.label,
                    fill="#64748b",
                    font=("Segoe UI", 8),
                )

    def _show_recent_periods(self, periods: list[ActivityPeriod]) -> None:
        for item in self.recent_tree.get_children():
            self.recent_tree.delete(item)
        for period in periods:
            self.recent_tree.insert(
                "",
                "end",
                values=(
                    period.started_at.astimezone().strftime("%H:%M:%S"),
                    period.application,
                    period.window_title,
                    format_clock(period.duration_seconds),
                    "Inactif" if period.is_idle else "Actif",
                ),
            )

    def reset_activity(self) -> None:
        confirmed = messagebox.askyesno(
            "Réinitialiser l'historique",
            "Toutes les périodes enregistrées seront définitivement supprimées.\n\n"
            "Les rapports HTML déjà générés seront conservés. Continuer ?",
            icon="warning",
        )
        if not confirmed:
            return
        self.pending_reset = True
        self.restart_after_reset = bool(
            self.tracker_thread and self.tracker_thread.is_alive()
        )
        self.reset_button.configure(state="disabled")
        self.reset_data_button.configure(state="disabled")
        if self.restart_after_reset:
            self.status_detail.set("Arrêt du suivi avant réinitialisation…")
            self.stop_tracking()
        else:
            self._perform_reset()

    def _perform_reset(self) -> None:
        try:
            with ActivityDatabase(DATABASE_PATH) as database:
                database.clear_periods()
        except (OSError, sqlite3.Error) as exc:
            self.pending_reset = False
            self.restart_after_reset = False
            self.reset_button.configure(state="normal")
            self.reset_data_button.configure(state="normal")
            messagebox.showerror("Réinitialisation impossible", str(exc))
            return

        restart = self.restart_after_reset
        self.pending_reset = False
        self.restart_after_reset = False
        self.current_signature = None
        self.current_since = None
        self.tracking_started_at = None
        self.application_text.set("—")
        self.window_text.set("Aucune fenêtre observée")
        self.current_duration_text.set("00:00:00")
        self.tracking_duration_text.set("00:00:00")
        self.last_measure_text.set("—")
        self.live_idle_text.set("0 s")
        self.active_text.set("0 min")
        self.idle_text.set("0 min")
        self.app_count_text.set("0")
        self.period_count_text.set("0")
        self._show_recent_periods([])
        self.analysis_data = None
        self.analysis_total_text.set("0 min")
        self.analysis_average_text.set("0 min")
        self.analysis_longest_text.set("0 min")
        self._replace_tree_rows(self.category_tree, [], "Aucune activité")
        self._replace_tree_rows(self.analysis_app_tree, [], "Aucune application")
        self._replace_tree_rows(self.analysis_tab_tree, [], "Aucun onglet détecté")
        self._draw_usage_chart()
        self.reset_button.configure(state="normal")
        self.reset_data_button.configure(state="normal")
        messagebox.showinfo("Historique réinitialisé", "Toutes les activités ont été effacées.")
        if restart and not self.closing:
            self.root.after(250, self.start_tracking)

    def _configuration_path(self) -> Path:
        personal = APP_DIRECTORY / "config.json"
        if personal.exists():
            return personal
        local_example = APP_DIRECTORY / "config.example.json"
        if local_example.exists():
            return local_example
        return bundled_resource("config.example.json")

    def generate_selected_report(self) -> None:
        try:
            selected_day = date.fromisoformat(self.report_date.get().strip())
        except ValueError:
            messagebox.showwarning("Date invalide", "Utilisez le format AAAA-MM-JJ.")
            return
        self.report_button.configure(state="disabled")
        threading.Thread(
            target=self._report_worker,
            args=(selected_day,),
            name="report-generator",
            daemon=True,
        ).start()

    def _report_worker(self, selected_day: date) -> None:
        try:
            categorizer = load_categorizer(self._configuration_path())
            output = REPORTS_DIRECTORY / f"report-{selected_day.isoformat()}.html"
            result = generate_report(
                database_path=DATABASE_PATH,
                output_path=output,
                start_day=selected_day,
                end_day=selected_day,
                categorizer=categorizer,
            )
            self.messages.put(("report_ready", result))
        except (CategoryConfigError, OSError, sqlite3.Error, ValueError) as exc:
            self.messages.put(("report_error", str(exc)))

    def open_reports_directory(self) -> None:
        REPORTS_DIRECTORY.mkdir(parents=True, exist_ok=True)
        try:
            os.startfile(str(REPORTS_DIRECTORY))
        except OSError as exc:
            messagebox.showerror("Ouverture impossible", str(exc))

    def close(self) -> None:
        self.closing = True
        self.stop_tracking()
        if not self.tracker_thread or not self.tracker_thread.is_alive():
            self.root.destroy()


def main() -> int:
    if sys.platform != "win32":
        print("Cette application graphique est disponible uniquement sous Windows.")
        return 1
    root = tk.Tk()
    TimeTrackerApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
