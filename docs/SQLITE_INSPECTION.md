# Inspect a SQLite backup safely

This walkthrough uses only a generated fictional database. It does not open the
installed application's database, read live activity, or upload any files.

The tracker stores activity in SQLite with write-ahead logging (WAL) enabled.
Do not copy an open database by copying only its `.db` file: committed data
may still be in the WAL sidecar. Use the existing
`timetracker.backup.backup_activity_database` helper to create a consistent
snapshot, then inspect that snapshot rather than the source.

## 1. Generate fictional activity

From the repository root, create a disposable fixture in a path containing
spaces and Unicode characters:

```powershell
.\.venv\Scripts\python.exe .\scripts\generate_demo_data.py --output "$env:TEMP\Time Tracker – SQLite inspection\source"
```

The generator refuses to overwrite an existing database. Its five fictional
periods are dated 16–17 September 2026 (UTC): 105 minutes active in the morning,
15 minutes idle, 40 minutes active in the evening, and 40 minutes active across
midnight. The expected totals are **185 minutes active** and **15 minutes idle**.

## 2. Create and inspect a read-only snapshot

Save the following temporary script as `inspect_sqlite_backup.py` in the
repository root. It uses the fixture created in step 1 and writes a separate
snapshot beside it.

```python
from contextlib import closing
from hashlib import sha256
from pathlib import Path
import sqlite3
import tempfile

from timetracker.backup import backup_activity_database

work_dir = Path(tempfile.gettempdir()) / "Time Tracker – SQLite inspection"
source = work_dir / "source" / "activity.db"
snapshot = work_dir / "backup snapshot.sqlite"

if not source.is_file():
    raise FileNotFoundError("Run the fictional-data generator in step 1 first")

source_before = sha256(source.read_bytes()).digest()
backup_activity_database(source, snapshot)
source_after_backup = sha256(source.read_bytes()).digest()
assert source_before == source_after_backup, "Backup changed the source database"

# as_uri() percent-encodes spaces and Unicode in the file path.
read_only_uri = snapshot.resolve().as_uri() + "?mode=ro"

query = """
SELECT
    COUNT(*) AS period_count,
    SUM(CASE WHEN is_idle = 0 THEN duration_seconds ELSE 0 END) AS active_seconds,
    SUM(CASE WHEN is_idle = 1 THEN duration_seconds ELSE 0 END) AS idle_seconds
FROM activity_periods
WHERE started_at >= ? AND started_at < ?
"""

with closing(sqlite3.connect(read_only_uri, uri=True)) as connection:
    period_count, active_seconds, idle_seconds = connection.execute(
        query,
        ("2026-09-16T00:00:00.000+00:00", "2026-09-18T00:00:00.000+00:00"),
    ).fetchone()

    print(f"Periods: {period_count}")
    print(f"Active: {active_seconds:.0f} seconds (185 minutes)")
    print(f"Idle: {idle_seconds:.0f} seconds (15 minutes)")

    try:
        connection.execute("DELETE FROM activity_periods")
    except sqlite3.OperationalError as error:
        print(f"Write refused: {error}")
    else:
        raise AssertionError("The read-only connection unexpectedly allowed a write")

source_after_inspection = sha256(source.read_bytes()).digest()
assert source_before == source_after_inspection, "Inspection changed the source database"
assert (period_count, active_seconds, idle_seconds) == (5, 11100.0, 900.0)
print("Source database unchanged: yes")
print(f"Snapshot: {snapshot}")
```

Run it with the configured environment:

```powershell
.\.venv\Scripts\python.exe .\inspect_sqlite_backup.py
```

Expected results:

```text
Periods: 5
Active: 11100 seconds (185 minutes)
Idle: 900 seconds (15 minutes)
Write refused: attempt to write a readonly database
Source database unchanged: yes
```

SQLite's exact error wording can vary by version; the important result is that
the attempted `DELETE` raises `sqlite3.OperationalError`. The script also
checks the source database's SHA-256 digest before backup, after backup, and
after inspection.

The SQL uses placeholders for both time bounds rather than interpolating values
into the query. The interval is half-open: it includes the start and excludes
the end. The stored `started_at` values are ISO-formatted UTC timestamps with
an explicit `+00:00` offset; the selected bounds use the same representation.
The totals are based on the stored `duration_seconds` and `is_idle` columns,
not on local-time display or application categorization.

The script explicitly closes the SQLite connection with
`contextlib.closing`. A SQLite connection's transaction context manager
commits or rolls back a transaction but does not close the connection.

## 3. Clean up

After checking the output, remove the temporary script and the printed
`Time Tracker – SQLite inspection` directory from your temporary-files
location. These files contain fictional data only.

Never use a personal activity database for this walkthrough, and do not attach
or upload a database or generated report when asking for help.
