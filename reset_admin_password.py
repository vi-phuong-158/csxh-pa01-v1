"""
reset_admin_password.py — Công cụ khôi phục mật khẩu tài khoản Quản trị viên (admin).
Công cụ này sẽ yêu cầu bạn nhập mật khẩu Cơ sở dữ liệu để mở khóa dữ liệu, 
sau đó sẽ đặt lại mật khẩu đăng nhập của tài khoản 'admin' về mặc định.
"""
import getpass
import os
import sys
import hashlib
import base64
from pathlib import Path

def _derive_secret_key(db_password: str) -> str:
    # Salt cố định giống trong run_server.py
    _SK_SALT = b"vcfe-secret-key-salt-2024-v1"
    raw = hashlib.pbkdf2_hmac(
        "sha256",
        db_password.encode("utf-8"),
        _SK_SALT,
        iterations=100_000,
        dklen=48,
    )
    return base64.urlsafe_b64encode(raw).decode()

def main():
    print("\n=== CÔNG CỤ KHÔI PHỤC MẬT KHẨU ADMIN ===")
    
    # 1. Yêu cầu mật khẩu DB để mở khóa SQLCipher
    db_password = getpass.getpass("\n1. Nhập mật khẩu Cơ sở dữ liệu (mật khẩu khi khởi động server): ")
    
    if not db_password:
        print("[LỖI] Bạn phải nhập mật khẩu cơ sở dữ liệu.")
        return

    # Thiết lập môi trường để backend/config.py không báo lỗi
    os.environ["DB_PASSWORD"] = db_password
    os.environ["SECRET_KEY"] = _derive_secret_key(db_password)
    
    try:
        # Import các thành phần backend sau khi đã set env vars
        from backend.db.session import SessionLocal
        from backend.models.models import User
        from backend.services.auth import hash_password
        from sqlalchemy import select
        
        db = SessionLocal()
        try:
            # Tìm tài khoản admin
            user = db.execute(select(User).where(User.username == "admin")).scalar_one_or_none()
            
            new_password = "admin@123"
            
            if user:
                user.password_hash = hash_password(new_password)
                user.is_active = True
                user.must_change_password = False
                db.commit()
                print(f"\n[THÀNH CÔNG] Đã đặt lại mật khẩu tài khoản 'admin' thành: {new_password}")
            else:
                # Nếu chưa có thì tạo mới (trường hợp DB trống hoặc bị xóa user admin)
                new_user = User(
                    username="admin",
                    password_hash=hash_password(new_password),
                    ho_ten="Quản trị viên hệ thống",
                    role="admin",
                    is_active=True,
                    must_change_password=False
                )
                db.add(new_user)
                db.commit()
                print(f"\n[THÀNH CÔNG] Đã tạo mới tài khoản 'admin' với mật khẩu: {new_password}")
            
            print("\nBây giờ bạn có thể khởi động lại server và đăng nhập bằng tài khoản admin.")
            
        except Exception as e:
            db.rollback()
            if "file is not a database" in str(e).lower():
                print("\n[LỖI] Mật khẩu Cơ sở dữ liệu không chính xác, không thể mở khóa dữ liệu.")
            else:
                print(f"\n[LỖI] Có lỗi xảy ra: {e}")
        finally:
            db.close()
            
    except ImportError as e:
        print(f"\n[LỖI] Không tìm thấy thư mục backend hoặc thư viện cần thiết: {e}")
    except Exception as e:
        print(f"\n[LỖI] Lỗi hệ thống: {e}")

if __name__ == "__main__":
    main()
