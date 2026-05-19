@echo off
chcp 65001 >nul
cd /d "%~dp0"
call packaging\BUILD_APP.bat
