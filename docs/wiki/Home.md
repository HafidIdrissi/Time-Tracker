# Local Time Tracker Wiki

Local Time Tracker is a free, open-source Windows application for understanding time spent in foreground applications and browser tabs. Activity is stored locally: no account, telemetry or cloud service is required.

## Start here

| What you want to do | Guide |
| --- | --- |
| Install the app | [Latest Windows release](https://github.com/HafidIdrissi/Time-Tracker/releases/latest) and [first-run walkthrough](https://github.com/HafidIdrissi/Time-Tracker/blob/main/docs/FIRST_RUN.md) |
| Understand the desktop | [Dashboard, Usage analysis, Reports and data](https://github.com/HafidIdrissi/Time-Tracker/blob/main/README.md#desktop-interface) |
| Customize categories | [Configuration and category preview](https://github.com/HafidIdrissi/Time-Tracker/blob/main/README.md#categories) |
| Export, back up or delete activity | [Reports and data](https://github.com/HafidIdrissi/Time-Tracker/blob/main/README.md#reports-and-data) and [privacy policy](https://github.com/HafidIdrissi/Time-Tracker/blob/main/PRIVACY.md) |
| Run the command-line tools | [Tracking and report commands](https://github.com/HafidIdrissi/Time-Tracker/blob/main/README.md#command-line-tools) |
| Get help | [Support guide](https://github.com/HafidIdrissi/Time-Tracker/blob/main/SUPPORT.md) and [Discussions](https://github.com/HafidIdrissi/Time-Tracker/discussions) |
| Make your first contribution | [Contributing guide](https://github.com/HafidIdrissi/Time-Tracker/blob/main/CONTRIBUTING.md) and [available starter tasks](https://github.com/HafidIdrissi/Time-Tracker/issues?q=is%3Aissue%20is%3Aopen%20no%3Aassignee%20label%3A%22good%20first%20issue%22) |
| Understand the code | [Architecture](https://github.com/HafidIdrissi/Time-Tracker/blob/main/docs/ARCHITECTURE.md), [fictional data](https://github.com/HafidIdrissi/Time-Tracker/blob/main/docs/SYNTHETIC_ACTIVITY.md) and [Windows validation](https://github.com/HafidIdrissi/Time-Tracker/blob/main/docs/WINDOWS_VALIDATION.md) |

## Install and try it

The desktop application supports **64-bit Windows 10 and Windows 11**.

1. Open the [latest release](https://github.com/HafidIdrissi/Time-Tracker/releases/latest).
2. Choose the `LocalTimeTracker-Setup-<version>-x64.exe` installer, or the `LocalTimeTracker-<version>-portable-x64.zip` portable build. The packaged application does not require a separate Python installation.
3. Download `SHA256SUMS.txt` from the same release if you want to [compare the download's SHA-256 hash](https://github.com/HafidIdrissi/Time-Tracker/blob/main/README.md#verify-the-windows-installer-checksum).
4. Install and launch the app, or extract the portable ZIP to a writable folder and run `LocalTimeTracker.exe`. Keep `portable.mode` beside the portable executable.
5. Tracking starts automatically on a normal first launch. Try harmless fictional window titles, then open **Usage analysis** or generate an offline report.

Run one tracker instance at a time. Follow the [first-run guide](https://github.com/HafidIdrissi/Time-Tracker/blob/main/docs/FIRST_RUN.md) for the status badges, stopping and restarting, and safe examples.

## Understand your activity

- **Dashboard** shows the current foreground application, its title, tracking status, active/idle totals and recent activity.
- **Usage analysis** provides Today, Last 7 days and Previous 7 days, with charts and category, application and browser-tab rankings.
- **Reports and data** generates offline HTML reports, exports CSV/JSON, creates a SQLite backup and offers a confirmed history reset.
- Sampling and idle settings are remembered in `preferences.json`; missing or invalid values fall back to a one-second interval and a three-minute idle threshold.

The tracker measures **foreground focus**, not attention. Background browser tabs and the monitor under the mouse pointer are not independent tracked activities. Browser-tab names come from window titles; very short visits can fall between samples. See [what the tracker measures](https://github.com/HafidIdrissi/Time-Tracker/blob/main/README.md#what-the-tracker-measures) and [known limitations](https://github.com/HafidIdrissi/Time-Tracker/blob/main/README.md#known-limitations).

## Categories and reports

Categories use case-insensitive keywords from `config.json`, falling back to `config.example.json` when no personal configuration exists. The first matching rule wins, so put specific rules before broader ones; idle periods retain the Idle category.

The [category guide](https://github.com/HafidIdrissi/Time-Tracker/blob/main/README.md#categories) includes a small example and a preview command that does not start tracking. For dated or multi-day HTML reports, use the [documented report commands](https://github.com/HafidIdrissi/Time-Tracker/blob/main/README.md#command-line-tools). Generated reports have no external scripts, fonts or network dependencies.

## Keep control of your data

| Mode | Activity and reports |
| --- | --- |
| Installed | Under `%LOCALAPPDATA%\LocalTimeTracker\` |
| Portable | In the extracted portable folder |
| Source checkout | In the repository's `data` and `reports` folders |

Window titles can contain private document names, searches and mail subjects. The database and generated reports are not encrypted by the application. Share fictional examples instead of personal databases or reports.

A database backup includes committed activity while tracking continues; it does not include HTML reports or `config.json`. Back up a portable installation's whole folder before replacing it. **Reset** deletes recorded periods after confirmation and keeps previously generated HTML reports. The official uninstaller removes the installed app's local data directory. Read the [privacy policy](https://github.com/HafidIdrissi/Time-Tracker/blob/main/PRIVACY.md) for details.

## Contribute one focused improvement

Documentation, Python core tests, offline report accessibility and Windows testing are all welcome.

1. Read [CONTRIBUTING.md](https://github.com/HafidIdrissi/Time-Tracker/blob/main/CONTRIBUTING.md).
2. Choose an open, unassigned [good first issue](https://github.com/HafidIdrissi/Time-Tracker/issues?q=is%3Aissue%20is%3Aopen%20no%3Aassignee%20label%3A%22good%20first%20issue%22) or [help wanted task](https://github.com/HafidIdrissi/Time-Tracker/issues?q=is%3Aissue%20is%3Aopen%20no%3Aassignee%20label%3A%22help%20wanted%22). Check comments and linked PRs as well as the assignee.
3. Comment with a short plan and wait for maintainer scope confirmation.
4. Follow the fork-first setup, work on one claimed task and open one focused PR.
5. Report the validation actually performed: OS/runtime, exact commands, results and any skipped checks. Code changes need focused and full tests with the same configured interpreter; documentation needs the relevant walkthrough and link/preview checks.

The desktop and live sampling need Windows. Core storage, categorization, analytics and report work also has a non-Windows CI path. Use the [architecture guide](https://github.com/HafidIdrissi/Time-Tracker/blob/main/docs/ARCHITECTURE.md) and [synthetic activity fixture](https://github.com/HafidIdrissi/Time-Tracker/blob/main/docs/SYNTHETIC_ACTIVITY.md) to explore without personal data. Follow the [Code of Conduct](https://github.com/HafidIdrissi/Time-Tracker/blob/main/CODE_OF_CONDUCT.md).

## Questions, bugs and security

Use [Discussions](https://github.com/HafidIdrissi/Time-Tracker/discussions) for questions and ideas. For a reproducible bug, search existing reports, then use the [bug report form](https://github.com/HafidIdrissi/Time-Tracker/issues/new?template=bug_report.yml) with the app/Windows versions and safe reproduction steps. Follow [SECURITY.md](https://github.com/HafidIdrissi/Time-Tracker/blob/main/SECURITY.md) for vulnerabilities rather than posting sensitive details publicly.

## Project references

[README](https://github.com/HafidIdrissi/Time-Tracker/blob/main/README.md) · [Release notes](https://github.com/HafidIdrissi/Time-Tracker/releases) · [Changelog](https://github.com/HafidIdrissi/Time-Tracker/blob/main/CHANGELOG.md) · [Roadmap](https://github.com/HafidIdrissi/Time-Tracker/blob/main/ROADMAP.md) · [MIT license](https://github.com/HafidIdrissi/Time-Tracker/blob/main/LICENSE)

The repository guides are the detailed references for these topics. Roadmap entries describe direction; they are not promises of available features or delivery dates.
