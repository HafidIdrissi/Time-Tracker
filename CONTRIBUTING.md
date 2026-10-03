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

## Find and claim an issue

New contributors can start from the repository's
[contribution page](https://github.com/HafidIdrissi/Time-Tracker/contribute).
Issues labeled `good first issue` are small, focused introductions to the
project. Issues labeled `help wanted` may require more design or Windows
testing.

1. Choose an open, unassigned issue that matches your experience.
2. Comment with a short implementation plan and ask to be assigned.
3. Wait for the maintainer to confirm the scope before starting substantial
   work, so two people do not solve the same issue.
4. Work on one claimed issue at a time. Open a draft pull request early if you
   want feedback on the approach.
5. Link the pull request with `Closes #<issue-number>` and include the validation
   you performed.

If you become unavailable or blocked, leave a comment so the issue can be made
available again. Claims with no update for seven days may be released after a
maintainer check-in.

The maintainer aims to acknowledge claim requests and review focused pull
requests within two working days. Larger changes may take longer or require a
design discussion first.

## Development setup

Local Time Tracker targets 64-bit Windows 10 and Windows 11 with Python 3.11 or
later. The commands below call the virtual environment's `python.exe`
directly, so PowerShell activation and an execution-policy change are not
required.

1. Fork [HafidIdrissi/Time-Tracker](https://github.com/HafidIdrissi/Time-Tracker).
2. Clone your fork. Replace `<your-username>` with your GitHub username:

```powershell
git clone https://github.com/<your-username>/Time-Tracker.git
cd Time-Tracker
git remote add upstream https://github.com/HafidIdrissi/Time-Tracker.git
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

`upstream` is optional. Use it when you want to update your fork from the
original repository. Create a focused branch before editing:

```powershell
git checkout -b fix/short-description
```

Run the desktop application:

```powershell
.\.venv\Scripts\python.exe windows_app.py
```

Open the pull request against `HafidIdrissi/Time-Tracker` from that branch.
The README section [Run from source](README.md#run-from-source) is for people
who only want to run the app. Use this page when you are changing it.

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

Use that same `python.exe` for every test command in this repository.

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
