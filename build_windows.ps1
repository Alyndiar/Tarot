param(
    [switch]$Clean
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

$ProjectName = Split-Path -Leaf $ProjectRoot
$DistDir = Join-Path $ProjectRoot "dist"
$BuildDir = Join-Path $ProjectRoot "build"

if ($Clean) {
    if (Test-Path $DistDir) { Remove-Item -Recurse -Force $DistDir }
    if (Test-Path $BuildDir) { Remove-Item -Recurse -Force $BuildDir }
}

$HasConda = $null -ne (Get-Command conda -ErrorAction SilentlyContinue)

if ($HasConda) {
    Write-Host "Conda détecté. Environnement: $ProjectName"
    conda create -y -n $ProjectName python=3.12
    conda run -n $ProjectName python -m pip install --upgrade pip
    conda run -n $ProjectName python -m pip install -r requirements.txt pyinstaller
    conda run -n $ProjectName pyinstaller `
        --noconfirm `
        --clean `
        --windowed `
        --name TarotDealerMarseille `
        --add-data "assets;assets" `
        --add-data "config;config" `
        run.py
}
else {
    Write-Host "Conda non détecté. Utilisation d'un venv local."
    $VenvPath = Join-Path $ProjectRoot ".venv"
    if (-not (Test-Path $VenvPath)) {
        python -m venv $VenvPath
    }
    $Py = Join-Path $VenvPath "Scripts\\python.exe"
    & $Py -m pip install --upgrade pip
    & $Py -m pip install -r requirements.txt pyinstaller
    & (Join-Path $VenvPath "Scripts\\pyinstaller.exe") `
        --noconfirm `
        --clean `
        --windowed `
        --name TarotDealerMarseille `
        --add-data "assets;assets" `
        --add-data "config;config" `
        run.py
}

Write-Host "Build terminé. Sortie: $DistDir"

