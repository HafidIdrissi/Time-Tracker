# Local Time Tracker

Local Time Tracker is a free, open-source Windows application that records how
much time you spend in applications and browser tabs. It runs locally, stores
its data in SQLite, and does not require an account or send your activity to a
remote server.

The project is published by **H.I. SOLUTIONS** and licensed under the MIT
License.

## Highlights

- native Windows desktop interface;
- live foreground application and window title;
- Start, Stop, and Reset controls;
- configurable sampling interval and idle threshold;
- active and idle time summaries;
- analysis for today or the last seven days;
- usage chart by hour or day;
- rankings by category, application, and browser tab;
- standalone HTML reports that work offline;
- local SQLite storage with no telemetry or advertising;
- distributable Windows installer and automatic GitHub releases.

## What the tracker measures

The tracker samples the Windows foreground window at a configurable interval.
For every sample, it records:

- the foreground process name, such as `Code.exe`, `chrome.exe`, or
  `TslGame.exe`;
- the foreground window title, which may contain a browser tab title;
- the start and end time of the continuous period;
- whether Windows reported keyboard and mouse inactivity.

A new period begins when the foreground application, window title, or idle state
changes. Consecutive samples for the same window extend the current period.

### Multiple monitors and games

Windows has one foreground window for the whole desktop, not one foreground
window per monitor. Local Time Tracker therefore follows keyboard focus rather
than the monitor containing the mouse pointer.

For example, if PUBG is open on the second monitor:

- PUBG is recorded while `TslGame.exe` remains the foreground window;
- moving the pointer to the first monitor does not necessarily change the
  foreground window;
- clicking Visual Studio Code, Chrome, Search, or Quick Settings makes that
  window the foreground application and starts a new period;
- returning focus to PUBG starts or resumes a PUBG period;
- after the configured idle threshold, time is recorded as `Idle` even if PUBG
  is still visible.

This explains why a detailed timeline can alternate between PUBG, Code, Chrome,
Search, and Windows system panels. The tracker reports foreground focus; it does
not claim that the user was continuously reading or interacting with the
content.

## Desktop interface

The app starts tracking automatically and provides three views.

### Dashboard

- current application and window title;
- duration of the current foreground window;
- keyboard and mouse idle time;
- time of the latest sample;
- active time, idle time, application count, and period count for today;
- recent activity timeline with exact durations and states.

### Usage analysis

- Today or Last 7 days selection;
- total active screen time and daily average;
- longest continuous active session;
- hourly or daily stacked usage chart;
- most used categories;
- most used applications;
- most used tabs from Chrome, Edge, Firefox, Brave, Opera, and Vivaldi.

Browser titles such as `Gmail - Google Chrome` are normalized to `Gmail`, so
separate visits to the same tab are added together.

### Reports and data

- generate an offline HTML report for a selected date;
- open the local reports folder;
- reset all recorded activity from the interface.

Reset deletes periods from the SQLite database. Previously generated HTML
reports are intentionally kept. The official uninstaller removes the local app
data directory.

## Install the released Windows application

1. Open the repository's
   [Releases](https://github.com/HafidIdrissi/Time-Tracker/releases) page.
2. Download `LocalTimeTracker-Setup-1.1.0-x64.exe` and `SHA256SUMS.txt`.
3. Optionally verify the SHA-256 checksum.
4. Run the installer and launch **Local Time Tracker** from the Start menu.

The current installer can be unsigned. Windows SmartScreen may therefore show a
warning until H.I. SOLUTIONS signs releases with a trusted Authenticode
certificate. See [SIGNING.md](SIGNING.md) for the distribution requirements.

## Run from source

### Requirements

- Windows 10 or Windows 11, 64-bit;
- Python 3.11 or later;
- Git, if cloning the repository.

Clone and prepare the environment in PowerShell:

```powershell
git clone https://github.com/HafidIdrissi/Time-Tracker.git
cd Time-Tracker
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Launch the desktop interface:

```powershell
python windows_app.py
```

You can also double-click `Launch Time Tracker.cmd` after creating `.venv`.
Do not run the source version and the installed version at the same time, because
two trackers would record overlapping periods.

## Test the application

Run the automated test suite:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
```

Then perform this short interface test:

1. start `windows_app.py`;
2. confirm the status changes to **Running**;
3. switch between Code, Chrome, File Explorer, and another application;
4. verify the live application and title update after each switch;
5. open **Usage analysis** and confirm applications and browser tabs appear;
6. click **Stop**, wait for **Stopped**, then click **Start tracking**;
7. generate today's HTML report and open it;
8. test **Reset** only with disposable data, because it permanently deletes the
   activity history.

To test the installer, build it, install it for the current Windows user, launch
it from the Start menu, and verify that uninstalling it removes the program.
Back up `%LOCALAPPDATA%\LocalTimeTracker\data\activity.db` first if it contains
activity you want to keep.

## Command-line tracker

The graphical app is recommended. A terminal-only tracker is also available:

```powershell
python track.py
```

Custom settings:

```powershell
python track.py --interval 2 --idle-after 300 --database data/activity.db
```

Stop it with `Ctrl+C`.

## Generate reports from the command line

Today's report:

```powershell
python report.py
```

A specific day:

```powershell
python report.py --date 2026-07-20
```

An inclusive date range:

```powershell
python report.py --from 2026-07-14 --to 2026-07-20
```

Reports contain active and idle totals, category totals, a timeline overview,
application shares, full window titles, and a detailed list of every period.
They contain no external scripts, fonts, trackers, or network dependencies.

## Categories

Activity is categorized with case-insensitive keywords from `config.json`. If
that file does not exist, the app uses `config.example.json`.

```json
{
  "default_category": "Other",
  "default_color": "#64748b",
  "categories": [
    {
      "name": "Work",
      "color": "#4f46e5",
      "keywords": ["code.exe", "github", "gmail"]
    },
    {
      "name": "Games",
      "color": "#ec4899",
      "keywords": ["steam.exe", "tslgame.exe", "pubg"]
    }
  ]
}
```

The first matching category wins, so put specific rules before broad rules.
Changes are reflected the next time analysis or a report loads the configuration.

## Local data and privacy

When installed, files are stored under:

```text
%LOCALAPPDATA%\LocalTimeTracker\
├── data\activity.db
└── reports\
```

When run directly from the repository, the equivalent folders are located in
the project directory.

Window and browser-tab titles can contain sensitive information such as document
names, searches, email subjects, account names, or private website titles. Do
not publish `activity.db` or personal HTML reports. The database is not encrypted
by the app; access is protected by the user's Windows account and disk settings.

See [PRIVACY.md](PRIVACY.md) for the complete policy.

## Build the Windows executable

From PowerShell:

```powershell
.\build_windows.ps1
```

This creates:

```text
dist\LocalTimeTracker\LocalTimeTracker.exe
```

Keep the entire `dist\LocalTimeTracker` folder together; the `.exe` depends on
the packaged files beside it.

## Build the Windows installer

Install [Inno Setup 6](https://jrsoftware.org/isinfo.php), or use:

```powershell
winget install JRSoftware.InnoSetup
```

Then build and test release version 1.1.0:

```powershell
.\build_release.ps1 -Version 1.1.0
```

The script runs the tests, builds the application, creates the installer, and
writes its SHA-256 checksum:

```text
release\LocalTimeTracker-Setup-1.1.0-x64.exe
release\SHA256SUMS.txt
```

Optional Authenticode signing is supported through
`TIME_TRACKER_SIGNTOOL` and `TIME_TRACKER_CERT_SHA1`. Both variables must be set
together.

## Publish a GitHub release

Commit and push the source changes before creating the version tag:

```powershell
git add .
git commit -m "Release Local Time Tracker 1.1.0 in English"
git push origin main
git tag -a v1.1.0 -m "Local Time Tracker 1.1.0"
git push origin v1.1.0
```

The tag starts `.github/workflows/release.yml`. GitHub Actions runs the tests,
builds the installer, and creates the GitHub release. If the release already
exists for that tag, the workflow safely replaces the installer and checksum
assets instead of failing with `a release with the same tag name already exists`.

Never reuse or move a published version tag. If a released version changes,
increment the version, commit it, and create a new tag.

## Contributing

Contributions are welcome. Contributors should:

1. fork the repository;
2. create a branch such as `feature/browser-analysis`;
3. make focused changes and add or update tests;
4. run `python -m unittest discover -v`;
5. push the branch and open a pull request.

Recommended protection for the `main` branch:

- require a pull request before merging;
- require conversation resolution;
- require status checks once the test workflow appears in GitHub;
- block force pushes and branch deletion;
- keep one approval optional for a solo maintainer, because the author cannot
  approve their own pull request.

Do not enable **Lock branch**, because it makes the branch read-only.

## Project structure

```text
.
├── windows_app.py                 # Windows desktop interface
├── Launch Time Tracker.cmd        # double-click source launcher
├── track.py                       # command-line tracking
├── report.py                      # command-line report generation
├── timetracker\
│   ├── windows.py                 # foreground window and idle sampling
│   ├── tracker.py                 # continuous periods and transitions
│   ├── database.py                # SQLite persistence
│   ├── categories.py              # keyword categorization
│   ├── analytics.py               # usage and browser-tab statistics
│   └── reporting.py               # standalone HTML reports
├── packaging\installer.iss       # Inno Setup definition
├── build_windows.ps1              # PyInstaller build
├── build_release.ps1              # tested installer build
└── tests\                         # automated tests
```

## Known limitations

- foreground focus is measured, not the position of the mouse pointer;
- an activity shorter than the sampling interval may not be observed;
- some elevated windows may hide their title from a non-elevated application;
- browser-tab reporting depends on the title format provided by the browser;
- the application currently supports Windows only.

## License

This project uses the [MIT License](LICENSE). It permits personal and commercial
use, modification, distribution, and sublicensing as long as the copyright and
license notice are preserved. It provides the software without warranty.

MIT is a suitable license for a permissive open-source project. It does not
require contributors or distributors to publish their modifications. If that
requirement is desired, a copyleft license such as GPL would be more appropriate.

## Publisher

**H.I. SOLUTIONS**<br>
IDRISSI HAFID — Sole proprietor<br>
67 rue Charles de Gaulle, 78350 Jouy-en-Josas, France<br>
SIREN: 981 951 080 · SIRET: 981 951 080 00028<br>
VAT: FR15981951080 · APE/NAF: 62.02A<br>
Registered with the RNE · Not registered with the RCS

Legal details are available in [LEGAL.md](LEGAL.md).
