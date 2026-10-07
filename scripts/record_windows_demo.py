"""Record only the native app window with disposable, fictional activity."""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from windows_desktop_smoke import NativeDesktopTests
import windows_app
from timetracker.database import ActivityDatabase
from timetracker.models import ActivityState


def cleanup_recorder(
    process: subprocess.Popen | None,
    fixture: Any,
    *,
    primary_error: BaseException | None = None,
) -> None:
    """Clean up the recording subprocess and ensure fixture cleanup runs unconditionally.

    If an unresponsive child ignores terminate(), falls back to kill().
    If terminate() or kill() fails:
      - If primary_error is set (recording already failed), reports the secondary cleanup
        failure to stderr and retains primary_error as the primary diagnostic.
      - If primary_error is None, propagates the cleanup failure.
    fixture.doCleanups() runs in all execution paths.
    """
    cleanup_error: BaseException | None = None
    try:
        if process is not None and process.poll() is None:
            try:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    print(
                        "Recording process did not exit after terminate; killing.",
                        file=sys.stderr,
                    )
                    process.kill()
                    process.wait(timeout=5)
            except BaseException as exc:
                cleanup_error = exc
    finally:
        fixture.doCleanups()

    if cleanup_error is not None:
        if primary_error is not None:
            print(
                f"Secondary cleanup failure after recording error: {cleanup_error}",
                file=sys.stderr,
            )
        else:
            raise cleanup_error


def record(output: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("Install FFmpeg to record the Windows demo.")
    output.mkdir(parents=True, exist_ok=True)
    fixture = NativeDesktopTests("test_tracker_titles_analysis_reports_stop_restart_and_reset")
    process = None
    primary_error: BaseException | None = None
    try:
        fixture.setUp()
        app, root = fixture.app, fixture.root
        midnight = windows_app.local_midnight(date.today())
        with ActivityDatabase(fixture.database) as database:
            database.clear_periods()
            for hour, minutes, application, title in (
                (9, 45, "Code.exe", "Fictional project — editing a feature"),
                (10, 20, "msedge.exe", "GitHub — fictional pull request - Microsoft Edge"),
                (11, 30, "Code.exe", "Fictional project — running tests"),
                (13, 15, "msedge.exe", "YouTube — invented tutorial - Microsoft Edge"),
                (14, 35, "Code.exe", "Fictional project — reviewing a patch"),
            ):
                start = midnight + timedelta(hours=hour)
                identifier = database.create_period(ActivityState(application, title), start)
                database.update_period(identifier, start, start + timedelta(minutes=minutes))
        app._refresh_summary()
        app._refresh_analysis(schedule=False)
        app.start_tracking()
        fixture.wait(lambda: app.status_text.get() == "Running")
        root.lift()
        root.focus_force()
        root.update()
        path = output / "LocalTimeTracker-demo.mp4"
        with (output / "recording.log").open("w", encoding="utf-8") as log:
            process = subprocess.Popen(
                [
                    ffmpeg, "-y", "-f", "gdigrab", "-draw_mouse", "0",
                    "-framerate", "15", "-i", f"title={root.title()}",
                    "-t", "45", "-an", "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
                    "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(path),
                ],
                stdin=subprocess.DEVNULL, stdout=log, stderr=log,
            )
            transitions = [
                (4, lambda: setattr(fixture.provider, "title", "Fictional project — updated title")),
                (10, lambda: app.notebook.select(1)),
                (18, lambda: (app.analysis_range.set("previous-week"), app._refresh_analysis(False))),
                (22, lambda: (app.analysis_range.set("today"), app._refresh_analysis(False))),
                (26, lambda: (app.notebook.select(2), app.generate_selected_report())),
                (34, app.stop_tracking),
                (38, lambda: (app.start_tracking(), app.notebook.select(0))),
            ]
            started = time.monotonic()
            while process.poll() is None:
                root.update()
                if fixture.callbacks:
                    raise RuntimeError(f"Tk errors: {fixture.callbacks}")
                elapsed = time.monotonic() - started
                while transitions and elapsed >= transitions[0][0]:
                    transitions.pop(0)[1]()
                if elapsed > 70:
                    raise RuntimeError("Recording exceeded its expected duration.")
                time.sleep(0.02)
            if process.returncode:
                raise RuntimeError("FFmpeg failed; inspect recording.log.")
        if path.stat().st_size < 10000:
            raise RuntimeError("Demo video is empty.")
        probe = shutil.which("ffprobe")
        if not probe:
            raise RuntimeError("FFprobe is required to validate the recording.")
        duration = float(subprocess.check_output(
            [probe, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            text=True,
        ).strip())
        if not 44 <= duration <= 47:
            raise RuntimeError(f"Unexpected demo duration: {duration}")
        (output / "LocalTimeTracker-demo.txt").write_text(
            "45-second native Windows recording, using only fictional activity.\n"
            "0-10s: tracking and updated window title.\n"
            "10-26s: current and previous-week usage analysis.\n"
            "26-34s: real offline HTML generation; shell opening is injected.\n"
            "34-45s: stop, restart and dashboard.\n"
            "No personal activity, account, API key or external service is used.\n",
            encoding="utf-8",
        )
        print(f"Validated fictional native demo: {duration:.2f}s, {path.stat().st_size} bytes")
    except BaseException as exc:
        primary_error = exc
        raise
    finally:
        cleanup_recorder(process, fixture, primary_error=primary_error)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("demo"))
    record(parser.parse_args().output.resolve())
