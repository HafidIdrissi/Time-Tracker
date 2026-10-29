# Upgrading a portable installation

**Production instructions:** The commands below affect **your own portable
installation**, not fictional data. Substitute your actual folders and ZIP
paths before executing anything. Stop both copies, keep a verified backup
outside the installation folders, and never overwrite that backup.

**Separate test evidence:** The last section describes only the actual
disposable Windows validation. A v1.3.0-to-v1.3.0 rehearsal is **not** proof
that every other release pair has been tested.

## What the portable folder contains

~~~text
<portable-folder>\
├── LocalTimeTracker.exe
├── portable.mode           marker from the installed release
├── preferences.json        sampling interval / idle threshold (ROOT LEVEL)
├── config.json             optional user category settings
├── data\
│   └── activity.db         activity records, when present
├── reports\                optional prior HTML reports
├── config.example.json     shipped default category configuration
└── _internal\              bundled runtime files
~~~

**Critical correction:** windows_app.py reads and writes
APP_DIRECTORY / "preferences.json", beside LocalTimeTracker.exe. It does
**not** store preferences in data/preferences.json. Preserve the root file
when present, or the real sampling/idle settings will be lost.

The data, reports, config.json, and root preferences.json paths must all be
handled **conditionally**: none is guaranteed to exist in a freshly used
portable installation. The executable and portable.mode must come from the
**new** release, not from the old installation.

## 1. Stop tracking and close both instances

In the old application, click **Stop**, wait for **Stopped**, and close it.
Close the new copy if it is open. Do not run both simultaneously or copy an
open activity database.

To inspect remaining Windows instances without terminating anything:

~~~powershell
Get-CimInstance Win32_Process -Filter "Name = 'LocalTimeTracker.exe'" |
    Select-Object ProcessId, ExecutablePath
~~~

If either old or new executable is listed, close it cleanly before copying.
Do **not** force-kill the tracker to replace its Stop action.

## 2. Set the real paths and reject existing destinations

Use **Windows PowerShell**. Replace every sample path below; choose a backup
location outside both installation folders. The backup, destination, and
rollback paths **must not exist**, even as empty directories:

~~~powershell
$Old = 'C:\YourApps\LocalTimeTracker-old'
$Backup = 'D:\VerifiedBackups\LocalTimeTracker-before-upgrade'
$New = 'C:\YourApps\LocalTimeTracker-new'
$Rollback = 'C:\YourApps\LocalTimeTracker-rollback'
$ReleaseZip = 'C:\Downloads\LocalTimeTracker-NEWVERSION-portable-x64.zip'
$Checksums = 'C:\Downloads\SHA256SUMS.txt'

foreach ($path in @($Old, $ReleaseZip, $Checksums)) {
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Required input missing: $path"
    }
}
foreach ($path in @($Backup, $New, $Rollback)) {
    if (Test-Path -LiteralPath $path) {
        throw "Destination must not exist: $path"
    }
}
~~~

PowerShell Copy-Item -Recurse has different behavior for existing and
nonexistent destination directories; copying to an existing directory can
silently create an additional nested folder. **Do not rerun** the same copy
command with the same destination. Pick another fresh destination and
investigate the earlier failure instead.

Use this helper to compare all existing files and subdirectories by path
and SHA-256. It works for individual files and folders and does not modify
either input:

~~~powershell
function Assert-Preserved([string]$Source, [string]$Target) {
    if (-not (Test-Path -LiteralPath $Target)) {
        throw "Missing destination: $Target"
    }
    if (Test-Path -LiteralPath $Source -PathType Leaf) {
        if (-not (Test-Path -LiteralPath $Target -PathType Leaf) -or
            (Get-FileHash -LiteralPath $Source).Hash -ne
            (Get-FileHash -LiteralPath $Target).Hash) {
            throw "File mismatch: $Source"
        }
        return
    }
    foreach ($dir in Get-ChildItem -LiteralPath $Source -Recurse -Directory -Force) {
        $relative = $dir.FullName.Substring($Source.Length).TrimStart('\')
        if (-not (Test-Path -LiteralPath (Join-Path $Target $relative) -PathType Container)) {
            throw "Missing directory: $relative"
        }
    }
    foreach ($file in Get-ChildItem -LiteralPath $Source -Recurse -File -Force) {
        $relative = $file.FullName.Substring($Source.Length).TrimStart('\')
        $copy = Join-Path $Target $relative
        if (-not (Test-Path -LiteralPath $copy -PathType Leaf) -or
            (Get-FileHash -LiteralPath $file.FullName).Hash -ne
            (Get-FileHash -LiteralPath $copy).Hash) {
            throw "File mismatch: $relative"
        }
    }
}
~~~

## 3. Back up and verify the complete stopped installation

~~~powershell
if (Test-Path -LiteralPath $Backup) { throw 'Backup path already exists' }
Copy-Item -LiteralPath $Old -Destination $Backup -Recurse -ErrorAction Stop
Assert-Preserved $Old $Backup
~~~

Because this copies the **entire** folder, root preferences.json and all
optional user paths are backed up **when present**; the verification does
not require any optional path to exist. Preserve this backup without changes.

## 4. Download and verify the new release

Download the desired ZIP and its SHA256SUMS.txt from
[GitHub Releases](https://github.com/HafidIdrissi/Time-Tracker/releases/latest).
The following checks the ZIP against the entry for its *exact filename*:

~~~powershell
$filename = [IO.Path]::GetFileName($ReleaseZip)
$matchingHashes = @(
    foreach ($entry in Get-Content -LiteralPath $Checksums) {
        # Match 64 hex digits, whitespace, optional * marker, and full filename.
        if ($entry -match '^\s*([0-9A-Fa-f]{64})\s+\*?(.+?)\s*$') {
            $entryName = $Matches[2]
            if ($entryName -ceq $filename) { $Matches[1] }
        }
    }
)
if ($matchingHashes.Count -ne 1) {
    throw "Expected exactly one valid SHA-256 entry for $filename; found $($matchingHashes.Count)"
}
$actual = (Get-FileHash -LiteralPath $ReleaseZip -Algorithm SHA256).Hash
if ($matchingHashes[0] -ine $actual) { throw 'Release ZIP hash mismatch' }
~~~

Do not extract or execute a release whose hash differs.

## 5. Extract separately and copy **only existing** user paths

~~~powershell
if (Test-Path -LiteralPath $New) { throw 'New folder already exists' }
Expand-Archive -LiteralPath $ReleaseZip -DestinationPath $New -ErrorAction Stop

foreach ($name in @('data', 'reports', 'config.json', 'preferences.json')) {
    $source = Join-Path $Old $name
    $destination = Join-Path $New $name
    if (Test-Path -LiteralPath $source) {
        if (Test-Path -LiteralPath $destination) {
            throw "Target already exists: $destination"
        }
        Copy-Item -LiteralPath $source -Destination $destination -Recurse -ErrorAction Stop
        Assert-Preserved $source $destination
    }
}
~~~

The copied root preferences.json retains the original sample interval and
idle threshold. The data folder retains the activity database, reports
retains existing HTML files, and config.json retains custom categories;
each is optional. Leave the new release's LocalTimeTracker.exe,
portable.mode, config.example.json and _internal untouched.

## 6. Start the new copy and manually verify it

Start the **new** LocalTimeTracker.exe only after step 5 has passed. Check
these items in the native Windows application:

1. **Settings:** Compare the visible sampling interval and idle threshold to
   the old **root** preferences.json, if present; otherwise expect defaults.
2. **Reports and data:** Check historical activity and earlier HTML reports
   if the corresponding old paths existed.
3. **Generate and open report:** Select a date with stored activity, generate
   a new report, and check that its HTML contains the expected activity.
4. Confirm the desired tracking status. Stop and close the app before any
   subsequent copy or rollback.

If any check fails, retain the old installation and verified backup. Only
retire the old folder after all checks have passed.

## 7. Roll back into another fresh folder

Stop and close the new application before restoring. Never overwrite the
original backup:

~~~powershell
if (Test-Path -LiteralPath $Rollback) {
    throw 'Rollback target must be a fresh, nonexistent directory'
}
Copy-Item -LiteralPath $Backup -Destination $Rollback -Recurse -ErrorAction Stop
Assert-Preserved $Backup $Rollback
~~~

Only then launch the restored copy. Keep the verified backup unchanged, so
the rollback can be repeated to another fresh destination if necessary.

## Validation performed — Windows test with **fictional data**

On **12 October 2026**, a disposable fixture was created in a **new Windows
temporary folder**. The genuine v1.3.0 portable ZIP was downloaded and
verified against its published SHA256SUMS.txt. Windows 11 build 26200,
**native Windows PowerShell 5.1**, and the real v1.3.0 Windows executable
were used.

- **Fixture generation:** WSL Python created one fictional 15-minute
  period in a SQLite activity.db, an old fictional HTML report, config.json
  and **root** preferences.json with sample_seconds="5" and
  idle_minutes="10". No actual user activity was read.
- **Windows commands actually run:** Get-FileHash verified the ZIP;
  Copy-Item backed up the complete 1.3.0 fixture to a **fresh** directory;
  hashes of all **1,004 files** matched. Expand-Archive extracted the
  release ZIP into another fresh directory. Native Copy-Item carried
  data, reports, config.json and **root preferences.json** to the new
  folder, with successful SHA-256 comparisons for each copied file.
  Restoring the entire backup into a new rollback folder produced
  **1,004 matching files**; rechecking confirmed the backup was unchanged.
  The new release's executable and portable.mode were retained.
- **Native packaged executable smoke test:** LocalTimeTracker.exe v1.3.0
  launched on the disposable Windows system and exposed a window titled
  "Local Time Tracker 1.3.0"; the test process was closed. The Windows
  accessibility tree did not expose the Tk controls in this packaged
  executable, so mouse/keyboard inspection of that *packaged executable*
  was not completed.
- **Windows Tk GUI code-path verification (13 October 2026 TR):**
  An isolated [successful Windows Actions run](https://github.com/Furox-Art/Time-Tracker/actions/runs/38317255364)
  used Windows Python 3.12 with the repository's actual v1.3.0
  windows_app.py native Tk widgets, extracted the official v1.3.0
  portable ZIP into disposable folders, and used fictional data only.
  It checked the rendered settings combobox values were **5 seconds**
  and **10 minutes**, used the actual Tk report button's invoke method
  on the "Reports and data" tab, and verified the generated HTML
  contained the fictional 15-minute "Fictional Editor" period.
  After closing the Tk window, a fresh restored copy retained the same
  visible settings and original fictional SQLite period. Automatic
  tracking was disabled in this test to avoid recording real activity.
  This is programmatic **native Windows Tk application UI-path**
  validation, *not* a physical mouse-click walkthrough of the packaged
  LocalTimeTracker.exe binary.
- **Optional-paths-absent case:** A separate native PowerShell check
  copied the data directory while reports, config.json, and root
  preferences.json were absent. All three optional paths were skipped,
  the existing data was copied, and no nested data/data folder was created.
- **Limits:** This was a **v1.3.0-to-v1.3.0 migration rehearsal**;
  no cross-version upgrade was exercised. The packaged binary's
  manual UI controls were not clicked. The earlier WSL/Linux copy
  checks are not presented as Windows execution. A separate
  [Windows PowerShell CI run](https://github.com/Furox-Art/Time-Tracker/actions/runs/38316721144)
  executed the documented checksum block with **eight passed cases**:
  genuine release manifest, optional binary/text markers, and correct
  rejection of missing, duplicate, suffix-only, wrong-hash and
  invalid-hash entries. These fork validation runs do not replace
  upstream PR CI; upstream maintainer authorization may still be needed.

Never publish a real activity.db, personal reports, or screenshots containing
private window titles.
