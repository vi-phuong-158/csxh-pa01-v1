import os
import sys
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
DIST_DIR = ROOT / "dist"
BUILD_DIR = ROOT / "build"
APP_NAME = "QLNNN"

DATA_TO_INCLUDE = [
    (ROOT / "frontend",         "frontend"),
    (ROOT / "landing_page",     "landing_page"),
    (ROOT / "assets",           "assets"),
    (ROOT / "nation.json",      "."),
]

HIDDEN_IMPORTS = [
    "uvicorn.logging", "uvicorn.loops", "uvicorn.loops.auto", "uvicorn.protocols",
    "uvicorn.protocols.http", "uvicorn.protocols.http.auto", "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto", "uvicorn.lifespan", "uvicorn.lifespan.on",
    "anyio", "anyio._backends._asyncio", "anyio._backends._trio", "starlette.routing",
    "starlette.staticfiles", "starlette.templating", "pydantic.deprecated.class_validators",
    "email.mime.multipart", "email.mime.text", "openpyxl", "pandas", "sqlcipher3",
    "bcrypt", "jwt", "cryptography"
]

EXCLUDES = [
    "tkinter", "matplotlib", "numpy.testing", "PIL", "pytest", "IPython",
    "notebook", "jupyter", "sphinx", "docutils", "pygments"
]

def check_pyinstaller():
    try:
        import PyInstaller
        print("[v] PyInstaller is installed.")
    except ImportError:
        print("[!] PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("[v] PyInstaller installed successfully.")

def clean_previous_build():
    for d in [DIST_DIR / APP_NAME, BUILD_DIR / APP_NAME]:
        if d.exists():
            print(f"[~] Cleaning old directory: {d}")
            shutil.rmtree(d, ignore_errors=True)

def build_add_data_args():
    args = []
    for src, dest in DATA_TO_INCLUDE:
        if src.exists():
            sep = ";" if sys.platform == "win32" else ":"
            args += ["--add-data", f"{src}{sep}{dest}"]
            print(f"[+] Attached: {src.name} -> {dest}/")
    return args

def run_pyinstaller():
    print("\n" + "=" * 60)
    print(f" STARTING BUILD: {APP_NAME}")
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
        print(f"[+] Using icon: {icon_path.name}")

    cmd += build_add_data_args()
    for hi in HIDDEN_IMPORTS: cmd += ["--hidden-import", hi]
    for exc in EXCLUDES: cmd += ["--exclude-module", exc]
    cmd.append(str(ROOT / "run_server.py"))

    print(f"\n[>] Running PyInstaller (3-7 minutes)...\n")
    result = subprocess.run(cmd, cwd=str(ROOT))
    if result.returncode != 0:
        print("\n[x] Build failed!")
        sys.exit(1)

def post_build():
    output_dir = DIST_DIR / APP_NAME
    print("\n" + "=" * 60)
    print(" Post-build steps")
    print("=" * 60)
    
    (output_dir / ".env.example").write_text(
        "QLNNN_DB_PASSPHRASE=your-password-here\n", encoding="utf-8"
    )
    
    (output_dir / "INSTRUCTIONS.txt").write_text(
        "1. Copy .env.example to .env and set password\n2. Run QLNNN.exe\n", encoding="utf-8"
    )

    print(f"\n[v] BUILD SUCCESSFUL!")
    print(f"    Output: {output_dir}")

if __name__ == "__main__":
    check_pyinstaller()
    clean_previous_build()
    run_pyinstaller()
    post_build()
