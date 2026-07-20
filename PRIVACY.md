# Privacy Policy

Last updated: July 20, 2026

Local Time Tracker is a local activity-tracking application published by
**H.I. SOLUTIONS**, operated by IDRISSI HAFID as a sole proprietor. The
application requires no account and does not send activity data to the
publisher.

## Data recorded

While tracking is active, the application records:

- the foreground application's process name;
- the foreground window or browser-tab title;
- the start and end time of each activity period;
- the calculated duration;
- whether keyboard and mouse inactivity exceeded the selected threshold.

Window titles can contain sensitive information, including document names,
searches, email subjects, user names, or private web page titles.

## Purpose

The recorded data is used only to display the dashboard, calculate usage
statistics, and generate reports requested by the user.

## Storage

Data is stored in a local SQLite database. For the installed application, the
default path is:

```text
%LOCALAPPDATA%\LocalTimeTracker\data\activity.db
```

HTML reports are stored under:

```text
%LOCALAPPDATA%\LocalTimeTracker\reports\
```

When the app is run from source, data is stored in the repository's `data` and
`reports` folders.

## Network access and third parties

The application:

- does not upload activity history;
- does not use telemetry, analytics, advertising, or tracking SDKs;
- does not create an online account;
- does not sell or share activity data.

GitHub or a third-party download platform may process its own technical data
when a visitor views a page or downloads an installer. Those services operate
under their own privacy policies and are separate from the local application.

## Retention and deletion

Activity remains on the computer until the user resets the history, deletes the
database, or uninstalls the application with the official uninstaller. Resetting
the history does not delete previously generated HTML reports. Those reports
must be deleted separately if they are no longer needed.

## Security

The database and reports are not encrypted by the application. They rely on the
security of the Windows account, filesystem, and disk. Anyone with access to the
files may be able to read the recorded window titles.

## Contact and publisher

**H.I. SOLUTIONS**<br>
IDRISSI HAFID — Sole proprietor<br>
67 rue Charles de Gaulle, 78350 Jouy-en-Josas, France<br>
SIREN: 981 951 080<br>
SIRET: 981 951 080 00028<br>
VAT number: FR15981951080

A public support email has not yet been published. Until one is added, technical
questions and privacy requests can be submitted through the repository's
[GitHub Issues](https://github.com/HafidIdrissi/Time-Tracker/issues) page. Do not
include private activity data in an issue.
