"""
run_server.py — Launcher chính cho VCFED Database Server.

Thay thế cơ chế .env cho các secret bằng nhập tay tương tác:
  - DB_PASSWORD  : nhập qua getpass (ẩn ký tự)
  - SECRET_KEY   : tự suy ra deterministric từ DB_PASSWORD (PBKDF2)
  - ADMIN_PASSWORD: chỉ hỏi lần đầu khi chưa có tài khoản nào trong DB

Các biến không nhạy cảm (DEBUG, DB_NAME, PORT, ...) vẫn đọc từ .env nếu có.
"""
from __future__ import annotations

import base64
import getpass
import hashlib
import os
import sys
from pathlib import Path

# Salt cố định để SECRET_KEY luôn nhất quán qua mỗi lần restart.
# Thay đổi salt này sẽ làm toàn bộ session hiện tại bị invalidate.
_SK_SALT = b"vcfe-secret-key-salt-2024-v1"
_DB_DEFAULT_NAME = "security_profile.db"


def _derive_secret_key(db_password: str) -> str:
    """Sinh SECRET_KEY 48-byte deterministric từ DB_PASSWORD (PBKDF2-SHA256)."""
    raw = hashlib.pbkdf2_hmac(
        "sha256",
        db_password.encode("utf-8"),
        _SK_SALT,
        iterations=100_000,
        dklen=48,
    )
    return base64.urlsafe_b64encode(raw).decode()


def _read_dotenv(name: str, default: str = "") -> str:
    """Đọc 1 biến từ file .env (nếu có), không dùng pydantic."""
    env_file = Path(".env")
    if not env_file.exists():
        return default
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        if key.strip() == name:
            return val.strip()
    return default


def _admin_exists(db_path: Path, db_password: str) -> bool:
    """
    Kiểm tra DB đã có user nào chưa bằng raw SQLCipher connection.
    Chạy TRƯỚC khi import bất kỳ module backend nào để tránh settings
    được load khi ADMIN_PASSWORD chưa được set vào os.environ.
    """
    if not db_path.exists():
        return False
    try:
        from sqlcipher3 import dbapi2 as sqlite3  # type: ignore

        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        safe_key = db_password.replace("'", "''")
        cur.execute(f"PRAGMA key='{safe_key}';")
        cur.execute("PRAGMA cipher_compatibility = 4;")
        # Query thử để xác thực key
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
        row = cur.fetchone()
        if not row:
            conn.close()
            return False  # Bảng users chưa tồn tại -> DB mới hoặc chưa khởi tạo

        cur.execute("SELECT COUNT(*) FROM users")
        count = cur.fetchone()[0]
        conn.close()
        return count > 0
    except Exception as e:
        # Nếu lỗi là "file is not a database" -> Sai mật khẩu SQLCipher
        if "file is not a database" in str(e).lower():
            print("\n  [LỖI] Mật khẩu cơ sở dữ liệu không đúng (không thể giải mã file).")
            sys.exit(1)
        # Các lỗi khác (ví dụ file bị khóa) coi như chưa có admin hoặc lỗi hệ thống
        return False


def main() -> None:
    root = Path(__file__).resolve().parent

    print()
    print("  ╔══════════════════════════════════════════╗")
    print("  ║         VCFED Database Server            ║")
    print("  ╚══════════════════════════════════════════╝")
    print()

    # ── 1. Nhập mật khẩu DB ──────────────────────────────────────────────
    db_password = getpass.getpass("  Mật khẩu cơ sở dữ liệu: ")

    if len(db_password) < 12:
        print("\n  [LỖI] Mật khẩu phải có ít nhất 12 ký tự.")
        sys.exit(1)
    if not any(c.isdigit() for c in db_password):
        print("\n  [LỖI] Mật khẩu phải chứa ít nhất 1 chữ số.")
        sys.exit(1)
    if not any(c.isalpha() for c in db_password):
        print("\n  [LỖI] Mật khẩu phải chứa ít nhất 1 chữ cái.")
        sys.exit(1)

    os.environ["DB_PASSWORD"] = db_password
    os.environ["SECRET_KEY"] = _derive_secret_key(db_password)

    # ── 2. Kiểm tra admin (trước khi import backend) ──────────────────────
    db_name = _read_dotenv("DB_NAME", _DB_DEFAULT_NAME)
    db_path = root / db_name

    if not _admin_exists(db_path, db_password):
        print()
        print("  [Lần đầu] Chưa có tài khoản nào trong cơ sở dữ liệu.")
        admin_pass = getpass.getpass("  Tạo mật khẩu admin (tối thiểu 12 ký tự): ")
        if len(admin_pass) < 12:
            print("\n  [LỖI] Mật khẩu admin phải có ít nhất 12 ký tự.")
            sys.exit(1)
        os.environ["ADMIN_PASSWORD"] = admin_pass
    # Nếu admin đã tồn tại: ADMIN_PASSWORD không cần thiết,
    # config.py sẽ nhận None và init_super_admin() sẽ bỏ qua.

    # ── 3. Khởi động uvicorn ──────────────────────────────────────────────
    # Khi chạy từ PyInstaller bundle: đổi working directory về _MEIPASS
    # để các đường dẫn tương đối "frontend/static", "frontend/templates"
    # trong main.py và các routes giải quyết đúng vị trí trong _internal/.
    if getattr(sys, "frozen", False):
        bundle_dir = getattr(sys, "_MEIPASS", Path(sys.executable).parent / "_internal")
        os.chdir(bundle_dir)
        if str(bundle_dir) not in sys.path:
            sys.path.insert(0, str(bundle_dir))

    # Import app TRỰC TIẾP sau khi env vars đã set — tránh dùng string
    # "backend.main:app" vì PyInstaller không phân tích được string đó.
    from backend.main import app as vcfe_app  # noqa: E402

    port = int(_read_dotenv("PORT", "8000"))

    print()
    print(f"  [OK] Khởi động tại http://127.0.0.1:{port}")
    print("       Nhấn Ctrl+C để dừng.")
    print()

    import uvicorn

    uvicorn.run(vcfe_app, host="127.0.0.1", port=port, reload=False)


if __name__ == "__main__":
    main()
