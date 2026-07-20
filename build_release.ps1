param(
    [string]$Version = ""
)

$ErrorActionPreference = "Stop"
$projectDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExecutable = Join-Path $projectDirectory ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $pythonExecutable)) {
    throw "Environnement Python introuvable. Créez .venv comme indiqué dans README.md."
}

$sourceVersion = (& $pythonExecutable -c "import timetracker; print(timetracker.__version__)").Trim()
if (-not $Version) {
    $Version = $sourceVersion
}
if ($Version -notmatch '^\d+\.\d+\.\d+$') {
    throw "La version doit utiliser le format X.Y.Z. Valeur reçue : $Version"
}
if ($Version -ne $sourceVersion) {
    throw "La version demandée ($Version) ne correspond pas à timetracker.__version__ ($sourceVersion)."
}

$signToolPath = $env:TIME_TRACKER_SIGNTOOL
$certificateSha1 = $env:TIME_TRACKER_CERT_SHA1
$signingEnabled = [bool]$signToolPath -and [bool]$certificateSha1
if ([bool]$signToolPath -xor [bool]$certificateSha1) {
    throw "Définissez TIME_TRACKER_SIGNTOOL et TIME_TRACKER_CERT_SHA1 ensemble."
}
if ($signingEnabled -and -not (Test-Path -LiteralPath $signToolPath)) {
    throw "SignTool introuvable : $signToolPath"
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
        throw "Échec de la signature : $FilePath"
    }
    & $signToolPath verify /pa $FilePath
    if ($LASTEXITCODE -ne 0) {
        throw "Signature invalide : $FilePath"
    }
}

Write-Host "Tests de la version $Version..."
& $pythonExecutable -m unittest discover -v
if ($LASTEXITCODE -ne 0) {
    throw "Les tests ont échoué. La release est annulée."
}

Write-Host "Construction de l'application Windows..."
& (Join-Path $projectDirectory "build_windows.ps1")
if ($LASTEXITCODE -ne 0) {
    throw "La construction PyInstaller a échoué."
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
    throw "Inno Setup 6 est requis. Installez-le avec : winget install JRSoftware.InnoSetup"
}

Write-Host "Création de l'installateur..."
Push-Location $projectDirectory
try {
    & $innoCompiler "/DMyAppVersion=$Version" "packaging\installer.iss"
    if ($LASTEXITCODE -ne 0) {
        throw "La compilation Inno Setup a échoué."
    }
}
finally {
    Pop-Location
}

$installerPath = Join-Path $projectDirectory "release\LocalTimeTracker-Setup-$Version-x64.exe"
if (-not (Test-Path -LiteralPath $installerPath)) {
    throw "Installateur attendu introuvable : $installerPath"
}

Invoke-CodeSigning -FilePath $installerPath

if (-not $signingEnabled) {
    Write-Warning "Release non signée : utilisable pour les tests et GitHub, mais pas encore prête pour Softonic."
}

$checksum = Get-FileHash -Algorithm SHA256 -LiteralPath $installerPath
$checksumLine = "$($checksum.Hash.ToLowerInvariant()) *$([System.IO.Path]::GetFileName($installerPath))"
$checksumPath = Join-Path $projectDirectory "release\SHA256SUMS.txt"
Set-Content -LiteralPath $checksumPath -Value $checksumLine -Encoding ascii

Write-Host "Release prête : $installerPath"
Write-Host "SHA-256 : $($checksum.Hash.ToLowerInvariant())"
