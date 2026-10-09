# VS Code Development and Test Discovery

This guide explains how to configure Visual Studio Code to develop Local Time Tracker, discover and run its core unittest suite using the project virtual environment, and run focused tests from the editor and terminal.

## Workspace setup

1. **Open the repository root**:
   Launch VS Code and open the repository root folder (`Time-Tracker`, where `CONTRIBUTING.md` and `windows_app.py` reside) as your workspace folder (**File > Open Folder...**). Opening a subfolder directly will prevent VS Code from resolving the relative paths for test discovery and configuration.

2. **Select the project interpreter**:
   Open the Command Palette (`Ctrl+Shift+P`) and choose **Python: Select Interpreter**.
   Select the Python interpreter from the project virtual environment:
   * On Windows: `.\.venv\Scripts\python.exe`
   * On Linux/macOS: `./.venv/bin/python`

   If the virtual environment does not exist yet, create it and install the dependencies as described in [CONTRIBUTING.md](../CONTRIBUTING.md):
   ```powershell
   py -3.11 -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

## Configuring unittest discovery

To configure VS Code to discover the core test suite:

1. Open the Command Palette (`Ctrl+Shift+P`) and run **Python: Configure Tests**.
2. Select **unittest** as the test framework.
3. Select **`tests`** as the directory containing tests.
4. Select **`test_*.py`** as the test file naming pattern.

### Portable `.vscode/settings.json` example (optional)

VS Code stores these test discovery settings in `.vscode/settings.json`. The repository `.gitignore` ignores `.vscode/`, keeping developer-specific configuration local. To keep settings portable across Windows, Linux, and macOS, select your platform-specific `.venv` interpreter through **Python: Select Interpreter** in VS Code rather than hardcoding interpreter paths in settings:

```json
{
  "python.testing.unittestArgs": [
    "-v",
    "-s",
    "tests",
    "-p",
    "test_*.py"
  ],
  "python.testing.unittestEnabled": true,
  "python.testing.pytestEnabled": false
}
```

> **Note**: Do not commit the `.vscode/` directory to source control.

## Running tests in the VS Code Testing panel

Once discovery is configured:

1. Open the **Testing** panel by clicking the beaker icon on the Activity Bar, or open the Command Palette (`Ctrl+Shift+P`) and run **Testing: Focus on Test Explorer View**.
2. Expand the test tree: `tests` > `test_usage_range.py` > `UsageRangeTests`.
3. Locate `test_previous_seven_days_do_not_overlap_last_seven_days`.
4. Click the **Run Test** icon (play button) next to the test, or right-click and choose **Run Test** / **Debug Test**.
5. The test status icon will turn green upon passing.

## Running the matching command from the repository root

You can run the exact matching focused test directly in your terminal from the repository root using the project virtual environment:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_usage_range.UsageRangeTests.test_previous_seven_days_do_not_overlap_last_seven_days -v
```

To run the entire core unit test suite via discovery matching the configuration:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

Or using the standard shortcut documented in [CONTRIBUTING.md](../CONTRIBUTING.md):

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
```

## Why command-line validation remains authoritative

While the VS Code Testing panel provides a convenient visual interface and interactive debugging, command-line validation in a clean terminal using the explicit virtual environment interpreter (`.\.venv\Scripts\python.exe`) remains authoritative because:

- **Exact parity with CI**: GitHub Actions runs test commands directly via `python -m unittest` in clean subshells without IDE extensions, background hooks, or cached discovery state.
- **Environment isolation**: Editor test runners can cache discovery metadata, retain stale environment variables, or inherit process-level configurations that mask transient or imported state issues.
- **Unambiguous executable path**: Invoking `.\.venv\Scripts\python.exe` directly guarantees execution against the project virtual environment rather than an ambient system Python interpreter.

Always verify your changes with the command-line test runner before submitting pull requests.

## Why unittest discovery does not run `tests/windows_desktop_smoke.py`

The core unittest discovery pattern is configured to match `test_*.py`. Consequently, `tests/windows_desktop_smoke.py` is intentionally excluded from ordinary unittest discovery:

1. **Naming pattern exclusion**: The file name `windows_desktop_smoke.py` does not start with `test_`, so pattern-based discovery (`-p "test_*.py"`) ignores it.
2. **Interactive UI and lifecycle requirements**: `windows_desktop_smoke.py` exercises native Windows desktop UI components (`Tk`/`ttk` windows, event loops, and dialog bindings). It is intended to be executed standalone on Windows rather than in headless or general headless discovery matrices (such as the non-Windows Ubuntu CI runner).

To run the native Windows desktop checks, execute the file directly from the repository root as documented in [docs/WINDOWS_VALIDATION.md](WINDOWS_VALIDATION.md):

```powershell
.\.venv\Scripts\python.exe tests/windows_desktop_smoke.py
```
