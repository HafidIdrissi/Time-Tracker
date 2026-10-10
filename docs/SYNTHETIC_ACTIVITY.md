# Synthetic activity database

Use this fixture for screenshots and interface checks. It does not read the
live desktop, and it never writes to `%LOCALAPPDATA%`.

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
