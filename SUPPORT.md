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

## Troubleshoot a missing Windows py launcher

The contributor and development setup begins with `py -m venv .venv` (see
[CONTRIBUTING.md: Development setup](CONTRIBUTING.md#development-setup)). If your
Windows environment does not recognize the `py` command, use this recipe to
diagnose the cause and create the project virtual environment without changing
system security settings.

### Distinguish the cause

Before troubleshooting, confirm which condition you are encountering:

- **Missing `py` launcher command:**
  In PowerShell, running `py` fails with:
  ```text
  py : The term 'py' is not recognized as the name of a cmdlet, function, script file, or operable program.
  ```
  In Command Prompt (`cmd.exe`), running `py` fails with:
  ```text
  'py' is not recognized as an internal or external command, operable program or batch file.
  ```
  This indicates that the Python launcher for Windows (`py.exe`) is not installed or not on `PATH`.
- **Unsupported Python version or architecture:**
  The command runs, but `python --version` reports an unsupported version (older than Python 3.11), or a 32-bit (`x86`) build. Local Time Tracker requires 64-bit Windows with Python 3.11 or later (see [README.md: Requirements](README.md#requirements)). Verify your Python interpreter with:
  ```powershell
  python -c "import sys; print(sys.version); print('64-bit' if sys.maxsize > 2**32 else '32-bit')"
  ```
- **Missing project virtual environment:**
  Running commands like `.\.venv\Scripts\python.exe` fails with path-not-found errors if `.venv` has not been created yet. The virtual environment must be created once before invoking its interpreter.

### Create the project virtual environment with an existing Python executable

From the repository root, if a supported 64-bit Python 3.11+ interpreter is already installed on your machine, you can create `.venv` directly without the `py` launcher. Replace the example paths below with your actual verified interpreter location:

1. Locate an existing Python executable:
   ```powershell
   # Search PATH in PowerShell:
   (Get-Command python).Source
   ```
   Note: On Windows, `Get-Command python` may return an App Execution Alias (such as `...\AppData\Local\Microsoft\WindowsApps\python.exe`) rather than a usable interpreter. If invoking it fails or opens the Microsoft Store, use a known installation path or the official installation guidance.

   Common Windows installation locations include:
   - Per-user: `C:\Users\<username>\AppData\Local\Programs\Python\Python312\python.exe`
   - System-wide: `C:\Program Files\Python312\python.exe`

2. Confirm the executable meets the 64-bit Python 3.11+ requirement:
   ```powershell
   & "C:\Program Files\Python312\python.exe" -c "import sys; print(sys.version); print('64-bit' if sys.maxsize > 2**32 else '32-bit')"
   ```

3. From the repository root, create the project `.venv` using the verified executable path. When the path contains spaces, enclose it in quotes:
   - In **PowerShell**, use the call operator `&` before the quoted path:
     ```powershell
     & "C:\Program Files\Python312\python.exe" -m venv .venv
     ```
   - In **Command Prompt** (`cmd.exe`), invoke the quoted path directly:
     ```cmd
     "C:\Program Files\Python312\python.exe" -m venv .venv
     ```

4. Run all subsequent setup and workflow commands from the repository root using that virtual environment's interpreter directly:
   ```powershell
   .\.venv\Scripts\python.exe -m pip install --upgrade pip
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   .\.venv\Scripts\python.exe -m unittest discover -v
   .\.venv\Scripts\python.exe windows_app.py
   ```

### Security and installation guidance

- **Do not weaken PowerShell protections:** Calling the virtual environment interpreter `.\.venv\Scripts\python.exe` directly avoids script execution, so you do not need to run `Set-ExecutionPolicy` or disable PowerShell execution policies.
- **Do not use blanket administrator elevation:** Creating virtual environments and running development commands should be performed in a standard user shell without Administrator privileges.
- **Do not install project dependencies globally:** Always install requirements into the project's `.venv` using `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`, rather than into your base Python installation.
- **Official installer guidance:** If no supported 64-bit Python is installed, download an official 64-bit installer from [Python Releases for Windows](https://www.python.org/downloads/windows/). For installation instructions, see [Python Docs: Using Python on Windows](https://docs.python.org/3/using/windows.html).


## Bug reports

Use the
[bug report form](https://github.com/HafidIdrissi/Time-Tracker/issues/new?template=bug_report.yml)
for reproducible application problems. Include the application version,
Windows version, expected behavior, actual behavior, and safe reproduction
steps.

Do not upload `activity.db` or a personal generated report. If sample data is
essential, create a new database containing demonstration activity only.

## Recover from malformed category configuration

If category preview reports `Invalid JSON`, check the configuration file you
passed to `--config`. First identify the intended file: the README's
[configuration-location guidance](README.md#local-data-and-privacy) lists
where the app keeps `config.json`, and the
[Categories guide](README.md#categories) explains the format. The preview
script does not find the app's config for you; `--config` must name the file
you want to check.

Before editing, make a backup of your own configuration. For example, if you
are using a fictional `C:\demo\config.json`, run this in PowerShell:

```powershell
Copy-Item "C:\demo\config.json" "C:\demo\config.json.bak"
```

Do not replace the backup with the edited file.

An error such as `Invalid JSON in C:\demo\config.json (line 3)` reports the
line where parsing failed; the mistake can be on that line or just before it.
For example, this fictional config is missing a comma after `"Other"`:

```json
{
  "default_category": "Other"
  "categories": [
    {"name": "Work", "keywords": ["gmail"]}
  ]
}
```

Add the comma, save the file, and preview that same path again:

```json
{
  "default_category": "Other",
  "categories": [
    {"name": "Work", "keywords": ["gmail"]}
  ]
}
```

From the repository root, run the existing preview command with the exact
configuration path (quote paths that contain spaces):

```powershell
.\.venv\Scripts\python.exe .\preview_category.py --config "C:\demo\config.json" --application chrome.exe --title "Fictional inbox gmail"
```

The malformed file prints an error and returns a non-zero exit status; the
corrected file prints `Work`. Preview only reads the file—it does not repair or
rewrite it. Do not delete `activity.db` or use Reset: those affect recorded
activity, not category configuration, and are unrelated to this repair.

Use a fictional or disposable configuration when testing recovery steps. Do not
share personal activity databases or reports when asking for help.

## Security issues

Do not open a public issue for a vulnerability. Follow the private process in
[SECURITY.md](SECURITY.md).
