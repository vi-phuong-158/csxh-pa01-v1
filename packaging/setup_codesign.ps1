#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Tao chung chi ky so (self-signed) de ky ung dung QLNNN.
    Chay MOT LAN DUNG trên may build voi quyen Administrator.

.OUTPUTS
    packaging\QLNNN_codesign.pfx  - file PFX de ky (giu bi mat)
    packaging\QLNNN_codesign.cer  - public cert de cai len may nguoi dung

.NOTES
    Sau buoc nay chay sign_release.ps1 de ky exe va installer.
    De cai cert len may nguoi dung, chay deploy_cert.ps1.
#>

$ErrorActionPreference = "Stop"

$CERT_SUBJECT  = "CN=Quan Ly Nguoi Nuoc Ngoai, O=Phong An ninh doi ngoai, C=VN"
$FRIENDLY_NAME = "QLNNN Code Signing"
$PFX_PATH      = Join-Path $PSScriptRoot "QLNNN_codesign.pfx"
$CER_PATH      = Join-Path $PSScriptRoot "QLNNN_codesign.cer"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  TAO CHUNG CHI KY SO CHO QLNNN" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Kiem tra neu cert da ton tai trong store
$existing = Get-ChildItem "Cert:\LocalMachine\My" -ErrorAction SilentlyContinue |
    Where-Object { $_.Subject -like "*Quan Ly Nguoi Nuoc Ngoai*" -and $_.HasPrivateKey }

if ($existing) {
    Write-Host "[i] Da tim thay chung chi cu: $($existing.Thumbprint)" -ForegroundColor Yellow
    $choice = Read-Host "Tao lai chung chi moi? (y/N)"
    if ($choice -notmatch "^[Yy]") {
        Write-Host "[>] Giu nguyen chung chi hien tai." -ForegroundColor Green
        $cert = $existing | Select-Object -First 1
    } else {
        $existing | ForEach-Object { Remove-Item "Cert:\LocalMachine\My\$($_.Thumbprint)" -Force }
        $cert = $null
    }
}

if (-not $cert) {
    Write-Host "[>] Dang tao self-signed code signing certificate..." -ForegroundColor White
    $cert = New-SelfSignedCertificate `
        -Type          CodeSigningCert `
        -Subject       $CERT_SUBJECT `
        -KeyUsage      DigitalSignature `
        -FriendlyName  $FRIENDLY_NAME `
        -CertStoreLocation "Cert:\LocalMachine\My" `
        -HashAlgorithm SHA256 `
        -NotAfter      (Get-Date).AddYears(5) `
        -KeyLength     2048

    Write-Host "[OK] Tao chung chi thanh cong." -ForegroundColor Green
}

Write-Host "    Thumbprint : $($cert.Thumbprint)"
Write-Host "    Het han    : $($cert.NotAfter.ToString('dd/MM/yyyy'))"
Write-Host ""

# Them vao Trusted Publishers va Root CA cua may build
foreach ($storeName in @("TrustedPublisher", "Root")) {
    $store = New-Object System.Security.Cryptography.X509Certificates.X509Store($storeName, "LocalMachine")
    $store.Open("ReadWrite")
    if (-not ($store.Certificates | Where-Object { $_.Thumbprint -eq $cert.Thumbprint })) {
        $store.Add($cert)
        Write-Host "[OK] Da them vao LocalMachine\$storeName" -ForegroundColor Green
    } else {
        Write-Host "[i] Da co trong LocalMachine\$storeName" -ForegroundColor Yellow
    }
    $store.Close()
}

Write-Host ""

# Xuat file PFX (co private key) de dung voi signtool
Write-Host "[>] Xuat file PFX (can mat khau de bao ve private key)..." -ForegroundColor White
Write-Host "    (Nhan Enter de bo trong mat khau - khong khuyen khich)" -ForegroundColor DarkGray
$pfxPwd = Read-Host "    Mat khau PFX" -AsSecureString

Export-PfxCertificate -Cert $cert -FilePath $PFX_PATH -Password $pfxPwd -Force | Out-Null
Write-Host "[OK] PFX da luu: $PFX_PATH" -ForegroundColor Green

# Xuat file CER (chi public cert) de cai len may nguoi dung
Export-Certificate -Cert $cert -FilePath $CER_PATH -Type CERT -Force | Out-Null
Write-Host "[OK] CER da luu: $CER_PATH" -ForegroundColor Green

# Luu thumbprint ra file de sign_release.ps1 dung
$thumbprintFile = Join-Path $PSScriptRoot ".cert_thumbprint"
$cert.Thumbprint | Out-File $thumbprintFile -Encoding ASCII -Force
Write-Host "[OK] Thumbprint da luu: $thumbprintFile" -ForegroundColor Green

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  HOAN TAT! Buoc tiep theo:" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  1. Chay BUILD_APP.bat de build va tu dong ky so" -ForegroundColor White
Write-Host "     HOAC chay thu cong: .\sign_release.ps1" -ForegroundColor White
Write-Host ""
Write-Host "  2. De nguoi dung tin tuong ung dung (khong bi SmartScreen chặn):" -ForegroundColor White
Write-Host "     Cai QLNNN_codesign.cer len may nguoi dung bang deploy_cert.ps1" -ForegroundColor White
Write-Host "     HOAC trien khai qua Group Policy (GPO)" -ForegroundColor White
Write-Host ""
Write-Host "  LUU Y: Giu bi mat file QLNNN_codesign.pfx - khong commit len Git!" -ForegroundColor Red
Write-Host ""
