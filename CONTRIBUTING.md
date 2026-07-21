# Contributing to Local Time Tracker

Thank you for helping improve Local Time Tracker. Bug reports, feature ideas,
documentation changes, tests, and focused code contributions are welcome.

## Before you start

- Search existing issues before opening a new one.
- Never attach a real `activity.db`, personal HTML report, or screenshot that
  contains private window titles.
- Use demonstration data when reproducing reporting or interface problems.
- For vulnerabilities, follow [SECURITY.md](SECURITY.md) instead of opening a
  public issue.

## Development setup

Local Time Tracker targets 64-bit Windows 10 and Windows 11 with Python 3.11 or
later.

```powershell
git clone https://github.com/HafidIdrissi/Time-Tracker.git
cd Time-Tracker
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Run the desktop application:

```powershell
python windows_app.py
```

## Making a change

1. Fork the repository and create a focused branch.
2. Keep the change small enough to review comfortably.
3. Add or update tests for behavior changes.
4. Update documentation when the user experience changes.
5. Run the complete automated test suite.
6. Open a pull request and explain the user impact.

Suggested branch names include `fix/idle-transition`,
`feature/csv-export`, and `docs/privacy-example`.

## Tests

Run all tests from the repository root:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
```

For interface changes, also verify that tracking starts, foreground titles
update, Usage analysis loads, an offline report can be generated, and tracking
can be stopped and restarted.

Only test Reset with disposable data. Back up personal data before testing the
installer or uninstaller.

## Pull request checklist

- [ ] The change solves one clearly described problem.
- [ ] Tests pass locally.
- [ ] New behavior is covered by tests where practical.
- [ ] User-facing documentation is updated.
- [ ] No personal activity data, generated report, credential, or certificate
      is included.
- [ ] The pull request explains any privacy or compatibility impact.

## Project principles

Contributions should preserve the project's core promises:

- activity data remains local by default;
- no account, telemetry, advertising, or hidden network dependency;
- generated reports remain usable offline;
- destructive data actions require explicit confirmation;
- the Windows experience stays understandable for non-developers.

Release tags and public installers are created by the maintainer. Contributors
should not change published version tags.

By participating, you agree to follow the
[Code of Conduct](CODE_OF_CONDUCT.md).
