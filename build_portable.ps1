# ============================================
# BUILD PORTABLE - Security Profile 360
# Python Embedded + PyArmor
# ============================================
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"

$PYTHON_VERSION = "3.13.5"
$PYTHON_EMBED_URL = "https://www.python.org/ftp/python/$PYTHON_VERSION/python-$PYTHON_VERSION-embed-amd64.zip"
$GET_PIP_URL = "https://bootstrap.pypa.io/get-pip.py"

$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
$BUILD_DIR = Join-Path $ROOT "dist_v3"
$PYTHON_DIR = Join-Path $BUILD_DIR "python"
$APP_DIR = Join-Path $BUILD_DIR "app"
$TEMP_DIR = Join-Path $ROOT "_build_temp"

$VENV_PYTHON = Join-Path $ROOT ".venv\Scripts\python.exe"
if (Test-Path $VENV_PYTHON) {
    $SYS_PYTHON = $VENV_PYTHON
}
else {
    $SYS_PYTHON = "python"
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  BUILD PORTABLE - Security Profile 360" -ForegroundColor Cyan
Write-Host "  Python Embedded + PyArmor" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# STEP 0: Clean up
Write-Host "[0/7] Don dep thu muc cu..." -ForegroundColor Yellow
if (Test-Path $BUILD_DIR) { Remove-Item -Recurse -Force $BUILD_DIR }
if (Test-Path $TEMP_DIR) { Remove-Item -Recurse -Force $TEMP_DIR }
New-Item -ItemType Directory -Force -Path $BUILD_DIR | Out-Null
New-Item -ItemType Directory -Force -Path $PYTHON_DIR | Out-Null
New-Item -ItemType Directory -Force -Path $APP_DIR | Out-Null
New-Item -ItemType Directory -Force -Path $TEMP_DIR | Out-Null
Write-Host "  [OK] Da don dep." -ForegroundColor Green
Write-Host ""

# STEP 1: Download Python Embedded
Write-Host "[1/7] Tai Python Embedded $PYTHON_VERSION..." -ForegroundColor Yellow
$pythonZip = Join-Path $TEMP_DIR "python-embed.zip"

if (-not (Test-Path $pythonZip)) {
    Write-Host "  Dang tai tu python.org..."
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $PYTHON_EMBED_URL -OutFile $pythonZip -UseBasicParsing
}

Write-Host "  Giai nen Python Embedded..."
Expand-Archive -Path $pythonZip -DestinationPath $PYTHON_DIR -Force
Write-Host "  [OK] Da tai va giai nen Python Embedded." -ForegroundColor Green
Write-Host ""

# STEP 2: Configure Python Embedded for pip
Write-Host "[2/7] Cau hinh Python Embedded de dung pip..." -ForegroundColor Yellow

$pthFile = Get-ChildItem -Path $PYTHON_DIR -Filter "python*._pth" | Select-Object -First 1

if ($pthFile) {
    Write-Host "  Chinh sua $($pthFile.Name)..."
    $pthContent = Get-Content $pthFile.FullName -Raw
    $pthContent = $pthContent -replace '#import site', 'import site'
    if ($pthContent -notmatch 'Lib\\site-packages') {
        $pthContent += "`r`nLib\site-packages"
    }
    Set-Content $pthFile.FullName $pthContent -NoNewline
}
else {
    Write-Host "  [CANH BAO] Khong tim thay file ._pth" -ForegroundColor Red
}

Write-Host "  Tai get-pip.py..."
$getPipPath = Join-Path $TEMP_DIR "get-pip.py"
Invoke-WebRequest -Uri $GET_PIP_URL -OutFile $getPipPath -UseBasicParsing

Write-Host "  Cai dat pip vao Python Embedded..."
$embedPython = Join-Path $PYTHON_DIR "python.exe"
& $embedPython $getPipPath --no-warn-script-location 2>&1 | Out-Host
if ($LASTEXITCODE -ne 0) { throw "Khong the cai pip" }

Write-Host "  [OK] Da cau hinh Python Embedded + pip." -ForegroundColor Green
Write-Host ""

# STEP 3: Install dependencies
Write-Host "[3/7] Cai dat dependencies..." -ForegroundColor Yellow
$reqFile = Join-Path $ROOT "requirements.txt"
& $embedPython -m pip install --no-warn-script-location -r $reqFile 2>&1 | Out-Host
if ($LASTEXITCODE -ne 0) { throw "Khong the cai dependencies" }
Write-Host "  [OK] Da cai dat tat ca dependencies." -ForegroundColor Green
Write-Host ""

# STEP 4: Install PyWebView for Desktop App Wrapper
Write-Host "[4/7] Cai dat PyWebView..." -ForegroundColor Yellow
& $embedPython -m pip install --no-warn-script-location pywebview 2>&1 | Out-Host
Write-Host "  [OK] Da cai dat PyWebView." -ForegroundColor Green
Write-Host ""

# STEP 5: Copy source code
Write-Host "[5/7] Copy source code..." -ForegroundColor Yellow

$mainFiles = @("app.py", "database.py", "auth.py", "constants.py", "services.py")
foreach ($f in $mainFiles) {
    $src = Join-Path $ROOT $f
    if (Test-Path $src) {
        Copy-Item $src -Destination $APP_DIR -Force
        Write-Host "  + $f"
    }
}

$sourceDirs = @("views", "utils", "app")
foreach ($d in $sourceDirs) {
    $src = Join-Path $ROOT $d
    if (Test-Path $src) {
        $dest = Join-Path $APP_DIR $d
        Copy-Item $src -Destination $dest -Recurse -Force
        Write-Host "  + $d/"
    }
}

Get-ChildItem -Path $APP_DIR -Directory -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force

$assets = @("logo.png", "style.css", "mau_ho_so_csxh.xlsx", "security_profile.db")
foreach ($f in $assets) {
    $src = Join-Path $ROOT $f
    if (Test-Path $src) {
        Copy-Item $src -Destination $APP_DIR -Force
        Write-Host "  + $f [asset]"
    }
}

Write-Host "  [OK] Da copy source code." -ForegroundColor Green
Write-Host ""

# STEP 6: Compile to .pyc and remove .py files
Write-Host "[6/7] Bien dich ma nguon sang Bytecode (.pyc)..." -ForegroundColor Yellow

Write-Host "  Dang bien dich ma nguon sang Bytecode (.pyc)..." -ForegroundColor Yellow
# Compile all .py files in app directory to .pyc (Python 3.13 uses __pycache__ or legacy generation)
# Using legacy flag (-b) to generate .pyc next to .py files without __pycache__
$compileCmd = "& ""$SYS_PYTHON"" -m compileall -b ""$APP_DIR"""
Invoke-Expression $compileCmd | Out-Host

if ($LASTEXITCODE -ne 0) {
    Write-Warning "Compileall co the gap canh bao, nhung qua trinh build van tiep tuc."
}

Write-Host "  Dang xoa file ma nguon goc (.py) de tang bao mat..."
# Get all .py files
$allPyFiles = Get-ChildItem -Path $APP_DIR -Filter "*.py" -Recurse
foreach ($file in $allPyFiles) {
    # Keep app.py as original .py to ensure 100% compatibility with Streamlit's entrypoint
    if ($file.Name -eq "app.py" -and $file.Directory.FullName -eq $APP_DIR) {
        Write-Host "  [OK] Giu nguyen $($file.Name) lam Entry Point." -ForegroundColor Cyan
        continue
    }
        
    # We ensure the corresponding .pyc was created before deleting the .py
    $pycPath = $file.FullName + "c"
    if (Test-Path $pycPath) {
        Remove-Item -Path $file.FullName -Force
    }
    else {
        Write-Warning "Khong tim thay file .pyc cho $($file.Name), giu nguyen file .py de tranh loi."
    }
}
    
# Remove any __pycache__ directories that might have been accidentally created
Get-ChildItem -Path $APP_DIR -Directory -Filter "__pycache__" -Recurse | Remove-Item -Recurse -Force

Write-Host "-> Bien dich hoan tat!" -ForegroundColor Green

# Ensure assets still exist
foreach ($f in $assets) {
    $destPath = Join-Path $APP_DIR $f
    $srcPath = Join-Path $ROOT $f
    if ((-not (Test-Path $destPath)) -and (Test-Path $srcPath)) {
        Copy-Item $srcPath -Destination $destPath -Force
    }
}

Write-Host ""

# STEP 7: Create launcher files (Desktop App Mode)
Write-Host "[7/7] Tao file khoi chay Desktop..." -ForegroundColor Yellow

# Create launcher.py for PyWebView
$launcherLines = @(
    "import subprocess"
    "import webview"
    "import time"
    "import socket"
    "import sys"
    "import os"
    ""
    "def wait_for_port(port, timeout=15):"
    "    start_time = time.time()"
    "    while time.time() - start_time < timeout:"
    "        try:"
    "            with socket.create_connection(('localhost', port), timeout=1):"
    "                return True"
    "        except OSError:"
    "            time.sleep(0.5)"
    "    return False"
    ""
    "if __name__ == '__main__':"
    "    base_dir = os.path.dirname(os.path.abspath(__file__))"
    "    python_exe = os.path.join(base_dir, 'python', 'python.exe')"
    "    app_file = os.path.join(base_dir, 'app', 'app.py')"
    "    "
    "    # 0x08000000 = CREATE_NO_WINDOW"
    "    process = subprocess.Popen("
    "        [python_exe, '-m', 'streamlit', 'run', app_file, '--server.headless=true', '--browser.gatherUsageStats=false'],"
    "        creationflags=0x08000000,"
    "        cwd=base_dir"
    "    )"
    "    "
    "    if wait_for_port(8501):"
    "        webview.create_window('Ho so CSXH - Security Profile 360', 'http://localhost:8501', width=1280, height=800)"
    "        webview.start()"
    "    "
    "    process.terminate()"
)
$launcherPath = Join-Path $BUILD_DIR "launcher.py"
$launcherLines -join "`r`n" | Set-Content -Path $launcherPath -Encoding UTF8
Write-Host "  + launcher.py" -ForegroundColor Green

# Create 1. Khoi_Dong.vbs
$startVbsLines = @(
    "Set WshShell = CreateObject(`"WScript.Shell`")"
    "WshShell.CurrentDirectory = CreateObject(`"Scripting.FileSystemObject`").GetParentFolderName(WScript.ScriptFullName)"
    "WshShell.Run `"python\pythonw.exe launcher.py`", 1, False"
)
$startVbsPath = Join-Path $BUILD_DIR "1. Khoi_Dong.vbs"
$startVbsLines -join "`r`n" | Set-Content -Path $startVbsPath -Encoding ASCII
Write-Host "  + 1. Khoi_Dong.vbs" -ForegroundColor Green

# Create 2. Tat_Ung_Dung.vbs
$stopVbsLines = @(
    "Set objWMIService = GetObject(`"winmgmts:\\.\root\cimv2`")"
    "Set colProcesses = objWMIService.ExecQuery(`"Select * from Win32_Process Where Name = 'python.exe' OR Name = 'pythonw.exe'`")"
    "For Each objProcess in colProcesses"
    "    If InStr(1, objProcess.CommandLine, `"streamlit run app\app.py`", 1) > 0 Or InStr(1, objProcess.CommandLine, `"launcher.py`", 1) > 0 Then"
    "        objProcess.Terminate()"
    "    End If"
    "Next"
    "MsgBox `"Da tat ung dung thanh cong!`", 64, `"He Thong`""
)
$stopVbsPath = Join-Path $BUILD_DIR "2. Tat_Ung_Dung.vbs"
$stopVbsLines -join "`r`n" | Set-Content -Path $stopVbsPath -Encoding ASCII
Write-Host "  + 2. Tat_Ung_Dung.vbs" -ForegroundColor Green

# Create HUONG_DAN.txt
$guideLines = @(
    'HUONG DAN SU DUNG PHAN MEM SECURITY PROFILE 360 (OFFLINE)'
    '=========================================================='
    ''
    '1. Cach khoi dong'
    '   - Nhan dup chuot vao file "1. Khoi_Dong.vbs".'
    '   - Ung dung se chay ngam hoan toan va tu do mo cua so ung dung.'
    '   - Khong co cua so terminal den nao hien len.'
    ''
    '2. Cach tat ung dung'
    '   - Tat bang dau X tren cua so ung dung chinh.'
    '   - Hoac nhan dup vao "2. Tat_Ung_Dung.vbs" neu bi hu/treo.'
    ''
    '3. Cau truc thu muc'
    '   - 1. Khoi_Dong.vbs   : File khoi chay Desktop App'
    '   - 2. Tat_Ung_Dung.vbs: File tat cuong che'
    '   - python\          : Bo Python portable (khong can cai Python)'
    '   - app\             : Ma nguon ung dung (da bien dich .pyc)'
    ''
    '4. Luu y quan trong'
    '   - KHONG xoa cac file/thu muc di kem.'
    '   - Co the copy TOAN BO thu muc nay sang USB hoac may khac.'
    ''
    '----------------------------------------------------------'
    'Phien ban: 2.0 (Portable + Native Compile + PyWebView)'
    'Thiet ke boi Vi Phuong'
)
$huongDanPath = Join-Path $BUILD_DIR "HUONG_DAN.txt"
$guideLines -join "`r`n" | Set-Content -Path $huongDanPath -Encoding UTF8
Write-Host "  + HUONG_DAN.txt" -ForegroundColor Green

Write-Host "  [OK] Da tao file khoi chay." -ForegroundColor Green
Write-Host ""

# CLEANUP
Write-Host "Don dep file tam..." -ForegroundColor Yellow
if (Test-Path $TEMP_DIR) { Remove-Item -Recurse -Force $TEMP_DIR }
Write-Host "  [OK] Da don dep." -ForegroundColor Green
Write-Host ""

# DONE
$totalSize = (Get-ChildItem $BUILD_DIR -Recurse | Measure-Object -Property Length -Sum).Sum
$sizeMB = [math]::Round($totalSize / 1MB, 2)

Write-Host "==================================================" -ForegroundColor Green
Write-Host "          DONG GOI THANH CONG!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host "  Thu muc output: dist_portable\" -ForegroundColor White
Write-Host "  Kich thuoc: $sizeMB MB" -ForegroundColor White
Write-Host "  Chay thu: dist_portable\start_app.bat" -ForegroundColor White
Write-Host ""
Write-Host "  De phan phoi: Copy toan bo thu muc" -ForegroundColor White
Write-Host "  dist_portable sang USB hoac may khac." -ForegroundColor White
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""
