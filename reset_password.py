from backend.db.session import engine, SessionLocal
from backend.models.models import User
from backend.services.auth import hash_password
from sqlalchemy import select

def reset_password():
    db = SessionLocal()
    try:
        user = db.execute(select(User).where(User.username == "admin")).scalar_one_or_none()
        if user:
            user.password_hash = hash_password("admin@123")
            user.is_active = True
            user.must_change_password = False
            db.commit()
            print("Đã reset mật khẩu tài khoản admin thành: admin@123")
        else:
            # Nếu chưa có thì tạo mới
            new_user = User(
                username="admin",
                password_hash=hash_password("admin@123"),
                ho_ten="Quản trị viên hệ thống",
                role="admin",
                is_active=True,
                must_change_password=False
            )
            db.add(new_user)
            db.commit()
            print("Đã tạo mới tài khoản admin với mật khẩu: admin@123")
    except Exception as e:
        db.rollback()
        print(f"Lỗi: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    reset_password()
