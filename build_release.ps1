param(
    [string]$Version = ""
)

$ErrorActionPreference = "Stop"
$projectDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExecutable = Join-Path $projectDirectory ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $pythonExecutable)) {
    throw "Python environment not found. Create .venv as described in README.md."
}

$sourceVersion = (& $pythonExecutable -c "import timetracker; print(timetracker.__version__)").Trim()
if (-not $Version) {
    $Version = $sourceVersion
}
if ($Version -notmatch '^\d+\.\d+\.\d+$') {
    throw "The version must use the X.Y.Z format. Received: $Version"
}
if ($Version -ne $sourceVersion) {
    throw "Requested version ($Version) does not match timetracker.__version__ ($sourceVersion)."
}

$signToolPath = $env:TIME_TRACKER_SIGNTOOL
$certificateSha1 = $env:TIME_TRACKER_CERT_SHA1
$signingEnabled = [bool]$signToolPath -and [bool]$certificateSha1
if ([bool]$signToolPath -xor [bool]$certificateSha1) {
    throw "Set TIME_TRACKER_SIGNTOOL and TIME_TRACKER_CERT_SHA1 together."
}
if ($signingEnabled -and -not (Test-Path -LiteralPath $signToolPath)) {
    throw "SignTool not found: $signToolPath"
}

function Invoke-CodeSigning {
    param([string]$FilePath)
    if (-not $signingEnabled) {
        return
    }
    & $signToolPath sign `
        /sha1 $certificateSha1 `
        /fd SHA256 `
        /tr "http://timestamp.digicert.com" `
        /td SHA256 `
        $FilePath
    if ($LASTEXITCODE -ne 0) {
        throw "Signing failed: $FilePath"
    }
    & $signToolPath verify /pa $FilePath
    if ($LASTEXITCODE -ne 0) {
        throw "Invalid signature: $FilePath"
    }
}

Write-Host "Testing version $Version..."
& $pythonExecutable -m unittest discover -v
if ($LASTEXITCODE -ne 0) {
    throw "Tests failed. The release has been cancelled."
}

Write-Host "Building the Windows application..."
& (Join-Path $projectDirectory "build_windows.ps1")
if ($LASTEXITCODE -ne 0) {
    throw "The PyInstaller build failed."
}

$applicationPath = Join-Path $projectDirectory "dist\LocalTimeTracker\LocalTimeTracker.exe"
Invoke-CodeSigning -FilePath $applicationPath

$compilerCandidates = @(
    (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
    (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"),
    (Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe")
)
$innoCompiler = $compilerCandidates |
    Where-Object { $_ -and (Test-Path -LiteralPath $_) } |
    Select-Object -First 1

if (-not $innoCompiler) {
    throw "Inno Setup 6 is required. Install it with: winget install JRSoftware.InnoSetup"
}

Write-Host "Creating the installer..."
Push-Location $projectDirectory
try {
    & $innoCompiler "/DMyAppVersion=$Version" "packaging\installer.iss"
    if ($LASTEXITCODE -ne 0) {
        throw "The Inno Setup build failed."
    }
}
finally {
    Pop-Location
}

$installerPath = Join-Path $projectDirectory "release\LocalTimeTracker-Setup-$Version-x64.exe"
if (-not (Test-Path -LiteralPath $installerPath)) {
    throw "Expected installer not found: $installerPath"
}

Invoke-CodeSigning -FilePath $installerPath

if (-not $signingEnabled) {
    Write-Warning "Unsigned release: suitable for testing and GitHub, but not yet ready for Softonic."
}

$checksum = Get-FileHash -Algorithm SHA256 -LiteralPath $installerPath
$checksumLine = "$($checksum.Hash.ToLowerInvariant()) *$([System.IO.Path]::GetFileName($installerPath))"
$checksumPath = Join-Path $projectDirectory "release\SHA256SUMS.txt"
Set-Content -LiteralPath $checksumPath -Value $checksumLine -Encoding ascii

Write-Host "Release ready: $installerPath"
Write-Host "SHA-256 : $($checksum.Hash.ToLowerInvariant())"
