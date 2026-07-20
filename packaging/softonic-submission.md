# Download Platform Submission Sheet

Use this sheet for Softonic or another software catalog only after the final
installer has been signed, verified, and published in an official GitHub
release.

## Product details

- Product: Local Time Tracker
- Version: 1.1.0
- Publisher: H.I. SOLUTIONS
- Developer/legal operator: IDRISSI HAFID, sole proprietor
- License: MIT License / Free and open-source software
- Price: Free
- Platform: Windows 10 and Windows 11, 64-bit
- Suggested category: Productivity / Time Management
- Interface language: English
- Installer language: English
- Official website and source:
  <https://github.com/HafidIdrissi/Time-Tracker>
- Support: <https://github.com/HafidIdrissi/Time-Tracker/issues>

## Short description

Track time spent in Windows applications and browser tabs locally, with live
activity, seven-day analysis, idle detection, and private offline reports.

## Long description

Local Time Tracker is a free, open-source Windows application that helps users
understand daily computer usage without uploading activity data. It detects the
foreground application and window, measures active periods, identifies keyboard
and mouse inactivity, and groups activity into configurable categories.

The dashboard displays the current application, window title, current duration,
idle time, and recent activity. Usage analysis shows active time, the longest
session, an hourly or daily chart, leading categories, most used applications,
and frequently used browser tabs. Standalone HTML reports provide a detailed
timeline and can be opened without an internet connection.

All activity is stored in a local SQLite database. The application has no
account, advertising, or telemetry.

## Feature list

- live foreground-window tracking;
- configurable idle detection;
- Today and Last 7 days analysis;
- application and browser-tab rankings;
- offline HTML reports;
- local SQLite storage;
- Start, Stop, and Reset controls;
- standard per-user Windows installation and uninstallation.

## Privacy disclosure

Window titles may contain sensitive information. Activity stays on the user's
computer and is not transmitted by the application. See `PRIVACY.md` in the
repository for the complete policy.

## Release assets to provide

- signed installer: `LocalTimeTracker-Setup-1.1.0-x64.exe`;
- SHA-256 checksum from `SHA256SUMS.txt`;
- direct URL to the signed GitHub release asset: **add after release**;
- repository URL and MIT License URL;
- privacy-policy URL;
- VirusTotal result for the exact signed installer: **add before submission**.

## Screenshots

Recommended images:

- Dashboard with neutral demonstration data;
- Today usage analysis;
- Last 7 days analysis;
- standalone HTML report;
- English installer wizard.

Before taking screenshots, use a demonstration database that contains no real
names, email addresses, documents, account details, or private window titles.

## Submission checklist

- [ ] version matches the application, installer, tag, and release;
- [ ] automated tests pass;
- [ ] installer is Authenticode-signed and signature verification passes;
- [ ] SHA-256 checksum is published;
- [ ] antivirus scan is complete;
- [ ] installation, launch, tracking, report, reset, and uninstall are tested;
- [ ] screenshots contain demonstration data only;
- [ ] download URL points to the official GitHub release asset;
- [ ] privacy policy and legal notice are publicly accessible.
