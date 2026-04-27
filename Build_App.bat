@echo off
chcp 65001 >nul
title BUILD APP VCFE DATABASE (ONE FOLDER MODE)

cd /d "%~dp0"

echo ============================================================
echo   BAT DAU QUA TRINH BUILD VCFE DATABASE
echo ============================================================
echo.

:: 1. Kich hoat moi truong ao
if exist "venv312\Scripts\activate.bat" (
    echo [1/5] Kich hoat venv312...
    call venv312\Scripts\activate.bat
) else (
    echo [LOI] Khong tim thay venv312. Vui long chay Cai_dat_VCFE.bat truoc.
    pause
    exit /b 1
)

:: Cai dat them pyinstaller neu chua co
python -m pip install pyinstaller

:: 2. Chuyen doi logo.png thanh logo.ico nhieu kich thuoc de shortcut khong bi nhoe
echo.
echo [2/5] Tao file icon do phan giai cao tu logo.png...
python packaging\convert_icon.py
if %ERRORLEVEL% neq 0 (
    echo [LOI] Convert icon that bai.
    pause
    exit /b 1
)

:: 3. Chay tool xoa sach comment (Python, HTML, JS, CSS)
echo.
echo [3/5] Sao chep code va xoa toan bo comment vao thu muc build_src...
python packaging\minify_code.py
if %ERRORLEVEL% neq 0 (
    echo [LOI] Xoa comment that bai.
    pause
    exit /b 1
)

:: 4. Build app bang PyInstaller
echo.
echo [4/5] Build dang One Folder voi PyInstaller...
pyinstaller --clean -y packaging\csxh_pa01_onefolder.spec
if %ERRORLEVEL% neq 0 (
    echo [LOI] Build bang PyInstaller that bai.
    pause
    exit /b 1
)

:: 5. Dong goi thanh file Setup bang Inno Setup
echo.
echo [5/5] Dong goi thanh file Setup...
set INNO_COMPILER="D:\Inno Setup 6\iscc.exe"
if not exist %INNO_COMPILER% (
    echo [CẢNH BÁO] Khong tim thay Inno Setup tai D:\Inno Setup 6\iscc.exe
    echo Vui long mo packaging\installer.iss bang Inno Setup va tu compile de tao file cai dat.
) else (
    %INNO_COMPILER% packaging\installer.iss
    if %ERRORLEVEL% equ 0 (
        echo [OK] Dong goi hoan tat! File Setup nam trong thu muc dist/
    ) else (
        echo [LOI] Dong goi bang Inno Setup that bai.
    )
)

echo.
echo ============================================================
echo   QUA TRINH BUILD HOAN TAT
echo ============================================================
pause
