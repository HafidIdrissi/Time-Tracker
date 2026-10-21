# Windows validation

The **Windows validation** Actions workflow runs alongside the existing Python
unit-test matrix. It creates no personal activity fixture and uploads only
installer, portable ZIP and checksum artifacts.

## Native desktop checks

Run on Windows from the repository root in a fresh Python process:

```powershell
.\.venv\Scripts\python.exe tests/windows_desktop_smoke.py
```

This process creates real Tk windows and native ttk controls. It uses a
temporary SQLite database, a fictional activity provider and the application's
real tracking and report threads. Checks cover:

- automatic tracking, title changes, live duration, stop and restart;
- Today, Last 7 days and Previous 7 days analysis;
- invalid local configuration, cleared error metrics and recovery;
- saved settings, failed preference writes and loading settings in a new app;
- Ctrl+Tab, Ctrl+Shift+Tab, Alt+D/U/R, Tab and Shift+Tab;
- Tab navigation to **Copy report path** and keyboard activation with the exact
  generated path sent to a mocked clipboard;
- Treeview selection, focus, visibility, top position and deleted rows;
- CSV/JSON round trips, cancellation and blocked destinations;
- SQLite backup while tracking, overwrite decisions and source protection;
- reports-directory failures, offline HTML generation and disposable Reset.

File-picker choices, message-box responses and shell opening are injected at
their boundaries. This suite does not attest to a human inspecting those
dialogs or to live foreground-window sampling on a personal Windows desktop.
The existing Win32 provider and storage tests remain part of the unit matrix.

## Release checks

Create the README's `.venv` and install PyInstaller and Inno Setup, then run:

```powershell
.\tests\windows_release_smoke.ps1
```

The script uses the system temporary directory when Actions' RUNNER_TEMP is
absent. CI explicitly unsets that variable to exercise the documented local
command.

The script rejects a mismatched version from both the checkout and an outside
directory with spaces. It then builds the actual installer and portable ZIP
from both locations and verifies caller-directory restoration, required ZIP
contents, executable version metadata, equality with the final application
executable, absence of user data and both SHA-256 entries.

The release builder stages the portable executable after application signing.
CI without signing credentials validates unsigned packages; it does not verify
a certificate or perform an interactive installer/uninstaller walkthrough.
