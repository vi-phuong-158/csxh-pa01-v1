@echo off
chcp 65001 >nul
title CAI DAT MOI TRUONG VCFE DATABASE

cd /d "%~dp0"

echo ============================================================
echo   CAI DAT MOI TRUONG VA THU VIEN CHO VCFE DATABASE
echo ============================================================
echo.

REM Tao venv neu chua co
if not exist "venv312" (
    echo [INFO] Dang tao moi truong ao venv312...
    python -m venv venv312
    if %ERRORLEVEL% neq 0 (
        echo [LOI] Khong the tao venv. Hay kiem tra xem Python da duoc cai dat chua.
        pause
        exit /b 1
    )
)

REM Kich hoat va cai dat
echo [INFO] Dang kich hoat moi truong ao...
call venv312\Scripts\activate.bat

echo [INFO] Dang cap nhat pip...
python -m pip install --upgrade pip

echo [INFO] Dang cai dat cac thu vien tu requirements.txt...
pip install -r requirements.txt

if %ERRORLEVEL% eq 0 (
    echo.
    echo [OK] Da cai dat xong moi thu.
    echo Bay gio ban co the chay file 'Chay_VCFE.bat' de bat dau.
) else (
    echo.
    echo [LOI] Co loi xay ra trong qua trinh cai dat.
)

pause
