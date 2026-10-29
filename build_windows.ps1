param(
    [switch]$SkipPortable
)

$ErrorActionPreference = "Stop"
$projectDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExecutable = Join-Path $projectDirectory ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $pythonExecutable)) {
    throw "Python environment not found. Create .venv as described in README.md."
}

Push-Location $projectDirectory
try {
    $versionOutput = & $pythonExecutable -c "import timetracker; print(timetracker.__version__)"
    if ($LASTEXITCODE -ne 0 -or -not $versionOutput) {
        throw "Unable to read the source version. The application build was not started."
    }
    $version = ([string]$versionOutput).Trim()

    & $pythonExecutable -c "import importlib.util; raise SystemExit(0 if importlib.util.find_spec('PyInstaller') else 1)"
    if ($LASTEXITCODE -ne 0) {
        & $pythonExecutable -m pip install "pyinstaller>=6,<7"
        if ($LASTEXITCODE -ne 0) { throw "PyInstaller installation failed." }
    }

    # Keep Windows executable metadata aligned with the Python source version.
    $metadata = Get-Content -LiteralPath "packaging\version_info.txt" -Raw
    $tuple = ($version.Split(".") + @("0")) -join ", "
    $metadata = $metadata -replace '(?m)(filevers|prodvers)=\([^)]*\)', ('$1=(' + $tuple + ')')
    $metadata = $metadata -replace "(StringStruct\('(FileVersion|ProductVersion)', ')[^']*('\))", ('${1}' + $version + '${3}')
    $metadataPath = Join-Path $projectDirectory "build\version_info.txt"
    New-Item -ItemType Directory -Path (Split-Path -Parent $metadataPath) -Force | Out-Null
    Set-Content -LiteralPath $metadataPath -Value $metadata -Encoding utf8

    & $pythonExecutable -m PyInstaller `
        --noconfirm `
        --clean `
        --windowed `
        --name "LocalTimeTracker" `
        --icon "assets\app-icon.ico" `
        --version-file $metadataPath `
        --add-data "config.example.json;." `
        windows_app.py
    if ($LASTEXITCODE -ne 0) { throw "The PyInstaller build failed." }

    if (-not $SkipPortable) {
        & (Join-Path $projectDirectory "build_portable.ps1") -Version $version
    }
}
finally {
    Pop-Location
}
Write-Host "Application created at dist\LocalTimeTracker\LocalTimeTracker.exe"
