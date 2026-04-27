#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Cai chung chi QLNNN_codesign.cer len may nguoi dung.
    Chay script nay voi quyen Administrator tren MAY NGUOI DUNG
    (hoac trien khai qua Group Policy).

.DESCRIPTION
    Them chung chi vao hai store tren may nguoi dung:
    - LocalMachine\TrustedPublisher  : Windows tin tuong publisher
    - LocalMachine\Root              : Windows xac thuc chu ky hop le

    Sau khi chay script nay, nguoi dung co the chay QLNNN.exe va
    QLNNN_Setup_*.exe ma khong bi SmartScreen chặn.

.EXAMPLE
    # Chay tren may nguoi dung (co file .cer cung thu muc):
    powershell -ExecutionPolicy Bypass -File "deploy_cert.ps1"

    # Hoac chi dinh duong dan den file .cer:
    powershell -ExecutionPolicy Bypass -File "deploy_cert.ps1" -CerPath "C:\path\to\QLNNN_codesign.cer"

.NOTES
    Trien khai hang loat qua GPO:
    Computer Configuration > Windows Settings > Security Settings >
    Public Key Policies > Trusted Publishers (them file .cer vao day)
#>
param(
    [string]$CerPath = (Join-Path $PSScriptRoot "QLNNN_codesign.cer")
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  CAI CHUNG CHI TIN CAY CHO QLNNN" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Kiem tra file .cer
if (-not (Test-Path $CerPath)) {
    Write-Host "[!] Khong tim thay file chung chi: $CerPath" -ForegroundColor Red
    Write-Host ""
    Write-Host "    Lay file QLNNN_codesign.cer tu may build (thu muc packaging\)" -ForegroundColor Yellow
    Write-Host "    roi chay lai script nay." -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] Tim thay file chung chi: $CerPath" -ForegroundColor Green

# Doc file .cer
try {
    $cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2 $CerPath
} catch {
    Write-Host "[!] File chung chi khong hop le: $_" -ForegroundColor Red
    exit 1
}

Write-Host "    Subject  : $($cert.Subject)"
Write-Host "    Het han  : $($cert.NotAfter.ToString('dd/MM/yyyy'))"
Write-Host "    SHA1     : $($cert.Thumbprint)"
Write-Host ""

if ($cert.NotAfter -lt (Get-Date)) {
    Write-Host "[!] CANH BAO: Chung chi da het han! Lien he admin de cap nhat." -ForegroundColor Red
    exit 1
}

# Cai vao cert store
$storeList = @(
    @{ Name = "TrustedPublisher"; DisplayName = "Trusted Publishers" },
    @{ Name = "Root";             DisplayName = "Trusted Root CA" }
)

foreach ($s in $storeList) {
    $store = New-Object System.Security.Cryptography.X509Certificates.X509Store($s.Name, "LocalMachine")
    $store.Open("ReadWrite")
    $alreadyExists = $store.Certificates | Where-Object { $_.Thumbprint -eq $cert.Thumbprint }
    if (-not $alreadyExists) {
        $store.Add($cert)
        Write-Host "[OK] Da cai vao LocalMachine\$($s.DisplayName)" -ForegroundColor Green
    } else {
        Write-Host "[i] Da co trong LocalMachine\$($s.DisplayName)" -ForegroundColor Yellow
    }
    $store.Close()
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  HOAN TAT! May nay se tin tuong ung dung QLNNN." -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Nguoi dung co the chay QLNNN.exe va QLNNN_Setup_*.exe" -ForegroundColor White
Write-Host "  ma khong bi Windows chặn." -ForegroundColor White
Write-Host ""
