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
}
finally {
    Pop-Location
}

Write-Host "Application created at dist\LocalTimeTracker\LocalTimeTracker.exe"
