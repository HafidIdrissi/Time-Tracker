# First run on Windows

This walkthrough takes about five minutes with the current Windows installer.
The examples below are synthetic. Local Time Tracker does not upload activity,
and the installer is not described as signed here.

## 1. Download

Open the [latest release](https://github.com/HafidIdrissi/Time-Tracker/releases/latest)
and download `LocalTimeTracker-Setup-<version>-x64.exe` together with
`SHA256SUMS.txt`.

Optional checksum check in PowerShell, from the folder that contains both files:

```powershell
Get-FileHash -Algorithm SHA256 "LocalTimeTracker-Setup-<version>-x64.exe"
```

Compare the hash with the matching line in `SHA256SUMS.txt`. Replace
`<version>` with the version shown on the release page.

## 2. Launch

Run the installer, then open **Local Time Tracker**. The status badge changes
from **Stopped** to **Starting…**, then to **Running**. The detail line says
tracking is active. You do not need to press **Start tracking** on a normal
first launch.

Activity stays on this computer, under
`%LOCALAPPDATA%\LocalTimeTracker\`. Window titles can include private document
names, searches, or mail subjects. Nothing in this first run is sent to a
server.

## 3. Watch a harmless sample

Leave a synthetic window in front, such as a blank Notepad file named
`fictional-note.txt`, then switch to another harmless window. On
**Dashboard**, **LIVE ACTIVITY** should show the foreground application and
window. **RECENT ACTIVITY** adds a row after the next sample.

**Running** means the tracker is sampling. **Stopped** means it is not. Idle
time is separate: it means the keyboard and mouse were still, not that tracking
was turned off.

## 4. Check Usage analysis

Open the **Usage analysis** tab. **Today** is selected by default. The summary
cards, chart, and rankings describe the same local day. An empty chart says
**No activity during this period** until a sample has been stored.

## 5. Generate an offline report

Open **Reports and data**. Keep today's date in **Date (YYYY-MM-DD)**, then
press **Generate and open report**. The report is an HTML file in the local
reports folder. **Open reports folder** shows that folder. The report does not
need a network connection.

## 6. Stop and start

Press **Stop**. The badge returns to **Stopped** and the detail line says
tracking is not running. Press **Start tracking** to sample again. Closing the
window also stops tracking.

Do not press **Reset** or **Reset all activity history** while learning the
app. Those actions permanently delete recorded periods. Previously generated
HTML reports are kept.

## If no activity appears

- Confirm the badge says **Running**, not **Stopped** or **Error**.
- Click a normal window so it is in the foreground, then wait for one sample.
- Some elevated windows hide their title from a non-elevated app.
- Very short visits can fall between samples.

For more help, read [SUPPORT.md](../SUPPORT.md). Do not send your
`activity.db` or a screenshot that shows real window titles.
