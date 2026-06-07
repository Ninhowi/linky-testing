# install-allure.ps1
# Run as Administrator

$ErrorActionPreference = "Stop"

$InstallDir = "C:\Program Files\Allure"
$TempDir = Join-Path $env:TEMP "allure-install"
$ZipPath = Join-Path $TempDir "allure.zip"

Write-Host "==> Checking Administrator permission..."

$isAdmin = ([Security.Principal.WindowsPrincipal] `
    [Security.Principal.WindowsIdentity]::GetCurrent()
).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    throw "Please run PowerShell as Administrator."
}

Write-Host "==> Checking JAVA_HOME..."

if (-not $env:JAVA_HOME) {
    Write-Warning "JAVA_HOME is not set. Allure requires Java 8+."
    Write-Warning "Install Java first, then set JAVA_HOME."
}

Write-Host "==> Getting latest Allure release from GitHub..."

$LatestRelease = Invoke-RestMethod `
    -Uri "https://api.github.com/repos/allure-framework/allure2/releases/latest" `
    -Headers @{ "User-Agent" = "PowerShell" }

$Version = $LatestRelease.tag_name
$Asset = $LatestRelease.assets | Where-Object {
    $_.name -match "^allure-.*\.zip$"
} | Select-Object -First 1

if (-not $Asset) {
    throw "Cannot find allure-*.zip asset in latest release."
}

Write-Host "==> Latest version: $Version"
Write-Host "==> Downloading: $($Asset.browser_download_url)"

Remove-Item $TempDir -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $TempDir | Out-Null

Invoke-WebRequest `
    -Uri $Asset.browser_download_url `
    -OutFile $ZipPath `
    -Headers @{ "User-Agent" = "PowerShell" }

Write-Host "==> Extracting..."

$ExtractDir = Join-Path $TempDir "extract"
New-Item -ItemType Directory -Path $ExtractDir | Out-Null

Expand-Archive -Path $ZipPath -DestinationPath $ExtractDir -Force

$ExtractedAllureDir = Get-ChildItem -Path $ExtractDir -Directory |
    Where-Object { $_.Name -match "^allure-" } |
    Select-Object -First 1

if (-not $ExtractedAllureDir) {
    throw "Cannot find extracted allure-* folder."
}

Write-Host "==> Installing to: $InstallDir"

Remove-Item $InstallDir -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $InstallDir | Out-Null

Copy-Item -Path (Join-Path $ExtractedAllureDir.FullName "*") `
    -Destination $InstallDir `
    -Recurse `
    -Force

$AllureBin = Join-Path $InstallDir "bin"

if (-not (Test-Path $AllureBin)) {
    throw "Allure bin directory not found: $AllureBin"
}

Write-Host "==> Updating System PATH..."

$CurrentPath = [Environment]::GetEnvironmentVariable("Path", "Machine")

$PathParts = $CurrentPath -split ";" | Where-Object {
    $_ -and
    $_ -ne $AllureBin -and
    $_ -notmatch "\\Allure\\bin$" -and
    $_ -notmatch "\\allure-[^\\]+\\bin$"
}

$NewPath = ($PathParts + $AllureBin) -join ";"

[Environment]::SetEnvironmentVariable("Path", $NewPath, "Machine")

Write-Host "==> Cleaning temp files..."
Remove-Item $TempDir -Recurse -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "Allure installed successfully."
Write-Host "Version: $Version"
Write-Host "Path: $InstallDir"
Write-Host ""
Write-Host "Close and reopen PowerShell, then run:"
Write-Host "allure --version"