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

## Wrong Python environment

If `import` errors appear after installing dependencies, the packages may have
been installed into a different Python environment. Verify the interpreter and
pip target with:

```powershell
.\.venv\Scripts\python.exe -c "import sys; print(sys.executable, sys.version)"
.\.venv\Scripts\python.exe -m pip --version
```

The first command prints the full path and version of the interpreter that will
run the application. The second shows which environment `pip` is operating in.
If either path points outside `.venv`, packages are being installed elsewhere.

Reinstall into the correct environment using the same interpreter:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If the virtual environment uses an unsupported interpreter (below Python 3.11),
recreate it with a supported version:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Not every `ModuleNotFoundError` is a Tk or system-library problem — check the
environment first. See [#209](https://github.com/HafidIdrissi/Time-Tracker/issues/209)
for additional context.

## Dependencies installed into the wrong Python environment

If `pip install` succeeds but `import` still fails, the packages may have been
installed into a different Python environment. Verify the project interpreter
and its pip location first:

```powershell
.\.venv\Scripts\python.exe -c "import sys; print(sys.executable, sys.version)"
.\.venv\Scripts\python.exe -m pip --version
```

The first command prints the full interpreter path and version. The second
shows which environment `pip` is operating in. If either path points outside
`.venv\Scripts\`, packages are being installed into the wrong environment.

Install the project requirements with the same interpreter so they land in the
correct virtual environment:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If the virtual environment is damaged or was created with an unsupported
interpreter, recreate it with a supported version (Python 3.11 or later):

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Not every `ImportError` is a Tk problem. Confirm which package is actually
missing and whether the interpreter path matches before assuming a toolkit
issue. See [#209](https://github.com/HafidIdrissi/Time-Tracker/issues/209)
for additional context on environment-related import failures.

## Dependencies installed into the wrong Python environment

If imports fail after installing packages, the most common cause is a mismatch
between the interpreter that created the virtual environment and the one used to
install or run. Diagnose with:

```powershell
.\.venv\Scripts\python.exe -c "import sys; print(sys.executable, sys.version)"
.\.venv\Scripts\python.exe -m pip --version
```

The first command prints the interpreter path and version. The second shows
which environment `pip` operates on. If either points outside `.venv`, packages
land in the wrong place.

Install into the correct environment by calling `pip` through the same
interpreter:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If the virtual environment was created with an unsupported interpreter, recreate
it with a supported version (Python 3.11 or later):

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Not every `ImportError` is a Tk problem. Confirm the interpreter and pip
environment match before investigating further. See
[#209](https://github.com/HafidIdrissi/Time-Tracker/issues/209) for additional
context, and the [Contributing guide](CONTRIBUTING.md#development-setup) for the
full development setup.

## Dependencies installed into the wrong Python environment

If `import` errors appear after installing packages, the project interpreter may
differ from the one `pip` used. Confirm the active interpreter and its `pip`:

```powershell
.\.venv\Scripts\python.exe -c "import sys; print(sys.executable, sys.version)"
.\.venv\Scripts\python.exe -m pip --version
```

The first command prints the full path and version of the interpreter inside the
virtual environment. The second shows which environment `pip` is operating in.
If either path points outside `.venv\Scripts\`, packages are being installed
into a different Python and will not be importable by the project.

Install dependencies with the same interpreter so they land in the correct
environment:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If the virtual environment was created with an unsupported interpreter, recreate
it with a supported version (Python 3.11 or later):

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Not every `ModuleNotFoundError` is a Tk or system library problem — check the
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
