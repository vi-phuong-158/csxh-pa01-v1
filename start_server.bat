@echo off
chcp 65001 >nul
title VCFE Database Server

cd /d "%~dp0"

call venv312\Scripts\activate.bat 2>nul || call venv\Scripts\activate.bat 2>nul

python run_server.py

pause
