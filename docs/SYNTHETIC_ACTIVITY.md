# Synthetic activity database

Use this fixture for screenshots and interface checks. It does not read the
live desktop, and it never writes to `%LOCALAPPDATA%`.

From the repository root, choose an explicit new directory:

```powershell
python scripts/generate_demo_data.py --output C:\demo-time-tracker
```

The command creates `C:\demo-time-tracker\activity.db`. Running it again with
the same directory fails instead of replacing that file. The rows are
fictional: a code editor, a browser title, an idle period, a game, and one
period that crosses midnight. With `config.example.json`, those rows fall into
more than one category.

To inspect the fixture from a source checkout, copy only that database into a
disposable clone:

```text
<disposable-checkout>\data\activity.db
```

Do not copy it over the installed database in
`%LOCALAPPDATA%\LocalTimeTracker\data\`. Launch `python windows_app.py` from
the disposable checkout. The Dashboard and Usage analysis then read the
fictional rows. Delete the disposable checkout when you are finished.
