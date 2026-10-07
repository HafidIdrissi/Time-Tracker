# Support

## Questions and troubleshooting

Use [GitHub Discussions](https://github.com/HafidIdrissi/Time-Tracker/discussions)
for installation questions, configuration help, ideas, and general usage
discussion.

Before posting:

1. check the [README](README.md) and
   [latest release notes](https://github.com/HafidIdrissi/Time-Tracker/releases/latest);
2. search existing discussions and issues;
3. remove private window titles, account names, document names, and paths from
   screenshots or logs.

### Dependencies installed into the wrong Python environment

Import errors after installation usually mean `pip install` ran against a
different Python than the one the project uses. Confirm the interpreter and
its pip target before reinstalling:

```powershell
.\.venv\Scripts\python.exe -c "import sys; print(sys.executable, sys.version)"
.\.venv\Scripts\python.exe -m pip --version
```

The first command prints the full path and version of the interpreter inside
the virtual environment. The second shows which environment `pip` will install
into. If either path points outside `.venv`, packages are landing in the wrong
place.

Install requirements with the same interpreter so every dependency reaches the
correct environment:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If the virtual environment was created with an unsupported interpreter, remove
and recreate it with a supported version (Python 3.11 or later):

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Not every `ImportError` is a Tk or system-library problem — check the
interpreter path first. See [#209](https://github.com/HafidIdrissi/Time-Tracker/issues/209)
for additional context.

## Bug reports

Use the
[bug report form](https://github.com/HafidIdrissi/Time-Tracker/issues/new?template=bug_report.yml)
for reproducible application problems. Include the application version,
Windows version, expected behavior, actual behavior, and safe reproduction
steps.

Do not upload `activity.db` or a personal generated report. If sample data is
essential, create a new database containing demonstration activity only.

## Security issues

Do not open a public issue for a vulnerability. Follow the private process in
[SECURITY.md](SECURITY.md).
