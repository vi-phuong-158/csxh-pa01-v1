<#
.SYNOPSIS
    Ky so (Authenticode) cho QLNNN.exe va file installer.
    Su dung chung chi trong Windows cert store (tao boi setup_codesign.ps1).

.PARAMETER Target
    "exe"       - Chi ky QLNNN.exe trong dist\QLNNN\
    "installer" - Chi ky file setup trong dist\installer\
    "all"       - Ky ca hai (mac dinh)

.EXAMPLE
    .\sign_release.ps1
    .\sign_release.ps1 -Target exe
    .\sign_release.ps1 -Target installer
#>
param(
    [ValidateSet("exe","installer","all")]
    [string]$Target = "all"
)

$ErrorActionPreference = "Stop"
$ROOT = Split-Path $PSScriptRoot -Parent

# -----------------------------------------------------------------------
# 1. Tim signtool.exe
# -----------------------------------------------------------------------
function Find-SignTool {
    $searchRoots = @(
        "C:\Program Files (x86)\Windows Kits\10\bin",
        "C:\Program Files\Windows Kits\10\bin"
    )
    foreach ($root in $searchRoots) {
        if (-not (Test-Path $root)) { continue }
        $found = Get-ChildItem -Path $root -Recurse -Filter "signtool.exe" -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -like "*x64*" } |
            Sort-Object FullName -Descending |
            Select-Object -First 1 -ExpandProperty FullName
        if ($found) { return $found }
    }

    # Thu tim trong PATH
    $inPath = Get-Command signtool.exe -ErrorAction SilentlyContinue
    if ($inPath) { return $inPath.Source }

    return $null
}

# -----------------------------------------------------------------------
# 2. Tim chung chi trong cert store
# -----------------------------------------------------------------------
function Find-SigningCert {
    # Uu tien thumbprint da luu boi setup_codesign.ps1
    $thumbprintFile = Join-Path $PSScriptRoot ".cert_thumbprint"
    if (Test-Path $thumbprintFile) {
        $thumb = (Get-Content $thumbprintFile -Raw).Trim()
        $cert = Get-ChildItem "Cert:\LocalMachine\My\$thumb" -ErrorAction SilentlyContinue
        if ($cert) { return $cert }
        $cert = Get-ChildItem "Cert:\CurrentUser\My\$thumb" -ErrorAction SilentlyContinue
        if ($cert) { return $cert }
    }

    # Tim theo subject name
    foreach ($store in @("Cert:\LocalMachine\My", "Cert:\CurrentUser\My")) {
        $cert = Get-ChildItem $store -ErrorAction SilentlyContinue |
            Where-Object {
                $_.Subject -like "*Quan Ly Nguoi Nuoc Ngoai*" -and
                $_.HasPrivateKey -and
                $_.NotAfter -gt (Get-Date) -and
                ($_.Extensions | Where-Object { $_.Oid.Value -eq "2.5.29.37" } |
                    ForEach-Object { $_.EnhancedKeyUsages | Where-Object { $_.Value -eq "1.3.6.1.5.5.7.3.3" } })
            } |
            Sort-Object NotAfter -Descending |
            Select-Object -First 1
        if ($cert) { return $cert }
    }
    return $null
}

# -----------------------------------------------------------------------
# 3. Ky mot file
# -----------------------------------------------------------------------
function Sign-File {
    param([string]$signTool, [string]$thumbprint, [string]$filePath)

    if (-not (Test-Path $filePath)) {
        Write-Host "  [skip] Khong tim thay: $(Split-Path $filePath -Leaf)" -ForegroundColor Yellow
        return $true
    }

    $fileName = Split-Path $filePath -Leaf
    Write-Host "  [>] Dang ky: $fileName" -ForegroundColor White

    $args = @(
        "sign",
        "/sha1", $thumbprint,
        "/fd",   "sha256",
        "/tr",   "http://timestamp.sectigo.com",
        "/td",   "sha256",
        "/v",    $filePath
    )

    $output = & $signTool @args 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  [x] Ky that bai: $fileName" -ForegroundColor Red
        Write-Host $output -ForegroundColor DarkRed
        return $false
    }

    Write-Host "  [OK] Da ky thanh cong: $fileName" -ForegroundColor Green
    return $true
}

# -----------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  KY SO AUTHENTICODE - QLNNN" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Tim signtool
$signTool = Find-SignTool
if (-not $signTool) {
    Write-Host "[!] Khong tim thay signtool.exe." -ForegroundColor Red
    Write-Host "    Cai Windows SDK tai:" -ForegroundColor Red
    Write-Host "    https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/" -ForegroundColor Yellow
    exit 1
}
Write-Host "[OK] signtool: $signTool" -ForegroundColor DarkGray

# Tim cert
$cert = Find-SigningCert
if (-not $cert) {
    Write-Host "[!] Khong tim thay chung chi ky so trong cert store." -ForegroundColor Red
    Write-Host "    Chay setup_codesign.ps1 truoc (voi quyen Administrator)." -ForegroundColor Yellow
    exit 1
}
Write-Host "[OK] Chung chi: $($cert.Subject)" -ForegroundColor DarkGray
Write-Host "     Thumbprint: $($cert.Thumbprint)" -ForegroundColor DarkGray
Write-Host ""

$allOk = $true

# Ky QLNNN.exe
if ($Target -in @("exe", "all")) {
    Write-Host "[Buoc 1] Ky QLNNN.exe..." -ForegroundColor Cyan
    $exePath = Join-Path $ROOT "dist\QLNNN\QLNNN.exe"
    if (-not (Sign-File $signTool $cert.Thumbprint $exePath)) { $allOk = $false }
    Write-Host ""
}

# Ky installer
if ($Target -in @("installer", "all")) {
    Write-Host "[Buoc 2] Ky file installer..." -ForegroundColor Cyan
    $installerDir = Join-Path $ROOT "dist\installer"
    if (Test-Path $installerDir) {
        $installers = Get-ChildItem $installerDir -Filter "QLNNN_Setup_*.exe" |
            Sort-Object LastWriteTime -Descending
        if ($installers) {
            foreach ($ins in $installers) {
                if (-not (Sign-File $signTool $cert.Thumbprint $ins.FullName)) { $allOk = $false }
            }
        } else {
            Write-Host "  [skip] Chua co file installer trong dist\installer\" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  [skip] Thu muc dist\installer\ chua ton tai." -ForegroundColor Yellow
    }
    Write-Host ""
}

# Ket qua
if ($allOk) {
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "  KY SO HOAN TAT - File san sang phan phoi!" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "  LUU Y: Nguoi dung can cai QLNNN_codesign.cer truoc khi chay" -ForegroundColor Yellow
    Write-Host "  (chay deploy_cert.ps1 hoac trien khai qua Group Policy)" -ForegroundColor Yellow
} else {
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host "  CO LOI KHI KY SO - Kiem tra lai!" -ForegroundColor Red
    Write-Host "============================================================" -ForegroundColor Red
    exit 1
}

Write-Host ""
