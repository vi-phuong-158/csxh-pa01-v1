"""
packaging/build_portable.py
============================
Build gói QLNNN Portable — không cần cài Python hay bất kỳ thứ gì.

Tại sao dùng Portable thay vì PyInstaller?
  PyInstaller tạo ra QLNNN.exe (unsigned) → bị WDAC/Device Guard chặn.
  Portable dùng python.exe gốc (ký bởi Python Software Foundation)
  → hầu hết WDAC policy đều trust.

Cách chạy:
    python packaging/build_portable.py

Kết quả: dist/QLNNN/  →  sao chép nguyên thư mục này đến máy người dùng.
Người dùng chỉ cần double-click QLNNN.bat (hoặc QLNNN.vbs nếu muốn ẩn console).
"""

import io
import sys
import shutil
import subprocess
import urllib.request
import zipfile
from pathlib import Path

if sys.platform == "win32" and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent.parent.resolve()
OUTPUT = ROOT / "dist" / "QLNNN"
RUNTIME_DIR = OUTPUT / "runtime"
CACHE_DIR = ROOT / "packaging" / ".build_cache"

# Python Embeddable — phải khớp với version đang dùng để package compat.
PY_VER = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
PY_EMBED_URL = (
    f"https://www.python.org/ftp/python/{PY_VER}"
    f"/python-{PY_VER}-embed-amd64.zip"
)
PY_EMBED_ZIP = CACHE_DIR / f"python-{PY_VER}-embed-amd64.zip"
GET_PIP_URL = "https://bootstrap.pypa.io/get-pip.py"
GET_PIP_PY = CACHE_DIR / "get-pip.py"

APP_ITEMS = [
    "backend",
    "frontend",
    "landing_page",
    "assets",
    "nation.json",
    "run_server.py",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _size_str(path: Path) -> str:
    mb = path.stat().st_size / 1_048_576
    return f"{mb:.1f} MB" if mb >= 1 else f"{path.stat().st_size // 1024} KB"


def _download(url: str, dest: Path, label: str) -> None:
    if dest.exists():
        print(f"    [=] Cache: {dest.name}")
        return
    print(f"    [↓] {label} ...", end="", flush=True)
    try:
        urllib.request.urlretrieve(url, dest)
        print(f" OK ({_size_str(dest)})")
    except Exception as e:
        dest.unlink(missing_ok=True)
        raise RuntimeError(f"Tải thất bại: {url}\n  {e}") from e


# ---------------------------------------------------------------------------
# Build steps
# ---------------------------------------------------------------------------

def clean() -> None:
    print("[~] Dọn build cũ ...")
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT, ignore_errors=True)
    OUTPUT.mkdir(parents=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def step1_setup_python() -> None:
    print(f"\n[1/4] Python {PY_VER} Embeddable runtime ...")
    _download(PY_EMBED_URL, PY_EMBED_ZIP, f"python-{PY_VER}-embed-amd64.zip")

    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(PY_EMBED_ZIP) as zf:
        zf.extractall(RUNTIME_DIR)
    print(f"    [+] Giải nén xong → {RUNTIME_DIR.name}/")

    # Embeddable Python tắt site-packages mặc định; bật lại qua file _pth.
    pth = next(RUNTIME_DIR.glob("python*._pth"), None)
    if pth:
        text = pth.read_text(encoding="utf-8")
        text = text.replace("#import site", "import site")
        if "Lib\\site-packages" not in text:
            text += "\nLib\\site-packages\n"
        pth.write_text(text, encoding="utf-8")
        print(f"    [+] Đã bật site-packages ({pth.name})")
    else:
        raise RuntimeError("Không tìm thấy file ._pth trong embeddable package!")

    (RUNTIME_DIR / "Lib" / "site-packages").mkdir(parents=True, exist_ok=True)

    # Bootstrap pip
    _download(GET_PIP_URL, GET_PIP_PY, "get-pip.py")
    python_exe = RUNTIME_DIR / "python.exe"
    subprocess.check_call(
        [str(python_exe), str(GET_PIP_PY), "--quiet", "--no-warn-script-location"],
        cwd=str(RUNTIME_DIR),
    )
    print("    [+] pip đã được bootstrap")


def step2_install_packages() -> None:
    print("\n[2/4] Cài thư viện vào runtime ...")
    python_exe = RUNTIME_DIR / "python.exe"
    subprocess.check_call([
        str(python_exe), "-m", "pip", "install",
        "-r", str(ROOT / "requirements.txt"),
        "--quiet",
        "--no-warn-script-location",
    ])
    print("    [+] Tất cả thư viện đã được cài")

    # Copy DLL của các native package (sqlcipher3, v.v.) lên cạnh python.exe
    # để Windows tìm được khi load.
    site_pkg = RUNTIME_DIR / "Lib" / "site-packages"
    dll_count = 0
    for dll in site_pkg.rglob("*.dll"):
        dst = RUNTIME_DIR / dll.name
        if not dst.exists():
            shutil.copy2(dll, dst)
            dll_count += 1
    if dll_count:
        print(f"    [+] Đã copy {dll_count} DLL lên runtime/")


def step3_copy_app() -> None:
    print("\n[3/4] Sao chép ứng dụng ...")
    for item in APP_ITEMS:
        src = ROOT / item
        if not src.exists():
            print(f"    [!] Bỏ qua (không tìm thấy): {item}")
            continue
        dst = OUTPUT / item
        if src.is_dir():
            shutil.copytree(
                src, dst,
                ignore=shutil.ignore_patterns(
                    "__pycache__", "*.pyc", "*.pyo",
                    "*.db", "*.db-wal", "*.db-shm",
                    "data",          # thư mục data/ chứa DB — KHÔNG đưa vào
                ),
            )
        else:
            shutil.copy2(src, dst)
        print(f"    [+] {item}")


def step4_create_launchers() -> None:
    print("\n[4/4] Tạo file khởi động ...")

    # --- QLNNN.bat: double-click mở console + tự mở browser ---
    bat = "\r\n".join([
        "@echo off",
        "title QLNNN - He thong Quan ly Nguoi Nuoc Ngoai",
        "cd /d \"%~dp0\"",
        "echo ================================================",
        "echo  QLNNN — Dang khoi dong, vui long cho...",
        "echo ================================================",
        "start \"QLNNN-Server\" \"%~dp0runtime\\python.exe\" \"%~dp0run_server.py\"",
        "timeout /t 4 >nul",
        "start http://127.0.0.1:9000",
    ]) + "\r\n"
    (OUTPUT / "QLNNN.bat").write_text(bat, encoding="utf-8")
    print("    [+] QLNNN.bat")

    # --- QLNNN.vbs: chạy ẩn console, tự mở browser ---
    vbs_lines = [
        'Dim d, sh',
        'd = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\\"))',
        'Set sh = CreateObject("WScript.Shell")',
        '\'  0 = ẩn cửa sổ; False = không đợi tiến trình kết thúc',
        'sh.Run Chr(34) & d & "runtime\\python.exe" & Chr(34) _',
        '      & " " & Chr(34) & d & "run_server.py" & Chr(34), 0, False',
        'WScript.Sleep 4000',
        'sh.Run "http://127.0.0.1:9000"',
        'Set sh = Nothing',
    ]
    (OUTPUT / "QLNNN.vbs").write_text("\n".join(vbs_lines) + "\n", encoding="utf-8")
    print("    [+] QLNNN.vbs  (không hiện cửa sổ đen)")

    # --- .env.example ---
    (OUTPUT / ".env.example").write_text(
        "# Mat khau ma hoa CSDL — doi thanh mat khau bi mat cua don vi\n"
        "QLNNN_DB_PASSPHRASE=mat-khau-cua-ban\n",
        encoding="utf-8",
    )

    # --- HUONG_DAN.txt ---
    guide = "\n".join([
        "=" * 56,
        "  HE THONG QUAN LY NGUOI NUOC NGOAI (QLNNN)",
        "  Huong dan su dung",
        "=" * 56,
        "",
        "LAN DAU SU DUNG:",
        "  1. Sao chep .env.example  =>  .env",
        "     (trong cung thu muc nay)",
        "  2. Mo file .env bang Notepad, sua mat khau:",
        "     QLNNN_DB_PASSPHRASE=<mat-khau-bi-mat-cua-ban>",
        "  3. Double-click QLNNN.bat",
        "  4. Trinh duyet tu dong mo; neu khong thi vao:",
        "     http://127.0.0.1:9000",
        "",
        "LAN SAU:",
        "  - Chi double-click QLNNN.bat (hoac QLNNN.vbs)",
        "  - Khong can lam gi them",
        "",
        "FILE QUAN TRONG:",
        "  - CSDL    : backend\\data\\qlnnn.db  (backup dinh ky!)",
        "  - Mat khau: .env  (giu bi mat, KHONG chia se)",
        "",
        "TAT UNG DUNG:",
        "  - Dong cua so console (X)",
        "  - Hoac vao Task Manager > tat python.exe",
        "=" * 56,
    ])
    (OUTPUT / "HUONG_DAN.txt").write_text(guide + "\n", encoding="utf-8")
    print("    [+] HUONG_DAN.txt")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print(f" BUILD QLNNN PORTABLE (Python {PY_VER} Embeddable)")
    print("=" * 60)

    clean()
    step1_setup_python()
    step2_install_packages()
    step3_copy_app()
    step4_create_launchers()

    total_mb = sum(
        f.stat().st_size for f in OUTPUT.rglob("*") if f.is_file()
    ) / 1_048_576

    print(f"\n{'=' * 60}")
    print(f" BUILD THANH CONG!")
    print(f" Thu muc : {OUTPUT}")
    print(f" Kich thuoc: {total_mb:.0f} MB")
    print(f"{'=' * 60}")
    print()
    print("Phan phoi: Sao chep NGUYEN THU MUC dist/QLNNN/ den may nguoi dung.")
    print("Nguoi dung: Double-click QLNNN.bat la xong.")
    print()


if __name__ == "__main__":
    main()
