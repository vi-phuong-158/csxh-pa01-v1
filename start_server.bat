@echo off
chcp 65001 >nul
title VCFE Database Server

cd /d "%~dp0"

if not exist ".env" (
    echo [LOI] Khong tim thay file .env
    echo Vui long tao file .env truoc khi chay server.
    pause
    exit /b 1
)

echo [OK] Khoi dong VCFE Database tai http://127.0.0.1:8000
echo      Nhan Ctrl+C de dung server.
echo.

call venv312\Scripts\activate.bat 2>nul || call venv\Scripts\activate.bat 2>nul

python run_server.py --port 8000

pause
