import os
import sys
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
DIST_DIR = ROOT / "dist"
BUILD_DIR = ROOT / "build"
APP_NAME = "VCFED"

DATA_TO_INCLUDE = [
    (ROOT / "frontend",           "frontend"),
    (ROOT / "assets",             "assets"),
    (ROOT / "mau_ho_so_csxh.xlsx", "."),
]

HIDDEN_IMPORTS = [
    # uvicorn
    "uvicorn.logging", "uvicorn.loops", "uvicorn.loops.auto",
    "uvicorn.protocols", "uvicorn.protocols.http", "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets", "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan", "uvicorn.lifespan.on",
    # anyio
    "anyio", "anyio._backends._asyncio",
    # starlette
    "starlette.routing", "starlette.staticfiles", "starlette.templating",
    "starlette.middleware", "starlette.middleware.sessions",
    # pydantic
    "pydantic.deprecated.class_validators",
    "pydantic_settings",
    # database
    "sqlcipher3", "sqlcipher3.dbapi2",
    "sqlalchemy.dialects.sqlite",
    "greenlet",
    # auth & security
    "bcrypt", "itsdangerous", "slowapi",
    # data processing
    "openpyxl", "pandas", "rapidfuzz",
    # export
    "fpdf2", "docx",
    # utils
    "cachetools", "aiofiles", "multipart",
    "email.mime.multipart", "email.mime.text",
]

EXCLUDES = [
    "tkinter", "matplotlib", "PIL", "pytest",
    "IPython", "notebook", "jupyter", "sphinx",
    "docutils", "pygments", "numpy.testing",
]


def check_pyinstaller():
    try:
        import PyInstaller
        print(f"[v] PyInstaller {PyInstaller.__version__}")
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])


def clean_previous_build():
    for d in [DIST_DIR / APP_NAME, BUILD_DIR / APP_NAME]:
        if d.exists():
            print(f"[~] Xoa: {d}")
            shutil.rmtree(d, ignore_errors=True)


def build_add_data_args():
    args = []
    sep = ";" if sys.platform == "win32" else ":"
    for src, dest in DATA_TO_INCLUDE:
        if Path(src).exists():
            args += ["--add-data", f"{src}{sep}{dest}"]
            print(f"[+] Data: {Path(src).name} -> {dest}/")
        else:
            print(f"[!] Bo qua (khong ton tai): {src}")
    return args


def run_pyinstaller():
    print("\n" + "=" * 60)
    print(f" BUILD: {APP_NAME}")
    print("=" * 60 + "\n")

    icon_path = ROOT / "assets" / "logo.ico"
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--onedir",
        "--noconfirm",
        "--clean",
        "--distpath", str(DIST_DIR),
        "--workpath", str(BUILD_DIR),
        "--log-level", "WARN",
    ]
    if icon_path.exists():
        cmd += ["--icon", str(icon_path)]

    cmd += build_add_data_args()

    for hi in HIDDEN_IMPORTS:
        cmd += ["--hidden-import", hi]
    for exc in EXCLUDES:
        cmd += ["--exclude-module", exc]

    cmd.append(str(ROOT / "run_server.py"))

    result = subprocess.run(cmd, cwd=str(ROOT))
    if result.returncode != 0:
        print("\n[x] Build that bai!")
        sys.exit(1)


def post_build():
    output_dir = DIST_DIR / APP_NAME
    # Tạo thư mục data/uploads trống để app có thể ghi file upload
    uploads_dir = output_dir / "_internal" / "data" / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n[v] BUILD THANH CONG!")
    print(f"    Output: {output_dir}")


if __name__ == "__main__":
    check_pyinstaller()
    clean_previous_build()
    run_pyinstaller()
    post_build()
