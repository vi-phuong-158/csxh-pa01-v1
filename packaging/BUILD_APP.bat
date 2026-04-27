@echo off
setlocal EnableDelayedExpansion
title QLNNN - Build Tool

cd /d "%~dp0\.."

echo.
echo ============================================================
echo   QLNNN - DONG GOI UNG DUNG
echo ============================================================
echo.

:: ============================================================
:: Step 0: Kiem tra Python
:: ============================================================
echo [Step 0] Kiem tra moi truong...
python --version
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Khong tim thay Python!
    pause
    exit /b 1
)

:: ============================================================
:: Step 1: Chuyen doi icon
:: ============================================================
echo.
echo [Step 1] Chuyen doi icon...
python packaging\convert_icon.py

:: ============================================================
:: Step 2: Dong goi voi PyInstaller
:: ============================================================
echo.
echo [Step 2] Dong goi voi PyInstaller (3-7 phut)...
python packaging\build.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] PyInstaller that bai!
    pause
    exit /b 1
)

echo.
echo [OK] PyInstaller hoan thanh. Output: dist\QLNNN\

:: ============================================================
:: Step 3: Ky so QLNNN.exe (neu co chung chi)
:: ============================================================
echo.
echo [Step 3] Ky so QLNNN.exe...

set CERT_THUMB_FILE=packaging\.cert_thumbprint
if exist "%CERT_THUMB_FILE%" (
    powershell -NoProfile -ExecutionPolicy Bypass -File "packaging\sign_release.ps1" -Target exe
    if %ERRORLEVEL% NEQ 0 (
        echo [WARN] Ky so that bai - tiep tuc khong co chu ky.
    )
) else (
    echo [WARN] Chua co chung chi ky so.
    echo        Chay packaging\setup_codesign.ps1 (quyen Admin) de tao chung chi.
    echo        Ung dung van hoat dong nhung co the bi Windows SmartScreen chặn.
)

:: ============================================================
:: Step 4: Bien dich installer voi Inno Setup
:: ============================================================
echo.
echo [Step 4] Tim Inno Setup Compiler...

set ISCC=
for %%P in (
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    "C:\Program Files\Inno Setup 6\ISCC.exe"
    "C:\Program Files (x86)\Inno Setup 5\ISCC.exe"
) do (
    if exist %%P (
        set ISCC=%%~P
        goto :found_iscc
    )
)

:not_found_iscc
echo [WARN] Khong tim thay Inno Setup.
echo        Tai mien phi tai: https://jrsoftware.org/isdl.php
echo.
echo        Sau khi cai, chay thu cong:
echo        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" packaging\installer.iss
goto :skip_installer

:found_iscc
echo [OK] Tim thay: %ISCC%
echo [Step 4] Bien dich installer...
"%ISCC%" packaging\installer.iss
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Inno Setup that bai!
    pause
    exit /b 1
)
echo [OK] Installer da tao: dist\installer\QLNNN_Setup_v1.0.exe

:: ============================================================
:: Step 5: Ky so installer (neu co chung chi)
:: ============================================================
echo.
echo [Step 5] Ky so installer...
if exist "%CERT_THUMB_FILE%" (
    powershell -NoProfile -ExecutionPolicy Bypass -File "packaging\sign_release.ps1" -Target installer
    if %ERRORLEVEL% NEQ 0 (
        echo [WARN] Ky so installer that bai.
    )
) else (
    echo [skip] Khong co chung chi - bo qua buoc ky installer.
)

:skip_installer

:: ============================================================
:: Ket qua
:: ============================================================
echo.
echo ============================================================
echo   BUILD HOAN TAT!
echo ============================================================
echo.
if exist "dist\installer\QLNNN_Setup_v1.0.exe" (
    echo   Bo cai: dist\installer\QLNNN_Setup_v1.0.exe
) else (
    echo   Thu muc app: dist\QLNNN\
)
echo.
if not exist "%CERT_THUMB_FILE%" (
    echo   [!] DE KHONG BI WINDOWS CHAN:
    echo       1. Chay packaging\setup_codesign.ps1 (Admin) de tao chung chi
    echo       2. Chay lai BUILD_APP.bat de ky so
    echo       3. Cai packaging\QLNNN_codesign.cer len may nguoi dung
    echo          bang packaging\deploy_cert.ps1 hoac Group Policy
    echo.
)
pause
