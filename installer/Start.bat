@echo off
chcp 65001 >nul
title VCFE Database — Server
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

cd /d "%~dp0"

:: ── Cai dat lan dau: tao .env neu chua co ────────────────────────────────
if not exist ".env" (
    echo.
    echo  Phat hien day la lan chay dau tien.
    echo  Wizard se giup ban thiet lap he thong.
    echo.
    python\python.exe first_run.py
    if errorlevel 1 (
        echo.
        echo  [LOI] Cau hinh that bai. Ung dung khong the khoi dong.
        pause
        exit /b 1
    )
)

:: ── Mo trinh duyet sau 3 giay (cho uvicorn san sang) ─────────────────────
start /b "" cmd /c "timeout /t 3 /nobreak >nul && start http://127.0.0.1:8000"

:: ── Khoi dong FastAPI server ──────────────────────────────────────────────
echo.
echo  ============================================
echo   VCFE Database  -  http://127.0.0.1:8000
echo  ============================================
echo.
echo  Server dang chay. Nhan Ctrl+C de dung.
echo.

python\python.exe -m uvicorn backend.main:app ^
    --host 127.0.0.1 ^
    --port 8000

echo.
echo  Server da dung.
pause >nul
