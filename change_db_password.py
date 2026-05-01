"""
change_db_password.py — Công cụ đổi mật khẩu mã hóa cho VCFE Database.
Dùng lệnh PRAGMA rekey của SQLCipher để mã hóa lại toàn bộ file với key mới.
"""
import getpass
import os
import sys
from pathlib import Path

def main():
    root = Path(__file__).resolve().parent
    # Đọc tên file DB từ .env nếu có, nếu không dùng mặc định
    db_name = "security_profile.db"
    env_file = root / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("DB_NAME="):
                db_name = line.split("=")[1].strip()
    
    db_path = root / db_name

    if not db_path.exists():
        print(f"\n[LỖI] Không tìm thấy file cơ sở dữ liệu tại: {db_path}")
        return

    print("\n=== CÔNG CỤ ĐỔI MẬT KHẨU MÃ HÓA CƠ SỞ DỮ LIỆU ===")
    
    # 1. Xác thực mật khẩu cũ
    old_pass = getpass.getpass("\n1. Nhập mật khẩu HIỆN TẠI: ")
    
    try:
        from sqlcipher3 import dbapi2 as sqlite3
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        safe_old = old_pass.replace("'", "''")
        cur.execute(f"PRAGMA key='{safe_old}';")
        cur.execute("PRAGMA cipher_compatibility = 4;")
        
        # Kiểm tra xem có mở được không
        cur.execute("SELECT name FROM sqlite_master;")
        cur.fetchone()
        print("   [OK] Xác thực mật khẩu cũ thành công.")
    except Exception as e:
        if "file is not a database" in str(e).lower():
            print("\n[LỖI] Mật khẩu cũ không chính xác.")
        else:
            print(f"\n[LỖI] {e}")
        return

    # 2. Nhập mật khẩu mới
    print("\n2. Thiết lập mật khẩu MỚI")
    new_pass = getpass.getpass("   Nhập mật khẩu mới (tối thiểu 12 ký tự): ")
    
    if len(new_pass) < 12:
        print("\n[LỖI] Mật khẩu mới quá ngắn.")
        return
    if not any(c.isdigit() for c in new_pass) or not any(c.isalpha() for c in new_pass):
        print("\n[LỖI] Mật khẩu phải bao gồm cả chữ và số.")
        return

    confirm_pass = getpass.getpass("   Xác nhận lại mật khẩu mới: ")
    if new_pass != confirm_pass:
        print("\n[LỖI] Xác nhận mật khẩu không khớp.")
        return

    # 3. Thực hiện Rekey
    try:
        safe_new = new_pass.replace("'", "''")
        print("\n   Đang mã hóa lại dữ liệu... Vui lòng không tắt chương trình.")
        cur.execute(f"PRAGMA rekey='{safe_new}';")
        conn.close()
        print("\n=== THÀNH CÔNG! ===")
        print("Mật khẩu mã hóa dữ liệu đã được thay đổi.")
        print("Lần tới khi chạy server, hãy dùng mật khẩu mới này.")
    except Exception as e:
        print(f"\n[LỖI nghiêm trọng khi mã hóa lại] {e}")

if __name__ == "__main__":
    main()
