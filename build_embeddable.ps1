#Requires -Version 5.1
<#
.SYNOPSIS
    Build: Python Embeddable + Inno Setup Installer cho VCFE Database.
.NOTES
    Yeu cau: Inno Setup 6  https://jrsoftware.org/isinfo.php
    Chay:    .\build_embeddable.ps1
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference    = "SilentlyContinue"

# -- Cau hinh ----------------------------------------------------------------
$PYTHON_VERSION = "3.12.9"
$APP_VERSION    = "2.0.0"
$APP_NAME       = "VCFE Database"

$Root         = $PSScriptRoot
$DistDir      = "$Root\dist"
$PythonDir    = "$DistDir\python"
$CacheDir     = "$Root\.build_cache"
$InstallerDir = "$Root\installer"

# -- Helper ------------------------------------------------------------------
function Write-Step([int]$n, [int]$total, [string]$msg) {
    Write-Host ""
    Write-Host "[$n/$total] $msg" -ForegroundColor Cyan
}
function Write-Ok([string]$msg)   { Write-Host "      OK  : $msg" -ForegroundColor Green  }
function Write-Warn([string]$msg) { Write-Host "      WARN: $msg" -ForegroundColor Yellow }
function Write-Err([string]$msg)  { Write-Host "      LOI : $msg" -ForegroundColor Red    }

# ---------------------------------------------------------------------------

Write-Host ""
Write-Host "====================================================" -ForegroundColor Magenta
Write-Host "  Build $APP_NAME Installer  v$APP_VERSION" -ForegroundColor Magenta
Write-Host "====================================================" -ForegroundColor Magenta

# -- Buoc 1: Xoa dist cu, tao thu muc moi ------------------------------------
Write-Step 1 5 "Chuan bi thu muc dist..."

if (Test-Path $DistDir) {
    Remove-Item -Recurse -Force $DistDir
}
New-Item -ItemType Directory -Path $DistDir                    | Out-Null
New-Item -ItemType Directory -Path $PythonDir                  | Out-Null
New-Item -ItemType Directory -Path $CacheDir -Force            | Out-Null
New-Item -ItemType Directory -Path "$DistDir\data\uploads" -Force | Out-Null

Write-Ok "dist\ san sang"

# -- Buoc 2: Tai Python embeddable (cache neu co san) ------------------------
Write-Step 2 5 "Chuan bi Python $PYTHON_VERSION embeddable..."

$ZipName = "python-$PYTHON_VERSION-embed-amd64.zip"
$ZipPath = "$CacheDir\$ZipName"
$ZipUrl  = "https://www.python.org/ftp/python/$PYTHON_VERSION/$ZipName"

if (-not (Test-Path $ZipPath)) {
    Write-Host "      Dang tai $ZipUrl ..." -ForegroundColor DarkCyan
    Invoke-WebRequest -Uri $ZipUrl -OutFile $ZipPath -UseBasicParsing
    Write-Ok "Tai thanh cong: $ZipName"
} else {
    Write-Ok "Dung ban cache : $ZipName"
}

Write-Host "      Dang giai nen..." -ForegroundColor DarkCyan
Expand-Archive -Path $ZipPath -DestinationPath $PythonDir -Force

# Bat site-packages: bo comment "#import site" trong file _pth
$PthFile = Get-ChildItem "$PythonDir" -Filter "python3*._pth" | Select-Object -First 1
if (-not $PthFile) {
    Write-Err "Khong tim thay file _pth trong ban embeddable."
    exit 1
}
$pthContent = Get-Content $PthFile.FullName -Raw
$pthContent = $pthContent -replace "#import site", "import site"
[System.IO.File]::WriteAllText($PthFile.FullName, $pthContent, [System.Text.Encoding]::ASCII)
Write-Ok "Bat site-packages: $($PthFile.Name)"

# -- Buoc 3: Copy goi tu venv312 (cung phien ban Python, khong can mang) -----
Write-Step 3 5 "Sao chep goi Python tu venv312..."

$VenvSitePkgs = "$Root\venv312\Lib\site-packages"
$DistSitePkgs = "$PythonDir\Lib\site-packages"

if (-not (Test-Path $VenvSitePkgs)) {
    Write-Err "Khong tim thay venv312\Lib\site-packages. Chay: python -m venv venv312 && venv312\Scripts\pip install -r requirements.txt"
    exit 1
}

New-Item -ItemType Directory -Path $DistSitePkgs -Force | Out-Null

# Cac goi chi dung de test, loai bo khoi ban phan phoi
# (khong loai anyio/exceptiongroup -- FastAPI/starlette can chung)
$ExcludePrefixes = @(
    "pytest", "_pytest", "pluggy", "iniconfig",
    "httpx", "httpcore", "h11"
)

$AllItems = Get-ChildItem $VenvSitePkgs
$Copied = 0

foreach ($item in $AllItems) {
    $skip = $false
    foreach ($prefix in $ExcludePrefixes) {
        if ($item.Name -like "$prefix*") { $skip = $true; break }
    }
    if ($skip) { continue }

    Copy-Item $item.FullName "$DistSitePkgs\$($item.Name)" -Recurse -Force
    $Copied++
}

Write-Ok "Sao chep $Copied muc tu venv312\Lib\site-packages"

# Xoa __pycache__ trong site-packages de giam kich thuoc
Get-ChildItem -Path $DistSitePkgs -Recurse -Filter "__pycache__" -Directory |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# -- Buoc 4: Chep ma nguon ung dung ------------------------------------------
Write-Step 4 5 "Chep ma nguon ung dung..."

# Tao logo.ico tu logo.png (Inno Setup can .ico cho shortcut)
$LogoPng = "$Root\frontend\static\img\logo.png"
$LogoIco = "$Root\frontend\static\img\logo.ico"
if (Test-Path $LogoPng) {
    & "$Root\venv312\Scripts\python.exe" -c @"
from PIL import Image
img = Image.open(r'$LogoPng').convert('RGBA')
img.save(r'$LogoIco', format='ICO', sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
"@
    if (Test-Path $LogoIco) { Write-Ok "logo.ico da tao tu logo.png" }
    else { Write-Warn "Khong tao duoc logo.ico, shortcut se dung icon mac dinh" }
}

foreach ($dir in @("backend", "frontend")) {
    $src = "$Root\$dir"
    if (Test-Path $src) {
        Copy-Item -Path $src -Destination "$DistDir\$dir" -Recurse -Force
        Write-Ok "Chep: $dir\"
    } else {
        Write-Warn "Khong tim thay: $dir\ (bo qua)"
    }
}

# Xoa __pycache__ va .pyc
Get-ChildItem -Path $DistDir -Recurse -Filter "__pycache__" -Directory |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path $DistDir -Recurse -Filter "*.pyc" |
    Remove-Item -Force -ErrorAction SilentlyContinue

# Chep launcher va wizard
Copy-Item "$InstallerDir\Start.bat"    "$DistDir\Start.bat"    -Force
Copy-Item "$InstallerDir\first_run.py" "$DistDir\first_run.py" -Force

# Placeholder cho thu muc data rong
$null = New-Item -ItemType File -Path "$DistDir\data\uploads\.gitkeep" -Force

Write-Ok "Ma nguon da chep xong"

# -- Buoc 5: Bien dich installer bang Inno Setup -----------------------------
Write-Step 5 5 "Bien dich installer voi Inno Setup..."

$ISSCCandidates = @(
    "D:\Inno Setup 6\ISCC.exe",
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe",
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
)
$ISCC = $ISSCCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

# Neu khong tim thay o duong dan chuan, tim dong trong toan bo o C:
if (-not $ISCC) {
    $found = cmd /c "where ISCC.exe 2>nul"
    if ($found) { $ISCC = $found.Trim() }
}
if (-not $ISCC) {
    $found = cmd /c "dir /s /b C:\ISCC.exe 2>nul" | Select-Object -First 1
    if ($found) { $ISCC = $found.Trim() }
}

if ($ISCC) {
    Write-Host "      Tim thay Inno Setup: $ISCC" -ForegroundColor DarkCyan
    & $ISCC "$InstallerDir\vcfe.iss"
    if ($LASTEXITCODE -ne 0) {
        Write-Err "Inno Setup bao loi. Kiem tra log phia tren."
        exit 1
    }
    Write-Host ""
    Write-Host "====================================================" -ForegroundColor Green
    Write-Host "  HOAN TAT: dist\Output\Setup_VCFE_v$APP_VERSION.exe" -ForegroundColor Green
    Write-Host "====================================================" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Warn "Khong tim thay Inno Setup 6."
    Write-Host ""
    Write-Host "  Tai va cai dat Inno Setup 6:" -ForegroundColor Yellow
    Write-Host "  https://jrsoftware.org/isinfo.php" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Sau do chay lai script nay," -ForegroundColor Yellow
    Write-Host "  hoac mo installer\vcfe.iss trong Inno Setup IDE." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  (Thu muc dist\ da san sang, chi thieu buoc dong goi .exe)" -ForegroundColor DarkGray
    Write-Host ""
}
