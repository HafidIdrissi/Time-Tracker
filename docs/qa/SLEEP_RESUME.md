# Windows sleep/resume QA protocol

This protocol exercises the live Windows tracker across one real system sleep
and resume. It uses a fresh SQLite database under the Windows temporary
directory, fictional Notepad document titles, and a local HTML report. It does
not change power settings, access a personal database, or upload data.

This is a manual native test, not a fake-clock or CI test. Record what actually
happens; in particular, do not mark the test as passed merely because tracking
resumes. A long activity interval spanning sleep may include unobserved time.

## Preparation

Use a Windows 10 or Windows 11 machine where sleep is already available under
its existing power policy. Do not alter that policy for this test. Save work,
ensure you can resume the machine using its normal method, and do not start if
sleep would risk losing unsaved work or interrupting critical services.

From the repository root, record the checkout revision and runtime:

```powershell
git rev-parse HEAD
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -c "import platform, sys; print(platform.platform()); print('64-bit' if sys.maxsize > 2**32 else '32-bit')"
.\.venv\Scripts\python.exe .\track.py --version
.\.venv\Scripts\python.exe .\report.py --version
```

This procedure covers the source tracker. Packaged-app behavior is outside
this protocol and must be reported as untested unless validated separately
with a portable copy and disposable storage.

Create a new, unique working directory and database. Do not reuse a previous
test directory:

```powershell
$qaRoot = Join-Path $env:TEMP ("time-tracker-sleep-qa-" + (Get-Date -Format "yyyyMMdd-HHmmss"))
New-Item -ItemType Directory -Path $qaRoot
$database = Join-Path $qaRoot "activity.db"
$report = Join-Path $qaRoot "report.html"
```

Keep the repository's example category configuration in use by passing it
explicitly when generating the report. The generated report and database stay
under `$qaRoot`; do not attach either to an issue or pull request.

## Run one trial

1. Record the test date and local time zone. Open two disposable Notepad
   documents whose visible titles are fictional, for example
   `Fictional Sleep QA - Before.txt` and `Fictional Sleep QA - After.txt`.
   Do not use real document names or private window titles.
2. In a PowerShell window at the repository root, start the source tracker
   against the fresh database with a five-second sampling interval and a
   60-second idle threshold:

   ```powershell
   .\.venv\Scripts\python.exe .\track.py --database $database --interval 5 --idle-after 60
   ```

   Retain the console window. Confirm the startup line reports those settings
   and that the tracker process remains running. Record the displayed startup
   time and process status.
3. Bring the fictional `Before` Notepad document to the foreground and interact
   with it for at least 15 seconds. Record the local time. Avoid using the
   tracker console as the foreground application during the observation.
4. Put Windows to sleep using the normal user-facing Sleep action (for example,
   Start > Power > Sleep). Record the time immediately before selecting Sleep.
   Resume using the machine's normal wake method and record the time the
   desktop becomes usable. Do not run a sleep command, simulate a gap, or
   change power policy.
5. After resume, note whether the tracker process and console are still
   present. The tracker does not log each successful sample, so do not claim
   that a sample occurred based only on the console being present or on the
   five-second polling setting. Bring the fictional `After` Notepad document
   to the foreground and interact with it for at least 15 seconds. After
   stopping the tracker, use the database timestamps and titles to establish
   whether and when the resumed sample was recorded.
6. Stop the tracker with Ctrl+C in its console. Confirm that it exits normally
   and logs `Tracker stopped`.
7. Inspect only the disposable database. This query prints recorded titles,
   UTC timestamps, durations, and idle flags:

   ```powershell
   .\.venv\Scripts\python.exe -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); rows=c.execute('SELECT application, window_title, started_at, ended_at, round(duration_seconds, 1), is_idle FROM activity_periods ORDER BY started_at, id'); [print(*row, sep=' | ') for row in rows]; c.close()" $database
   ```

   Confirm whether the before- and after-sleep titles were recorded and identify
   the corresponding UTC timestamps. Convert them to the machine's local time
   zone before comparing with the manually recorded sleep and resume times.
   Check whether a period spans the sleep interval and distinguish idle from
   active periods. Estimate the interval's overlap with the manually observed
   sleep-to-desktop-usable window, and report that estimate as approximate
   because the actual suspend and first post-resume sample boundaries may
   differ from the manual times. If overcount cannot be determined from the
   observations, say so; do not label unobserved time as active work.
8. Generate and open the local report covering the trial dates. If sleep and
   resume cross local midnight, include both dates:

   ```powershell
   $trialStartDate = "YYYY-MM-DD"
   $trialEndDate = "YYYY-MM-DD"
   .\.venv\Scripts\python.exe .\report.py --database $database --config .\config.example.json --from $trialStartDate --to $trialEndDate --output $report
   ```

   Inspect the report's timeline, application/title rows, active and idle
   totals, and any interval spanning sleep. The report can contain window
   titles: keep it local and do not publish or attach it.
9. Verify normal restart behavior using the same disposable database. Start
   the same tracker command again, leave it running for at least 15 seconds
   with the fictional `After` document foreground, then stop with Ctrl+C.
   Confirm it logs `Tracker stopped` and exits normally. Run the database query
   again and verify a new period was recorded after the restart; the tracker
   does not print a success message for each sample.
10. Once the observations are recorded and the report is no longer needed,
    remove only the uniquely named `$qaRoot` test directory if desired. Never
    clean up a broader temporary or repository directory.

## Evidence record

**Status: not performed in this contribution session.** No real Windows
suspend/resume was initiated or observed here, so there are no measured sleep
or resume times, sample observations, interval results, report results, or
normal restart result to claim. This protocol is not evidence that the native
trial passed. Complete this record from an actual trial before reporting the
issue's requested Windows QA as done.

### Environment and checks in this contribution session

These are documentation/tooling checks, not a native tracking or sleep/resume
trial:

| Field | Observed result |
|---|---|
| Checkout revision for current documentation review | `cfc08f432ea3f0ed630898e62e2c234b98d39fd0` |
| OS | Windows 11, platform build `10.0.26200` |
| Python | 3.14.2, 64-bit |
| Source CLI version commands | `track.py --version` and `report.py --version` both returned `1.3.0` |
| CLI options | `track.py --help` and `report.py --help` displayed the documented options |
| Report command check | Generated an HTML report from an empty disposable database using `config.example.json`; temporary database and report were removed |
| Documentation diff check | `git diff --check` passed |
| Native trial / tracker sampling / restart | Not performed |

Record only sanitized steps and numeric observations. Do not include raw
database rows, HTML reports, screenshots, real window titles, user names, or
local paths in a public contribution.

| Field | Actual observation |
|---|---|
| Trial date and time zone | Not recorded — trial not performed |
| App revision (`git rev-parse HEAD`) and source/package mode | Record during native trial; session revision above is documentation-only |
| Windows version/build | Record during native trial; session OS above is documentation-only |
| Python version/architecture or packaged-app version | Record during native trial; session runtime above is documentation-only |
| Poll interval and idle threshold | 5 seconds and 60 seconds are the protocol settings; not exercised |
| Sleep method | Not recorded — trial not performed |
| Sleep initiated / desktop usable after resume | Not recorded — trial not performed |
| Tracker status before sleep / after resume | Not recorded — trial not performed |
| Before/after fictional samples observed | Not recorded — trial not performed |
| Recorded interval across the gap and measured overcount | Not recorded — trial not performed |
| Local report inspection | Not recorded — trial not performed |
| Normal stop and restart | Not recorded — trial not performed |
| Unavailable or untested modes | Real suspend/resume, live sampling, packaged-app mode, and trial report behavior are untested |

Any fix for unobserved-gap accounting belongs in
[issue #138](https://github.com/HafidIdrissi/Time-Tracker/issues/138), not in
this QA-only contribution. This protocol does not cover lock/unlock or virtual
desktop switching.
