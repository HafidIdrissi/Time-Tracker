$ErrorActionPreference = "Stop"

$projectDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExecutable = Join-Path $projectDirectory ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $pythonExecutable)) {
    throw "Python environment not found. Create .venv as described in README.md."
}

& $pythonExecutable -c "import importlib.util; raise SystemExit(0 if importlib.util.find_spec('PyInstaller') else 1)"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing PyInstaller..."
    & $pythonExecutable -m pip install "pyinstaller>=6,<7"
}

$version = (& $pythonExecutable -c "import timetracker; print(timetracker.__version__)").Trim()
$releaseDirectory = Join-Path $projectDirectory "release"
$portableDirectory = Join-Path $projectDirectory "dist\LocalTimeTracker"
$portableStagingDirectory = Join-Path $projectDirectory "dist\LocalTimeTracker-portable"
$portableZip = Join-Path $releaseDirectory "LocalTimeTracker-$version-portable-x64.zip"

Push-Location $projectDirectory
try {
    & $pythonExecutable -m PyInstaller `
        --noconfirm `
        --clean `
        --windowed `
        --name "LocalTimeTracker" `
        --version-file "packaging\version_info.txt" `
        --add-data "config.example.json;." `
        windows_app.py

    if ($LASTEXITCODE -ne 0) {
        throw "The PyInstaller build failed."
    }
}
finally {
    Pop-Location
}

if (-not (Test-Path -LiteralPath (Join-Path $portableDirectory "LocalTimeTracker.exe"))) {
    throw "Expected application executable not found: $portableDirectory\LocalTimeTracker.exe"
}

if (Test-Path -LiteralPath $portableStagingDirectory) {
    Remove-Item -LiteralPath $portableStagingDirectory -Recurse -Force
}

New-Item -ItemType Directory -Path $portableStagingDirectory | Out-Null

Copy-Item `
    -Path (Join-Path $portableDirectory "*") `
    -Destination $portableStagingDirectory `
    -Recurse `
    -Force

New-Item `
    -ItemType File `
    -Path (Join-Path $portableStagingDirectory "portable.mode") `
    -Force | Out-Null

$portableNoticeTemplate = Join-Path $projectDirectory "packaging\PORTABLE_NOTICE.txt"
$portableNotice = Get-Content -LiteralPath $portableNoticeTemplate -Raw
$portableNotice = $portableNotice.Replace("{{VERSION}}", $version)

Set-Content `
    -LiteralPath (Join-Path $portableStagingDirectory "PORTABLE_NOTICE.txt") `
    -Value $portableNotice `
    -Encoding utf8

Copy-Item `
    -LiteralPath (Join-Path $projectDirectory "config.example.json") `
    -Destination $portableStagingDirectory `
    -Force

Copy-Item `
    -LiteralPath (Join-Path $projectDirectory "LICENSE") `
    -Destination $portableStagingDirectory `
    -Force

Copy-Item `
    -LiteralPath (Join-Path $projectDirectory "PRIVACY.md") `
    -Destination $portableStagingDirectory `
    -Force

Copy-Item `
    -LiteralPath (Join-Path $projectDirectory "CHANGELOG.md") `
    -Destination $portableStagingDirectory `
    -Force

Copy-Item `
    -LiteralPath (Join-Path $projectDirectory "LEGAL.md") `
    -Destination $portableStagingDirectory `
    -Force

Write-Host "Creating portable archive..."
New-Item -ItemType Directory -Path $releaseDirectory -Force | Out-Null

if (Test-Path -LiteralPath $portableZip) {
    Remove-Item -LiteralPath $portableZip -Force
}

Add-Type -AssemblyName System.IO.Compression.FileSystem

[System.IO.Compression.ZipFile]::CreateFromDirectory(
    $portableStagingDirectory,
    $portableZip,
    [System.IO.Compression.CompressionLevel]::Optimal,
    $false
)

if (-not (Test-Path -LiteralPath $portableZip)) {
    throw "Expected portable archive not found: $portableZip"
}

Write-Host "Application created at dist\LocalTimeTracker\LocalTimeTracker.exe"
Write-Host "Portable archive created at $portableZip"
