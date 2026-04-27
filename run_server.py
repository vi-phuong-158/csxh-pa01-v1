# run_server.py
"""
Entry-point khởi động và Bootstrap hệ thống VCFE Database.
Tự động cấu hình file .env nếu chạy lần đầu.
"""
import os
import sys
import io
import secrets
import getpass
from pathlib import Path

# Force UTF-8 cho console Windows
if sys.platform == "win32" and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

def bootstrap_env():
    env_path = Path(".env")
    example_path = Path(".env.example")
    
    # Nếu chưa có .env, tạo từ .env.example hoặc tạo mới
    if not env_path.exists():
        print("=" * 60)
        print(" KHOI TAO HE THONG VCFE DATABASE (LAN DAU)")
        print("=" * 60)
        
        db_pass = ""
        while len(db_pass) < 16:
            print("\n[!] Thiet lap mat khau ma hoa CSDL (SQLCipher)")
            print("    (Toi thieu 16 ky tu, bao gom chu va so)")
            db_pass = getpass.getpass(" Nhap mat khau CSDL: ")
            if len(db_pass) < 16:
                print(" >> Loi: Mat khau phai co it nhat 16 ky tu!")
            elif not any(c.isdigit() for c in db_pass) or not any(c.isalpha() for c in db_pass):
                print(" >> Loi: Mat khau phai chua ca chu va so!")
                db_pass = ""

        admin_pass = ""
        while len(admin_pass) < 12:
            print("\n[!] Thiet lap mat khau cho tai khoan Admin")
            print("    (Toi thieu 12 ky tu)")
            admin_pass = getpass.getpass(" Nhap mat khau Admin: ")
            if len(admin_pass) < 12:
                print(" >> Loi: Mat khau phai co it nhat 12 ky tu!")

        secret_key = secrets.token_urlsafe(32)
        
        env_content = f"""# Cấu hình VCFE Database
PROJECT_NAME="VCFE Database"
DB_PASSWORD="{db_pass}"
SECRET_KEY="{secret_key}"
ADMIN_PASSWORD="{admin_pass}"
DEBUG=False
USE_HTTPS=False
"""
        env_path.write_text(env_content, encoding="utf-8")
        print("\n[OK] Da khoi tao file .env thanh cong.")
        print("=" * 60)

def main():
    # 1. Đảm bảo có .env trước khi load backend.config
    bootstrap_env()
    
    # 2. Load settings
    from backend.config import settings
    
    print("\n" + "=" * 60)
    print(f" {settings.PROJECT_NAME} v{settings.PROJECT_VERSION}")
    print(" CƠ SỞ DỮ LIỆU NGƯỜI VN CÓ YẾU TỐ NƯỚC NGOÀI (VCFE)")
    print(f" He thong dang chay tai: http://127.0.0.1:8000")
    print("=" * 60)
    
    # 3. Chạy uvicorn
    import uvicorn
    from backend.main import app
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=False,
        workers=1,
        log_level="info",
        server_header=False,
    )

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Da dung he thong.")
    except RuntimeError as e:
        print(f"\n[LOI HE THONG] {e}")
        input("\nNhan Enter de thoat...")
        sys.exit(1)
    except Exception as e:
        print(f"\n[LOI KHONG XAC DINH] {e}")
        import traceback
        traceback.print_exc()
        input("\nNhan Enter de thoat...")
        sys.exit(1)
