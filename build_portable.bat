@echo off
chcp 65001 >nul 2>&1
echo.
echo Dang chay script dong goi...
echo.
powershell -ExecutionPolicy Bypass -File "%~dp0build_portable.ps1"
pause
