@echo off
chcp 65001 >nul
title VCFE DATABASE - CSDL NGUOI VIET NAM CO YEU TO NUOC NGOAI

cd /d "%~dp0"

echo ============================================================
echo   KHOI DONG HE THONG VCFE DATABASE
echo ============================================================
echo.

REM Kiem tra virtual environment
if exist "venv312\Scripts\activate.bat" (
    echo [OK] Tim thay moi truong venv312.
    call venv312\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    echo [OK] Tim thay moi truong venv.
    call venv\Scripts\activate.bat
) else (
    echo [LOI] Khong tim thay moi truong ao venv. 
    echo Vui long chay: python -m venv venv312 && venv312\Scripts\activate && pip install -r requirements.txt
    pause
    exit /b 1
)

REM Chay server qua run_server.py
python run_server.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo [LOI] Co loi xay ra khi chay he thong.
    pause
)

deactivate
