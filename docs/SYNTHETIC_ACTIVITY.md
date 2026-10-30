# Synthetic activity database

Use this fixture for screenshots and interface checks. It does not read the
live desktop, and it never writes to `%LOCALAPPDATA%`. To reduce a bug to a
few fictional periods, follow
[Reproduce a bug with a few fictional periods](#reproduce-a-bug-with-a-few-fictional-periods).

## Full demonstration database

From the repository root, choose an explicit new directory:

```powershell
python scripts/generate_demo_data.py --output C:\demo-time-tracker
```

The command creates `C:\demo-time-tracker\activity.db`. Running it again with
the same directory fails instead of replacing that file. If the destination is
unwritable, its parent path is a file, or SQLite encounters an error, the
command prints a concise error message to standard error without a traceback
and exits with status code 1.

To check the generator version without creating a database, run:

```powershell
python scripts/generate_demo_data.py --version
```

Every generated database contains the same fictional rows, fixed to
16–17 September 2026 (UTC):

- 16 September, 09:00–10:15, `Code.exe` (Work);
- 16 September, 10:15–10:45, a Gmail browser title (Work);
- 16 September, 10:45–11:00, an idle period;
- 16 September, 18:00–18:40, `steam.exe` (Games);
- 16 September 23:40 through 17 September 00:20, a YouTube browser title
  (Entertainment), crossing midnight.

Dashboard and Usage analysis show today and the recent week, so these historical
rows do not appear there. Inspect them with a dated report from the repository
root:

```powershell
python report.py --database C:\demo-time-tracker\activity.db --from 2026-09-16 --to 2026-09-17 --config config.example.json --output C:\demo-time-tracker\report-2026-09-16_2026-09-17.html
```

Do not copy the fixture over the installed database in
`%LOCALAPPDATA%\LocalTimeTracker\data\`. Delete the output directory when you
are finished.

## Reproduce a bug with a few fictional periods

The [full demonstration database](#full-demonstration-database) is a fixed set
of rows from
[`scripts/generate_demo_data.py`](../scripts/generate_demo_data.py). To reproduce
a bug with only the periods that matter, write those rows with `ActivityState`
and `ActivityDatabase` in a new temporary folder. That folder is not
`%LOCALAPPDATA%\LocalTimeTracker\data\` and it is not `data/activity.db` in a
checkout.

`ActivityState` is the fictional application and window title
(`timetracker/models.py`). `ActivityDatabase.create_period` inserts the row
and `update_period` sets its end (`timetracker/database.py`). Both timestamps
must be timezone-aware. A naive `datetime` raises `ValueError`.

From the repository root:

```python
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from timetracker.database import ActivityDatabase
from timetracker.models import ActivityState

folder = Path(tempfile.mkdtemp(prefix="time-tracker-repro-"))
database_path = folder / "activity.db"
report_path = folder / "report.html"
start = datetime(2026, 7, 20, 9, 0, tzinfo=timezone.utc)
mid = datetime(2026, 7, 20, 9, 15, tzinfo=timezone.utc)
end = datetime(2026, 7, 20, 9, 30, tzinfo=timezone.utc)

with ActivityDatabase(database_path) as database:
    active_id = database.create_period(
        ActivityState("Code.exe", "Fictional code editor"), start
    )
    database.update_period(active_id, start, mid)
    idle_id = database.create_period(
        ActivityState("Idle", "No keyboard or mouse activity", is_idle=True),
        mid,
    )
    database.update_period(idle_id, mid, end)

local_day = start.astimezone().date().isoformat()
print(f"database={database_path}")
print(f"report={report_path}")
print(f"local_day={local_day}")
```

Replace the fictional titles and the aware timestamps with the smallest
history that still shows the bug. Then generate a report from that database
only. Quote the printed paths:

```powershell
python report.py --database "<database>" --date <local_day> --config config.example.json --output "<report>"
```

`--date` is a local calendar day. Use the printed `local_day` so these UTC
timestamps fall inside the report. The HTML file is written beside the
temporary database and is built only from that file. Delete the temporary
folder when you are finished. Do not copy it over
`%LOCALAPPDATA%\LocalTimeTracker\data\`.

Do not add another fixture format, and do not attach a real database. When the
fixed multi-day rows are enough, use the full demonstration generator linked
above.

### Expected versus actual

Paste this template into the bug report. Keep every title fictional.

```text
Minimal history (aware timestamps):
- 2026-07-20 09:00–09:15 UTC, Code.exe, "Fictional code editor"
- 2026-07-20 09:15–09:30 UTC, Idle, "No keyboard or mouse activity"

Command:
python report.py --database "<database>" --date <local_day> --config config.example.json --output "<report>"

Expected (config.example.json, report limited to the printed local day):
- Active time: 15 min
- Idle time detected: 15 min
- Applications used: 1
- Totals by category: Work, 15 min (keyword code.exe)
- Applications: Code.exe, 100 %, 15 min
- Window titles: Code.exe, Fictional code editor, 15 min
- Detailed timeline: Code.exe / Work, then Idle / Idle
- Report file stays inside the temporary folder

Actual:
- <what the command printed, or what the report showed>

Temporary folder (deleted afterwards): <path>
```
