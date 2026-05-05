@echo off
chcp 65001 >nul
title Build - VCFED Database

cd /d "%~dp0\.."

echo.
echo ============================================================
echo   DONG GOI VCFED DATABASE v2.0
echo ============================================================
echo.

python --version
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Khong tim thay Python!
    pause & exit /b 1
)

call venv312\Scripts\activate.bat 2>nul || call venv\Scripts\activate.bat 2>nul

echo.
echo [Step 1] Dong goi voi PyInstaller (co the mat 5-10 phut)...
python packaging\build.py
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] PyInstaller that bai!
    pause & exit /b 1
)

echo.
echo [Step 2] Bien dich Inno Setup installer...

set ISCC=
for %%P in (
    "D:\Inno Setup 6\ISCC.exe"
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    "C:\Program Files\Inno Setup 6\ISCC.exe"
) do (
    if exist %%P (
        set ISCC=%%~P
        goto :found_iscc
    )
)

echo [WARN] Khong tim thay Inno Setup. Tai tai: https://jrsoftware.org/isdl.php
goto :skip_installer

:found_iscc
echo [OK] Tim thay: %ISCC%
"%ISCC%" packaging\installer.iss
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Inno Setup that bai!
    pause & exit /b 1
)

:skip_installer
echo.
echo ============================================================
echo   BUILD HOAN TAT!
echo ============================================================
echo.
if exist "dist\installer\" (
    dir /b "dist\installer\*.exe" 2>nul
    echo   Output: dist\installer\
) else (
    echo   Thu muc app: dist\VCFED\
)
echo.
pause
