"""
run_server.py — Launcher chính cho VCFE Database Server.

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
import webbrowser
from pathlib import Path

# Cấu hình encoding UTF-8 chống lỗi UnicodeEncodeError trên Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Salt cố định để SECRET_KEY luôn nhất quán qua mỗi lần restart.
# Thay đổi salt này sẽ làm toàn bộ session hiện tại bị invalidate.
_SK_SALT = b"vcfe-secret-key-salt-2024-v1"
_DB_DEFAULT_NAME = "security_profile.db"

# ── Windows Credential Manager (keyring) ─────────────────────────────────────
_KEYRING_SERVICE = "VCFE-Database"
_KEYRING_USERNAME = "db_password"

def _keyring_get() -> str:
    """Lấy passphrase đã lưu từ Windows Credential Manager."""
    try:
        import keyring
        val = keyring.get_password(_KEYRING_SERVICE, _KEYRING_USERNAME)
        return val or ""
    except Exception:
        return ""

def _keyring_set(password: str) -> bool:
    """Lưu passphrase vào Windows Credential Manager."""
    try:
        import keyring
        keyring.set_password(_KEYRING_SERVICE, _KEYRING_USERNAME, password)
        return True
    except Exception:
        return False

def _keyring_clear() -> None:
    """Xóa passphrase khỏi Windows Credential Manager (khi sai mật khẩu)."""
    try:
        import keyring
        keyring.delete_password(_KEYRING_SERVICE, _KEYRING_USERNAME)
    except Exception:
        pass


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


def _prompt_gui_password(title: str, prompt_text: str, icon_path: str = None) -> str:
    import tkinter as tk
    from tkinter import messagebox
    import sys
    
    root = tk.Tk()
    root.withdraw()
    
    if icon_path and os.path.exists(icon_path):
        try:
            root.iconbitmap(icon_path)
        except Exception:
            pass

    final_password = None
    
    while True:
        dialog = tk.Toplevel(root)
        dialog.title(title)
        dialog.geometry("400x170")
        dialog.resizable(False, False)
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 400) // 2
        y = (dialog.winfo_screenheight() - 170) // 2
        dialog.geometry(f"+{x}+{y}")
        
        tk.Label(dialog, text=prompt_text, font=("Segoe UI", 10, "bold")).pack(pady=(20, 10))
        entry = tk.Entry(dialog, show="●", width=35, font=("Segoe UI", 12))
        entry.pack(pady=5)
        entry.focus_set()
        
        pwd_input = None
        
        def on_submit(event=None):
            nonlocal pwd_input
            pwd_input = entry.get()
            dialog.destroy()
            
        def on_cancel(event=None):
            dialog.destroy()
            
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=15)
        
        btn_submit = tk.Button(btn_frame, text="Xác nhận", width=12, command=on_submit, bg="#0ea5e9", fg="white", font=("Segoe UI", 9, "bold"), relief=tk.FLAT)
        btn_submit.pack(side=tk.LEFT, padx=10)
        
        btn_cancel = tk.Button(btn_frame, text="Thoát", width=12, command=on_cancel, font=("Segoe UI", 9), relief=tk.FLAT)
        btn_cancel.pack(side=tk.LEFT, padx=10)
        
        dialog.bind('<Return>', on_submit)
        dialog.bind('<Escape>', on_cancel)
        
        dialog.attributes('-topmost', True)
        dialog.focus_force()
        dialog.grab_set()
        
        root.wait_window(dialog)
        
        if pwd_input is None:
            root.destroy()
            sys.exit(0)
            
        if len(pwd_input) < 12:
            messagebox.showerror("Lỗi", "Mật khẩu phải có ít nhất 12 ký tự.", parent=root)
            continue
        if not any(c.isdigit() for c in pwd_input):
            messagebox.showerror("Lỗi", "Mật khẩu phải chứa ít nhất 1 chữ số.", parent=root)
            continue
        if not any(c.isalpha() for c in pwd_input):
            messagebox.showerror("Lỗi", "Mật khẩu phải chứa ít nhất 1 chữ cái.", parent=root)
            continue
            
        final_password = pwd_input
        break
        
    root.destroy()
    return final_password


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
            raise ValueError("WRONG_PASSWORD")
        # Các lỗi khác (ví dụ file bị khóa) coi như chưa có admin hoặc lỗi hệ thống
        return False


def _kill_process_on_port(port: int) -> None:
    """Tự động tìm và kill tiến trình đang chiếm port trên Windows."""
    import subprocess
    import time
    try:
        output = subprocess.check_output(f"netstat -ano | findstr :{port}", shell=True).decode()
        for line in output.splitlines():
            parts = line.strip().split()
            # Netstat output pattern: PROTO  LOCAL_ADDRESS  FOREIGN_ADDRESS  STATE  PID
            if len(parts) >= 5 and parts[1].endswith(f":{port}") and parts[3] == "LISTENING":
                pid = parts[-1]
                print(f"  [HỆ THỐNG] Phát hiện cổng {port} đang bị treo bởi PID {pid}. Đang tự động dọn dẹp...")
                subprocess.call(f"taskkill /F /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(1.5)  # Chờ Windows nhả cổng hoàn toàn
                break
    except subprocess.CalledProcessError:
        # Lỗi lệnh hoặc không tìm thấy tiến trình (port đang rảnh)
        pass
    except Exception as e:
        print(f"  [LỖI] Không thể giải phóng cổng {port}: {e}")


def main() -> None:
    root = Path(__file__).resolve().parent

    print()
    print("  ╔══════════════════════════════════════════╗")
    print("  ║         VCFE Database Server             ║")
    print("  ╚══════════════════════════════════════════╝")
    print()

    try:
        import tkinter
        gui_available = True
    except ImportError:
        gui_available = False

    db_name = _read_dotenv("DB_NAME", _DB_DEFAULT_NAME)
    db_path = root / db_name

    # Cấu hình logo custom (nếu có)
    logo_path = str(root / "assets" / "logo.ico")

    # ── 1. Nhập mật khẩu DB ──────────────────────────────────────────────
    try_env = True
    while True:
        db_password = ""
        if try_env:
            db_password = _read_dotenv("DB_PASSWORD") or os.environ.get("DB_PASSWORD", "")
            try_env = False
        
        if not db_password:
            # Ưu tiên lấy từ Keyring (nếu không có trong .env / env var)
            db_password = _keyring_get()
            
        if not db_password:
            # Hỏi người dùng nếu chưa có ở đâu
            if gui_available:
                db_password = _prompt_gui_password("VCFED Database Server", "🔑 Nhập mật khẩu cơ sở dữ liệu để khởi động:", icon_path=logo_path)
            else:
                db_password = getpass.getpass("  Mật khẩu cơ sở dữ liệu: ")
                if len(db_password) < 12 or not any(c.isdigit() for c in db_password) or not any(c.isalpha() for c in db_password):
                    print("\n  [LỖI] Mật khẩu phải >= 12 ký tự, gồm cả chữ và số.")
                    continue

        os.environ["DB_PASSWORD"] = db_password
        os.environ["SECRET_KEY"] = _derive_secret_key(db_password)

        try:
            admin_exists = _admin_exists(db_path, db_password)
            # Mật khẩu đúng -> lưu lại vào keyring nếu vừa mới nhập thủ công
            if _keyring_get() != db_password:
                _keyring_set(db_password)
            break
        except ValueError as e:
            if str(e) == "WRONG_PASSWORD":
                # Sai mật khẩu -> Xóa khỏi keyring để lần lặp sau hỏi lại
                _keyring_clear()
                os.environ.pop("DB_PASSWORD", None)
                os.environ.pop("SECRET_KEY", None)
                
                if gui_available:
                    import tkinter as tk
                    from tkinter import messagebox
                    tk_root = tk.Tk()
                    tk_root.withdraw()
                    if os.path.exists(logo_path):
                        try: tk_root.iconbitmap(logo_path)
                        except: pass
                    messagebox.showerror("Sai mật khẩu", "Mật khẩu cơ sở dữ liệu không đúng (không thể giải mã file).", parent=tk_root)
                    tk_root.destroy()
                else:
                    print("\n  [LỖI] Mật khẩu cơ sở dữ liệu không đúng (không thể giải mã file).")
                continue
            raise

    # ── 2. Kiểm tra admin (trước khi import backend) ──────────────────────
    if not admin_exists:
        print()
        print("  [Lần đầu] Chưa có tài khoản nào trong cơ sở dữ liệu.")
        if gui_available:
            admin_pass = _prompt_gui_password("Tạo tài khoản quản trị", "Lần đầu khởi chạy! Tạo mật khẩu Admin:", icon_path=logo_path)
        else:
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
    
    # Dọn dẹp cổng trước khi bind
    _kill_process_on_port(port)

    # Tự động mở trình duyệt
    webbrowser.open(f"http://127.0.0.1:{port}")

    print()
    print(f"  [OK] Khởi động tại http://127.0.0.1:{port}")
    print("       Nhấn Ctrl+C để dừng.")
    print()

    import uvicorn

    uvicorn.run(vcfe_app, host="127.0.0.1", port=port, reload=False)


if __name__ == "__main__":
    main()
